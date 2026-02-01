"""
Reasoning Agent - Correlation and Pattern Detection

Responsibilities:
1. Correlate information from multiple sources
2. Identify patterns across past tickets
3. Detect root causes for recurring issues
4. Assess risk and impact
5. Generate insights and recommendations
"""
from typing import Dict, Any, List
import time
import os
from openai import OpenAI
from .base_agent import BaseAgent, logger


class ReasoningAgent(BaseAgent):
    """
    Analyzes and correlates data from Intent, Retrieval, and Memory agents.
    Identifies patterns, root causes, and generates actionable insights.
    """
    
    def __init__(self):
        super().__init__("ReasoningAgent")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.system_prompt = """You are an expert reasoning system for IT support ticket analysis.

Your role is to:
1. Analyze the current ticket/issue
2. Correlate with similar past tickets
3. Identify patterns and root causes
4. Assess risks and business impact
5. Generate actionable insights and recommendations

You will receive:
- User's input (current issue)
- Classification (intent, urgency, category)
- Retrieved knowledge base documents
- Similar past tickets and their resolutions

Your output should include:
- Pattern analysis: Is this a recurring issue?
- Root cause hypothesis: What might be causing this?
- Risk assessment: What are the potential impacts?
- Correlation insights: How does this relate to past tickets?
- Recommendations: What should be done?

Provide structured, actionable analysis that helps resolve the ticket efficiently.
"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and correlate information to generate insights.
        
        Args:
            state: Must contain user_input, intent, retrieved_docs, past_tickets
            
        Returns:
            State updated with:
            - reasoning: Analysis and insights
            - pattern_detected: Whether recurring pattern found
            - root_cause: Hypothesis about root cause
            - recommendations: List of recommended actions
        """
        start_time = time.time()
        
        try:
            # Validate required data
            if not self.validate_state(state, ["user_input"]):
                logger.error("ReasoningAgent: Missing required state keys")
                return state
            
            # Build reasoning context
            reasoning_context = self.build_reasoning_context(state)
            
            logger.info("Generating reasoning and insights...")
            
            # Use GPT-4 for complex reasoning
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": reasoning_context}
                ],
                temperature=0.4,  # Moderate creativity for reasoning
                max_tokens=800
            )
            
            reasoning = response.choices[0].message.content
            
            # Parse reasoning output
            analysis = self.parse_reasoning(reasoning)
            
            state["reasoning"] = reasoning
            state["pattern_detected"] = analysis["pattern_detected"]
            state["root_cause"] = analysis["root_cause"]
            state["recommendations"] = analysis["recommendations"]
            state["risk_level"] = analysis["risk_level"]
            
            # Update confidence based on reasoning quality
            reasoning_confidence = analysis["confidence"]
            self.update_confidence(state, reasoning_confidence)
            
            logger.info(f"Reasoning complete: {reasoning[:100]}...")
            
            # Log execution time
            execution_time = time.time() - start_time
            state = self.log_execution(state, execution_time)
            
            return state
            
        except Exception as e:
            logger.error(f"ReasoningAgent error: {str(e)}")
            state["reasoning"] = "Unable to generate detailed reasoning"
            state["pattern_detected"] = False
            state["error"] = f"Reasoning failed: {str(e)}"
            return state
    
    def build_reasoning_context(self, state: Dict[str, Any]) -> str:
        """
        Build context for reasoning from all available information.
        
        Args:
            state: Current state with all agent outputs
            
        Returns:
            Formatted context string for reasoning
        """
        context_parts = []
        
        # Current issue
        context_parts.append(f"CURRENT ISSUE:\n{state.get('user_input', '')}\n")
        
        # Classification
        intent = state.get("intent", "")
        category = state.get("category", "")
        urgency = state.get("urgency", "")
        severity = state.get("severity", "")
        
        context_parts.append(f"CLASSIFICATION:\n- Type: {intent}\n- Category: {category}\n- Urgency: {urgency}\n- Severity: {severity}\n")
        
        # Retrieved documents
        retrieved_docs = state.get("retrieved_docs", [])
        if retrieved_docs:
            context_parts.append("KNOWLEDGE BASE DOCUMENTS:")
            for i, doc in enumerate(retrieved_docs[:3], 1):  # Top 3 docs
                content = doc.get("content", "")[:300]  # First 300 chars
                context_parts.append(f"{i}. {content}...")
            context_parts.append("")
        
        # Past tickets
        past_tickets = state.get("past_tickets", [])
        if past_tickets:
            context_parts.append("SIMILAR PAST TICKETS:")
            for i, ticket in enumerate(past_tickets[:3], 1):  # Top 3 tickets
                context_parts.append(f"{i}. Issue: {ticket.get('user_input', '')[:200]}")
                context_parts.append(f"   Resolution: {ticket.get('resolution', 'N/A')[:200]}")
                context_parts.append(f"   Outcome: {ticket.get('outcome', 'N/A')}\n")
            context_parts.append("")
        
        context_parts.append("""
Please analyze the above information and provide:
1. Pattern Analysis: Is this a recurring issue? Any trends?
2. Root Cause: What might be causing this issue?
3. Risk Assessment: What are the potential impacts?
4. Recommendations: What actions should be taken?
5. Confidence: How confident are you in this analysis? (0.0-1.0)
""")
        
        return "\n".join(context_parts)
    
    def parse_reasoning(self, reasoning: str) -> Dict[str, Any]:
        """
        Parse reasoning output to extract structured insights.
        
        Args:
            reasoning: Raw reasoning text from GPT-4
            
        Returns:
            Dictionary with parsed insights
        """
        reasoning_lower = reasoning.lower()
        
        # Detect patterns
        pattern_keywords = ["recurring", "pattern", "frequent", "repeated", "similar issue"]
        pattern_detected = any(keyword in reasoning_lower for keyword in pattern_keywords)
        
        # Extract root cause (look for "root cause" section)
        root_cause = "Analysis in progress"
        if "root cause" in reasoning_lower:
            lines = reasoning.split("\n")
            for i, line in enumerate(lines):
                if "root cause" in line.lower() and i + 1 < len(lines):
                    root_cause = lines[i + 1].strip()
                    break
        
        # Extract recommendations
        recommendations = []
        if "recommendation" in reasoning_lower:
            lines = reasoning.split("\n")
            capturing = False
            for line in lines:
                if "recommendation" in line.lower():
                    capturing = True
                    continue
                if capturing and line.strip():
                    if line.strip().startswith(("-", "•", "*", "1.", "2.", "3.")):
                        recommendations.append(line.strip())
                    elif not line[0].isdigit() and not line.strip().startswith(("-", "•", "*")):
                        capturing = False
        
        # Assess risk level
        risk_level = "medium"
        if any(word in reasoning_lower for word in ["critical", "severe", "high risk", "urgent"]):
            risk_level = "high"
        elif any(word in reasoning_lower for word in ["low risk", "minimal", "minor"]):
            risk_level = "low"
        
        # Extract confidence (look for number between 0-1 or percentage)
        confidence = 0.75  # Default
        import re
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', reasoning_lower)
        if confidence_match:
            try:
                conf_value = float(confidence_match.group(1))
                if conf_value > 1:  # Percentage
                    confidence = conf_value / 100.0
                else:
                    confidence = conf_value
            except:
                pass
        
        return {
            "pattern_detected": pattern_detected,
            "root_cause": root_cause,
            "recommendations": recommendations if recommendations else ["Investigate further based on analysis"],
            "risk_level": risk_level,
            "confidence": confidence
        }
    
    def get_reasoning_summary(self, state: Dict[str, Any]) -> str:
        """Generate brief summary of reasoning"""
        pattern = "Pattern detected" if state.get("pattern_detected") else "No pattern"
        risk = state.get("risk_level", "unknown")
        rec_count = len(state.get("recommendations", []))
        
        return f"{pattern}, Risk: {risk}, {rec_count} recommendations"
