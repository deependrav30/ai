"""
Generate realistic test documents for knowledge base testing

Creates diverse document types:
- PDF, DOCX, PPTX, TXT, Images
- Ticket scenarios across different categories
- Realistic support content
"""
import os
from datetime import datetime, timedelta
import random

# Create data directories
os.makedirs("data/test_documents/pdfs", exist_ok=True)
os.makedirs("data/test_documents/docs", exist_ok=True)
os.makedirs("data/test_documents/presentations", exist_ok=True)
os.makedirs("data/test_documents/text", exist_ok=True)

# Document templates by category
CATEGORIES = {
    "authentication": {
        "common_issues": [
            "Login failures and password resets",
            "SSO integration problems",
            "MFA not working",
            "Session timeout issues",
            "Account lockout procedures"
        ],
        "resolutions": [
            "Reset password via email link",
            "Clear browser cache and cookies",
            "Verify MFA device sync",
            "Check SSO configuration",
            "Contact admin for unlock"
        ]
    },
    "payment": {
        "common_issues": [
            "Payment gateway timeout",
            "Transaction declined errors",
            "Refund processing delays",
            "Payment method not accepted",
            "Duplicate charge issues"
        ],
        "resolutions": [
            "Retry payment after 5 minutes",
            "Verify card details and billing address",
            "Process refund within 5-7 business days",
            "Use alternate payment method",
            "Contact payment support for duplicates"
        ]
    },
    "api": {
        "common_issues": [
            "API endpoint 500 errors",
            "Rate limit exceeded",
            "Authentication token expired",
            "Webhook delivery failures",
            "API response timeout"
        ],
        "resolutions": [
            "Check API status page",
            "Implement exponential backoff",
            "Refresh authentication token",
            "Verify webhook endpoint URL",
            "Increase timeout to 30 seconds"
        ]
    },
    "database": {
        "common_issues": [
            "Connection pool exhausted",
            "Slow query performance",
            "Deadlock detected",
            "Replication lag issues",
            "Table lock timeout"
        ],
        "resolutions": [
            "Increase connection pool size",
            "Add index on query columns",
            "Review transaction isolation level",
            "Monitor replication delay",
            "Optimize long-running queries"
        ]
    },
    "network": {
        "common_issues": [
            "VPN connection failures",
            "DNS resolution errors",
            "SSL certificate expired",
            "Firewall blocking traffic",
            "Network latency spikes"
        ],
        "resolutions": [
            "Restart VPN client",
            "Flush DNS cache",
            "Renew SSL certificate",
            "Update firewall rules",
            "Check network routing"
        ]
    }
}

def generate_txt_files(count=20):
    """Generate text files with FAQs and troubleshooting guides"""
    print(f"\n📝 Generating {count} TXT files...")
    
    for i in range(count):
        category = random.choice(list(CATEGORIES.keys()))
        data = CATEGORIES[category]
        
        content = f"""# {category.upper()} TROUBLESHOOTING GUIDE
Generated: {datetime.now().strftime('%Y-%m-%d')}
Version: 1.{i}

## Common Issues

"""
        
        for idx, issue in enumerate(data['common_issues'], 1):
            content += f"{idx}. {issue}\n"
            content += f"   Resolution: {data['resolutions'][idx-1]}\n\n"
        
        content += """
## Escalation Process

If the issue persists:
1. Gather error logs and screenshots
2. Document steps to reproduce
3. Check knowledge base for similar cases
4. Escalate to L2 support if unresolved within 30 minutes

## SLA Guidelines

- Critical: 1 hour response, 4 hours resolution
- High: 2 hours response, 8 hours resolution  
- Medium: 4 hours response, 24 hours resolution
- Low: 8 hours response, 48 hours resolution
"""
        
        filename = f"data/test_documents/text/{category}_guide_{i+1:03d}.txt"
        with open(filename, 'w') as f:
            f.write(content)
    
    print(f"✅ Created {count} TXT files")

