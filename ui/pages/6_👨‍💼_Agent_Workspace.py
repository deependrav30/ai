"""
Agent Assistance Workspace
Real-time AI assistant for support agents handling tickets
"""
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.workflow import AgentWorkflow
from agents.intent_agent import IntentAgent
from agents.retrieval_agent import RetrievalAgent
from agents.duplicate_detector_agent import DuplicateDetectorAgent
from agents.sla_predictor_agent import SLAPredictorAgent
from agents.synthesis_agent import SynthesisAgent
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="Agent Workspace",
    page_icon="👨‍💼",
    layout="wide"
)

# Initialize agents
@st.cache_resource
def get_agents():
    return {
        'intent': IntentAgent(),
        'retrieval': RetrievalAgent(),
        'duplicate': DuplicateDetectorAgent(),
        'sla': SLAPredictorAgent(),
        'synthesis': SynthesisAgent()
    }

agents = get_agents()

# Sample ticket queue
SAMPLE_TICKETS = [
    {
        'id': 'TICK-1001',
        'subject': 'Cannot login - getting "Invalid credentials" error',
        'description': 'I\'ve been trying to login for the past 30 minutes but keep getting invalid credentials error. I\'m sure my password is correct. This is urgent as I need to access the dashboard for a client meeting in 1 hour.',
        'customer': 'john.doe@company.com',
        'created': datetime.now() - timedelta(minutes=25),
        'priority': None,
        'status': 'new'
    },
    {
        'id': 'TICK-1002',
        'subject': 'Payment failed with error code 401',
        'description': 'Customer tried to process payment but got error 401. Transaction ID: TXN-998877. Amount: $150. Need immediate resolution.',
        'customer': 'jane.smith@business.com',
        'created': datetime.now() - timedelta(hours=1, minutes=15),
        'priority': None,
        'status': 'new'
    },
    {
        'id': 'TICK-1003',
        'subject': 'API returning 500 errors on webhook endpoint',
        'description': 'Our webhook endpoint /api/v1/webhooks/payment has been returning 500 errors since 2 PM today. Affecting production transactions. Logs show "Database connection timeout".',
        'customer': 'dev.team@startup.io',
        'created': datetime.now() - timedelta(hours=2),
        'priority': None,
        'status': 'new'
    },
    {
        'id': 'TICK-1004',
        'subject': 'How do I enable MFA for my account?',
        'description': 'I want to add multi-factor authentication to my account for better security. Can you guide me through the setup process?',
        'customer': 'security.conscious@email.com',
        'created': datetime.now() - timedelta(minutes=10),
        'priority': None,
        'status': 'new'
    }
]

# Session state
if 'agent_tickets' not in st.session_state:
    st.session_state.agent_tickets = SAMPLE_TICKETS.copy()
if 'selected_ticket' not in st.session_state:
    st.session_state.selected_ticket = None
if 'ticket_analysis' not in st.session_state:
    st.session_state.ticket_analysis = {}
if 'handled_count' not in st.session_state:
    st.session_state.handled_count = 0

# Header
st.title("👨‍💼 Agent Assistance Workspace")
st.markdown("**AI-powered tools to help you work faster and smarter**")

# Metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    open_tickets = len([t for t in st.session_state.agent_tickets if t['status'] == 'new'])
    st.metric("Open Tickets", open_tickets)
with col2:
    st.metric("Handled Today", st.session_state.handled_count)
with col3:
    if st.session_state.handled_count > 0:
        avg_time = "8.5 min"  # Simulated
    else:
        avg_time = "-"
    st.metric("Avg Handle Time", avg_time)
with col4:
    sla_compliance = "96%"  # Simulated
    st.metric("SLA Compliance", sla_compliance)

st.markdown("---")

# Two column layout
col_queue, col_details = st.columns([1, 2])

# Ticket Queue
with col_queue:
    st.subheader("📥 Ticket Queue")
    
    # Filter
    filter_status = st.selectbox("Filter", ["All", "New", "In Progress", "Pending"])
    
    # Display tickets
    for ticket in st.session_state.agent_tickets:
        if filter_status != "All" and ticket['status'] != filter_status.lower().replace(" ", "_"):
            continue
        
        # Time since creation
        time_elapsed = datetime.now() - ticket['created']
        minutes = int(time_elapsed.total_seconds() / 60)
        
        # Priority badge
        if ticket.get('priority'):
            if ticket['priority'] == 'critical':
                priority_color = "🔴"
            elif ticket['priority'] == 'high':
                priority_color = "🟠"
            elif ticket['priority'] == 'medium':
                priority_color = "🟡"
            else:
                priority_color = "🟢"
        else:
            priority_color = "⚪"
        
        # Display ticket card
        with st.container():
            col_info, col_action = st.columns([4, 1])
            
            with col_info:
                st.markdown(f"**{priority_color} {ticket['id']}**")
                st.caption(ticket['subject'])
                st.caption(f"⏱️ {minutes} min ago • {ticket['customer']}")
            
            with col_action:
                if st.button("View", key=f"view_{ticket['id']}"):
                    st.session_state.selected_ticket = ticket
                    st.rerun()
            
            st.markdown("---")

