import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from rag.rag_workflow import retrieval, generate_response
from database.chat_storage import ChatStorage
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize chat storage
chat_storage = ChatStorage()

st.set_page_config(page_title="RAG Chat Assistant", layout="wide", page_icon="💬")

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 5px solid #2196F3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

st.title("💬 RAG Chat Assistant")
st.markdown("Have a conversation with your documents! Context is maintained throughout the session.")

# Initialize session state
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = None


def reformulate_query(user_query: str, chat_history: list) -> str:
    """
    Reformulate user query based on conversation history to make it standalone.
    
    Args:
        user_query: Current user question
        chat_history: List of previous Q&A pairs
    
    Returns:
        Reformulated standalone query
    """
    if not chat_history:
        return user_query
    
    # Build context from recent history (last 3 exchanges)
    recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
    context_text = "\n".join([
        f"User: {item['question']}\nAssistant: {item['answer']}"
        for item in recent_history
    ])
    
    prompt = f"""Given the conversation history below, reformulate the user's latest question to be a standalone question that includes necessary context.

Conversation History:
{context_text}

Latest User Question: {user_query}

Reformulated Standalone Question:"""
    
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that reformulates questions to include necessary context from conversation history. Keep the reformulated question concise and clear."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        reformulated = response.choices[0].message.content.strip()
        return reformulated
    except Exception as e:
        st.warning(f"Query reformulation failed: {str(e)}. Using original query.")
        return user_query


def process_chat_message(user_input: str):
    """Process user message and generate response with RAG."""
    
    # Save user message to storage
    chat_storage.save_message(st.session_state.session_id, 'user', user_input)
    
    # Add user message to history
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Log user interaction
    chat_storage.log_interaction(
        st.session_state.session_id,
        None,
        'query_submitted',
        metadata={'query': user_input}
    )
    
    # Show processing status
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        
        # Step 1: Reformulate query
        status_placeholder.info("🔄 Understanding your question in context...")
        reformulated_query = reformulate_query(user_input, st.session_state.chat_history)
        
        if reformulated_query != user_input:
            st.caption(f"🔍 Searching for: *{reformulated_query}*")
        
        # Step 2: Retrieve chunks
        status_placeholder.info("📚 Searching through documents...")
        results = retrieval.retrieve(reformulated_query)
        
        if not results:
            status_placeholder.empty()
            response = "I couldn't find any relevant information in the documents to answer your question. Could you please rephrase or provide more context?"
            sources = None
        else:
            # Step 3: Show fast-moving chunks
            chunks_placeholder = st.empty()
            for i, res in enumerate(results, 1):
                chunk_text = res.get('chunk', res.get('chunk_text', ''))[:150]
                chunks_placeholder.markdown(f"""
                <div style='
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    padding: 8px 15px;
                    border-radius: 8px;
                    color: white;
                    font-size: 13px;
                    margin: 5px 0;
                    animation: slideIn 0.2s;
                '>
                    📄 Source [{i}/{len(results)}] • {res['score']:.0%} match • {chunk_text}...
                </div>
                """, unsafe_allow_html=True)
                import time
                time.sleep(0.12)
            
            chunks_placeholder.empty()
            
            # Step 4: Generate response
            status_placeholder.info("🤖 Generating answer with GPT-4...")
            response = generate_response(reformulated_query, results)
            status_placeholder.empty()
            
            # Show final response
            st.markdown(f"""
            <div style='
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #9c27b0;
                color: #2d3748;
                line-height: 1.7;
            '>
                {response}
            </div>
            """, unsafe_allow_html=True)
            
            # Show sources in expander
            with st.expander(f"📚 View {len(results)} Sources"):
                for i, res in enumerate(results, 1):
                    st.markdown(f"**Source {i}** (Relevance: {res['score']:.1%})")
                    st.text(res.get('chunk', res.get('chunk_text', 'N/A'))[:500])
                    st.divider()
            
            sources = results
    
    # Save assistant response to storage
    chat_storage.save_message(
        st.session_state.session_id,
        'assistant',
        response,
        reformulated_query=reformulated_query if reformulated_query != user_input else None,
        sources=sources
    )
    
    # Log response generation
    chat_storage.log_interaction(
        st.session_state.session_id,
        None,
        'response_generated',
        metadata={
            'reformulated': reformulated_query != user_input,
            'sources_count': len(sources) if sources else 0
        }
    )
    
    # Save to session history
    st.session_state.chat_history.append({
        'question': user_input,
        'answer': response,
        'timestamp': datetime.now().isoformat(),
        'reformulated_query': reformulated_query if reformulated_query != user_input else None
    })


