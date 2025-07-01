"""
Test script for VENDORA Hierarchical Flow
Demonstrates the complete L1 -> L2 -> L3 -> L1 flow
"""

import asyncio
import json
from datetime import datetime
from services.hierarchical_flow_manager import HierarchicalFlowManager
from services.explainability_engine import ExplainabilityEngine


async def test_hierarchical_flow():
    """Test the complete hierarchical flow with various queries"""
    
    print("🚀 Starting VENDORA Hierarchical Flow Test")
    print("=" * 60)
    
    # Configuration
    config = {
        "gemini_api_key": "test-api-key",  # Replace with actual key
        "bigquery_project": "vendora-test",
        "quality_threshold": 0.85
    }
    
    # Initialize components
    flow_manager = HierarchicalFlowManager(config)
    explainability_engine = ExplainabilityEngine()
    
    print("\n📋 Initializing components...")
    await flow_manager.initialize()
    await explainability_engine.start()
    print("✅ Components initialized")
    
    # Test queries of varying complexity
    test_queries = [
        {
            "query": "How many cars did we sell today?",
            "expected_complexity": "simple",
            "dealership_id": "dealer_123"
        },
        {
            "query": "What were the sales trends for SUVs over the last 3 months?",
            "expected_complexity": "standard",
            "dealership_id": "dealer_123"
        },
        {
            "query": "Forecast next quarter's revenue based on historical data and market trends",
            "expected_complexity": "complex",
            "dealership_id": "dealer_123"
        },
        {
            "query": "Should we invest $2M in expanding our EV inventory given market conditions?",
            "expected_complexity": "critical",
            "dealership_id": "dealer_123"
        }
    ]
    
    # Process each query
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test_case['expected_complexity'].upper()} Query")
        print(f"Query: {test_case['query']}")
        print(f"{'='*60}")
        
        # Start tracking agent activity
        explainability_engine.start_agent_activity(
            "orchestrator", 
            f"TEST-{i}"
        )
        
        # Process query through hierarchical flow
        start_time = datetime.now()
        
        try:
            result = await flow_manager.process_user_query(
                user_query=test_case['query'],
                dealership_id=test_case['dealership_id'],
                user_context={"test_case": i}
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Display results
            print(f"\n✅ Query processed successfully in {processing_time:.2f} seconds")
            print(f"\nResult Summary:")
            print(f"  - Task ID: {result.get('metadata', {}).get('task_id')}")
            print(f"  - Complexity: {result.get('metadata', {}).get('complexity')}")
            print(f"  - Processing Time: {result.get('metadata', {}).get('processing_time_ms')}ms")
            print(f"  - Revisions: {result.get('metadata', {}).get('revision_count')}")
            
            if 'summary' in result:
                print(f"\nInsight Summary:")
                print(f"  {result['summary'][:200]}...")
            
            if 'error' in result:
                print(f"\n❌ Error: {result['error']}")
            
            # Get flow status
            task_id = result.get('metadata', {}).get('task_id')
            if task_id:
                flow_status = await flow_manager.get_flow_status(task_id)
                print(f"\nFlow Status:")
                print(f"  - Status: {flow_status['status']}")
                print(f"  - Draft Insights: {flow_status['draft_insights_count']}")
                print(f"  - Validated: {flow_status['has_validated_insight']}")
            
            # Get agent explanation
            explanation = explainability_engine.get_agent_explanation("orchestrator")
            print(f"\nAgent Activity Summary:")
            print(f"  - Operations: {explanation['operations']['total']}")
            print(f"  - Success Rate: {explanation['operations']['success_rate']:.1%}")
            
        except Exception as e:
            print(f"\n❌ Error processing query: {str(e)}")
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Display final metrics
    print(f"\n{'='*60}")
    print("📊 Final System Metrics")
    print(f"{'='*60}")
    
    metrics = await flow_manager.get_metrics()
    print(f"\nFlow Manager Metrics:")
    print(f"  - Total Queries: {metrics['total_queries']}")
    print(f"  - Approved Insights: {metrics['approved_insights']}")
    print(f"  - Rejected Insights: {metrics['rejected_insights']}")
    print(f"  - Approval Rate: {metrics['approval_rate']:.1%}")
    print(f"  - Avg Processing Time: {metrics['avg_processing_time_ms']:.0f}ms")
    
    print(f"\nComplexity Distribution:")
    for complexity, count in metrics['complexity_distribution'].items():
        print(f"  - {complexity}: {count}")
    
    system_overview = explainability_engine.get_system_overview()
    print(f"\nExplainability Engine Overview:")
    print(f"  - Total Operations: {system_overview['total_operations']}")
    print(f"  - Error Rate: {system_overview['error_rate']:.1%}")
    
    # Shutdown
    print("\n🛑 Shutting down test...")
    await flow_manager.shutdown()
    await explainability_engine.stop()
    print("✅ Test complete!")


async def test_revision_flow():
    """Test the revision flow when Master Analyst requests changes"""
    
    print("\n🔄 Testing Revision Flow")
    print("=" * 60)
    
    # This would simulate a case where the Master Analyst
    # requests revisions from the Specialist Agent
    
    # Configuration with lower quality threshold to trigger revisions
    config = {
        "gemini_api_key": "test-api-key",
        "bigquery_project": "vendora-test",
        "quality_threshold": 0.95  # Higher threshold to trigger more revisions
    }
    
    flow_manager = HierarchicalFlowManager(config)
    await flow_manager.initialize()
    
    # Query that might need revision
    result = await flow_manager.process_user_query(
        user_query="Analyze our customer churn rate and provide retention strategies",
        dealership_id="dealer_123",
        user_context={"require_high_quality": True}
    )
    
    print(f"\nRevision Test Result:")
    print(f"  - Revisions Required: {result.get('metadata', {}).get('revision_count', 0)}")
    
    await flow_manager.shutdown()


async def test_error_handling():
    """Test error handling in the hierarchical flow"""
    
    print("\n❌ Testing Error Handling")
    print("=" * 60)
    
    config = {
        "gemini_api_key": "invalid-key",  # Invalid key to trigger errors
        "bigquery_project": "vendora-test",
        "quality_threshold": 0.85
    }
    
    flow_manager = HierarchicalFlowManager(config)
    
    try:
        await flow_manager.initialize()
        
        # Query that might cause errors
        result = await flow_manager.process_user_query(
            user_query="SELECT * FROM non_existent_table",  # Malformed query
            dealership_id="invalid_dealer",
            user_context={}
        )
        
        if 'error' in result:
            print(f"✅ Error handled gracefully: {result['error']}")
        
    except Exception as e:
        print(f"✅ Exception caught: {str(e)}")
    
    await flow_manager.shutdown()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║          VENDORA Hierarchical Flow Test Suite            ║
║                                                          ║
║  Testing L1 -> L2 -> L3 -> L1 Agent Architecture       ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run tests
    asyncio.run(test_hierarchical_flow())
    asyncio.run(test_revision_flow())
    asyncio.run(test_error_handling())
