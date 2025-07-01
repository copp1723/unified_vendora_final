"""
Enhanced BigQuery Client with Connection Pooling
Implements SQLAlchemy-style connection pooling for BigQuery operations
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import weakref

from google.cloud import bigquery
from google.cloud.bigquery.job import QueryJob
from google.oauth2 import service_account
from prometheus_client import Counter, Gauge, Histogram
from tenacity import retry, stop_after_attempt, wait_exponential

from src.reliability.circuit_breaker import circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Connection pool metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_connections: int = 0
    destroyed_connections: int = 0
    pool_exhausted_count: int = 0
    last_pool_exhausted: Optional[datetime] = None


@dataclass
class PooledConnection:
    """Represents a pooled BigQuery connection"""
    client: bigquery.Client
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    query_count: int = 0
    is_active: bool = False
    connection_id: str = field(default_factory=lambda: f"conn_{int(time.time()*1000)}")


class PooledBigQueryClient:
    """
    Enhanced BigQuery client with connection pooling, query optimization, and monitoring
    """
    
    def __init__(self, 
                 project_id: str,
                 max_connections: int = 10,
                 min_connections: int = 2,
                 max_idle_time: int = 300,  # 5 minutes
                 connection_timeout: int = 30,
                 query_timeout: int = 60,
                 credentials_path: Optional[str] = None):
        
        self.project_id = project_id
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.max_idle_time = max_idle_time
        self.connection_timeout = connection_timeout
        self.query_timeout = query_timeout
        self.credentials_path = credentials_path
        
        # Connection pool
        self._pool: List[PooledConnection] = []
        self._pool_lock = asyncio.Lock()
        self._connection_semaphore = asyncio.Semaphore(max_connections)
        
        # Metrics and monitoring
        self.metrics = ConnectionMetrics()
        self._query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._query_stats = defaultdict(int)
        
        # Prometheus metrics
        self.prom_active_connections = Gauge(
            'bigquery_pool_active_connections',
            'Number of active BigQuery connections'
        )
        self.prom_idle_connections = Gauge(
            'bigquery_pool_idle_connections', 
            'Number of idle BigQuery connections'
        )
        self.prom_query_duration = Histogram(
            'bigquery_query_duration_seconds',
            'BigQuery query execution time',
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]
        )
        self.prom_pool_exhausted = Counter(
            'bigquery_pool_exhausted_total',
            'Number of times connection pool was exhausted'
        )
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the connection pool"""
        if self._initialized:
            return
            
        logger.info(f"🚀 Initializing BigQuery connection pool (max: {self.max_connections})")
        
        # Create minimum connections
        async with self._pool_lock:
            for _ in range(self.min_connections):
                try:
                    conn = await self._create_connection()
                    self._pool.append(conn)
                    logger.info(f"✅ Created initial connection: {conn.connection_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to create initial connection: {e}")
                    
        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._connection_cleanup_loop())
        self._initialized = True
        
        logger.info(f"✅ BigQuery connection pool initialized with {len(self._pool)} connections")
    
    async def _create_connection(self) -> PooledConnection:
        """Create a new BigQuery connection"""
        try:
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                client = bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
            else:
                client = bigquery.Client(project=self.project_id)
            
            # Test the connection
            test_query = "SELECT 1 as test_connection"
            query_job = client.query(test_query)
            query_job.result(timeout=5)  # Quick test
            
            connection = PooledConnection(client=client)
            self.metrics.created_connections += 1
            self.metrics.total_connections += 1
            
            logger.debug(f"📡 Created new BigQuery connection: {connection.connection_id}")
            return connection
            
        except Exception as e:
            logger.error(f"❌ Failed to create BigQuery connection: {e}")
            raise
    
    async def _get_connection(self) -> PooledConnection:
        """Get an available connection from the pool"""
        async with self._connection_semaphore:
            async with self._pool_lock:
                # Try to find an idle connection
                for conn in self._pool:
                    if not conn.is_active:
                        conn.is_active = True
                        conn.last_used = datetime.now()
                        self.metrics.active_connections += 1
                        self.metrics.idle_connections = max(0, self.metrics.idle_connections - 1)
                        self.prom_active_connections.inc()
                        self.prom_idle_connections.dec()
                        return conn
                
                # No idle connections available, try to create a new one
                if len(self._pool) < self.max_connections:
                    try:
                        conn = await self._create_connection()
                        conn.is_active = True
                        self._pool.append(conn)
                        self.metrics.active_connections += 1
                        self.prom_active_connections.inc()
                        return conn
                    except Exception as e:
                        logger.error(f"Failed to create new connection: {e}")
                
                # Pool is exhausted
                self.metrics.pool_exhausted_count += 1
                self.metrics.last_pool_exhausted = datetime.now()
                self.prom_pool_exhausted.inc()
                
                logger.warning("🚨 BigQuery connection pool exhausted, waiting...")
                
        # If we get here, we need to wait for a connection to become available
        # This will block until a connection is returned
        return await self._get_connection()
    
    def _return_connection(self, conn: PooledConnection):
        """Return a connection to the pool"""
        conn.is_active = False
        conn.last_used = datetime.now()
        self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
        self.metrics.idle_connections += 1
        self.prom_active_connections.dec()
        self.prom_idle_connections.inc()
        self._connection_semaphore.release()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    @circuit_breaker("bigquery", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60))
    async def execute_query(self, 
                          query: str, 
                          params: Optional[Dict] = None,
                          use_cache: bool = True,
                          cache_ttl: int = 300) -> Dict[str, Any]:
        """
        Execute a BigQuery query with connection pooling and caching
        """
        query_start = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query, params)
        
        # Check cache first
        if use_cache and cache_key in self._query_cache:
            cached_result, cached_time = self._query_cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=cache_ttl):
                logger.info(f"🎯 Cache HIT for query: {cache_key[:20]}...")
                return {
                    **cached_result,
                    "metadata": {
                        **cached_result.get("metadata", {}),
                        "cached": True,
                        "cache_age_seconds": (datetime.now() - cached_time).total_seconds()
                    }
                }
        
        # Get connection from pool
        conn = await self._get_connection()
        
        try:
            # Configure query job
            job_config = bigquery.QueryJobConfig()
            if params:
                job_config.query_parameters = [
                    bigquery.ScalarQueryParameter(k, "STRING", str(v))
                    for k, v in params.items()
                ]
            
            # Execute query
            logger.info(f"🔍 Executing BigQuery: {query[:100]}...")
            query_job = conn.client.query(query, job_config=job_config)
            
            # Wait for results with timeout
            results = query_job.result(timeout=self.query_timeout)
            
            # Process results
            rows = [dict(row) for row in results]
            
            # Collect job statistics
            job_stats = {
                "total_bytes_processed": query_job.total_bytes_processed,
                "total_bytes_billed": query_job.total_bytes_billed,
                "cache_hit": query_job.cache_hit,
                "creation_time": query_job.created.isoformat() if query_job.created else None,
                "end_time": query_job.ended.isoformat() if query_job.ended else None,
                "slot_ms": query_job.slot_millis
            }
            
            result = {
                "data": rows,
                "row_count": len(rows),
                "job_id": query_job.job_id,
                "metadata": {
                    "query_stats": job_stats,
                    "connection_id": conn.connection_id,
                    "cached": False,
                    "execution_time_seconds": time.time() - query_start
                }
            }
            
            # Cache the result
            if use_cache:
                self._query_cache[cache_key] = (result, datetime.now())
                # Cleanup old cache entries
                await self._cleanup_query_cache()
            
            # Update metrics
            conn.query_count += 1
            self._query_stats[cache_key] += 1
            
            # Record metrics
            self.prom_query_duration.observe(time.time() - query_start)
            
            logger.info(f"✅ Query completed in {time.time() - query_start:.2f}s, "
                       f"returned {len(rows)} rows")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ BigQuery query failed: {e}")
            raise
        finally:
            # Always return connection to pool
            self._return_connection(conn)
    
    async def execute_batch_queries(self, 
                                  queries: List[Tuple[str, Optional[Dict]]],
                                  max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Execute multiple queries concurrently with controlled parallelism
        """
        logger.info(f"🚀 Executing batch of {len(queries)} queries")
        