# Sidebar - Always visible for session management
with st.sidebar:
    st.header("💬 Chat Sessions")
    
    # New chat button
    if st.button("➕ New Chat Session", use_container_width=True, type="primary"):
        st.session_state.chat_started = True
        st.session_state.chat_history = []
        new_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.session_id = new_session_id
        chat_storage.create_session(new_session_id)
        st.success("New session created!")
        st.rerun()
    
    st.divider()
    
    # Load previous sessions
    st.subheader("📚 Previous Sessions")
    sessions = chat_storage.get_all_sessions(limit=20)
    
    if sessions:
        for session in sessions:
            session_date = datetime.fromisoformat(session['updated_at']).strftime("%b %d, %H:%M")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                    f"💬 {session['title'][:25]}...\n📅 {session_date} • {session['message_count']} msgs",
                    key=f"load_{session['session_id']}",
                    use_container_width=True
                ):
                    # Load session
                    st.session_state.session_id = session['session_id']
                    st.session_state.chat_started = True
                    
                    # Load messages
                    messages = chat_storage.get_session_messages(session['session_id'])
                    st.session_state.chat_history = []
                    for msg in messages:
                        if msg['role'] == 'user':
                            current_q = msg['content']
                        elif msg['role'] == 'assistant':
                            st.session_state.chat_history.append({
                                'question': current_q,
                                'answer': msg['content'],
                                'timestamp': msg['timestamp'],
                                'reformulated_query': msg.get('reformulated_query')
                            })
                    
                    st.success(f"Loaded: {session['title']}")
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{session['session_id']}"):
                    chat_storage.delete_session(session['session_id'])
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("No previous sessions yet.")
    
    st.divider()
    
    # Training data export
    st.subheader("🎓 Training Data")
    st.caption("Export user interactions for system improvement")
    
    if st.button("📥 Export Training Data", use_container_width=True):
        output_file = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if chat_storage.export_training_data(output_file):
            st.success(f"Exported to {output_file}")
            
            # Show stats
            interactions = chat_storage.get_training_data(limit=1000)
            st.metric("Total Interactions", len(interactions))
        else:
            st.error("Export failed")
    
    # Current session info
    if st.session_state.chat_started:
        st.divider()
        st.subheader("📊 Current Session")
        st.metric("Session ID", st.session_state.session_id[:12])
        st.metric("Messages", len(st.session_state.chat_history) * 2)
        
        if st.button("⏹️ End Session", use_container_width=True):
            st.session_state.chat_started = False
            st.session_state.chat_history = []
            st.session_state.session_id = None
            st.rerun()


# Main UI
if not st.session_state.chat_started:
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h2>Welcome to RAG Chat Assistant</h2>
        <p style='color: #666; font-size: 18px;'>
            Start a conversation and ask questions about your uploaded documents.<br/>
            I'll maintain context throughout our discussion.<br/><br/>
            👈 Use the sidebar to start a new session or load previous conversations.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Chat interface
    st.caption(f"Session: {st.session_state.session_id}")
    
    # Display chat history
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(msg['question'])
            
            with st.chat_message("assistant"):
                st.markdown(f"""
                <div style='
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 10px;
                    border-left: 4px solid #9c27b0;
                    color: #2d3748;
                    line-height: 1.7;
                '>
                    {msg['answer']}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your question here...")
    
    if user_input:
        process_chat_message(user_input)
        st.rerun()
