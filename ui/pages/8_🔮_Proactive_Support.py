"""
Proactive Support Dashboard
Pattern detection, trend analysis, and preventive insights
"""
import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.reasoning_agent import ReasoningAgent
from agents.retrieval_agent import RetrievalAgent
from datetime import datetime, timedelta
import time
import random

# Page config
st.set_page_config(
    page_title="Proactive Support",
    page_icon="🔮",
    layout="wide"
)

# Initialize agents
@st.cache_resource
def get_agents():
    return {
        'reasoning': ReasoningAgent(),
        'retrieval': RetrievalAgent()
    }

agents = get_agents()

# Simulated ticket data for pattern detection
SIMULATED_TICKETS = [
    # Authentication pattern
    {'id': 'T-1001', 'category': 'authentication', 'issue': 'SSO login failure', 'time': datetime.now() - timedelta(hours=2)},
    {'id': 'T-1005', 'category': 'authentication', 'issue': 'SSO timeout error', 'time': datetime.now() - timedelta(hours=1.5)},
    {'id': 'T-1008', 'category': 'authentication', 'issue': 'Cannot login via SSO', 'time': datetime.now() - timedelta(hours=1)},
    {'id': 'T-1012', 'category': 'authentication', 'issue': 'SSO redirect broken', 'time': datetime.now() - timedelta(minutes=45)},
    {'id': 'T-1015', 'category': 'authentication', 'issue': 'SSO authentication failing', 'time': datetime.now() - timedelta(minutes=30)},
    
    # Payment pattern
    {'id': 'T-1003', 'category': 'payment', 'issue': 'Payment gateway timeout', 'time': datetime.now() - timedelta(hours=3)},
    {'id': 'T-1009', 'category': 'payment', 'issue': 'Payment processing slow', 'time': datetime.now() - timedelta(hours=2)},
    {'id': 'T-1014', 'category': 'payment', 'issue': 'Payment gateway error 504', 'time': datetime.now() - timedelta(hours=1)},
    
    # API issues
    {'id': 'T-1002', 'category': 'api', 'issue': 'API 500 error on webhook', 'time': datetime.now() - timedelta(hours=4)},
    {'id': 'T-1007', 'category': 'api', 'issue': 'API response time degraded', 'time': datetime.now() - timedelta(hours=2.5)},
    
    # Database issues
    {'id': 'T-1011', 'category': 'database', 'issue': 'Database connection timeout', 'time': datetime.now() - timedelta(hours=5)},
    {'id': 'T-1013', 'category': 'database', 'issue': 'Slow query performance', 'time': datetime.now() - timedelta(hours=3)},
]

# Session state
if 'detected_patterns' not in st.session_state:
    st.session_state.detected_patterns = []
if 'alerts_dismissed' not in st.session_state:
    st.session_state.alerts_dismissed = set()
if 'kb_articles_created' not in st.session_state:
    st.session_state.kb_articles_created = 0

# Header
st.title("🔮 Proactive Support Dashboard")
st.markdown("**AI-powered pattern detection and preventive insights**")

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Count recent tickets (last 6 hours)
    recent_tickets = [t for t in SIMULATED_TICKETS 
                     if (datetime.now() - t['time']).total_seconds() < 6*3600]
    st.metric("Tickets (6h)", len(recent_tickets))

with col2:
    # Detect patterns
    patterns_detected = 0
    
    # Group by category and time window
    category_counts = {}
    time_window = timedelta(hours=3)
    
    for ticket in SIMULATED_TICKETS:
        if (datetime.now() - ticket['time']) < time_window:
            cat = ticket['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Pattern = 3+ tickets in same category within 3 hours
    for cat, count in category_counts.items():
        if count >= 3:
            patterns_detected += 1
    
    st.metric("Patterns Detected", patterns_detected, 
             delta="2 new" if patterns_detected > 0 else None)

with col3:
    prevented_impact = random.randint(50, 150) if patterns_detected > 0 else 0
    st.metric("Prevented Impacts", prevented_impact)

with col4:
    st.metric("KB Articles Created", st.session_state.kb_articles_created)

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["🚨 Active Alerts", "📈 Trend Analysis", "💡 Insights", "📚 KB Generator"])

