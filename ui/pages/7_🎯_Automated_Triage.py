"""
Automated Ticket Triage
Intelligent intake workflow with auto-classification and routing
"""
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.intent_agent import IntentAgent
from agents.duplicate_detector_agent import DuplicateDetectorAgent
from agents.sla_predictor_agent import SLAPredictorAgent
from datetime import datetime
import time
import random

# Page config
st.set_page_config(
    page_title="Automated Triage",
    page_icon="🎯",
    layout="wide"
)

# Initialize agents
@st.cache_resource
def get_agents():
    return {
        'intent': IntentAgent(),
        'duplicate': DuplicateDetectorAgent(),
        'sla': SLAPredictorAgent()
    }

agents = get_agents()

# Session state
if 'triage_metrics' not in st.session_state:
    st.session_state.triage_metrics = {
        'total_tickets': 0,
        'auto_routed': 0,
        'duplicates_caught': 0,
        'avg_triage_time': 0,
        'routing_by_team': {},
        'routing_history': []
    }

# Routing configuration
ROUTING_RULES = {
    'authentication': {
        'team': 'Identity & Access Team',
        'queue': 'auth-queue',
        'icon': '🔐'
    },
    'payment': {
        'team': 'Billing & Payments Team',
        'queue': 'payment-queue',
        'icon': '💳'
    },
    'api': {
        'team': 'Developer Support Team',
        'queue': 'api-queue',
        'icon': '🔧'
    },
    'database': {
        'team': 'Database Operations Team',
        'queue': 'db-queue',
        'icon': '🗄️'
    },
    'network': {
        'team': 'Network & Infrastructure Team',
        'queue': 'network-queue',
        'icon': '🌐'
    },
    'general': {
        'team': 'General Support Team',
        'queue': 'general-queue',
        'icon': '📋'
    }
}

# Header
st.title("🎯 Automated Ticket Triage")
st.markdown("**AI-powered intelligent routing - Zero manual triage required**")

# Metrics Dashboard
st.markdown("### 📊 Triage Performance")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Tickets Processed",
        st.session_state.triage_metrics['total_tickets']
    )

with col2:
    if st.session_state.triage_metrics['total_tickets'] > 0:
        auto_rate = (st.session_state.triage_metrics['auto_routed'] / 
                    st.session_state.triage_metrics['total_tickets']) * 100
        st.metric("Auto-Routed", f"{auto_rate:.0f}%")
    else:
        st.metric("Auto-Routed", "-")

with col3:
    st.metric(
        "Duplicates Detected",
        st.session_state.triage_metrics['duplicates_caught']
    )

with col4:
    if st.session_state.triage_metrics['total_tickets'] > 0:
        avg_time = st.session_state.triage_metrics['avg_triage_time']
        st.metric("Avg Triage Time", f"{avg_time:.1f}s")
    else:
        st.metric("Avg Triage Time", "-")

st.markdown("---")

# Two column layout
col_intake, col_routing = st.columns([2, 1])

