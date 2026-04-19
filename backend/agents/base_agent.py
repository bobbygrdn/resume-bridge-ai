"""
BaseAgent defines the interface for all LLM-powered agents in Resume Bridge AI.
All agents should inherit from this class and implement the async run() method.
"""
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    async def run(self, *args, **kwargs):
        """Run the agent's main logic."""
        pass
