"""
Metrics Instrumentation for AI Agent System

Provides Prometheus metrics collection for:
- Agent execution time and count
- Agent success/failure rates
- OpenAI API calls and latency
- Memory operations
- Error tracking
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
import time
from functools import wraps
from typing import Callable, Any

# Agent execution metrics
agent_executions_total = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_type', 'status']  # status: success, failure
)

agent_duration_seconds = Histogram(
    'agent_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

agent_errors_total = Counter(
    'agent_errors_total',
    'Total number of agent errors',
    ['agent_type', 'error_type']
)

# OpenAI API metrics
openai_api_calls_total = Counter(
    'openai_api_calls_total',
    'Total number of OpenAI API calls',
    ['model', 'operation']  # operation: chat, embedding
)

openai_api_duration_seconds = Histogram(
    'openai_api_duration_seconds',
    'OpenAI API call duration in seconds',
    ['model', 'operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
)

openai_api_tokens_total = Counter(
    'openai_api_tokens_total',
    'Total tokens consumed from OpenAI API',
    ['model', 'token_type']  # token_type: prompt, completion
)

# Memory operation metrics
memory_operations_total = Counter(
    'memory_operations_total',
    'Total number of memory operations',
    ['memory_type', 'operation']  # memory_type: working, episodic, semantic; operation: read, write, delete
)

memory_operation_duration_seconds = Histogram(
    'memory_operation_duration_seconds',
    'Memory operation duration in seconds',
    ['memory_type', 'operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Workflow metrics
workflow_executions_total = Counter(
    'workflow_executions_total',
    'Total number of workflow executions',
    ['workflow_type', 'status']
)

workflow_duration_seconds = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# Ticket metrics
tickets_processed_total = Counter(
    'tickets_processed_total',
    'Total number of tickets processed',
    ['intent', 'urgency', 'status']
)

ticket_resolution_time_seconds = Histogram(
    'ticket_resolution_time_seconds',
    'Ticket resolution time in seconds',
    ['intent', 'urgency'],
    buckets=[60, 300, 900, 1800, 3600, 7200, 14400]  # 1m, 5m, 15m, 30m, 1h, 2h, 4h
)

# System health
system_health = Gauge(
    'system_health_status',
    'Overall system health status',
    ['component']
)

active_sessions = Gauge(
    'active_sessions_total',
    'Number of active user sessions'
)

# Version info
system_info = Info(
    'ai_agent_system',
    'AI Agent System version and build info'
)

# Set system info (call once at startup)
system_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'build_date': '2026-02-01'
})


# Decorator for automatic agent metrics
def track_agent_execution(agent_type: str):
    """
    Decorator to automatically track agent execution metrics.
    
    Usage:
        @track_agent_execution("intent_agent")
        def process(self, query: str):
            # agent logic
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failure"
                error_type = type(e).__name__
                agent_errors_total.labels(
                    agent_type=agent_type,
                    error_type=error_type
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                agent_executions_total.labels(
                    agent_type=agent_type,
                    status=status
                ).inc()
                agent_duration_seconds.labels(
                    agent_type=agent_type
                ).observe(duration)
        
        return wrapper
    return decorator


# Context manager for tracking operations
class MetricsContext:
    """Context manager for tracking operation metrics."""
    
    def __init__(self, metric_type: str, labels: dict):
        self.metric_type = metric_type
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if self.metric_type == "memory":
            memory_operations_total.labels(**self.labels).inc()
            memory_operation_duration_seconds.labels(**self.labels).observe(duration)
        elif self.metric_type == "openai":
            openai_api_calls_total.labels(**self.labels).inc()
            openai_api_duration_seconds.labels(**self.labels).observe(duration)
        elif self.metric_type == "workflow":
            status = "success" if exc_type is None else "failure"
            workflow_executions_total.labels(
                workflow_type=self.labels.get('workflow_type', 'unknown'),
                status=status
            ).inc()
            workflow_duration_seconds.labels(
                workflow_type=self.labels.get('workflow_type', 'unknown')
            ).observe(duration)


# Helper functions
def track_openai_call(model: str, operation: str, tokens: dict = None):
    """
    Track OpenAI API call.
    
    Args:
        model: Model name (e.g., 'gpt-4', 'gpt-4o-mini')
        operation: Operation type ('chat', 'embedding')
        tokens: Dict with 'prompt' and 'completion' token counts
    """
    openai_api_calls_total.labels(model=model, operation=operation).inc()
    
    if tokens:
        if 'prompt' in tokens:
            openai_api_tokens_total.labels(
                model=model,
                token_type='prompt'
            ).inc(tokens['prompt'])
        if 'completion' in tokens:
            openai_api_tokens_total.labels(
                model=model,
                token_type='completion'
            ).inc(tokens['completion'])


def track_ticket_processed(intent: str, urgency: str, status: str, resolution_time: float):
    """
    Track ticket processing.
    
    Args:
        intent: Ticket intent (incident, service_request, question, etc.)
        urgency: Urgency level (critical, high, medium, low)
        status: Processing status (resolved, escalated, failed)
        resolution_time: Time to resolve in seconds
    """
    tickets_processed_total.labels(
        intent=intent,
        urgency=urgency,
        status=status
    ).inc()
    
    ticket_resolution_time_seconds.labels(
        intent=intent,
        urgency=urgency
    ).observe(resolution_time)


def update_system_health(component: str, status: float):
    """
    Update system health gauge.
    
    Args:
        component: Component name (database, api, agents, etc.)
        status: 1.0 = healthy, 0.0 = unhealthy, 0.5 = degraded
    """
    system_health.labels(component=component).set(status)


def update_active_sessions(count: int):
    """Update active session count."""
    active_sessions.set(count)


# Example usage in agents:
"""
from utils.metrics import track_agent_execution, MetricsContext, track_openai_call

class IntentAgent:
    @track_agent_execution("intent_agent")
    def classify(self, query: str):
        # Track OpenAI call
        with MetricsContext("openai", {"model": "gpt-4o-mini", "operation": "chat"}):
            response = openai.chat.completions.create(...)
        
        track_openai_call(
            model="gpt-4o-mini",
            operation="chat",
            tokens={"prompt": 100, "completion": 50}
        )
        
        return result
"""
