"""
VENDORA L1 Orchestrator
The "Front Desk" - handles task ingestion, analysis, and intelligent dispatch
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from dataclasses import dataclass

from .hierarchical_flow_manager import AnalyticalTask, TaskComplexity, ValidatedInsight

logger = logging.getLogger(__name__)


class VendoraOrchestrator:
    """
    Level 1 Agent - The Orchestrator
    Acts as the primary interface and conscious mind of the system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gemini_model = None
        self.task_patterns = self._load_task_patterns()
        self.dispatch_rules = self._load_dispatch_rules()
        
    async def initialize(self):
        """Initialize the orchestrator"""
        logger.info("🎯 Initializing L1 Orchestrator")
        
        # Initialize Gemini
        genai.configure(api_key=self.config.get("gemini_api_key"))
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        logger.info("✅ L1 Orchestrator initialized")
    
    def _load_task_patterns(self) -> Dict[str, Any]:
        """Load patterns for task classification"""
        return {
            "simple_queries": [
                "current inventory",
                "today's sales",
                "customer count",
                "basic metrics",
                "simple lookup"
            ],
            "standard_queries": [
                "monthly performance",
                "sales trends",
                "inventory analysis",
                "customer behavior",
                "comparative analysis"
            ],
            "complex_queries": [
                "forecast",
                "predictive",
                "multi-year",
                "optimization",
                "what-if analysis",
                "machine learning",
                "anomaly detection"
            ],
            "critical_queries": [
                "financial impact",
                "strategic decision",
                "risk assessment",
                "compliance audit",
                "major investment"
            ]
        }
    
    def _load_dispatch_rules(self) -> Dict[TaskComplexity, str]:
        """Load dispatch rules for agent assignment"""
        return {
            TaskComplexity.SIMPLE: "data_analyst",
            TaskComplexity.STANDARD: "data_analyst",
            TaskComplexity.COMPLEX: "senior_analyst",
            TaskComplexity.CRITICAL: "senior_analyst"
        }
    
    async def analyze_and_dispatch(self, task: AnalyticalTask) -> Dict[str, Any]:
        """
        Analyze the task and determine dispatch strategy
        
        Returns:
            Dict containing:
            - complexity: TaskComplexity enum
            - assigned_agent: str (agent ID)
            - required_data: List[str] (data sources needed)
            - analysis_approach: str (methodology to use)
        """
        logger.info(f"🔍 Analyzing task {task.id}: {task.user_query[:50]}...")
        
        # Use Gemini to analyze the query
        analysis_prompt = f"""
        Analyze this automotive dealership query and provide a structured analysis:
        
        Query: {task.user_query}
        Dealership: {task.dealership_id}
        Context: {task.context}
        
        Determine:
        1. Complexity level (simple/standard/complex/critical)
        2. Required data sources (inventory/sales/customers/service/finance)
        3. Time range needed
        4. Key metrics to calculate
        5. Analysis methodology
        
        Respond in JSON format:
        {{
            "complexity": "simple|standard|complex|critical",
            "data_sources": ["source1", "source2"],
            "time_range": "description",
            "key_metrics": ["metric1", "metric2"],
            "methodology": "description"
        }}
        """
        
        try:
            response = await self._call_gemini(analysis_prompt)
            analysis = self._parse_json_response(response)
            
            # Determine complexity
            complexity = self._determine_complexity(task.user_query, analysis)
            
            # Determine assigned agent
            assigned_agent = self.dispatch_rules.get(complexity, "data_analyst")
            
            # Extract required data sources
            required_data = analysis.get("data_sources", ["sales", "inventory"])
            
            # Build dispatch result
            dispatch_result = {
                "complexity": complexity,
                "assigned_agent": assigned_agent,
                "required_data": required_data,
                "analysis_approach": analysis.get("methodology", "standard_analysis"),
                "time_range": analysis.get("time_range", "last_30_days"),
                "key_metrics": analysis.get("key_metrics", [])
            }
            
            logger.info(f"✅ Task {task.id} classified as {complexity.value}, "
                       f"assigned to {assigned_agent}")
            
            return dispatch_result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing task {task.id}: {str(e)}")
            
            # Fallback to pattern matching
            complexity = self._fallback_complexity_detection(task.user_query)
            
            return {
                "complexity": complexity,
                "assigned_agent": self.dispatch_rules[complexity],
                "required_data": ["sales", "inventory"],  # Default
                "analysis_approach": "standard_analysis",
                "time_range": "last_30_days",
                "key_metrics": []
            }
    
    def _determine_complexity(self, query: str, analysis: Dict[str, Any]) -> TaskComplexity:
        """Determine task complexity based on query and analysis"""
        query_lower = query.lower()
        
        # Check analysis result first
        if analysis.get("complexity"):
            complexity_map = {
                "simple": TaskComplexity.SIMPLE,
                "standard": TaskComplexity.STANDARD,
                "complex": TaskComplexity.COMPLEX,
                "critical": TaskComplexity.CRITICAL
            }
            return complexity_map.get(analysis["complexity"], TaskComplexity.STANDARD)
        
        # Pattern-based detection
        return self._fallback_complexity_detection(query)
    
    def _fallback_complexity_detection(self, query: str) -> TaskComplexity:
        """Fallback pattern-based complexity detection"""
        query_lower = query.lower()
        
        # Check patterns
        for pattern in self.task_patterns["critical_queries"]:
            if pattern in query_lower:
                return TaskComplexity.CRITICAL
        
        for pattern in self.task_patterns["complex_queries"]:
            if pattern in query_lower:
                return TaskComplexity.COMPLEX
        
        for pattern in self.task_patterns["simple_queries"]:
            if pattern in query_lower:
                return TaskComplexity.SIMPLE
        
        # Default to standard
        return TaskComplexity.STANDARD
    
    async def format_user_response(self, validated_insight: ValidatedInsight) -> Dict[str, Any]:
        """
        Format the validated insight for user delivery
        """
        logger.info(f"📤 Formatting response for task {validated_insight.task_id}")
        
        # Use Gemini to create a natural language summary
        summary_prompt = f"""
        Create a clear, professional summary of this automotive dealership insight
        for a business user. Make it actionable and easy to understand.
        
        Insight data: {validated_insight.final_content}
        Data sources: {validated_insight.draft_insight.data_sources}
        Confidence: {validated_insight.quality_score}
        
        Format the response with:
        1. A brief executive summary (2-3 sentences)
        2. Key findings (bullet points)
        3. Recommended actions (if applicable)
        
        Keep the tone professional but conversational.
        """
        
        try:
            summary = await self._call_gemini(summary_prompt)
            
            return {
                "summary": summary,
                "detailed_insight": validated_insight.final_content,
                "data_visualization": self._prepare_visualization_config(
                    validated_insight.final_content
                ),
                "confidence_level": self._format_confidence(validated_insight.quality_score),
                "data_sources": validated_insight.draft_insight.data_sources,
                "generated_at": validated_insight.approval_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error formatting response: {str(e)}")
            
            # Fallback formatting
            return validated_insight.to_user_response()
    
    def _prepare_visualization_config(self, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare visualization configuration based on insight data"""
        # Determine best visualization type
        if "trend" in str(insight_data).lower():
            return {
                "type": "line_chart",
                "config": {
                    "title": "Trend Analysis",
                    "x_axis": "Time Period",
                    "y_axis": "Value"
                }
            }
        elif "comparison" in str(insight_data).lower():
            return {
                "type": "bar_chart",
                "config": {
                    "title": "Comparative Analysis",
                    "orientation": "vertical"
                }
            }
        elif "distribution" in str(insight_data).lower():
            return {
                "type": "pie_chart",
                "config": {
                    "title": "Distribution Analysis"
                }
            }
        else:
            return {
                "type": "table",
                "config": {
                    "title": "Data Summary"
                }
            }
    
    def _format_confidence(self, score: float) -> str:
        """Format confidence score for user display"""
        if score >= 0.95:
            return "Very High"
        elif score >= 0.85:
            return "High"
        elif score >= 0.70:
            return "Moderate"
        elif score >= 0.50:
            return "Low"
        else:
            return "Very Low"
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response"""
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini response")
        
        return {}
    
    async def shutdown(self):
        """Shutdown the orchestrator"""
        logger.info("🛑 Shutting down L1 Orchestrator")
        # Cleanup resources if needed
