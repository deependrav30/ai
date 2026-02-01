"""
Business Scenario 5: Quality Assurance & Training Dashboard

Automated QA system for agent response quality analysis and training.

Target Metrics:
- QA Coverage: 100% of tickets
- Response Quality: +25% improvement
- Training Material Freshness: < 30 days
- Agent Performance: +20% within 90 days
- CSAT: +0.5 points
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.guardrails_agent import GuardrailsAgent
from agents.reasoning_agent import ReasoningAgent
from agents.synthesis_agent import SynthesisAgent

# Initialize agents
guardrails_agent = GuardrailsAgent()
reasoning_agent = ReasoningAgent()
synthesis_agent = SynthesisAgent()

st.set_page_config(
    page_title="QA & Training Dashboard",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Quality Assurance & Training Dashboard")
st.caption("Automated quality analysis and agent coaching system")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Quality Review", 
    "🏆 Best Practices", 
    "📚 Training Materials",
    "👥 Agent Performance"
])

# Sample agent responses for QA review
SAMPLE_RESPONSES = [
    {
        "ticket_id": "TKT-1234",
        "agent": "Sarah Chen",
        "customer_query": "I've been trying to reset my password for 2 hours and nothing works. This is unacceptable!",
        "agent_response": "I apologize for the frustration you're experiencing with the password reset. I understand how important it is to access your account. Let me help you resolve this immediately.\n\nI've checked your account and see multiple reset attempts. Here's what we'll do:\n\n1. I'm sending a fresh reset link to your email (ending in @gmail.com)\n2. Please check your spam folder as well\n3. The link expires in 15 minutes, so use it right away\n4. If you still have issues, I'm available via this chat for immediate assistance\n\nI've also flagged this with our technical team to investigate why the standard process didn't work for you. Your account security is our priority.\n\nDid you receive the reset email?",
        "resolution_time": "4 minutes",
        "customer_satisfaction": 5,
        "timestamp": datetime.now() - timedelta(hours=2)
    },
    {
        "ticket_id": "TKT-1235",
        "agent": "Mike Johnson",
        "customer_query": "What's the status of my refund request from last week?",
        "agent_response": "Your refund has been processed.",
        "resolution_time": "1 minute",
        "customer_satisfaction": 2,
        "timestamp": datetime.now() - timedelta(hours=5)
    },
    {
        "ticket_id": "TKT-1236",
        "agent": "Sarah Chen",
        "customer_query": "The API is returning 500 errors when I try to create a user via POST /api/v1/users",
        "agent_response": "Thank you for reporting this API issue. I can see you're getting 500 errors on user creation, which definitely shouldn't happen.\n\nI've checked our API logs and found the issue:\n- Error: Database connection timeout during user validation\n- Affecting: POST /api/v1/users endpoint\n- Started: 30 minutes ago\n- Our engineering team is investigating\n\nTemporary workaround while we fix this:\n- Use POST /api/v2/users instead (new endpoint, same functionality)\n- Or wait 10-15 minutes for the fix deployment\n\nI've added you to the incident notification list - you'll get an email when it's fully resolved. Our SLA for P1 API issues is 1 hour, and we're on track.\n\nWould the v2 endpoint work for your use case, or would you prefer to wait?",
        "resolution_time": "6 minutes",
        "customer_satisfaction": 5,
        "timestamp": datetime.now() - timedelta(hours=1)
    },
    {
        "ticket_id": "TKT-1237",
        "agent": "Emily Rodriguez",
        "customer_query": "I need help integrating the payment SDK into my mobile app",
        "agent_response": "Sure, here's the documentation link: https://docs.example.com/payment-sdk\n\nLet me know if you need anything else.",
        "resolution_time": "2 minutes",
        "customer_satisfaction": 3,
        "timestamp": datetime.now() - timedelta(hours=3)
    },
    {
        "ticket_id": "TKT-1238",
        "agent": "Sarah Chen",
        "customer_query": "My subscription renewal failed but I was still charged!",
        "agent_response": "I'm sorry to hear about this billing issue - I can imagine how concerning it is to see a charge when the service didn't renew properly. Let me investigate this right away.\n\nI've pulled up your account and here's what happened:\n- Charge: $49.99 processed on Jan 29th ✓\n- Renewal: Failed due to account configuration error ✗\n- Status: You were charged but service didn't activate\n\nThis is clearly our mistake. Here's how I'm fixing it:\n\n1. ✓ Manually activated your subscription (effective immediately)\n2. ✓ Extended your subscription by 3 extra days as an apology\n3. ✓ Flagged the billing bug for our engineering team\n\nYou now have full access through March 1st (instead of Feb 28th). I've verified the features are working - can you try logging in?\n\nI've also added a note to prevent this from happening on your next renewal. You deserve a smooth experience, and I apologize for the inconvenience.",
        "resolution_time": "5 minutes",
        "customer_satisfaction": 5,
        "timestamp": datetime.now() - timedelta(minutes=30)
    }
]

# --- TAB 1: Quality Review ---
with tab1:
    st.header("📊 Response Quality Review")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Today's Reviews", "47", "+12")
    with col2:
        st.metric("Avg Quality Score", "8.2/10", "+0.4")
    with col3:
        st.metric("Auto-QA Coverage", "100%", "")
    with col4:
        st.metric("Issues Flagged", "3", "-2")
    
    st.divider()
    
    # Response selector
    selected_response = st.selectbox(
        "Select Response to Review",
        options=range(len(SAMPLE_RESPONSES)),
        format_func=lambda x: f"{SAMPLE_RESPONSES[x]['ticket_id']} - {SAMPLE_RESPONSES[x]['agent']} ({SAMPLE_RESPONSES[x]['timestamp'].strftime('%H:%M')})"
    )
    
    response_data = SAMPLE_RESPONSES[selected_response]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Ticket Details")
        st.markdown(f"**Ticket:** {response_data['ticket_id']}")
        st.markdown(f"**Agent:** {response_data['agent']}")
        st.markdown(f"**Resolution Time:** {response_data['resolution_time']}")
        st.markdown(f"**Customer Rating:** {'⭐' * response_data['customer_satisfaction']}")
        
        st.markdown("**Customer Query:**")
        st.info(response_data['customer_query'])
        
        st.markdown("**Agent Response:**")
        st.success(response_data['agent_response'])
        
        # AI Quality Analysis
        if st.button("🤖 Run AI Quality Analysis", key=f"analyze_{selected_response}"):
            with st.spinner("Analyzing response quality..."):
                # Use GuardrailsAgent to check for safety/compliance
                safety_check = guardrails_agent.check_safety(response_data['agent_response'])
                
                # Use ReasoningAgent to evaluate quality
                analysis_prompt = f"""Analyze this customer support response for quality:

