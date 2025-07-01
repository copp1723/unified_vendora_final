"""
SuperMemory client for VENDORA automotive data platform.
Handles context storage and retrieval for dealer-specific data and insights.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SuperMemoryClient:
    """Client for interacting with SuperMemory API for context storage."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('SUPERMEMORY_API_KEY')
        self.base_url = config.get('SUPERMEMORY_BASE_URL', 'https://api.supermemory.ai')
        self.memory_storage_path = config.get('MEMORY_STORAGE_PATH', '/tmp/vendora_memory')
        
        # Ensure memory storage directory exists (for local fallback)
        os.makedirs(self.memory_storage_path, exist_ok=True)
        os.makedirs(f"{self.memory_storage_path}/dealer_preferences", exist_ok=True)
        os.makedirs(f"{self.memory_storage_path}/common_queries", exist_ok=True)
        os.makedirs(f"{self.memory_storage_path}/insights", exist_ok=True)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to SuperMemory API."""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"SuperMemory API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making SuperMemory API request: {e}")
            return None
    
    def _validate_dealer_id(self, dealer_id: str) -> bool:
        """Validate dealer ID format for security."""
        if not dealer_id or not isinstance(dealer_id, str):
            return False
        return bool(re.match(r'^[a-zA-Z0-9-_]+$', dealer_id)) and len(dealer_id) <= 50
    
    def _validate_key(self, key: str) -> bool:
        """Validate key format for security."""
        if not key or not isinstance(key, str):
            return False
        return bool(re.match(r'^[a-zA-Z0-9-_]+$', key)) and len(key) <= 100
    
    def _store_locally(self, category: str, dealer_id: str, key: str, data: Any) -> bool:
        """Store data locally as fallback when API is unavailable."""
        try:
            if not self._validate_dealer_id(dealer_id) or not self._validate_key(key):
                logger.error(f"Invalid dealer_id or key format: {dealer_id}, {key}")
                return False
            
            # Use Path for safer file handling
            category_dir = Path(self.memory_storage_path) / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = category_dir / f"{dealer_id}_{key}.json"
            
            storage_data = {
                'dealer_id': dealer_id,
                'key': key,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'category': category
            }
            
            with open(file_path, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            logger.info(f"Stored data locally: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing data locally: {e}")
            return False
    
    def _retrieve_locally(self, category: str, dealer_id: str, key: str) -> Optional[Any]:
        """Retrieve data locally as fallback when API is unavailable."""
        try:
            if not self._validate_dealer_id(dealer_id) or not self._validate_key(key):
                logger.error(f"Invalid dealer_id or key format: {dealer_id}, {key}")
                return None
            
            file_path = Path(self.memory_storage_path) / category / f"{dealer_id}_{key}.json"
            
            if file_path.exists():
                with open(file_path, 'r') as f:
                    storage_data = json.load(f)
                    if isinstance(storage_data, dict):  # Validate JSON structure
                        return storage_data.get('data')
            
            return None
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error retrieving data locally: {e}")
            return None
    
    def store_dealer_preferences(self, dealer_id: str, preferences: Dict[str, Any]) -> bool:
        """Store dealer-specific preferences (UI layout, report formats, etc.)."""
        try:
            if not self._validate_dealer_id(dealer_id):
                logger.error(f"Invalid dealer_id format: {dealer_id}")
                return False
            
            if not isinstance(preferences, dict):
                logger.error("Preferences must be a dictionary")
                return False
            # Try SuperMemory API first
            data = {
                'dealer_id': dealer_id,
                'preferences': preferences,
                'timestamp': datetime.now().isoformat(),
                'type': 'dealer_preferences'
            }
            
            result = self._make_request('POST', '/memories', data)
            
            if result:
                logger.info(f"Stored dealer preferences for {dealer_id} in SuperMemory")
                return True
            else:
                # Fallback to local storage
                return self._store_locally('dealer_preferences', dealer_id, 'preferences', preferences)
                
        except Exception as e:
            logger.error(f"Error storing dealer preferences: {e}")
            return self._store_locally('dealer_preferences', dealer_id, 'preferences', preferences)
    
    def get_dealer_preferences(self, dealer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve dealer-specific preferences."""
        try:
            if not self._validate_dealer_id(dealer_id):
                logger.error(f"Invalid dealer_id format: {dealer_id}")
                return None
            # Try SuperMemory API first
            params = {
                'dealer_id': dealer_id,
                'type': 'dealer_preferences'
            }
            
            result = self._make_request('GET', '/memories', params)
            
            if result and 'preferences' in result:
                return result['preferences']
            else:
                # Fallback to local storage
                return self._retrieve_locally('dealer_preferences', dealer_id, 'preferences')
                
        except Exception as e:
            logger.error(f"Error retrieving dealer preferences: {e}")
            return self._retrieve_locally('dealer_preferences', dealer_id, 'preferences')
    
    def store_query_interaction(self, dealer_id: str, query: str, response: str, context: Dict[str, Any]) -> bool:
        """Store query interaction for learning and context building."""
        try:
            if not self._validate_dealer_id(dealer_id):
                logger.error(f"Invalid dealer_id format: {dealer_id}")
                return False
            
            if not query or len(query.strip()) == 0:
                logger.error("Query cannot be empty")
                return False
            interaction_data = {
                'dealer_id': dealer_id,
                'query': query,
                'response': response,
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'type': 'query_interaction'
            }
            
            # Try SuperMemory API first
            result = self._make_request('POST', '/memories', interaction_data)
            
            if result:
                logger.info(f"Stored query interaction for {dealer_id} in SuperMemory")
                return True
            else:
                # Fallback to local storage
                interaction_key = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return self._store_locally('common_queries', dealer_id, interaction_key, interaction_data)
                
        except Exception as e:
            logger.error(f"Error storing query interaction: {e}")
            interaction_key = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return self._store_locally('common_queries', dealer_id, interaction_key, interaction_data)
    
    def get_recent_queries(self, dealer_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get recent query interactions for context (last 3 months by default)."""
        try:
            if not self._validate_dealer_id(dealer_id):
                logger.error(f"Invalid dealer_id format: {dealer_id}")
                return []
            
            # Limit days to reasonable range
            days = max(1, min(days, 365))
            # Try SuperMemory API first
            cutoff_date = datetime.now() - timedelta(days=days)
            params = {
                'dealer_id': dealer_id,
                'type': 'query_interaction',
                'since': cutoff_date.isoformat()
            }
            
            result = self._make_request('GET', '/memories', params)
            
            if result and isinstance(result, list):
                return result
            else:
                # Fallback to local storage
                return self._get_recent_queries_locally(dealer_id, days)
                
        except Exception as e:
            logger.error(f"Error retrieving recent queries: {e}")
            return self._get_recent_queries_locally(dealer_id, days)
    
    def _get_recent_queries_locally(self, dealer_id: str, days: int) -> List[Dict[str, Any]]:
        """Get recent queries from local storage."""
        try:
            queries_dir = Path(self.memory_storage_path) / 'common_queries'
            recent_queries = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if not queries_dir.exists():
                return []
            
            for file_path in queries_dir.glob(f"{dealer_id}_*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if not isinstance(data, dict):
                        continue
                    
                    # Check if within date range
                    timestamp_str = data.get('timestamp', '')
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp >= cutoff_date and 'data' in data:
                            recent_queries.append(data['data'])
                except (json.JSONDecodeError, ValueError, IOError) as e:
                    logger.error(f"Error reading query file {file_path}: {e}")
            
            # Sort by timestamp and limit results
            recent_queries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return recent_queries[:100]  # Cap at 100 for safety
            
        except Exception as e:
            logger.error(f"Error getting recent queries locally: {e}")
            return []
    
    def store_insights(self, dealer_id: str, insights: Dict[str, Any], file_context: str) -> bool:
        """Store generated insights for future reference and context."""
        try:
            if not self._validate_dealer_id(dealer_id):
                logger.error(f"Invalid dealer_id format: {dealer_id}")
                return False
            
            if not isinstance(insights, dict):
                logger.error("Insights must be a dictionary")
                return False
            insight_data = {
                'dealer_id': dealer_id,
                'insights': insights,
                'file_context': file_context,
                'timestamp': datetime.now().isoformat(),
                'type': 'insights'
            }
            
            # Try SuperMemory API first
            result = self._make_request('POST', '/memories', insight_data)
            
            if result:
                logger.info(f"Stored insights for {dealer_id} in SuperMemory")
                return True
            else:
                # Fallback to local storage
                insight_key = f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return self._store_locally('insights', dealer_id, insight_key, insight_data)
                
        except Exception as e:
            logger.error(f"Error storing insights: {e}")
            insight_key = f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return self._store_locally('insights', dealer_id, insight_key, insight_data)
    
    def get_dealer_context(self, dealer_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a dealer including preferences, recent queries, and insights."""
        try:
            if not self._validate_dealer_id(dealer_id):
                logger.error(f"Invalid dealer_id format: {dealer_id}")
                return {'dealer_id': dealer_id, 'preferences': {}, 'recent_queries': []}
            context = {
                'dealer_id': dealer_id,
                'preferences': self.get_dealer_preferences(dealer_id) or {},
                'recent_queries': self.get_recent_queries(dealer_id, days=90),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Retrieved dealer context for {dealer_id}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting dealer context: {e}")
            return {'dealer_id': dealer_id, 'preferences': {}, 'recent_queries': []}


if __name__ == '__main__':
    # Test the SuperMemory client
    config = {
        'SUPERMEMORY_API_KEY': 'test_key',
        'MEMORY_STORAGE_PATH': '/home/ubuntu/vendora/memory'
    }
    
    client = SuperMemoryClient(config)
    print("SuperMemory client initialized successfully")

