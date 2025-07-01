"""
GCP Cloud Configuration for VENDORA
Connects to Secret Manager, BigQuery, and Firebase
"""

import os
import logging
from google.cloud import secretmanager
from google.cloud import bigquery
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import auth, credentials
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CloudConfig:
    """Manages GCP cloud configuration and secrets"""
    
    def __init__(self, project_id: str = "vendora-464403"):
        self.project_id = project_id
        self.secret_client = None
        self.bigquery_client = None
        self.secrets_cache: Dict[str, str] = {}
        
    async def initialize(self):
        """Initialize all cloud services"""
        logger.info("🌩️ Initializing GCP Cloud Services...")
        
        try:
            # Initialize Secret Manager
            self.secret_client = secretmanager.SecretManagerServiceClient()
            logger.info("✅ Secret Manager initialized")
            
            # Load secrets
            await self._load_secrets()
            
            # Initialize BigQuery
            await self._initialize_bigquery()
            
            # Initialize Firebase
            await self._initialize_firebase()
            
            logger.info("✅ All GCP services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GCP services: {str(e)}")
            raise
    
    async def _load_secrets(self):
        """Load all secrets from Secret Manager"""
        secret_names = [
            "Mailgun_API",
            "Mailgun_Domain", 
            "Mailgun_Private_API_Key",
            "OPENROUTER_API_KEY",
            "SUPER_MEMORY_API",
            "GEMINI_API_KEY"  # Add if stored in Secret Manager
        ]
        
        for secret_name in secret_names:
            try:
                secret_value = await self._get_secret(secret_name)
                if secret_value:
                    self.secrets_cache[secret_name] = secret_value
                    logger.info(f"✅ Loaded secret: {secret_name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load secret {secret_name}: {str(e)}")
    
    async def _get_secret(self, secret_id: str) -> Optional[str]:
        """Get secret from Secret Manager"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to get secret {secret_id}: {str(e)}")
            return None
    
    async def _initialize_bigquery(self):
        """Initialize BigQuery client"""
        try:
            # Use default credentials (service account)
            self.bigquery_client = bigquery.Client(project=self.project_id)
            
            # Test connection
            query = "SELECT 1 as test"
            query_job = self.bigquery_client.query(query)
            list(query_job.result())  # Wait for completion
            
            logger.info("✅ BigQuery client initialized and tested")
            
        except Exception as e:
            logger.error(f"❌ BigQuery initialization failed: {str(e)}")
            self.bigquery_client = None
    
    async def _initialize_firebase(self):
        """Initialize Firebase Admin"""
        try:
            if not firebase_admin._apps:
                # Use default credentials
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {
                    'projectId': self.project_id
                })
            
            # Test Firebase Auth
            auth.get_user_by_email("test@example.com")  # This will fail but validates connection
            
        except firebase_admin.auth.UserNotFoundError:
            # Expected - just testing connection
            logger.info("✅ Firebase Auth initialized and tested")
        except Exception as e:
            logger.warning(f"⚠️ Firebase initialization: {str(e)}")
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get cached secret value"""
        return self.secrets_cache.get(key)
    
    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration for VENDORA"""
        return {
            'project_id': self.project_id,
            'gemini_api_key': self.get_secret('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY'),
            'openrouter_api_key': self.get_secret('OPENROUTER_API_KEY'),
            'mailgun_api_key': self.get_secret('Mailgun_API'),
            'mailgun_domain': self.get_secret('Mailgun_Domain'),
            'mailgun_private_key': self.get_secret('Mailgun_Private_API_Key'),
            'supermemory_api_key': self.get_secret('SUPER_MEMORY_API'),
            'bigquery_client': self.bigquery_client,
            'bigquery_project': self.project_id,
            'use_cloud_services': True
        }

# Global cloud config instance
cloud_config = CloudConfig()