# Ticket Details & AI Assistant
with col_details:
    if st.session_state.selected_ticket:
        ticket = st.session_state.selected_ticket
        
        # Ticket header
        st.subheader(f"🎫 {ticket['id']}")
        st.markdown(f"**{ticket['subject']}**")
        
        # Quick actions
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        with action_col1:
            if st.button("✅ Resolve"):
                ticket['status'] = 'resolved'
                st.session_state.handled_count += 1
                st.session_state.selected_ticket = None
                st.success("Ticket marked as resolved!")
                time.sleep(1)
                st.rerun()
        with action_col2:
            if st.button("⏸️ Pending"):
                ticket['status'] = 'pending'
                st.info("Ticket marked as pending")
                time.sleep(1)
                st.rerun()
        with action_col3:
            if st.button("⚡ Escalate"):
                ticket['priority'] = 'high'
                st.warning("Ticket escalated to L2")
                time.sleep(1)
                st.rerun()
        with action_col4:
            if st.button("🔄 Analyze", type="primary"):
                # Trigger AI analysis
                with st.spinner("🤖 AI analyzing ticket..."):
                    # Intent classification
                    intent_result = agents['intent'].process({'query': ticket['description']})
                    
                    # Retrieve similar tickets
                    retrieval_result = agents['retrieval'].process({
                        'query': ticket['description'],
                        'top_k': 3
                    })
                    
                    # Duplicate detection
                    duplicate_result = agents['duplicate'].process({
                        'ticket_id': ticket['id'],
                        'description': ticket['description']
                    })
                    
                    # SLA prediction
                    sla_result = agents['sla'].process({
                        'urgency': intent_result.get('urgency', 'medium'),
                        'intent': intent_result.get('intent', 'question'),
                        'description': ticket['description']
                    })
                    
                    # Generate response draft
                    synthesis_result = agents['synthesis'].process({
                        'query': ticket['description'],
                        'retrieved_docs': retrieval_result.get('retrieved_docs', []),
                        'intent': intent_result
                    })
                    
                    # Store analysis
                    st.session_state.ticket_analysis[ticket['id']] = {
                        'intent': intent_result,
                        'retrieval': retrieval_result,
                        'duplicate': duplicate_result,
                        'sla': sla_result,
                        'synthesis': synthesis_result,
                        'analyzed_at': datetime.now()
                    }
                    
                    # Update ticket priority
                    ticket['priority'] = intent_result.get('urgency', 'medium')
                    
                st.success("✅ Analysis complete!")
                st.rerun()
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Details", "🤖 AI Insights", "💬 Draft Response", "📚 Similar Tickets"])
        
        with tab1:
            st.markdown("**Description:**")
            st.info(ticket['description'])
            
            st.markdown("**Customer:**")
            st.text(ticket['customer'])
            
            st.markdown("**Created:**")
            time_elapsed = datetime.now() - ticket['created']
            st.text(f"{ticket['created'].strftime('%Y-%m-%d %H:%M')} ({int(time_elapsed.total_seconds() / 60)} minutes ago)")
            
            st.markdown("**Status:**")
            st.text(ticket['status'].upper())
        
        with tab2:
            if ticket['id'] in st.session_state.ticket_analysis:
                analysis = st.session_state.ticket_analysis[ticket['id']]
                
                # Intent & Classification
                st.markdown("### 🎯 Classification")
                intent_data = analysis['intent']
                
                col_int1, col_int2, col_int3 = st.columns(3)
                with col_int1:
                    st.metric("Intent", intent_data.get('intent', 'unknown').upper())
                with col_int2:
                    urgency = intent_data.get('urgency', 'medium')
                    st.metric("Urgency", urgency.upper())
                with col_int3:
                    confidence = intent_data.get('confidence', 0)
                    st.metric("Confidence", f"{confidence:.1%}")
                
                if intent_data.get('category'):
                    st.caption(f"📂 Category: {intent_data['category']}")
                
                # SLA Info
                st.markdown("### ⏰ SLA Tracking")
                sla_data = analysis['sla']
                
                col_sla1, col_sla2, col_sla3 = st.columns(3)
                with col_sla1:
                    response_time = sla_data.get('response_deadline_hours', 2)
                    st.metric("Response SLA", f"{response_time}h")
                with col_sla2:
                    resolution_time = sla_data.get('resolution_deadline_hours', 8)
                    st.metric("Resolution SLA", f"{resolution_time}h")
                with col_sla3:
                    risk = sla_data.get('risk_level', 'safe')
                    if risk == 'critical':
                        st.metric("Risk", "🔴 CRITICAL")
                    elif risk == 'danger':
                        st.metric("Risk", "🟠 DANGER")
                    elif risk == 'warning':
                        st.metric("Risk", "🟡 WARNING")
                    else:
                        st.metric("Risk", "🟢 SAFE")
                
                if sla_data.get('recommendation'):
                    st.info(f"💡 {sla_data['recommendation']}")
                
                # Duplicate Detection
                st.markdown("### 🔍 Duplicate Check")
                dup_data = analysis['duplicate']
                
                if dup_data.get('has_duplicates'):
                    st.warning(f"⚠️ Found {dup_data.get('duplicate_count', 0)} similar ticket(s)")
                    if dup_data.get('most_similar'):
                        similar = dup_data['most_similar']
                        st.markdown(f"**Most similar:** Ticket #{similar.get('id', 'unknown')}")
                        st.caption(f"Similarity: {similar.get('similarity', 0):.1%}")
                else:
                    st.success("✅ No duplicates found - this is a unique issue")
                
            else:
                st.info("👆 Click **Analyze** button to get AI insights")
        
        with tab3:
            if ticket['id'] in st.session_state.ticket_analysis:
                analysis = st.session_state.ticket_analysis[ticket['id']]
                synthesis_data = analysis['synthesis']
                
                st.markdown("### ✍️ AI-Generated Response Draft")
                st.info("💡 Review and edit before sending to customer")
                
                draft_response = synthesis_data.get('response', 'No draft available')
                
                # Editable text area
                edited_response = st.text_area(
                    "Response:",
                    value=draft_response,
                    height=300,
                    key=f"draft_{ticket['id']}"
                )
                
                col_send1, col_send2 = st.columns([1, 4])
                with col_send1:
                    if st.button("📤 Send Response", type="primary"):
                        st.success("✅ Response sent to customer!")
                        ticket['status'] = 'pending'
                        time.sleep(1)
                        st.rerun()
                with col_send2:
                    if st.button("📋 Copy to Clipboard"):
                        st.info("Copied to clipboard!")
            else:
                st.info("👆 Click **Analyze** button to generate response draft")
        
        with tab4:
            if ticket['id'] in st.session_state.ticket_analysis:
                analysis = st.session_state.ticket_analysis[ticket['id']]
                retrieval_data = analysis['retrieval']
                
                st.markdown("### 📚 Similar Tickets & Knowledge Base")
                
                retrieved_docs = retrieval_data.get('retrieved_docs', [])
                
                if retrieved_docs:
                    for i, doc in enumerate(retrieved_docs[:5], 1):
                        with st.expander(f"#{i} - Relevance: {doc.get('score', 0):.1%}"):
                            metadata = doc.get('metadata', {})
                            st.markdown(f"**Type:** {metadata.get('Type', 'Unknown')}")
                            st.markdown(f"**Category:** {metadata.get('Subtype', 'General')}")
                            st.markdown(f"**Priority:** {metadata.get('Priority', 'P2')}")
                            st.markdown("**Content:**")
                            st.text(doc.get('chunk', 'No content available')[:500])
                else:
                    st.warning("No similar tickets found in knowledge base")
            else:
                st.info("👆 Click **Analyze** button to find similar tickets")
    
    else:
        # No ticket selected
        st.info("👈 Select a ticket from the queue to view details and get AI assistance")
        
        # Show quick stats
        st.markdown("### 📊 Quick Stats")
        
        col_stat1, col_stat2 = st.columns(2)
        
        with col_stat1:
            st.markdown("**Today's Performance**")
            st.metric("Tickets Handled", st.session_state.handled_count)
            st.metric("Avg Resolution Time", "8.5 min" if st.session_state.handled_count > 0 else "-")
            st.metric("First Contact Resolution", "82%" if st.session_state.handled_count > 0 else "-")
        
        with col_stat2:
            st.markdown("**AI Assistance Impact**")
            st.metric("Time Saved", "~45 min" if st.session_state.handled_count > 0 else "-")
            st.metric("KB Articles Suggested", "12" if st.session_state.handled_count > 0 else "-")
            st.metric("Auto-Draft Acceptance", "78%" if st.session_state.handled_count > 0 else "-")

# Footer
st.markdown("---")
st.caption("💡 **Pro Tip:** Use the Analyze button to get instant AI insights, similar ticket suggestions, and response drafts")
