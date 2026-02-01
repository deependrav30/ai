"""
Base Agent class for all collaborative agents
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the collaborative system.
    
    All agents must implement:
    - process(): Main processing logic
    - get_name(): Agent name for logging
    """
    
    def __init__(self, name: str):
        self.name = name
        self.execution_count = 0
        self.total_time = 0.0
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current state and return updated state.
        
        Args:
            state: Current agent state containing all context
            
        Returns:
            Updated state with agent's contributions
        """
        pass
    
    def get_name(self) -> str:
        """Return agent name"""
        return self.name
    
    def log_execution(self, state: Dict[str, Any], execution_time: float):
        """Log agent execution for observability"""
        self.execution_count += 1
        self.total_time += execution_time
        
        log_entry = {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time,
            "execution_count": self.execution_count,
            "state_keys": list(state.keys())
        }
        
        logger.info(f"{self.name} executed in {execution_time:.3f}s")
        
        # Store in state for UI display
        if "execution_logs" not in state:
            state["execution_logs"] = []
        state["execution_logs"].append(log_entry)
        
        return state
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return agent performance metrics"""
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "total_time": self.total_time,
            "avg_time": self.total_time / self.execution_count if self.execution_count > 0 else 0
        }
    
    def validate_state(self, state: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that state contains required keys.
        
        Args:
            state: Current state
            required_keys: List of required keys
            
        Returns:
            True if all keys present, False otherwise
        """
        missing_keys = [key for key in required_keys if key not in state]
        if missing_keys:
            logger.error(f"{self.name}: Missing required keys: {missing_keys}")
            return False
        return True
    
    def update_confidence(self, state: Dict[str, Any], agent_confidence: float):
        """
        Update overall confidence based on agent's confidence.
        Uses minimum confidence across all agents.
        
        Args:
            state: Current state
            agent_confidence: This agent's confidence (0.0 to 1.0)
        """
        if "confidence" not in state:
            state["confidence"] = agent_confidence
        else:
            # Use minimum confidence (most conservative)
            state["confidence"] = min(state["confidence"], agent_confidence)
        
        logger.info(f"{self.name} confidence: {agent_confidence:.2f}, overall: {state['confidence']:.2f}")
