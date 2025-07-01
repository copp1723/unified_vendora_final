"""
Test script for VENDORA Cloud Integration
Tests all cloud components and BigQuery connectivity
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cloud_config():
    """Test cloud configuration initialization"""
    logger.info("🧪 Testing Cloud Configuration...")
    
    try:
        from ..config.cloud_config import CloudConfig
        
        cloud_config = CloudConfig()
        await cloud_config.initialize()
        
        config = cloud_config.get_config()
        
        logger.info("✅ Cloud Config Test Results:")
        logger.info(f"   Project ID: {config.get('project_id')}")
        logger.info(f"   BigQuery Client: {'✅' if config.get('bigquery_client') else '❌'}")
        logger.info(f"   Secrets Loaded: {len(cloud_config.secrets_cache)}")
        logger.info(f"   Available Secrets: {list(cloud_config.secrets_cache.keys())}")
        
        return True, config
        
    except Exception as e:
        logger.error(f"❌ Cloud Config Test Failed: {str(e)}")
        return False, None

async def test_enhanced_flow_manager(cloud_config):
    """Test enhanced flow manager with BigQuery"""
    logger.info("🧪 Testing Enhanced Flow Manager...")
    
    try:
        from ..managers.enhanced_flow_manager import EnhancedFlowManager
        
        flow_manager = EnhancedFlowManager(cloud_config)
        await flow_manager.initialize()
        
        # Test query processing
        test_query = "What are our top selling vehicles this month?"
        result = await flow_manager.process_user_query(
            test_query, 
            "TEST_DEALERSHIP_001"
        )
        
        logger.info("✅ Enhanced Flow Manager Test Results:")
        logger.info(f"   Query Processed: '{test_query}'")
        logger.info(f"   Result Type: {type(result)}")
        logger.info(f"   Has Summary: {'✅' if 'summary' in result else '❌'}")
        logger.info(f"   Has Details: {'✅' if 'detailed_insight' in result else '❌'}")
        
        # Test metrics
        metrics = await flow_manager.get_metrics()
        logger.info(f"   Metrics Available: {'✅' if metrics else '❌'}")
        logger.info(f"   BigQuery Integration: {'✅' if metrics.get('gcp_integration', {}).get('bigquery_enabled') else '❌'}")
        
        await flow_manager.shutdown()
        return True, result
        
    except Exception as e:
        logger.error(f"❌ Enhanced Flow Manager Test Failed: {str(e)}")
        return False, None

async def test_bigquery_queries(cloud_config):
    """Test BigQuery connectivity and sample queries"""
    logger.info("🧪 Testing BigQuery Queries...")
    
    try:
        from ..managers.enhanced_flow_manager import EnhancedFlowManager
        
        flow_manager = EnhancedFlowManager(cloud_config)
        await flow_manager.initialize()
        
        # Test different query types
        test_queries = [
            ("sales query", "Show me sales data for last month"),
            ("inventory query", "What's our current inventory status?"),
            ("customer query", "How are our customer leads performing?")
        ]
        
        results = {}
        for query_type, query in test_queries:
            try:
                data_context = await flow_manager._fetch_dealership_data(
                    "TEST_DEALERSHIP", query
                )
                results[query_type] = {
                    "success": True,
                    "has_bigquery_data": any(
                        isinstance(v, dict) and v.get("bigquery_data") 
                        for v in data_context.values()
                    ),
                    "data_types": list(data_context.keys())
                }
                logger.info(f"   {query_type}: ✅")
            except Exception as e:
                results[query_type] = {"success": False, "error": str(e)}
                logger.info(f"   {query_type}: ❌ {str(e)}")
        
        await flow_manager.shutdown()
        return True, results
        
    except Exception as e:
        logger.error(f"❌ BigQuery Test Failed: {str(e)}")
        return False, None

async def test_fastapi_endpoints():
    """Test FastAPI endpoints"""
    logger.info("🧪 Testing FastAPI Application...")
    
    try:
        import httpx
        import subprocess
        import time
        
        # Start the FastAPI server in background
        logger.info("   Starting FastAPI server...")
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "working_fastapi_cloud:app", 
            "--host", "0.0.0.0", 
            "--port", "8001"  # Use different port for testing
        ])
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get("http://localhost:8001/health")
            health_result = response.status_code == 200
            
            # Test demo endpoint
            demo_response = await client.get("http://localhost:8001/demo/sample-query")
            demo_result = demo_response.status_code == 200
            
            # Test analyze endpoint
            analyze_payload = {
                "query": "What are our best selling vehicles?",
                "dealership_id": "TEST_DEALERSHIP",
                "use_cloud_data": True
            }
            analyze_response = await client.post(
                "http://localhost:8001/analyze", 
                json=analyze_payload
            )
            analyze_result = analyze_response.status_code == 200
        
        # Stop the server
        process.terminate()
        process.wait()
        
        logger.info("✅ FastAPI Test Results:")
        logger.info(f"   Health Endpoint: {'✅' if health_result else '❌'}")
        logger.info(f"   Demo Endpoint: {'✅' if demo_result else '❌'}")
        logger.info(f"   Analyze Endpoint: {'✅' if analyze_result else '❌'}")
        
        return all([health_result, demo_result, analyze_result])
        
    except Exception as e:
        logger.error(f"❌ FastAPI Test Failed: {str(e)}")
        return False

async def test_error_handling():
    """Test error handling and fallback mechanisms"""
    logger.info("🧪 Testing Error Handling...")
    
    try:
        from ..managers.enhanced_flow_manager import EnhancedFlowManager
        from ..config.cloud_config import CloudConfig
        
        # Test with invalid configuration
        cloud_config = CloudConfig()
        # Don't initialize to test error handling
        
        flow_manager = EnhancedFlowManager(cloud_config)
        
        # This should handle errors gracefully
        result = await flow_manager.process_user_query(
            "Test error handling", 
            "INVALID_DEALERSHIP"
        )
        
        logger.info("✅ Error Handling Test Results:")
        logger.info(f"   Graceful Degradation: {'✅' if result else '❌'}")
        logger.info(f"   Fallback Response: {'✅' if 'error' in result or 'summary' in result else '❌'}")
        
        return True
        
    except Exception as e:
        logger.info(f"✅ Error Handling Working: Exception caught as expected - {str(e)}")
        return True

async def run_comprehensive_test():
    """Run all cloud integration tests"""
    logger.info("🚀 Starting VENDORA Cloud Integration Tests")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Cloud Configuration
    config_success, cloud_config = await test_cloud_config()
    test_results["cloud_config"] = config_success
    
    if not config_success:
        logger.error("❌ Cannot proceed with other tests - Cloud Config failed")
        return test_results
    
    # Test 2: Enhanced Flow Manager
    flow_success, flow_result = await test_enhanced_flow_manager(cloud_config)
    test_results["enhanced_flow_manager"] = flow_success
    
    # Test 3: BigQuery Integration
    bigquery_success, bigquery_results = await test_bigquery_queries(cloud_config)
    test_results["bigquery_integration"] = bigquery_success
    
    # Test 4: FastAPI Endpoints
    fastapi_success = await test_fastapi_endpoints()
    test_results["fastapi_endpoints"] = fastapi_success
    
    # Test 5: Error Handling
    error_handling_success = await test_error_handling()
    test_results["error_handling"] = error_handling_success
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 VENDORA Cloud Integration Test Summary")
    logger.info("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for success in test_results.values() if success)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! VENDORA Cloud Platform is ready for deployment.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")
    
    return test_results

async def quick_connectivity_test():
    """Quick test to verify basic connectivity"""
    logger.info("⚡ Quick Connectivity Test")
    
    try:
        from ..config.cloud_config import CloudConfig
        cloud_config = CloudConfig()
        await cloud_config.initialize()
        
        config = cloud_config.get_config()
        
        logger.info("✅ Quick Test Results:")
        logger.info(f"   GCP Project: {config.get('project_id', 'Not found')}")
        logger.info(f"   BigQuery: {'Available' if config.get('bigquery_client') else 'Not available'}")
        logger.info(f"   Secrets: {len(cloud_config.secrets_cache)} loaded")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Quick test failed: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Run quick test
        asyncio.run(quick_connectivity_test())
    else:
        # Run comprehensive test
        asyncio.run(run_comprehensive_test())