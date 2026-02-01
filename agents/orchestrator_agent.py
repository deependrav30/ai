"""
Orchestrator Agent - The Brain of the Multi-Agent System

Responsibilities:
1. Decide if query should use general chatbot or multi-agent system
2. Plan execution strategy: serial, parallel, or async
3. Coordinate agent execution
4. Aggregate results from multiple agents
5. Handle errors and fallbacks
"""
from typing import Dict, Any, List
import asyncio
import time
from .base_agent import BaseAgent, logger
from .general_chatbot import GeneralChatbot
from .intent_agent import IntentAgent


class OrchestratorAgent(BaseAgent):
    """
    Orchestrates the entire multi-agent workflow.
    Decides execution strategy and coordinates all agents.
    """
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        super().__init__("OrchestratorAgent")
        self.agents = agents
        self.general_chatbot = GeneralChatbot()
        
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration logic.
        
        1. Check if general chatbot should handle
        2. If not, route to multi-agent system
        3. Decide execution model (serial/parallel/async)
        4. Execute agents
        5. Return final state
        
        Args:
            state: Must contain 'user_input'
            
        Returns:
            Final state with 'response' and all agent outputs
        """
        start_time = time.time()
        user_input = state.get("user_input", "")
        
        try:
            input_text = str(user_input) if user_input else ""
            logger.info(f"Orchestrator processing: {input_text[:100]}...")
            
            # Step 1: Check if general chatbot should handle
            if self.general_chatbot.is_general_query(user_input):
                logger.info("Routing to general chatbot (no agent orchestration)")
                state = await self.general_chatbot.process(state)
                state["execution_model"] = "general_chat"
                return state
            
            # Step 2: Route to multi-agent system
            logger.info("Routing to multi-agent system")
            state["execution_model"] = self.decide_execution_model(state)
            
            # Step 3: Execute based on model
            if state["execution_model"] == "parallel":
                state = await self.execute_parallel(state)
            elif state["execution_model"] == "async":
                state = await self.execute_async(state)
            else:  # serial (default)
                state = await self.execute_serial(state)
            
            # Log total execution time
            execution_time = time.time() - start_time
            state["total_execution_time"] = execution_time
            logger.info(f"Orchestrator completed in {execution_time:.2f}s")
            
            return state
            
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            state["error"] = f"Orchestration failed: {str(e)}"
            state["response"] = "I apologize, but I encountered an error processing your request. Please try again or contact support."
            return state
    
    def decide_execution_model(self, state: Dict[str, Any]) -> str:
        """
        Decide whether to use serial, parallel, or async execution.
        
        Logic:
        - Critical urgency → parallel (speed priority)
        - Complex reasoning → serial (accuracy priority)
        - Default → serial (most common)
        
        Args:
            state: Current state
            
        Returns:
            "serial", "parallel", or "async"
        """
        # For now, use serial by default
        # Later, we can add logic based on urgency/complexity
        urgency = state.get("urgency", "medium")
        
        if urgency == "critical":
            logger.info("Using PARALLEL execution for critical urgency")
            return "parallel"
        
        logger.info("Using SERIAL execution (default)")
        return "serial"
    
    async def execute_serial(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agents sequentially (each waits for previous).
        
        Flow:
        1. Intent Agent → classify intent/urgency
        2. Retrieval Agent → search knowledge base
        3. Memory Agent → search past tickets
        4. Reasoning Agent → correlate and analyze
        5. Synthesis Agent → generate response
        6. Guardrails Agent → validate safety
        
        Args:
            state: Current state
            
        Returns:
            Updated state with all agent outputs
        """
        logger.info("Starting SERIAL execution")
        state["agent_execution_order"] = []
        
        # Agent execution order
        agent_order = [
            "intent",
            "retrieval",
            "memory",
            "reasoning",
            "synthesis",
            "guardrails"
        ]
        
        for agent_name in agent_order:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                logger.info(f"Executing {agent.get_name()}...")
                
                try:
                    state = await agent.process(state)
                    state["agent_execution_order"].append(agent_name)
                except Exception as e:
                    logger.error(f"{agent.get_name()} failed: {str(e)}")
                    state["errors"] = state.get("errors", [])
                    state["errors"].append({
                        "agent": agent_name,
                        "error": str(e)
                    })
        
        logger.info("Serial execution completed")
        return state
    
    async def execute_parallel(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute independent agents simultaneously for speed.
        
        Parallel Phase:
        - Intent Agent (classify)
        - Memory Agent (search past tickets)
        - Retrieval Agent (search knowledge base)
        
        Then Serial:
        - Reasoning Agent (needs all results)
        - Synthesis Agent (needs reasoning)
        - Guardrails Agent (needs final response)
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        logger.info("Starting PARALLEL execution")
        state["agent_execution_order"] = []
        
        # Phase 1: Run independent agents in parallel
        parallel_agents = ["intent", "memory", "retrieval"]
        tasks = []
        
        for agent_name in parallel_agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                tasks.append(agent.process(state.copy()))  # Pass copy to avoid conflicts
        
        # Wait for all parallel agents
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results into state
        for i, agent_name in enumerate(parallel_agents):
            if agent_name in self.agents and i < len(results):
                if isinstance(results[i], Exception):
                    logger.error(f"{agent_name} failed: {str(results[i])}")
                else:
                    # Merge result into main state
                    result_state = results[i]
                    for key, value in result_state.items():
                        if key not in ["user_input", "execution_logs"]:
                            state[key] = value
                    state["agent_execution_order"].append(agent_name)
        
        logger.info("Parallel phase completed")
        
        # Phase 2: Run dependent agents serially
        serial_agents = ["reasoning", "synthesis", "guardrails"]
        for agent_name in serial_agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                state = await agent.process(state)
                state["agent_execution_order"].append(agent_name)
        
        logger.info("Parallel execution completed")
        return state
    
    async def execute_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute main flow + background tasks.
        
        Main flow (blocking):
        - Run serial or parallel execution
        
        Background tasks (non-blocking):
        - Memory storage
        - Logging
        - Training data export
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        logger.info("Starting ASYNC execution")
        
        # Execute main flow (user waits for this)
        state = await self.execute_serial(state)
        
        # Launch background tasks (user doesn't wait)
        asyncio.create_task(self.background_memory_storage(state))
        asyncio.create_task(self.background_logging(state))
        
        logger.info("Async execution completed (background tasks launched)")
        return state
    
    async def background_memory_storage(self, state: Dict[str, Any]):
        """Store interaction in episodic memory (background)"""
        await asyncio.sleep(0.1)  # Simulate async delay
        logger.info("Background: Storing episodic memory...")
        # TODO: Implement actual memory storage
    
    async def background_logging(self, state: Dict[str, Any]):
        """Log interaction for observability (background)"""
        await asyncio.sleep(0.1)
        logger.info("Background: Logging interaction...")
        # TODO: Implement actual logging
    
    def get_execution_summary(self, state: Dict[str, Any]) -> str:
        """Generate summary of agent execution"""
        model = state.get("execution_model", "unknown")
        order = state.get("agent_execution_order", [])
        time_taken = state.get("total_execution_time", 0)
        
        return f"Execution: {model}, Agents: {' → '.join(order)}, Time: {time_taken:.2f}s"
