"""
Synthesis Agent - Response Generation

Responsibilities:
1. Generate final user-facing response
2. Combine insights from all agents
3. Format response appropriately (ticket update, resolution, escalation)
4. Include source citations from knowledge base
5. Provide clear next steps
"""
from typing import Dict, Any
import time
import os
from openai import OpenAI
from .base_agent import BaseAgent, logger


class SynthesisAgent(BaseAgent):
    """
    Synthesizes final response from all agent outputs.
    Creates user-facing response with citations and recommendations.
    """
    
    def __init__(self):
        super().__init__("SynthesisAgent")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.system_prompt = """You are an expert support response writer for a ticketing system.

Your role is to generate a clear, professional, helpful response to the user based on:
- Classification of their issue (type, urgency, severity)
- Retrieved knowledge base documents
- Similar past tickets and resolutions
- Analysis and recommendations from reasoning

Your response should:
1. Acknowledge the issue clearly
2. Provide solution steps or explanation
3. Reference knowledge base sources when applicable
4. Suggest next steps or escalation if needed
5. Be professional, empathetic, and actionable

Response format:
- For incidents: Provide resolution steps, workarounds, or escalation
- For questions: Provide clear answer with documentation links
- For service requests: Explain process and timeline
- For problems: Explain investigation approach and updates

Always maintain a helpful, solution-oriented tone.
Include source citations from knowledge base when referencing documentation.
"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final response from all agent outputs.
        
        Args:
            state: Must contain all agent outputs (intent, retrieved_docs, reasoning, etc.)
            
        Returns:
            State updated with:
            - response: Final user-facing response
            - sources: List of source citations
            - next_steps: Recommended next actions
        """
        start_time = time.time()
        
        try:
            # Build synthesis context
            synthesis_context = self.build_synthesis_context(state)
            
            logger.info("Generating final response...")
            
            # Use GPT-4 for high-quality response generation
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": synthesis_context}
                ],
                temperature=0.5,  # Balanced creativity
                max_tokens=1000
            )
            
            final_response = response.choices[0].message.content
            
            # Extract sources from retrieved documents
            sources = self.extract_sources(state)
            
            # Extract next steps from recommendations
            next_steps = state.get("recommendations", [])
            
            # Add metadata to response
            state["response"] = final_response
            state["sources"] = sources
            state["next_steps"] = next_steps
            state["response_generated"] = True
            
            logger.info(f"Response generated: {final_response[:100]}...")
            
            # Log execution time
            execution_time = time.time() - start_time
            state = self.log_execution(state, execution_time)
            
            return state
            
        except Exception as e:
            logger.error(f"SynthesisAgent error: {str(e)}")
            
            # Fallback response
            state["response"] = self.generate_fallback_response(state)
            state["sources"] = []
            state["next_steps"] = ["Contact support for further assistance"]
            state["error"] = f"Response synthesis failed: {str(e)}"
            
            return state
    
    def build_synthesis_context(self, state: Dict[str, Any]) -> str:
        """
        Build context for response synthesis from all agent outputs.
        
        Args:
            state: Current state with all agent outputs
            
        Returns:
            Formatted context string for synthesis
        """
        context_parts = []
        
        # User's original input
        context_parts.append(f"USER ISSUE:\n{state.get('user_input', '')}\n")
        
        # Classification
        intent = state.get("intent", "")
        category = state.get("category", "")
        urgency = state.get("urgency", "")
        severity = state.get("severity", "")
        team = state.get("team", "")
        
        context_parts.append(f"CLASSIFICATION:")
        context_parts.append(f"- Type: {intent}")
        context_parts.append(f"- Category: {category}")
        context_parts.append(f"- Urgency: {urgency}")
        context_parts.append(f"- Severity: {severity}")
        context_parts.append(f"- Assigned Team: {team}\n")
        
        # Knowledge base documents
        retrieved_docs = state.get("retrieved_docs", [])
        if retrieved_docs:
            context_parts.append("KNOWLEDGE BASE INFORMATION:")
            for i, doc in enumerate(retrieved_docs[:3], 1):
                content = doc.get("content", "")[:400]
                source = doc.get("source", "unknown")
                context_parts.append(f"{i}. Source: {source}")
                context_parts.append(f"   {content}...\n")
        
        # Past resolutions
        past_resolutions = state.get("past_resolutions", [])
        if past_resolutions:
            context_parts.append("SUCCESSFUL PAST RESOLUTIONS:")
            for i, resolution in enumerate(past_resolutions[:2], 1):
                context_parts.append(f"{i}. {resolution.get('resolution', '')[:300]}...\n")
        
        # Reasoning and recommendations
        reasoning = state.get("reasoning", "")
        if reasoning:
            context_parts.append(f"ANALYSIS:\n{reasoning[:500]}...\n")
        
        recommendations = state.get("recommendations", [])
        if recommendations:
            context_parts.append("RECOMMENDATIONS:")
            for rec in recommendations:
                context_parts.append(f"- {rec}")
            context_parts.append("")
        
        # Request for response
        context_parts.append("""
Please generate a professional, helpful response to the user that:
1. Acknowledges their issue
2. Provides a solution, explanation, or next steps
3. References relevant knowledge base sources
4. Maintains a supportive, solution-oriented tone

The response should be clear, actionable, and appropriate for the urgency level.
""")
        
        return "\n".join(context_parts)
    
    def extract_sources(self, state: Dict[str, Any]) -> list:
        """
        Extract source citations from retrieved documents.
        
        Args:
            state: State with retrieved_docs
            
        Returns:
            List of source dictionaries
        """
        sources = []
        retrieved_docs = state.get("retrieved_docs", [])
        
        for doc in retrieved_docs:
            source = {
                "name": doc.get("source", "Unknown"),
                "score": doc.get("score", 0.0)
            }
            if source not in sources:
                sources.append(source)
        
        return sources[:5]  # Top 5 sources
    
    def generate_fallback_response(self, state: Dict[str, Any]) -> str:
        """
        Generate simple fallback response when synthesis fails.
        
        Args:
            state: Current state
            
        Returns:
            Basic fallback response
        """
        intent = state.get("intent", "question")
        urgency = state.get("urgency", "medium")
        
        if urgency == "critical":
            return """Thank you for reporting this critical issue. I've escalated this to our support team for immediate attention.

A support engineer will contact you shortly to assist with resolution.

If you need immediate assistance, please contact our emergency support line."""
        
        elif intent == "question":
            return """Thank you for your question. While I couldn't find a complete answer in our knowledge base, I've forwarded your inquiry to our support team.

They will respond with detailed information shortly.

Is there anything else I can help you with?"""
        
        else:
            return """Thank you for contacting support. I've received your request and our team will review it.

We'll get back to you with a solution or next steps soon.

If this is urgent, please let us know and we'll prioritize accordingly."""
    
    def format_response_with_sources(self, response: str, sources: list) -> str:
        """
        Format response with source citations appended.
        
        Args:
            response: Main response text
            sources: List of source dictionaries
            
        Returns:
            Formatted response with sources
        """
        if not sources:
            return response
        
        formatted = response + "\n\n---\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            formatted += f"{i}. {source['name']} (relevance: {source['score']:.2f})\n"
        
        return formatted
