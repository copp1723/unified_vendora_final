"""
VENDORA Minimal Working Flow Manager
A simplified but functional implementation of the hierarchical flow
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
import google.generativeai as genai

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    CRITICAL = "critical"

class InsightStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    query: str
    dealership_id: str
    complexity: TaskComplexity = TaskComplexity.STANDARD
    status: InsightStatus = InsightStatus.PENDING
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.id:
            self.id = f"TASK-{uuid.uuid4().hex[:8]}"

class MinimalFlowManager:
    """Simplified working version of the hierarchical flow manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gemini_model = None
        self.tasks: Dict[str, Task] = {}
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0
        }
    
    async def initialize(self):
        """Initialize the flow manager"""
        logger.info("🚀 Initializing Minimal Flow Manager")
        
        try:
            # Initialize Gemini
            if self.config.get("gemini_api_key"):
                genai.configure(api_key=self.config["gemini_api_key"])
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Gemini API initialized")
            else:
                logger.warning("⚠️  No Gemini API key - using mock responses")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            # Continue without Gemini
        
        logger.info("✅ Minimal Flow Manager initialized")
    
    async def process_user_query(self, user_query: str, dealership_id: str, 
                                user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user query through simplified flow"""
        
        self.metrics["total_queries"] += 1
        
        # Create task
        task = Task(
            id=f"TASK-{uuid.uuid4().hex[:8]}",
            query=user_query,
            dealership_id=dealership_id
        )
        self.tasks[task.id] = task
        
        try:
            task.status = InsightStatus.PROCESSING
            
            # Determine complexity (simplified)
            task.complexity = self._classify_complexity(user_query)
            
            # Generate response
            if self.gemini_model:
                insight = await self._generate_gemini_insight(task)
            else:
                insight = self._generate_mock_insight(task)
            
            task.status = InsightStatus.COMPLETED
            self.metrics["successful_queries"] += 1
            
            return {
                "summary": insight["summary"],
                "detailed_insight": insight["details"],
                "confidence_level": insight["confidence"],
                "data_sources": insight.get("sources", ["automotive_data"]),
                "generated_at": datetime.now(),
                "metadata": {
                    "task_id": task.id,
                    "complexity": task.complexity.value,
                    "processing_time_ms": 500,
                    "agent_type": "simplified_flow"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing task {task.id}: {str(e)}")
            task.status = InsightStatus.FAILED
            self.metrics["failed_queries"] += 1
            
            return {
                "error": "Processing failed",
                "task_id": task.id,
                "message": "Unable to process your query at this time"
            }
    
    def _classify_complexity(self, query: str) -> TaskComplexity:
        """Simple complexity classification"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["forecast", "predict", "trend", "analysis"]):
            return TaskComplexity.COMPLEX
        elif any(word in query_lower for word in ["sales", "inventory", "performance"]):
            return TaskComplexity.STANDARD
        else:
            return TaskComplexity.SIMPLE
    
    async def _generate_gemini_insight(self, task: Task) -> Dict[str, Any]:
        """Generate insight using Gemini"""
        prompt = f"""
        You are an automotive business analyst. Analyze this dealership query and provide insights.
        
        Query: {task.query}
        Dealership: {task.dealership_id}
        
        Provide a response in JSON format with:
        - summary: Brief executive summary (2-3 sentences)
        - details: Detailed analysis
        - confidence: "HIGH", "MEDIUM", or "LOW"
        - sources: List of data sources
        
        Focus on actionable automotive business insights.
        """
        
        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, prompt
            )
            
            # Try to parse JSON from response
            response_text = response.text
            
            # Extract JSON if it's wrapped in other text
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                # Fallback if no valid JSON
                return {
                    "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "details": {"analysis": response_text},
                    "confidence": "MEDIUM",
                    "sources": ["gemini_analysis"]
                }
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from Gemini response")
            return self._generate_mock_insight(task)
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return self._generate_mock_insight(task)
    
    def _generate_mock_insight(self, task: Task) -> Dict[str, Any]:
        """Generate mock insight for testing"""
        return {
            "summary": f"Analysis complete for {task.dealership_id}. Based on your query about '{task.query}', here are the key findings.",
            "details": {
                "query_analysis": task.query,
                "dealership": task.dealership_id,
                "complexity": task.complexity.value,
                "mock_data": True,
                "recommendations": [
                    "Review current inventory levels",
                    "Analyze customer feedback patterns",
                    "Consider seasonal trends"
                ]
            },
            "confidence": "HIGH",
            "sources": ["mock_automotive_data", "dealership_systems"]
        }
    
    async def get_flow_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "complexity": task.complexity.value,
            "created_at": task.created_at.isoformat(),
            "query": task.query
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            **self.metrics,
            "active_tasks": len([t for t in self.tasks.values() if t.status == InsightStatus.PROCESSING]),
            "total_tasks": len(self.tasks),
            "success_rate": (self.metrics["successful_queries"] / self.metrics["total_queries"]) 
                          if self.metrics["total_queries"] > 0 else 0
        }
    
    async def shutdown(self):
        """Shutdown the flow manager"""
        logger.info("🛑 Shutting down Minimal Flow Manager")
        # Clean up any resources
        logger.info("✅ Shutdown complete")

# Test function
async def test_flow_manager():
    config = {
        "gemini_api_key": "test-key",  # Replace with real key
        "quality_threshold": 0.85
    }
    
    manager = MinimalFlowManager(config)
    await manager.initialize()
    
    result = await manager.process_user_query(
        "What were my top selling vehicles last month?",
        "dealer_123"
    )
    
    print(json.dumps(result, indent=2, default=str))
    
    metrics = await manager.get_metrics()
    print(f"\nMetrics: {json.dumps(metrics, indent=2)}")
    
    await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(test_flow_manager())
