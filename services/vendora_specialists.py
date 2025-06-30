"""
VENDORA L2 Specialist Agents - Fixed Implementation
The "Workshop" - domain experts with secure SQL generation and proper error handling
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import google.generativeai as genai
from google.cloud import bigquery
import time
import re
from tenacity import retry, stop_after_attempt, wait_exponential

from .hierarchical_flow_manager import AnalyticalTask, DraftInsight
from src.security.input_validator import InputValidator, SecureQueryBuilder
from src.cache.redis_cache import RedisCache
from src.reliability.circuit_breaker import circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)


class BaseSpecialistAgent:
    """Base class for L2 specialist agents with improved security and reliability"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.gemini_model = None
        self.bigquery_client = None
        self.capabilities = []
        self.redis_cache: Optional[RedisCache] = None
        
    async def initialize(self):
        """Initialize the specialist agent"""
        logger.info(f"🔧 Initializing L2 Specialist: {self.agent_id}")
        
        try:
            # Initialize Gemini
<<<<<<< HEAD
            genai.configure(api_key=self.config.get("gemini_api_key"))
=======
>>>>>>> b5dd85a (Organize frontend files and remove duplicates)
            self.gemini_model = genai.GenerativeModel(
                'gemini-pro',
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                    "top_k": 40,
                    "top_p": 0.95,
                }
            )
            
            # Initialize BigQuery
            if self.config.get('service_account_path'):
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    self.config['service_account_path']
                )
                self.bigquery_client = bigquery.Client(
                    credentials=credentials,
                    project=self.config.get('bigquery_project')
                )
            else:
                self.bigquery_client = bigquery.Client(
                    project=self.config.get('bigquery_project')
                )
            
            # Initialize Redis cache
            redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379')
            self.redis_cache = RedisCache(redis_url)
            await self.redis_cache.connect()
            
            logger.info(f"✅ L2 Specialist {self.agent_id} initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize specialist {self.agent_id}: {str(e)}")
            # Continue without BigQuery for development
            self.bigquery_client = None
            logger.warning(f"Specialist {self.agent_id} running in mock mode")
    
    def _sanitize_table_name(self, dealership_id: str, table_type: str) -> str:
        """Sanitize table name to prevent SQL injection"""
        # Use secure validator
        clean_dealership = InputValidator.validate_dealership_id(dealership_id)
        project = self.config.get('bigquery_project', 'vendora_analytics')
        dataset = f"dealership_{clean_dealership}"
        
        return InputValidator.sanitize_table_name(project, dataset, table_type)
    
    async def _get_table_schema(self, dealership_id: str, table_name: str) -> List[Dict[str, str]]:
        """Get actual table schema from BigQuery"""
        if not self.bigquery_client:
            # Return mock schema for development
            return self._get_mock_schema(table_name)
        
        try:
            dataset_id = f"dealership_{dealership_id}"
            table_ref = self.bigquery_client.dataset(dataset_id).table(table_name)
            table = self.bigquery_client.get_table(table_ref)
            
            return [
                {"name": field.name, "type": field.field_type, "mode": field.mode}
                for field in table.schema
            ]
        except Exception as e:
            logger.warning(f"Could not fetch schema for {table_name}: {str(e)}")
            return self._get_mock_schema(table_name)
    
    def _get_mock_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get mock schema for development/testing"""
        schemas = {
            "sales": [
                {"name": "sale_id", "type": "STRING", "mode": "REQUIRED"},
                {"name": "vehicle_id", "type": "STRING", "mode": "REQUIRED"},
                {"name": "customer_id", "type": "STRING", "mode": "REQUIRED"},
                {"name": "sale_date", "type": "DATE", "mode": "REQUIRED"},
                {"name": "sale_amount", "type": "FLOAT64", "mode": "REQUIRED"},
                {"name": "salesperson_id", "type": "STRING", "mode": "NULLABLE"}
            ],
            "inventory": [
                {"name": "vehicle_id", "type": "STRING", "mode": "REQUIRED"},
                {"name": "make", "type": "STRING", "mode": "REQUIRED"},
                {"name": "model", "type": "STRING", "mode": "REQUIRED"},
                {"name": "year", "type": "INTEGER", "mode": "REQUIRED"},
                {"name": "vin", "type": "STRING", "mode": "REQUIRED"},
                {"name": "status", "type": "STRING", "mode": "REQUIRED"},
                {"name": "acquisition_date", "type": "DATE", "mode": "NULLABLE"},
                {"name": "acquisition_cost", "type": "FLOAT64", "mode": "NULLABLE"}
            ]
        }
        return schemas.get(table_name, [])
    
    async def generate_insight(self, task: AnalyticalTask) -> DraftInsight:
        """Generate analytical insight for the task"""
        raise NotImplementedError("Subclasses must implement generate_insight")
    
    async def revise_insight(self, task: AnalyticalTask, 
                           original_insight: DraftInsight,
                           feedback: Dict[str, Any]) -> DraftInsight:
        """Revise insight based on Master Analyst feedback"""
        logger.info(f"📝 Revising insight for task {task.id} based on feedback")
        
        # Extract revision requirements
        revision_prompt = f"""
        Revise the following analytical insight based on the feedback provided:
        
        Original Query: {task.user_query}
        Original Insight: {original_insight.content}
        
        Feedback from Quality Review:
        {feedback}
        
        Please address all the issues mentioned and provide an improved analysis.
        Focus on:
        1. Accuracy of data interpretation
        2. Completeness of analysis
        3. Clarity of conclusions
        4. Actionability of recommendations
        
        Provide the revised insight in the same JSON format as before.
        """
        
        try:
            start_time = time.time()
            
            # Generate revised content
            revised_content = await self._call_gemini(revision_prompt)
            revised_data = self._parse_json_response(revised_content)
            
            # Re-run any SQL queries if needed
            sql_queries = original_insight.sql_queries
            if feedback.get("data_issues"):
                # Re-generate queries with feedback
                new_queries = []
                for i, query in enumerate(sql_queries):
                    new_query = await self._revise_sql_query(
                        task, query, feedback.get("data_issues", {})
                    )
                    new_queries.append(new_query)
                sql_queries = new_queries
            
            # Create revised insight
            revised_insight = DraftInsight(
                task_id=task.id,
                agent_id=self.agent_id,
                content=revised_data,
                sql_queries=sql_queries,
                data_sources=original_insight.data_sources,
                confidence_score=min(original_insight.confidence_score * 1.1, 0.95),  # Slight boost
                generation_time_ms=int((time.time() - start_time) * 1000),
                methodology={
                    **original_insight.methodology,
                    "revision_reason": feedback.get("summary", "Quality improvements"),
                    "revision_number": 1
                }
            )
            
            return revised_insight
            
        except Exception as e:
            logger.error(f"❌ Error revising insight: {str(e)}")
            # Return original with lower confidence
            original_insight.confidence_score *= 0.8
            return original_insight
    
    async def _revise_sql_query(self, task: AnalyticalTask, 
                              original_query: str, 
                              feedback: Dict[str, Any]) -> str:
        """Revise a SQL query based on feedback"""
        revision_prompt = f"""
        Revise this BigQuery SQL query based on the feedback.
        
        Original Query:
        {original_query}
        
        Feedback: {feedback}
        
        Requirements:
        1. Use parameterized queries with @dealership_id parameter
        2. Include proper date filtering
        3. Add appropriate aggregations
        4. Ensure all table names use backticks
        
        Generate ONLY the revised SQL query.
        """
        
        revised_query = await self._call_gemini(revision_prompt)
        return self._clean_sql_query(revised_query)
    
    async def _generate_sql_query(self, task: AnalyticalTask, 
                                query_purpose: str) -> Tuple[str, Dict[str, Any]]:
        """Generate secure SQL query for the analysis"""
        
        # Validate inputs first
        clean_dealership = InputValidator.validate_dealership_id(task.dealership_id)
        clean_query = InputValidator.validate_user_query(task.user_query)
        
        # Use secure query builder for common patterns
        query_builder = SecureQueryBuilder(self.config.get('bigquery_project', 'vendora_analytics'))
        
        # Check for common query patterns
        if "sales" in query_purpose.lower():
            date_filter = None
            if "last month" in clean_query.lower():
                date_filter = "last_month"
            elif "last week" in clean_query.lower():
                date_filter = "last_week"
            elif "today" in clean_query.lower():
                date_filter = "today"
            
            sql_query, params = query_builder.build_sales_query(clean_dealership, date_filter)
        elif "inventory" in query_purpose.lower():
            status_filter = None
            if "available" in clean_query.lower():
                status_filter = "available"
            elif "sold" in clean_query.lower():
                status_filter = "sold"
            
            sql_query, params = query_builder.build_inventory_query(clean_dealership, status_filter)
        else:
            # Fallback to AI generation with validation
            sql_query = await self._generate_ai_sql_query(task, query_purpose)
            params = {"dealership_id": clean_dealership}
        
        # Validate generated SQL
        sql_query = InputValidator.validate_sql_query(sql_query)
        
        # Check Redis cache first
        if self.redis_cache:
            cached_result = await self.redis_cache.get(sql_query, clean_dealership)
            if cached_result:
                return sql_query, cached_result
        
        # Execute query with timeout and circuit breaker
        try:
            if self.bigquery_client:
                result = await self._execute_bigquery_with_circuit_breaker(
                    sql_query, clean_dealership, params
                )
                
                # Cache successful results
                if result["success"] and self.redis_cache:
                    await self.redis_cache.set(sql_query, clean_dealership, result, ttl=1800)  # 30 min cache
                
                return sql_query, result
            else:
                # Mock mode
                return sql_query, self._get_mock_query_result(query_purpose)
                
        except Exception as e:
            logger.error(f"❌ SQL execution error: {str(e)}")
            return sql_query, {"success": False, "error": str(e), "data": []}
    
    def _clean_sql_query(self, query: str) -> str:
        """Clean and validate SQL query"""
        # Remove markdown code blocks
        query = query.strip().replace("```sql", "").replace("```", "").strip()
        
        # Use secure validator
        return InputValidator.validate_sql_query(query)
    
    async def _generate_ai_sql_query(self, task: AnalyticalTask, query_purpose: str) -> str:
        """Generate SQL query using AI with security validation"""
        # Get schemas for available tables
        schemas = {}
        for table in ["sales", "inventory", "customers", "service"]:
            schemas[table] = await self._get_table_schema(task.dealership_id, table)
        
        # Build schema description for Gemini
        schema_desc = "\n".join([
            f"Table: {self._sanitize_table_name(task.dealership_id, table)}\nColumns: {', '.join([f'{col['name']} ({col['type']})' for col in schema])}"
            for table, schema in schemas.items() if schema
        ])
        
        sql_prompt = f"""
        Generate a BigQuery SQL query for the following automotive dealership analysis:
        
        Query Purpose: {query_purpose}
        User Query: {task.user_query}
        
        Available tables and schemas:
        {schema_desc}
        
        Requirements:
        1. Use parameterized query with @dealership_id parameter
        2. All table names must use backticks
        3. Include appropriate WHERE clauses for data filtering
        4. Use proper date functions for time-based queries
        5. Include LIMIT clause if querying large datasets
        6. ONLY use SELECT statements - no INSERT, UPDATE, DELETE, DROP, etc.
        
        Generate ONLY the SQL query, no explanations.
        """
        
        sql_query = await self._call_gemini(sql_prompt)
        return self._clean_sql_query(sql_query)
    
    def _get_mock_query_result(self, query_purpose: str) -> Dict[str, Any]:
        """Generate mock query results for development"""
        if "sales" in query_purpose.lower():
            return {
                "success": True,
                "data": [
                    {"vehicle_id": "V001", "make": "Toyota", "model": "Camry", "sales_count": 15, "total_revenue": 450000},
                    {"vehicle_id": "V002", "make": "Honda", "model": "Accord", "sales_count": 12, "total_revenue": 384000},
                    {"vehicle_id": "V003", "make": "Ford", "model": "F-150", "sales_count": 10, "total_revenue": 500000}
                ],
                "row_count": 3
            }
        else:
            return {
                "success": True,
                "data": [{"metric": "sample_value", "count": 100}],
                "row_count": 1
            }
    
    @circuit_breaker("gemini_api", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30))
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with circuit breaker and retry logic"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from Gemini response with error handling"""
        import json
        
        # Try to extract JSON from response
        try:
            # First try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from response")
            
        # Return default structure
        return {
            "summary": "Analysis could not be parsed",
            "insights": ["Please try rephrasing your query"],
            "recommendations": ["Ensure your query is specific and clear"]
        }
    
    @circuit_breaker("bigquery_api", CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60))
    async def _execute_bigquery_with_circuit_breaker(self, sql_query: str, dealership_id: str, params: Dict) -> Dict:
        """Execute BigQuery with circuit breaker protection"""
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("dealership_id", "STRING", dealership_id)
            ] + [bigquery.ScalarQueryParameter(k, "STRING", v) for k, v in params.items() if k != "dealership_id"],
            use_query_cache=True,
            timeout_ms=10000
        )
        
        query_job = self.bigquery_client.query(sql_query, job_config=job_config)
        results = query_job.result(timeout=10)
        
        data = [dict(row) for row in results]
        
        if len(data) > 1000:
            data = data[:1000]
            logger.warning("Query results truncated to 1000 rows")
        
        return {"success": True, "data": data, "row_count": len(data)}
    
    async def shutdown(self):
        """Shutdown the specialist agent"""
        logger.info(f"🛑 Shutting down L2 Specialist: {self.agent_id}")
        if self.bigquery_client:
            self.bigquery_client.close()
        if self.redis_cache:
            await self.redis_cache.disconnect()


