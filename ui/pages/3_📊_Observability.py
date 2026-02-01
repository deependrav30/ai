import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from database.chat_storage import ChatStorage
from agents.workflow import AgentWorkflow
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Observability Dashboard", layout="wide", page_icon="📊")

# Initialize storage and workflow
chat_storage = ChatStorage()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1.1em;
        opacity: 0.9;
    }
    .agent-stat {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Agent System Observability Dashboard")
st.markdown("Real-time monitoring and analytics for the multi-agent support system")

# Initialize workflow for metrics
if 'workflow' not in st.session_state:
    st.session_state.workflow = AgentWorkflow()

# Sidebar filters
with st.sidebar:
    st.header("⚙️ Filters")
    
    time_range = st.selectbox(
        "Time Range",
        ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=1
    )
    
    st.divider()
    
    refresh = st.button("🔄 Refresh Data", use_container_width=True)

# Main dashboard layout
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🤖 Agents", "📝 Execution Logs", "⚠️ Incidents"])

with tab1:
    st.header("System Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Get session data
    sessions = chat_storage.get_all_sessions()
    total_sessions = len(sessions)
    
    # Calculate metrics (mock data for now - would come from real logs)
    total_requests = total_sessions * 5  # Average 5 messages per session
    avg_response_time = 2.3  # seconds
    escalation_rate = 0.12  # 12%
    avg_confidence = 0.85  # 85%
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Requests</div>
            <div class="metric-value">{total_requests}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value">{avg_response_time}s</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="metric-label">Escalation Rate</div>
            <div class="metric-value">{escalation_rate:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div class="metric-label">Avg Confidence</div>
            <div class="metric-value">{avg_confidence:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Requests by Execution Mode")
        
        # Mock data - would come from real logs
        execution_data = pd.DataFrame({
            'Mode': ['General Chat', 'Serial', 'Parallel', 'Async'],
            'Count': [45, 28, 15, 12]
        })
        
        fig = px.pie(
            execution_data,
            values='Count',
            names='Mode',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Confidence Score Distribution")
        
        # Mock confidence data
        confidence_data = pd.DataFrame({
            'Range': ['90-100%', '80-90%', '70-80%', '60-70%', '<60%'],
            'Count': [42, 28, 18, 8, 4]
        })
        
        fig = px.bar(
            confidence_data,
            x='Range',
            y='Count',
            color='Count',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Timeline
    st.subheader("⏱️ Response Time Trend (Last 24 Hours)")
    
    # Mock timeline data
    import numpy as np
    hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
    response_times = np.random.normal(2.5, 0.5, 24)
    
    timeline_df = pd.DataFrame({
        'Time': hours,
        'Response Time (s)': response_times
    })
    
    fig = px.line(
        timeline_df,
        x='Time',
        y='Response Time (s)',
        markers=True
    )
    fig.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="SLA Target")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("🤖 Agent Performance")
    
    # Get agent metrics
    try:
        metrics = st.session_state.workflow.get_metrics()
        
        # Display each agent's metrics
        for agent_name, agent_metrics in metrics.items():
            with st.expander(f"**{agent_name.upper()}** Agent", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Executions", agent_metrics.get('execution_count', 0))
                
                with col2:
                    total_time = agent_metrics.get('total_time', 0)
                    st.metric("Total Time", f"{total_time:.2f}s")
                
                with col3:
                    avg_time = agent_metrics.get('avg_time', 0)
                    st.metric("Avg Time", f"{avg_time:.3f}s")
    
    except Exception as e:
        st.warning("No agent execution data available yet. Process some queries to see metrics.")
    
    st.divider()
    
    # Agent comparison chart
    st.subheader("⚡ Agent Execution Time Comparison")
    
    # Mock data - would come from real metrics
    agent_perf_data = pd.DataFrame({
        'Agent': ['Intent', 'Retrieval', 'Memory', 'Reasoning', 'Synthesis', 'Guardrails'],
        'Avg Time (s)': [0.45, 0.32, 0.28, 1.2, 0.95, 0.15]
    })
    
    fig = px.bar(
        agent_perf_data,
        x='Agent',
        y='Avg Time (s)',
        color='Avg Time (s)',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("📝 Execution Logs")
    
    st.info("Recent agent execution logs will appear here after processing queries.")
    
    # Mock execution log data
    log_data = [
        {
            'Timestamp': datetime.now() - timedelta(minutes=5),
            'Ticket ID': 'TICKET-001',
            'Execution Model': 'serial',
            'Agents': 'Intent → Retrieval → Memory → Reasoning → Synthesis → Guardrails',
            'Total Time': '2.8s',
            'Confidence': '92%',
            'Status': '✅ Success'
        },
        {
            'Timestamp': datetime.now() - timedelta(minutes=12),
            'Ticket ID': 'TICKET-002',
            'Execution Model': 'parallel',
            'Agents': 'Intent + Memory + Retrieval → Reasoning → Synthesis → Guardrails',
            'Total Time': '1.9s',
            'Confidence': '88%',
            'Status': '✅ Success'
        },
        {
            'Timestamp': datetime.now() - timedelta(minutes=18),
            'Ticket ID': 'TICKET-003',
            'Execution Model': 'general_chat',
            'Agents': 'GeneralChatbot',
            'Total Time': '0.5s',
            'Confidence': '95%',
            'Status': '✅ Success'
        }
    ]
    
    for log in log_data:
        with st.expander(f"{log['Ticket ID']} - {log['Timestamp'].strftime('%H:%M:%S')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Execution Model:** {log['Execution Model']}")
                st.write(f"**Agent Flow:** {log['Agents']}")
            
            with col2:
                st.metric("Time", log['Total Time'])
                st.metric("Confidence", log['Confidence'])
            
            st.markdown(f"**Status:** {log['Status']}")

with tab4:
    st.header("⚠️ Incidents & Escalations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 Safety Violations")
        st.metric("Total Blocked", 3)
        st.metric("Last 24h", 1)
        
        # Sample violations
        violations = [
            {'Time': '2 hours ago', 'Type': 'Financial Fraud', 'Action': 'Blocked'},
            {'Time': '1 day ago', 'Type': 'Self-harm', 'Action': 'Escalated'},
            {'Time': '2 days ago', 'Type': 'Jailbreak', 'Action': 'Blocked'}
        ]
        
        for v in violations:
            st.markdown(f"""
            <div class="agent-stat">
                <strong>{v['Type']}</strong><br>
                {v['Time']} - <span style="color: red;">{v['Action']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("👥 Human Escalations")
        st.metric("Total Escalated", 8)
        st.metric("Pending Review", 2)
        
        # Sample escalations
        escalations = [
            {'Time': '30 min ago', 'Reason': 'Low confidence (45%)', 'Status': 'Pending'},
            {'Time': '3 hours ago', 'Reason': 'Complex root cause', 'Status': 'Pending'},
            {'Time': '1 day ago', 'Reason': 'SLA breach risk', 'Status': 'Resolved'}
        ]
        
        for esc in escalations:
            color = 'orange' if esc['Status'] == 'Pending' else 'green'
            st.markdown(f"""
            <div class="agent-stat">
                <strong>{esc['Reason']}</strong><br>
                {esc['Time']} - <span style="color: {color};">{esc['Status']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("📊 Escalation Reasons Breakdown")
    
    esc_data = pd.DataFrame({
        'Reason': ['Low Confidence', 'SLA Risk', 'Complex Issue', 'Safety Concern', 'Unknown Pattern'],
        'Count': [12, 8, 6, 3, 2]
    })
    
    fig = px.bar(
        esc_data,
        x='Reason',
        y='Count',
        color='Count',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption("📊 Dashboard updates in real-time as agents process queries | Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