# Ticket Intake Form
with col_intake:
    st.subheader("📝 New Ticket Submission")
    
    with st.form("ticket_intake_form"):
        # Customer info
        st.markdown("**Customer Information**")
        customer_email = st.text_input("Email", placeholder="customer@example.com")
        
        st.markdown("**Issue Details**")
        subject = st.text_input("Subject", placeholder="Brief description of the issue")
        
        description = st.text_area(
            "Description",
            placeholder="Detailed description of the problem, error messages, steps to reproduce, etc.",
            height=150
        )
        
        # Optional fields
        with st.expander("⚙️ Additional Information (Optional)"):
            customer_type = st.selectbox("Customer Type", ["Free", "Standard", "Premium", "Enterprise"])
            product_area = st.selectbox("Product Area", ["Web App", "Mobile App", "API", "Billing", "Other"])
            attachment = st.file_uploader("Attachments", accept_multiple_files=True)
        
        # Submit button
        col_submit, col_clear = st.columns([1, 1])
        
        with col_submit:
            submit_button = st.form_submit_button("🎯 Submit & Auto-Route", type="primary", use_container_width=True)
        
        with col_clear:
            clear_button = st.form_submit_button("🔄 Clear Form", use_container_width=True)
    
    # Process submission
    if submit_button and subject and description:
        with st.spinner("🤖 AI analyzing and routing ticket..."):
            start_time = time.time()
            
            # Classification
            intent_result = agents['intent'].process({'query': description})
            
            # Duplicate detection
            duplicate_result = agents['duplicate'].process({
                'ticket_id': f'TEMP-{int(time.time())}',
                'description': description
            })
            
            # SLA calculation
            sla_result = agents['sla'].process({
                'urgency': intent_result.get('urgency', 'medium'),
                'intent': intent_result.get('intent', 'question'),
                'description': description
            })
            
            # Determine category and routing
            category = intent_result.get('category', 'general')
            if category not in ROUTING_RULES:
                category = 'general'
            
            routing_info = ROUTING_RULES[category]
            
            triage_time = time.time() - start_time
            
            # Create ticket ID
            ticket_id = f"TICK-{int(time.time())}"
            
            # Update metrics
            st.session_state.triage_metrics['total_tickets'] += 1
            st.session_state.triage_metrics['auto_routed'] += 1
            
            if duplicate_result.get('has_duplicates'):
                st.session_state.triage_metrics['duplicates_caught'] += 1
            
            # Update average triage time
            total = st.session_state.triage_metrics['total_tickets']
            current_avg = st.session_state.triage_metrics['avg_triage_time']
            st.session_state.triage_metrics['avg_triage_time'] = (
                (current_avg * (total - 1) + triage_time) / total
            )
            
            # Update routing by team
            team = routing_info['team']
            if team not in st.session_state.triage_metrics['routing_by_team']:
                st.session_state.triage_metrics['routing_by_team'][team] = 0
            st.session_state.triage_metrics['routing_by_team'][team] += 1
            
            # Add to routing history
            routing_record = {
                'ticket_id': ticket_id,
                'subject': subject,
                'category': category,
                'urgency': intent_result.get('urgency'),
                'intent': intent_result.get('intent'),
                'team': team,
                'queue': routing_info['queue'],
                'sla_hours': sla_result.get('resolution_deadline_hours', 24),
                'is_duplicate': duplicate_result.get('has_duplicates', False),
                'confidence': intent_result.get('confidence', 0),
                'triage_time': triage_time,
                'timestamp': datetime.now()
            }
            
            st.session_state.triage_metrics['routing_history'].insert(0, routing_record)
            
            # Keep only last 50 records
            st.session_state.triage_metrics['routing_history'] = \
                st.session_state.triage_metrics['routing_history'][:50]
        
        # Display results
        st.success(f"✅ Ticket {ticket_id} created and automatically routed!")
        
        # Results card
        with st.container():
            st.markdown("### 🎯 Triage Results")
            
            # Classification
            col_class1, col_class2, col_class3, col_class4 = st.columns(4)
            
            with col_class1:
                st.metric("Intent", intent_result.get('intent', 'unknown').upper())
            
            with col_class2:
                urgency = intent_result.get('urgency', 'medium')
                urgency_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                st.metric("Urgency", f"{urgency_emoji.get(urgency, '⚪')} {urgency.upper()}")
            
            with col_class3:
                st.metric("Category", category.upper())
            
            with col_class4:
                confidence = intent_result.get('confidence', 0)
                st.metric("Confidence", f"{confidence:.0%}")
            
            # Routing
            st.markdown("### 📍 Routing Decision")
            
            col_route1, col_route2 = st.columns(2)
            
            with col_route1:
                st.info(f"{routing_info['icon']} **Assigned To:** {routing_info['team']}")
                st.caption(f"Queue: `{routing_info['queue']}`")
            
            with col_route2:
                sla_hours = sla_result.get('resolution_deadline_hours', 24)
                st.info(f"⏰ **SLA Deadline:** {sla_hours} hours")
                st.caption(f"Risk Level: {sla_result.get('risk_level', 'safe').upper()}")
            
            # Duplicate warning
            if duplicate_result.get('has_duplicates'):
                st.warning(
                    f"⚠️ **Potential Duplicate Detected!** "
                    f"Found {duplicate_result.get('duplicate_count', 0)} similar ticket(s). "
                    f"Consider reviewing before processing."
                )
                
                if duplicate_result.get('most_similar'):
                    similar = duplicate_result['most_similar']
                    st.caption(
                        f"Most similar: Ticket #{similar.get('id', 'unknown')} "
                        f"({similar.get('similarity', 0):.0%} match)"
                    )
            
            # Processing time
            st.caption(f"⚡ Triage completed in {triage_time:.2f} seconds")
        
        st.rerun()

