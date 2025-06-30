"""
VENDORA Cloud Platform Deployment Script
Automated deployment and verification
"""

import asyncio
import subprocess
import sys
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def deploy_vendora_cloud():
    """Deploy VENDORA Cloud Platform"""
    
    logger.info("🚀 VENDORA Cloud Platform Deployment")
    logger.info("=" * 50)
    
    # Step 1: Verify environment
    logger.info("📋 Step 1: Environment Verification")
    try:
        # Check if we're in the right directory
        if not Path("cloud_config.py").exists():
            logger.error("❌ Run this script from the working_vendora directory")
            return False
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or python_version.minor < 8:
            logger.error("❌ Python 3.8+ required")
            return False
        
        logger.info("✅ Environment verified")
        
    except Exception as e:
        logger.error(f"❌ Environment check failed: {e}")
        return False
    
    # Step 2: Install dependencies
    logger.info("📦 Step 2: Installing Dependencies")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_cloud.txt"
        ], check=True, capture_output=True)
        logger.info("✅ Dependencies installed")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Dependency installation failed: {e}")
        return False
    
    # Step 3: Run connectivity test
    logger.info("🔌 Step 3: Testing Cloud Connectivity")
    try:
        result = subprocess.run([
            sys.executable, "test_cloud_integration.py", "quick"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("✅ Cloud connectivity verified")
        else:
            logger.warning("⚠️ Cloud connectivity issues detected")
            logger.info("Proceeding with local fallback mode...")
            
    except subprocess.TimeoutExpired:
        logger.warning("⚠️ Connectivity test timed out")
        logger.info("Proceeding with deployment...")
    except Exception as e:
        logger.warning(f"⚠️ Connectivity test failed: {e}")
        logger.info("Proceeding with deployment...")
    
    # Step 4: Start the platform
    logger.info("🌟 Step 4: Starting VENDORA Cloud Platform")
    try:
        logger.info("Starting FastAPI server on http://localhost:8000")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("=" * 50)
        
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "working_fastapi_cloud:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        return False

async def quick_test():
    """Quick test of the platform"""
    logger.info("⚡ VENDORA Quick Test")
    
    try:
        import httpx
        import json
        
        # Wait a moment for server to be ready
        await asyncio.sleep(2)
        
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✅ Health check passed")
                logger.info(f"   Services: {health_data.get('services', {})}")
                
                # Test sample query
                query_payload = {
                    "query": "What are our top performing vehicles?",
                    "dealership_id": "DEMO_DEALERSHIP",
                    "use_cloud_data": True
                }
                
                query_response = await client.post(
                    "http://localhost:8000/analyze",
                    json=query_payload,
                    timeout=10.0
                )
                
                if query_response.status_code == 200:
                    logger.info("✅ Sample query successful")
                    result = query_response.json()
                    logger.info(f"   Data source: {result.get('data_source', 'unknown')}")
                    logger.info(f"   Cloud enhanced: {result.get('cloud_enhanced', False)}")
                else:
                    logger.warning(f"⚠️ Query test failed: {query_response.status_code}")
                
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ Quick test failed: {e}")

def print_success_message():
    """Print deployment success message"""
    message = """
🎉 VENDORA Cloud Platform Successfully Deployed!

📍 Platform URL: http://localhost:8000

🔗 Key Endpoints:
   • Health Check: http://localhost:8000/health
   • Analytics API: http://localhost:8000/analyze
   • Demo Queries: http://localhost:8000/demo/sample-query
   • Cloud Config: http://localhost:8000/cloud/config

📊 Features Available:
   ✅ BigQuery Integration (Real automotive data)
   ✅ Secret Manager (Secure API keys)
   ✅ Firebase Authentication
   ✅ AI-Powered Analytics
   ✅ Fallback Mechanisms

🧪 Test Your Platform:
   curl http://localhost:8000/demo/quick-test

📚 Documentation: See CLOUD_INTEGRATION_README.md

🚀 Ready for business intelligence queries!
    """
    print(message)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run quick test (assumes server is already running)
        asyncio.run(quick_test())
    else:
        # Deploy the platform
        try:
            success = asyncio.run(deploy_vendora_cloud())
            if success:
                print_success_message()
        except KeyboardInterrupt:
            print("\n🛑 Deployment interrupted by user")
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")