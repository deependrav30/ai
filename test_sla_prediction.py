"""
Test script for SLA breach prediction

This demonstrates:
1. SLA calculation for different urgency levels
2. Complexity-adjusted resolution times
3. Breach risk assessment
4. Historical data integration for better predictions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from agents.sla_predictor_agent import SLAPredictorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)


async def test_sla_predictions():
    """Test SLA predictions for various scenarios"""
    agent = SLAPredictorAgent()
    
    print("=" * 80)
    print("TESTING SLA BREACH PREDICTION")
    print("=" * 80)
    
    # Test Case 1: Critical ticket just created
    print("\n" + "=" * 80)
    print("Test 1: Critical ticket - just created")
    print("=" * 80)
    result = await agent.process({
        'urgency': 'critical',
        'complexity': 'moderate',
        'category': 'infrastructure',
        'created_at': datetime.now()
    })
    print(agent.format_sla_summary(result))
    
    # Test Case 2: High urgency ticket created 1.5 hours ago
    print("\n" + "=" * 80)
    print("Test 2: High urgency ticket - created 1.5 hours ago")
    print("=" * 80)
    result = await agent.process({
        'urgency': 'high',
        'complexity': 'complex',
        'category': 'application',
        'created_at': datetime.now() - timedelta(hours=1.5)
    })
    print(agent.format_sla_summary(result))
    
    # Test Case 3: Medium urgency with historical data
    print("\n" + "=" * 80)
    print("Test 3: Medium urgency - with similar ticket history")
    print("=" * 80)
    similar_tickets = [
        {'resolution_time_hours': 18.5},
        {'resolution_time_hours': 22.0},
        {'resolution_time_hours': 16.0}
    ]
    result = await agent.process({
        'urgency': 'medium',
        'complexity': 'moderate',
        'category': 'general',
        'created_at': datetime.now() - timedelta(hours=3),
        'similar_tickets': similar_tickets
    })
    print(agent.format_sla_summary(result))
    print(f"\nNote: Resolution time adjusted from 24h to {result['sla_config']['adjusted_resolution_time_hours']:.1f}h based on historical avg of 18.8h")
    
    # Test Case 4: Critical ticket approaching breach
    print("\n" + "=" * 80)
    print("Test 4: Critical ticket - approaching response deadline")
    print("=" * 80)
    result = await agent.process({
        'urgency': 'critical',
        'complexity': 'simple',
        'category': 'access',
        'created_at': datetime.now() - timedelta(minutes=55)  # 5 mins until response SLA
    })
    print(agent.format_sla_summary(result))
    
    # Test Case 5: Low urgency ticket breached
    print("\n" + "=" * 80)
    print("Test 5: Low urgency ticket - SLA already breached")
    print("=" * 80)
    result = await agent.process({
        'urgency': 'low',
        'complexity': 'moderate',
        'category': 'question',
        'created_at': datetime.now() - timedelta(hours=50)  # Past 48h resolution SLA
    })
    print(agent.format_sla_summary(result))
    
    # Test Case 6: Very complex high urgency ticket
    print("\n" + "=" * 80)
    print("Test 6: High urgency very complex ticket")
    print("=" * 80)
    result = await agent.process({
        'urgency': 'high',
        'complexity': 'very_complex',
        'category': 'integration',
        'created_at': datetime.now()
    })
    print(agent.format_sla_summary(result))
    print(f"\nNote: Resolution time increased from 8h to {result['sla_config']['adjusted_resolution_time_hours']:.1f}h due to very_complex multiplier (2.0x)")
    
    print("\n" + "=" * 80)
    print("SLA PREDICTION TEST COMPLETE")
    print("=" * 80)
    
    # Summary table
    print("\n" + "=" * 80)
    print("SLA TIME WINDOWS REFERENCE")
    print("=" * 80)
    print(f"{'Urgency':<12} {'Response':<12} {'Resolution':<12}")
    print("-" * 80)
    for urgency, times in agent.SLA_WINDOWS.items():
        print(f"{urgency:<12} {times['response_time']:<12}h {times['resolution_time']:<12}h")
    
    print(f"\n{'Complexity':<15} {'Multiplier':<12} {'Effect':<30}")
    print("-" * 80)
    for complexity, mult in agent.COMPLEXITY_MULTIPLIERS.items():
        effect = f"{mult:+.0%} time" if mult != 1.0 else "Normal time"
        print(f"{complexity:<15} {mult:<12.1f}x {effect:<30}")


if __name__ == "__main__":
    asyncio.run(test_sla_predictions())
