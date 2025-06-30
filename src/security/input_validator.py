"""
VENDORA Input Validation and Security Module
Provides comprehensive input validation and SQL injection protection
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, validator, ValidationError
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security validation levels"""
    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


class InputValidator:
    """Comprehensive input validation for VENDORA platform"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"].*['\"])",
        r"(;|\|\||&&)",
        r"(\bxp_cmdshell\b|\bsp_executesql\b)",
        r"(\b(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)\b)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>"
    ]
    
    @classmethod
    def validate_dealership_id(cls, dealership_id: str, security_level: SecurityLevel = SecurityLevel.STANDARD) -> str:
        """Validate and sanitize dealership ID"""
        if not dealership_id:
            raise ValueError("Dealership ID cannot be empty")
        
        if len(dealership_id) > 50:
            raise ValueError("Dealership ID too long (max 50 characters)")
        
        if security_level == SecurityLevel.STRICT:
            # Only alphanumeric and underscores
            if not re.match(r"^[a-zA-Z0-9_]+$", dealership_id):
                raise ValueError("Dealership ID contains invalid characters (strict mode)")
        else:
            # Allow hyphens as well
            if not re.match(r"^[a-zA-Z0-9_-]+$", dealership_id):
                raise ValueError("Dealership ID contains invalid characters")
        
        return dealership_id.strip()
    
    @classmethod
    def validate_task_id(cls, task_id: str) -> str:
        """Validate task ID format"""
        if not task_id:
            raise ValueError("Task ID cannot be empty")
        
        if not re.match(r"^TASK-[a-f0-9]{8}$", task_id):
            raise ValueError("Invalid task ID format (expected: TASK-xxxxxxxx)")
        
        return task_id
    
    @classmethod
    def validate_user_query(cls, query: str, max_length: int = 1000) -> str:
        """Validate and sanitize user query"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        query = query.strip()
        
        if len(query) > max_length:
            raise ValueError(f"Query too long (max {max_length} characters)")
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected in query: {pattern}")
                raise ValueError("Query contains potentially dangerous SQL patterns")
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potential XSS detected in query: {pattern}")
                raise ValueError("Query contains potentially dangerous script patterns")
        
        return query
    
    @classmethod
    def validate_sql_query(cls, sql_query: str) -> str:
        """Validate SQL query for security"""
        if not sql_query:
            raise ValueError("SQL query cannot be empty")
        
        # Remove comments and normalize whitespace
        sql_clean = re.sub(r"--.*$", "", sql_query, flags=re.MULTILINE)
        sql_clean = re.sub(r"/\*.*?\*/", "", sql_clean, flags=re.DOTALL)
        sql_clean = " ".join(sql_clean.split())
        
        # Check for dangerous operations
        dangerous_keywords = [
            "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE",
            "EXEC", "EXECUTE", "xp_cmdshell", "sp_executesql"
        ]
        
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_clean, re.IGNORECASE):
                raise ValueError(f"Dangerous SQL operation detected: {keyword}")
        
        # Ensure query uses parameterized format
        if "@dealership_id" not in sql_clean and "dealership" in sql_clean.lower():
            logger.warning("SQL query should use @dealership_id parameter")
        
        return sql_query
    
    @classmethod
    def sanitize_table_name(cls, project_id: str, dataset_id: str, table_name: str) -> str:
        """Create safe table reference"""
        # Sanitize each component
        clean_project = re.sub(r'[^a-zA-Z0-9_-]', '', project_id)
        clean_dataset = re.sub(r'[^a-zA-Z0-9_]', '', dataset_id)
        clean_table = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
        
        if not all([clean_project, clean_dataset, clean_table]):
            raise ValueError("Invalid table reference components")
        
        return f"`{clean_project}.{clean_dataset}.{clean_table}`"
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email format"""
        if not email:
            raise ValueError("Email cannot be empty")
        
        email = email.strip().lower()
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:
            raise ValueError("Email too long")
        
        return email
    
    @classmethod
    def validate_context_data(cls, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize context data"""
        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")
        
        # Limit context size
        if len(str(context)) > 10000:
            raise ValueError("Context data too large")
        
        # Remove potentially dangerous keys
        dangerous_keys = ["__", "eval", "exec", "import", "open", "file"]
        cleaned_context = {}
        
        for key, value in context.items():
            if any(danger in str(key).lower() for danger in dangerous_keys):
                logger.warning(f"Skipping potentially dangerous context key: {key}")
                continue
            
            # Sanitize string values
            if isinstance(value, str):
                value = cls._sanitize_string_value(value)
            
            cleaned_context[key] = value
        
        return cleaned_context
    
    @classmethod
    def _sanitize_string_value(cls, value: str) -> str:
        """Sanitize string values in context"""
        if len(value) > 1000:
            value = value[:1000]
        
        # Remove potential XSS
        for pattern in cls.XSS_PATTERNS:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
        
        return value.strip()


class SecureQueryBuilder:
    """Build secure parameterized queries for BigQuery"""
    
    def __init__(self, project_id: str):
        self.project_id = InputValidator.sanitize_table_name(project_id, "temp", "temp").split(".")[0].strip("`")
    
    def build_sales_query(self, dealership_id: str, date_filter: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """Build secure sales query with parameters"""
        # Validate inputs
        clean_dealership = InputValidator.validate_dealership_id(dealership_id)
        
        # Build safe table reference
        table_ref = InputValidator.sanitize_table_name(
            self.project_id, 
            f"dealership_{clean_dealership}", 
            "sales"
        )
        
        # Base query with parameters
        query = f"""
        SELECT 
            sale_id,
            vehicle_id,
            customer_id,
            sale_date,
            sale_amount,
            salesperson_id
        FROM {table_ref}
        WHERE 1=1
        """
        
        params = {}
        
        # Add date filter if provided
        if date_filter:
            if date_filter.lower() == "last_month":
                query += " AND sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)"
            elif date_filter.lower() == "last_week":
                query += " AND sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK)"
            elif date_filter.lower() == "today":
                query += " AND sale_date = CURRENT_DATE()"
        
        query += " ORDER BY sale_date DESC LIMIT 1000"
        
        return query, params
    
    def build_inventory_query(self, dealership_id: str, status_filter: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """Build secure inventory query"""
        clean_dealership = InputValidator.validate_dealership_id(dealership_id)
        
        table_ref = InputValidator.sanitize_table_name(
            self.project_id,
            f"dealership_{clean_dealership}",
            "inventory"
        )
        
        query = f"""
        SELECT 
            vehicle_id,
            make,
            model,
            year,
            vin,
            status,
            acquisition_date,
            acquisition_cost
        FROM {table_ref}
        WHERE 1=1
        """
        
        params = {}
        
        if status_filter:
            # Validate status
            valid_statuses = ["available", "sold", "pending", "service"]
            if status_filter.lower() in valid_statuses:
                query += " AND LOWER(status) = @status"
                params["status"] = status_filter.lower()
        
        query += " ORDER BY acquisition_date DESC LIMIT 1000"
        
        return query, params