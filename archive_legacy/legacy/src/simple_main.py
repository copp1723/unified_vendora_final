#!/usr/bin/env python3
"""
VENDORA - Simplified Main Entry Point
A minimal FastAPI application for initial deployment without complex dependencies.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="VENDORA AI Data Platform",
    description="Automotive AI Data Platform - Simplified Deployment",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for deployment verification."""
    return {
        "status": "healthy",
        "service": "vendora-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint."""
    return {
        "message": "VENDORA AI Data Platform",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/api/v1/status", status_code=status.HTTP_200_OK)
async def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "health_check": True,
            "cors_enabled": True,
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "timestamp": datetime.now().isoformat()
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint was not found",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    # Configuration for Uvicorn server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    log_level = os.getenv('LOG_LEVEL', 'info').lower()
    
    logger.info("🚀 Starting VENDORA platform (Simplified)...")
    logger.info("📊 Automotive AI Data Platform")
    logger.info(f"🌐 Access at: http://{host}:{port}")
    
    # Run with Uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )