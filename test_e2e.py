#!/usr/bin/env python3
"""
End-to-end test with knowledge base retrieval
"""
import sys
import os
import asyncio
sys.path.insert(0, os.getcwd())

from agents.workflow import AgentWorkflow

async def test_with_kb():
    """Test agent workflow with knowledge base retrieval"""
    
    print("="*70)
    print("END-TO-END TEST WITH KNOWLEDGE BASE")
    print("="*70)
    
    print("\n1. Initializing AgentWorkflow...")
    workflow = AgentWorkflow()
    print("   ✓ Workflow initialized")
    
    # Test query that should match knowledge base
    query = "Payment API is returning 500 errors, what should I do?"
    
    print(f"\n2. Processing query:")
    print(f"   \"{query}\"")
    print("\n3. Executing agent workflow...")
    print("-"*70)
    
    try:
        result = await workflow.process_ticket(query, "E2E_TEST_001")
        
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        print(f"\n🎯 Classification:")
        print(f"   Intent: {result.get('intent', 'N/A')}")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Urgency: {result.get('urgency', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")
        
        # Check if documents were retrieved
        retrieved_docs = result.get('retrieved_docs', [])
        print(f"\n📚 Knowledge Base Retrieval:")
        print(f"   Documents Retrieved: {len(retrieved_docs)}")
        
        if retrieved_docs:
            print(f"\n   Top Retrieved Document:")
            top_doc = retrieved_docs[0]
            content = top_doc.get('content', '')
            source = top_doc.get('source', 'unknown')
            score = top_doc.get('score', 0.0)
            
            print(f"   - Source: {source}")
            print(f"   - Score: {score:.4f}")
            print(f"   - Content Preview: {content[:200]}...")
        else:
            print(f"   ⚠️  No documents retrieved from knowledge base")
        
        # Check response quality
        response = result.get('response', '')
        if response:
            print(f"\n💬 Generated Response Preview:")
            print(f"   {response[:300]}...")
            
            # Check if KB was used in response
            kb_used = any([
                'resolution steps' in response.lower(),
                'root cause' in response.lower(),
                'database connection' in response.lower(),
                'escalate to' in response.lower()
            ])
            print(f"\n✓ Knowledge Base Integration: {'YES - KB info found in response' if kb_used else 'NO - generic response'}")
        
        print("\n" + "="*70)
        print("✓ END-TO-END TEST COMPLETE")
        print("="*70)
        
        # Success metrics
        print(f"\nSuccess Metrics:")
        print(f"   ✓ Workflow executed: YES")
        print(f"   ✓ Classification accurate: {result.get('intent') == 'incident'}")
        print(f"   ✓ Documents retrieved: {len(retrieved_docs) > 0}")
        print(f"   ✓ Response generated: {len(response) > 0}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_with_kb())
