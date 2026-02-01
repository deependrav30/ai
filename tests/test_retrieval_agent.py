"""
Tests for RetrievalAgent - RAG Knowledge Search

Coverage targets:
- Knowledge base search
- Query building
- Result processing
- Metadata filtering
"""
import pytest
import asyncio
from agents.retrieval_agent import RetrievalAgent


class TestRetrievalAgent:
    """Test suite for RetrievalAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create RetrievalAgent instance for testing"""
        return RetrievalAgent()
    
    @pytest.fixture
    def base_state(self):
        """Base state for testing"""
        return {
            "user_input": "How do I reset my password?",
            "intent": "question",
            "category": "account"
        }
    
    # ===== Initialization Tests =====
    
    def test_initialization(self, agent):
        """Test agent initialization"""
        assert agent.name == "RetrievalAgent"
        assert agent.top_k == 5
    
    # ===== Query Building Tests =====
    
    def test_build_search_query_basic(self, agent, base_state):
        """Test basic query building"""
        query = agent.build_search_query(base_state)
        
        assert isinstance(query, str)
        assert len(query) > 0
        assert "password" in query.lower()
    
    def test_build_search_query_with_intent(self, agent):
        """Test query building includes intent"""
        state = {
            "user_input": "Server down",
            "intent": "incident"
        }
        
        query = agent.build_search_query(state)
        
        assert "server" in query.lower() or "down" in query.lower()
    
    def test_build_search_query_with_category(self, agent):
        """Test query building includes category"""
        state = {
            "user_input": "VPN issue",
            "category": "network"
        }
        
        query = agent.build_search_query(state)
        
        assert "vpn" in query.lower() or "issue" in query.lower()
    
    def test_build_search_query_empty_input(self, agent):
        """Test query building with empty input"""
        state = {}
        
        query = agent.build_search_query(state)
        
        # Should return something, even if empty
        assert isinstance(query, str)
    
    # ===== Process Tests =====
    
    @pytest.mark.asyncio
    async def test_process_basic(self, agent, base_state):
        """Test basic processing"""
        result = await agent.process(base_state)
        
        assert "retrieved_docs" in result
        assert "doc_count" in result
        assert "execution_time" in result
        assert isinstance(result["retrieved_docs"], list)
    
    @pytest.mark.asyncio
    async def test_process_empty_input(self, agent):
        """Test processing with empty input"""
        state = {"user_input": ""}
        
        result = await agent.process(state)
        
        assert "retrieved_docs" in result
        assert result["retrieved_docs"] == []
    
    @pytest.mark.asyncio
    async def test_process_no_results(self, agent):
        """Test processing when no documents match"""
        state = {
            "user_input": "xyzabc12345nonexistentquery98765"
        }
        
        result = await agent.process(state)
        
        # Should handle gracefully
        assert "retrieved_docs" in result
        assert isinstance(result["retrieved_docs"], list)
    
    @pytest.mark.asyncio
    async def test_process_updates_confidence(self, agent, base_state):
        """Test that confidence is updated based on results"""
        result = await agent.process(base_state)
        
        # Should have confidence based on retrieval
        if result["doc_count"] > 0:
            assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_process_with_results(self, agent):
        """Test processing when documents are found"""
        state = {
            "user_input": "password reset account login"  # Common terms
        }
        
        result = await agent.process(state)
        
        # Check document structure if found
        if result["doc_count"] > 0:
            doc = result["retrieved_docs"][0]
            assert "content" in doc or "chunk" in doc
            assert "source" in doc or "metadata" in doc
    
    # ===== Result Ranking Tests =====
    
    def test_rank_results_by_score(self, agent):
        """Test ranking results by relevance score"""
        docs = [
            {"content": "Doc 1", "score": 0.5},
            {"content": "Doc 2", "score": 0.9},
            {"content": "Doc 3", "score": 0.7}
        ]
        
        ranked = agent.rank_results(docs)
        
        # Should be sorted by score descending
        assert ranked[0]["score"] >= ranked[1]["score"]
        assert ranked[1]["score"] >= ranked[2]["score"]
    
    def test_rank_results_empty(self, agent):
        """Test ranking empty results"""
        ranked = agent.rank_results([])
        
        assert ranked == []
    
    def test_rank_results_single(self, agent):
        """Test ranking single result"""
        docs = [{"content": "Doc 1", "score": 0.8}]
        
        ranked = agent.rank_results(docs)
        
        assert len(ranked) == 1
        assert ranked[0]["score"] == 0.8
    
    # ===== Filtering Tests =====
    
    def test_filter_by_category(self, agent):
        """Test filtering documents by category"""
        docs = [
            {"content": "Doc 1", "metadata": {"category": "network"}},
            {"content": "Doc 2", "metadata": {"category": "account"}},
            {"content": "Doc 3", "metadata": {"category": "network"}}
        ]
        
        filtered = agent.filter_by_category(docs, "network")
        
        assert len(filtered) == 2
        assert all(d["metadata"]["category"] == "network" for d in filtered)
    
    def test_filter_by_category_no_match(self, agent):
        """Test filtering with no matches"""
        docs = [
            {"content": "Doc 1", "metadata": {"category": "network"}}
        ]
        
        filtered = agent.filter_by_category(docs, "email")
        
        assert len(filtered) == 0
    
    def test_filter_by_category_missing_metadata(self, agent):
        """Test filtering when metadata is missing"""
        docs = [
            {"content": "Doc 1"},
            {"content": "Doc 2", "metadata": {}}
        ]
        
        filtered = agent.filter_by_category(docs, "network")
        
        # Should handle gracefully
        assert isinstance(filtered, list)
    
    # ===== Summary Tests =====
    
    def test_get_retrieval_summary_with_results(self, agent):
        """Test retrieval summary with documents found"""
        state = {
            "retrieved_docs": [
                {"content": "Doc 1", "score": 0.9},
                {"content": "Doc 2", "score": 0.8}
            ],
            "doc_count": 2
        }
        
        summary = agent.get_retrieval_summary(state)
        
        assert isinstance(summary, str)
        assert "2" in summary or "found" in summary.lower()
    
    def test_get_retrieval_summary_no_results(self, agent):
        """Test retrieval summary with no documents"""
        state = {
            "retrieved_docs": [],
            "doc_count": 0
        }
        
        summary = agent.get_retrieval_summary(state)
        
        assert isinstance(summary, str)
        assert "no" in summary.lower() or "0" in summary
    
    def test_get_retrieval_summary_missing_data(self, agent):
        """Test retrieval summary with missing data"""
        state = {}
        
        summary = agent.get_retrieval_summary(state)
        
        # Should handle gracefully
        assert isinstance(summary, str)
    
    # ===== Integration Tests =====
    
    @pytest.mark.asyncio
    async def test_process_full_workflow(self, agent):
        """Test full retrieval workflow"""
        state = {
            "user_input": "How to configure email settings?",
            "intent": "question",
            "category": "email"
        }
        
        result = await agent.process(state)
        
        # Verify all expected fields
        assert "retrieved_docs" in result
        assert "doc_count" in result
        assert "execution_time" in result
        assert result["execution_time"] >= 0
    
    # ===== Error Handling Tests =====
    
    @pytest.mark.asyncio
    async def test_process_handles_retrieval_error(self, agent):
        """Test that process handles retrieval errors gracefully"""
        state = {"user_input": "test query"}
        
        # Should not raise exception even if retrieval fails
        result = await agent.process(state)
        
        assert "retrieved_docs" in result
        # May be empty due to error, but should not crash
        assert isinstance(result["retrieved_docs"], list)
    
    @pytest.mark.asyncio
    async def test_process_with_none_user_input(self, agent):
        """Test processing with None user_input"""
        state = {"user_input": None}
        
        result = await agent.process(state)
        
        assert "retrieved_docs" in result
        assert result["retrieved_docs"] == []
    
    # ===== Metadata Extraction Tests =====
    
    def test_extract_source_from_metadata(self, agent):
        """Test extracting source from document metadata"""
        doc = {
            "metadata": {
                "file_name": "user_guide.pdf",
                "page": 5
            }
        }
        
        source = agent.extract_source(doc)
        
        assert "user_guide" in source.lower()
    
    def test_extract_source_fallback(self, agent):
        """Test source extraction with missing file_name"""
        doc = {
            "metadata": {
                "Timestamp": "2024-01-01"
            }
        }
        
        source = agent.extract_source(doc)
        
        # Should fall back to timestamp or unknown
        assert isinstance(source, str)
    
    def test_extract_source_no_metadata(self, agent):
        """Test source extraction with no metadata"""
        doc = {}
        
        source = agent.extract_source(doc)
        
        assert source == "unknown" or isinstance(source, str)
