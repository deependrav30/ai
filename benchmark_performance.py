#!/usr/bin/env python3
"""
Performance benchmarking for ingestion and retrieval
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from rag.rag_workflow import index_document, retrieval
import time
import tempfile
import statistics

def benchmark_ingestion():
    """Benchmark document ingestion performance"""
    
    print("="*70)
    print("INGESTION PERFORMANCE BENCHMARK")
    print("="*70)
    
    # Create test documents of various sizes
    test_docs = [
        ("small", 500),      # 500 characters
        ("medium", 2000),    # 2K characters
        ("large", 10000),    # 10K characters
        ("xlarge", 50000)    # 50K characters
    ]
    
    results = {}
    
    for doc_type, size in test_docs:
        print(f"\n{doc_type.upper()} Document ({size} chars)")
        print("-" * 70)
        
        # Create temporary document
        content = "Test content. " * (size // 14)  # ~14 chars per repetition
        
        times = []
        for i in range(3):  # 3 runs for average
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                metadata = {
                    'Type': 'Test',
                    'Subtype': 'Benchmark',
                    'Priority': 'P2',
                    'Uploaded By': 'Benchmark Script',
                    'Timestamp': '2026-02-01T00:00:00',
                    'Source': 'performance_test'
                }
                
                start_time = time.time()
                index_document(temp_path, metadata)
                elapsed = time.time() - start_time
                times.append(elapsed)
                
                print(f"  Run {i+1}: {elapsed*1000:.2f}ms")
                
            finally:
                os.unlink(temp_path)
        
        avg_time = statistics.mean(times) * 1000
        std_dev = statistics.stdev(times) * 1000 if len(times) > 1 else 0
        
        results[doc_type] = {
            'size': size,
            'avg_time_ms': avg_time,
            'std_dev_ms': std_dev,
            'throughput_chars_per_sec': size / (avg_time / 1000)
        }
        
        print(f"\n  Average: {avg_time:.2f}ms (±{std_dev:.2f}ms)")
        print(f"  Throughput: {results[doc_type]['throughput_chars_per_sec']:.0f} chars/sec")
    
    return results


def benchmark_retrieval():
    """Benchmark retrieval performance with different query complexities"""
    
    print("\n" + "="*70)
    print("RETRIEVAL PERFORMANCE BENCHMARK")
    print("="*70)
    
    test_queries = {
        'simple': [
            "login",
            "password",
            "error"
        ],
        'moderate': [
            "login failure troubleshooting",
            "payment gateway timeout",
            "database connection issues"
        ],
        'complex': [
            "How do I troubleshoot authentication failures when users cannot log in with SSO?",
            "What are the best practices for handling payment gateway timeouts and retries?",
            "Database connection pool exhausted and queries are timing out frequently"
        ]
    }
    
    results = {}
    
    for complexity, queries in test_queries.items():
        print(f"\n{complexity.upper()} Queries")
        print("-" * 70)
        
        times = []
        for query in queries:
            print(f"  Query: {query[:60]}...")
            
            query_times = []
            for _ in range(3):  # 3 runs for average
                start_time = time.time()
                retrieval.retrieve(query, filters=None, deduplicate=True)
                elapsed = time.time() - start_time
                query_times.append(elapsed)
            
            avg_time = statistics.mean(query_times)
            times.append(avg_time)
            print(f"    {avg_time*1000:.2f}ms")
        
        overall_avg = statistics.mean(times) * 1000
        overall_std = statistics.stdev(times) * 1000 if len(times) > 1 else 0
        
        results[complexity] = {
            'queries': len(queries),
            'avg_time_ms': overall_avg,
            'std_dev_ms': overall_std,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000
        }
        
        print(f"\n  Average: {overall_avg:.2f}ms (±{overall_std:.2f}ms)")
        print(f"  Min/Max: {results[complexity]['min_time_ms']:.2f}ms / {results[complexity]['max_time_ms']:.2f}ms")
    
    return results


def print_summary(ingestion_results, retrieval_results):
    """Print comprehensive summary of benchmarks"""
    
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    
    print("\n📝 INGESTION BENCHMARKS:")
    print(f"{'Document Size':<15} {'Avg Time':<15} {'Throughput':<20}")
    print("-" * 70)
    for doc_type, data in ingestion_results.items():
        print(f"{doc_type.capitalize():<15} {data['avg_time_ms']:>10.2f}ms    "
              f"{data['throughput_chars_per_sec']:>15.0f} chars/sec")
    
    print("\n🔍 RETRIEVAL BENCHMARKS:")
    print(f"{'Query Type':<15} {'Avg Time':<15} {'Min/Max':<25}")
    print("-" * 70)
    for complexity, data in retrieval_results.items():
        print(f"{complexity.capitalize():<15} {data['avg_time_ms']:>10.2f}ms    "
              f"{data['min_time_ms']:>7.2f} / {data['max_time_ms']:<7.2f}ms")
    
    # Performance rating
    print("\n" + "="*70)
    print("PERFORMANCE RATING")
    print("="*70)
    
    # Check ingestion performance
    avg_ingestion = statistics.mean([r['avg_time_ms'] for r in ingestion_results.values()])
    if avg_ingestion < 500:
        print("✅ Ingestion: EXCELLENT (< 500ms avg)")
    elif avg_ingestion < 1000:
        print("⚠️  Ingestion: GOOD (< 1s avg)")
    else:
        print("❌ Ingestion: SLOW (> 1s avg)")
    
    # Check retrieval performance
    avg_retrieval = statistics.mean([r['avg_time_ms'] for r in retrieval_results.values()])
    if avg_retrieval < 100:
        print("✅ Retrieval: EXCELLENT (< 100ms avg)")
    elif avg_retrieval < 500:
        print("⚠️  Retrieval: GOOD (< 500ms avg)")
    else:
        print("❌ Retrieval: SLOW (> 500ms avg)")
    
    print(f"\nOverall System Latency: ~{avg_ingestion + avg_retrieval:.2f}ms per document+query cycle")
    
    return avg_ingestion < 1000 and avg_retrieval < 500


def main():
    print("Starting performance benchmarks...")
    print("This will test ingestion and retrieval performance.\n")
    
    try:
        # Run benchmarks
        ingestion_results = benchmark_ingestion()
        retrieval_results = benchmark_retrieval()
        
        # Print summary
        success = print_summary(ingestion_results, retrieval_results)
        
        print("\n✅ Performance benchmarking complete!")
        return success
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