def generate_markdown_docs(count=15):
    """Generate markdown documentation"""
    print(f"\n📄 Generating {count} Markdown files...")
    
    for i in range(count):
        category = random.choice(list(CATEGORIES.keys()))
        
        content = f"""# {category.title()} Support Documentation

## Overview
This document provides comprehensive guidance for resolving {category}-related issues.

## Quick Reference

| Issue Type | Severity | Typical Resolution Time |
|------------|----------|------------------------|
| Critical   | P0       | 1-4 hours              |
| High       | P1       | 2-8 hours              |
| Medium     | P2       | 4-24 hours             |
| Low        | P3       | 8-48 hours             |

## Common Scenarios

### Scenario 1: Production Outage
**Symptoms:** Service unavailable, 500 errors
**Impact:** All users affected
**Resolution:**
1. Check service status
2. Review recent deployments
3. Rollback if needed
4. Notify stakeholders

### Scenario 2: Performance Degradation
**Symptoms:** Slow response times, timeouts
**Impact:** Partial service impact
**Resolution:**
1. Check system metrics
2. Identify bottlenecks
3. Scale resources if needed
4. Optimize queries

### Scenario 3: Configuration Issue
**Symptoms:** Feature not working, incorrect behavior
**Impact:** Specific feature affected
**Resolution:**
1. Review configuration changes
2. Compare with working environment
3. Revert incorrect settings
4. Test functionality

## Best Practices

1. **Monitor Proactively**: Set up alerts for key metrics
2. **Document Everything**: Keep detailed notes of resolutions
3. **Follow Runbooks**: Use established procedures
4. **Escalate Early**: Don't wait if uncertain
5. **Learn from Incidents**: Update documentation

## Related Documents
- Incident Response Procedure
- SLA Guidelines
- Escalation Matrix
- On-call Rotation

---
*Last Updated: {datetime.now().strftime('%Y-%m-%d')}*
*Document ID: DOC-{i+1:04d}*
"""
        
        filename = f"data/test_documents/text/{category}_documentation_{i+1:03d}.md"
        with open(filename, 'w') as f:
            f.write(content)
    
    print(f"✅ Created {count} Markdown files")

def generate_incident_reports(count=10):
    """Generate incident report files"""
    print(f"\n📋 Generating {count} incident reports...")
    
    priorities = ['P0-Critical', 'P1-High', 'P2-Medium', 'P3-Low']
    statuses = ['Resolved', 'In Progress', 'Closed']
    
    for i in range(count):
        incident_date = datetime.now() - timedelta(days=random.randint(1, 90))
        category = random.choice(list(CATEGORIES.keys()))
        priority = random.choice(priorities)
        status = random.choice(statuses)
        
        content = f"""INCIDENT REPORT
================

Incident ID: INC-{incident_date.strftime('%Y%m%d')}-{i+1:03d}
Category: {category.title()}
Priority: {priority}
Status: {status}
Reported: {incident_date.strftime('%Y-%m-%d %H:%M:%S')}

DESCRIPTION
-----------
{random.choice(CATEGORIES[category]['common_issues'])}

IMPACT
------
- Affected Users: {random.randint(1, 1000)}
- Affected Services: {random.choice(['Web Application', 'Mobile App', 'API', 'Database', 'Network'])}
- Business Impact: {random.choice(['High', 'Medium', 'Low'])}

TIMELINE
--------
{incident_date.strftime('%H:%M')} - Issue reported by user
{(incident_date + timedelta(minutes=5)).strftime('%H:%M')} - Ticket assigned to support team
{(incident_date + timedelta(minutes=15)).strftime('%H:%M')} - Investigation started
{(incident_date + timedelta(minutes=30)).strftime('%H:%M')} - Root cause identified
{(incident_date + timedelta(hours=1)).strftime('%H:%M')} - Fix implemented
{(incident_date + timedelta(hours=2)).strftime('%H:%M')} - Resolution verified

RESOLUTION
----------
{random.choice(CATEGORIES[category]['resolutions'])}

ROOT CAUSE
----------
{random.choice([
    'Configuration error in production environment',
    'Database connection pool exhaustion',
    'Third-party service degradation',
    'Recent deployment introduced regression',
    'Network infrastructure issue'
])}

PREVENTIVE MEASURES
-------------------
1. Update monitoring alerts
2. Improve deployment validation
3. Add automated tests
4. Update documentation
5. Training for team members

FOLLOW-UP ACTIONS
-----------------
[ ] Update runbook with resolution steps
[ ] Review similar past incidents
[ ] Implement preventive measures
[ ] Schedule postmortem meeting
[ ] Update knowledge base

---
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Prepared By: Support Team
"""
        
        filename = f"data/test_documents/text/incident_report_{i+1:03d}.txt"
        with open(filename, 'w') as f:
            f.write(content)
    
    print(f"✅ Created {count} incident reports")

def main():
    print("="*60)
    print("🚀 Test Document Generation Starting...")
    print("="*60)
    
    # Generate different document types
    generate_txt_files(20)
    generate_markdown_docs(15)
    generate_incident_reports(10)
    
    print("\n" + "="*60)
    print("✅ Document Generation Complete!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"  - TXT Files: 20 troubleshooting guides")
    print(f"  - Markdown: 15 documentation files")
    print(f"  - Reports: 10 incident reports")
    print(f"  - Total: 45 documents")
    print(f"\n📁 Location: data/test_documents/")
    print(f"  - text/: {20 + 15 + 10} files")
    print("\n✨ Ready for ingestion testing!")

if __name__ == "__main__":
    main()
