"""
VENDORA Production Launcher
Quick start script for production environment
"""

import sys
import os
import subprocess
import logging
import argparse

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_basic_server(port=8000):
    """Start the basic production server"""
    logger.info("🚀 Starting VENDORA Production Server (Basic Mode)")
    logger.info("📍 Server will be available at: http://localhost:8000")
    logger.info("📖 API Documentation: http://localhost:8000/docs")
    logger.info("🔧 Health Check: http://localhost:8000/health")
    logger.info("=" * 60)
    
    try:
        # Import and run the basic server
        from api.main import app
        import uvicorn
        
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("💡 Make sure you're running from the vendora_production directory")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")

def start_cloud_server(port=8000):
    """Start the cloud-enhanced server"""
    logger.info("🚀 Starting VENDORA Production Server (Cloud Mode)")
    logger.info("☁️  GCP Integration: BigQuery, Secret Manager, Firebase")
    logger.info("📍 Server will be available at: http://localhost:8000")
    logger.info("=" * 60)
    
    try:
        from api.main_cloud import app
        import uvicorn
        
        uvicorn.run(
            "api.main_cloud:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("💡 Cloud mode requires additional system dependencies")
        logger.info("   Try: sudo apt install build-essential libstdc++6")
        logger.info("   Or use basic mode: python start_production.py basic")
    except Exception as e:
        logger.error(f"❌ Cloud startup failed: {e}")

def test_production():
    """Test the production environment"""
    logger.info("🧪 Testing VENDORA Production Environment")
    
    try:
        # Test basic imports first
        from api.main import app as basic_app
        logger.info("✅ Basic API imports working")
        
        from managers.basic_flow_manager import FlowManager
        logger.info("✅ Basic flow manager imports working")
        
        # Test cloud imports separately (may fail due to system dependencies)
        try:
            from config.cloud_config import CloudConfig
            logger.info("✅ Cloud config imports working")
            cloud_available = True
        except Exception as e:
            logger.warning(f"⚠️  Cloud config not available: {e}")
            logger.info("💡 This is expected if system dependencies aren't installed")
            cloud_available = False
        
        logger.info("🎉 Basic production environment tested successfully!")
        if cloud_available:
            logger.info("☁️  Cloud features are also available")
        else:
            logger.info("🔧 Cloud features require: sudo apt install build-essential libstdc++6")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Production test failed: {e}")
        return False

def show_help():
    """Show usage information"""
    help_text = """
🚀 VENDORA Production Launcher

Usage:
  python start_production.py [mode]

Modes:
  basic    - Start basic server (default, no cloud dependencies)
  cloud    - Start cloud-enhanced server (requires system dependencies)
  test     - Test production environment imports
  help     - Show this help message

Examples:
  python start_production.py              # Start basic server
  python start_production.py basic        # Start basic server  
  python start_production.py cloud        # Start cloud server
  python start_production.py test         # Test environment

Current Directory Requirements:
  - Run from: vendora_production/
  - Python path will be configured automatically

Production Structure:
  ├── api/          # FastAPI applications
  ├── managers/     # Business logic
  ├── config/       # Configuration
  ├── tests/        # Test suites
  └── docs/         # Documentation
    """
    print(help_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='VENDORA Production Launcher')
    parser.add_argument('mode', nargs='?', default='basic',
                       choices=['basic', 'cloud', 'test', 'help'],
                       help='Server mode (default: basic)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port number (default: 8000)')
    
    args = parser.parse_args()
    
    if args.mode == "cloud":
        start_cloud_server(args.port)
    elif args.mode == "test":
        success = test_production()
        sys.exit(0 if success else 1)
    elif args.mode == "help":
        show_help()
    else:
        start_basic_server(args.port)