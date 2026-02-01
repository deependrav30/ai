"""
Pytest configuration and fixtures for the AI support system

This file sets up shared fixtures and configuration for all tests.
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_ticket():
    """Sample ticket data for testing"""
    return {
        'ticket_id': 'TEST-001',
        'title': 'Payment API returning 500 errors',
        'description': 'Users cannot complete checkout due to payment API errors',
        'status': 'open',
        'priority': 'high',
        'created_at': datetime.now().isoformat()
    }


@pytest.fixture
def sample_tickets():
    """Multiple sample tickets for testing"""
    return [
        {
            'ticket_id': 'TEST-001',
            'title': 'Payment API errors',
            'description': 'Payment processing failing with 500 errors',
            'urgency': 'critical'
        },
        {
            'ticket_id': 'TEST-002',
            'title': 'Password reset not working',
            'description': 'Users cannot reset their passwords',
            'urgency': 'medium'
        },
        {
            'ticket_id': 'TEST-003',
            'title': 'Production database down',
            'description': 'All users affected, database connection timeout',
            'urgency': 'critical'
        }
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        'choices': [{
            'message': {
                'content': '{"intent": "incident", "urgency": "critical", "category": "technical"}'
            }
        }]
    }


@pytest.fixture
def mock_embedding():
    """Mock OpenAI embedding response"""
    return [0.1] * 1536  # OpenAI embeddings are 1536 dimensions


@pytest.fixture
def classification_result():
    """Sample classification result"""
    return {
        'intent': 'incident',
        'urgency': 'critical',
        'category': 'technical',
        'confidence': 0.95
    }


@pytest.fixture
def duplicate_detection_result():
    """Sample duplicate detection result"""
    return {
        'duplicates': {
            'exact_duplicate': [],
            'very_similar': [{
                'ticket_id': 'TICK-1001',
                'similarity': 0.948,
                'metadata': {'title': 'Payment API 500 errors'}
            }],
            'similar': [],
            'related': []
        },
        'total_found': 1
    }


@pytest.fixture
def sla_prediction_result():
    """Sample SLA prediction result"""
    return {
        'urgency': 'critical',
        'sla_config': {
            'response_time_hours': 1,
            'base_resolution_time_hours': 4,
            'adjusted_resolution_time_hours': 4.0
        },
        'deadlines': {
            'response_deadline': datetime.now().isoformat(),
            'resolution_deadline': datetime.now().isoformat()
        },
        'time_remaining': {
            'response_hours': 1.0,
            'resolution_hours': 4.0,
            'response_status': 'active',
            'resolution_status': 'active'
        },
        'breach_risk': {
            'level': 'safe',
            'color': 'green',
            'message': 'SLA on track'
        },
        'predictions': {
            'estimated_resolution_hours': 4.0,
            'confidence': 'medium'
        },
        'recommendations': [
            '✅ On track - continue normal workflow'
        ]
    }
