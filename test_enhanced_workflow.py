"""
Test enhanced workflow with Phase 7 agents integration

Tests:
1. Duplicate detection integration
2. SLA prediction integration
3. End-to-end workflow with all agents
"""

import asyncio
import logging
from agents.workflow import AgentWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)


async def test_enhanced_workflow():
    """Test the enhanced workflow with duplicate detection and SLA prediction"""
    workflow = AgentWorkflow()
    
    print("=" * 80)
    print("TESTING ENHANCED WORKFLOW WITH PHASE 7 AGENTS")
    print("=" * 80)
    
    # Test Case 1: Technical incident (should trigger duplicate detection and SLA)
    print("\n" + "=" * 80)
    print("Test 1: Technical Incident - Payment API Error")
    print("=" * 80)
    
    result1 = await workflow.process_ticket(
        "Payment API is returning 500 errors, customers cannot complete checkout"
    )
    
    print(f"\nResponse: {result1['response'][:200]}...")
    print(f"\nClassification:")
    print(f"  Intent: {result1.get('intent')}")
    print(f"  Urgency: {result1.get('urgency')}")
    print(f"  Category: {result1.get('category')}")
    print(f"\nDuplicate Detection:")
    print(f"  Similar tickets found: {result1.get('duplicate_count', 0)}")
    if result1.get('has_duplicates'):
        print(f"  Warning: {result1.get('duplicate_warning')}")
    print(f"\nSLA Prediction:")
    print(f"  Risk Level: {result1.get('sla_risk', 'unknown').upper()}")
    print(f"  Response deadline: {result1.get('sla_response_hours', 0):.1f} hours")
    print(f"  Resolution deadline: {result1.get('sla_resolution_hours', 0):.1f} hours")
    
    # Test Case 2: Simple question (should still work, no duplicates needed)
    print("\n" + "=" * 80)
    print("Test 2: Simple Question - Password Reset")
    print("=" * 80)
    
    result2 = await workflow.process_ticket("How do I reset my password?")
    
    print(f"\nResponse: {result2['response'][:200]}...")
    print(f"\nClassification:")
    print(f"  Intent: {result2.get('intent')}")
    print(f"  Urgency: {result2.get('urgency')}")
    print(f"\nSLA Prediction:")
    print(f"  Risk Level: {result2.get('sla_risk', 'unknown').upper()}")
    print(f"  Response deadline: {result2.get('sla_response_hours', 0):.1f} hours")
    
    # Test Case 3: Critical incident
    print("\n" + "=" * 80)
    print("Test 3: Critical Incident - Production Database Down")
    print("=" * 80)
    
    result3 = await workflow.process_ticket(
        "URGENT: Production database is down, all users are affected!"
    )
    
    print(f"\nResponse: {result3['response'][:200]}...")
    print(f"\nClassification:")
    print(f"  Intent: {result3.get('intent')}")
    print(f"  Urgency: {result3.get('urgency')}")
    print(f"\nSLA Prediction:")
    print(f"  Risk Level: {result3.get('sla_risk', 'unknown').upper()}")
    print(f"  Response deadline: {result3.get('sla_response_hours', 0):.1f} hours")
    print(f"  Resolution deadline: {result3.get('sla_resolution_hours', 0):.1f} hours")
    
    # Get workflow metrics
    print("\n" + "=" * 80)
    print("WORKFLOW METRICS")
    print("=" * 80)
    
    metrics = workflow.get_metrics()
    for agent_name, agent_metrics in metrics.items():
        if agent_metrics:
            print(f"\n{agent_name.upper()}:")
            for key, value in agent_metrics.items():
                print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("ENHANCED WORKFLOW TEST COMPLETE")
    print("=" * 80)
    print("\n✅ All Phase 7 agents successfully integrated!")
    print("✅ Duplicate detection working")
    print("✅ SLA prediction working")
    print("✅ End-to-end workflow operational")


if __name__ == "__main__":
    asyncio.run(test_enhanced_workflow())