with tab1:
    st.subheader("🚨 Active Pattern Alerts")
    
    # Analyze patterns
    active_alerts = []
    
    # SSO pattern
    sso_tickets = [t for t in SIMULATED_TICKETS 
                   if 'SSO' in t['issue'] or 'sso' in t['issue']]
    recent_sso = [t for t in sso_tickets 
                  if (datetime.now() - t['time']).total_seconds() < 3*3600]
    
    if len(recent_sso) >= 3:
        active_alerts.append({
            'id': 'ALERT-001',
            'severity': 'critical',
            'title': 'SSO Authentication Failure Spike',
            'description': f'{len(recent_sso)} SSO-related tickets in last 3 hours',
            'category': 'authentication',
            'tickets': [t['id'] for t in recent_sso],
            'recommendation': 'Check SSO provider status and authentication service logs',
            'impact': 'High - Affecting user login across all services',
            'trend': 'Increasing',
            'first_detected': min([t['time'] for t in recent_sso])
        })
    
    # Payment gateway pattern
    payment_tickets = [t for t in SIMULATED_TICKETS if t['category'] == 'payment']
    recent_payment = [t for t in payment_tickets 
                     if (datetime.now() - t['time']).total_seconds() < 4*3600]
    
    if len(recent_payment) >= 3:
        active_alerts.append({
            'id': 'ALERT-002',
            'severity': 'high',
            'title': 'Payment Gateway Performance Degradation',
            'description': f'{len(recent_payment)} payment issues detected',
            'category': 'payment',
            'tickets': [t['id'] for t in recent_payment],
            'recommendation': 'Monitor payment gateway response times and check provider status',
            'impact': 'Medium - Transactions processing slowly',
            'trend': 'Stable',
            'first_detected': min([t['time'] for t in recent_payment])
        })
    
    # Display alerts
    if active_alerts:
        for alert in active_alerts:
            if alert['id'] in st.session_state.alerts_dismissed:
                continue
            
            # Alert severity color
            if alert['severity'] == 'critical':
                alert_type = st.error
                severity_icon = '🔴'
            elif alert['severity'] == 'high':
                alert_type = st.warning
                severity_icon = '🟠'
            else:
                alert_type = st.info
                severity_icon = '🟡'
            
            with alert_type:
                col_alert, col_dismiss = st.columns([5, 1])
                
                with col_alert:
                    st.markdown(f"### {severity_icon} {alert['title']}")
                    st.markdown(f"**{alert['description']}**")
                    
                    col_detail1, col_detail2, col_detail3 = st.columns(3)
                    
                    with col_detail1:
                        st.caption(f"📂 Category: {alert['category'].upper()}")
                    
                    with col_detail2:
                        time_ago = datetime.now() - alert['first_detected']
                        minutes = int(time_ago.total_seconds() / 60)
                        st.caption(f"⏱️ First detected: {minutes}m ago")
                    
                    with col_detail3:
                        st.caption(f"📊 Trend: {alert['trend']}")
                    
                    st.markdown(f"**💡 Recommendation:** {alert['recommendation']}")
                    st.caption(f"**Impact:** {alert['impact']}")
                    st.caption(f"**Related tickets:** {', '.join(alert['tickets'])}")
                
                with col_dismiss:
                    if st.button("✖️", key=f"dismiss_{alert['id']}"):
                        st.session_state.alerts_dismissed.add(alert['id'])
                        st.rerun()
    
    else:
        st.success("✅ No active pattern alerts. System operating normally.")
    
    # Run pattern analysis button
    if st.button("🔄 Refresh Pattern Detection", type="primary"):
        with st.spinner("🔍 Analyzing ticket patterns..."):
            time.sleep(1.5)
        st.rerun()

