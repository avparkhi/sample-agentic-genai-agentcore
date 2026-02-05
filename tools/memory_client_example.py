"""
Example implementation of AgentCore Memory client (OPTIONAL)

This file shows how to implement memory_client.py if you want to enable
AWS Bedrock AgentCore Memory integration. If this file doesn't exist,
the orchestrator will work fine without memory features.

To enable memory:
1. Rename this file to memory_client.py
2. Install: pip install bedrock-agentcore
3. Configure AWS credentials with Bedrock access
4. Set environment variables (see below)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Environment variables for memory configuration
MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID", "campaign-orchestrator-memory")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")


class MemoryClient:
    """
    Wrapper for AWS Bedrock AgentCore Memory
    
    This provides a simplified interface for storing and retrieving
    campaign context across sessions.
    """
    
    def __init__(self, memory_id: str, region: str = "us-west-2"):
        """
        Initialize memory client
        
        Args:
            memory_id: Unique identifier for the memory store
            region: AWS region for Bedrock service
        """
        try:
            # Import bedrock-agentcore (optional dependency)
            from bedrock_agentcore.memory import Memory
            
            self.memory = Memory(
                memory_id=memory_id,
                region_name=region
            )
            self.memory_id = memory_id
            logger.info(f"AgentCore Memory initialized: {memory_id}")
        except ImportError:
            raise ImportError(
                "bedrock-agentcore not installed. "
                "Install with: pip install bedrock-agentcore"
            )
        except Exception as e:
            logger.error(f"Failed to initialize AgentCore Memory: {e}")
            raise
    
    def retrieve(self, query: str, max_results: int = 5, **kwargs) -> str:
        """
        Retrieve relevant context from memory
        
        Args:
            query: Search query (e.g., campaign content)
            max_results: Maximum number of results to return
            **kwargs: Additional parameters for memory retrieval
        
        Returns:
            Retrieved context as string
        """
        try:
            results = self.memory.retrieve(
                memory_id=self.memory_id,
                query=query,
                max_results=max_results,
                **kwargs
            )
            
            if results:
                # Format results into readable context
                context_parts = []
                for i, result in enumerate(results, 1):
                    context_parts.append(f"Context {i}:\n{result}")
                return "\n\n".join(context_parts)
            else:
                return ""
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
            return ""
    
    def store(self, content: str, metadata: dict = None, **kwargs) -> bool:
        """
        Store content in memory
        
        Args:
            content: Content to store
            metadata: Optional metadata dictionary
            **kwargs: Additional parameters for memory storage
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.memory.store(
                memory_id=self.memory_id,
                content=content,
                metadata=metadata or {},
                **kwargs
            )
            logger.info(f"Stored content in memory: {len(content)} chars")
            return True
        except Exception as e:
            logger.warning(f"Memory storage failed: {e}")
            return False


# Global memory client instance
_memory_client: Optional[MemoryClient] = None


def get_memory_client() -> MemoryClient:
    """
    Get or create the global memory client instance
    
    Returns:
        MemoryClient instance
    
    Raises:
        ImportError: If bedrock-agentcore not installed
        Exception: If memory initialization fails
    """
    global _memory_client
    
    if _memory_client is None:
        _memory_client = MemoryClient(
            memory_id=MEMORY_ID,
            region=AWS_REGION
        )
    
    return _memory_client


def initialize_memory() -> str:
    """
    Initialize memory and return memory_id
    
    Returns:
        Memory ID string
    
    Raises:
        ImportError: If bedrock-agentcore not installed
        Exception: If memory initialization fails
    """
    client = get_memory_client()
    return client.memory_id


# Example usage
if __name__ == "__main__":
    # Test memory client
    try:
        client = get_memory_client()
        
        # Store test content
        client.store(
            content="Test campaign review for EA Sports FC",
            metadata={
                "campaign_id": "test_001",
                "franchise": "EA Sports FC",
                "type": "test"
            }
        )
        
        # Retrieve test content
        results = client.retrieve(
            query="EA Sports FC campaign",
            max_results=3
        )
        
        print(f"Retrieved context:\n{results}")
        
    except ImportError as e:
        print(f"Memory not available: {e}")
        print("To enable memory, install: pip install bedrock-agentcore")
    except Exception as e:
        print(f"Memory test failed: {e}")
