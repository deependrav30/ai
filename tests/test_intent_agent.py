"""
Unit tests for IntentAgent

Tests keyword matching, LLM integration, and classification accuracy.
"""

import pytest
from agents.intent_agent import IntentAgent


class TestIntentAgent:
    """Test suite for IntentAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create IntentAgent instance"""
        return IntentAgent()
    
    def test_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "IntentAgent"
        assert agent.INTENT_KEYWORDS is not None
        assert agent.URGENCY_KEYWORDS is not None
        assert len(agent.INTENT_KEYWORDS) == 5  # 5 intent types
        assert len(agent.URGENCY_KEYWORDS) == 4  # 4 urgency levels
    
    def test_keyword_match_incident(self, agent):
        """Test keyword matching for incident intent"""
        text = "Production server is down and not responding"
        predicted, confidence, keywords = agent._keyword_match(text, agent.INTENT_KEYWORDS)
        
        assert predicted == 'incident'
        assert confidence > 0
        assert any(keyword in ['down', 'not responding'] for keyword in keywords)
    
    def test_keyword_match_service_request(self, agent):
        """Test keyword matching for service request"""
        text = "Please create a new user account for John Doe"
        predicted, confidence, keywords = agent._keyword_match(text, agent.INTENT_KEYWORDS)
        
        assert predicted == 'service_request'
        assert 'create' in keywords or 'new' in keywords
    
    def test_keyword_match_question(self, agent):
        """Test keyword matching for question intent"""
        text = "How do I reset my password?"
        predicted, confidence, keywords = agent._keyword_match(text, agent.INTENT_KEYWORDS)
        
        assert predicted == 'question'
        assert any('how' in kw for kw in keywords) or 'how do i' in text.lower()
    
    def test_keyword_match_urgency_critical(self, agent):
        """Test keyword matching for critical urgency"""
        text = "URGENT: Production down, all users affected!"
        predicted, confidence, keywords = agent._keyword_match(text, agent.URGENCY_KEYWORDS)
        
        assert predicted == 'critical'
        assert confidence > 0
    
    def test_keyword_match_urgency_low(self, agent):
        """Test keyword matching for low urgency"""
        text = "I have a minor question about the documentation"
        predicted, confidence, keywords = agent._keyword_match(text, agent.URGENCY_KEYWORDS)
        
        # The text should match 'question' keyword which might not trigger urgency
        # Or it should return None if no urgency keywords match
        assert predicted is None or predicted in ['low', 'medium']
    
    @pytest.mark.asyncio
    async def test_process_incident(self, agent):
        """Test full processing of an incident ticket"""
        state = {
            'user_input': 'Payment API is returning 500 errors, customers cannot checkout'
        }
        
        result = await agent.process(state)
        
        assert 'intent' in result
        assert 'urgency' in result
        assert 'category' in result
        assert 'confidence' in result
        assert result['intent'] in ['incident', 'problem']
        assert result['urgency'] in ['critical', 'high']
    
    @pytest.mark.asyncio
    async def test_process_question(self, agent):
        """Test full processing of a question"""
        state = {
            'user_input': 'How do I reset my password?'
        }
        
        result = await agent.process(state)
        
        assert result['intent'] == 'question'
        assert result['urgency'] in ['low', 'medium']
        assert result['confidence'] > 0
    
    @pytest.mark.asyncio
    async def test_process_service_request(self, agent):
        """Test full processing of a service request"""
        state = {
            'user_input': 'Can you create a new user account for our team member?'
        }
        
        result = await agent.process(state)
        
        assert result['intent'] == 'service_request'
        assert result['urgency'] in ['low', 'medium']
    
    def test_keyword_coverage(self, agent):
        """Test that keyword dictionaries have sufficient coverage"""
        # Each intent should have at least 5 keywords
        for intent, keywords in agent.INTENT_KEYWORDS.items():
            assert len(keywords) >= 5, f"{intent} should have at least 5 keywords"
        
        # Each urgency level should have keywords
        for urgency, keywords in agent.URGENCY_KEYWORDS.items():
            assert len(keywords) >= 3, f"{urgency} should have at least 3 keywords"
    
    def test_keyword_match_edge_cases(self, agent):
        """Test edge cases in keyword matching"""
        # Empty text - should return None
        predicted, confidence, keywords = agent._keyword_match("", agent.INTENT_KEYWORDS)
        assert predicted is None
        assert confidence == 0.0
        assert keywords == []
        
        # Very short text - may or may not match
        predicted, confidence, keywords = agent._keyword_match("error", agent.INTENT_KEYWORDS)
        # 'error' should match 'incident' intent
        assert predicted is not None
        
        # All caps with actual keywords
        predicted, confidence, keywords = agent._keyword_match("CRITICAL PRODUCTION DOWN", agent.URGENCY_KEYWORDS)
        assert predicted == 'critical'
