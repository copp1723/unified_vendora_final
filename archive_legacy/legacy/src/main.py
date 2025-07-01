#!/usr/bin/env python3
"""
VENDORA - Automotive AI Data Platform
Main entry point for the FastAPI application.
"""

import os
import logging
import sys
from typing import Dict, List, Optional, Any

# Enhanced logging for container diagnostics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Add startup diagnostic logging
logger.info("🚀 VENDORA Container Startup - BEGIN")
logger.info(f"📍 Python executable: {sys.executable}")
logger.info(f"📍 Python version: {sys.version}")
logger.info(f"📍 Working directory: {os.getcwd()}")
logger.info(f"📍 PORT environment variable: {os.getenv('PORT', 'NOT SET')}")
logger.info(f"📍 HOST environment variable: {os.getenv('HOST', 'NOT SET')}")

try:
    from dotenv import load_dotenv
    logger.info("✅ dotenv import successful")
except ImportError as e:
    logger.error(f"❌ dotenv import failed: {e}")

try:
    from fastapi import FastAPI, Request, HTTPException, status, UploadFile, File, Form, Depends
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware # Added for CORS
    logger.info("✅ FastAPI imports successful")
except ImportError as e:
    logger.error(f"❌ FastAPI import failed: {e}")
    raise

try:
    import uvicorn
    logger.info("✅ uvicorn import successful")
except ImportError as e:
    logger.error(f"❌ uvicorn import failed: {e}")
    raise

# Assuming mailgun_handler is now in agents.email_processor
# Adjust the import path if your project structure is different
try:
    from agents.email_processor.mailgun_handler import MailgunWebhookHandler
    logger.info("✅ MailgunWebhookHandler import successful")
except ImportError as e:
    logger.error(f"❌ MailgunWebhookHandler import failed: {e}")
    # Continue without mailgun handler for now
    MailgunWebhookHandler = None

try:
    from src.auth.firebase_auth import initialize_firebase_auth, get_current_user, FirebaseUser
    logger.info("✅ Firebase Auth import successful")
except ImportError as e:
    logger.error(f"❌ Firebase Auth import failed: {e}")
    # Continue without auth for now
    initialize_firebase_auth = None
    get_current_user = None
    FirebaseUser = None


def create_app(app_config: Dict) -> FastAPI:
    """Creates and configures the FastAPI application."""
    logger.info("🏗️ Creating FastAPI application...")
    
    try:
        fast_app = FastAPI(title="VENDORA AI Data Platform", version="0.1.0")
        logger.info("✅ FastAPI app instance created")
    except Exception as e:
        logger.error(f"❌ Failed to create FastAPI app: {e}")
        raise

    # Add CORS middleware if needed (adjust origins as necessary)
    try:
        fast_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"], # Allows all origins
            allow_credentials=True,
            allow_methods=["*"], # Allows all methods
            allow_headers=["*"], # Allows all headers
        )
        logger.info("✅ CORS middleware added")
    except Exception as e:
        logger.error(f"❌ Failed to add CORS middleware: {e}")
        raise

    # Initialize Firebase Auth
    try:
        if initialize_firebase_auth:
            initialize_firebase_auth(app_config)
            logger.info("✅ Firebase Auth initialized")
        else:
            logger.warning("⚠️ Firebase Auth not available, skipping initialization")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase Auth: {e}")

    # Initialize MailgunWebhookHandler
    try:
        if MailgunWebhookHandler:
            mailgun_handler = MailgunWebhookHandler(app_config)
            logger.info("✅ MailgunWebhookHandler initialized")
        else:
            logger.warning("⚠️ MailgunWebhookHandler not available, skipping initialization")
            mailgun_handler = None
    except Exception as e:
        logger.error(f"❌ Failed to initialize MailgunWebhookHandler: {e}")
        mailgun_handler = None

    @fast_app.post("/webhook/mailgun")
    async def handle_mailgun_webhook(request: Request, current_user: FirebaseUser = Depends(get_current_user)):
        """
        Handles incoming Mailgun webhooks.
        Mailgun can send data as 'application/json' or 'multipart/form-data'.
        This endpoint attempts to handle both.
        """
        content_type = request.headers.get("content-type", "").lower()

        request_data: Dict[str, Any] = {}
        parsed_attachments: List[Dict[str, Any]] = []

        try:
            if "application/json" in content_type:
                request_data = await request.json()
                logger.info("Received JSON webhook payload.")

            elif "multipart/form-data" in content_type:
                logger.info("Received multipart/form-data webhook payload.")
                async with request.form() as form_data:
                    form_data_dict = {}
                    temp_files: List[UploadFile] = []

                    for key, value in form_data.items():
                        if isinstance(value, UploadFile):
                            if key.startswith("attachment-") and not key.endswith("-signature"):
                                temp_files.append(value)
                            else: 
                                form_data_dict[key] = value
                        else:
                             form_data_dict[key] = value

                    request_data = form_data_dict

                    for uploaded_file in temp_files:
                        if uploaded_file.filename:
                            if uploaded_file.filename.lower().endswith(".csv") or "csv" in (uploaded_file.content_type or "").lower():
                                content_bytes = await uploaded_file.read()
                                try:
                                    content_str = content_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    try:
                                        content_str = content_bytes.decode('latin-1')
                                    except UnicodeDecodeError as ude:
                                        logger.error(f"Could not decode attachment {uploaded_file.filename}: {ude}")
                                        continue

                                parsed_attachments.append({
                                    "filename": uploaded_file.filename,
                                    "content": content_str,
                                    "content_type": uploaded_file.content_type or "text/csv"
                                })
                            else:
                                logger.info(f"Skipping non-CSV attachment: {uploaded_file.filename}")
                        await uploaded_file.close()
            else:
                logger.error(f"Unsupported content type: {content_type}")
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported content type: {content_type}"
                )

            if not request_data and not parsed_attachments:
                 logger.warning("Webhook request body was empty or not parsed correctly.")

            if 'message-headers' in request_data and not isinstance(request_data['message-headers'], (dict, list)):
                 pass

            result = await mailgun_handler.process_webhook(request_data, parsed_attachments)

            if result.get('status') == 'failed':
                error_detail = result.get('error', 'Processing failed')
                logger.error(f"Webhook processing failed: {error_detail}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

            return JSONResponse(content=result, status_code=status.HTTP_200_OK)

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.exception(f"Unhandled error in Mailgun webhook endpoint: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An internal server error occurred: {str(e)}"
            )

    @fast_app.get("/", status_code=status.HTTP_200_OK)
    async def root():
        """Root endpoint."""
        logger.info("🏠 Root endpoint called")
        return {
            "message": "VENDORA AI Data Platform",
            "status": "running",
            "version": "0.1.0",
            "service": "vendora-main-api",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "webhook": "/webhook/mailgun"
            }
        }

    @fast_app.get("/health", status_code=status.HTTP_200_OK)
    async def health_check():
        """Health check endpoint."""
        logger.info("🏥 Health check endpoint called")
        return {"status": "healthy", "service": "vendora-main-api"}

    # Log all registered routes for debugging
    logger.info("📋 Registered routes:")
    for route in fast_app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            logger.info(f"  {route.methods} {route.path}")
    
    logger.info("✅ FastAPI application created successfully with all routes")
    return fast_app

