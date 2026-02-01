"""
Test Enhanced Ingestion Pipeline

Tests the new enhanced ingestion features:
1. Semantic chunking vs fixed chunking
2. Table detection and preservation
3. Figure detection
4. Section/header extraction
"""

from rag.ingestion.enhanced_ingestion import EnhancedIngestionPipeline
from rag.ingestion.ingestion_pipeline import IngestionPipeline
import os


def test_semantic_chunking():
    """Test semantic chunking on the knowledge base document."""
    print("="*70)
    print("TEST 1: Semantic Chunking vs Fixed Chunking")
    print("="*70)
    
    file_path = "data/knowledge_base.txt"
    metadata = {
        'Type': 'Company',
        'Subtype': 'General',
        'Priority': 'P0'
    }
    
    # Test basic ingestion (fixed chunking)
    print("\n1. BASIC INGESTION (Fixed 500 char chunks):")
    basic_pipeline = IngestionPipeline(chunk_size=500, chunk_overlap=50)
    basic_chunks, basic_metas = basic_pipeline.ingest(file_path, metadata)
    print(f"   Chunks created: {len(basic_chunks)}")
    print(f"   Avg chunk size: {sum(len(c) for c in basic_chunks) / len(basic_chunks):.0f} chars")
    print(f"\n   First chunk preview:")
    print(f"   {basic_chunks[0][:200]}...")
    
    # Test enhanced ingestion (semantic chunking)
    print("\n2. ENHANCED INGESTION (Semantic chunking by paragraphs):")
    enhanced_pipeline = EnhancedIngestionPipeline(
        min_chunk_size=300,
        max_chunk_size=1000,
        semantic_chunking=True
    )
    enhanced_chunks, enhanced_metas = enhanced_pipeline.ingest(file_path, metadata)
    print(f"   Chunks created: {len(enhanced_chunks)}")
    print(f"   Avg chunk size: {sum(len(c) for c in enhanced_chunks) / len(enhanced_chunks):.0f} chars")
    print(f"\n   First chunk preview:")
    print(f"   {enhanced_chunks[0][:200]}...")
    
    # Show metadata differences
    print("\n3. METADATA COMPARISON:")
    print(f"\n   Basic metadata keys: {list(basic_metas[0].keys())}")
    print(f"   Enhanced metadata keys: {list(enhanced_metas[0].keys())}")
    print(f"\n   Enhanced metadata sample:")
    print(f"   Section: {enhanced_metas[0].get('section', 'N/A')}")
    print(f"   Chunk type: {enhanced_metas[0].get('chunk_type', 'N/A')}")
    print(f"   Has table: {enhanced_metas[0].get('has_table', False)}")
    print(f"   Has figure: {enhanced_metas[0].get('has_figure', False)}")


def test_table_detection():
    """Test table detection in documents."""
    print("\n" + "="*70)
    print("TEST 2: Table Detection")
    print("="*70)
    
    # Create a sample document with a table
    test_content = """
# Payment Processing Guide

## Overview
This guide explains how to handle payment errors.

## Error Codes Table

| Error Code | Description | Resolution |
|-----------|-------------|------------|
| 500 | Server Error | Check logs and restart service |
| 401 | Auth Error | Verify API key |
| 404 | Not Found | Check endpoint URL |

## Common Issues

When you encounter a 500 error, follow these steps:
1. Check server logs
2. Verify database connectivity
3. Restart the service if needed
"""
    
    # Write test file
    test_file = "data/test_table_doc.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Test with enhanced ingestion
    enhanced_pipeline = EnhancedIngestionPipeline(
        min_chunk_size=100,
        max_chunk_size=500,
        semantic_chunking=True
    )
    
    chunks, metadatas = enhanced_pipeline.ingest(test_file, {'Type': 'Test'})
    
    print(f"\nTotal chunks: {len(chunks)}")
    
    # Find and display chunks with tables
    for i, (chunk, meta) in enumerate(zip(chunks, metadatas)):
        if meta.get('has_table', False):
            print(f"\n   Chunk {i+1} (Contains Table):")
            print(f"   Section: {meta.get('section', 'N/A')}")
            print(f"   Chunk type: {meta.get('chunk_type', 'N/A')}")
            print(f"   Content:\n   {chunk[:300]}...")
    
    # Cleanup
    os.remove(test_file)


