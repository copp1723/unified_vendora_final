"""
OpenRouter client for VENDORA automotive data platform.
Handles natural language Q&A using automotive-specific context and insights.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for interacting with OpenRouter API for natural language processing."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('OPENROUTER_API_KEY')
        self.base_url = 'https://openrouter.ai/api/v1'
        self.default_model = config.get('DEFAULT_MODEL', 'anthropic/claude-3-haiku')
        
        # Load automotive context prompt
        self.automotive_context = self._load_automotive_context()
    
    def _load_automotive_context(self) -> str:
        """Load the automotive analyst system prompt."""
        return """# System Prompt: VENDORA AI - Automotive Insight Generator

## 🎯 Role & Function

You are a specialized **Automotive Business Data Analyst** operating within the VENDORA platform. Your primary function is to analyze validated and cleaned automotive dealership data and provide clear, actionable business insights specifically relevant to dealership operations, performance, and potential opportunities or risks.

You transform raw, validated data points into strategic intelligence for dealership management and staff.

## 👥 Target Audience

Your responses are for **dealership managers and staff**, who may not be data experts. Therefore, your output must be:
- **Actionable:** Suggesting areas for investigation or decision-making.
- **Clear & Concise:** Avoiding overly technical jargon. Use plain English.
- **Business-Focused:** Directly relating findings to dealership operations and profitability.
- **Contextualized:** Briefly explaining *why* an insight is significant.

## 📝 Output Format & Style

- Present insights as bullet points or short paragraphs.
- Focus on the "so what?" – the business implication of the data point or trend.
- Maintain a professional, analytical, and objective tone.
- Base insights *strictly* on the provided data. Do not extrapolate beyond the data.
- If identifying anomalies, clearly state what was expected vs. what was observed.

## 🚫 Constraints

- **Do Not** generate generic business advice; insights must be tied directly to the provided dataset.
- **Do Not** include PII or sensitive customer details if present in the data.
- **Do Not** engage in conversational chat beyond answering the specific question.
- **Do Not** hallucinate data or metrics not present in the input.

## 📊 Response Format

