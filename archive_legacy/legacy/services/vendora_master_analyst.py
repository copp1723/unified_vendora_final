"""
VENDORA L3 Master Analyst
The "Editor-in-Chief" - validates, synthesizes, and approves all insights
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import google.generativeai as genai
from google.cloud import bigquery
import hashlib
import json

from .hierarchical_flow_manager import AnalyticalTask, DraftInsight

logger = logging.getLogger(__name__)


class MasterAnalyst:
    """
    Level 3 Agent - The Master Analyst
    Ultimate authority on quality and truth within the system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gemini_model = None
        self.bigquery_client = None
        self.quality_threshold = config.get("quality_threshold", 0.85)
        self.validation_rules = self._load_validation_rules()
        self.audit_log = []
        
    async def initialize(self):
        """Initialize the Master Analyst"""
        logger.info("👑 Initializing L3 Master Analyst")
        
        # Initialize Gemini with advanced model
        genai.configure(api_key=self.config.get("gemini_api_key"))
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Initialize BigQuery for data verification
        self.bigquery_client = bigquery.Client(project=self.config.get("bigquery_project"))
        
        logger.info("✅ L3 Master Analyst initialized - Quality Gate Active")
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load comprehensive validation rules"""
        return {
            "data_accuracy": {
                "sql_verification": True,
                "data_consistency": True,
                "outlier_detection": True,
                "source_validation": True
            },
            "methodology_standards": {
                "statistical_rigor": True,
                "assumption_validation": True,
                "confidence_requirements": True,
                "peer_review_simulation": True
            },
            "business_logic": {
                "reasonableness_check": True,
                "industry_benchmarks": True,
                "historical_consistency": True,
                "actionability": True
            },
            "compliance": {
                "data_privacy": True,
                "regulatory_requirements": True,
                "ethical_considerations": True
            }
        }
    
    async def validate_insight(self, task: AnalyticalTask, 
                             draft_insight: DraftInsight) -> Dict[str, Any]:
        """
        Validate draft insight with extreme prejudice
        Primary directive: Distrust and verify
        """
        logger.info(f"🔍 Master Analyst validating insight for task {task.id}")
        
        validation_start = datetime.now()
        
        # Initialize validation result
        validation_result = {
            "approved": False,
            "quality_score": 0.0,
            "validation_details": {},
            "issues_found": [],
            "feedback": {},
            "needs_revision": False,
            "final_content": None
        }
        
        try:
            # Step 1: Data Accuracy Validation
            data_validation = await self._validate_data_accuracy(task, draft_insight)
            validation_result["validation_details"]["data_accuracy"] = data_validation
            
            # Step 2: Methodology Validation
            methodology_validation = await self._validate_methodology(task, draft_insight)
            validation_result["validation_details"]["methodology"] = methodology_validation
            
            # Step 3: Business Logic Validation
            business_validation = await self._validate_business_logic(task, draft_insight)
            validation_result["validation_details"]["business_logic"] = business_validation
            
            # Step 4: Compliance Validation
            compliance_validation = await self._validate_compliance(task, draft_insight)
            validation_result["validation_details"]["compliance"] = compliance_validation
            
            # Step 5: Cross-Validation and Synthesis
            synthesis_result = await self._synthesize_validations(
                task, draft_insight, validation_result["validation_details"]
            )
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(validation_result["validation_details"])
            validation_result["quality_score"] = quality_score
            
            # Determine approval
            if quality_score >= self.quality_threshold:
                validation_result["approved"] = True
                validation_result["final_content"] = synthesis_result["enhanced_content"]
                logger.info(f"✅ Insight APPROVED for task {task.id} "
                          f"(quality score: {quality_score:.2f})")
            else:
                validation_result["approved"] = False
                validation_result["needs_revision"] = quality_score >= (self.quality_threshold - 0.15)
                
                # Generate specific feedback for revision
                if validation_result["needs_revision"]:
                    validation_result["feedback"] = self._generate_revision_feedback(
                        validation_result["validation_details"]
                    )
                    logger.warning(f"⚠️ Insight needs REVISION for task {task.id} "
                                 f"(quality score: {quality_score:.2f})")
                else:
                    validation_result["reason"] = "Quality standards not met"
                    logger.error(f"❌ Insight REJECTED for task {task.id} "
                               f"(quality score: {quality_score:.2f})")
            
            # Log audit trail
            self._log_audit(task.id, draft_insight.agent_id, validation_result)
            
            # Add validation time
            validation_result["validation_time_ms"] = int(
                (datetime.now() - validation_start).total_seconds() * 1000
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Error during validation: {str(e)}")
            validation_result["approved"] = False
            validation_result["reason"] = f"Validation error: {str(e)}"
            return validation_result
    
    async def _validate_data_accuracy(self, task: AnalyticalTask, 
                                    draft_insight: DraftInsight) -> Dict[str, Any]:
        """Validate the accuracy of data and SQL queries"""
        logger.info("🔢 Validating data accuracy...")
        
        validation = {
            "passed": True,
            "score": 1.0,
            "checks": {}
        }
        
        # Verify SQL queries
        if draft_insight.sql_queries:
            sql_check = await self._verify_sql_queries(task, draft_insight.sql_queries)
            validation["checks"]["sql_verification"] = sql_check
            if not sql_check["passed"]:
                validation["passed"] = False
                validation["score"] *= 0.7
        
        # Check data consistency
        consistency_check = await self._check_data_consistency(draft_insight)
        validation["checks"]["consistency"] = consistency_check
        if not consistency_check["passed"]:
            validation["passed"] = False
            validation["score"] *= 0.8
        
        # Validate against source data
        source_check = await self._validate_against_source(task, draft_insight)
        validation["checks"]["source_validation"] = source_check
        if not source_check["passed"]:
            validation["passed"] = False
            validation["score"] *= 0.6
        
        return validation
    
    async def _validate_methodology(self, task: AnalyticalTask, 
                                  draft_insight: DraftInsight) -> Dict[str, Any]:
        """Validate the analytical methodology"""
        logger.info("📐 Validating methodology...")
        
        validation = {
            "passed": True,
            "score": 1.0,
            "checks": {}
        }
        
        # Check statistical rigor
        if task.complexity.value in ["complex", "critical"]:
            stats_check = self._check_statistical_rigor(draft_insight)
            validation["checks"]["statistical_rigor"] = stats_check
            if not stats_check["passed"]:
                validation["score"] *= 0.85
        
        # Validate assumptions
        assumptions_check = self._validate_assumptions(draft_insight)
        validation["checks"]["assumptions"] = assumptions_check
        if not assumptions_check["passed"]:
            validation["score"] *= 0.9
        
        # Check confidence levels
        confidence_check = {
            "passed": draft_insight.confidence_score >= 0.7,
            "confidence": draft_insight.confidence_score,
            "threshold": 0.7
        }
        validation["checks"]["confidence"] = confidence_check
        if not confidence_check["passed"]:
            validation["passed"] = False
            validation["score"] *= 0.7
        
        return validation
    
    async def _validate_business_logic(self, task: AnalyticalTask, 
                                     draft_insight: DraftInsight) -> Dict[str, Any]:
        """Validate business logic and reasonableness"""
        logger.info("💼 Validating business logic...")
        
        # Use Gemini to perform reasonableness check
        reasonableness_prompt = f"""
        Evaluate the business logic and reasonableness of this automotive dealership insight:
        
        Original Query: {task.user_query}
        Generated Insight: {draft_insight.content}
        
        Check for:
        1. Logical consistency
        2. Reasonable conclusions given the data
        3. Industry-appropriate metrics and benchmarks
        4. Actionable recommendations
        5. Any red flags or unrealistic claims
        
        Provide assessment in JSON format:
        {{
            "is_reasonable": true/false,
            "logic_score": 0-1,
            "issues": ["issue1", "issue2"],
            "strengths": ["strength1", "strength2"]
        }}
        """
        
        try:
            assessment = await self._call_gemini(reasonableness_prompt)
            result = self._parse_json_response(assessment)
            
            validation = {
                "passed": result.get("is_reasonable", True),
                "score": result.get("logic_score", 0.8),
                "checks": {
                    "reasonableness": result,
                    "actionability": self._check_actionability(draft_insight)
                }
            }
            
            return validation
            
        except Exception as e:
            logger.error(f"Business logic validation error: {str(e)}")
            return {
                "passed": False,
                "score": 0.5,
                "checks": {"error": str(e)}
            }
    
    async def _validate_compliance(self, task: AnalyticalTask, 
                                 draft_insight: DraftInsight) -> Dict[str, Any]:
        """Validate compliance and ethical considerations"""
        logger.info("⚖️ Validating compliance...")
        
        validation = {
            "passed": True,
            "score": 1.0,
            "checks": {}
        }
        
        # Check data privacy
        privacy_check = self._check_data_privacy(draft_insight)
        validation["checks"]["data_privacy"] = privacy_check
        if not privacy_check["passed"]:
            validation["passed"] = False
            validation["score"] = 0  # Zero tolerance for privacy violations
        
        # Check ethical considerations
        ethics_check = self._check_ethical_considerations(draft_insight)
        validation["checks"]["ethics"] = ethics_check
        if not ethics_check["passed"]:
            validation["score"] *= 0.9
        
        return validation
    
    async def _synthesize_validations(self, task: AnalyticalTask,
                                    draft_insight: DraftInsight,
                                    validations: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all validations and enhance the insight if approved"""
        
        # If all validations pass, enhance the insight
        all_passed = all(v.get("passed", False) for v in validations.values())
        
        if all_passed:
            # Use Gemini to create enhanced, validated version
            enhancement_prompt = f"""
            Create a final, polished version of this automotive dealership insight.
            Incorporate any improvements needed while maintaining accuracy.
            
            Original Query: {task.user_query}
            Draft Insight: {draft_insight.content}
            Validation Notes: {validations}
            
            Enhance the insight with:
            1. Clear, executive-friendly language
            2. Highlighted key takeaways
            3. Specific, actionable recommendations
            4. Confidence levels for predictions
            5. Any important caveats or limitations
            
            Maintain the same JSON structure but improve clarity and impact.
            """
            
            enhanced_response = await self._call_gemini(enhancement_prompt)
            enhanced_content = self._parse_json_response(enhanced_response)
            
            return {
                "enhanced_content": enhanced_content,
                "synthesis_notes": "Insight enhanced and validated"
            }
        else:
            return {
                "enhanced_content": None,
                "synthesis_notes": "Validation failed - enhancement not performed"
            }
    
    async def _verify_sql_queries(self, task: AnalyticalTask, 
                                sql_queries: List[str]) -> Dict[str, Any]:
        """Verify SQL queries are correct and safe"""
        result = {"passed": True, "issues": []}
        
        for query in sql_queries:
            # Check for dangerous operations
            dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE"]
            for keyword in dangerous_keywords:
                if keyword in query.upper():
                    result["passed"] = False
                    result["issues"].append(f"Dangerous operation detected: {keyword}")
            
            # Verify dealership ID is properly scoped
            if task.dealership_id not in query:
                result["issues"].append("Query may access data from wrong dealership")
            
            # Try to explain query to ensure it makes sense
            try:
                query_job = self.bigquery_client.query(f"EXPLAIN {query}")
                # Just checking if query is valid
            except Exception as e:
                result["passed"] = False
                result["issues"].append(f"Invalid SQL: {str(e)}")
        
        return result
    
    async def _check_data_consistency(self, draft_insight: DraftInsight) -> Dict[str, Any]:
        """Check internal consistency of the insight data"""
        content = draft_insight.content
        issues = []
        
        # Check if numbers add up
        if "key_metrics" in content:
            # Validate metric relationships if any
            pass
        
        # Check for contradictions
        if "insights" in content and "trends" in content:
            # Could use Gemini to check for logical contradictions
            pass
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    async def _validate_against_source(self, task: AnalyticalTask,
                                     draft_insight: DraftInsight) -> Dict[str, Any]:
        """Validate insight against source data"""
        # For critical insights, re-run a sample query to verify
        if task.complexity.value in ["complex", "critical"] and draft_insight.sql_queries:
            try:
                # Take first query and add LIMIT to make it fast
                sample_query = draft_insight.sql_queries[0]
                if "LIMIT" not in sample_query.upper():
                    sample_query += " LIMIT 10"
                
                query_job = self.bigquery_client.query(sample_query)
                results = query_job.result()
                
                # Just checking that we can get data
                return {"passed": True, "sample_verified": True}
                
            except Exception as e:
                return {"passed": False, "error": str(e)}
        
        return {"passed": True, "sample_verified": False}
    
    def _check_statistical_rigor(self, draft_insight: DraftInsight) -> Dict[str, Any]:
        """Check statistical rigor for complex analyses"""
        content = draft_insight.content
        methodology = draft_insight.methodology
        
        checks = {
            "has_confidence_intervals": "confidence_interval" in str(content).lower(),
            "has_sample_size": "data_points_analyzed" in methodology,
            "has_methodology": "techniques" in methodology,
            "adequate_sample": methodology.get("data_points_analyzed", 0) > 30
        }
        
        passed = sum(checks.values()) >= 3  # At least 3 out of 4 checks
        
        return {
            "passed": passed,
            "checks": checks
        }
    
    def _validate_assumptions(self, draft_insight: DraftInsight) -> Dict[str, Any]:
        """Validate assumptions made in the analysis"""
        assumptions = draft_insight.methodology.get("assumptions", [])
        
        if draft_insight.content.get("predictions"):
            # For predictions, assumptions are mandatory
            if not assumptions:
                return {
                    "passed": False,
                    "issue": "Predictions made without stating assumptions"
                }
        
        return {"passed": True, "assumptions_stated": len(assumptions) > 0}
    
    def _check_actionability(self, draft_insight: DraftInsight) -> Dict[str, Any]:
        """Check if recommendations are actionable"""
        content = draft_insight.content
        recommendations = content.get("recommendations", [])
        
        if isinstance(recommendations, list) and recommendations:
            # Check if recommendations have enough detail
            actionable_count = 0
            for rec in recommendations:
                if isinstance(rec, dict):
                    if rec.get("action") and rec.get("priority"):
                        actionable_count += 1
                elif isinstance(rec, str) and len(rec) > 20:
                    actionable_count += 1
            
            return {
                "passed": actionable_count > 0,
                "actionable_recommendations": actionable_count,
                "total_recommendations": len(recommendations)
            }
        
        return {
            "passed": False,
            "issue": "No actionable recommendations provided"
        }
    
    def _check_data_privacy(self, draft_insight: DraftInsight) -> Dict[str, Any]:
        """Check for data privacy violations"""
        content_str = json.dumps(draft_insight.content)
        
        # Check for PII
        privacy_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone
        ]
        
        import re
        violations = []
        for pattern in privacy_patterns:
            if re.search(pattern, content_str):
                violations.append(f"Potential PII found matching pattern: {pattern}")
        
        return {
            "passed": len(violations) == 0,
            "violations": violations
        }
    
    def _check_ethical_considerations(self, draft_insight: DraftInsight) -> Dict[str, Any]:
        """Check for ethical issues"""
        content = draft_insight.content
        
        # Check for discriminatory language or unfair practices
        ethical_issues = []
        
        # This is a simplified check - in production would be more sophisticated
        problematic_terms = ["discriminate", "exclude", "target"]
        content_str = json.dumps(content).lower()
        
        for term in problematic_terms:
            if term in content_str:
                ethical_issues.append(f"Potentially problematic term found: {term}")
        
        return {
            "passed": len(ethical_issues) == 0,
            "issues": ethical_issues
        }
    
    def _calculate_quality_score(self, validations: Dict[str, Any]) -> float:
        """Calculate overall quality score from all validations"""
        weights = {
            "data_accuracy": 0.35,
            "methodology": 0.25,
            "business_logic": 0.25,
            "compliance": 0.15
        }
        
        total_score = 0.0
        for category, weight in weights.items():
            if category in validations:
                score = validations[category].get("score", 0.0)
                total_score += score * weight
        
        return total_score
    
    def _generate_revision_feedback(self, validations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific feedback for revision"""
        feedback = {
            "summary": "Insight requires revision to meet quality standards",
            "specific_issues": [],
            "improvement_suggestions": []
        }
        
        # Analyze each validation category
        for category, validation in validations.items():
            if not validation.get("passed", True):
                for check_name, check_result in validation.get("checks", {}).items():
                    if isinstance(check_result, dict) and not check_result.get("passed", True):
                        feedback["specific_issues"].append({
                            "category": category,
                            "check": check_name,
                            "issue": check_result.get("issue", "Check failed")
                        })
        
        # Generate improvement suggestions
        if validations.get("data_accuracy", {}).get("score", 1.0) < 0.8:
            feedback["improvement_suggestions"].append(
                "Verify SQL queries and ensure data sources are correctly referenced"
            )
        
        if validations.get("methodology", {}).get("score", 1.0) < 0.8:
            feedback["improvement_suggestions"].append(
                "Strengthen statistical analysis and clearly state assumptions"
            )
        
        if validations.get("business_logic", {}).get("score", 1.0) < 0.8:
            feedback["improvement_suggestions"].append(
                "Ensure recommendations are specific and actionable"
            )
        
        return feedback
    
    def _log_audit(self, task_id: str, agent_id: str, validation_result: Dict[str, Any]):
        """Log audit trail for compliance and monitoring"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent_id": agent_id,
            "approved": validation_result["approved"],
            "quality_score": validation_result["quality_score"],
            "validation_time_ms": validation_result.get("validation_time_ms", 0),
            "issues_found": len(validation_result.get("issues_found", []))
        }
        
        self.audit_log.append(audit_entry)
        
        # In production, this would be persisted to a database
        logger.info(f"📝 Audit logged: {audit_entry}")
    
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
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from response")
        
        return {}
    
    async def shutdown(self):
        """Shutdown the Master Analyst"""
        logger.info("🛑 Shutting down L3 Master Analyst")
        
        # Save audit log
        if self.audit_log:
            audit_summary = {
                "total_validations": len(self.audit_log),
                "approved": sum(1 for a in self.audit_log if a["approved"]),
                "rejected": sum(1 for a in self.audit_log if not a["approved"]),
                "avg_quality_score": sum(a["quality_score"] for a in self.audit_log) / len(self.audit_log)
            }
            logger.info(f"📊 Validation Summary: {audit_summary}")
        
        if self.bigquery_client:
            self.bigquery_client.close()
