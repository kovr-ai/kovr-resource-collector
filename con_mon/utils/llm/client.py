"""
LLM Client for AWS Bedrock

This module provides a singleton client for interacting with AWS Bedrock's
large language models. It handles authentication, request formatting, and
response parsing, but delegates prompt management to separate classes.

Key Features:
- Singleton pattern ensures single instance across application
- Support for multiple Bedrock models (Claude, Llama, etc.)
- Configurable parameters (temperature, max tokens, etc.)
- Error handling and retry logic
- Thread-safe implementation
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

from con_mon.utils.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class BedrockModel(Enum):
    """Supported Bedrock model identifiers."""
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    LLAMA2_13B = "meta.llama2-13b-chat-v1"
    LLAMA2_70B = "meta.llama2-70b-chat-v1"
    LLAMA3_8B = "meta.llama3-8b-instruct-v1:0"
    LLAMA3_70B = "meta.llama3-70b-instruct-v1:0"


@dataclass
class LLMRequest:
    """Request object for LLM operations."""
    prompt: str
    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None


@dataclass
class LLMResponse:
    """Response object from LLM operations."""
    content: str
    model_id: str
    usage: Dict[str, int]
    stop_reason: str
    raw_response: Dict[str, Any]


class LLMClient:
    """
    Singleton client for AWS Bedrock LLM operations.
    
    This client handles the low-level Bedrock API interactions and provides
    a simple interface for generating text responses from prompts.
    """
    
    _instance: Optional['LLMClient'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls) -> 'LLMClient':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LLMClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._setup_client()
                    self._initialized = True
    
    def _setup_client(self):
        """Set up the Bedrock client with proper configuration."""
        try:
            # Configure boto3 client with retry and timeout settings
            config = Config(
                region_name=settings.BEDROCK_REGION,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                read_timeout=settings.BEDROCK_TIMEOUT,
                connect_timeout=60
            )
            
            # Check if we have meaningful AWS credentials (not just empty strings)
            has_credentials = (
                settings.AWS_ACCESS_KEY_ID and 
                settings.AWS_SECRET_ACCESS_KEY and 
                settings.AWS_ACCESS_KEY_ID.strip() != "" and 
                settings.AWS_SECRET_ACCESS_KEY.strip() != ""
            )
            
            if has_credentials:
                # Use explicit credentials
                session = boto3.Session(
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logger.info(f"✅ Using explicit AWS credentials for Bedrock client")
            else:
                # Use AWS profile
                try:
                    session = boto3.Session(profile_name=settings.AWS_PROFILE)
                    logger.info(f"✅ Using AWS profile: {settings.AWS_PROFILE}")
                except ProfileNotFound as e:
                    logger.error(f"❌ AWS profile '{settings.AWS_PROFILE}' not found: {e}")
                    raise
            
            # Create Bedrock client
            self.client = session.client('bedrock-runtime', config=config)
            
            logger.info(f"✅ Bedrock client initialized successfully")
            logger.info(f"   Region: {settings.BEDROCK_REGION}")
            logger.info(f"   Default Model: {settings.BEDROCK_MODEL_ID}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bedrock client: {str(e)}")
            raise
    
    def _format_request_body(self, request: LLMRequest) -> str:
        """Format the request body based on the model type."""
        model_id = request.model_id or settings.BEDROCK_MODEL_ID
        
        if "anthropic.claude" in model_id:
            # Claude format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": request.max_tokens or settings.BEDROCK_MAX_TOKENS,
                "temperature": request.temperature or settings.BEDROCK_TEMPERATURE,
                "top_p": request.top_p or settings.BEDROCK_TOP_P,
                "messages": [
                    {
                        "role": "user",
                        "content": request.prompt
                    }
                ]
            }
            
            if request.stop_sequences:
                body["stop_sequences"] = request.stop_sequences
                
        elif "meta.llama" in model_id:
            # Llama format
            body = {
                "prompt": request.prompt,
                "max_gen_len": request.max_tokens or settings.BEDROCK_MAX_TOKENS,
                "temperature": request.temperature or settings.BEDROCK_TEMPERATURE,
                "top_p": request.top_p or settings.BEDROCK_TOP_P,
            }
            
        else:
            raise ValueError(f"Unsupported model: {model_id}")
        
        return json.dumps(body)
    
    def _parse_response(self, response_body: str, model_id: str) -> LLMResponse:
        """Parse the response body based on the model type."""
        response_data = json.loads(response_body)
        
        if "anthropic.claude" in model_id:
            # Claude response format
            content = response_data.get("content", [{}])[0].get("text", "")
            usage = response_data.get("usage", {})
            stop_reason = response_data.get("stop_reason", "unknown")
            
        elif "meta.llama" in model_id:
            # Llama response format
            content = response_data.get("generation", "")
            usage = {
                "input_tokens": response_data.get("prompt_token_count", 0),
                "output_tokens": response_data.get("generation_token_count", 0)
            }
            stop_reason = response_data.get("stop_reason", "unknown")
            
        else:
            raise ValueError(f"Unsupported model for response parsing: {model_id}")
        
        return LLMResponse(
            content=content,
            model_id=model_id,
            usage=usage,
            stop_reason=stop_reason,
            raw_response=response_data
        )
    
    def generate_response(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            request: LLMRequest object containing prompt and parameters
            
        Returns:
            LLMResponse object containing the generated content
            
        Raises:
            ClientError: If the Bedrock API call fails
            ValueError: If the model is not supported
        """
        model_id = request.model_id or settings.BEDROCK_MODEL_ID
        
        try:
            # Format request body
            body = self._format_request_body(request)
            
            # Make API call
            logger.debug(f"🔄 Making Bedrock API call with model: {model_id}")
            start_time = time.time()
            
            response = self.client.invoke_model(
                body=body,
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse response
            response_body = response.get('body').read().decode('utf-8')
            llm_response = self._parse_response(response_body, model_id)
            
            logger.info(f"✅ LLM response generated successfully")
            logger.info(f"   Model: {model_id}")
            logger.info(f"   Duration: {duration:.2f}s")
            logger.info(f"   Input tokens: {llm_response.usage.get('input_tokens', 0)}")
            logger.info(f"   Output tokens: {llm_response.usage.get('output_tokens', 0)}")
            
            return llm_response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"❌ Bedrock API error [{error_code}]: {error_message}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in LLM generation: {str(e)}")
            raise
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Simple text generation method.
        
        Args:
            prompt: Text prompt to send to the LLM
            **kwargs: Additional parameters (model_id, max_tokens, temperature, etc.)
            
        Returns:
            Generated text content
        """
        request = LLMRequest(
            prompt=prompt,
            model_id=kwargs.get('model_id'),
            max_tokens=kwargs.get('max_tokens'),
            temperature=kwargs.get('temperature'),
            top_p=kwargs.get('top_p'),
            stop_sequences=kwargs.get('stop_sequences')
        )
        
        response = self.generate_response(request)
        return response.content
    
    def test_connection(self) -> bool:
        """
        Test the Bedrock connection with a simple prompt.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            test_prompt = "Hello, please respond with 'Connection successful'"
            response = self.generate_text(test_prompt, max_tokens=50)
            logger.info(f"✅ Bedrock connection test successful")
            logger.debug(f"   Test response: {response[:100]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Bedrock connection test failed: {str(e)}")
            return False


# Global singleton instance
_llm_client: Optional[LLMClient] = None
_client_lock = threading.Lock()


def get_llm_client() -> LLMClient:
    """
    Get the singleton LLM client instance.
    
    Returns:
        LLMClient singleton instance
    """
    global _llm_client
    
    if _llm_client is None:
        with _client_lock:
            if _llm_client is None:
                _llm_client = LLMClient()
    
    return _llm_client 