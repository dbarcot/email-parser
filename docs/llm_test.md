# llm_test.py

Test Azure OpenAI configuration and connection.

## Overview

`llm_test.py` is a diagnostic tool that verifies your Azure OpenAI setup before running the email filter. It tests credentials, connectivity, and model functionality with a sample email.

**Use this tool:** Before running `llm_email_filter.py` to catch configuration issues early.

## What It Tests

1. ✓ `.env` file exists and is readable
2. ✓ All required environment variables are set
3. ✓ Azure OpenAI client can be created
4. ✓ Network connectivity to Azure endpoint
5. ✓ Model deployment is accessible
6. ✓ API can analyze a sample vacation email
7. ✓ JSON response parsing works
8. ✓ Token usage tracking works
9. ✓ Cost calculation is correct

## Usage

```bash
python llm_test.py
```

No parameters required. The tool automatically loads configuration from `.env`.

## Example Output

### Successful Test

```
================================================================================
AZURE OPENAI CONNECTION TEST
================================================================================

STEP 1: Testing .env configuration
[✓] .env file found
[✓] AZURE_OPENAI_ENDPOINT: https://your-resource.openai.azure.com/
[✓] AZURE_OPENAI_API_KEY: sk-proj-abc...xyz1
[✓] AZURE_OPENAI_DEPLOYMENT: gpt-4o-mini
[✓] AZURE_OPENAI_API_VERSION: 2024-02-15-preview
[✓] Pricing: $0.15/1M input, $0.60/1M output
[✓] All required environment variables are set

STEP 2: Testing Azure OpenAI connection
[✓] Azure OpenAI client created successfully

STEP 3: Testing LLM analysis with sample vacation email
[✓] LLM Response received successfully!

--- LLM Analysis Result ---
Decision: MATCH
Confidence: 95.00%
Reasoning: Clear vacation notification with specific dates and alternative contact information

--- Token Usage ---
Input tokens:  245
Output tokens: 28
Total tokens:  273

--- Cost ---
This request:  $0.000054 USD
Est. per 1000 emails: $0.05 USD

================================================================================
✓✓✓ ALL TESTS PASSED ✓✓✓
================================================================================

Your Azure OpenAI configuration is working correctly!
You can now run llm_email_filter.py with confidence.
```

### Failed Test (Missing .env)

```
================================================================================
AZURE OPENAI CONNECTION TEST
================================================================================

STEP 1: Testing .env configuration
[ERROR] .env file not found in current directory

Create .env file with:
  cp .env.example .env
  # Edit .env with your Azure OpenAI credentials

================================================================================
✗✗✗ TESTS FAILED ✗✗✗
================================================================================
```

### Failed Test (Wrong Credentials)

```
================================================================================
AZURE OPENAI CONNECTION TEST
================================================================================

STEP 1: Testing .env configuration
[✓] .env file found
[✓] AZURE_OPENAI_ENDPOINT: https://your-resource.openai.azure.com/
[✓] AZURE_OPENAI_API_KEY: sk-proj-abc...xyz1
[✓] AZURE_OPENAI_DEPLOYMENT: gpt-4o-mini
[✓] All required environment variables are set

STEP 2: Testing Azure OpenAI connection
[✓] Azure OpenAI client created successfully

STEP 3: Testing LLM analysis with sample vacation email
[✗] LLM API call failed!

Error: Error code: 401 - {'error': {'code': '401', 'message': 'Unauthorized. Access token is missing, invalid, expired, or revoked.'}}

================================================================================
✗✗✗ TESTS FAILED ✗✗✗
================================================================================

Troubleshooting:
1. Check AZURE_OPENAI_API_KEY in .env
2. Verify key is copied correctly from Azure Portal
3. Ensure key hasn't expired
4. Check if resource is active in Azure
```

## Test Email Sample

The tool sends this Czech vacation email to test the API:

```
From: jan.novak@firma.cz
Date: Mon, 15 Jan 2024 10:30:00 +0100
Subject: Re: OOO

Dobrý den,

budu na dovolené od 15.1. do 30.1.2024.
V případě naléhavosti mě kontaktujte na mobilu nebo se obraťte na kolegu Petra.

S pozdravem,
Jan Novák
```

This tests:
- Czech character encoding (ď, é, á)
- Date pattern matching
- Alternative contact detection

## Common Issues

### Issue: "openai package not installed"

```
[ERROR] openai package not installed.
Install with: pip install openai
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: ".env file not found"

**Solution:**
```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### Issue: "Missing environment variables"

```
[✗] AZURE_OPENAI_ENDPOINT: NOT SET
[✗] AZURE_OPENAI_API_KEY: NOT SET
```

**Solution:** Edit `.env` and add all required variables:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Issue: "Deployment not found"

```
Error: Error code: 404 - {'error': {'code': 'DeploymentNotFound', 'message': 'The API deployment for this resource does not exist.'}}
```

**Solution:** Check deployment name in Azure Portal:
1. Go to Azure OpenAI Studio
2. Navigate to Deployments
3. Copy exact deployment name
4. Update `AZURE_OPENAI_DEPLOYMENT` in `.env`

### Issue: "Invalid endpoint"

```
Error: Error code: 404 - Not Found
```

**Solution:** Verify endpoint format:
- Correct: `https://your-resource.openai.azure.com/`
- Include `https://`
- Include trailing `/`
- Use your actual resource name

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure resource endpoint | `https://myresource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | API key from Azure Portal | Get from "Keys and Endpoint" section |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o-mini` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` |
| `AZURE_OPENAI_REASONING_EFFORT` | For thinking models: `minimal`/`medium`/`high` | Not set |
| `AZURE_OPENAI_TEMPERATURE` | Response randomness (0.0-1.0) | Model default |
| `AZURE_OPENAI_PRICE_INPUT` | Input token price per 1M tokens | `0.15` |
| `AZURE_OPENAI_PRICE_OUTPUT` | Output token price per 1M tokens | `0.60` |

## What The Tool Checks

### Step 1: Configuration
- File existence
- Variable presence
- Basic format validation

### Step 2: Connection
- Azure OpenAI client initialization
- No actual API call yet

### Step 3: Functionality
- Send sample email to API
- Parse JSON response
- Calculate token usage
- Compute cost estimate

## Cost Estimate Formula

```
Input cost = (input_tokens / 1,000,000) × AZURE_OPENAI_PRICE_INPUT
Output cost = (output_tokens / 1,000,000) × AZURE_OPENAI_PRICE_OUTPUT
Total cost = Input cost + Output cost

Per 1000 emails = Total cost × 1000
```

## When to Run This Tool

- **Before first use** - Verify setup is correct
- **After changing .env** - Test new credentials
- **After Azure changes** - Verify deployment still works
- **Troubleshooting** - Diagnose API issues
- **Cost planning** - Estimate token usage and costs

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | Tests failed |

Use in scripts:

```bash
if python llm_test.py; then
    echo "Configuration OK, proceeding..."
    python llm_email_filter.py ...
else
    echo "Configuration failed, fix .env first"
    exit 1
fi
```

## Related Tools

- **[llm_email_filter.py](llm_email_filter.md)** - Main email filtering tool
- **[.env.example](../.env.example)** - Configuration template

## See Also

- [LLM Email Filter Guide](llm_email_filter.md)
- [Project README](../README.md)
