"""
SLA Predictor Agent

Predicts SLA breach risk based on ticket urgency, complexity, and historical data.
Helps prioritize tickets and alert teams about potential SLA violations.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SLAPredictorAgent(BaseAgent):
    """Agent for predicting SLA breach risk and response/resolution times"""
    
    # SLA time windows based on urgency (in hours)
    SLA_WINDOWS = {
        'critical': {
            'response_time': 1,    # 1 hour to respond
            'resolution_time': 4   # 4 hours to resolve
        },
        'high': {
            'response_time': 2,    # 2 hours to respond
            'resolution_time': 8   # 8 hours to resolve (1 business day)
        },
        'medium': {
            'response_time': 4,    # 4 hours to respond
            'resolution_time': 24  # 24 hours to resolve
        },
        'low': {
            'response_time': 8,    # 8 hours to respond
            'resolution_time': 48  # 48 hours to resolve
        }
    }
    
    # Complexity multipliers for resolution time
    COMPLEXITY_MULTIPLIERS = {
        'simple': 0.5,       # -50% time (e.g., password reset)
        'moderate': 1.0,     # Normal time (e.g., configuration issue)
        'complex': 1.5,      # +50% time (e.g., integration problem)
        'very_complex': 2.0  # +100% time (e.g., architectural issue)
    }
    
    # Risk levels
    RISK_LEVELS = {
        'safe': 'green',
        'warning': 'yellow',
        'danger': 'orange',
        'critical': 'red'
    }
    
    def __init__(self):
        super().__init__(name="SLAPredictorAgent")
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict SLA breach risk and timeline
        
        Args:
            context: Contains:
                - urgency: critical/high/medium/low
                - complexity: simple/moderate/complex/very_complex (optional)
                - created_at: ticket creation timestamp (optional, defaults to now)
                - category: ticket category for better estimation (optional)
                - similar_tickets: list of similar past tickets with resolution times (optional)
        
        Returns:
            Dict with SLA prediction including:
                - response_deadline: when first response is due
                - resolution_deadline: when resolution is due
                - time_remaining_response: hours until response deadline
                - time_remaining_resolution: hours until resolution deadline
                - breach_risk_level: safe/warning/danger/critical
                - predicted_resolution_time: estimated hours to resolve
                - recommendations: list of action items
        """
        start_time = datetime.now()
        
        try:
            urgency = context.get('urgency', 'medium').lower()
            complexity = context.get('complexity', 'moderate').lower()
            created_at = context.get('created_at', datetime.now())
            category = context.get('category', 'general')
            similar_tickets = context.get('similar_tickets', [])
            
            # Parse created_at if it's a string
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            logger.info(f"Calculating SLA for urgency={urgency}, complexity={complexity}")
            
            # Get SLA windows for this urgency level
            sla_config = self.SLA_WINDOWS.get(urgency, self.SLA_WINDOWS['medium'])
            
            # Calculate deadlines
            response_deadline = created_at + timedelta(hours=sla_config['response_time'])
            
            # Adjust resolution time based on complexity
            complexity_multiplier = self.COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
            adjusted_resolution_time = sla_config['resolution_time'] * complexity_multiplier
            
            # Further adjust based on historical data if available
            if similar_tickets:
                avg_resolution_time = self._calculate_avg_resolution_time(similar_tickets)
                # Blend SLA baseline with historical average (70% historical, 30% baseline)
                adjusted_resolution_time = (avg_resolution_time * 0.7) + (adjusted_resolution_time * 0.3)
            
            resolution_deadline = created_at + timedelta(hours=adjusted_resolution_time)
            
            # Calculate time remaining
            now = datetime.now()
            time_remaining_response = (response_deadline - now).total_seconds() / 3600
            time_remaining_resolution = (resolution_deadline - now).total_seconds() / 3600
            
            # Determine breach risk
            breach_risk = self._calculate_breach_risk(
                time_remaining_response, 
                time_remaining_resolution,
                urgency
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                breach_risk,
                time_remaining_response,
                time_remaining_resolution,
                urgency,
                complexity
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'urgency': urgency,
                'complexity': complexity,
                'sla_config': {
                    'response_time_hours': sla_config['response_time'],
                    'base_resolution_time_hours': sla_config['resolution_time'],
                    'adjusted_resolution_time_hours': round(adjusted_resolution_time, 1)
                },
                'deadlines': {
                    'response_deadline': response_deadline.isoformat(),
                    'resolution_deadline': resolution_deadline.isoformat()
                },
                'time_remaining': {
                    'response_hours': round(time_remaining_response, 1),
                    'resolution_hours': round(time_remaining_resolution, 1),
                    'response_status': 'breached' if time_remaining_response < 0 else 'active',
                    'resolution_status': 'breached' if time_remaining_resolution < 0 else 'active'
                },
                'breach_risk': breach_risk,
                'predictions': {
                    'estimated_resolution_hours': round(adjusted_resolution_time, 1),
                    'confidence': 'high' if similar_tickets else 'medium'
                },
                'recommendations': recommendations
            }
            
            logger.info(f"SLAPredictorAgent executed in {execution_time:.3f}s - Risk: {breach_risk['level']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in SLAPredictorAgent: {e}")
            raise
    
    def _calculate_avg_resolution_time(self, similar_tickets: list) -> float:
        """Calculate average resolution time from similar past tickets"""
        resolution_times = []
        
        for ticket in similar_tickets:
            if 'resolution_time_hours' in ticket:
                resolution_times.append(ticket['resolution_time_hours'])
            elif 'resolved_at' in ticket and 'created_at' in ticket:
                # Calculate from timestamps
                created = datetime.fromisoformat(ticket['created_at'].replace('Z', '+00:00'))
                resolved = datetime.fromisoformat(ticket['resolved_at'].replace('Z', '+00:00'))
                hours = (resolved - created).total_seconds() / 3600
                resolution_times.append(hours)
        
        if resolution_times:
            return sum(resolution_times) / len(resolution_times)
        
        return 0
    
    def _calculate_breach_risk(
        self, 
        time_remaining_response: float,
        time_remaining_resolution: float,
        urgency: str
    ) -> Dict[str, str]:
        """Calculate breach risk level"""
        
        # Already breached
        if time_remaining_response < 0:
            return {
                'level': 'critical',
                'color': self.RISK_LEVELS['critical'],
                'message': 'Response SLA already breached!'
            }
        
        if time_remaining_resolution < 0:
            return {
                'level': 'critical',
                'color': self.RISK_LEVELS['critical'],
                'message': 'Resolution SLA already breached!'
            }
        
        # Critical/high urgency tickets need more aggressive monitoring
        if urgency in ['critical', 'high']:
            if time_remaining_response < 0.5:  # Less than 30 minutes
                return {
                    'level': 'critical',
                    'color': self.RISK_LEVELS['critical'],
                    'message': 'Response deadline in less than 30 minutes!'
                }
            elif time_remaining_resolution < 1:  # Less than 1 hour
                return {
                    'level': 'danger',
                    'color': self.RISK_LEVELS['danger'],
                    'message': 'Resolution deadline in less than 1 hour!'
                }
            elif time_remaining_resolution < 2:  # Less than 2 hours
                return {
                    'level': 'warning',
                    'color': self.RISK_LEVELS['warning'],
                    'message': 'Resolution deadline approaching (< 2 hours)'
                }
        else:
            # Medium/low urgency tickets
            if time_remaining_response < 1:  # Less than 1 hour
                return {
                    'level': 'danger',
                    'color': self.RISK_LEVELS['danger'],
                    'message': 'Response deadline in less than 1 hour!'
                }
            elif time_remaining_resolution < 4:  # Less than 4 hours
                return {
                    'level': 'warning',
                    'color': self.RISK_LEVELS['warning'],
                    'message': 'Resolution deadline approaching (< 4 hours)'
                }
        
        # All good
        return {
            'level': 'safe',
            'color': self.RISK_LEVELS['safe'],
            'message': 'SLA on track'
        }
    
    def _generate_recommendations(
        self,
        breach_risk: Dict[str, str],
        time_remaining_response: float,
        time_remaining_resolution: float,
        urgency: str,
        complexity: str
    ) -> list:
        """Generate actionable recommendations based on SLA status"""
        recommendations = []
        
        risk_level = breach_risk['level']
        
        if risk_level == 'critical':
            recommendations.append("🚨 URGENT: Immediate action required!")
            recommendations.append("Escalate to senior engineer immediately")
            recommendations.append("Notify customer of delay if resolution is breached")
            recommendations.append("Consider emergency change process")
        
        elif risk_level == 'danger':
            recommendations.append("⚠️ HIGH PRIORITY: Address this ticket now")
            recommendations.append("Assign to available senior team member")
            if complexity in ['complex', 'very_complex']:
                recommendations.append("Consider bringing in specialist for complex issue")
            recommendations.append("Prepare customer communication if needed")
        
        elif risk_level == 'warning':
            recommendations.append("⏰ Monitor closely - deadline approaching")
            recommendations.append("Ensure ticket is actively being worked on")
            if time_remaining_resolution < 6:
                recommendations.append("Update customer on progress")
        
        else:  # safe
            recommendations.append("✅ On track - continue normal workflow")
            if urgency == 'critical':
                recommendations.append("Keep monitoring - critical tickets can escalate quickly")
        
        # Add general recommendations based on complexity
        if complexity in ['complex', 'very_complex']:
            recommendations.append("📋 Document solution steps for knowledge base")
            recommendations.append("Consider pair programming or knowledge transfer")
        
        return recommendations
    
    def format_sla_summary(self, sla_data: Dict[str, Any]) -> str:
        """Format SLA data into human-readable summary"""
        risk = sla_data['breach_risk']
        time_rem = sla_data['time_remaining']
        
        summary = f"""
SLA Status: {risk['message']}
Risk Level: {risk['level'].upper()} ({risk['color']})

Time Remaining:
  • Response: {time_rem['response_hours']:.1f} hours ({time_rem['response_status']})
  • Resolution: {time_rem['resolution_hours']:.1f} hours ({time_rem['resolution_status']})

Predictions:
  • Estimated resolution: {sla_data['predictions']['estimated_resolution_hours']:.1f} hours
  • Confidence: {sla_data['predictions']['confidence']}

Recommendations:
"""
        for rec in sla_data['recommendations']:
            summary += f"  {rec}\n"
        
        return summary.strip()
