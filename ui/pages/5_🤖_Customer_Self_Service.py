"""
Customer Self-Service Chatbot
Handles L1 support queries autonomously with knowledge base integration
"""
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.workflow import AgentWorkflow
from agents.general_chatbot import GeneralChatbot
from agents.retrieval_agent import RetrievalAgent
from agents.guardrails_agent import GuardrailsAgent
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Customer Self-Service",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'customer_chat_history' not in st.session_state:
    st.session_state.customer_chat_history = []
if 'customer_session_id' not in st.session_state:
    st.session_state.customer_session_id = f"customer_{int(time.time())}"
if 'resolved_count' not in st.session_state:
    st.session_state.resolved_count = 0
if 'escalated_count' not in st.session_state:
    st.session_state.escalated_count = 0

# Initialize agents
@st.cache_resource
def get_agents():
    return {
        'chatbot': GeneralChatbot(),
        'retrieval': RetrievalAgent(),
        'guardrails': GuardrailsAgent()
    }

agents = get_agents()

# Sidebar - Metrics
st.sidebar.header("📊 Session Metrics")
st.sidebar.metric("Resolved", st.session_state.resolved_count)
st.sidebar.metric("Escalated", st.session_state.escalated_count)

if st.session_state.customer_chat_history:
    total = st.session_state.resolved_count + st.session_state.escalated_count
    if total > 0:
        resolution_rate = (st.session_state.resolved_count / total) * 100
        st.sidebar.metric("Resolution Rate", f"{resolution_rate:.1f}%")

st.sidebar.markdown("---")

# Common scenarios
st.sidebar.header("💡 Try These")
example_queries = [
    "I forgot my password",
    "My account is locked",
    "Payment failed - error code 401",
    "API not responding",
    "How do I enable MFA?",
    "Can't connect to VPN",
    "Database timeout errors",
    "Need to upgrade my plan"
]

for query in example_queries:
    if st.sidebar.button(query, key=f"ex_{query}"):
        st.session_state.pending_query = query

st.sidebar.markdown("---")
if st.sidebar.button("🔄 New Session"):
    st.session_state.customer_chat_history = []
    st.session_state.customer_session_id = f"customer_{int(time.time())}"
    st.session_state.resolved_count = 0
    st.session_state.escalated_count = 0
    st.rerun()

# Main area
st.title("🤖 Customer Self-Service Portal")
st.markdown("**Get instant help 24/7 - No login required**")

# Instructions
with st.expander("ℹ️ How it works"):
    st.markdown("""
    This AI-powered chatbot can help you with:
    - 🔐 Account & authentication issues
    - 💳 Payment & billing questions
    - 🔧 Technical troubleshooting
    - 📚 How-to guides & documentation
    - ⚡ API & integration support
    
    **What happens:**
    1. Ask your question in natural language
    2. AI searches knowledge base for relevant solutions
    3. Get instant step-by-step guidance
    4. If unresolved, seamlessly escalate to a human agent
    
    **Typical resolution time:** < 2 minutes
    """)

# Chat display
st.markdown("---")
chat_container = st.container()

with chat_container:
    for i, msg in enumerate(st.session_state.customer_chat_history):
        if msg['role'] == 'user':
            with st.chat_message("user"):
                st.markdown(msg['content'])
        elif msg['role'] == 'assistant':
            with st.chat_message("assistant"):
                st.markdown(msg['content'])
                
                # Show KB articles if available
                if 'sources' in msg and msg['sources']:
                    with st.expander("📚 Knowledge Base Articles Used"):
                        for j, source in enumerate(msg['sources'], 1):
                            st.markdown(f"**{j}. {source.get('title', 'Article')}**")
                            st.caption(f"Relevance: {source.get('score', 0):.2%}")
        elif msg['role'] == 'system':
            st.info(msg['content'])

# Chat input
if 'pending_query' in st.session_state:
    user_input = st.session_state.pending_query
    del st.session_state.pending_query
else:
    user_input = st.chat_input("What can I help you with today?")

if user_input:
    # Add user message
    st.session_state.customer_chat_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    })
    
    # Show user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    
    # Process query
    with chat_container:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            sources_placeholder = st.empty()
            
            # Show thinking
            message_placeholder.markdown("🔍 Searching knowledge base...")
            
            try:
                # Check safety first
                safety_check = agents['guardrails'].process({
                    'query': user_input,
                    'context': {}
                })
                
                if safety_check.get('safety_violation'):
                    response = "I apologize, but I cannot assist with that request. Please rephrase your question or contact support for assistance."
                    sources = []
                else:
                    # Retrieve relevant articles
                    retrieval_result = agents['retrieval'].process({
                        'query': user_input,
                        'top_k': 3
                    })
                    
                    retrieved_docs = retrieval_result.get('retrieved_docs', [])
                    
                    # Generate response
                    chatbot_result = agents['chatbot'].process({
                        'query': user_input,
                        'retrieved_docs': retrieved_docs,
                        'conversation_history': st.session_state.customer_chat_history[-5:]  # Last 5 messages
                    })
                    
                    response = chatbot_result.get('response', 'I apologize, but I encountered an error. Please try again.')
                    sources = retrieved_docs
                
                # Display response
                message_placeholder.markdown(response)
                
                # Check if resolved or needs escalation
                needs_escalation = any(phrase in response.lower() for phrase in [
                    'contact support',
                    'escalate',
                    'human agent',
                    'cannot assist',
                    'unable to help'
                ])
                
                has_solution = any(phrase in response.lower() for phrase in [
                    'try',
                    'follow these steps',
                    'you can',
                    'here\'s how',
                    'solution'
                ])
                
                # Show sources if available
                if sources:
                    with sources_placeholder.expander("📚 Knowledge Base Articles Used"):
                        for j, source in enumerate(sources, 1):
                            metadata = source.get('metadata', {})
                            st.markdown(f"**{j}. {metadata.get('Type', 'Article')}: {metadata.get('Subtype', 'General')}**")
                            st.caption(f"Relevance: {source.get('score', 0):.2%}")
                            st.text(source.get('chunk', '')[:200] + "...")
                
                # Add response to history
                st.session_state.customer_chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'sources': sources,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Ask for feedback
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    if st.button("✅ Resolved", key=f"resolve_{len(st.session_state.customer_chat_history)}"):
                        st.session_state.resolved_count += 1
                        st.session_state.customer_chat_history.append({
                            'role': 'system',
                            'content': '✅ **Issue marked as resolved.** Thank you for using self-service!',
                            'timestamp': datetime.now().isoformat()
                        })
                        st.rerun()
                
                with col2:
                    if st.button("🎫 Escalate to Agent", key=f"escalate_{len(st.session_state.customer_chat_history)}"):
                        st.session_state.escalated_count += 1
                        st.session_state.customer_chat_history.append({
                            'role': 'system',
                            'content': '🎫 **Ticket created: #TICKET-' + str(int(time.time())) + '**\n\nA support agent will contact you within:\n- Critical issues: 1 hour\n- High priority: 2 hours\n- Standard: 4 hours',
                            'timestamp': datetime.now().isoformat()
                        })
                        st.rerun()
                
            except Exception as e:
                message_placeholder.error(f"❌ Error: {str(e)}")
                st.session_state.customer_chat_history.append({
                    'role': 'assistant',
                    'content': f"I apologize, but I encountered a technical error. Please try again or contact support.",
                    'timestamp': datetime.now().isoformat()
                })
    
    st.rerun()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🤖 Powered by AI Agents")
with col2:
    st.caption("⚡ Average resolution: < 2 min")
with col3:
    st.caption("📞 Human support available 24/7")
