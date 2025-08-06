"""
LLM Singleton Class for AWS Bedrock Integration

This module provides a singleton class for interacting with AWS Bedrock's large language models.
It handles authentication, request formatting, and response parsing for various Bedrock models.

Key Features:
- Singleton pattern ensures single instance across application
- Support for multiple Bedrock models (Claude, Llama, etc.)
- Configurable parameters (temperature, max tokens, etc.)
- Error handling and retry logic
- Thread-safe implementation
- Type-safe request/response handling

Example:
    >>> from con_mon.utils.llm import LLMClient
    >>> llm = LLMClient()
    >>> response = llm.generate_text("Explain NIST 800-53 AC-2 control")
    >>> print(response.content)
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from con_mon.utils.config import settings


logger = logging.getLogger(__name__)


class BedrockModel(Enum):
    """Supported Bedrock model identifiers."""
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    CLAUDE_3_OPUS = "anthropic.claude-3-opus-20240229-v1:0"
    CLAUDE_3_5_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    LLAMA_2_70B = "meta.llama2-70b-chat-v1"
    LLAMA_3_70B = "meta.llama3-70b-instruct-v1:0"


@dataclass
class LLMResponse:
    """Response object from LLM API calls."""
    content: str
    model_id: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    response_time: float
    raw_response: Dict[str, Any]


@dataclass
class LLMRequest:
    """Request object for LLM API calls."""
    prompt: str
    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    system_prompt: Optional[str] = None


class LLMClient:
    """
    Singleton client for AWS Bedrock LLM interactions.
    
    This class provides a thread-safe singleton implementation for interacting
    with AWS Bedrock's large language models. It handles authentication,
    request formatting, response parsing, and error handling.
    
    Attributes:
        _instance: Singleton instance
        _lock: Thread lock for singleton creation
        _bedrock_client: Boto3 Bedrock Runtime client
        _default_model: Default model to use for requests
    """
    
    _instance: Optional['LLMClient'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'LLMClient':
        """Create or return existing singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM client (only once for singleton)."""
        if self._initialized:
            return
            
        self._initialized = True
        self._bedrock_client = None
        self._default_model = settings.BEDROCK_MODEL_ID
        self._setup_client()
        
        logger.info(f"LLM Client initialized with model: {self._default_model}")
    
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
            
            # Create session with configured AWS profile or explicit credentials
            if has_credentials:
                session_kwargs = {
                    'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
                    'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
                }
                logger.info("Using explicit AWS credentials from settings")
            else:
                session_kwargs = {'profile_name': settings.AWS_PROFILE}
                logger.info(f"Using AWS profile: {settings.AWS_PROFILE}")
            
            try:
                session = boto3.Session(**session_kwargs)
                self._bedrock_client = session.client('bedrock-runtime', config=config)
                
                profile_info = f"profile '{settings.AWS_PROFILE}'" if 'profile_name' in session_kwargs else "explicit credentials"
                logger.info(f"Bedrock client configured for region: {settings.BEDROCK_REGION} using {profile_info}")
                
            except Exception as session_error:
                if 'profile_name' in session_kwargs:
                    logger.error(f"Failed to create session with profile '{settings.AWS_PROFILE}': {session_error}")
                    logger.info("Available profiles can be found in ~/.aws/credentials or ~/.aws/config")
                    logger.info("To create the profile, run: aws configure --profile dev-kovr")
                raise session_error
            
        except Exception as e:
            logger.error(f"Failed to setup Bedrock client: {str(e)}")
            raise
    
    def _format_claude_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Format request for Claude models."""
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
        
        if request.system_prompt:
            body["system"] = request.system_prompt
        
        if request.stop_sequences:
            body["stop_sequences"] = request.stop_sequences
            
        return body
    
    def _format_llama_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Format request for Llama models."""
        prompt = f"<s>[INST] {request.prompt} [/INST]"
        if request.system_prompt:
            prompt = f"<s>[INST] <<SYS>>\n{request.system_prompt}\n<</SYS>>\n\n{request.prompt} [/INST]"
        
        body = {
            "prompt": prompt,
            "max_gen_len": request.max_tokens or settings.BEDROCK_MAX_TOKENS,
            "temperature": request.temperature or settings.BEDROCK_TEMPERATURE,
            "top_p": request.top_p or settings.BEDROCK_TOP_P,
        }
        
        return body
    
    def _parse_claude_response(self, response_body: Dict[str, Any], model_id: str, response_time: float) -> LLMResponse:
        """Parse response from Claude models."""
        content = ""
        if "content" in response_body and response_body["content"]:
            content = response_body["content"][0].get("text", "")
        
        return LLMResponse(
            content=content,
            model_id=model_id,
            input_tokens=response_body.get("usage", {}).get("input_tokens", 0),
            output_tokens=response_body.get("usage", {}).get("output_tokens", 0),
            stop_reason=response_body.get("stop_reason", "unknown"),
            response_time=response_time,
            raw_response=response_body
        )
    
    def _parse_llama_response(self, response_body: Dict[str, Any], model_id: str, response_time: float) -> LLMResponse:
        """Parse response from Llama models."""
        content = response_body.get("generation", "")
        
        return LLMResponse(
            content=content,
            model_id=model_id,
            input_tokens=response_body.get("prompt_token_count", 0),
            output_tokens=response_body.get("generation_token_count", 0),
            stop_reason=response_body.get("stop_reason", "unknown"),
            response_time=response_time,
            raw_response=response_body
        )
    
    def generate_text(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate text using the specified Bedrock model.
        
        Args:
            prompt: The input prompt for text generation
            model_id: Bedrock model ID to use (defaults to configured model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Top-p sampling parameter
            stop_sequences: List of sequences to stop generation
            system_prompt: System prompt for models that support it
            
        Returns:
            LLMResponse: Generated text and metadata
            
        Raises:
            ClientError: AWS Bedrock API errors
            ValueError: Invalid parameters
            RuntimeError: Client setup or connection issues
        """
        if not self._bedrock_client:
            raise RuntimeError("Bedrock client not initialized")
        
        # Create request object
        request = LLMRequest(
            prompt=prompt,
            model_id=model_id or self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            system_prompt=system_prompt
        )
        
        try:
            start_time = time.time()
            
            # Format request based on model type
            if "anthropic.claude" in request.model_id:
                body = self._format_claude_request(request)
            elif "meta.llama" in request.model_id:
                body = self._format_llama_request(request)
            else:
                raise ValueError(f"Unsupported model: {request.model_id}")
            
            # Make API call
            response = self._bedrock_client.invoke_model(
                modelId=request.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_time = time.time() - start_time
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if "anthropic.claude" in request.model_id:
                return self._parse_claude_response(response_body, request.model_id, response_time)
            elif "meta.llama" in request.model_id:
                return self._parse_llama_response(response_body, request.model_id, response_time)
            raise ValueError(f"Unsupported model: {request.model_id}")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock API error [{error_code}]: {error_message}")
            raise
        
        except BotoCoreError as e:
            logger.error(f"Boto3 error: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in generate_text: {str(e)}")
            raise
    
    def generate_check_logic(
        self,
        control_text: str,
        control_name: str,
        resource_type: str = "github",
        context: Optional[str] = None
    ) -> str:
        """
        Generate compliance check logic for a given control.
        
        Args:
            control_text: The full NIST control requirement text
            control_name: Control identifier (e.g., "AC-2")
            resource_type: Target resource type ("github", "aws", etc.)
            context: Additional context for check generation
            
        Returns:
            str: Generated Python code for the compliance check
        """
        system_prompt = f"""You are an expert in cybersecurity compliance and automation. 
        Generate Python code for compliance checks that validate {resource_type} resources against NIST controls.
        
        The code should:
        1. Be practical and implementable
        2. Check specific technical configurations
        3. Return boolean results (True for compliant, False for non-compliant)
        4. Include clear comments explaining the logic
        5. Handle edge cases and errors gracefully
        
        Focus on automated, technical checks rather than policy or procedural requirements."""
        
        prompt = f"""Generate a compliance check for NIST control {control_name}.

Control Requirements:
{control_text}

Target Resource Type: {resource_type}
{f"Additional Context: {context}" if context else ""}

Generate Python code that can be used in a custom_logic field to validate compliance with this control.
The code should work with fetched resource data and set a 'result' variable to True/False."""
        
        response = self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,  # Low temperature for consistent code generation
            max_tokens=2048
        )
        
        return response.content
    
    def analyze_control_requirements(self, control_text: str, control_name: str) -> Dict[str, Any]:
        """
        Analyze a control's requirements to extract key information for check generation.
        
        Args:
            control_text: The full NIST control requirement text
            control_name: Control identifier (e.g., "AC-2")
            
        Returns:
            Dict containing analysis results with keys:
            - technical_requirements: List of technical requirements
            - automation_feasibility: Assessment of automation potential
            - suggested_checks: List of suggested check types
            - resource_types: Relevant resource types for implementation
        """
        system_prompt = """You are an expert in cybersecurity compliance analysis. 
        Analyze NIST control requirements and provide structured information for automated compliance checking."""
        
        prompt = f"""Analyze NIST control {control_name} and provide a structured analysis.

Control Text:
{control_text}

Please provide a JSON response with the following structure:
{{
    "technical_requirements": ["list of specific technical requirements"],
    "automation_feasibility": "high/medium/low with explanation",
    "suggested_checks": ["list of specific automated checks that could be implemented"],
    "resource_types": ["github", "aws", "azure", etc. - which platforms this applies to"],
    "key_validation_points": ["specific things that need to be validated"],
    "implementation_notes": "guidance for implementing automated checks"
}}"""
        
        response = self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=1024
        )
        
        try:
            # Try to parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                return {"analysis": response.content}
        except json.JSONDecodeError:
            return {"analysis": response.content}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration."""
        return {
            "default_model": self._default_model,
            "region": settings.BEDROCK_REGION,
            "max_tokens": settings.BEDROCK_MAX_TOKENS,
            "temperature": settings.BEDROCK_TEMPERATURE,
            "top_p": settings.BEDROCK_TOP_P,
            "timeout": settings.BEDROCK_TIMEOUT,
            "client_initialized": self._bedrock_client is not None
        }


# Convenience function to get the singleton instance
def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    return LLMClient() 