class DataAnalystAgent(BaseSpecialistAgent):
    """Standard Data Analyst Agent for routine queries"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("data_analyst", config)
        self.capabilities = [
            "standard_reporting",
            "kpi_analysis",
            "trend_detection",
            "comparative_analysis",
            "data_aggregation"
        ]
    
    async def generate_insight(self, task: AnalyticalTask) -> DraftInsight:
        """Generate analytical insight using standard analysis techniques"""
        logger.info(f"📊 Data Analyst generating insight for task {task.id}")
        
        start_time = time.time()
        
        try:
            # Step 1: Generate SQL queries for required data
            sql_queries = []
            query_results = []
            
            # Limit queries to prevent overload
            for i, data_source in enumerate(task.required_data[:3]):  # Max 3 data sources
                query_purpose = f"Extract {data_source} data for: {task.user_query}"
                sql_query, result = await self._generate_sql_query(task, query_purpose)
                sql_queries.append(sql_query)
                query_results.append(result)
            
            # Step 2: Analyze the data using Gemini
            # Truncate data for Gemini to prevent token limit issues
            truncated_results = []
            for result in query_results:
                if result.get("success") and result.get("data"):
                    truncated = {
                        **result,
                        "data": result["data"][:10],  # First 10 rows
                        "truncated": len(result["data"]) > 10
                    }
                    truncated_results.append(truncated)
                else:
                    truncated_results.append(result)
            
            analysis_prompt = f"""
            Analyze the following automotive dealership data to answer this query:
            "{task.user_query}"
            
            Data retrieved:
            {truncated_results}
            
            Provide a comprehensive analysis including:
            1. Key findings and insights
            2. Relevant metrics and KPIs
            3. Trends or patterns observed
            4. Actionable recommendations
            
            Format your response as JSON:
            {{
                "summary": "Executive summary of findings",
                "key_metrics": {{"metric_name": value}},
                "insights": ["insight1", "insight2"],
                "trends": ["trend1", "trend2"],
                "recommendations": ["recommendation1", "recommendation2"],
                "data_quality_notes": "Any data quality observations"
            }}
            """
            
            analysis_response = await self._call_gemini(analysis_prompt)
            analysis_data = self._parse_json_response(analysis_response)
            
            # Step 3: Calculate confidence score
            confidence_score = self._calculate_confidence(query_results, analysis_data)
            
            # Create draft insight
            draft_insight = DraftInsight(
                task_id=task.id,
                agent_id=self.agent_id,
                content=analysis_data,
                sql_queries=sql_queries,
                data_sources=task.required_data,
                confidence_score=confidence_score,
                generation_time_ms=int((time.time() - start_time) * 1000),
                methodology={
                    "approach": "standard_analysis",
                    "techniques": ["sql_aggregation", "trend_analysis", "kpi_calculation"],
                    "data_points_analyzed": sum(r.get("row_count", 0) for r in query_results if r.get("success")),
                    "queries_executed": len(sql_queries),
                    "data_sources_used": len([r for r in query_results if r.get("success")])
                }
            )
            
            logger.info(f"✅ Data Analyst completed insight for task {task.id} "
                       f"(confidence: {confidence_score:.2f})")
            
            return draft_insight
            
        except Exception as e:
            logger.error(f"❌ Error generating insight: {str(e)}", exc_info=True)
            
            # Return minimal insight on error
            return DraftInsight(
                task_id=task.id,
                agent_id=self.agent_id,
                content={
                    "summary": "Analysis encountered an error",
                    "error": str(e),
                    "recommendations": ["Please try rephrasing your query", "Ensure data is available for the requested period"]
                },
                sql_queries=sql_queries if 'sql_queries' in locals() else [],
                data_sources=task.required_data,
                confidence_score=0.3,
                generation_time_ms=int((time.time() - start_time) * 1000),
                methodology={"approach": "error_recovery"}
            )
    
    def _calculate_confidence(self, query_results: List[Dict[str, Any]], 
                            analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for the insight"""
        confidence = 0.5  # Base confidence
        
        # Check data availability
        successful_queries = sum(1 for r in query_results if r.get("success"))
        total_queries = len(query_results)
        
        if total_queries > 0:
            confidence += 0.2 * (successful_queries / total_queries)
        
        # Check data volume
        total_rows = sum(r.get("row_count", 0) for r in query_results if r.get("success"))
        if total_rows > 100:
            confidence += 0.1
        elif total_rows > 50:
            confidence += 0.05
        elif total_rows == 0:
            confidence -= 0.2
        
        # Check analysis completeness
        if analysis.get("insights") and len(analysis["insights"]) > 2:
            confidence += 0.1
        
        if analysis.get("recommendations") and len(analysis["recommendations"]) > 1:
            confidence += 0.1
        
        if analysis.get("key_metrics") and len(analysis["key_metrics"]) > 0:
            confidence += 0.05
        
        return max(0.1, min(confidence, 0.9))  # Clamp between 0.1 and 0.9


