# Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** February 1, 2026  
**Environment:** Production

---

## 🎯 Overview

This guide provides step-by-step instructions for deploying the AI-Powered Support System to production environments.

---

## ✅ Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu 22.04+ recommended) or macOS
- **Docker:** 24.0+ with Docker Compose v2
- **RAM:** 8GB minimum, 16GB recommended
- **CPU:** 4 cores minimum, 8 cores recommended
- **Disk:** 50GB minimum for data volumes
- **Network:** Stable internet for OpenAI API calls

### Required Credentials
- OpenAI API key with GPT-4 access
- GitHub access (for code repository)
- SMTP server (optional, for alerts)
- Slack webhook (optional, for notifications)

### Software Dependencies
```bash
# Install Docker (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version  # Should be 24.0+
docker compose version  # Should be v2.0+
```

---

## 📦 Deployment Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/deependrav30/ai.git
cd ai
```

### Step 2: Configure Environment
```bash
# Create .env file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required Environment Variables:**
```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-...

# Database Configuration
POSTGRES_USER=ai_agent
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=episodic_memory

# ChromaDB Authentication
CHROMA_SERVER_AUTH_CREDENTIALS=your_chroma_token_here

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# Monitoring (optional)
GRAFANA_ADMIN_PASSWORD=change_me_in_production
ALERT_EMAIL=team@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 3: Start Infrastructure Services
```bash
# Start all services
docker compose up -d

# Verify all services are healthy
docker compose ps

# Expected output:
# NAME            STATUS              PORTS
# ai_redis        Up (healthy)        0.0.0.0:6380->6379/tcp
# ai_postgres     Up (healthy)        0.0.0.0:5433->5432/tcp
# ai_chromadb     Up (healthy)        0.0.0.0:8001->8000/tcp
# ai_prometheus   Up (healthy)        0.0.0.0:9090->9090/tcp
# ai_grafana      Up (healthy)        0.0.0.0:3000->3000/tcp
# ai_alertmanager Up (healthy)        0.0.0.0:9093->9093/tcp
```

### Step 4: Initialize Database
```bash
# Database is auto-initialized from init.sql
# Verify initialization
docker exec -it ai_postgres psql -U ai_agent -d episodic_memory -c "\dt"

# Expected tables:
# - past_tickets
# - resolutions
# - ticket_patterns
```

### Step 5: Verify Knowledge Base
```bash
# Run knowledge base setup
python3 setup_knowledge_base.py

# Expected output:
# ✓ Copied knowledge base to upload location
# ✓ Processing document into vector store
# ✓ Document processed successfully
# ✓ Found 8 chunks in ChromaDB
```

### Step 6: Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify critical packages
python3 -c "import openai, chromadb, streamlit, prometheus_client; print('✓ All dependencies installed')"
```

### Step 7: Start Application
```bash
# Start Streamlit application
streamlit run ui/app.py

# Application will be available at:
# http://localhost:8501
```

### Step 8: Verify Deployment
```bash
# Run health checks
./scripts/health_check.sh

# Check monitoring dashboards
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - AlertManager: http://localhost:9093

# Run smoke tests
python3 -m pytest tests/ -v -k "test_workflow"
```

---

## 🔍 Health Check Endpoints

### Application Health
```bash
# Test basic connectivity
curl http://localhost:8501

# Test agent workflow (manual in UI)
# Navigate to: Agent Chat page
# Send test query: "Password reset issue"
# Verify: All agents execute successfully
```

### Infrastructure Health
```bash
# Redis
docker exec ai_redis redis-cli ping
# Expected: PONG

# PostgreSQL
docker exec ai_postgres pg_isready -U ai_agent
# Expected: accepting connections

# ChromaDB
curl http://localhost:8001/api/v1/heartbeat
# Expected: {"nanosecond heartbeat": ...}

# Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# Grafana
curl http://localhost:3000/api/health
# Expected: {"commit": "...", "database": "ok", "version": "..."}
```

---

## 🎛️ Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Streamlit | 8501 | Web UI |
| Redis | 6380 | Working Memory |
| PostgreSQL | 5433 | Episodic Memory |
| ChromaDB | 8001 | Semantic Memory |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards |
| AlertManager | 9093 | Alerts |

---

## 🔄 Rollback Procedure

If deployment fails or issues arise:

