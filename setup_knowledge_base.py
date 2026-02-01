#!/usr/bin/env python3
"""
Script to upload and process knowledge base documents
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from rag.rag_workflow import index_document
import shutil

def setup_knowledge_base():
    """Process knowledge base document into vector store"""
    
    print("="*70)
    print("KNOWLEDGE BASE SETUP")
    print("="*70)
    
    # Source document
    kb_source = "data/knowledge_base.txt"
    
    if not os.path.exists(kb_source):
        print(f"\n❌ Knowledge base file not found: {kb_source}")
        return False
    
    # Setup upload directory structure
    upload_base = "data/uploaded"
    company_dir = os.path.join(upload_base, "Company")
    general_dir = os.path.join(company_dir, "General")
    priority_dir = os.path.join(general_dir, "P0")
    
    # Create directory structure
    os.makedirs(priority_dir, exist_ok=True)
    
    # Copy to upload location
    dest_path = os.path.join(priority_dir, "technical_support_kb.txt")
    shutil.copy(kb_source, dest_path)
    
    print(f"\n1. Copied knowledge base to: {dest_path}")
    print(f"2. Processing document into vector store...")
    
    # Process the document
    try:
        metadata = {
            'Type': 'Company',
            'Subtype': 'General',
            'Priority': 'P0',
            'Uploaded By': 'System',
            'Timestamp': '2026-02-01T00:00:00'
        }
        
        index_document(dest_path, metadata)
        
        print(f"\n✓ Document processed successfully!")
        print(f"   - File size: {os.path.getsize(dest_path)} bytes")
        
        # Verify in ChromaDB
        print(f"\n3. Verifying in vector store...")
        
        import chromadb
        client = chromadb.PersistentClient(path="db/chroma_db")
        
        # Get all collections
        collections = client.list_collections()
        print(f"   Collections found: {len(collections)}")
        
        for coll in collections:
            count = coll.count()
            print(f"   - {coll.name}: {count} documents")
        
        print("\n" + "="*70)
        print("✓ KNOWLEDGE BASE SETUP COMPLETE")
        print("="*70)
        print("\nNext steps:")
        print("1. Test retrieval with sample queries")
        print("2. Run agent workflow with technical questions")
        print("3. Verify relevant documents are retrieved")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_knowledge_base()
    sys.exit(0 if success else 1)
