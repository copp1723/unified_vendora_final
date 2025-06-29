#!/usr/bin/env python3
"""
VENDORA - Automotive AI Data Platform
Main entry point for the application.
"""

from enhanced_main import create_app
import os
from dotenv import load_dotenv

if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Configuration
    config = {
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
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        print(f"❌ Missing required configuration: {missing_keys}")
        print("Please check your .env file")
        exit(1)
    
    # Create and run the app
    app = create_app(config)
    
    print("🚀 Starting VENDORA platform...")
    print("📊 Automotive AI Data Platform")
    print("🌐 Access at: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

