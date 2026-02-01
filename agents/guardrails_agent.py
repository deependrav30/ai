"""
Guardrails Agent - Safety and Compliance Validation

Responsibilities:
1. Detect harmful content (violence, self-harm, sexual, hate)
2. Detect jailbreak attempts
3. Detect financial fraud requests
4. Validate response appropriateness
5. Flag for human review if needed
6. Block unsafe responses

Safety Categories:
- Violence: Threats, harm, weapons
- Self-harm: Suicide, self-injury
- Sexual: Inappropriate content
- Hate: Discrimination, harassment
- Jailbreak: Attempts to bypass rules
- Financial Fraud: Scams, unauthorized transactions
"""
from typing import Dict, Any, List
import time
import os
import re
from openai import OpenAI
from .base_agent import BaseAgent, logger
from utils.metrics import track_agent_execution, track_openai_call


class GuardrailsAgent(BaseAgent):
    """
    Final safety check before response delivery.
    Blocks unsafe content and flags for human review.
    """
    
    def __init__(self):
        super().__init__("GuardrailsAgent")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Define safety categories and keywords
        self.safety_keywords = {
            "violence": ["kill", "murder", "attack", "bomb", "weapon", "hurt", "harm someone"],
            "self_harm": ["suicide", "kill myself", "self harm", "end my life", "hurt myself"],
            "sexual": ["explicit", "nsfw", "sexual content"],
            "hate": ["racist", "sexist", "discrimination", "hate speech"],
            "jailbreak": ["ignore previous", "ignore instructions", "pretend you", "roleplay as", "jailbreak"],
            "financial_fraud": ["transfer money", "unauthorized access", "steal", "fraud", "scam", "hack account"]
        }
    
    @track_agent_execution
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of user input and generated response.
        
        Args:
            state: Must contain 'user_input' and 'response'
            
        Returns:
            State updated with:
            - safety_passed: Boolean
            - safety_violations: List of detected violations
            - needs_human_review: Boolean
            - blocked: Boolean if response should be blocked
        """
        start_time = time.time()
        
        try:
            user_input = state.get("user_input", "")
            response = state.get("response", "")
            
            logger.info("Running safety guardrails...")
            
            # Check user input for safety violations
            input_violations = self.detect_violations(user_input)
            
            # Check response for safety violations
            response_violations = self.detect_violations(response)
            
            # Combine violations
            all_violations = list(set(input_violations + response_violations))
            
            # Determine if response should be blocked
            critical_violations = ["violence", "self_harm", "hate", "financial_fraud"]
            blocked = any(v in critical_violations for v in all_violations)
            
            # Determine if human review needed
            needs_review = len(all_violations) > 0 or state.get("confidence", 1.0) < 0.4
            
            # Update state
            state["safety_passed"] = len(all_violations) == 0
            state["safety_violations"] = all_violations
            state["needs_human_review"] = needs_review
            state["blocked"] = blocked
            
            # If blocked, replace response with safety message
            if blocked:
                state["response"] = self.get_safety_message(all_violations)
                state["confidence"] = 0.0
                logger.warning(f"BLOCKED: Safety violations detected: {all_violations}")
            elif needs_review:
                logger.info(f"FLAGGED for human review: {all_violations if all_violations else 'low confidence'}")
            else:
                logger.info("Safety check passed")
            
            # Update confidence based on safety
            if not blocked:
                safety_confidence = 1.0 if len(all_violations) == 0 else 0.7
                self.update_confidence(state, safety_confidence)
            
            # Log execution time
            execution_time = time.time() - start_time
            state = self.log_execution(state, execution_time)
            
            return state
            
        except Exception as e:
            logger.error(f"GuardrailsAgent error: {str(e)}")
            # In case of error, flag for human review to be safe
            state["safety_passed"] = False
            state["needs_human_review"] = True
            state["error"] = f"Safety check failed: {str(e)}"
            return state
    
    def detect_violations(self, text: str) -> List[str]:
        """
        Detect safety violations in text using keyword matching.
        
        Args:
            text: Text to check
            
        Returns:
            List of violated categories
        """
        violations = []
        text_lower = text.lower()
        
        for category, keywords in self.safety_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    violations.append(category)
                    logger.warning(f"Detected {category} violation: keyword '{keyword}'")
                    break  # One violation per category
        
        return violations
    
    def get_safety_message(self, violations: List[str]) -> str:
        """
        Generate appropriate safety message based on violations.
        
        Args:
            violations: List of violated categories
            
        Returns:
            Safety message for user
        """
        if "self_harm" in violations:
            return """I notice you may be in distress. Please reach out to someone who can help:

