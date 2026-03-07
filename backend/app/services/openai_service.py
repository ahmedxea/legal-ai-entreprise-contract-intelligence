"""
OpenAI service for Azure OpenAI API calls
"""
from openai import AzureOpenAI
import logging
from typing import List, Dict, Any, Optional
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with Azure OpenAI"""
    
    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        
        self.client = None
        if self.endpoint and self.api_key:
            try:
                self.client = AzureOpenAI(
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    api_version=self.api_version
                )
                logger.info("Azure OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI: {e}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Get a chat completion from Azure OpenAI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            Response content as string
        """
        if not self.client:
            logger.warning("OpenAI client not initialized, returning mock response")
            return self._mock_response(messages)
        
        try:
            kwargs = {
                "model": self.deployment_name,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Log token usage
            logger.info(f"Tokens used: {response.usage.total_tokens}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}", exc_info=True)
            raise
    
    async def structured_extraction(
        self,
        prompt: str,
        context: str,
        schema: Dict
    ) -> Dict:
        """
        Extract structured data using JSON mode
        
        Args:
            prompt: System prompt describing extraction task
            context: Contract text to extract from
            schema: JSON schema describing expected output
            
        Returns:
            Extracted data as dictionary
        """
        messages = [
            {
                "role": "system",
                "content": f"{prompt}\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
            },
            {
                "role": "user",
                "content": context
            }
        ]
        
        response = await self.chat_completion(
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            return {}
    
    async def get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not self.client:
            logger.warning("OpenAI client not initialized, returning mock embedding")
            return [0.0] * 1536
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
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
        
        return "This is a mock response. Azure OpenAI is not configured."


# Global instance
openai_service = OpenAIService()
