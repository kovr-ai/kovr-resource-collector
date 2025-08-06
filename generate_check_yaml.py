#!/usr/bin/env python3
"""
Basic LLM Client Usage Example

This example demonstrates how to use the LLM client with AWS Bedrock
to generate compliance check logic from NIST control requirements.

The client will automatically use the dev-kovr AWS profile unless
explicit credentials are provided in the environment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from con_mon.utils.llm import get_llm_client, BedrockModel
from con_mon.utils.config import settings


def main():
    """Demonstrate basic LLM client usage."""
    print("🚀 LLM Client Basic Usage Example")
    print("=" * 50)
    
    try:
        # Get the singleton LLM client
        llm = get_llm_client()
        
        print(f"✅ LLM Client initialized")
        print(f"   Using profile: {settings.AWS_PROFILE}")
        print(f"   Model: {settings.BEDROCK_MODEL_ID}")
        print()
        
        # Example 1: Simple text generation
        print("📝 Example 1: Simple Text Generation")
        print("-" * 40)
        
        response = llm.generate_text(
            prompt="Explain what NIST 800-53 AC-2 control is about in one sentence.",
            max_tokens=100,
            temperature=0.1
        )
        
        print(f"Response: {response.content}")
        print(f"Tokens: {response.input_tokens} in → {response.output_tokens} out")
        print(f"Time: {response.response_time:.2f}s")
        print()
        
        # Example 2: Generate compliance check logic
        print("🔧 Example 2: Generate Compliance Check Logic")
        print("-" * 40)
        
        control_text = """
        AC-2 ACCOUNT MANAGEMENT
        a. Define and document the types of accounts allowed and specifically prohibited for use within the system;
        b. Assign account managers;
        c. Require [Assignment: organization-defined prerequisites and criteria] for group and role membership;
        d. Specify authorized users of the system, group and role membership, and access authorizations for each account;
        """
        
        check_logic = llm.generate_check_logic(
            control_text=control_text,
            control_name="AC-2",
            resource_type="github",
            context="Focus on GitHub organization user management and access controls"
        )
        
        print("Generated Check Logic:")
        print("```python")
        print(check_logic)
        print("```")
        print()
        
        print("✅ Examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("1. Ensure AWS profile 'dev-kovr' is configured")
        print("2. Check Bedrock service access in your AWS account")
        print("3. Verify model permissions in Bedrock console")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 