#!/usr/bin/env python3
"""
Test script to generate data for Observability Dashboard
Runs multiple queries through the agent system to populate metrics
"""
import sys
import os
import asyncio
from datetime import datetime
sys.path.insert(0, os.getcwd())

from agents.workflow import AgentWorkflow

# Test queries with different characteristics
TEST_QUERIES = [
    {
        "query": "Payment API returning 500 errors affecting multiple customers",
        "expected_intent": "incident",
        "expected_urgency": "high"
    },
    {
        "query": "How do I reset my password?",
        "expected_intent": "question",
        "expected_urgency": "low"
    },
    {
        "query": "Request access to production database for new team member",
        "expected_intent": "service_request",
        "expected_urgency": "medium"
    },
    {
        "query": "Database performance degrading over past week, queries taking 10x longer",
        "expected_intent": "problem",
        "expected_urgency": "high"
    },
    {
        "query": "Need to upgrade Node.js version from 16 to 18 in production",
        "expected_intent": "change",
        "expected_urgency": "medium"
    },
    {
        "query": "What are your support hours?",
        "expected_intent": "question",
        "expected_urgency": "low"
    },
    {
        "query": "Critical: Application crashed, all users unable to login",
        "expected_intent": "incident",
        "expected_urgency": "critical"
    },
    {
        "query": "Request VPN access for remote work",
        "expected_intent": "service_request",
        "expected_urgency": "low"
    }
]

async def run_observability_test():
    """Run multiple queries to generate observability data"""
    
    print("="*70)
    print("OBSERVABILITY DASHBOARD DATA GENERATION TEST")
    print("="*70)
    
    print("\n1. Initializing AgentWorkflow...")
    workflow = AgentWorkflow()
    print("   ✓ Workflow initialized")
    
    results = []
    
    print(f"\n2. Processing {len(TEST_QUERIES)} test queries...")
    print("-"*70)
    
    for i, test_case in enumerate(TEST_QUERIES, 1):
        query = test_case["query"]
        ticket_id = f"OBS_TEST_{i:03d}"
        
        print(f"\n[{i}/{len(TEST_QUERIES)}] Processing: {ticket_id}")
        print(f"   Query: {query[:60]}...")
        
        try:
            result = await workflow.process_ticket(query, ticket_id)
            
            # Extract key metrics
            intent = result.get('intent', 'N/A')
            urgency = result.get('urgency', 'N/A')
            confidence = result.get('confidence', 0)
            execution_mode = result.get('execution_mode', 'N/A')
            escalate = result.get('escalate', False)
            
            print(f"   ✓ Intent: {intent} | Urgency: {urgency} | Confidence: {confidence:.2f}")
            print(f"   ✓ Mode: {execution_mode} | Escalate: {escalate}")
            
            results.append({
                "ticket_id": ticket_id,
                "query": query,
                "intent": intent,
                "urgency": urgency,
                "confidence": confidence,
                "execution_mode": execution_mode,
                "escalate": escalate,
                "expected_intent": test_case["expected_intent"],
                "expected_urgency": test_case["expected_urgency"]
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "ticket_id": ticket_id,
                "query": query,
                "error": str(e)
            })
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"\n✓ Successful: {len(successful)}/{len(TEST_QUERIES)}")
    print(f"❌ Failed: {len(failed)}/{len(TEST_QUERIES)}")
    
    # Classification accuracy
    if successful:
        intent_matches = sum(1 for r in successful if r['intent'] == r['expected_intent'])
        urgency_matches = sum(1 for r in successful if r['urgency'] == r['expected_urgency'])
        
        print(f"\n📊 Classification Accuracy:")
        print(f"   Intent: {intent_matches}/{len(successful)} ({intent_matches/len(successful)*100:.0f}%)")
        print(f"   Urgency: {urgency_matches}/{len(successful)} ({urgency_matches/len(successful)*100:.0f}%)")
    
    # Distribution stats
    if successful:
        print(f"\n📈 Distribution:")
        
        # Intent distribution
        intents = {}
        for r in successful:
            intent = r['intent']
            intents[intent] = intents.get(intent, 0) + 1
        print(f"   Intents: {intents}")
        
        # Urgency distribution
        urgencies = {}
        for r in successful:
            urgency = r['urgency']
            urgencies[urgency] = urgencies.get(urgency, 0) + 1
        print(f"   Urgencies: {urgencies}")
        
        # Execution modes
        modes = {}
        for r in successful:
            mode = r['execution_mode']
            modes[mode] = modes.get(mode, 0) + 1
        print(f"   Execution Modes: {modes}")
        
        # Escalations
        escalated = sum(1 for r in successful if r['escalate'])
        print(f"   Escalations: {escalated}/{len(successful)} ({escalated/len(successful)*100:.0f}%)")
        
        # Avg confidence
        avg_conf = sum(r['confidence'] for r in successful) / len(successful)
        print(f"   Avg Confidence: {avg_conf:.2f}")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Open Streamlit UI: http://localhost:8501")
    print("2. Navigate to '📊 Observability' page")
    print("3. Verify metrics are displaying correctly:")
    print("   - Total requests should show 8 (or more)")
    print("   - Charts should show distribution of intents, urgencies, modes")
    print("   - Execution logs should show all test tickets")
    print("\n✓ Test data generation complete!")
    print("="*70)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_observability_test())
