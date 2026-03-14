"""
Ollama service for local AI inference using Microsoft Phi-3 Mini
Gracefully degrades to mock mode when Ollama/models are unavailable (e.g., Azure F1 tier)
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

# Conditional imports - graceful fallback for Azure deployment
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() == "true"


def _int_env(name: str, default: int) -> int:
    """Read an integer env var with a safe fallback."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default

try:
    if MOCK_MODE:
        raise ImportError("Mock mode enabled, skipping ollama import")
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama package not available - running in mock mode")

try:
    if MOCK_MODE:
        raise ImportError("Mock mode enabled, skipping sentence_transformers import")
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None
    logger.warning("sentence-transformers not available - using mock embeddings")


class OllamaService:
    """Service for interacting with local Ollama models"""
    
    def __init__(self, model_name: str = "phi3", embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model_name = embedding_model
        self.mock_mode = MOCK_MODE or not OLLAMA_AVAILABLE
        self.request_timeout_seconds = _int_env("OLLAMA_REQUEST_TIMEOUT_SECONDS", 120)
        self.structured_max_tokens = _int_env("OLLAMA_STRUCTURED_MAX_TOKENS", 300)
        
        if self.mock_mode:
            logger.info("OllamaService running in MOCK MODE (no AI inference)")
            self.embedding_model = None
            return
        
        # Initialize embedding model
        try:
            if EMBEDDINGS_AVAILABLE:
                logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info("Embedding model loaded successfully")
            else:
                self.embedding_model = None
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            self.embedding_model = None
        
        # Test Ollama connection
        try:
            ollama.list()
            logger.info(f"Ollama connected, using model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama: {e}")
            self.mock_mode = True
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Get a chat completion from Ollama
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            Response content as string
        """
        try:
            # If in mock mode, return mock response immediately
            if self.mock_mode:
                return self._mock_response(messages)
            
            # Build options
            options = {
                "temperature": temperature,
            }
            
            if max_tokens:
                options["num_predict"] = max_tokens
            
            # If JSON format requested, add instruction to system message
            if response_format and response_format.get("type") == "json_object":
                # Ensure there's a system message emphasizing JSON
                if not any(msg.get("role") == "system" for msg in messages):
                    messages.insert(0, {
                        "role": "system",
                        "content": "You are a helpful assistant that responds with valid JSON only. Do not include any text before or after the JSON."
                    })
                else:
                    # Add JSON instruction to existing system message
                    for msg in messages:
                        if msg.get("role") == "system":
                            msg["content"] += "\n\nIMPORTANT: You must respond with valid JSON only. Do not include any text before or after the JSON."
                            break
            
            # Call Ollama (sync library — run in thread to avoid blocking the event loop)
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    ollama.chat,
                    model=self.model_name,
                    messages=messages,
                    options=options,
                    format="json" if response_format and response_format.get("type") == "json_object" else None,
                ),
                timeout=self.request_timeout_seconds,
            )
            
            content = response.get("message", {}).get("content", "")
            
            # Log metrics
            if "eval_count" in response:
                logger.info(f"Tokens generated: {response.get('eval_count', 0)}")
            
            return content
            
        except asyncio.TimeoutError:
            logger.error(
                f"Ollama request timed out after {self.request_timeout_seconds}s "
                f"(model={self.model_name})"
            )
            return self._mock_response(messages)
        except Exception as e:
            logger.error(f"Error in chat completion: {e}", exc_info=True)
            # Return mock response for gracefuldegradation
            return self._mock_response(messages)
    
    async def structured_extraction(
        self,
        prompt: str,
        context: str,
        schema: Dict,
        max_tokens: Optional[int] = None,
    ) -> Dict:
        """
        Extract structured data using JSON mode
        
        Args:
            prompt: System prompt describing extraction task
            context: Contract text to extract from
            schema: JSON schema describing expected output
            max_tokens: Optional output token cap to prevent runaway responses
            
        Returns:
            Extracted data as dictionary
        """
        messages = [
            {
                "role": "system",
                "content": f"{prompt}\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}\n\nIMPORTANT: Return ONLY the JSON object, no other text."
            },
            {
                "role": "user",
                "content": context
            }
        ]
        
        response = await self.chat_completion(
            messages=messages,
            temperature=0.0,
            max_tokens=max_tokens or self.structured_max_tokens,
            response_format={"type": "json_object"}
        )
        
        try:
            # Clean up response (remove markdown code blocks if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            # Try to extract JSON from response
            try:
                # Find first { and last }
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except:
                pass
            return {}
    
    async def get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for text using sentence-transformers
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not self.embedding_model:
            logger.warning("Embedding model not initialized, returning mock embedding")
            return [0.0] * 384  # multilingual-e5-small dimension
        
        try:
            # Get embeddings (sync call — run in thread)
            embedding = await asyncio.to_thread(
                self.embedding_model.encode, text, convert_to_numpy=True
            )
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return [0.0] * 384
    
    async def analyze_with_guidance(
        self,
        system_prompt: str,
        content: str,
        temperature: float = 0.3,
        max_tokens: int = 4000
    ) -> str:
        """
        Analyze content with guidance
        
        Args:
            system_prompt: System prompt with instructions
            content: Content to analyze
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Analysis result
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def _mock_response(self, messages: List[Dict]) -> str:
        """Return a mock response for testing"""
        last_message = messages[-1]["content"]
        
        if "extract" in last_message.lower():
            return json.dumps({
                "parties": ["Company A", "Company B"],
                "key_dates": [{"date_type": "Effective Date", "date": "2026-01-01"}],
                "financial_terms": [{"description": "Payment", "amount": 100000, "currency": "QAR"}]
            })
        
        return "This is a mock response. Ollama is not available."


# Global instance
ollama_service = OllamaService()