# Routing Analytics
with col_routing:
    st.subheader("📊 Routing Analytics")
    
    if st.session_state.triage_metrics['routing_by_team']:
        st.markdown("**Tickets by Team**")
        
        for team, count in sorted(
            st.session_state.triage_metrics['routing_by_team'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            # Find icon for team
            team_icon = '📋'
            for category, info in ROUTING_RULES.items():
                if info['team'] == team:
                    team_icon = info['icon']
                    break
            
            st.metric(f"{team_icon} {team}", count)
    
    else:
        st.info("No tickets processed yet. Submit a ticket to see routing analytics.")
    
    st.markdown("---")
    
    # Quick submit examples
    st.markdown("**💡 Try Quick Examples**")
    
    examples = [
        ("Login Failed", "I can't login. Getting 'Invalid credentials' error."),
        ("Payment Declined", "Customer payment failed with error code 401. Need help ASAP."),
        ("API 500 Error", "API endpoint returning 500 errors. Check logs immediately."),
        ("DB Connection", "Database connection timeout. Production system affected."),
        ("Enable MFA", "How do I enable multi-factor authentication?")
    ]
    
    for subj, desc in examples:
        if st.button(f"📝 {subj}", key=f"ex_{subj}", use_container_width=True):
            st.session_state.example_subject = subj
            st.session_state.example_description = desc
            st.rerun()

# Recent Routing History
st.markdown("---")
st.subheader("📜 Recent Routing History")

if st.session_state.triage_metrics['routing_history']:
    # Display as table
    for record in st.session_state.triage_metrics['routing_history'][:10]:
        with st.container():
            col_id, col_details, col_routing, col_time = st.columns([1, 3, 2, 1])
            
            with col_id:
                st.markdown(f"**{record['ticket_id']}**")
                urgency_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                st.caption(f"{urgency_emoji.get(record['urgency'], '⚪')} {record['urgency']}")
            
            with col_details:
                st.markdown(f"**{record['subject']}**")
                st.caption(f"{record['intent'].upper()} • {record['category'].upper()}")
            
            with col_routing:
                # Find icon
                team_icon = '📋'
                for cat, info in ROUTING_RULES.items():
                    if info['team'] == record['team']:
                        team_icon = info['icon']
                        break
                
                st.markdown(f"{team_icon} {record['team']}")
                if record['is_duplicate']:
                    st.caption("⚠️ Duplicate detected")
            
            with col_time:
                minutes_ago = int((datetime.now() - record['timestamp']).total_seconds() / 60)
                st.caption(f"{minutes_ago}m ago")
                st.caption(f"{record['triage_time']:.1f}s")
            
            st.markdown("---")
else:
    st.info("No tickets processed yet. Submit a ticket above to see routing history.")

# Pre-fill form if example clicked
if 'example_subject' in st.session_state:
    st.info(f"💡 Example loaded: **{st.session_state.example_subject}**. Scroll up to submit the form.")
    del st.session_state.example_subject
    del st.session_state.example_description

# Footer
st.markdown("---")
st.caption("🤖 **Automated Triage:** AI classifies, detects duplicates, and routes tickets in < 3 seconds")
