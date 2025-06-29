#!/usr/bin/env python3
"""
VENDORA - Automotive AI Data Platform
Main entry point for the FastAPI application.
"""

import os
import logging
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware # Added for CORS
import uvicorn

# Assuming mailgun_handler is now in agents.email_processor
# Adjust the import path if your project structure is different
from agents.email_processor.mailgun_handler import MailgunWebhookHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(app_config: Dict) -> FastAPI:
    """Creates and configures the FastAPI application."""

    fast_app = FastAPI(title="VENDORA AI Data Platform", version="0.1.0")

    # Add CORS middleware if needed (adjust origins as necessary)
    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Allows all origins
        allow_credentials=True,
        allow_methods=["*"], # Allows all methods
        allow_headers=["*"], # Allows all headers
    )

    # Initialize MailgunWebhookHandler
    mailgun_handler = MailgunWebhookHandler(app_config)

    @fast_app.post("/webhook/mailgun")
    async def handle_mailgun_webhook(request: Request):
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
                # If Mailgun sends JSON with attachments, they might be links or small files inline.
                # The refactored handler expects 'parsed_attachments'.
                # For JSON, Mailgun's 'attachments' field usually contains metadata + URLs.
                # True file content usually comes via multipart/form-data.
                # This part might need adjustment based on actual Mailgun JSON payload for attachments.
                # For now, we assume if it's JSON, any 'attachments' field in it is just metadata
                # and we are not processing files from JSON directly this way.
                # The `extract_csv_attachments` in the handler will look for `parsed_attachments`.
                # If you expect JSON to contain file content (e.g. base64 encoded), you'd parse it here.
                logger.info("Received JSON webhook payload.")

            elif "multipart/form-data" in content_type:
                logger.info("Received multipart/form-data webhook payload.")
                async with request.form() as form_data:
                    # Convert form_data (an immutable MultiDict) to a mutable dict
                    # for easier processing by the handler.
                    # We also need to handle file uploads explicitly.

                    form_data_dict = {}
                    temp_files: List[UploadFile] = []

                    for key, value in form_data.items():
                        if isinstance(value, UploadFile):
                            # Store UploadFile objects to process them
                            # Mailgun uses 'attachment-1', 'attachment-2', etc. for files
                            # and also 'attachment-x-signature' for detached signatures.
                            if key.startswith("attachment-") and not key.endswith("-signature"): # Basic check
                                temp_files.append(value)
                            else: # Other form fields like 'subject', 'sender', 'signature', etc.
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
                                        content_str = content_bytes.decode('latin-1') # Try another common encoding
                                    except UnicodeDecodeError as ude:
                                        logger.error(f"Could not decode attachment {uploaded_file.filename}: {ude}")
                                        continue # Skip this file

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

            # If request_data is empty after attempting to parse, it's an issue.
            if not request_data and not parsed_attachments: # Check if anything was actually parsed
                 logger.warning("Webhook request body was empty or not parsed correctly.")
                 # Mailgun should always send some data. If not, it might be a misconfiguration or empty POST.
                 # Depending on strictness, could raise HTTPException here.
                 # For now, let handler decide if it's an error.

            # Process the webhook using the handler
            # The handler expects 'message-headers' to be a stringified JSON or already a dict/list.
            # If it's form data, Mailgun sends headers as separate fields or within 'message-headers' field.
            # If 'message-headers' is a string, the handler will parse it.
            if 'message-headers' in request_data and not isinstance(request_data['message-headers'], (dict, list)):
                 pass # Handler will attempt json.loads

            result = await mailgun_handler.process_webhook(request_data, parsed_attachments)

            if result.get('status') == 'failed':
                # Log the detailed error from result if present
                error_detail = result.get('error', 'Processing failed')
                logger.error(f"Webhook processing failed: {error_detail}")
                # For client errors (like invalid signature), 400 is appropriate.
                # For server-side errors during processing, 500 might be.
                # Let's use 400 if it's a known "failed" status from our handler,
                # implying bad input or verification failure.
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

            return JSONResponse(content=result, status_code=status.HTTP_200_OK)

        except HTTPException as http_exc:
            # Re-raise HTTPException to let FastAPI handle it
            raise http_exc
        except Exception as e:
            logger.exception(f"Unhandled error in Mailgun webhook endpoint: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An internal server error occurred: {str(e)}"
            )

    @fast_app.get("/health", status_code=status.HTTP_200_OK)
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "vendora-main-api"}

    return fast_app

if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()
    
    # Configuration
    app_config = {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'MAILGUN_PRIVATE_API_KEY': os.getenv('MAILGUN_PRIVATE_API_KEY'),
        'MAILGUN_DOMAIN': os.getenv('MAILGUN_DOMAIN'),
        'MAILGUN_SENDING_API_KEY': os.getenv('MAILGUN_SENDING_API_KEY'),
        'SUPERMEMORY_API_KEY': os.getenv('SUPERMEMORY_API_KEY'),
        'DATA_STORAGE_PATH': os.getenv('DATA_STORAGE_PATH', './data'),
        'MEMORY_STORAGE_PATH': os.getenv('MEMORY_STORAGE_PATH', './memory')
    }
    
    # Validate required configuration
    required_keys = ['OPENROUTER_API_KEY', 'MAILGUN_PRIVATE_API_KEY', 'SUPERMEMORY_API_KEY']
    missing_keys = [key for key in required_keys if not app_config.get(key)]
    
    if missing_keys:
        logger.critical(f"❌ Missing required configuration: {missing_keys}. Please check your .env file or environment variables.")
        exit(1)
    
    # Create the FastAPI app instance
    app = create_app(app_config)
    
    # Configuration for Uvicorn server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))  # Use PORT env var, default to 8000
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    reload_app = os.getenv('RELOAD_APP', 'False').lower() == 'true'
    
    logger.info("🚀 Starting VENDORA platform...")
    logger.info("📊 Automotive AI Data Platform")
    logger.info(f"🌐 Access at: http://{host}:{port}")
    if reload_app:
        logger.info("🔥 Application reloading is ENABLED.")
    
    # Run with Uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=reload_app
        # If using multiple workers in production, add `workers=N`
        # workers=int(os.getenv('APP_WORKERS', '1'))
    )