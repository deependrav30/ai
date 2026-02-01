"""
Unit tests for SLAPredictorAgent

Tests SLA calculations, risk assessment, and recommendations.
"""

import pytest
from datetime import datetime, timedelta
from agents.sla_predictor_agent import SLAPredictorAgent


class TestSLAPredictorAgent:
    """Test suite for SLAPredictorAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create SLAPredictorAgent instance"""
        return SLAPredictorAgent()
    
    def test_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.name == "SLAPredictorAgent"
        assert agent.SLA_WINDOWS is not None
        assert agent.COMPLEXITY_MULTIPLIERS is not None
        assert len(agent.SLA_WINDOWS) == 4  # 4 urgency levels
        assert len(agent.COMPLEXITY_MULTIPLIERS) == 4  # 4 complexity levels
    
    def test_sla_windows_critical(self, agent):
        """Test SLA windows for critical urgency"""
        sla = agent.SLA_WINDOWS['critical']
        assert sla['response_time'] == 1
        assert sla['resolution_time'] == 4
    
    def test_sla_windows_high(self, agent):
        """Test SLA windows for high urgency"""
        sla = agent.SLA_WINDOWS['high']
        assert sla['response_time'] == 2
        assert sla['resolution_time'] == 8
    
    def test_sla_windows_medium(self, agent):
        """Test SLA windows for medium urgency"""
        sla = agent.SLA_WINDOWS['medium']
        assert sla['response_time'] == 4
        assert sla['resolution_time'] == 24
    
    def test_sla_windows_low(self, agent):
        """Test SLA windows for low urgency"""
        sla = agent.SLA_WINDOWS['low']
        assert sla['response_time'] == 8
        assert sla['resolution_time'] == 48
    
    def test_complexity_multipliers(self, agent):
        """Test complexity multipliers"""
        assert agent.COMPLEXITY_MULTIPLIERS['simple'] == 0.5
        assert agent.COMPLEXITY_MULTIPLIERS['moderate'] == 1.0
        assert agent.COMPLEXITY_MULTIPLIERS['complex'] == 1.5
        assert agent.COMPLEXITY_MULTIPLIERS['very_complex'] == 2.0
    
    @pytest.mark.asyncio
    async def test_process_critical_just_created(self, agent):
        """Test SLA calculation for newly created critical ticket"""
        result = await agent.process({
            'urgency': 'critical',
            'complexity': 'moderate',
            'created_at': datetime.now()
        })
        
        assert result['urgency'] == 'critical'
        assert result['sla_config']['response_time_hours'] == 1
        assert result['sla_config']['base_resolution_time_hours'] == 4
        assert result['time_remaining']['response_hours'] > 0
        assert result['breach_risk']['level'] in ['safe', 'warning']
    
    @pytest.mark.asyncio
    async def test_process_with_complexity_simple(self, agent):
        """Test SLA with simple complexity (0.5x multiplier)"""
        result = await agent.process({
            'urgency': 'high',
            'complexity': 'simple',
            'created_at': datetime.now()
        })
        
        # Simple should reduce time by 50%
        assert result['sla_config']['adjusted_resolution_time_hours'] == 4.0  # 8 * 0.5
    
    @pytest.mark.asyncio
    async def test_process_with_complexity_very_complex(self, agent):
        """Test SLA with very complex (2.0x multiplier)"""
        result = await agent.process({
            'urgency': 'high',
            'complexity': 'very_complex',
            'created_at': datetime.now()
        })
        
        # Very complex should double time
        assert result['sla_config']['adjusted_resolution_time_hours'] == 16.0  # 8 * 2.0
    
    @pytest.mark.asyncio
    async def test_process_with_historical_data(self, agent):
        """Test SLA with historical ticket data"""
        similar_tickets = [
            {'resolution_time_hours': 18.0},
            {'resolution_time_hours': 22.0},
            {'resolution_time_hours': 20.0}
        ]
        
        result = await agent.process({
            'urgency': 'medium',
            'complexity': 'moderate',
            'created_at': datetime.now(),
            'similar_tickets': similar_tickets
        })
        
        # Should blend historical (20h avg) with baseline (24h): 70% * 20 + 30% * 24 = 21.2h
        adjusted_time = result['sla_config']['adjusted_resolution_time_hours']
        assert 20.0 <= adjusted_time <= 22.0  # Should be close to 21.2
    
    @pytest.mark.asyncio
    async def test_process_approaching_deadline(self, agent):
        """Test SLA for ticket approaching deadline"""
        # Create ticket 55 minutes ago (5 mins before 1h response deadline)
        result = await agent.process({
            'urgency': 'critical',
            'complexity': 'moderate',
            'created_at': datetime.now() - timedelta(minutes=55)
        })
        
        assert result['time_remaining']['response_hours'] < 0.2  # Less than 12 minutes
        assert result['breach_risk']['level'] in ['critical', 'danger']
    
    @pytest.mark.asyncio
    async def test_process_breached_sla(self, agent):
        """Test SLA for already breached ticket"""
        # Create ticket 50 hours ago (past 48h low urgency resolution)
        result = await agent.process({
            'urgency': 'low',
            'complexity': 'moderate',
            'created_at': datetime.now() - timedelta(hours=50)
        })
        
        assert result['time_remaining']['resolution_hours'] < 0
        assert result['time_remaining']['resolution_status'] == 'breached'
        assert result['breach_risk']['level'] == 'critical'
    
    def test_calculate_breach_risk_safe(self, agent):
        """Test breach risk calculation for safe status"""
        risk = agent._calculate_breach_risk(
            time_remaining_response=2.0,
            time_remaining_resolution=8.0,
            urgency='high'
        )
        
        assert risk['level'] == 'safe'
        assert risk['color'] == 'green'
    
    def test_calculate_breach_risk_warning(self, agent):
        """Test breach risk calculation for warning status"""
        risk = agent._calculate_breach_risk(
            time_remaining_response=2.0,
            time_remaining_resolution=1.5,  # Less than 2h for critical/high
            urgency='critical'
        )
        
        assert risk['level'] == 'warning'
        assert risk['color'] == 'yellow'
    
    def test_calculate_breach_risk_danger(self, agent):
        """Test breach risk calculation for danger status"""
        risk = agent._calculate_breach_risk(
            time_remaining_response=0.8,  # Less than 1h for medium/low
            time_remaining_resolution=5.0,
            urgency='medium'
        )
        
        assert risk['level'] == 'danger'
        assert risk['color'] == 'orange'
    
    def test_calculate_breach_risk_critical_breached(self, agent):
        """Test breach risk for already breached SLA"""
        risk = agent._calculate_breach_risk(
            time_remaining_response=-1.0,  # Already breached
            time_remaining_resolution=2.0,
            urgency='high'
        )
        
        assert risk['level'] == 'critical'
        assert risk['color'] == 'red'
    
    def test_generate_recommendations_critical(self, agent):
        """Test recommendations for critical risk"""
        breach_risk = {'level': 'critical', 'color': 'red', 'message': 'Breached!'}
        
        recommendations = agent._generate_recommendations(
            breach_risk=breach_risk,
            time_remaining_response=0.1,
            time_remaining_resolution=1.0,
            urgency='critical',
            complexity='moderate'
        )
        
        assert len(recommendations) > 0
        assert any('URGENT' in rec or '🚨' in rec for rec in recommendations)
    
    def test_generate_recommendations_safe(self, agent):
        """Test recommendations for safe status"""
        breach_risk = {'level': 'safe', 'color': 'green', 'message': 'On track'}
        
        recommendations = agent._generate_recommendations(
            breach_risk=breach_risk,
            time_remaining_response=2.0,
            time_remaining_resolution=8.0,
            urgency='medium',
            complexity='moderate'
        )
        
        assert len(recommendations) > 0
        assert any('On track' in rec or '✅' in rec for rec in recommendations)
    
    def test_calculate_avg_resolution_time(self, agent):
        """Test average resolution time calculation"""
        similar_tickets = [
            {'resolution_time_hours': 10.0},
            {'resolution_time_hours': 15.0},
            {'resolution_time_hours': 20.0}
        ]
        
        avg = agent._calculate_avg_resolution_time(similar_tickets)
        
        assert avg == 15.0
    
    def test_calculate_avg_resolution_time_from_timestamps(self, agent):
        """Test average resolution time from timestamps"""
        base_time = datetime.now()
        similar_tickets = [
            {
                'created_at': base_time.isoformat(),
                'resolved_at': (base_time + timedelta(hours=10)).isoformat()
            },
            {
                'created_at': base_time.isoformat(),
                'resolved_at': (base_time + timedelta(hours=20)).isoformat()
            }
        ]
        
        avg = agent._calculate_avg_resolution_time(similar_tickets)
        
        assert 14.5 <= avg <= 15.5  # Should be around 15
    
    def test_format_sla_summary(self, agent, sla_prediction_result):
        """Test SLA summary formatting"""
        summary = agent.format_sla_summary(sla_prediction_result)
        
        assert 'SLA Status:' in summary
        assert 'Risk Level:' in summary
        assert 'Time Remaining:' in summary
        assert 'Recommendations:' in summary
