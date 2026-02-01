# Monitoring & Observability Setup

This directory contains configuration for production monitoring infrastructure.

## 📊 Components

### Prometheus (Metrics Collection)
- **Port:** 9090
- **Config:** `prometheus/prometheus.yml`
- **Alerts:** `prometheus/alerts/ai_agents.yml`
- **Retention:** 30 days
- **URL:** http://localhost:9090

### Grafana (Dashboards)
- **Port:** 3000
- **User:** admin
- **Password:** admin123 (change in production!)
- **Dashboards:** 
  - System Overview: Service health and uptime
  - Agent Performance: Execution metrics and response times
  - Database Metrics: Redis, PostgreSQL, ChromaDB status
- **URL:** http://localhost:3000

### AlertManager (Alert Routing)
- **Port:** 9093
- **Config:** `alertmanager/alertmanager.yml`
- **Alert Levels:** Critical, Warning, Info
- **URL:** http://localhost:9093

## 🚀 Quick Start

### 1. Start Monitoring Stack
```bash
docker-compose up -d prometheus grafana alertmanager
```

### 2. Verify Services
```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check AlertManager
curl http://localhost:9093/-/healthy
```

### 3. Access Dashboards
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin123)
- AlertManager: http://localhost:9093

### 4. View Metrics
Grafana will automatically load:
- **System Overview** dashboard
- **Agent Performance** dashboard
- **Database Metrics** dashboard

## 📈 Available Metrics

### Agent Metrics
- `agent_executions_total` - Total executions by agent type
- `agent_duration_seconds` - Execution time histogram
- `agent_errors_total` - Error count by agent and error type

### OpenAI API Metrics
- `openai_api_calls_total` - API calls by model
- `openai_api_duration_seconds` - API latency histogram
- `openai_api_tokens_total` - Token usage (prompt + completion)

### Memory Metrics
- `memory_operations_total` - Operations by type (read/write/delete)
- `memory_operation_duration_seconds` - Operation latency

### Workflow Metrics
- `workflow_executions_total` - Workflow runs
- `workflow_duration_seconds` - End-to-end workflow time

### Ticket Metrics
- `tickets_processed_total` - Tickets by intent, urgency, status
- `ticket_resolution_time_seconds` - Resolution time histogram

### System Metrics
- `system_health_status` - Health by component (0-1)
- `active_sessions_total` - Current active user sessions

## 🔔 Alert Rules

### Critical Alerts (Page Immediately)
- Any service down for > 1 minute
- Database connectivity lost
- Error rate > 5%

### Warning Alerts (Email Notification)
- High response time (P95 > 5s)
- Error rate > 2%
- Memory usage > 80%

### Info Alerts (Dashboard Only)
- Performance degradation
- Unusual traffic patterns

## 📝 Custom Metrics Integration

To add metrics to your agents, use the instrumentation in `utils/metrics.py`:

```python
from utils.metrics import track_agent_execution, track_openai_call, MetricsContext

class YourAgent:
    @track_agent_execution("your_agent")
    def process(self, query: str):
        # Your logic here
        
        # Track OpenAI calls
        with MetricsContext("openai", {"model": "gpt-4", "operation": "chat"}):
            response = openai.chat.completions.create(...)
        
        track_openai_call("gpt-4", "chat", {"prompt": 100, "completion": 50})
        
        return result
```

## 🔧 Configuration Files

```
docker/
├── prometheus/
│   ├── prometheus.yml          # Main Prometheus config
│   └── alerts/
│       └── ai_agents.yml       # Alert rules
├── grafana/
│   ├── datasources/
│   │   └── datasources.yml     # Prometheus + PostgreSQL datasources
│   └── dashboards/
│       ├── dashboard-provider.yml
│       ├── system_overview.json
│       ├── agent_performance.json
│       └── database_metrics.json
└── alertmanager/
    └── alertmanager.yml        # Alert routing config
```

## 📊 Next Steps

1. **Start Services:** `docker-compose up -d`
2. **Verify Health:** Check all health endpoints
3. **View Dashboards:** Open Grafana at http://localhost:3000
4. **Instrument Code:** Add `@track_agent_execution` to agent methods
5. **Test Alerts:** Trigger test alerts to verify routing
6. **Customize:** Adjust thresholds and add custom metrics

## 🎯 Production Checklist

- [ ] Change Grafana admin password
- [ ] Configure alert notification channels (Slack, email, PagerDuty)
- [ ] Set up backup for Prometheus data
- [ ] Configure SSL/TLS for dashboards
- [ ] Implement authentication for Prometheus/Grafana
- [ ] Set up log rotation
- [ ] Document runbooks for each alert
- [ ] Load test with realistic traffic
- [ ] Establish SLO baselines

---

*Production-grade monitoring for AI agent system* 🚀