Customer Query: {response_data['customer_query']}

Agent Response: {response_data['agent_response']}

Evaluate on these criteria (score 1-10 each):
1. Empathy & Tone: Does the agent acknowledge the customer's feelings?
2. Clarity: Is the response easy to understand?
3. Completeness: Does it fully address the query?
4. Actionability: Are next steps clear?
5. Professionalism: Appropriate language and structure?

Provide scores and specific feedback for improvement."""

                quality_analysis = reasoning_agent.reason(analysis_prompt)
                
                st.session_state[f'analysis_{selected_response}'] = {
                    'safety': safety_check,
                    'quality': quality_analysis
                }
        
        # Display analysis if available
        if f'analysis_{selected_response}' in st.session_state:
            analysis = st.session_state[f'analysis_{selected_response}']
            
            st.markdown("### 🔍 Quality Analysis Results")
            
            # Safety Check
            if analysis['safety']['is_safe']:
                st.success("✓ Safety Check: PASSED - No compliance or safety issues detected")
            else:
                st.error(f"⚠️ Safety Check: FLAGGED - {', '.join(analysis['safety']['violations'])}")
            
            # Quality Analysis
            st.markdown("**AI Quality Evaluation:**")
            st.markdown(analysis['quality'])
    
    with col2:
        st.subheader("Quality Scoring Rubric")
        
        # Calculate quality score based on response characteristics
        response_text = response_data['agent_response']
        response_length = len(response_text.split())
        has_empathy = any(word in response_text.lower() for word in ['sorry', 'apologize', 'understand', 'appreciate'])
        has_structure = '1.' in response_text or '2.' in response_text or '\n\n' in response_text
        has_action = any(word in response_text.lower() for word in ['will', 'can', 'here', 'step', 'let me'])
        csat = response_data['customer_satisfaction']
        
        # Score calculation
        empathy_score = 10 if has_empathy else 4
        clarity_score = 10 if has_structure else 6
        completeness_score = min(10, (response_length // 20))
        actionability_score = 10 if has_action else 5
        professionalism_score = csat * 2
        
        overall_score = (empathy_score + clarity_score + completeness_score + actionability_score + professionalism_score) / 5
        
        st.metric("Overall Score", f"{overall_score:.1f}/10")
        
        st.markdown("**Breakdown:**")
        st.progress(empathy_score / 10, text=f"Empathy: {empathy_score}/10")
        st.progress(clarity_score / 10, text=f"Clarity: {clarity_score}/10")
        st.progress(completeness_score / 10, text=f"Completeness: {completeness_score}/10")
        st.progress(actionability_score / 10, text=f"Actionability: {actionability_score}/10")
        st.progress(professionalism_score / 10, text=f"Professional: {professionalism_score}/10")
        
        st.divider()
        
        # Coaching suggestions
        st.markdown("**💡 Coaching Suggestions:**")
        
        suggestions = []
        if empathy_score < 7:
            suggestions.append("• Add empathy statements acknowledging customer frustration")
        if clarity_score < 7:
            suggestions.append("• Use numbered lists or bullet points for clarity")
        if completeness_score < 7:
            suggestions.append("• Provide more detailed explanation")
        if actionability_score < 7:
            suggestions.append("• Include clear next steps for the customer")
        if professionalism_score < 7:
            suggestions.append("• Review tone and professional language")
        
        if suggestions:
            for suggestion in suggestions:
                st.warning(suggestion)
        else:
            st.success("✓ Excellent response quality!")

# --- TAB 2: Best Practices ---
with tab2:
    st.header("🏆 Best Practice Library")
    st.caption("AI-detected exceptional responses for training")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Practices Identified", "24", "+3 this week")
    with col2:
        st.metric("Training Examples", "156", "+8")
    with col3:
        st.metric("Avg Agent Access", "12/day", "+2")
    
    st.divider()
    
    # Filter best practices
    category_filter = st.selectbox(
        "Filter by Category",
        ["All Categories", "Empathy & De-escalation", "Technical Problem Solving", "Billing Issues", "API Support"]
    )
    
    # Display best practice examples (using top-rated responses)
    best_practices = [r for r in SAMPLE_RESPONSES if r['customer_satisfaction'] >= 5]
    
    st.markdown(f"### 📚 Found {len(best_practices)} Exceptional Responses")
    
    for bp in best_practices:
        with st.expander(f"🏆 {bp['ticket_id']} - {bp['agent']} | CSAT: {'⭐' * bp['customer_satisfaction']}"):
            st.markdown(f"**Scenario:** {bp['customer_query'][:100]}...")
            st.markdown(f"**What Made This Great:**")
            
            # AI analysis of why this is a best practice
            highlights = []
            if 'apologize' in bp['agent_response'].lower():
                highlights.append("✓ Strong empathy and acknowledgment")
            if '1.' in bp['agent_response']:
                highlights.append("✓ Clear step-by-step guidance")
            if 'sla' in bp['agent_response'].lower():
                highlights.append("✓ Proactive SLA communication")
            if len(bp['agent_response'].split()) > 50:
                highlights.append("✓ Comprehensive explanation")
            if '?' in bp['agent_response']:
                highlights.append("✓ Engagement with follow-up questions")
            
            for h in highlights:
                st.success(h)
            
            st.markdown(f"**Full Response:**")
            st.code(bp['agent_response'], language=None)
            
            col1, col2 = st.columns(2)
            with col1:
                st.button("📋 Add to Training", key=f"train_{bp['ticket_id']}")
            with col2:
                st.button("📤 Share with Team", key=f"share_{bp['ticket_id']}")

# --- TAB 3: Training Materials ---
with tab3:
    st.header("📚 AI-Generated Training Materials")
    st.caption("Automatically curated knowledge from top performers")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Courses", "8", "+1 new")
    with col2:
        st.metric("Material Freshness", "12 days", "< 30 day target")
    with col3:
        st.metric("Agent Completion", "87%", "+5%")
    
    st.divider()
    
    # Training topic selector
    training_topic = st.selectbox(
        "Select Training Topic",
        [
            "Password Reset Best Practices",
            "Handling Angry Customers",
            "API Error Troubleshooting",
            "Billing Issue Resolution",
            "Technical Documentation Sharing"
        ]
    )
    
    st.markdown(f"### 📖 Training Module: {training_topic}")
    
    # Generate training material using AI
    if st.button("🤖 Generate Training Material", key="gen_training"):
        with st.spinner("AI is analyzing best practices and creating training content..."):
            # Use SynthesisAgent to create training material
            training_prompt = f"""Create a training module for support agents on: {training_topic}

