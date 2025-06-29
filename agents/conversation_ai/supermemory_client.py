"""
SuperMemory client for VENDORA automotive data platform.
Handles context storage and retrieval for dealer-specific data and insights.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
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
    
    def _store_locally(self, category: str, dealer_id: str, key: str, data: Any) -> bool:
        """Store data locally as fallback when API is unavailable."""
        try:
            file_path = os.path.join(self.memory_storage_path, category, f"{dealer_id}_{key}.json")
            
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
            file_path = os.path.join(self.memory_storage_path, category, f"{dealer_id}_{key}.json")
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    storage_data = json.load(f)
                return storage_data.get('data')
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving data locally: {e}")
            return None
    
    def store_dealer_preferences(self, dealer_id: str, preferences: Dict[str, Any]) -> bool:
        """Store dealer-specific preferences (UI layout, report formats, etc.)."""
        try:
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
            queries_dir = os.path.join(self.memory_storage_path, 'common_queries')
            recent_queries = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filename in os.listdir(queries_dir):
                if filename.startswith(dealer_id) and filename.endswith('.json'):
                    file_path = os.path.join(queries_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        # Check if within date range
                        timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                        if timestamp >= cutoff_date:
                            recent_queries.append(data['data'])
                    except Exception as e:
                        logger.error(f"Error reading query file {file_path}: {e}")
            
            # Sort by timestamp
            recent_queries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return recent_queries
            
        except Exception as e:
            logger.error(f"Error getting recent queries locally: {e}")
            return []
    
    def store_insights(self, dealer_id: str, insights: Dict[str, Any], file_context: str) -> bool:
        """Store generated insights for future reference and context."""
        try:
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

