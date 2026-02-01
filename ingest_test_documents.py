#!/usr/bin/env python3
"""
Script to ingest all test documents into the knowledge base
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from rag.rag_workflow import index_document
import glob
from datetime import datetime

def ingest_test_documents():
    """Process all test documents into vector store"""
    
    print("="*70)
    print("TEST DOCUMENTS INGESTION")
    print("="*70)
    
    # Find all test documents
    test_docs_dir = "data/test_documents/text"
    
    if not os.path.exists(test_docs_dir):
        print(f"\n❌ Test documents directory not found: {test_docs_dir}")
        return False
    
    # Get all txt and md files
    txt_files = glob.glob(os.path.join(test_docs_dir, "*.txt"))
    md_files = glob.glob(os.path.join(test_docs_dir, "*.md"))
    all_files = txt_files + md_files
    
    if not all_files:
        print(f"\n❌ No test documents found in: {test_docs_dir}")
        return False
    
    print(f"\n📄 Found {len(all_files)} documents to ingest")
    print(f"   - {len(txt_files)} TXT files")
    print(f"   - {len(md_files)} MD files")
    print()
    
    # Categorize documents
    categories = {
        'authentication': [],
        'payment': [],
        'api': [],
        'database': [],
        'network': []
    }
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        for category in categories.keys():
            if category in filename.lower():
                categories[category].append(file_path)
                break
    
    # Display categorization
    print("Document Distribution by Category:")
    for category, files in categories.items():
        print(f"  {category.upper()}: {len(files)} documents")
    print()
    
    # Ingest documents
    success_count = 0
    failed_count = 0
    
    for category, files in categories.items():
        if not files:
            continue
            
        print(f"\n{'='*70}")
        print(f"Processing {category.upper()} documents ({len(files)} files)")
        print('='*70)
        
        for i, file_path in enumerate(files, 1):
            filename = os.path.basename(file_path)
            print(f"\n[{i}/{len(files)}] Processing: {filename}")
            
            try:
                # Determine document type and priority
                if 'incident' in filename.lower():
                    doc_type = 'Incident Report'
                    priority = 'P1'
                elif filename.endswith('.md'):
                    doc_type = 'Documentation'
                    priority = 'P0'
                else:
                    doc_type = 'Troubleshooting Guide'
                    priority = 'P0'
                
                metadata = {
                    'Type': doc_type,
                    'Subtype': category.capitalize(),
                    'Priority': priority,
                    'Uploaded By': 'Test Data Generator',
                    'Timestamp': datetime.now().isoformat(),
                    'Category': category,
                    'Source': 'test_data'
                }
                
                # Index the document
                index_document(file_path, metadata)
                print(f"   ✓ Successfully indexed as {doc_type} (Priority: {priority})")
                success_count += 1
                
            except Exception as e:
                print(f"   ✗ Failed to index: {str(e)}")
                failed_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("INGESTION SUMMARY")
    print("="*70)
    print(f"Total documents processed: {len(all_files)}")
    print(f"✓ Successfully indexed: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"Success rate: {(success_count/len(all_files)*100):.1f}%")
    
    if success_count > 0:
        print("\n✅ Test documents ingestion complete!")
        print("\nNext steps:")
        print("  1. Test retrieval with category-specific queries")
        print("  2. Validate semantic chunking quality")
        print("  3. Run performance benchmarks")
        return True
    else:
        print("\n❌ Ingestion failed - no documents were indexed successfully")
        return False

if __name__ == "__main__":
    try:
        success = ingest_test_documents()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