Based on these best practice examples:

Example 1:
Query: {SAMPLE_RESPONSES[0]['customer_query']}
Response: {SAMPLE_RESPONSES[0]['agent_response']}

Example 2:
Query: {SAMPLE_RESPONSES[2]['customer_query']}
Response: {SAMPLE_RESPONSES[2]['agent_response']}

Create a training module with:
1. Learning Objectives (3-5 points)
2. Key Principles (what makes a great response)
3. Do's and Don'ts
4. Example Phrases to Use
5. Practice Scenario

Make it actionable and specific."""

            training_content = synthesis_agent.synthesize(training_prompt)
            
            st.session_state['training_content'] = training_content
    
    # Display generated training
    if 'training_content' in st.session_state:
        st.markdown(st.session_state['training_content'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("💾 Save to Library")
        with col2:
            st.button("📧 Send to Agents")
        with col3:
            st.button("📊 Create Quiz")
    
    st.divider()
    
    # Recent training materials
    st.markdown("### 📑 Recently Published Materials")
    
    materials = [
        {"title": "Empathy Statements for De-escalation", "date": "Jan 30", "views": 45},
        {"title": "API Error Code Reference Guide", "date": "Jan 28", "views": 67},
        {"title": "Billing Dispute Resolution Playbook", "date": "Jan 25", "views": 89}
    ]
    
    for mat in materials:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"📄 **{mat['title']}**")
        with col2:
            st.caption(mat['date'])
        with col3:
            st.caption(f"👁️ {mat['views']} views")

# --- TAB 4: Agent Performance ---
with tab4:
    st.header("👥 Agent Performance & Coaching")
    st.caption("Individual performance tracking and improvement areas")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Team Avg Quality", "8.2/10", "+0.4")
    with col2:
        st.metric("Agents Above Target", "12/15", "80%")
    with col3:
        st.metric("Improvement Rate", "+18%", "90 days")
    with col4:
        st.metric("Training Completion", "87%", "+5%")
    
    st.divider()
    
    # Agent selector
    agent_name = st.selectbox(
        "Select Agent",
        ["Sarah Chen", "Mike Johnson", "Emily Rodriguez", "David Kim", "Jessica Liu"]
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Performance Dashboard: {agent_name}")
        
        # Performance metrics over time
        st.markdown("**Quality Score Trend (Last 30 Days)**")
        
        # Generate sample data
        if agent_name == "Sarah Chen":
            scores = [7.5, 7.8, 8.1, 8.3, 8.6, 8.8, 9.0, 9.2]
        elif agent_name == "Mike Johnson":
            scores = [6.0, 6.2, 6.5, 6.3, 6.8, 7.0, 7.2, 7.5]
        else:
            scores = [7.0, 7.2, 7.5, 7.6, 7.8, 8.0, 8.1, 8.3]
        
        st.line_chart(scores)
        
        st.markdown("**Performance Breakdown**")
        
        # Agent-specific metrics
        metrics = {
            "Sarah Chen": {"empathy": 9.5, "clarity": 9.0, "completeness": 9.2, "action": 9.3, "professional": 9.1},
            "Mike Johnson": {"empathy": 6.5, "clarity": 7.5, "completeness": 6.0, "action": 7.0, "professional": 8.0},
            "Emily Rodriguez": {"empathy": 8.0, "clarity": 8.5, "completeness": 7.5, "action": 7.8, "professional": 8.2}
        }
        
        agent_metrics = metrics.get(agent_name, {"empathy": 8.0, "clarity": 8.0, "completeness": 8.0, "action": 8.0, "professional": 8.0})
        
        for metric, score in agent_metrics.items():
            st.progress(score / 10, text=f"{metric.title()}: {score:.1f}/10")
        
        st.divider()
        
        st.markdown("**Recent Tickets Reviewed**")
        
        agent_responses = [r for r in SAMPLE_RESPONSES if r['agent'] == agent_name]
        
        if agent_responses:
            for resp in agent_responses:
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.markdown(f"**{resp['ticket_id']}** - {resp['customer_query'][:50]}...")
                with col_b:
                    st.caption(f"{'⭐' * resp['customer_satisfaction']}")
                with col_c:
                    st.caption(resp['resolution_time'])
        else:
            st.info(f"No recent tickets for {agent_name}")
    
    with col2:
        st.subheader("💡 Coaching Insights")
        
        if agent_name == "Sarah Chen":
            st.success("🌟 **Top Performer**")
            st.markdown("**Strengths:**")
            st.markdown("• Exceptional empathy")
            st.markdown("• Clear communication")
            st.markdown("• Proactive SLA management")
            
            st.markdown("**Development Areas:**")
            st.markdown("• Continue mentoring others")
            st.markdown("• Document best practices")
            
        elif agent_name == "Mike Johnson":
            st.warning("📈 **Needs Improvement**")
            st.markdown("**Focus Areas:**")
            st.markdown("• ⚠️ Empathy & tone (6.5/10)")
            st.markdown("• ⚠️ Response completeness (6.0/10)")
            
            st.markdown("**Recommended Training:**")
            st.markdown("• Empathy statements module")
            st.markdown("• Handling angry customers")
            st.markdown("• Detailed explanation techniques")
            
            st.markdown("**Next Steps:**")
            st.markdown("• 1:1 coaching session (tomorrow)")
            st.markdown("• Shadow Sarah Chen")
            
        else:
            st.info("✓ **Meets Expectations**")
            st.markdown("**Strengths:**")
            st.markdown("• Good technical knowledge")
            st.markdown("• Professional communication")
            
            st.markdown("**Growth Opportunities:**")
            st.markdown("• Increase response depth")
            st.markdown("• Add more actionable steps")
        
        st.divider()
        
        st.markdown("**📊 Comparison to Team**")
        team_avg = 8.2
        agent_avg = sum(agent_metrics.values()) / len(agent_metrics)
        diff = agent_avg - team_avg
        
        if diff > 0:
            st.success(f"+{diff:.1f} above team average")
        else:
            st.warning(f"{diff:.1f} below team average")
        
        st.button("📧 Schedule Coaching Session")
        st.button("📚 Assign Training Module")
        st.button("📈 View Full Report")

# Footer
st.divider()
st.caption("✅ QA & Training Dashboard - Automated quality analysis powered by AI")
st.caption("💡 All agent reviews are conducted with privacy and coaching in mind")