```bash
# Step 1: Stop new application
docker compose down

# Step 2: Restore from backup (if needed)
./scripts/restore_backup.sh <backup_timestamp>

# Step 3: Start previous version
git checkout <previous_commit>
docker compose up -d

# Step 4: Verify rollback
./scripts/health_check.sh
```

---

## 🔐 Security Considerations

### Production Hardening
1. **Change Default Passwords:**
   ```bash
   # Update in .env file:
   - Grafana admin password
   - PostgreSQL password
   - ChromaDB auth token
   ```

2. **Enable HTTPS:**
   - Use nginx or Traefik reverse proxy
   - Configure SSL certificates (Let's Encrypt)

3. **Network Security:**
   - Restrict port access via firewall
   - Use private networks for inter-service communication
   - Enable Docker network isolation

4. **API Security:**
   - Store OpenAI API key in secrets manager
   - Rotate keys regularly
   - Monitor API usage and costs

### Secrets Management
```bash
# Option 1: Docker Secrets (Swarm mode)
echo "your_api_key" | docker secret create openai_api_key -

# Option 2: AWS Secrets Manager
aws secretsmanager create-secret --name ai-agent/openai-key --secret-string "your_api_key"

# Option 3: HashiCorp Vault
vault kv put secret/ai-agent openai_key="your_api_key"
```

---

## 📊 Monitoring Setup

### Access Grafana
1. Navigate to http://localhost:3000
2. Login: `admin` / `admin123`
3. View pre-configured dashboards:
   - System Overview
   - Agent Performance
   - Database Metrics

### Configure Alerts
1. Edit `docker/alertmanager/alertmanager.yml`
2. Add notification channels:
   ```yaml
   receivers:
     - name: 'critical-alerts'
       slack_configs:
         - api_url: 'YOUR_SLACK_WEBHOOK'
           channel: '#alerts-critical'
       pagerduty_configs:
         - service_key: 'YOUR_PAGERDUTY_KEY'
   ```
3. Restart AlertManager:
   ```bash
   docker compose restart alertmanager
   ```

---

## 🧪 Smoke Tests

Run these tests after deployment to verify functionality:

```bash
# 1. Unit tests
python3 -m pytest tests/ -v

# 2. Integration tests
python3 test_workflow.py
python3 test_e2e.py

# 3. Load test (optional)
# Install: pip install locust
# Run: locust -f tests/load_test.py --host http://localhost:8501
```

---

## 📝 Post-Deployment Checklist

- [ ] All Docker services healthy (`docker compose ps`)
- [ ] Database initialized with schema (`\dt` in postgres)
- [ ] Knowledge base loaded (check ChromaDB collection count)
- [ ] Streamlit UI accessible (http://localhost:8501)
- [ ] All 9 pages load without errors
- [ ] Agent Chat successfully processes test query
- [ ] Prometheus collecting metrics (check targets page)
- [ ] Grafana dashboards show data
- [ ] Alerts configured and tested
- [ ] Health checks passing
- [ ] Backups scheduled
- [ ] Documentation reviewed with team

---

## 🆘 Troubleshooting

### Issue: Service won't start
```bash
# Check logs
docker compose logs <service_name>

# Common fixes:
docker compose down
docker compose up -d
```

### Issue: Database connection failed
```bash
# Check PostgreSQL logs
docker compose logs postgres

# Verify credentials in .env file
# Test connection:
docker exec -it ai_postgres psql -U ai_agent -d episodic_memory
```

### Issue: ChromaDB not accessible
```bash
# Check ChromaDB logs
docker compose logs chromadb

# Verify auth token matches in .env and ChromaDB config
# Test API:
curl http://localhost:8001/api/v1/heartbeat
```

### Issue: Streamlit errors
```bash
# Check Python dependencies
pip install -r requirements.txt

# Verify OpenAI API key
python3 -c "import os; print('OPENAI_API_KEY' in os.environ)"

# Check logs
streamlit run ui/app.py --logger.level=debug
```

---

## 📞 Support

- **Documentation:** See `docker/README.md` for monitoring details
- **Operations:** See `OPERATIONS.md` for day-to-day procedures
- **GitHub Issues:** https://github.com/deependrav30/ai/issues

---

*Deployment guide for AI Agent Support System v1.0.0*