- National Suicide Prevention Lifeline: 988 or 1-800-273-8255
- Crisis Text Line: Text HOME to 741741
- International: https://findahelpline.com

For technical support, please contact our team during business hours."""
        
        elif "violence" in violations:
            return """I cannot assist with requests involving violence or harm.

If you have a legitimate technical support question, please rephrase your request.

For emergencies, please contact local authorities."""
        
        elif "financial_fraud" in violations:
            return """I cannot assist with requests that may involve unauthorized access or financial fraud.

For legitimate account or billing issues, please contact our authorized support team:
- Email: support@company.com
- Phone: 1-800-XXX-XXXX

Verify all support contacts through our official website."""
        
        elif "jailbreak" in violations:
            return """I'm designed to assist with technical support questions within my guidelines.

If you have a genuine support need, please describe the issue clearly and I'll do my best to help."""
        
        else:
            return """I'm unable to process this request as it may violate our content policies.

For technical support, please rephrase your question or contact our support team directly.

Thank you for understanding."""
    
    def check_confidence_threshold(self, state: Dict[str, Any]) -> bool:
        """
        Check if confidence is below threshold for human escalation.
        
        Args:
            state: Current state
            
        Returns:
            True if should escalate, False otherwise
        """
        confidence = state.get("confidence", 0.5)
        urgency = state.get("urgency", "medium")
        
        # Lower threshold for critical issues
        threshold = 0.3 if urgency == "critical" else 0.4
        
        return confidence < threshold
    
    def should_escalate(self, state: Dict[str, Any]) -> bool:
        """
        Determine if ticket should be escalated to human.
        
        Escalation triggers:
        - Safety violations
        - Low confidence
        - Critical urgency + pattern detected
        - SLA risk
        
        Args:
            state: Current state
            
        Returns:
            True if should escalate, False otherwise
        """
        # Safety violations
        if not state.get("safety_passed", True):
            return True
        
        # Low confidence
        if self.check_confidence_threshold(state):
            return True
        
        # Critical + pattern
        if state.get("urgency") == "critical" and state.get("pattern_detected"):
            return True
        
        # SLA risk
        if state.get("sla_risk"):
            return True
        
        return False
    
    def generate_escalation_message(self, state: Dict[str, Any]) -> str:
        """
        Generate message explaining escalation to human.
        
        Args:
            state: Current state
            
        Returns:
            Escalation message
        """
        reasons = []
        
        if not state.get("safety_passed", True):
            reasons.append("requires human review for safety")
        
        if state.get("confidence", 1.0) < 0.4:
            reasons.append("complex issue requiring expert attention")
        
        if state.get("urgency") == "critical":
            reasons.append("critical urgency")
        
        if state.get("sla_risk"):
            reasons.append("SLA risk detected")
        
        reason_text = ", ".join(reasons) if reasons else "additional expertise needed"
        
        return f"""This ticket has been escalated to our {state.get('team', 'support')} team because it {reason_text}.

A specialist will review your case and respond shortly.

Ticket ID: {state.get('ticket_id', 'N/A')}
Priority: {state.get('urgency', 'medium').upper()}
Estimated Response Time: Based on SLA"""
    
    def get_safety_summary(self, state: Dict[str, Any]) -> str:
        """Generate summary of safety check"""
        passed = state.get("safety_passed", True)
        violations = state.get("safety_violations", [])
        needs_review = state.get("needs_human_review", False)
        
        if passed and not needs_review:
            return "✅ Safety check passed"
        elif needs_review and not violations:
            return "⚠️ Flagged for human review (low confidence)"
        else:
            return f"🚫 Violations: {', '.join(violations)}"
