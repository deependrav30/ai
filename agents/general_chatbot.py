"""
General Chatbot - Non-Agent Mode for Simple Queries

Handles simple, non-technical queries without agent orchestration.
Examples:
- Greetings: "Hi", "Hello", "How are you?"
- General questions: "What can you do?", "How does this work?"
- Small talk that doesn't require ticket processing

If query needs technical analysis, routes to multi-agent system.
"""
from typing import Dict, Any
import os
from openai import OpenAI
from .base_agent import BaseAgent, logger
from utils.metrics import track_agent_execution, track_openai_call


class GeneralChatbot(BaseAgent):
    """
    Simple chatbot for non-technical, conversational queries.
    Does NOT use agent orchestration.
    """
    
    def __init__(self):
        super().__init__("GeneralChatbot")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # System prompt for general chat
        self.system_prompt = """You are a helpful AI assistant for a support ticketing system.

You handle simple, conversational queries like:
- Greetings and small talk
- Questions about how the system works
- General information requests

For technical issues, incidents, or support tickets, politely suggest:
"For technical support or incident reporting, please provide details about your issue and I'll route it to our specialized support agents."

Keep responses friendly, concise, and helpful.
"""
    
    def is_general_query(self, query: str) -> bool:
        """
        Determine if query is general/conversational (no agent needed).
        
        Args:
            query: User input
            
        Returns:
            True if general query, False if needs agent processing
        """
        query_lower = query.lower().strip()
        
        # Greetings
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if any(greeting in query_lower for greeting in greetings):
            return True
        
        # System questions
        system_questions = [
            "what can you do",
            "how does this work",
            "what is this",
            "help me",
            "who are you"
        ]
        if any(q in query_lower for q in system_questions):
            return True
        
        # Very short queries (likely greetings)
        if len(query.split()) <= 3:
            return True
        
        # Technical keywords indicate agent processing needed
        technical_keywords = [
            "error", "bug", "issue", "problem", "not working", "broken",
            "down", "failed", "cannot", "can't", "unable to",
            "crash", "timeout", "slow", "performance",
            "access", "permission", "denied", "password", "login"
        ]
        if any(keyword in query_lower for keyword in technical_keywords):
            return False
        
        # Default to general for short, simple queries
        return len(query.split()) <= 10
    
    @track_agent_execution
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process general query with simple GPT-4 chat.
        
        Args:
            state: Must contain 'user_input'
            
        Returns:
            State with 'response', 'mode': 'general_chat'
        """
        try:
            user_input = state.get("user_input", "")
            
            # Generate response using GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            # Track OpenAI API call
            track_openai_call("gpt-4", "chat", response.usage.prompt_tokens, response.usage.completion_tokens)
            
            answer = response.choices[0].message.content
            
            state["response"] = answer
            state["mode"] = "general_chat"
            state["agent_used"] = "GeneralChatbot"
            state["confidence"] = 0.95  # High confidence for simple queries
            
            logger.info(f"General chatbot response: {answer[:100]}...")
            
            return state
            
        except Exception as e:
            logger.error(f"GeneralChatbot error: {str(e)}")
            state["response"] = "I apologize, but I'm having trouble processing your request. Please try again."
            state["mode"] = "general_chat"
            state["error"] = str(e)
            return state
    
    def should_route_to_agents(self, query: str) -> bool:
        """
        Check if query should be routed to multi-agent system.
        Opposite of is_general_query()
        
        Args:
            query: User input
            
        Returns:
            True if should use agents, False if general chat is fine
        """
        return not self.is_general_query(query)
