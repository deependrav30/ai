"""
Integration tests for AgentWorkflow

Tests the complete workflow with multiple agents working together.
"""

import pytest
from agents.workflow import AgentWorkflow
from unittest.mock import AsyncMock, patch


class TestAgentWorkflow:
    """Test suite for AgentWorkflow integration"""
    
    @pytest.fixture
    def workflow(self):
        """Create AgentWorkflow instance"""
        return AgentWorkflow()
    
    def test_initialization(self, workflow):
        """Test workflow initializes all agents"""
        assert len(workflow.agents) == 8
        assert 'intent' in workflow.agents
        assert 'duplicate_detector' in workflow.agents
        assert 'sla_predictor' in workflow.agents
        assert workflow.orchestrator is not None
    
    @pytest.mark.asyncio
    async def test_process_ticket_basic(self, workflow):
        """Test basic ticket processing"""
        result = await workflow.process_ticket(
            user_input="Payment API is returning 500 errors",
            ticket_id="TEST-001"
        )
        
        assert 'ticket_id' in result
        assert result['ticket_id'] == "TEST-001"
        assert 'user_input' in result
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_process_ticket_classification(self, workflow):
        """Test ticket gets classified"""
        result = await workflow.process_ticket(
            user_input="Production database is down, all users affected!"
        )
        
        # Should have classification
        assert 'intent' in result
        assert 'urgency' in result
        assert 'category' in result
    
    @pytest.mark.asyncio
    async def test_process_ticket_duplicate_detection(self, workflow):
        """Test duplicate detection runs"""
        result = await workflow.process_ticket(
            user_input="Payment API error 500"
        )
        
        # Should have duplicate detection results
        assert 'duplicates' in result or 'duplicate_count' in result
    
    @pytest.mark.asyncio
    async def test_process_ticket_sla_prediction(self, workflow):
        """Test SLA prediction runs"""
        result = await workflow.process_ticket(
            user_input="Critical: Production server down!"
        )
        
        # Should have SLA prediction
        assert 'sla' in result or 'sla_risk' in result
    
    @pytest.mark.asyncio
    async def test_enhance_ticket_processing(self, workflow):
        """Test ticket enhancement with duplicate and SLA"""
        state = {
            'ticket_id': 'TEST-001',
            'user_input': 'Test issue',
            'intent': 'incident',
            'urgency': 'high',
            'category': 'technical',
            'timestamp': '2026-02-01T12:00:00'
        }
        
        await workflow._enhance_ticket_processing(state)
        
        # Should have both duplicate and SLA data
        assert 'duplicates' in state
        assert 'sla' in state
        assert 'sla_risk' in state
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow):
        """Test workflow handles errors gracefully"""
        # Test with empty input
        result = await workflow.process_ticket("")
        
        # Should not crash, should have response
        assert 'response' in result or 'error' in result
    
    @pytest.mark.asyncio
    async def test_workflow_generates_ticket_id(self, workflow):
        """Test workflow generates ticket ID if not provided"""
        result = await workflow.process_ticket("Test issue")
        
        assert 'ticket_id' in result
        assert result['ticket_id'].startswith('TICKET-')
    
    @pytest.mark.asyncio
    async def test_workflow_metrics(self, workflow):
        """Test workflow tracks metrics"""
        # Process a ticket
        await workflow.process_ticket("Test issue")
        
        # Get metrics
        metrics = workflow.get_metrics()
        
        assert metrics is not None
        assert 'intent' in metrics
        assert 'duplicate_detector' in metrics
        assert 'sla_predictor' in metrics
    
    @pytest.mark.asyncio
    async def test_multiple_tickets_sequential(self, workflow):
        """Test processing multiple tickets sequentially"""
        result1 = await workflow.process_ticket("First issue", "TICKET-001")
        result2 = await workflow.process_ticket("Second issue", "TICKET-002")
        
        assert result1['ticket_id'] == "TICKET-001"
        assert result2['ticket_id'] == "TICKET-002"
        assert result1['ticket_id'] != result2['ticket_id']
    
    @pytest.mark.asyncio
    async def test_workflow_confidence_tracking(self, workflow):
        """Test workflow tracks confidence scores"""
        result = await workflow.process_ticket("Production down!")
        
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1


class TestWorkflowIntegrationScenarios:
    """Real-world scenario tests"""
    
    @pytest.fixture
    def workflow(self):
        """Create workflow instance"""
        return AgentWorkflow()
    
    @pytest.mark.asyncio
    async def test_critical_incident_flow(self, workflow):
        """Test complete flow for critical incident"""
        result = await workflow.process_ticket(
            "URGENT: Production database is completely down, all users cannot access the system!"
        )
        
        # Should be classified as critical
        assert result.get('urgency') in ['critical', 'high']
        
        # Should have SLA with short deadlines
        if 'sla_response_hours' in result:
            assert result['sla_response_hours'] <= 2  # Critical/high should be 1-2h
    
    @pytest.mark.asyncio
    async def test_simple_question_flow(self, workflow):
        """Test complete flow for simple question"""
        result = await workflow.process_ticket(
            "How do I reset my password?"
        )
        
        # Should be classified as question with low urgency
        assert result.get('intent') == 'question'
        assert result.get('urgency') in ['low', 'medium']
    
    @pytest.mark.asyncio
    async def test_service_request_flow(self, workflow):
        """Test complete flow for service request"""
        result = await workflow.process_ticket(
            "Please create a new user account for our new team member John Doe"
        )
        
        # Should be classified as service request
        assert result.get('intent') == 'service_request'
        assert result.get('urgency') in ['low', 'medium']
    
    @pytest.mark.asyncio
    async def test_duplicate_ticket_scenario(self, workflow):
        """Test scenario where duplicate tickets exist"""
        # First, add a ticket to history (would normally be done after resolution)
        # For now, just process and check duplicate detection runs
        result = await workflow.process_ticket(
            "Payment API showing 500 errors, customers cannot checkout"
        )
        
        # Should have checked for duplicates
        assert 'duplicate_count' in result
    
    @pytest.mark.asyncio
    async def test_sla_at_risk_scenario(self, workflow):
        """Test scenario with SLA at risk"""
        result = await workflow.process_ticket(
            "Production API is slow, need urgent help!"
        )
        
        # Should have SLA risk assessment
        assert 'sla_risk' in result
        assert result['sla_risk'] in ['safe', 'warning', 'danger', 'critical']
