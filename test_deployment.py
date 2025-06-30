#!/usr/bin/env python3
"""
VENDORA Deployment Test Script
Tests the deployed service endpoints to verify functionality.
"""

import requests
import sys
import json
from typing import Dict, Any

def test_endpoint(url: str, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
    """Test a single endpoint and return results."""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        response = requests.get(full_url, timeout=10)
        
        result = {
            "endpoint": endpoint,
            "url": full_url,
            "status_code": response.status_code,
            "success": response.status_code == expected_status,
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get("content-type", ""),
        }
        
        # Try to parse JSON response
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            "endpoint": endpoint,
            "url": full_url,
            "status_code": None,
            "success": False,
            "error": str(e),
            "response_time": None
        }

def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python test_deployment.py <service-url>")
        print("Example: python test_deployment.py https://vendora-api-xyz-uc.a.run.app")
        sys.exit(1)
    
    service_url = sys.argv[1]
    
    # Test endpoints
    endpoints_to_test = [
        "/",
        "/health",
        "/api/v1/status",
        "/docs",  # FastAPI auto-generated docs
    ]
    
    print(f"🧪 Testing VENDORA deployment at: {service_url}")
    print("=" * 60)
    
    all_passed = True
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"Testing {endpoint}...", end=" ")
        result = test_endpoint(service_url, endpoint)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {result['status_code']} ({result['response_time']:.2f}s)")
        else:
            print(f"❌ {result.get('status_code', 'ERROR')}")
            if "error" in result:
                print(f"   Error: {result['error']}")
            all_passed = False
    
    print("=" * 60)
    
    # Summary
    if all_passed:
        print("🎉 All tests passed! Deployment is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    
    # Detailed results
    print("\n📊 Detailed Results:")
    print(json.dumps(results, indent=2))
    
    # Health check specific info
    health_result = next((r for r in results if r["endpoint"] == "/health"), None)
    if health_result and health_result["success"]:
        print(f"\n💚 Service Health: {health_result['response'].get('status', 'unknown')}")
        print(f"🏷️  Version: {health_result['response'].get('version', 'unknown')}")
        print(f"🌍 Environment: {health_result['response'].get('environment', 'unknown')}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())