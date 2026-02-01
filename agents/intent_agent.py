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

Enhanced with keyword matching for better accuracy.
"""
from typing import Dict, Any
import os
import json
import time
import re
from openai import OpenAI
from .base_agent import BaseAgent, logger


class IntentAgent(BaseAgent):
    """
    Classifies user intent and ticket characteristics using GPT-4o-mini.
    Fast, cost-effective, and accurate for structured classification.
    Enhanced with keyword matching for improved accuracy.
    """
    
    # Keyword patterns for intent detection
    INTENT_KEYWORDS = {
        'incident': [
            'down', 'outage', 'not working', 'broken', 'failed', 'error',
            'crashed', 'unavailable', 'timeout', 'slow', 'degraded',
            'returning 500', 'returning 404', '401 error', '403 error',
            'api error', 'service error', 'connection failed',
            'cannot access', 'unable to', 'users affected', 'production issue'
        ],
        'service_request': [
            'create', 'add', 'provision', 'setup', 'configure', 'install',
            'need access to', 'request access', 'grant permission',
            'reset password', 'unlock account', 'new user', 'new account'
        ],
        'question': [
            'how do i', 'how to', 'what is', 'what does', 'why is',
            'can you explain', 'where can i find', 'is it possible',
            'documentation', 'guide', 'help me understand'
        ],
        'problem': [
            'keep getting', 'repeatedly', 'frequently', 'intermittent',
            'sometimes works', 'root cause', 'pattern', 'trend'
        ],
        'change': [
            'deploy', 'release', 'rollout', 'migration', 'maintenance window',
            'scheduled change'
        ]
    }
    
    # Urgency indicators
    URGENCY_KEYWORDS = {
        'critical': [
            'production down', 'all users affected', 'revenue impact',
            'customer facing', 'complete outage', 'critical', 'emergency',
            'immediate', 'sev 1', 'p0', 'urgent urgent', 'right now'
        ],
        'high': [
            'multiple users', 'important feature', 'major issue',
            'blocking', 'preventing work', 'cannot proceed',
            'sev 2', 'p1', 'soon', 'today'
        ],
        'medium': [
            'some users', 'workaround available', 'not blocking',
            'sev 3', 'p2', 'normal priority', 'moderate'
        ],
        'low': [
            'cosmetic', 'nice to have', 'enhancement', 'when possible',
            'sev 4', 'p3', 'low priority', 'eventually'
        ]
    }
    
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
    
    def _keyword_match(self, text: str, keywords_dict: dict) -> tuple:
        """
        Match keywords against text to predict classification.
        
        Returns:
            (predicted_value, confidence, matched_keywords)
        """
        text_lower = text.lower()
        scores = {}
        
        for value, keywords in keywords_dict.items():
            matched = [kw for kw in keywords if kw in text_lower]
            scores[value] = len(matched)
        
        if not scores or max(scores.values()) == 0:
            return None, 0.0, []
        
        predicted = max(scores, key=scores.get)
        # Normalize confidence: more matches = higher confidence
        confidence = min(scores[predicted] / 3, 0.9)  # Cap at 0.9
        
        # Get matched keywords
        matched_kws = [kw for kw in keywords_dict[predicted] if kw in text_lower]
        
        return predicted, confidence, matched_kws
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify ticket intent and characteristics.
        Enhanced with keyword matching for improved accuracy.
        
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
            
            # Pre-classify using keyword matching
            intent_hint, intent_conf, intent_kws = self._keyword_match(user_input, self.INTENT_KEYWORDS)
            urgency_hint, urgency_conf, urgency_kws = self._keyword_match(user_input, self.URGENCY_KEYWORDS)
            
            # Add hints to the prompt if confidence is high
            enhanced_prompt = user_input
            if intent_hint and intent_conf > 0.3:
                enhanced_prompt += f"\n\n[Keyword Analysis Hint: Detected intent='{intent_hint}' with {len(intent_kws)} matching keywords: {', '.join(intent_kws[:3])}]"
            if urgency_hint and urgency_conf > 0.3:
                enhanced_prompt += f"\n[Urgency Hint: Detected urgency='{urgency_hint}' with {len(urgency_kws)} matching keywords: {', '.join(urgency_kws[:3])}]"
            
            # Call GPT-4o-mini for classification
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": enhanced_prompt}
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