# Load environment variables and create app instance for deployment
logger.info("📋 Loading environment variables...")
try:
    load_dotenv()
    logger.info("✅ Environment variables loaded")
except Exception as e:
    logger.error(f"❌ Failed to load environment variables: {e}")

# Configuration
logger.info("⚙️ Building application configuration...")
app_config = {
    'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
    'MAILGUN_PRIVATE_API_KEY': os.getenv('MAILGUN_PRIVATE_API_KEY'),
    'MAILGUN_DOMAIN': os.getenv('MAILGUN_DOMAIN'),
    'MAILGUN_SENDING_API_KEY': os.getenv('MAILGUN_SENDING_API_KEY'),
    'SUPERMEMORY_API_KEY': os.getenv('SUPERMEMORY_API_KEY'),
    'DATA_STORAGE_PATH': os.getenv('DATA_STORAGE_PATH', './data'),
    'MEMORY_STORAGE_PATH': os.getenv('MEMORY_STORAGE_PATH', './memory'),
    'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID'),
    'FIREBASE_SERVICE_ACCOUNT_PATH': os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
}

# Log configuration status (without exposing sensitive values)
config_status = {}
for key, value in app_config.items():
    if 'API_KEY' in key or 'PRIVATE' in key:
        config_status[key] = "SET" if value else "NOT SET"
    else:
        config_status[key] = value if value else "NOT SET"
logger.info(f"📋 Configuration status: {config_status}")

# Create the FastAPI app instance (required for uvicorn deployment)
logger.info("🚀 Creating FastAPI app instance...")
try:
    app = create_app(app_config)
    logger.info("✅ FastAPI app instance created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create FastAPI app instance: {e}")
    raise

if __name__ == '__main__':
    logger.info("🎯 Main execution block - running directly")
    
    # Validate required configuration only when running directly
    required_keys = ['OPENROUTER_API_KEY', 'MAILGUN_PRIVATE_API_KEY', 'SUPERMEMORY_API_KEY']
    missing_keys = [key for key in required_keys if not app_config.get(key)]
    
    if missing_keys:
        logger.warning(f"⚠️ Missing optional configuration: {missing_keys}. Some features may be limited.")
    
    # Configuration for Uvicorn server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    reload_app = os.getenv('RELOAD_APP', 'False').lower() == 'true'
    
    logger.info("🚀 Starting VENDORA platform...")
    logger.info("📊 Automotive AI Data Platform")
    logger.info(f"🌐 Server will bind to: {host}:{port}")
    logger.info(f"📊 Log level: {log_level}")
    if reload_app:
        logger.info("🔥 Application reloading is ENABLED.")
    
    # Pre-flight checks
    logger.info("✈️ Running pre-flight checks...")
    logger.info(f"✅ FastAPI app object: {type(app)}")
    logger.info(f"✅ Host: {host}")
    logger.info(f"✅ Port: {port} (type: {type(port)})")
    
    # Run with Uvicorn
    try:
        logger.info("🚀 Starting uvicorn server...")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=reload_app
        )
    except Exception as e:
        logger.error(f"❌ Failed to start uvicorn server: {e}")
        raise
else:
    logger.info("📦 Module imported - app instance available for external server")
