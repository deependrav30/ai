"""
Agent Workflow Coordinator

Main entry point for the multi-agent system.
Initializes all agents and orchestrates ticket processing.
"""
import asyncio
from typing import Dict, Any
from datetime import datetime

from agents.base_agent import logger
from agents.general_chatbot import GeneralChatbot
from agents.orchestrator_agent import OrchestratorAgent
from agents.intent_agent import IntentAgent
from agents.retrieval_agent import RetrievalAgent
from agents.memory_agent import MemoryAgent
from agents.reasoning_agent import ReasoningAgent
from agents.synthesis_agent import SynthesisAgent
from agents.guardrails_agent import GuardrailsAgent


class AgentWorkflow:
    """
    Main workflow coordinator for the multi-agent system.
    """
    
    def __init__(self):
        """Initialize all agents"""
        logger.info("Initializing Agent Workflow...")
        
        # Initialize individual agents
        self.agents = {
            "intent": IntentAgent(),
            "retrieval": RetrievalAgent(),
            "memory": MemoryAgent(),
            "reasoning": ReasoningAgent(),
            "synthesis": SynthesisAgent(),
            "guardrails": GuardrailsAgent()
        }
        
        # Initialize orchestrator with agents
        self.orchestrator = OrchestratorAgent(self.agents)
        
        logger.info(f"Initialized {len(self.agents)} agents successfully")
    
    async def process_ticket(self, user_input: str, ticket_id: str = None) -> Dict[str, Any]:
        """
        Process a ticket/query through the multi-agent system.
        
        Args:
            user_input: User's question or issue description
            ticket_id: Optional ticket ID (generated if not provided)
            
        Returns:
            Final state with response and all agent outputs
        """
        # Initialize state
        state = {
            "user_input": user_input,
            "ticket_id": ticket_id or f"TICKET-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "confidence": 1.0,  # Start with high confidence
            "execution_logs": []
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Ticket: {state['ticket_id']}")
        input_text = str(state.get('user_input', ''))
        logger.info(f"Input: {input_text[:100]}...")
        logger.info(f"{'='*60}\n")
        
        try:
            # Execute orchestrator (handles general chat vs multi-agent routing)
            state = await self.orchestrator.process(state)
            
            # Log final results
            self._log_final_state(state)
            
            # Store in episodic memory if ticket resolved successfully
            if state.get("response_generated") and not state.get("blocked"):
                self.agents["memory"].store_episodic_memory(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}")
            state["error"] = str(e)
            state["response"] = "I apologize, but an error occurred. Please try again or contact support."
            return state
    
    def _log_final_state(self, state: Dict[str, Any]):
        """Log final state for debugging and observability"""
        logger.info(f"\n{'='*60}")
        logger.info(f"FINAL STATE - Ticket {state.get('ticket_id')}")
        logger.info(f"{'='*60}")
        logger.info(f"Mode: {state.get('execution_model', 'unknown')}")
        logger.info(f"Agents: {' → '.join(state.get('agent_execution_order', []))}")
        
        if state.get("intent"):
            logger.info(f"\nClassification:")
            logger.info(f"  Intent: {state.get('intent')}")
            logger.info(f"  Category: {state.get('category')}")
            logger.info(f"  Urgency: {state.get('urgency')}")
            logger.info(f"  Team: {state.get('team')}")
        
        logger.info(f"\nResults:")
        logger.info(f"  Confidence: {state.get('confidence', 0):.2f}")
        logger.info(f"  Documents Retrieved: {state.get('doc_count', 0)}")
        logger.info(f"  Past Tickets Found: {state.get('memory_matches', 0)}")
        logger.info(f"  Pattern Detected: {state.get('pattern_detected', False)}")
        logger.info(f"  Safety Passed: {state.get('safety_passed', True)}")
        
        if state.get("needs_human_review"):
            logger.info(f"  ⚠️  NEEDS HUMAN REVIEW")
        if state.get("blocked"):
            logger.info(f"  🚫 BLOCKED - Safety Violation")
        
        logger.info(f"\nResponse: {state.get('response', 'No response')[:200]}...")
        logger.info(f"{'='*60}\n")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        metrics = {
            "orchestrator": self.orchestrator.get_metrics()
        }
        
        for name, agent in self.agents.items():
            metrics[name] = agent.get_metrics()
        
        return metrics


# Convenience function for single ticket processing
async def process_single_ticket(user_input: str) -> Dict[str, Any]:
    """
    Process a single ticket through the agent system.
    
    Args:
        user_input: User's question or issue
        
    Returns:
        Final state with response
    """
    workflow = AgentWorkflow()
    result = await workflow.process_ticket(user_input)
    return result


# Example usage
if __name__ == "__main__":
    async def main():
        # Example 1: General chatbot query
        print("\n" + "="*60)
        print("Example 1: General Query")
        print("="*60)
        result1 = await process_single_ticket("Hello! How are you?")
        print(f"\nResponse: {result1['response']}\n")
        
        # Example 2: Technical incident
        print("\n" + "="*60)
        print("Example 2: Technical Incident")
        print("="*60)
        result2 = await process_single_ticket(
            "The payment API is returning 500 errors and customers can't checkout"
        )
        print(f"\nResponse: {result2['response']}\n")
        print(f"Classification: {result2.get('intent')} - {result2.get('urgency')} urgency")
        print(f"Confidence: {result2.get('confidence', 0):.2f}")
        
        # Example 3: Simple question
        print("\n" + "="*60)
        print("Example 3: Simple Question")
        print("="*60)
        result3 = await process_single_ticket("How do I reset my password?")
        print(f"\nResponse: {result3['response']}\n")
    
    # Run examples
    asyncio.run(main())
