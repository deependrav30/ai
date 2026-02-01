import streamlit as st
import os
from datetime import datetime



import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rag.rag_workflow import index_document, retrieval

st.set_page_config(page_title="RAG System - Home", layout="wide", page_icon="📚")

st.title("📚 RAG System - Document Management")
st.markdown("Upload and index documents, then search with semantic queries.")

# Navigation hint
st.info("💡 **Tip:** Use the sidebar to navigate to the **💬 Chat** page for conversational interactions with your documents!")

st.markdown("---")

# Document Upload Section
st.header("1. Upload Document")
doc_type = st.selectbox("Type", ["Company", "Process", "Incident"])
doc_subtype = st.text_input("Subtype (e.g. Payments, KYC, Loans, UI)")
priority = st.selectbox("Priority", ["P0", "P1", "P2", "P3"])
uploader = st.text_input("Uploaded By", value="Admin")
file = st.file_uploader("Choose a file (PDF, DOCX, PPTX, TXT, Image)", type=["pdf", "docx", "pptx", "txt", "png", "jpg", "jpeg"])

if st.button("Upload") and file:
    try:
        timestamp = datetime.now().isoformat()
        save_dir = f"../data/uploaded/{doc_type}/{doc_subtype}/{priority}/"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file.name)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
        st.success(f"Uploaded to {save_path}")
        st.session_state['last_upload'] = {
            'file_path': save_path,
            'metadata': {
                'Type': doc_type,
                'Subtype': doc_subtype,
                'Priority': priority,
                'Uploaded By': uploader,
                'Timestamp': timestamp
            }
        }
        # Try to ingest and check for extracted text chunks before indexing
        try:
            from rag.ingestion.ingestion_pipeline import IngestionPipeline
            ingestion = IngestionPipeline(chunk_size=500, chunk_overlap=50)
            chunk_texts, chunk_metadatas = ingestion.ingest(save_path, st.session_state['last_upload']['metadata'])
            if not chunk_texts:
                st.warning("⚠️ No text could be extracted from this document. Please try a different file.")
            else:
                # Backend integration: Index document
                index_document(save_path, st.session_state['last_upload']['metadata'])
                st.info("✅ Document indexed successfully in RAG pipeline.")
        except ValueError as ve:
            st.error(f"⚠️ {str(ve)}")
        except Exception as e:
            print(f"Indexing error: {str(e)}")
            st.error("❌ Failed to process document. Please ensure the file is valid and try again.")
    except Exception as e:
        print(f"Upload error: {str(e)}")
        st.error("❌ Upload failed. Please try again or contact support if the issue persists.")

# Query Section
st.header("2. Semantic Search Query")
query = st.text_input("Enter your search query")

if st.button("Search") and query:
    try:
        import time
        
        # Phase 1: Searching animation
        search_status = st.empty()
        search_status.info("🔍 Searching through document knowledge base...")
        time.sleep(0.5)
        
        results = retrieval.retrieve(query)
    except Exception as e:
        print(f"Search error: {str(e)}")
        st.error("❌ Search failed. Please try again or contact support if the issue persists.")
        results = []
    
    if results:
        # Phase 2: Show chunks being analyzed with fast animation (then disappear)
        search_status.success(f"✅ Found {len(results)} relevant chunks!")
        
        # Create temporary container for fast-moving chunks
        chunks_container = st.empty()
        
        # Show each chunk briefly
        for i, res in enumerate(results, 1):
            chunk_text = res.get('chunk', res.get('chunk_text', '[No text available]'))
            
            chunks_container.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2px;
                border-radius: 10px;
                margin: 10px 0;
                animation: slideIn 0.2s ease-out;
            '>
                <div style='background-color: white; padding: 15px; border-radius: 8px;'>
                    <div style='color: #667eea; font-weight: bold; margin-bottom: 8px;'>
                        📄 Analyzing Source [{i}/{len(results)}] • Relevance: {res['score']:.1%}
                    </div>
                    <div style='color: #2d3748; line-height: 1.6; font-size: 14px; opacity: 0.8;'>
                        {chunk_text[:200]}{'...' if len(chunk_text) > 200 else ''}
                    </div>
                </div>
            </div>
            <style>
            @keyframes slideIn {{
                from {{ opacity: 0; transform: translateX(-20px); }}
                to {{ opacity: 1; transform: translateX(0); }}
            }}
            </style>
            """, unsafe_allow_html=True)
            time.sleep(0.15)  # Fast display time
        
        # Clear the chunks container after showing all
        time.sleep(0.3)
        chunks_container.empty()
        search_status.empty()
        
        st.markdown("---")
        
        # Phase 3: Generate final response
        try:
            from rag.rag_workflow import generate_response
            response_placeholder = st.empty()
            response_placeholder.info("🤖 Synthesizing answer from sources using GPT-4...")
            
            final_response = generate_response(query, results)
            response_placeholder.empty()
        except Exception as e:
            response_placeholder.empty()
            print(f"Response generation error: {str(e)}")
            final_response = "❌ Unable to generate response. Please try again or contact support if the issue persists."
        
        # Phase 4: Show final response with sources
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 3px;
            border-radius: 15px;
            margin: 20px 0;
        '>
            <div style='background-color: white; padding: 25px; border-radius: 12px;'>
                <h2 style='color: #f5576c; margin: 0 0 15px 0;'>✨ AI-Generated Answer</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='
            background-color: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
            color: #2d3748;
            line-height: 1.8;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        '>
            {final_response}
        </div>
        """, unsafe_allow_html=True)
        
        # Show sources used
        st.markdown("---")
        st.markdown("""
        <div style='margin: 20px 0;'>
            <h3 style='color: #4a5568; font-size: 18px;'>📚 Sources Used in Answer</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for i, res in enumerate(results, 1):
            with st.expander(f"📄 Source {i} (Relevance: {res['score']:.1%})"):
                chunk_text = res.get('chunk', res.get('chunk_text', '[No text available]'))
                st.markdown(f"""
                <div style='
                    background-color: #edf2f7;
                    padding: 15px;
                    border-radius: 8px;
                    color: #2d3748;
                    line-height: 1.6;
                '>
                    {chunk_text}
                </div>
                """, unsafe_allow_html=True)
                
                # Metadata
                st.markdown("**Metadata:**")
                metadata_display = {k: v for k, v in res.items() if k not in ['chunk', 'chunk_text', 'score']}
                st.json(metadata_display)
                
                # Document preview
                if 'file_path' in res:
                    ext = os.path.splitext(res['file_path'])[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg']:
                        st.image(res['file_path'], caption=res['file_path'], width=300)
                    elif ext == '.pdf':
                        st.markdown(f"📎 [View PDF Document]({res['file_path']})")
    else:
        st.warning("⚠️ No relevant results found. Try rephrasing your query.")
