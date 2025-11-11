#!/usr/bin/env python3
"""
Azure OpenAI Connection Test
=============================
Simple test script to verify Azure OpenAI configuration and connection.

Usage:
  python llm_test.py

This will:
- Load .env configuration
- Test Azure OpenAI connection
- Send a test vacation email for analysis
- Show token usage and cost
- Report success or detailed errors

Author: Claude
Version: 1.3
"""

import os
import sys
import json

# Check dependencies
try:
    from dotenv import load_dotenv
except ImportError:
    print("[ERROR] python-dotenv not installed.")
    print("Install with: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import AzureOpenAI
except ImportError:
    print("[ERROR] openai package not installed.")
    print("Install with: pip install openai")
    sys.exit(1)

# Test email example
TEST_EMAIL = """From: jan.novak@firma.cz
Date: Mon, 15 Jan 2024 10:30:00 +0100
Subject: Re: OOO

Dobrý den,

budu na dovolené od 15.1. do 30.1.2024.
V případě naléhavosti mě kontaktujte na mobilu nebo se obraťte na kolegu Petra (petr@firma.cz).

S pozdravem,
Jan Novák"""

SYSTEM_PROMPT = """You are an expert email analyzer. Determine if the email below is a genuine vacation/out-of-office response.

Respond with JSON only:
{"is_vacation_response": true/false, "confidence": 0.95, "reasoning": "brief explanation"}"""

USER_PROMPT = """Analyze this email and determine if it's a genuine vacation auto-response or absence notification.

EMAIL TO ANALYZE:
"""

def test_env_loading():
    """Test .env file loading."""
    print("\n" + "=" * 80)
    print("STEP 1: Testing .env configuration")
    print("=" * 80)

    if not os.path.exists('.env'):
        print("[ERROR] .env file not found in current directory")
        print("\nCreate .env file with:")
        print("  cp .env.example .env")
        print("  # Edit .env with your Azure OpenAI credentials")
        return False

    print("[✓] .env file found")

    # Load .env
    if not load_dotenv():
        print("[WARN] Failed to load .env file")

    # Check required variables
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"[✗] {var}: NOT SET")
        else:
            # Mask API key for security
            if 'KEY' in var:
                display_value = value[:10] + '...' + value[-4:]
            else:
                display_value = value
            print(f"[✓] {var}: {display_value}")

    if missing_vars:
        print(f"\n[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
        return False

    # Optional pricing variables
    price_input = os.getenv('AZURE_OPENAI_PRICE_INPUT', '0.15')
    price_output = os.getenv('AZURE_OPENAI_PRICE_OUTPUT', '0.60')
    print(f"[✓] Pricing: ${price_input}/1M input, ${price_output}/1M output")

    return True

def test_openai_connection():
    """Test Azure OpenAI connection."""
    print("\n" + "=" * 80)
    print("STEP 2: Testing Azure OpenAI connection")
    print("=" * 80)

    # Get configuration
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

    print(f"Connecting to: {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: {api_version}")

    # Create client
    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        print("[✓] Azure OpenAI client created successfully")
        return client, deployment
    except Exception as e:
        print(f"[ERROR] Failed to create Azure OpenAI client: {e}")
        return None, None

def test_llm_analysis(client, deployment):
    """Test LLM analysis with sample email."""
    print("\n" + "=" * 80)
    print("STEP 3: Testing LLM analysis with sample vacation email")
    print("=" * 80)

    print("\n--- Test Email ---")
    print(TEST_EMAIL)
    print("--- End of Test Email ---\n")

    print("Sending to LLM for analysis...")

    # Get optional reasoning effort (for thinking models like gpt-5-nano)
    reasoning_effort = os.getenv('AZURE_OPENAI_REASONING_EFFORT', 'minimal')

    # Get optional temperature (thinking models only support default value of 1)
    temperature_str = os.getenv('AZURE_OPENAI_TEMPERATURE', '')
    temperature = float(temperature_str) if temperature_str else None

    try:
        # Prepare API call parameters
        api_params = {
            "model": deployment,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT + TEST_EMAIL}
            ],
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 500
        }

        # Add temperature if set (thinking models like gpt-5-nano only support default)
        if temperature is not None:
            api_params["temperature"] = temperature
            print(f"Using temperature: {temperature}")

        # Add reasoning_effort if set (for thinking models like gpt-5-nano)
        if reasoning_effort:
            api_params["reasoning_effort"] = reasoning_effort
            print(f"Using reasoning_effort: {reasoning_effort}")

        # Send request
        response = client.chat.completions.create(**api_params)

        # Extract response
        content = response.choices[0].message.content
        result = json.loads(content)

        # Token usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        # Calculate cost
        price_input = float(os.getenv('AZURE_OPENAI_PRICE_INPUT', '0.15'))
        price_output = float(os.getenv('AZURE_OPENAI_PRICE_OUTPUT', '0.60'))
        cost = (input_tokens / 1_000_000 * price_input) + (output_tokens / 1_000_000 * price_output)

        print("\n[✓] LLM Response received successfully!\n")

        # Display results
        print("--- LLM Analysis Result ---")
        print(f"Decision: {'VACATION RESPONSE' if result.get('is_vacation_response') else 'NOT VACATION RESPONSE'}")
        print(f"Confidence: {result.get('confidence', 0):.2%}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        print("\n--- Token Usage ---")
        print(f"Input tokens:  {input_tokens:,}")
        print(f"Output tokens: {output_tokens:,}")
        print(f"Total tokens:  {total_tokens:,}")
        print(f"\n--- Cost ---")
        print(f"This request:  ${cost:.6f} USD")
        print(f"Est. per 1000 emails: ${cost * 1000:.2f} USD")
        print("--- End of Analysis ---\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] LLM analysis failed: {e}")
        print("\nPossible issues:")
        print("- Invalid API key or expired credentials")
        print("- Deployment name doesn't exist or is not accessible")
        print("- Network connectivity issues")
        print("- API endpoint is incorrect")
        print("- Rate limiting or quota exceeded")
        return False

def main():
    """Main test function."""
    print("\n" + "=" * 80)
    print("AZURE OPENAI CONNECTION TEST")
    print("=" * 80)
    print("\nThis script will test your Azure OpenAI configuration.")
    print("Make sure you have a .env file with your credentials.\n")

    # Step 1: Test .env loading
    if not test_env_loading():
        print("\n" + "=" * 80)
        print("TEST FAILED: Configuration issues")
        print("=" * 80)
        sys.exit(1)

    # Step 2: Test OpenAI connection
    client, deployment = test_openai_connection()
    if not client:
        print("\n" + "=" * 80)
        print("TEST FAILED: Connection issues")
        print("=" * 80)
        sys.exit(1)

    # Step 3: Test LLM analysis
    if not test_llm_analysis(client, deployment):
        print("\n" + "=" * 80)
        print("TEST FAILED: LLM analysis issues")
        print("=" * 80)
        sys.exit(1)

    # Success!
    print("=" * 80)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("=" * 80)
    print("\nYour Azure OpenAI configuration is working correctly!")
    print("You can now run llm_vacation_filter.py with confidence.\n")
    print("Next steps:")
    print("1. Prepare your prompts in prompts/system.txt and prompts/user.txt")
    print("2. Run vacation_email_extractor.py to extract candidate emails")
    print("3. Run llm_vacation_filter.py to filter with LLM")
    print("\n")

    sys.exit(0)

if __name__ == '__main__':
    main()
