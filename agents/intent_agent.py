"""
Intent & Classification Agent

Uses GPT-4o-mini to classify tickets by:
- Ticket type (incident, service_request, question, problem, change)
- Ticket category (technical, application, security, data)
- Urgency level (low, medium, high, critical)
- Severity impact (single_user, multiple_users, business_critical)
- SLA risk assessment
- Team routing
- Confidence score (0.0 to 1.0)
"""
from typing import Dict, Any
import os
import json
import time
from openai import OpenAI
from .base_agent import BaseAgent, logger


class IntentAgent(BaseAgent):
    """
    Classifies user intent and ticket characteristics using GPT-4o-mini.
    Fast, cost-effective, and accurate for structured classification.
    """
    
    def __init__(self):
        super().__init__("IntentAgent")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Classification prompt
        self.system_prompt = """You are an expert ticket classification system for IT support.

Analyze the user's input and classify it into:

1. **Ticket Type:**
   - incident: System down, error, bug, outage
   - service_request: Access request, provisioning, change request
   - question: How-to, information request, documentation
   - problem: Recurring incident, pattern analysis, root cause investigation
   - change: Deployment, configuration change, upgrade

2. **Ticket Category:**
   - technical: API, database, infrastructure, network, server
   - application: UI, functionality, feature, performance
   - security: Access control, vulnerability, compliance, authentication
   - data: Data loss, corruption, migration, backup

3. **Urgency Level:**
   - low: Non-critical, can wait
   - medium: Important but not blocking
   - high: Blocking work, needs attention soon
   - critical: System down, business impact, immediate attention

4. **Severity Impact:**
   - single_user: Affects one person
   - multiple_users: Affects team or department
   - business_critical: Affects entire organization or revenue

5. **SLA Risk:**
   - Assess if ticket is at risk of breaching SLA based on urgency and impact
   - Return true/false

6. **Team Routing:**
   - Suggest appropriate team: DevOps, Support, Security, Database, Network, Application

7. **Confidence Score:**
   - Based on clarity of input, keyword matches, known patterns
   - Return value between 0.0 (very uncertain) and 1.0 (very certain)

Return response as JSON with this exact structure:
{
  "intent": "incident|service_request|question|problem|change",
  "category": "technical|application|security|data",
  "urgency": "low|medium|high|critical",
  "severity": "single_user|multiple_users|business_critical",
  "sla_risk": true|false,
  "team": "DevOps|Support|Security|Database|Network|Application",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification"
}

Examples:

Input: "The payment API is returning 500 errors and customers can't checkout"
Output: {
  "intent": "incident",
  "category": "technical",
  "urgency": "critical",
  "severity": "business_critical",
  "sla_risk": true,
  "team": "DevOps",
  "confidence": 0.95,
  "reasoning": "Payment system down affecting revenue, clear API error code"
}

Input: "How do I reset my password?"
Output: {
  "intent": "question",
  "category": "security",
  "urgency": "low",
  "severity": "single_user",
  "sla_risk": false,
  "team": "Support",
  "confidence": 0.98,
  "reasoning": "Simple password reset question, common request"
}

Input: "Need access to production database"
Output: {
  "intent": "service_request",
  "category": "security",
  "urgency": "medium",
  "severity": "single_user",
  "sla_risk": false,
  "team": "Security",
  "confidence": 0.92,
  "reasoning": "Access request requiring approval, security team handles permissions"
}
"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify ticket intent and characteristics.
        
        Args:
            state: Must contain 'user_input'
            
        Returns:
            State updated with classification fields:
            - intent, category, urgency, severity, sla_risk, team, confidence
        """
        start_time = time.time()
        
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                logger.error("IntentAgent: No user_input in state")
                state["error"] = "No user input provided"
                return state
            
            logger.info(f"Classifying intent for: {user_input[:100]}...")
            
            # Call GPT-4o-mini for classification
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,  # Low temperature for consistent classification
                max_tokens=500,
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse JSON response
            classification = json.loads(response.choices[0].message.content)
            
            # Update state with classification
            state["intent"] = classification.get("intent", "question")
            state["category"] = classification.get("category", "technical")
            state["urgency"] = classification.get("urgency", "medium")
            state["severity"] = classification.get("severity", "single_user")
            state["sla_risk"] = classification.get("sla_risk", False)
            state["team"] = classification.get("team", "Support")
            state["classification_reasoning"] = classification.get("reasoning", "")
            
            # Update confidence
            classification_confidence = classification.get("confidence", 0.7)
            self.update_confidence(state, classification_confidence)
            
            logger.info(f"Classification: {state['intent']}, {state['urgency']}, confidence={classification_confidence:.2f}")
            
            # Log execution time
            execution_time = time.time() - start_time
            state = self.log_execution(state, execution_time)
            
            return state
            
        except json.JSONDecodeError as e:
            logger.error(f"IntentAgent JSON parse error: {str(e)}")
            # Fallback to defaults
            state["intent"] = "question"
            state["category"] = "technical"
            state["urgency"] = "medium"
            state["severity"] = "single_user"
            state["sla_risk"] = False
            state["team"] = "Support"
            state["confidence"] = 0.5
            state["error"] = "Classification parsing failed"
            return state
            
        except Exception as e:
            logger.error(f"IntentAgent error: {str(e)}")
            state["error"] = f"Intent classification failed: {str(e)}"
            state["confidence"] = 0.3
            return state
    
    def get_intent_summary(self, state: Dict[str, Any]) -> str:
        """Generate human-readable classification summary"""
        intent = state.get("intent", "unknown")
        urgency = state.get("urgency", "unknown")
        severity = state.get("severity", "unknown")
        team = state.get("team", "unknown")
        
        return f"{intent.upper()} - {urgency} urgency, {severity} impact → {team} team"
