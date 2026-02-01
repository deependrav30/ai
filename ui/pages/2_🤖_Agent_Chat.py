import streamlit as st
import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from database.chat_storage import ChatStorage
from agents.workflow import AgentWorkflow
from dotenv import load_dotenv

load_dotenv()

# Initialize chat storage and agent workflow
chat_storage = ChatStorage()

st.set_page_config(page_title="AI Co-Pilot Chat", layout="wide", page_icon="🤖")

# Custom CSS for chat interface with agent streaming
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
    .agent-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
        animation: pulse 1.5s infinite;
    }
    .agent-running {
        background-color: #4CAF50;
        color: white;
    }
    .agent-completed {
        background-color: #e0e0e0;
        color: #666;
    }
    .execution-step {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        font-size: 13px;
        margin: 5px 0;
        animation: slideIn 0.3s;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    .confidence-bar {
        height: 6px;
        border-radius: 3px;
        background: linear-gradient(90deg, #ff6b6b 0%, #feca57 50%, #48dbfb 100%);
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI Support Co-Pilot")
st.markdown("Powered by collaborative multi-agent system with live execution streaming")

# Initialize session state
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = None

if 'workflow' not in st.session_state:
    st.session_state.workflow = AgentWorkflow()

# Sidebar for session management
with st.sidebar:
    st.header("📋 Session Management")
    
    # Start new session
    if st.button("➕ New Session", use_container_width=True):
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        chat_storage.create_session(session_id)
        st.session_state.session_id = session_id
        st.session_state.chat_history = []
        st.session_state.chat_started = True
        st.success(f"New session created! ID: {session_id[:20]}...")
        st.rerun()
    
    st.divider()
    
    # Load existing sessions
    st.subheader("Previous Sessions")
    sessions = chat_storage.get_all_sessions()
    
    if sessions:
        for session in sessions[:10]:  # Show last 10 sessions
            col1, col2 = st.columns([3, 1])
            with col1:
                session_label = f"📅 {session['created_at'][:16]} ({session.get('message_count', 0)} msgs)"
                if st.button(
                    session_label, 
                    key=f"load_{session['session_id']}",
                    use_container_width=True
                ):
                    st.session_state.session_id = session['session_id']
                    # Load messages and convert to chat history format
                    messages = chat_storage.get_session_messages(session['session_id'])
                    chat_history = []
                    for i in range(0, len(messages), 2):
                        if i + 1 < len(messages):
                            chat_history.append({
                                'question': messages[i]['content'],
                                'answer': messages[i+1]['content'],
                                'timestamp': messages[i]['timestamp']
                            })
                    st.session_state.chat_history = chat_history
                    st.session_state.chat_started = True
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{session['session_id']}"):
                    chat_storage.delete_session(session['session_id'])
                    st.rerun()
    else:
        st.info("No previous sessions")
    
    st.divider()
    
    # Export training data
    st.subheader("🎓 Training Data")
    if st.button("📥 Export Training Data", use_container_width=True):
        filename = chat_storage.export_training_data()
        if filename:
            st.success(f"Exported to {filename}")
        else:
            st.warning("No training data to export")
    
    # System info
    st.divider()
    st.subheader("ℹ️ System Info")
    if st.session_state.session_id:
        st.caption(f"Session: {st.session_state.session_id[:8]}...")
        st.caption(f"Messages: {len(st.session_state.chat_history)}")


def display_agent_execution(state: dict, agent_stream_placeholder):
    """Display live agent execution with streaming visualization."""
    
    execution_model = state.get('execution_model', 'unknown')
    agent_order = state.get('agent_execution_order', [])
    execution_logs = state.get('execution_logs', [])
    
    # Show execution model
    model_emoji = {
        'general_chat': '💬',
        'serial': '➡️',
        'parallel': '⚡',
        'async': '🔄'
    }
    
    agent_stream_placeholder.markdown(f"""
    ### {model_emoji.get(execution_model, '🔧')} Execution Mode: **{execution_model.upper()}**
    """)
    
    # Show agent badges
    if agent_order:
        badges_html = "<div style='margin: 10px 0;'>"
        for agent in agent_order:
            badges_html += f'<span class="agent-badge agent-completed">✓ {agent.title()}</span>'
        badges_html += "</div>"
        agent_stream_placeholder.markdown(badges_html, unsafe_allow_html=True)
    
    # Show execution logs
    if execution_logs:
        with agent_stream_placeholder.expander("📊 Execution Timeline", expanded=False):
            for log in execution_logs:
                st.markdown(f"""
                **{log['agent']}** - {log['execution_time']:.3f}s  
                `{log['timestamp']}`
                """)


def display_classification_info(state: dict):
    """Display classification results from Intent Agent."""
    
    if state.get('intent'):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Intent", state.get('intent', 'N/A').upper())
        with col2:
            st.metric("Urgency", state.get('urgency', 'N/A').upper())
        with col3:
            st.metric("Category", state.get('category', 'N/A').upper())
        with col4:
            confidence = state.get('confidence', 0)
            st.metric("Confidence", f"{confidence:.0%}")
            # Visual confidence bar
            st.markdown(f"""
            <div class="confidence-bar" style="width: {confidence * 100}%"></div>
            """, unsafe_allow_html=True)


def display_insights(state: dict):
    """Display reasoning insights and recommendations."""
    
    if state.get('pattern_detected'):
        st.warning("🔁 **Pattern Detected**: This appears to be a recurring issue")
    
    if state.get('root_cause'):
        with st.expander("🔍 Root Cause Analysis"):
            st.write(state['root_cause'])
    
    if state.get('recommendations'):
        with st.expander("💡 Recommendations"):
            for i, rec in enumerate(state['recommendations'], 1):
                st.markdown(f"{i}. {rec}")
    
    if state.get('past_resolutions'):
        with st.expander("📚 Similar Past Resolutions"):
            for res in state['past_resolutions'][:3]:
                st.markdown(f"- **Issue**: {res['input'][:100]}...")
                st.markdown(f"  **Resolution**: {res['resolution'][:200]}...")
                st.markdown("")


def display_sources(state: dict):
    """Display knowledge base sources."""
    
    sources = state.get('sources', [])
    if sources:
        with st.expander(f"📖 Sources ({len(sources)})"):
            for i, source in enumerate(sources, 1):
                st.markdown(f"{i}. **{source['name']}** (relevance: {source['score']:.0%})")


async def process_chat_message(user_input: str):
    """Process user message through multi-agent system."""
    
    # Save user message
    chat_storage.save_message(st.session_state.session_id, 'user', user_input)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Log interaction
    chat_storage.log_interaction(
        st.session_state.session_id,
        None,
        'query_submitted',
        metadata={'query': user_input}
    )
    
    # Process with agent system
    with st.chat_message("assistant"):
        # Placeholders for streaming display
        agent_stream_placeholder = st.empty()
        classification_placeholder = st.empty()
        insights_placeholder = st.empty()
        sources_placeholder = st.empty()
        response_placeholder = st.empty()
        
        try:
            # Show initial status
            with agent_stream_placeholder:
                with st.status("🤖 Processing with AI agents...", expanded=True) as status:
                    st.write("🔄 Initializing agent workflow...")
                    
                    # Process through agent system
                    state = await st.session_state.workflow.process_ticket(user_input)
                    
                    st.write(f"✓ Completed in {state.get('total_execution_time', 0):.2f}s")
                    status.update(label="✅ Processing complete!", state="complete")
            
            # Display execution details
            display_agent_execution(state, agent_stream_placeholder)
            
            # Display classification if available
            with classification_placeholder:
                if state.get('execution_model') != 'general_chat':
                    display_classification_info(state)
            
            # Display insights
            with insights_placeholder:
                display_insights(state)
            
            # Display sources
            with sources_placeholder:
                display_sources(state)
            
            # Display final response
            response = state.get('response', 'No response generated')
            
            # Check if blocked by guardrails
            if state.get('blocked'):
                response_placeholder.error(f"🚫 **Safety Check Failed**\n\n{response}")
            elif state.get('needs_human_review'):
                response_placeholder.warning(f"⚠️ **Human Review Needed**\n\n{response}")
            else:
                response_placeholder.markdown(response)
            
            # Save assistant message
            chat_storage.save_message(st.session_state.session_id, 'assistant', response)
            
            # Update chat history
            st.session_state.chat_history.append({
                'question': user_input,
                'answer': response,
                'timestamp': datetime.now().isoformat(),
                'confidence': state.get('confidence', 0),
                'execution_model': state.get('execution_model', 'unknown')
            })
            
            # Log completion
            chat_storage.log_interaction(
                st.session_state.session_id,
                None,
                'response_generated',
                metadata={
                    'execution_model': state.get('execution_model'),
                    'confidence': state.get('confidence'),
                    'agents_used': state.get('agent_execution_order', [])
                }
            )
            
        except Exception as e:
            response_placeholder.error(f"❌ An error occurred: {str(e)}")
            print(f"Chat processing error: {str(e)}")


# Main chat interface
st.markdown("---")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg['question'])
    
    with st.chat_message("assistant"):
        st.markdown(msg['answer'])
        
        # Show metadata
        if msg.get('execution_model'):
            st.caption(f"Mode: {msg['execution_model']} | Confidence: {msg.get('confidence', 0):.0%}")

# Chat input
if not st.session_state.chat_started:
    st.info("👈 Start a new session or load an existing one from the sidebar to begin chatting!")
else:
    user_input = st.chat_input("Ask me anything about your documents or report an issue...")
    
    if user_input:
        # Run async processing
        asyncio.run(process_chat_message(user_input))
        st.rerun()

# Footer
st.markdown("---")
st.caption("🤖 Powered by 8-agent collaborative system | 💾 All conversations are saved for continuous learning")
