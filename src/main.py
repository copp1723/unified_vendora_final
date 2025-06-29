#!/usr/bin/env python3
"""
VENDORA - Automotive AI Data Platform
Main entry point for the FastAPI application.
"""

import uvicorn
import os
from dotenv import load_dotenv

if __name__ == '__main__':
    # Load environment variables from .env file
    # This ensures that environment variables are available for Uvicorn and the FastAPI app startup.
    load_dotenv()

    # Configuration for Uvicorn server
    # Port and host can also be driven by environment variables if needed
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '8000')) # FastAPI default is often 8000
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    reload_app = os.getenv('RELOAD_APP', 'False').lower() == 'true' # For development

    print("🚀 Starting VENDORA FastAPI platform...")
    print(f"🌐 Access at: http://{host}:{port}")
    if reload_app:
        print("🔥 Application reloading is ENABLED.")
    
    # Run Uvicorn server
    # The string "src.fastapi_main:app" tells Uvicorn:
    # - Look in the "src" directory (or package)
    # - Find the file "fastapi_main.py"
    # - In that file, find the FastAPI application instance named "app"
    uvicorn.run(
        "src.fastapi_main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload_app
        # If using multiple workers in production, add `workers=N`
        # workers=int(os.getenv('APP_WORKERS', '1'))
    )