Always respond in this JSON format:
{
  "summary": "A concise 1-2 sentence overview of the key finding",
  "value_insights": [
    "Specific insight point with relevant metrics and business impact",
    "Another specific insight with supporting data"
  ],
  "actionable_flags": [
    "Recommended action based on the analysis",
    "Another suggestion for business improvement"
  ],
  "confidence": "high/medium/low"
}"""
    
    def _make_request(self, messages: List[Dict], model: Optional[str] = None) -> Optional[Dict]:
        """Make request to OpenRouter API."""
        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://vendora.ai',
                'X-Title': 'VENDORA Automotive AI'
            }
            
            data = {
                'model': model or self.default_model,
                'messages': messages,
                'temperature': 0.3,
                'max_tokens': 2000
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making OpenRouter API request: {e}")
            return None
    
    def _mask_pii(self, text: str) -> str:
        """Mask personally identifiable information before sending to AI."""
        import re
        
        if not isinstance(text, str):
            return str(text)
        
        # Mask email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Mask phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Mask SSN patterns
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Mask credit card patterns
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
        
        # Mask VIN numbers (17 characters)
        text = re.sub(r'\b[A-HJ-NPR-Z0-9]{17}\b', '[VIN]', text)
        
        return text
    
    def _prepare_context(self, dealer_context: Dict, insights_data: List[Dict], query: str) -> List[Dict]:
        """Prepare conversation context for OpenRouter."""
        messages = [
            {
                'role': 'system',
                'content': self.automotive_context
            }
        ]
        
        # Validate inputs
        if not isinstance(dealer_context, dict):
            dealer_context = {}
        if not isinstance(insights_data, list):
            insights_data = []
        if not isinstance(query, str):
            query = str(query)
        
        # Add dealer context if available
        if dealer_context.get('preferences') and isinstance(dealer_context['preferences'], dict):
            try:
                context_msg = f"Dealer preferences: {json.dumps(dealer_context['preferences'])}"
                context_msg = self._mask_pii(context_msg)
                messages.append({
                    'role': 'system',
                    'content': f"Context: {context_msg}"
                })
            except (TypeError, ValueError) as e:
                logger.warning(f"Error serializing dealer context: {e}")
        
        # Add recent insights data
        if insights_data:
            # Combine recent insights into context
            recent_insights = []
            for insight in insights_data[:3]:  # Use last 3 insights for context
                if isinstance(insight, dict) and 'insights' in insight:
                    recent_insights.append(insight['insights'])
            
            if recent_insights:
                try:
                    insights_context = f"Recent dealership data insights: {json.dumps(recent_insights)}"
                    # Mask PII before adding to context
                    insights_context = self._mask_pii(insights_context)
                    # Limit context size
                    if len(insights_context) > 5000:
                        insights_context = insights_context[:5000] + "...[truncated]"
                    messages.append({
                        'role': 'system',
                        'content': insights_context
                    })
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error serializing insights context: {e}")
        
        # Add the user query
        masked_query = self._mask_pii(query)
        # Limit query length
        if len(masked_query) > 2000:
            masked_query = masked_query[:2000] + "...[truncated]"
        
        messages.append({
            'role': 'user',
            'content': masked_query
        })
        
        return messages
    
    def answer_question(self, query: str, dealer_context: Dict, insights_data: List[Dict], model: Optional[str] = None) -> Dict[str, Any]:
        """Answer a natural language question about automotive data."""
        try:
            # Input validation
            if not query or not isinstance(query, str) or len(query.strip()) == 0:
                return {
                    'error': 'Query cannot be empty',
                    'status': 'failed'
                }
            
            if len(query) > 2000:
                return {
                    'error': 'Query too long',
                    'status': 'failed'
                }
            # Prepare conversation context
            messages = self._prepare_context(dealer_context, insights_data, query)
            
            # Make API request
            response = self._make_request(messages, model)
            
            if not response:
                return {
                    'error': 'Failed to get response from OpenRouter API',
                    'status': 'failed'
                }
            
            # Extract response content
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                
                # Try to parse as JSON first
                try:
                    parsed_response = json.loads(content)
                    if isinstance(parsed_response, dict):
                        # Validate required fields
                        if 'summary' not in parsed_response:
                            parsed_response['summary'] = 'Analysis completed'
                        if 'value_insights' not in parsed_response:
                            parsed_response['value_insights'] = []
                        if 'actionable_flags' not in parsed_response:
                            parsed_response['actionable_flags'] = []
                        if 'confidence' not in parsed_response:
                            parsed_response['confidence'] = 'medium'
                        
                        return {
                            'response': parsed_response,
                            'raw_content': content,
                            'model_used': response.get('model', model or self.default_model),
                            'status': 'success'
                        }
                except json.JSONDecodeError:
                    pass
                
                # If not JSON, return as plain text with structured format
                return {
                    'response': {
                        'summary': content[:200] + '...' if len(content) > 200 else content,
                        'value_insights': [content],
                        'actionable_flags': [],
                        'confidence': 'medium'
                    },
                    'raw_content': content,
                    'model_used': response.get('model', model or self.default_model),
                    'status': 'success'
                }
            else:
                return {
                    'error': 'No response content received',
                    'status': 'failed'
                }
                
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def generate_insights_summary(self, insights_data: List[Dict], dealer_context: Dict) -> Dict[str, Any]:
        """Generate a summary of recent insights for a dealer."""
        try:
            if not insights_data:
                return {
                    'response': {
                        'summary': 'No recent data available for analysis.',
                        'value_insights': [],
                        'actionable_flags': ['Upload recent sales data for analysis'],
                        'confidence': 'low'
                    },
                    'status': 'success'
                }
            
            # Create summary query
            summary_query = "Please provide a comprehensive summary of the recent automotive dealership performance based on the available data insights."
            
            return self.answer_question(summary_query, dealer_context, insights_data)
            
        except Exception as e:
            logger.error(f"Error generating insights summary: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from OpenRouter."""
        try:
            url = f"{self.base_url}/models"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                models_data = response.json()
                if 'data' in models_data:
                    return [model['id'] for model in models_data['data']]
            
            # Return default models if API call fails
            return [
                'anthropic/claude-3-haiku',
                'anthropic/claude-3-sonnet',
                'openai/gpt-4o-mini',
                'openai/gpt-4o'
            ]
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return ['anthropic/claude-3-haiku']


if __name__ == '__main__':
    # Test the OpenRouter client
    config = {
        'OPENROUTER_API_KEY': 'test_key'
    }
    
    client = OpenRouterClient(config)
    print("OpenRouter client initialized successfully")

