#!/usr/bin/env python3
"""
Test script for multi-agent workflow
"""
import sys
import os
import asyncio
sys.path.insert(0, os.getcwd())

from agents.workflow import AgentWorkflow

async def test_agent_workflow():
    """Test the multi-agent workflow with a sample query"""
    
    print("="*60)
    print("MULTI-AGENT WORKFLOW TEST")
    print("="*60)
    
    print("\n1. Initializing AgentWorkflow...")
    try:
        workflow = AgentWorkflow()
        print("   ✓ Workflow initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return
    
    # Test query
    test_query = "Our payment API is returning 500 errors for the past 2 hours. Multiple customers affected."
    test_ticket_id = "test_001"
    
    print("\n2. Testing with sample query:")
    print(f"   Query: {test_query}")
    print("\n3. Processing ticket through agent workflow...")
    
    # Process the ticket
    try:
        result = await workflow.process_ticket(test_query, test_ticket_id)
        
        print("\n" + "="*60)
        print("AGENT WORKFLOW RESULTS")
        print("="*60)
        
        print(f"\n🎯 Intent: {result.get('intent', 'N/A')}")
        print(f"📊 Category: {result.get('category', 'N/A')}")
        print(f"🚨 Urgency: {result.get('urgency', 'N/A')}")
        print(f"✨ Confidence: {result.get('confidence', 0):.2f}")
        print(f"⚡ Execution Mode: {result.get('execution_mode', 'N/A')}")
        
        if result.get('patterns_detected'):
            print(f"\n⚠️  Patterns Detected:")
            for pattern in result['patterns_detected']:
                print(f"   - {pattern}")
        
        if result.get('response'):
            response = result['response']
            print(f"\n💬 Response Preview:")
            # Show first 300 chars for better visibility
            if len(response) > 300:
                print(f"   {response[:300]}...")
                print(f"   ... (Total length: {len(response)} characters)")
            else:
                print(f"   {response}")
        
        if result.get('escalate'):
            print(f"\n🚀 Escalation: Required")
            print(f"   Team: {result.get('escalate_to', 'N/A')}")
        
        agents_used = result.get('agents_used', [])
        if agents_used:
            print(f"\n🤖 Agents Executed: {', '.join(agents_used)}")
        
        print("\n" + "="*60)
        print("✓ Multi-agent workflow test PASSED")
        print("="*60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_agent_workflow())