class SeniorAnalystAgent(BaseSpecialistAgent):
    """Senior Data Analyst Agent for complex queries and advanced analytics"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("senior_analyst", config)
        self.capabilities = [
            "predictive_analytics",
            "forecasting",
            "anomaly_detection",
            "optimization",
            "advanced_statistics",
            "machine_learning",
            "strategic_analysis"
        ]
    
    async def generate_insight(self, task: AnalyticalTask) -> DraftInsight:
        """Generate advanced analytical insight using sophisticated techniques"""
        logger.info(f"🎯 Senior Analyst generating advanced insight for task {task.id}")
        
        start_time = time.time()
        
        try:
            # Step 1: Generate comprehensive SQL queries
            sql_queries = []
            query_results = []
            
            # Get historical data for advanced analysis
            historical_query_purpose = f"Extract comprehensive historical data (last 12 months) for advanced analysis: {task.user_query}"
            sql_query, result = await self._generate_sql_query(task, historical_query_purpose)
            sql_queries.append(sql_query)
            query_results.append(result)
            
            # Get additional context data (limit to 2 additional queries)
            for i, data_source in enumerate(task.required_data[:2]):
                context_purpose = f"Extract detailed {data_source} context with statistical aggregations for: {task.user_query}"
                sql_query, result = await self._generate_sql_query(task, context_purpose)
                sql_queries.append(sql_query)
                query_results.append(result)
            
            # Step 2: Perform advanced analysis
            # Prepare data summary for Gemini
            data_summary = self._prepare_data_summary(query_results)
            
            advanced_analysis_prompt = f"""
            Perform advanced data analysis for this automotive dealership query:
            "{task.user_query}"
            
            Data summary:
            {data_summary}
            
            Apply advanced analytical techniques including:
            1. Statistical analysis and confidence intervals
            2. Trend forecasting and predictions
            3. Anomaly detection and outlier analysis
            4. Correlation and causation analysis
            5. Scenario modeling (if applicable)
            6. Risk assessment
            
            Provide a comprehensive analysis in JSON format:
            {{
                "executive_summary": "High-level strategic insights",
                "statistical_analysis": {{
                    "key_statistics": {{}},
                    "confidence_intervals": {{}},
                    "correlations": {{}}
                }},
                "predictions": {{
                    "forecast": {{}},
                    "confidence_level": "percentage",
                    "assumptions": []
                }},
                "anomalies": [
                    {{"description": "", "severity": "high/medium/low", "impact": ""}}
                ],
                "strategic_insights": ["insight1", "insight2"],
                "recommendations": [
                    {{"action": "", "priority": "high/medium/low", "expected_impact": ""}}
                ],
                "risks": [
                    {{"risk": "", "probability": "percentage", "mitigation": ""}}
                ],
                "methodology_notes": "Advanced techniques applied"
            }}
            """
            
            analysis_response = await self._call_gemini(advanced_analysis_prompt)
            analysis_data = self._parse_json_response(analysis_response)
            
            # Step 3: Enhance with predictive modeling (if applicable)
            if any(keyword in task.user_query.lower() for keyword in ["forecast", "predict", "future", "trend"]):
                prediction_data = await self._generate_predictions(task, data_summary)
                if "predictions" not in analysis_data:
                    analysis_data["predictions"] = {}
                analysis_data["predictions"].update(prediction_data)
            
            # Step 4: Calculate senior-level confidence score
            confidence_score = self._calculate_senior_confidence(query_results, analysis_data)
            
            # Create draft insight
            draft_insight = DraftInsight(
                task_id=task.id,
                agent_id=self.agent_id,
                content=analysis_data,
                sql_queries=sql_queries,
                data_sources=task.required_data + ["historical_data", "contextual_data"],
                confidence_score=confidence_score,
                generation_time_ms=int((time.time() - start_time) * 1000),
                methodology={
                    "approach": "advanced_analytics",
                    "techniques": [
                        "statistical_modeling",
                        "predictive_analytics",
                        "anomaly_detection",
                        "correlation_analysis"
                    ],
                    "data_points_analyzed": sum(r.get("row_count", 0) for r in query_results if r.get("success")),
                    "complexity_level": "high",
                    "assumptions": analysis_data.get("predictions", {}).get("assumptions", []),
                    "statistical_methods": ["regression", "time_series", "confidence_intervals"]
                }
            )
            
            logger.info(f"✅ Senior Analyst completed advanced insight for task {task.id} "
                       f"(confidence: {confidence_score:.2f})")
            
            return draft_insight
            
        except Exception as e:
            logger.error(f"❌ Error generating advanced insight: {str(e)}", exc_info=True)
            
            # Return basic insight on error
            return DraftInsight(
                task_id=task.id,
                agent_id=self.agent_id,
                content={
                    "executive_summary": "Advanced analysis encountered limitations",
                    "error": str(e),
                    "recommendations": [
                        {"action": "Simplify the query scope", "priority": "high", "expected_impact": "Better results"},
                        {"action": "Verify data availability", "priority": "medium", "expected_impact": "Complete analysis"}
                    ]
                },
                sql_queries=sql_queries if 'sql_queries' in locals() else [],
                data_sources=task.required_data,
                confidence_score=0.4,
                generation_time_ms=int((time.time() - start_time) * 1000),
                methodology={"approach": "error_recovery", "complexity_level": "reduced"}
            )
    
    def _prepare_data_summary(self, query_results: List[Dict[str, Any]]) -> str:
        """Prepare a concise data summary for Gemini"""
        summary_parts = []
        
        for i, result in enumerate(query_results):
            if result.get("success"):
                data = result.get("data", [])
                summary_parts.append(f"""
                Query {i+1} Results:
                - Rows returned: {result.get('row_count', 0)}
                - Sample data (first 5 rows): {data[:5] if data else 'No data'}
                - Data structure: {list(data[0].keys()) if data else 'Unknown'}
                """)
            else:
                summary_parts.append(f"""
                Query {i+1} Failed: {result.get('error', 'Unknown error')}
                """)
        
        return "\n".join(summary_parts)
    
    async def _generate_predictions(self, task: AnalyticalTask, 
                                  data_summary: str) -> Dict[str, Any]:
        """Generate predictive analytics"""
        prediction_prompt = f"""
        Based on the historical automotive dealership data provided, generate
        predictive analytics for: {task.user_query}
        
        Data summary: {data_summary}
        
        Provide predictions including:
        1. Forecast values with confidence intervals (next 3 months)
        2. Key assumptions made
        3. Risk factors that could affect predictions
        4. Recommended monitoring metrics
        
        Format as JSON with specific numeric predictions where possible.
        """
        
        prediction_response = await self._call_gemini(prediction_prompt)
        predictions = self._parse_json_response(prediction_response)
        
        # Ensure proper structure
        if not isinstance(predictions, dict):
            predictions = {"error": "Could not generate predictions"}
        
        return predictions
    
    def _calculate_senior_confidence(self, query_results: List[Dict[str, Any]], 
                                   analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for senior-level analysis"""
        confidence = 0.6  # Higher base confidence for senior analyst
        
        # Data quality and volume
        successful_queries = sum(1 for r in query_results if r.get("success"))
        total_queries = len(query_results)
        
        if total_queries > 0:
            confidence += 0.15 * (successful_queries / total_queries)
        
        # Data volume bonus
        total_rows = sum(r.get("row_count", 0) for r in query_results if r.get("success"))
        if total_rows > 1000:
            confidence += 0.1
        elif total_rows > 500:
            confidence += 0.05
        elif total_rows < 50:
            confidence -= 0.1
        
        # Analysis sophistication
        if analysis.get("statistical_analysis"):
            confidence += 0.05
        
        if analysis.get("predictions") and analysis["predictions"].get("forecast"):
            confidence += 0.05
        
        if analysis.get("anomalies") and len(analysis["anomalies"]) > 0:
            confidence += 0.05
        
        if analysis.get("strategic_insights") and len(analysis["strategic_insights"]) > 1:
            confidence += 0.05
        
        return max(0.2, min(confidence, 0.95))  # Clamp between 0.2 and 0.95