with tab2:
    st.subheader("📈 Trend Analysis")
    
    # Category distribution
    st.markdown("### Ticket Volume by Category (Last 24h)")
    
    category_data = {}
    for ticket in SIMULATED_TICKETS:
        cat = ticket['category']
        category_data[cat] = category_data.get(cat, 0) + 1
    
    # Display as metrics
    cols = st.columns(len(category_data))
    for i, (category, count) in enumerate(sorted(category_data.items(), 
                                                  key=lambda x: x[1], 
                                                  reverse=True)):
        with cols[i]:
            # Icon mapping
            icons = {
                'authentication': '🔐',
                'payment': '💳',
                'api': '🔧',
                'database': '🗄️',
                'network': '🌐'
            }
            icon = icons.get(category, '📋')
            st.metric(f"{icon} {category.title()}", count)
    
    st.markdown("---")
    
    # Time-based analysis
    st.markdown("### Hourly Ticket Distribution")
    
    # Group by hour
    hourly_data = {}
    for ticket in SIMULATED_TICKETS:
        hour = ticket['time'].hour
        hourly_data[hour] = hourly_data.get(hour, 0) + 1
    
    # Simple text-based chart
    st.markdown("```")
    max_count = max(hourly_data.values()) if hourly_data else 1
    for hour in range(24):
        count = hourly_data.get(hour, 0)
        bar = '█' * int((count / max_count) * 20)
        st.text(f"{hour:02d}:00 | {bar} {count}")
    st.markdown("```")
    
    st.markdown("---")
    
    # Emerging issues
    st.markdown("### 🆕 Emerging Issues (Last 6h)")
    
    recent_issues = {}
    cutoff = datetime.now() - timedelta(hours=6)
    
    for ticket in SIMULATED_TICKETS:
        if ticket['time'] > cutoff:
            # Extract key terms
            issue = ticket['issue']
            for term in ['SSO', 'payment', 'gateway', 'API', 'database', 'timeout']:
                if term.lower() in issue.lower():
                    recent_issues[term] = recent_issues.get(term, 0) + 1
    
    if recent_issues:
        for term, count in sorted(recent_issues.items(), 
                                  key=lambda x: x[1], 
                                  reverse=True)[:5]:
            st.markdown(f"- **{term}**: {count} mentions")
    else:
        st.info("No emerging patterns detected")

with tab3:
    st.subheader("💡 AI-Generated Insights")
    
    # Use reasoning agent to analyze patterns
    if st.button("🤖 Generate Insights from Recent Patterns"):
        with st.spinner("🧠 AI analyzing patterns and generating insights..."):
            # Prepare context
            pattern_summary = []
            if len(recent_sso) >= 3:
                pattern_summary.append(f"SSO authentication issues: {len(recent_sso)} tickets")
            if len(recent_payment) >= 3:
                pattern_summary.append(f"Payment gateway issues: {len(recent_payment)} tickets")
            
            context_str = "\n".join(pattern_summary) if pattern_summary else "No significant patterns"
            
            # Get reasoning
            reasoning_result = agents['reasoning'].process({
                'query': f"Analyze these support ticket patterns and provide insights: {context_str}",
                'retrieved_docs': [],
                'past_tickets': SIMULATED_TICKETS[-5:]
            })
            
            insights = reasoning_result.get('analysis', 'No insights available')
            
            st.success("✅ Insights generated!")
            st.markdown("### 🧠 AI Analysis")
            st.info(insights)
            
            # Recommendations
            st.markdown("### 📋 Recommended Actions")
            
            if len(recent_sso) >= 3:
                st.markdown("""
                **SSO Authentication Issues:**
                1. Check SSO provider (Okta/Auth0) service status
                2. Review authentication service logs for errors
                3. Verify SSL certificate validity
                4. Test SSO flow in staging environment
                5. Create proactive customer notification if widespread
                """)
            
            if len(recent_payment) >= 3:
                st.markdown("""
                **Payment Gateway Issues:**
                1. Monitor payment provider API response times
                2. Check for rate limiting or throttling
                3. Review recent gateway configuration changes
                4. Implement retry logic with exponential backoff
                5. Consider switching to backup payment processor
                """)
    
    st.markdown("---")
    
    # Root cause correlation
    st.markdown("### 🔍 Potential Root Causes")
    
    col_cause1, col_cause2 = st.columns(2)
    
    with col_cause1:
        st.markdown("**Infrastructure Events**")
        st.markdown("""
        - Recent deployment: 2 hours ago
        - Database failover: 4 hours ago
        - CDN cache purge: 1 hour ago
        """)
    
    with col_cause2:
        st.markdown("**External Factors**")
        st.markdown("""
        - SSO provider incident (ongoing)
        - Payment gateway maintenance window
        - Increased traffic (+40% vs yesterday)
        """)

