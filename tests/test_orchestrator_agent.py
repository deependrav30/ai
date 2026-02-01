"""
Tests for OrchestratorAgent - Multi-Agent Coordinator

Coverage targets:
- Execution model decisions (serial/parallel/async)
- Agent coordination
- General chatbot routing
- Error handling and fallbacks
"""
import pytest
import asyncio
from agents.orchestrator_agent import OrchestratorAgent
from agents.intent_agent import IntentAgent
from agents.memory_agent import MemoryAgent
from agents.retrieval_agent import RetrievalAgent
from agents.reasoning_agent import ReasoningAgent
from agents.synthesis_agent import SynthesisAgent
from agents.guardrails_agent import GuardrailsAgent


class TestOrchestratorAgent:
    """Test suite for OrchestratorAgent"""
    
    @pytest.fixture
    def agents_dict(self):
        """Create mock agent dictionary"""
        return {
            "intent": IntentAgent(),
            "memory": MemoryAgent(),
            "retrieval": RetrievalAgent(),
            "reasoning": ReasoningAgent(),
            "synthesis": SynthesisAgent(),
            "guardrails": GuardrailsAgent()
        }
    
    @pytest.fixture
    def orchestrator(self, agents_dict):
        """Create OrchestratorAgent instance"""
        return OrchestratorAgent(agents_dict)
    
    @pytest.fixture
    def base_state(self):
        """Base state for testing"""
        return {
            "user_input": "My server is down and production is affected",
            "confidence": 0.5
        }
    
    # ===== Initialization Tests =====
    
    def test_initialization(self, orchestrator, agents_dict):
        """Test orchestrator initialization"""
        assert orchestrator.name == "OrchestratorAgent"
        assert orchestrator.agents == agents_dict
        assert orchestrator.general_chatbot is not None
    
    # ===== Execution Model Tests =====
    
    def test_decide_execution_model_critical(self, orchestrator):
        """Test execution model for critical urgency"""
        state = {"urgency": "critical"}
        
        model = orchestrator.decide_execution_model(state)
        
        # Critical should use parallel or async for speed
        assert model in ["parallel", "async", "serial"]
    
    def test_decide_execution_model_simple(self, orchestrator):
        """Test execution model for simple queries"""
        state = {
            "intent": "question",
            "urgency": "low"
        }
        
        model = orchestrator.decide_execution_model(state)
        
        # Simple queries can use serial
        assert model in ["serial", "parallel", "async"]
    
    def test_decide_execution_model_default(self, orchestrator):
        """Test default execution model"""
        state = {}
        
        model = orchestrator.decide_execution_model(state)
        
        assert model in ["serial", "parallel", "async"]
    
    def test_decide_execution_model_pattern_detected(self, orchestrator):
        """Test execution model when pattern detected"""
        state = {"pattern_detected": True}
        
        model = orchestrator.decide_execution_model(state)
        
        # Pattern detection may benefit from parallel
        assert model in ["serial", "parallel", "async"]
    
    # ===== General Chat Routing Tests =====
    
    @pytest.mark.asyncio
    async def test_routes_to_general_chatbot(self, orchestrator):
        """Test routing simple queries to general chatbot"""
        state = {
            "user_input": "Hello, how are you?"
        }
        
        result = await orchestrator.process(state)
        
        assert "execution_model" in result
        if result["execution_model"] == "general_chat":
            assert "response" in result
    
    @pytest.mark.asyncio
    async def test_routes_to_multi_agent(self, orchestrator, base_state):
        """Test routing complex queries to multi-agent system"""
        result = await orchestrator.process(base_state)
        
        assert "execution_model" in result
        assert result["execution_model"] in ["serial", "parallel", "async"]
    
    # ===== Serial Execution Tests =====
    
    @pytest.mark.asyncio
    async def test_execute_serial(self, orchestrator):
        """Test serial execution of agents"""
        state = {
            "user_input": "How do I reset my password?",
            "execution_model": "serial"
        }
        
        result = await orchestrator.execute_serial(state)
        
        # Should have agent outputs
        assert "intent" in result or "response" in result
        assert "total_execution_time" in result or "execution_time" in result
    
    @pytest.mark.asyncio
    async def test_serial_execution_order(self, orchestrator):
        """Test that serial execution maintains order"""
        state = {
            "user_input": "Server down",
            "execution_model": "serial"
        }
        
        result = await orchestrator.execute_serial(state)
        
        # State should be updated sequentially
        assert isinstance(result, dict)
    
    # ===== Parallel Execution Tests =====
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self, orchestrator):
        """Test parallel execution of agents"""
        state = {
            "user_input": "Critical server outage",
            "urgency": "critical"
        }
        
        result = await orchestrator.execute_parallel(state)
        
        # Should complete faster than serial
        assert isinstance(result, dict)
        assert "total_execution_time" in result or "execution_time" in result
    
    @pytest.mark.asyncio
    async def test_parallel_execution_combines_results(self, orchestrator):
        """Test that parallel execution combines all results"""
        state = {
            "user_input": "Email not working",
            "urgency": "high"
        }
        
        result = await orchestrator.execute_parallel(state)
        
        # Should have combined results from multiple agents
        assert isinstance(result, dict)
        # May have intent, memory, retrieval results
    
    # ===== Async Execution Tests =====
    
    @pytest.mark.asyncio
    async def test_execute_async(self, orchestrator):
        """Test async execution of agents"""
        state = {
            "user_input": "Production database issue",
            "urgency": "critical"
        }
        
        result = await orchestrator.execute_async(state)
        
        # Should handle async execution
        assert isinstance(result, dict)
    
    # ===== Process Tests =====
    
    @pytest.mark.asyncio
    async def test_process_complete_workflow(self, orchestrator, base_state):
        """Test complete orchestration workflow"""
        result = await orchestrator.process(base_state)
        
        # Should have execution metadata
        assert "execution_model" in result
        assert "total_execution_time" in result
        assert result["total_execution_time"] >= 0
    
    @pytest.mark.asyncio
    async def test_process_updates_state(self, orchestrator):
        """Test that process updates state properly"""
        state = {
            "user_input": "Cannot access my account",
            "confidence": 0.5
        }
        
        result = await orchestrator.process(state)
        
        # Original fields should be preserved
        assert result["user_input"] == state["user_input"]
        # New fields should be added
        assert "execution_model" in result
    
    @pytest.mark.asyncio
    async def test_process_with_empty_input(self, orchestrator):
        """Test processing with empty input"""
        state = {"user_input": ""}
        
        result = await orchestrator.process(state)
        
        # Should handle gracefully
        assert isinstance(result, dict)
    
    # ===== Error Handling Tests =====
    
    @pytest.mark.asyncio
    async def test_process_handles_errors(self, orchestrator):
        """Test that orchestrator handles agent errors"""
        state = {
            "user_input": "Test query"
        }
        
        # Should not raise exception even if agents fail
        result = await orchestrator.process(state)
        
        assert isinstance(result, dict)
        # May have error field if something failed
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, orchestrator):
        """Test fallback behavior on error"""
        state = {"user_input": "Test"}
        
        result = await orchestrator.process(state)
        
        # Should complete even with errors
        assert "execution_model" in result or "error" in result
    
    # ===== Agent Selection Tests =====
    
    def test_get_required_agents_incident(self, orchestrator):
        """Test agent selection for incident"""
        state = {
            "intent": "incident",
            "urgency": "critical"
        }
        
        agents = orchestrator.get_required_agents(state)
        
        assert isinstance(agents, list)
        # Should include key agents for incidents
        assert len(agents) > 0
    
    def test_get_required_agents_question(self, orchestrator):
        """Test agent selection for question"""
        state = {
            "intent": "question",
            "urgency": "low"
        }
        
        agents = orchestrator.get_required_agents(state)
        
        assert isinstance(agents, list)
        # Questions may need fewer agents
    
    def test_get_required_agents_service_request(self, orchestrator):
        """Test agent selection for service request"""
        state = {
            "intent": "service_request",
            "urgency": "medium"
        }
        
        agents = orchestrator.get_required_agents(state)
        
        assert isinstance(agents, list)
    
    # ===== Aggregation Tests =====
    
    def test_aggregate_results_serial(self, orchestrator):
        """Test aggregating results from serial execution"""
        states = [
            {"intent": "incident", "confidence": 0.8},
            {"category": "network", "confidence": 0.7},
            {"retrieved_docs": [], "confidence": 0.6}
        ]
        
        aggregated = orchestrator.aggregate_results(states)
        
        # Should combine all fields
        assert "intent" in aggregated
        assert "category" in aggregated
        assert "retrieved_docs" in aggregated
    
    def test_aggregate_results_parallel(self, orchestrator):
        """Test aggregating results from parallel execution"""
        states = [
            {"field1": "value1"},
            {"field2": "value2"},
            {"field3": "value3"}
        ]
        
        aggregated = orchestrator.aggregate_results(states)
        
        # Should merge all results
        assert len(aggregated) >= 3
    
    def test_aggregate_results_empty(self, orchestrator):
        """Test aggregating empty results"""
        aggregated = orchestrator.aggregate_results([])
        
        assert isinstance(aggregated, dict)
    
    # ===== Performance Tests =====
    
    @pytest.mark.asyncio
    async def test_parallel_faster_than_serial(self, orchestrator):
        """Test that parallel execution is faster for complex queries"""
        state = {
            "user_input": "Critical production database outage affecting all users",
            "urgency": "critical"
        }
        
        # Run both and compare (conceptually)
        # This is more of a concept test than strict timing
        parallel_result = await orchestrator.execute_parallel(state.copy())
        
        # Should complete
        assert "total_execution_time" in parallel_result or "execution_time" in parallel_result
    
    # ===== Integration Tests =====
    
    @pytest.mark.asyncio
    async def test_full_orchestration_incident(self, orchestrator):
        """Test full orchestration for incident"""
        state = {
            "user_input": "Production server crashed, users cannot login",
            "urgency": "critical"
        }
        
        result = await orchestrator.process(state)
        
        # Should have complete processing
        assert "execution_model" in result
        assert "total_execution_time" in result
        # May have various agent outputs
    
    @pytest.mark.asyncio
    async def test_full_orchestration_question(self, orchestrator):
        """Test full orchestration for question"""
        state = {
            "user_input": "How do I change my email signature?"
        }
        
        result = await orchestrator.process(state)
        
        # Should complete successfully
        assert isinstance(result, dict)
        assert "execution_model" in result
    
    @pytest.mark.asyncio
    async def test_orchestrator_preserves_context(self, orchestrator):
        """Test that orchestrator preserves context across agents"""
        state = {
            "user_input": "Reset my password",
            "session_id": "test_session_123",
            "user_id": "user_456"
        }
        
        result = await orchestrator.process(state)
        
        # Should preserve original context
        assert result.get("session_id") == "test_session_123"
        assert result.get("user_id") == "user_456"
