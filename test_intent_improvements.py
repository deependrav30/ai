"""
Test Enhanced IntentAgent with Keyword Matching
"""

from agents.intent_agent import IntentAgent
import asyncio


async def main():
    agent = IntentAgent()
    
    test_cases = [
        ("Payment API is returning 500 errors, what should I do?", "incident", "high"),
        ("How do I reset my password?", "question", "low"),
        ("Production database is down, all users affected!", "incident", "critical"),
        ("Can you create a new user account for John Doe?", "service_request", "medium"),
        ("API latency is intermittently high, need root cause analysis", "problem", "medium")
    ]
    
    print("="*70)
    print("TESTING ENHANCED INTENT AGENT WITH KEYWORD MATCHING")
    print("="*70)
    
    correct_intent = 0
    correct_urgency = 0
    
    for i, (test_input, exp_intent, exp_urgency) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_input}")
        
        state = {
            "user_input": test_input,
            "ticket_id": f"TEST_{i}"
        }
        
        result = await agent.process(state)
        
        intent = result.get('intent', 'unknown')
        urgency = result.get('urgency', 'unknown')
        confidence = result.get('confidence', 0)
        
        print(f"  Result: intent={intent}, urgency={urgency}, confidence={confidence:.2f}")
        print(f"  Expected: intent={exp_intent}, urgency={exp_urgency}")
        
        if intent == exp_intent:
            print(f"  ✓ Intent correct")
            correct_intent += 1
        else:
            print(f"  ✗ Intent WRONG")
        
        if urgency == exp_urgency:
            print(f"  ✓ Urgency correct")
            correct_urgency += 1
        else:
            print(f"  ✗ Urgency wrong")
    
    print(f"\n{'='*70}")
    print(f"RESULTS:")
    print(f"Intent Accuracy: {correct_intent}/{len(test_cases)} ({correct_intent/len(test_cases)*100:.0f}%)")
    print(f"Urgency Accuracy: {correct_urgency}/{len(test_cases)} ({correct_urgency/len(test_cases)*100:.0f}%)")
    print(f"{'='*70}")
    
    improvement = ""
    if correct_intent == len(test_cases):
        improvement += "\n✓ Intent classification at 100% - EXCELLENT!"
    elif correct_intent >= len(test_cases) * 0.9:
        improvement += f"\n✓ Intent classification at {correct_intent/len(test_cases)*100:.0f}% - GOOD"
    
    if correct_urgency >= len(test_cases) * 0.8:
        improvement += f"\n✓ Urgency classification at {correct_urgency/len(test_cases)*100:.0f}% - IMPROVED!"
    
    print(improvement)


if __name__ == "__main__":
    asyncio.run(main())
