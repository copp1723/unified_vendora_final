#!/usr/bin/env python3
"""
Test script for Firebase Authentication implementation
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.auth.firebase_auth import (
    FirebaseAuthHandler,
    FirebaseUser,
    initialize_firebase_auth
)


async def test_firebase_auth():
    """Test Firebase authentication functionality"""
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    config = {
        'FIREBASE_PROJECT_ID': os.getenv('FIREBASE_PROJECT_ID', 'vendora-analytics'),
        'FIREBASE_SERVICE_ACCOUNT_PATH': os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    }
    
    print("🔧 Testing Firebase Authentication Setup")
    print(f"Project ID: {config['FIREBASE_PROJECT_ID']}")
    print(f"Service Account: {config['FIREBASE_SERVICE_ACCOUNT_PATH']}")
    
    try:
        # Initialize Firebase Auth
        print("\n📌 Initializing Firebase Authentication...")
        initialize_firebase_auth(config)
        print("✅ Firebase Auth initialized successfully")
        
        # Get auth handler
        auth_handler = FirebaseAuthHandler(config)
        
        # Test token verification (you'll need a valid token for this)
        test_token = os.getenv('TEST_FIREBASE_TOKEN')
        if test_token:
            print("\n🔐 Testing token verification...")
            try:
                user = await auth_handler.verify_token(test_token)
                print(f"✅ Token verified successfully!")
                print(f"   User ID: {user.uid}")
                print(f"   Email: {user.email}")
                print(f"   Email Verified: {user.email_verified}")
                print(f"   Dealership ID: {user.dealership_id}")
                print(f"   Custom Claims: {user.custom_claims}")
            except Exception as e:
                print(f"❌ Token verification failed: {e}")
        else:
            print("\n⚠️  No TEST_FIREBASE_TOKEN found in environment")
            print("   To test token verification, set TEST_FIREBASE_TOKEN with a valid Firebase ID token")
        
        # Test public key fetching
        print("\n🔑 Testing public key fetching...")
        keys = await auth_handler._get_public_keys()
        print(f"✅ Successfully fetched {len(keys)} public keys")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_firebase_auth())