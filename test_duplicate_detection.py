"""
Test script for duplicate ticket detection

This demonstrates:
1. Adding historical tickets to ChromaDB
2. Detecting duplicates for new tickets
3. Categorizing by similarity levels
"""

import asyncio
import logging
from agents.duplicate_detector_agent import DuplicateDetectorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Sample historical tickets
HISTORICAL_TICKETS = [
    {
        'ticket_id': 'TICK-1001',
        'title': 'Payment API returning 500 errors',
        'description': 'Users are reporting that payment processing is failing with HTTP 500 errors. Started around 2pm.',
        'metadata': {
            'status': 'resolved',
            'resolution': 'Database connection pool exhausted, increased pool size',
            'priority': 'P1',
            'created_at': '2026-01-15T14:00:00Z',
            'resolved_at': '2026-01-15T15:30:00Z'
        }
    },
    {
        'ticket_id': 'TICK-1002',
        'title': 'How to reset password',
        'description': 'User John Doe needs help resetting his password. Forgot password link not working.',
        'metadata': {
            'status': 'resolved',
            'resolution': 'Sent manual password reset link',
            'priority': 'P3',
            'created_at': '2026-01-16T10:00:00Z',
            'resolved_at': '2026-01-16T10:15:00Z'
        }
    },
    {
        'ticket_id': 'TICK-1003',
        'title': 'Production database connectivity issues',
        'description': 'Multiple services reporting database connection timeouts. Production is impacted.',
        'metadata': {
            'status': 'resolved',
            'resolution': 'Network switch failure, rerouted traffic',
            'priority': 'P0',
            'created_at': '2026-01-17T08:00:00Z',
            'resolved_at': '2026-01-17T08:45:00Z'
        }
    },
    {
        'ticket_id': 'TICK-1004',
        'title': 'API latency high during peak hours',
        'description': 'Response times spike to 5+ seconds during 9am-11am. Need performance optimization.',
        'metadata': {
            'status': 'in_progress',
            'priority': 'P2',
            'created_at': '2026-01-18T12:00:00Z'
        }
    },
    {
        'ticket_id': 'TICK-1005',
        'title': 'Payment gateway timeout errors',
        'description': 'Payment processing intermittently timing out. Error rate around 5%.',
        'metadata': {
            'status': 'resolved',
            'resolution': 'Gateway provider had outage, switched to backup',
            'priority': 'P1',
            'created_at': '2026-01-19T16:00:00Z',
            'resolved_at': '2026-01-19T17:00:00Z'
        }
    }
]

# New tickets to test against
NEW_TICKETS = [
    {
        'ticket_id': 'TICK-2001',
        'title': 'Payment API 500 error spam',
        'description': 'Getting tons of 500 errors from payment API. Started about an hour ago.',
        'expected': 'Should find TICK-1001 as very similar (same issue)'
    },
    {
        'ticket_id': 'TICK-2002',
        'title': 'Cannot reset my account password',
        'description': 'I forgot my password and the reset link in email is not working.',
        'expected': 'Should find TICK-1002 as very similar (password reset)'
    },
    {
        'ticket_id': 'TICK-2003',
        'title': 'Slow API performance in morning hours',
        'description': 'Our API calls are very slow between 9-11am every day.',
        'expected': 'Should find TICK-1004 as similar (performance issue)'
    },
    {
        'ticket_id': 'TICK-2004',
        'title': 'New feature request: dark mode',
        'description': 'Would love to have a dark mode option in the dashboard.',
        'expected': 'Should find no duplicates (unique request)'
    }
]


async def populate_ticket_history(agent: DuplicateDetectorAgent):
    """Add historical tickets to ChromaDB"""
    print("=" * 80)
    print("POPULATING TICKET HISTORY")
    print("=" * 80)
    
    for ticket in HISTORICAL_TICKETS:
        await agent.add_ticket_to_history(
            ticket_id=ticket['ticket_id'],
            ticket_title=ticket['title'],
            ticket_description=ticket['description'],
            metadata=ticket['metadata']
        )
        print(f"✓ Added {ticket['ticket_id']}: {ticket['title']}")
    
    print(f"\n✓ Loaded {len(HISTORICAL_TICKETS)} historical tickets\n")


async def test_duplicate_detection(agent: DuplicateDetectorAgent):
    """Test duplicate detection on new tickets"""
    print("=" * 80)
    print("TESTING DUPLICATE DETECTION")
    print("=" * 80)
    
    for i, ticket in enumerate(NEW_TICKETS, 1):
        print(f"\nTest {i}: {ticket['title']}")
        print(f"Expected: {ticket['expected']}")
        print("-" * 80)
        
        # Run duplicate detection
        result = await agent.process({
            'ticket_id': ticket['ticket_id'],
            'ticket_title': ticket['title'],
            'ticket_description': ticket['description']
        })
        
        # Print summary
        duplicates = result['duplicates']
        summary = agent.get_duplicate_summary(duplicates)
        print(f"\n{summary}\n")
        
        # Show top matches
        all_matches = []
        for category in ['exact_duplicate', 'very_similar', 'similar', 'related']:
            all_matches.extend(duplicates.get(category, []))
        
        if all_matches:
            print("Top matches:")
            for match in all_matches[:3]:
                print(f"  • {match['ticket_id']} ({match['similarity']:.1%} similar)")
                print(f"    {match['metadata'].get('title', 'No title')}")
                if 'resolution' in match['metadata']:
                    print(f"    Resolution: {match['metadata']['resolution']}")
        else:
            print("No similar tickets found")
        
        print()


async def main():
    """Main test function"""
    agent = DuplicateDetectorAgent()
    
    # Populate ticket history
    await populate_ticket_history(agent)
    
    # Test duplicate detection
    await test_duplicate_detection(agent)
    
    print("=" * 80)
    print("DUPLICATE DETECTION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
