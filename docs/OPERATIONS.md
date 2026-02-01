# Operations Runbook

**System:** AI-Powered Support System  
**Version:** 1.0.0  
**Maintainer:** AI Support Team

---

## 🚀 Daily Operations

### Starting the System
```bash
# 1. Start all Docker services
cd /path/to/ai
docker compose up -d

# 2. Verify all services are healthy
docker compose ps

# 3. Check service health
./scripts/health_check.sh

# 4. Start Streamlit application
source venv/bin/activate
streamlit run ui/app.py
```

### Stopping the System
```bash
# 1. Stop Streamlit (Ctrl+C in terminal)

# 2. Stop Docker services gracefully
docker compose down

# 3. Force stop if needed
docker compose down --remove-orphans
docker compose down --volumes  # ⚠️ WARNING: Deletes all data
```

### Restarting Services
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart redis
docker compose restart postgres
docker compose restart chromadb
```

---

## 📊 Monitoring & Health Checks

### Check Service Status
```bash
# View all service status
docker compose ps

# View service logs
docker compose logs -f <service_name>

# Examples:
docker compose logs -f redis
docker compose logs -f postgres
docker compose logs -f chromadb
docker compose logs -f prometheus
docker compose logs -f grafana
```

### Access Monitoring Dashboards
- **Grafana:** http://localhost:3000 (admin/admin123)
- **Prometheus:** http://localhost:9090
- **AlertManager:** http://localhost:9093

### Check Resource Usage
```bash
# View Docker container stats
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a  # ⚠️ Use with caution
```

---

## 🔧 Common Maintenance Tasks

### 1. Database Maintenance

#### PostgreSQL
```bash
# Connect to database
docker exec -it ai_postgres psql -U ai_agent -d episodic_memory

# View tables
\dt

# Check ticket count
SELECT COUNT(*) FROM past_tickets;

# View recent tickets
SELECT ticket_id, summary, created_at 
FROM past_tickets 
ORDER BY created_at DESC 
LIMIT 10;

# Backup database
docker exec ai_postgres pg_dump -U ai_agent episodic_memory > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i ai_postgres psql -U ai_agent -d episodic_memory < backup_20260201.sql
```

#### Redis
```bash
# Connect to Redis
docker exec -it ai_redis redis-cli

# Check memory usage
INFO memory

# View all keys
KEYS *

# Check key count
DBSIZE

# Flush all data (⚠️ WARNING: Deletes everything)
FLUSHALL
```

#### ChromaDB
```bash
# Check collections
curl http://localhost:8001/api/v1/collections

# Get collection details
python3 << EOF
import chromadb
client = chromadb.HttpClient(host="localhost", port=8001)
collections = client.list_collections()
for col in collections:
    print(f"{col.name}: {col.count()} items")
EOF
```

### 2. Knowledge Base Updates

```bash
# Add new documents
python3 setup_knowledge_base.py

# Verify ingestion
python3 -c "
from rag.retrieval.retriever import SemanticRetriever
retriever = SemanticRetriever()
results = retriever.search('test query', top_k=5)
print(f'Found {len(results)} results')
"
```

### 3. Log Management

```bash
# View application logs
streamlit run ui/app.py --logger.level=DEBUG

# View Docker service logs
docker compose logs --tail=100 -f

# Save logs to file
docker compose logs > system_logs_$(date +%Y%m%d).txt

# Rotate logs (if not using log rotation)
docker compose logs --since 24h > logs/app_$(date +%Y%m%d).log
```

---

## 🚨 Incident Response

### Alert: Service Down

**Symptoms:**
- Service status shows "Down" in Grafana
- Health check endpoint returns error
- Application errors in UI

**Investigation:**
```bash
# 1. Check service status
docker compose ps

# 2. View service logs
docker compose logs <service_name> --tail=50

# 3. Check resource usage
docker stats --no-stream

# 4. Check network connectivity
docker network inspect ai_agent_network
```

**Resolution:**
```bash
# Restart affected service
docker compose restart <service_name>

# If restart fails, recreate service
docker compose up -d --force-recreate <service_name>

# If still failing, check configuration
docker compose config  # Validate docker-compose.yml
```

### Alert: High Error Rate

**Symptoms:**
- Agent error rate > 5%
- Errors visible in Observability dashboard
- Customer reports of failures

**Investigation:**
```bash
# 1. Check recent errors in logs
docker compose logs --since 10m | grep ERROR

# 2. View Grafana error dashboard
# Navigate to: Agent Performance > Error Rate panel

# 3. Check OpenAI API status
curl https://status.openai.com/api/v2/status.json

# 4. Test agent workflow
python3 << EOF
from agents.workflow import AgentWorkflow
workflow = AgentWorkflow()
result = workflow.process_ticket("Test query")
print(result)
EOF
```

**Resolution:**
- If OpenAI API issues: Wait for service restoration or switch to fallback model
- If database issues: Restart database service
- If code issues: Review logs, fix bug, redeploy
- If rate limiting: Implement exponential backoff or increase quota

### Alert: High Response Time

**Symptoms:**
- P95 latency > 5 seconds
- UI feels sluggish
- Timeout errors

**Investigation:**
```bash
# 1. Check system resources
docker stats

