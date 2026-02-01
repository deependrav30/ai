"""
Unit tests for DuplicateDetectorAgent

Tests embedding generation, similarity search, and duplicate detection.
"""

import pytest
from agents.duplicate_detector_agent import DuplicateDetectorAgent
from unittest.mock import AsyncMock, MagicMock, patch


class TestDuplicateDetectorAgent:
    """Test suite for DuplicateDetectorAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create DuplicateDetectorAgent instance"""
        return DuplicateDetectorAgent()
    
    def test_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "DuplicateDetectorAgent"
        assert agent.THRESHOLDS is not None
        assert agent.THRESHOLDS['exact_duplicate'] == 0.95
        assert agent.THRESHOLDS['very_similar'] == 0.85
        assert agent.THRESHOLDS['similar'] == 0.70
        assert agent.THRESHOLDS['related'] == 0.60
    
    def test_categorize_duplicates_exact(self, agent):
        """Test categorization of exact duplicates"""
        duplicates = [
            {'ticket_id': 'T1', 'similarity': 0.96},
            {'ticket_id': 'T2', 'similarity': 0.97}
        ]
        
        categorized = agent._categorize_duplicates(duplicates)
        
        assert len(categorized['exact_duplicate']) == 2
        assert len(categorized['very_similar']) == 0
        assert len(categorized['similar']) == 0
    
    def test_categorize_duplicates_very_similar(self, agent):
        """Test categorization of very similar tickets"""
        duplicates = [
            {'ticket_id': 'T1', 'similarity': 0.92},
            {'ticket_id': 'T2', 'similarity': 0.88}
        ]
        
        categorized = agent._categorize_duplicates(duplicates)
        
        assert len(categorized['exact_duplicate']) == 0
        assert len(categorized['very_similar']) == 2
        assert len(categorized['similar']) == 0
    
    def test_categorize_duplicates_similar(self, agent):
        """Test categorization of similar tickets"""
        duplicates = [
            {'ticket_id': 'T1', 'similarity': 0.78},
            {'ticket_id': 'T2', 'similarity': 0.72}
        ]
        
        categorized = agent._categorize_duplicates(duplicates)
        
        assert len(categorized['exact_duplicate']) == 0
        assert len(categorized['very_similar']) == 0
        assert len(categorized['similar']) == 2
    
    def test_categorize_duplicates_related(self, agent):
        """Test categorization of related tickets"""
        duplicates = [
            {'ticket_id': 'T1', 'similarity': 0.65},
            {'ticket_id': 'T2', 'similarity': 0.62}
        ]
        
        categorized = agent._categorize_duplicates(duplicates)
        
        assert len(categorized['related']) == 2
    
    def test_categorize_duplicates_mixed(self, agent):
        """Test categorization of mixed similarity levels"""
        duplicates = [
            {'ticket_id': 'T1', 'similarity': 0.96},  # exact
            {'ticket_id': 'T2', 'similarity': 0.90},  # very similar
            {'ticket_id': 'T3', 'similarity': 0.75},  # similar
            {'ticket_id': 'T4', 'similarity': 0.63},  # related
            {'ticket_id': 'T5', 'similarity': 0.50}   # below threshold
        ]
        
        categorized = agent._categorize_duplicates(duplicates)
        
        assert len(categorized['exact_duplicate']) == 1
        assert len(categorized['very_similar']) == 1
        assert len(categorized['similar']) == 1
        assert len(categorized['related']) == 1
    
    def test_get_duplicate_summary_none(self, agent):
        """Test summary when no duplicates found"""
        duplicates = {
            'exact_duplicate': [],
            'very_similar': [],
            'similar': [],
            'related': []
        }
        
        summary = agent.get_duplicate_summary(duplicates)
        
        assert "No duplicates found" in summary
        assert "✅" in summary
    
    def test_get_duplicate_summary_exact(self, agent):
        """Test summary with exact duplicates"""
        duplicates = {
            'exact_duplicate': [{'ticket_id': 'T1'}],
            'very_similar': [],
            'similar': [],
            'related': []
        }
        
        summary = agent.get_duplicate_summary(duplicates)
        
        assert "🔴" in summary or "exact duplicate" in summary.lower()
        assert "1" in summary
    
    def test_get_duplicate_summary_multiple_levels(self, agent):
        """Test summary with multiple similarity levels"""
        duplicates = {
            'exact_duplicate': [{'ticket_id': 'T1'}],
            'very_similar': [{'ticket_id': 'T2'}, {'ticket_id': 'T3'}],
            'similar': [],
            'related': [{'ticket_id': 'T4'}]
        }
        
        summary = agent.get_duplicate_summary(duplicates)
        
        assert "🔴" in summary  # exact
        assert "🟠" in summary  # very similar
        assert "🟢" in summary  # related
    
    @pytest.mark.asyncio
    async def test_process_no_duplicates(self, agent):
        """Test processing when no duplicates exist"""
        with patch.object(agent, '_get_embedding', new_callable=AsyncMock) as mock_embed, \
             patch.object(agent, '_search_similar_tickets', new_callable=AsyncMock) as mock_search:
            
            mock_embed.return_value = [0.1] * 1536
            mock_search.return_value = []
            
            result = await agent.process({
                'ticket_id': 'TEST-001',
                'ticket_title': 'Unique issue',
                'ticket_description': 'This is completely unique'
            })
            
            assert result['total_found'] == 0
            assert result['exact_duplicates'] == 0
    
    @pytest.mark.asyncio
    async def test_process_with_duplicates(self, agent):
        """Test processing when duplicates exist"""
        with patch.object(agent, '_get_embedding', new_callable=AsyncMock) as mock_embed, \
             patch.object(agent, '_search_similar_tickets', new_callable=AsyncMock) as mock_search:
            
            mock_embed.return_value = [0.1] * 1536
            mock_search.return_value = [
                {'ticket_id': 'T1', 'similarity': 0.95, 'metadata': {}}
            ]
            
            result = await agent.process({
                'ticket_id': 'TEST-001',
                'ticket_title': 'Payment error',
                'ticket_description': 'Payment API failing'
            })
            
            assert result['total_found'] == 1
            assert result['exact_duplicates'] >= 0
    
    @pytest.mark.asyncio
    async def test_add_ticket_to_history(self, agent):
        """Test adding ticket to history collection"""
        with patch.object(agent, '_get_embedding', new_callable=AsyncMock) as mock_embed, \
             patch.object(agent.ticket_collection, 'add') as mock_add:
            
            mock_embed.return_value = [0.1] * 1536
            
            await agent.add_ticket_to_history(
                ticket_id='TEST-001',
                ticket_title='Test ticket',
                ticket_description='Test description',
                metadata={'status': 'resolved'}
            )
            
            mock_embed.assert_called_once()
            mock_add.assert_called_once()