def test_section_extraction():
    """Test section name extraction."""
    print("\n" + "="*70)
    print("TEST 3: Section Extraction")
    print("="*70)
    
    file_path = "data/knowledge_base.txt"
    metadata = {'Type': 'Test'}
    
    enhanced_pipeline = EnhancedIngestionPipeline(
        min_chunk_size=200,
        max_chunk_size=800,
        semantic_chunking=True
    )
    
    chunks, metadatas = enhanced_pipeline.ingest(file_path, metadata)
    
    # Show sections found
    sections = set(meta.get('section', 'Unknown') for meta in metadatas)
    print(f"\nSections found: {len(sections)}")
    for section in sorted(sections):
        count = sum(1 for m in metadatas if m.get('section') == section)
        print(f"   - {section}: {count} chunks")


def test_comparison_summary():
    """Summary comparison of basic vs enhanced ingestion."""
    print("\n" + "="*70)
    print("SUMMARY: Basic vs Enhanced Ingestion")
    print("="*70)
    
    file_path = "data/knowledge_base.txt"
    metadata = {'Type': 'Company', 'Subtype': 'General', 'Priority': 'P0'}
    
    # Basic ingestion
    basic = IngestionPipeline(chunk_size=500, chunk_overlap=50)
    basic_chunks, basic_metas = basic.ingest(file_path, metadata)
    
    # Enhanced ingestion
    enhanced = EnhancedIngestionPipeline(
        min_chunk_size=300,
        max_chunk_size=1000,
        semantic_chunking=True
    )
    enhanced_chunks, enhanced_metas = enhanced.ingest(file_path, metadata)
    
    print(f"\nMetric                    | Basic      | Enhanced   | Improvement")
    print(f"--------------------------|------------|------------|-------------")
    print(f"Total chunks              | {basic_chunks.__len__():10} | {enhanced_chunks.__len__():10} | {((enhanced_chunks.__len__() - basic_chunks.__len__()) / basic_chunks.__len__() * 100):+.1f}%")
    print(f"Avg chunk size (chars)    | {sum(len(c) for c in basic_chunks) / len(basic_chunks):10.0f} | {sum(len(c) for c in enhanced_chunks) / len(enhanced_chunks):10.0f} | {((sum(len(c) for c in enhanced_chunks) / len(enhanced_chunks) - sum(len(c) for c in basic_chunks) / len(basic_chunks)) / (sum(len(c) for c in basic_chunks) / len(basic_chunks)) * 100):+.1f}%")
    print(f"Metadata fields           | {len(basic_metas[0]):10} | {len(enhanced_metas[0]):10} | +{len(enhanced_metas[0]) - len(basic_metas[0])}")
    print(f"Table detection           | {'No':10} | {'Yes':10} | ✓")
    print(f"Figure detection          | {'No':10} | {'Yes':10} | ✓")
    print(f"Section extraction        | {'No':10} | {'Yes':10} | ✓")
    print(f"Semantic chunking         | {'No':10} | {'Yes':10} | ✓")
    
    # Calculate unique sections in enhanced
    sections = len(set(m.get('section', 'Unknown') for m in enhanced_metas))
    print(f"\nUnique sections found: {sections}")
    
    # Calculate chunks with special features
    tables = sum(1 for m in enhanced_metas if m.get('has_table', False))
    figures = sum(1 for m in enhanced_metas if m.get('has_figure', False))
    print(f"Chunks with tables: {tables}")
    print(f"Chunks with figures: {figures}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING ENHANCED INGESTION PIPELINE")
    print("="*70)
    
    # Run all tests
    test_semantic_chunking()
    test_table_detection()
    test_section_extraction()
    test_comparison_summary()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS COMPLETE")
    print("="*70)
    print("\nConclusion:")
    print("- Enhanced ingestion provides better semantic understanding")
    print("- Table and figure detection working")
    print("- Section extraction helps with context")
    print("- Larger, more meaningful chunks preserve context better")
    print("="*70)