# 2. Check database query performance
docker exec -it ai_postgres psql -U ai_agent -d episodic_memory -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;"

# 3. Check OpenAI API latency in logs

# 4. Run performance benchmark
python3 benchmark_performance.py
```

**Resolution:**
- Scale up resources (CPU, RAM)
- Optimize slow database queries
- Add caching layer
- Reduce OpenAI API timeout
- Enable parallel agent execution

---

## 🔄 Backup & Restore

### Automated Backups

**Schedule:** Daily at 2 AM UTC

```bash
# PostgreSQL backup
docker exec ai_postgres pg_dump -U ai_agent episodic_memory | gzip > backups/postgres_$(date +%Y%m%d_%H%M%S).sql.gz

# ChromaDB backup
docker cp ai_chromadb:/chroma/chroma backups/chromadb_$(date +%Y%m%d_%H%M%S)

# Redis backup (automatic via AOF)
docker exec ai_redis redis-cli BGSAVE
docker cp ai_redis:/data/dump.rdb backups/redis_$(date +%Y%m%d_%H%M%S).rdb
```

**Add to crontab:**
```bash
0 2 * * * /path/to/ai/scripts/backup.sh
```

### Manual Backup
```bash
# Create backup script
./scripts/backup.sh

# Verify backup created
ls -lh backups/
```

### Restore from Backup
```bash
# 1. Stop services
docker compose down

# 2. Restore PostgreSQL
gunzip < backups/postgres_20260201_020000.sql.gz | docker exec -i ai_postgres psql -U ai_agent -d episodic_memory

# 3. Restore ChromaDB
docker cp backups/chromadb_20260201_020000 ai_chromadb:/chroma/chroma

# 4. Restore Redis
docker cp backups/redis_20260201_020000.rdb ai_redis:/data/dump.rdb

# 5. Restart services
docker compose up -d
```

---

## 📈 Scaling Guidelines

### Horizontal Scaling

**When to scale:**
- CPU usage consistently > 70%
- Response time P95 > 5 seconds
- Active sessions > 500

**How to scale:**
```bash
# Option 1: Add more Streamlit instances (load balancer required)
streamlit run ui/app.py --server.port 8501 &
streamlit run ui/app.py --server.port 8502 &
streamlit run ui/app.py --server.port 8503 &

# Option 2: Deploy to Kubernetes
kubectl apply -f k8s/deployment.yml
kubectl scale deployment ai-agents --replicas=5
```

### Vertical Scaling

```yaml
# docker-compose.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## 🧹 Cleanup & Maintenance

### Weekly Tasks
```bash
# Clean Docker cache
docker system prune -f

# Vacuum PostgreSQL
docker exec ai_postgres psql -U ai_agent -d episodic_memory -c "VACUUM ANALYZE;"

# Check disk usage
df -h
docker system df
```

### Monthly Tasks
```bash
# Review and archive old logs
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;

# Update dependencies
pip list --outdated
pip install -r requirements.txt --upgrade

# Review alert thresholds
# Edit: docker/prometheus/alerts/ai_agents.yml

# Performance review
python3 benchmark_performance.py > reports/performance_$(date +%Y%m).txt
```

---

## 🔍 Debugging Tips

### Enable Debug Logging
```bash
# Streamlit debug mode
streamlit run ui/app.py --logger.level=DEBUG

# Agent debug logs
LOG_LEVEL=DEBUG python3 -c "from agents.workflow import AgentWorkflow; ..."
```

### Interactive Debugging
```python
# Add breakpoint in agent code
import pdb; pdb.set_trace()

# Or use IPython
from IPython import embed; embed()
```

### Performance Profiling
```python
# Profile agent execution
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run agent workflow
workflow.process_ticket("query")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## 📞 Escalation Matrix

### L1: Self-Service (< 15 min)
- Restart services
- Check health endpoints
- Review recent logs
- Consult this runbook

### L2: On-Call Engineer (< 1 hour)
- Database issues
- Performance degradation
- Configuration problems
- Contact: oncall@example.com

### L3: Senior Engineer (< 4 hours)
- Architecture issues
- Data corruption
- Security incidents
- Contact: engineering-lead@example.com

### L4: Vendor Support (< 24 hours)
- OpenAI API issues
- Cloud provider outages
- Third-party integrations
- Contact: vendors' support channels

---

## 📚 Related Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Initial deployment guide
- [MONITORING.md](MONITORING.md) - Monitoring and alerting guide
- [docker/README.md](../docker/README.md) - Docker configuration details
- [PHASE11_PLAN.md](../PHASE11_PLAN.md) - Production deployment roadmap

---

*Operations runbook for production AI agent system* 🛠️
