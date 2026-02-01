import streamlit as st
import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from agents.memory_agent import MemoryAgent
from database.chat_storage import ChatStorage
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Memory Management", layout="wide", page_icon="🧠")

# Initialize agents
if 'memory_agent' not in st.session_state:
    st.session_state.memory_agent = MemoryAgent()

chat_storage = ChatStorage()

# Custom CSS
st.markdown("""
<style>
    .memory-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .memory-type-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 10px;
    }
    .working-badge {
        background-color: #feca57;
        color: #000;
    }
    .episodic-badge {
        background-color: #48dbfb;
        color: #fff;
    }
    .semantic-badge {
        background-color: #9c27b0;
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Memory Management")
st.markdown("Manage the three types of memory: Working, Episodic, and Semantic")

# Create tabs for different memory types
tab1, tab2, tab3 = st.tabs([
    "⚡ Working Memory",
    "📚 Episodic Memory", 
    "🔍 Semantic Memory"
])

with tab1:
    st.header("⚡ Working Memory (Current Tasks)")
    st.markdown("""
    <span class="memory-type-badge working-badge">SHORT-TERM</span>
    Temporary context for active tasks. Cleared after completion.
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Display working memory
    working_memory = st.session_state.memory_agent.working_memory
    
    if working_memory:
        st.success(f"📊 {len(working_memory)} active tasks in working memory")
        
        for task_id, data in working_memory.items():
            with st.expander(f"🎯 {task_id}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Input:** {data.get('user_input', 'N/A')[:200]}")
                    st.write(f"**Intent:** {data.get('intent', 'N/A')}")
                    st.write(f"**Category:** {data.get('category', 'N/A')}")
                
                with col2:
                    st.write(f"**Time:** {data.get('timestamp', 'N/A')[:19]}")
                    
                    if st.button("🗑️ Clear", key=f"clear_{task_id}"):
                        st.session_state.memory_agent.clear_working_memory(task_id)
                        st.rerun()
        
        st.divider()
        
        if st.button("🗑️ Clear All Working Memory", type="secondary"):
            st.session_state.memory_agent.working_memory.clear()
            st.success("All working memory cleared!")
            st.rerun()
    else:
        st.info("No active tasks in working memory")

with tab2:
    st.header("📚 Episodic Memory (Past Tickets)")
    st.markdown("""
    <span class="memory-type-badge episodic-badge">LONG-TERM</span>
    Historical tickets, resolutions, and outcomes. Used for pattern detection.
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Query episodic memory
    conn = sqlite3.connect(st.session_state.memory_agent.episodic_db_path)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_intent = st.selectbox(
            "Filter by Intent",
            ["All", "incident", "service_request", "question", "problem", "change"]
        )
    
    with col2:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All", "technical", "application", "security", "data"]
        )
    
    with col3:
        filter_urgency = st.selectbox(
            "Filter by Urgency",
            ["All", "low", "medium", "high", "critical"]
        )
    
    # Build query
    query = "SELECT * FROM past_tickets WHERE 1=1"
    params = []
    
    if filter_intent != "All":
        query += " AND intent = ?"
        params.append(filter_intent)
    
    if filter_category != "All":
        query += " AND category = ?"
        params.append(filter_category)
    
    if filter_urgency != "All":
        query += " AND urgency = ?"
        params.append(filter_urgency)
    
    query += " ORDER BY timestamp DESC LIMIT 50"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    tickets = cursor.fetchall()
    
    st.success(f"📊 Found {len(tickets)} tickets")
    
    # Display tickets
    for ticket in tickets:
        ticket_id, user_input, intent, category, urgency, resolution, outcome, confidence, timestamp = ticket[:9]
        
        with st.expander(f"🎫 {ticket_id} - {intent} ({urgency})", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Issue:** {user_input[:300]}")
                st.write(f"**Resolution:** {resolution[:300] if resolution else 'N/A'}")
                
                # Metadata - convert confidence to float for formatting
                try:
                    conf_value = float(confidence) if confidence else 0.0
                    conf_display = f"{conf_value:.0%}"
                except (ValueError, TypeError):
                    conf_display = str(confidence)
                st.caption(f"Category: {category} | Outcome: {outcome} | Confidence: {conf_display}")
            
            with col2:
                st.write(f"**Timestamp:**")
                st.code(timestamp[:19] if timestamp else 'N/A')
                
                if st.button("🗑️ Delete", key=f"delete_{ticket_id}"):
                    cursor.execute("DELETE FROM past_tickets WHERE ticket_id = ?", (ticket_id,))
                    conn.commit()
                    st.success(f"Deleted {ticket_id}")
                    st.rerun()
    
    conn.close()
    
    st.divider()
    
    # Add new ticket manually
    with st.expander("➕ Add New Ticket to Memory", expanded=False):
        with st.form("add_ticket_form"):
            ticket_id = st.text_input("Ticket ID", f"TICKET-MANUAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            user_input = st.text_area("Issue Description")
            
            col1, col2 = st.columns(2)
            with col1:
                intent = st.selectbox("Intent", ["incident", "service_request", "question", "problem", "change"])
                category = st.selectbox("Category", ["technical", "application", "security", "data"])
            
            with col2:
                urgency = st.selectbox("Urgency", ["low", "medium", "high", "critical"])
                outcome = st.selectbox("Outcome", ["success", "pending", "escalated", "failed"])
            
            resolution = st.text_area("Resolution")
            confidence = st.slider("Confidence", 0.0, 1.0, 0.8, 0.05)
            
            submitted = st.form_submit_button("💾 Save to Episodic Memory")
            
            if submitted and user_input:
                conn = sqlite3.connect(st.session_state.memory_agent.episodic_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO past_tickets 
                    (ticket_id, user_input, intent, category, urgency, resolution, outcome, confidence, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticket_id, user_input, intent, category, urgency,
                    resolution, outcome, confidence, datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                
                st.success(f"✅ Ticket {ticket_id} saved to episodic memory!")
                st.rerun()

with tab3:
    st.header("🔍 Semantic Memory (Knowledge Base)")
    st.markdown("""
    <span class="memory-type-badge semantic-badge">EMBEDDINGS</span>
    Document embeddings in ChromaDB. Search and manage indexed documents.
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Search semantic memory
    search_query = st.text_input("🔍 Search Knowledge Base", placeholder="Enter keywords...")
    
    if search_query:
        st.info("Search functionality integrates with the Retrieval Agent")
        st.write("Use the main Document Management page to:")
        st.write("- Upload and index documents")
        st.write("- Search knowledge base")
        st.write("- View indexed documents")
    
    st.divider()
    
    # Stats from ChromaDB
    try:
        import chromadb
        client = chromadb.PersistentClient(path="db/chroma_db")
        
        # Try to get collection stats
        try:
            collection = client.get_collection(name="rag_collection")
            doc_count = collection.count()
            
            st.success(f"📊 {doc_count} document chunks indexed in semantic memory")
            
            # Option to clear
            if st.button("🗑️ Clear Semantic Memory", type="secondary"):
                client.delete_collection(name="rag_collection")
                st.warning("Semantic memory cleared! Please re-index documents.")
                st.rerun()
        
        except Exception as e:
            st.info("No documents indexed yet. Upload documents from the main page to populate semantic memory.")
    
    except Exception as e:
        st.error(f"Error accessing semantic memory: {str(e)}")
    
    st.divider()
    
    # Memory statistics
    st.subheader("📊 Memory Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Working Memory", len(st.session_state.memory_agent.working_memory), "tasks")
    
    with col2:
        # Count episodic tickets
        conn = sqlite3.connect(st.session_state.memory_agent.episodic_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM past_tickets")
        episodic_count = cursor.fetchone()[0]
        conn.close()
        
        st.metric("Episodic Memory", episodic_count, "tickets")
    
    with col3:
        try:
            import chromadb
            client = chromadb.PersistentClient(path="db/chroma_db")
            collection = client.get_collection(name="rag_collection")
            semantic_count = collection.count()
        except:
            semantic_count = 0
        
        st.metric("Semantic Memory", semantic_count, "chunks")

# Footer
st.markdown("---")
st.caption("🧠 Memory system enables learning from past tickets and knowledge base | All three memory types work together")