with tab4:
    st.subheader("📚 Knowledge Base Article Generator")
    
    st.markdown("Generate preventive documentation from detected patterns")
    
    # Select pattern to document
    if active_alerts:
        selected_alert = st.selectbox(
            "Select pattern to document",
            options=active_alerts,
            format_func=lambda x: x['title']
        )
        
        if st.button("📝 Generate KB Article", type="primary"):
            with st.spinner("✍️ AI generating knowledge base article..."):
                time.sleep(2)
                
                # Simulate KB article generation
                article_title = f"Troubleshooting: {selected_alert['title']}"
                
                article_content = f"""
# {article_title}

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Category:** {selected_alert['category'].title()}
**Severity:** {selected_alert['severity'].upper()}

## Overview
{selected_alert['description']}

## Symptoms
Users experiencing:
- {selected_alert['title']}
- Error messages related to {selected_alert['category']}
- Impact: {selected_alert['impact']}

## Common Causes
Based on analysis of {len(selected_alert['tickets'])} related incidents:
1. Service provider outage or degradation
2. Recent deployment or configuration change
3. Network connectivity issues
4. SSL/TLS certificate expiration
5. Rate limiting or quota exhaustion

## Resolution Steps

### For Users
1. Try clearing browser cache and cookies
2. Attempt login using incognito/private browsing mode
3. Check your internet connection
4. If issue persists, contact support

### For Support Agents
1. Check {selected_alert['category']} service status page
2. Review recent deployments (last 24 hours)
3. Verify SSL certificates are valid
4. Check service logs for error patterns
5. Monitor response times and success rates

### For Operations Team
{selected_alert['recommendation']}

## Related Tickets
{', '.join(selected_alert['tickets'])}

## Prevention
To prevent similar issues:
- Implement health checks and monitoring
- Set up automated alerts for service degradation
- Maintain service provider status subscriptions
- Document rollback procedures
- Test in staging before production deployments

## See Also
- [{selected_alert['category'].title()} Service Documentation](#)
- [Incident Response Playbook](#)
- [System Status Page](#)
"""
                
                st.session_state.kb_articles_created += 1
                
                st.success(f"✅ Knowledge base article created: **{article_title}**")
                
                # Display article
                with st.expander("📄 View Generated Article", expanded=True):
                    st.markdown(article_content)
                
                # Actions
                col_kb1, col_kb2, col_kb3 = st.columns(3)
                
                with col_kb1:
                    st.button("💾 Save to KB")
                
                with col_kb2:
                    st.button("📧 Email to Team")
                
                with col_kb3:
                    st.button("📋 Copy Markdown")
    else:
        st.info("No active patterns detected. Generate alerts first to create KB articles.")

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.caption("🔮 Proactive pattern detection")

with col_footer2:
    st.caption("⚡ Real-time trend analysis")

with col_footer3:
    st.caption("📚 Auto-generate KB articles")
