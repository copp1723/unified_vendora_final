#!/usr/bin/env python3
"""
Test script for VENDORA Working Version
Tests the minimal flow manager and API endpoints
"""

import asyncio
import json
import requests
import time
from minimal_flow_manager import MinimalFlowManager

async def test_flow_manager():
    """Test the minimal flow manager directly"""
    print("🧪 Testing Minimal Flow Manager...")
    
    config = {
        "gemini_api_key": None,  # Test without Gemini first
        "quality_threshold": 0.85
    }
    
    manager = MinimalFlowManager(config)
    await manager.initialize()
    
    # Test query processing
    result = await manager.process_user_query(
        "What were my top selling vehicles last month?",
        "dealer_123"
    )
    
    print("✅ Flow Manager Test Results:")
    print(json.dumps(result, indent=2, default=str))
    
    # Test metrics
    metrics = await manager.get_metrics()
    print(f"\n📊 Metrics: {json.dumps(metrics, indent=2)}")
    
    await manager.shutdown()
    print("✅ Flow Manager test completed\n")

def test_api_endpoints():
    """Test API endpoints if server is running"""
    print("🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return
        
        # Test query endpoint
        query_data = {
            "query": "Show me last month's sales performance",
            "dealership_id": "test_dealer_123",
            "context": {"test": True}
        }
        
        response = requests.post(
            f"{base_url}/api/v1/query",
            json=query_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Query endpoint working")
            result = response.json()
            print(f"   Summary: {result.get('summary', 'N/A')[:100]}...")
            print(f"   Confidence: {result.get('confidence_level', 'N/A')}")
        else:
            print(f"❌ Query endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Test metrics endpoint
        response = requests.get(f"{base_url}/api/v1/system/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Metrics endpoint working")
            metrics = response.json()
            print(f"   Total queries: {metrics.get('total_queries', 0)}")
            print(f"   Success rate: {metrics.get('success_rate', 0):.2%}")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            
    except requests.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Make sure the server is running: python3 working_fastapi.py")
    except requests.Timeout:
        print("❌ API request timed out")
    except Exception as e:
        print(f"❌ API test error: {str(e)}")

def main():
    print("🚀 VENDORA Working Version Test Suite")
    print("=" * 50)
    
    # Test 1: Flow Manager
    asyncio.run(test_flow_manager())
    
    # Test 2: API Endpoints (if server is running)
    test_api_endpoints()
    
    print("\n🎉 Test suite completed!")
    print("\nTo start the API server:")
    print("   python3 working_fastapi.py")
    print("\nOr use the startup script:")
    print("   chmod +x start_working.sh && ./start_working.sh")

if __name__ == "__main__":
    main()
