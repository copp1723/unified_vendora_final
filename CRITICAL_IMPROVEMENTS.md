"""
Critical Improvements for VENDORA Hierarchical Flow Implementation

After thorough review, here are the critical issues and required improvements:

## 1. CRITICAL SECURITY & RELIABILITY FIXES

### Fix Flask Async Issues
The current implementation uses async routes with Flask, which doesn't work. Need to either:
- Use Quart (async Flask alternative)
- Use asyncio.run() within sync routes
- Switch to FastAPI

### Add SQL Injection Protection
- Use parameterized queries
- Validate dealership_id format
- Sanitize all user inputs

### Implement Actual Client Initialization
```python
async def _initialize_clients(self):
    # Gemini client with retry logic
    self.gemini_client = genai.GenerativeModel(
        'gemini-pro',
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 2048,
        }
    )
    
    # BigQuery client with proper credentials
    from google.oauth2 import service_account
    credentials = service_account.Credentials.from_service_account_file(
        self.config.get('service_account_path')
    )
    self.bigquery_client = bigquery.Client(
        credentials=credentials,
        project=self.config.get('bigquery_project')
    )
```

## 2. RELIABILITY IMPROVEMENTS

### Add Timeout Handling
```python
async def process_user_query(self, user_query: str, dealership_id: str, 
                           user_context: Dict[str, Any] = None,
                           timeout: int = 30) -> Dict[str, Any]:
    try:
        return await asyncio.wait_for(
            self._process_query_internal(user_query, dealership_id, user_context),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return {"error": "Query processing timed out", "timeout": timeout}
```

### Add Retry Logic
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def _call_gemini_with_retry(self, prompt: str) -> str:
    return await self._call_gemini(prompt)
```

### Add State Persistence
- Use Redis or Firestore for flow state
- Implement checkpointing for long-running tasks
- Add recovery mechanism for interrupted flows

## 3. INTELLIGENCE IMPROVEMENTS

### Dynamic Table Schema Discovery
Instead of hardcoding table schemas, query them dynamically:
```python
async def _get_table_schema(self, dataset_id: str, table_id: str):
    query = f"""
    SELECT column_name, data_type 
    FROM `{self.config['bigquery_project']}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table_id}'
    """
    return await self._execute_query(query)
```

### Add Query Result Caching
```python
from functools import lru_cache
import hashlib

def _get_query_cache_key(self, query: str, params: Dict) -> str:
    cache_data = f"{query}:{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(cache_data.encode()).hexdigest()

async def _execute_query_with_cache(self, query: str, params: Dict):
    cache_key = self._get_query_cache_key(query, params)
    
    # Check cache first
    cached_result = await self.cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Execute query
    result = await self._execute_query(query, params)
    
    # Cache for 1 hour
    await self.cache.set(cache_key, result, expire=3600)
    return result
```

### Improve Error Messages
Provide actionable error messages:
```python
class VendoraError(Exception):
    def __init__(self, message: str, error_code: str, suggestions: List[str]):
        self.message = message
        self.error_code = error_code
        self.suggestions = suggestions
        super().__init__(message)

# Usage
if not data:
    raise VendoraError(
        message="No sales data found for the specified period",
        error_code="NO_DATA",
        suggestions=[
            "Try expanding the date range",
            "Verify the dealership has sales in this period",
            "Check if data ingestion is up to date"
        ]
    )
```

## 4. PERFORMANCE OPTIMIZATIONS

### Parallel Query Execution
```python
async def _execute_queries_parallel(self, queries: List[str]):
    tasks = [self._execute_query(query) for query in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle partial failures
    successful_results = []
    failed_queries = []
    
    for query, result in zip(queries, results):
        if isinstance(result, Exception):
            failed_queries.append((query, str(result)))
        else:
            successful_results.append(result)
    
    return successful_results, failed_queries
```

### Add Query Optimization
```python
def _optimize_query(self, query: str) -> str:
    # Add automatic date partitioning
    if "sale_date" in query and "_TABLE_SUFFIX" not in query:
        # Convert to partitioned query
        query = query.replace(
            "FROM sales",
            "FROM `sales_*` WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)) AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())"
        )
    return query
```

## 5. MONITORING & OBSERVABILITY

### Add Structured Logging
```python
import structlog

logger = structlog.get_logger()

async def process_user_query(self, user_query: str, dealership_id: str):
    log = logger.bind(
        task_id=task.id,
        dealership_id=dealership_id,
        query_length=len(user_query)
    )
    
    log.info("processing_query_start")
    
    try:
        result = await self._process_internal(...)
        log.info("processing_query_success", 
                processing_time_ms=result['metadata']['processing_time_ms'])
        return result
    except Exception as e:
        log.error("processing_query_failed", error=str(e))
        raise
```

### Add Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
query_counter = Counter('vendora_queries_total', 'Total queries processed', 
                       ['dealership', 'complexity', 'status'])
query_duration = Histogram('vendora_query_duration_seconds', 'Query processing time',
                         ['complexity'])
active_flows = Gauge('vendora_active_flows', 'Number of active flows')

# Use in code
query_counter.labels(
    dealership=dealership_id,
    complexity=task.complexity.value,
    status='success'
).inc()
```

## 6. CONFIGURATION IMPROVEMENTS

### Use Pydantic for Config Validation
```python
from pydantic import BaseSettings, validator

class VendoraConfig(BaseSettings):
    gemini_api_key: str
    bigquery_project: str
    quality_threshold: float = 0.85
    max_query_timeout: int = 30
    max_retries: int = 3
    
    @validator('quality_threshold')
    def validate_threshold(cls, v):
        if not 0 < v <= 1:
            raise ValueError('quality_threshold must be between 0 and 1')
        return v
    
    class Config:
        env_file = '.env'
```

## 7. TESTING IMPROVEMENTS

### Add Unit Tests
```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_hierarchical_flow_simple_query():
    config = {"gemini_api_key": "test", "bigquery_project": "test"}
    flow_manager = HierarchicalFlowManager(config)
    
    # Mock the Gemini responses
    with patch.object(flow_manager.orchestrator, '_call_gemini') as mock_gemini:
        mock_gemini.return_value = '{"complexity": "simple", "data_sources": ["sales"]}'
        
        result = await flow_manager.process_user_query(
            "How many cars sold today?",
            "dealer_123"
        )
        
        assert result['metadata']['complexity'] == 'simple'
        assert 'error' not in result
```

## 8. DEPLOYMENT READINESS

### Add Health Checks
```python
async def health_check(self) -> Dict[str, Any]:
    checks = {
        "bigquery": await self._check_bigquery_connection(),
        "gemini": await self._check_gemini_connection(),
        "memory": self._check_memory_usage(),
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}
```

### Add Graceful Shutdown
```python
async def shutdown(self):
    # Set shutdown flag
    self.shutting_down = True
    
    # Stop accepting new queries
    logger.info("Stopped accepting new queries")
    
    # Wait for active flows with timeout
    await self._wait_for_active_flows(timeout=30)
    
    # Close connections
    if self.bigquery_client:
        self.bigquery_client.close()
    
    # Save state
    await self._persist_final_state()
```

These improvements would make the system production-ready, secure, and truly reliable.
"""
