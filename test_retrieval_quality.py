#!/usr/bin/env python3
"""
Test retrieval quality across different categories
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from rag.rag_workflow import retrieval
import time

def test_retrieval_quality():
    """Test retrieval across different categories"""
    
    print("="*70)
    print("RETRIEVAL QUALITY VALIDATION")
    print("="*70)
    
    # Test queries for each category
    test_queries = {
        'Authentication': [
            "How do I troubleshoot login failures?",
            "What are the best practices for SSO integration?",
            "User cannot authenticate with MFA"
        ],
        'Payment': [
            "Payment gateway timeout issues",
            "How to handle failed transactions?",
            "Refund processing best practices"
        ],
        'Api': [
            "API endpoint returning 500 errors",
            "Webhook not receiving callbacks",
            "How to optimize API performance?"
        ],
        'Database': [
            "Database connection pool exhausted",
            "Slow query performance issues",
            "Replication lag troubleshooting"
        ],
        'Network': [
            "VPN connection keeps dropping",
            "DNS resolution failures",
            "SSL certificate validation errors"
        ]
    }
    
    overall_results = {
        'total_queries': 0,
        'successful_retrievals': 0,
        'avg_response_time': 0,
        'avg_relevance': 0,
        'category_results': {}
    }
    
    total_time = 0
    
    for category, queries in test_queries.items():
        print(f"\n{'='*70}")
        print(f"Testing {category.upper()} Category")
        print('='*70)
        
        category_success = 0
        category_time = 0
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Query: {query}")
            
            start_time = time.time()
            try:
                results = retrieval.retrieve(query, filters=None, deduplicate=True)
                query_time = time.time() - start_time
                category_time += query_time
                total_time += query_time
                
                if results:
                    print(f"   ⏱️  Response time: {query_time*1000:.2f}ms")
                    print(f"   📄 Retrieved {len(results)} results:")
                    
                    for j, result in enumerate(results, 1):
                        # Check if metadata exists and has Subtype
                        metadata = result.get('metadata', {})
                        subtype = metadata.get('Subtype', 'Unknown')
                        score = result.get('score', 0)
                        text_preview = result.get('chunk', '')[:100]
                        
                        print(f"      {j}. Category: {subtype} | Relevance: {score:.3f}")
                        print(f"         Preview: {text_preview}...")
                    
                    # Check if at least one result matches the category
                    category_match = any(
                        result.get('metadata', {}).get('Subtype', '').lower() == category.lower()
                        for result in results
                    )
                    
                    if category_match:
                        category_success += 1
                        print(f"   ✓ Correct category match found")
                    else:
                        print(f"   ⚠️  No exact category match in top results")
                else:
                    print(f"   ✗ No results returned")
                    
            except Exception as e:
                print(f"   ✗ Error: {str(e)}")
                query_time = time.time() - start_time
                category_time += query_time
                total_time += query_time
        
        accuracy = (category_success / len(queries)) * 100 if len(queries) > 0 else 0
        avg_time = (category_time / len(queries)) * 1000 if len(queries) > 0 else 0
        
        overall_results['category_results'][category] = {
            'queries': len(queries),
            'successful': category_success,
            'accuracy': accuracy,
            'avg_time_ms': avg_time
        }
        
        print(f"\n{category} Category Results:")
        print(f"  Accuracy: {accuracy:.1f}% ({category_success}/{len(queries)})")
        print(f"  Avg Response Time: {avg_time:.2f}ms")
    
    # Calculate overall statistics
    total_queries = sum(len(queries) for queries in test_queries.values())
    total_successful = sum(
        results['successful'] 
        for results in overall_results['category_results'].values()
    )
    
    overall_accuracy = (total_successful / total_queries) * 100 if total_queries > 0 else 0
    avg_response_time = (total_time / total_queries) * 1000 if total_queries > 0 else 0
    
    overall_results['total_queries'] = total_queries
    overall_results['successful_retrievals'] = total_successful
    overall_results['avg_response_time'] = avg_response_time
    overall_results['overall_accuracy'] = overall_accuracy
    
    # Print overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY")
    print("="*70)
    print(f"Total Queries: {total_queries}")
    print(f"Successful Retrievals: {total_successful}")
    print(f"Overall Accuracy: {overall_accuracy:.1f}%")
    print(f"Average Response Time: {avg_response_time:.2f}ms")
    print()
    
    print("Category Breakdown:")
    for category, results in overall_results['category_results'].items():
        print(f"  {category:15} - Accuracy: {results['accuracy']:5.1f}% | "
              f"Avg Time: {results['avg_time_ms']:6.2f}ms")
    
    # Quality assessment
    print("\n" + "="*70)
    print("QUALITY ASSESSMENT")
    print("="*70)
    
    if overall_accuracy >= 80:
        print("✅ EXCELLENT - Retrieval quality meets production standards")
    elif overall_accuracy >= 60:
        print("⚠️  GOOD - Retrieval quality acceptable, minor improvements possible")
    elif overall_accuracy >= 40:
        print("⚠️  FAIR - Retrieval quality needs improvement")
    else:
        print("❌ POOR - Retrieval quality requires significant improvement")
    
    if avg_response_time < 100:
        print("✅ EXCELLENT - Response time is very fast")
    elif avg_response_time < 500:
        print("⚠️  GOOD - Response time is acceptable")
    else:
        print("⚠️  SLOW - Response time needs optimization")
    
    return overall_accuracy >= 60 and avg_response_time < 500

if __name__ == "__main__":
    try:
        success = test_retrieval_quality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
