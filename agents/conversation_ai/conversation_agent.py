"""
Conversation Agent for VENDORA automotive data platform.
Orchestrates the complete Q&A pipeline using SuperMemory context and OpenRouter AI.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .supermemory_client import SuperMemoryClient
from .openrouter_client import OpenRouterClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationAgent:
    """Main conversation agent that handles natural language Q&A about automotive data."""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize clients
        self.supermemory = SuperMemoryClient(config)
        self.openrouter = OpenRouterClient(config)
        
        # Data storage path for accessing processed insights
        self.data_storage_path = config.get('DATA_STORAGE_PATH', '/tmp/vendora_data')
    
    def get_dealer_insights(self, dealer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent processed insights for a dealer."""
        try:
            processed_dir = os.path.join(self.data_storage_path, 'processed')
            insights = []
            
            if not os.path.exists(processed_dir):
                return []
            
            # Find all processed files for this dealer
            for filename in os.listdir(processed_dir):
                if filename.startswith(dealer_id) and filename.endswith('_processed.json'):
                    file_path = os.path.join(processed_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            insights.append(data)
                    except Exception as e:
                        logger.error(f"Error reading processed file {file_path}: {e}")
            
            # Sort by timestamp and return most recent
            insights.sort(key=lambda x: x.get('processed_timestamp', ''), reverse=True)
            return insights[:limit]
            
        except Exception as e:
            logger.error(f"Error getting dealer insights for {dealer_id}: {e}")
            return []
    
    def process_query(self, dealer_id: str, query: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Process a natural language query about automotive data."""
        try:
            logger.info(f"Processing query for dealer {dealer_id}: {query}")
            
            # Get dealer context from SuperMemory
            dealer_context = self.supermemory.get_dealer_context(dealer_id)
            
            # Get recent insights data
            insights_data = self.get_dealer_insights(dealer_id)
            
            # Use OpenRouter to answer the question
            response = self.openrouter.answer_question(
                query=query,
                dealer_context=dealer_context,
                insights_data=insights_data,
                model=model
            )
            
            if response.get('status') == 'success':
                # Store the interaction in SuperMemory for future context
                interaction_context = {
                    'query': query,
                    'response': response.get('response', {}),
                    'model_used': response.get('model_used'),
                    'insights_count': len(insights_data)
                }
                
                self.supermemory.store_query_interaction(
                    dealer_id=dealer_id,
                    query=query,
                    response=json.dumps(response.get('response', {})),
                    context=interaction_context
                )
                
                logger.info(f"Successfully processed query for dealer {dealer_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def get_dealer_summary(self, dealer_id: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Get a comprehensive summary of dealer performance and insights."""
        try:
            logger.info(f"Generating summary for dealer {dealer_id}")
            
            # Get dealer context
            dealer_context = self.supermemory.get_dealer_context(dealer_id)
            
            # Get recent insights
            insights_data = self.get_dealer_insights(dealer_id)
            
            # Generate summary using OpenRouter
            response = self.openrouter.generate_insights_summary(insights_data, dealer_context)
            
            if response.get('status') == 'success':
                # Store the summary interaction
                self.supermemory.store_query_interaction(
                    dealer_id=dealer_id,
                    query="[SUMMARY_REQUEST]",
                    response=json.dumps(response.get('response', {})),
                    context={'type': 'summary', 'insights_count': len(insights_data)}
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating dealer summary: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def update_dealer_preferences(self, dealer_id: str, preferences: Dict[str, Any]) -> bool:
        """Update dealer preferences in SuperMemory."""
        try:
            return self.supermemory.store_dealer_preferences(dealer_id, preferences)
        except Exception as e:
            logger.error(f"Error updating dealer preferences: {e}")
            return False
    
    def get_dealer_preferences(self, dealer_id: str) -> Dict[str, Any]:
        """Get dealer preferences from SuperMemory."""
        try:
            return self.supermemory.get_dealer_preferences(dealer_id) or {}
        except Exception as e:
            logger.error(f"Error getting dealer preferences: {e}")
            return {}
    
    def get_conversation_history(self, dealer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent conversation history for a dealer."""
        try:
            return self.supermemory.get_recent_queries(dealer_id, days)
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models."""
        try:
            return self.openrouter.get_available_models()
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return ['anthropic/claude-3-haiku']
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of all components."""
        health = {
            'conversation_agent': 'healthy',
            'supermemory': 'unknown',
            'openrouter': 'unknown',
            'data_storage': 'unknown'
        }
        
        try:
            # Check data storage
            if os.path.exists(self.data_storage_path):
                health['data_storage'] = 'healthy'
            else:
                health['data_storage'] = 'unhealthy'
            
            # Check SuperMemory (try to get a test preference)
            test_prefs = self.supermemory.get_dealer_preferences('health_check')
            health['supermemory'] = 'healthy'
            
            # Check OpenRouter (try to get models)
            models = self.openrouter.get_available_models()
            if models:
                health['openrouter'] = 'healthy'
            else:
                health['openrouter'] = 'unhealthy'
                
        except Exception as e:
            logger.error(f"Error in health check: {e}")
        
        return health


if __name__ == '__main__':
    # Test the conversation agent
    config = {
        'OPENROUTER_API_KEY': 'test_key',
        'SUPERMEMORY_API_KEY': 'test_key',
        'DATA_STORAGE_PATH': '/home/ubuntu/vendora/data',
        'MEMORY_STORAGE_PATH': '/home/ubuntu/vendora/memory'
    }
    
    agent = ConversationAgent(config)
    print("Conversation agent initialized successfully")

