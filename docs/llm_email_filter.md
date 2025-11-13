# llm_email_filter.py

AI-powered false positive filtering for email extraction results.

## Overview

`llm_email_filter.py` uses Azure OpenAI to analyze emails extracted by `mbox_email_parser.py` and distinguish genuine matches from false positives. It provides LLM-powered classification with customizable prompts for various use cases.

**Primary use case:** Filtering vacation/OOO emails to reduce false positives from regex matching

**Secondary use cases:** Any content classification where AI can improve on pattern matching

## Features

- ✅ **Azure OpenAI integration** - Supports gpt-4o-mini, gpt-4o, gpt-4-turbo, gpt-5-nano
- ✅ **Smart text extraction** - Analyzes immediate reply only (filters quoted email history)
- ✅ **Structured responses** - JSON output with confidence scores (0.0-1.0)
- ✅ **Confidence-based sorting** - Filename prefix (00-99) for easy visual sorting
- ✅ **Organized output** - Separate directories for matched/rejected/failed emails
- ✅ **Cost tracking** - Real-time token usage and cost monitoring
- ✅ **Comprehensive logging** - Detailed CSV log + JSON summary report
- ✅ **Retry logic** - Automatic retry on API/network errors
- ✅ **Safe interruption** - Graceful Ctrl+C handling, partial results saved
- ✅ **Customizable prompts** - Adapt for any classification task
- ✅ **.env configuration** - Secure credential management

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `openai>=1.0.0` - Azure OpenAI client
- `python-dotenv>=1.0.0` - Environment variable management

### 2. Configure Azure OpenAI

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_REASONING_EFFORT=minimal
AZURE_OPENAI_PRICE_INPUT=0.15
AZURE_OPENAI_PRICE_OUTPUT=0.60
```

**Configuration details:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure resource endpoint | `https://myresource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | API key from Azure Portal | Get from Keys and Endpoint section |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o-mini` (recommended) |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` |
| `AZURE_OPENAI_REASONING_EFFORT` | For thinking models (gpt-5-nano): `minimal`/`medium`/`high` | `minimal` (fastest) |
| `AZURE_OPENAI_PRICE_INPUT` | Input token cost per 1M tokens | `0.15` for gpt-4o-mini |
| `AZURE_OPENAI_PRICE_OUTPUT` | Output token cost per 1M tokens | `0.60` for gpt-4o-mini |

**Model recommendations:**
- **gpt-4o-mini**: Best cost/performance ratio (~$0.09 per 1000 emails)
- **gpt-4o**: Higher accuracy, 15x more expensive
- **gpt-5-nano**: Thinking model with configurable reasoning depth

### 3. Test Your Connection

Before processing emails, verify your Azure OpenAI setup:

```bash
python llm_test.py
```

**This verifies:**
- ✓ .env file exists and is valid
- ✓ All required credentials are set
- ✓ Azure OpenAI connection works
- ✓ Model deployment is accessible
- ✓ API can analyze a sample email
- ✓ Token usage and cost calculation works

**Example successful test output:**

```
================================================================================
AZURE OPENAI CONNECTION TEST
================================================================================

STEP 1: Testing .env configuration
[✓] .env file found
[✓] AZURE_OPENAI_ENDPOINT: https://your-resource.openai.azure.com/
[✓] AZURE_OPENAI_API_KEY: sk-proj-abc...xyz1
[✓] AZURE_OPENAI_DEPLOYMENT: gpt-4o-mini
[✓] Pricing: $0.15/1M input, $0.60/1M output

STEP 2: Testing Azure OpenAI connection
[✓] Azure OpenAI client created successfully

STEP 3: Testing LLM analysis with sample vacation email
[✓] LLM Response received successfully!

--- LLM Analysis Result ---
Decision: MATCH
Confidence: 95.00%
Reasoning: Clear vacation notification with dates and alternative contact

--- Token Usage ---
Input tokens:  245
Output tokens: 28
Total tokens:  273

--- Cost ---
This request:  $0.000054 USD
Est. per 1000 emails: $0.05 USD

✓✓✓ ALL TESTS PASSED ✓✓✓

Your Azure OpenAI configuration is working correctly!
```

### 4. Prepare Prompts

Prompt templates are provided in `prompts/` directory:

- **`prompts/vacation/`** - Vacation/OOO specific prompts (default)
  - `system.txt` - System instructions for vacation detection
  - `user.txt` - Analysis criteria for absence responses

- **`prompts/general/`** - Generic templates for custom use cases
  - `system.txt` - Generalized system prompt template
  - `user.txt` - Generalized analysis criteria

See [prompts/README.md](../prompts/README.md) for customization guide.

## Usage

### Basic Usage

Filter emails using vacation/OOO prompts:

```bash
python llm_email_filter.py \
  --input-dir ./output \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./filtered_results \
  --log-file ./filter_log.csv
```

### Test with Limited Emails

Always test with a small batch first:

```bash
python llm_email_filter.py \
  --input-dir ./output \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./test_results \
  --log-file ./test_log.csv \
  --email-limit 10
```

### Debug Mode

See exactly what text is being analyzed:

```bash
python llm_email_filter.py \
  --input-dir ./output \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./test_results \
  --log-file ./test_log.csv \
  --email-limit 5 \
  --debug
```

**Debug output example:**

```
================================================================================
[DEBUG] Email: 20240115_jan.novak_vacation.eml
================================================================================
From: jan.novak@firma.cz
Date: Mon, 15 Jan 2024 10:30:00 +0100
Subject: Re: Project Update

Full body length: 2,450 chars
Immediate reply length: 180 chars

--- Immediate Reply Text (sent to LLM) ---
Ahoj, budu na dovolené od 15.1. do 30.1.
V případě naléhavosti kontaktujte kolegu Petra.
Děkuji, Jan
--- End of Immediate Reply ---
```

**Use debug mode to verify:**
- ✓ Only immediate reply extracted (no quoted history)
- ✓ Email is from correct sender
- ✓ Text length is reasonable
- ✓ Czech characters decoded correctly

### Custom Prompts

Use your own classification criteria:

```bash
python llm_email_filter.py \
  --input-dir ./extracted_emails \
  --system-prompt ./my_prompts/system.txt \
  --user-prompt ./my_prompts/user.txt \
  --output-dir ./custom_results \
  --log-file ./custom_log.csv
```

## Parameters

### Required

| Parameter | Description |
|-----------|-------------|
| `--input-dir DIR` | Directory with EML files from mbox_email_parser.py |
| `--system-prompt FILE` | Path to system prompt file (defines LLM role) |
| `--user-prompt FILE` | Path to user prompt file (analysis criteria) |
| `--output-dir DIR` | Output directory for filtered results |
| `--log-file FILE` | CSV log file path |

### Optional

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--email-limit N` | Process maximum N emails (for testing) | Unlimited |
| `--debug` | Show extracted text before sending to LLM | False |

## Output Structure

```
filtered_results/
├── matched/                    # Genuine matches (LLM: true)
│   ├── 95_20240115_jan.eml   # 95% confidence
│   ├── 88_20240128_petr.eml  # 88% confidence
│   └── 72_20240203_marie.eml # 72% confidence
├── rejected/                   # False positives (LLM: false)
│   ├── 15_20240210_email.eml # 15% confidence (correctly rejected)
│   └── 08_20240215_email.eml # 8% confidence (correctly rejected)
├── failed/                     # Processing errors
│   ├── failed_20240220_api_error.eml
│   └── failed_20240221_timeout.eml
├── filter_log.csv             # Detailed per-email log
└── filter_report.json         # Summary statistics
```

### Filename Format

All output files include confidence score prefix (00-99):

```
{confidence}_{original_filename}.eml

Examples:
95_email.eml  → 95% confidence (very likely correct)
72_email.eml  → 72% confidence (likely correct)
08_email.eml  → 8% confidence (likely incorrect)
```

**Benefits:**
- Easy sorting by confidence in file explorer
- Quick visual identification of borderline cases
- Simple filtering: `ls matched/9*_*.eml` shows 90%+ confidence

## Output Files

### CSV Log (filter_log.csv)

Detailed results for every processed email:

| Column | Description |
|--------|-------------|
| `filename` | Original EML filename |
| `processed_at` | Processing timestamp |
| `llm_decision` | `true` / `false` / `error` |
| `confidence` | Confidence score (0.0-1.0) |
| `reasoning` | LLM's explanation for decision |
| `prompt_tokens` | Input tokens used |
| `completion_tokens` | Output tokens used |
| `total_tokens` | Total tokens consumed |
| `processing_time_ms` | Processing time in milliseconds |
| `error_message` | Error details (if failed) |
| `retried` | Whether retry was attempted |
| `from_address` | Email sender |
| `subject` | Email subject |
| `output_filename` | Output filename with confidence prefix |

**Example CSV rows:**

```csv
filename,processed_at,llm_decision,confidence,reasoning,prompt_tokens,completion_tokens,total_tokens,processing_time_ms,error_message,retried,from_address,subject,output_filename
20240115_jan.eml,2024-01-15T10:30:00,true,0.95,Clear vacation notification with dates,245,28,273,450,,false,jan@firma.cz,Dovolená,95_20240115_jan.eml
```

### JSON Report (filter_report.json)

Summary statistics and configuration:

```json
{
  "summary": {
    "total_processed": 150,
    "matched": 42,
    "rejected": 105,
    "failed": 3,
    "total_tokens": 57801,
    "input_tokens": 45234,
    "output_tokens": 12567,
    "total_cost_usd": 0.14,
    "processing_time_seconds": 68.5,
    "average_speed_emails_per_sec": 2.2
  },
  "configuration": {
    "input_dir": "./output",
    "system_prompt": "./prompts/vacation/system.txt",
    "user_prompt": "./prompts/vacation/user.txt",
    "output_dir": "./filtered_results",
    "model": "gpt-4o-mini",
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

## Real-Time Progress

During processing, you'll see live status updates:

```
Processing: 45/150 (30.0%) | ✓ Matched: 12 | ✗ Rejected: 31 | ⚠ Failed: 2
Tokens: 15,234 (in: 10,156, out: 5,078) | Cost: $0.05 | Speed: 2.3/s | ETA: 45s
```

## Final Summary

```
================================================================================
FILTERING COMPLETE
================================================================================
Total processed:   150
✓ Matched:         42 (28.0%) → output/matched/
✗ Rejected:        105 (70.0%) → output/rejected/
⚠ Failed:          3 (2.0%) → output/failed/

Token usage:
  Input tokens:    45,234
  Output tokens:   12,567
  Total tokens:    57,801

Cost:              $0.14 USD
Time elapsed:      68.5 seconds
Average speed:     2.2 emails/s

Log file:          ./filter_log.csv
JSON report:       ./filter_report.json
================================================================================
```

## Workflow Example

### Complete 2-Step Process

**Step 1: Extract emails with regex patterns**

```bash
python mbox_email_parser.py \
  --mbox archive.mbox \
  --email jan.novak@firma.cz \
  --output ./extracted_emails
```

Result: 500 potential vacation/OOO emails extracted

**Step 2: Filter with AI**

```bash
python llm_email_filter.py \
  --input-dir ./extracted_emails \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./filtered_results \
  --log-file ./filter_log.csv
```

Result:
- ✓ 45 genuine vacation responses (matched/)
- ✗ 453 false positives correctly rejected (rejected/)
- ⚠ 2 processing errors (failed/)

**Step 3: Review results**

```bash
# Review high-confidence matches (90%+)
ls filtered_results/matched/9*_*.eml

# Review borderline cases (60-80%) manually
ls filtered_results/matched/[6-8]*_*.eml

# Check if any rejected emails have high confidence (potential errors)
ls filtered_results/rejected/9*_*.eml
```

## Cost Estimation

### gpt-4o-mini Pricing (Recommended)

- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Typical costs per email:**
- Average email: ~300 input tokens, ~50 output tokens
- Cost per email: ~$0.00009 USD
- **1,000 emails: ~$0.09 USD**
- **10,000 emails: ~$0.90 USD**

### Model Comparison

| Model | Input (per 1M) | Output (per 1M) | Cost per 1000 emails |
|-------|----------------|-----------------|---------------------|
| gpt-4o-mini | $0.15 | $0.60 | $0.09 |
| gpt-4o | $2.50 | $10.00 | $1.25 |
| gpt-4-turbo | $10.00 | $30.00 | $4.50 |

## Error Handling

### Retry Logic

- **API errors**: Automatic retry once
- **Network errors**: Retry with 2-second delay
- **Parsing errors**: Log and move to failed/

### Failed Emails

Failed emails are saved to `output-dir/failed/` with details in CSV log.

**Common failure reasons:**
- API timeout
- Invalid EML format
- Malformed LLM response
- Text too long (>4000 chars after truncation)

## Troubleshooting

### Error: "AZURE_OPENAI_ENDPOINT not set"

**Solution:** Create `.env` file:

```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

### Error: "System prompt file not found"

**Solution:** Ensure prompt files exist:

```bash
ls prompts/vacation/system.txt
ls prompts/vacation/user.txt
```

### High Cost / Many Tokens

**Solutions:**
1. Use `gpt-4o-mini` instead of `gpt-4` (15x cheaper)
2. Shorten custom prompts (reduce token usage)
3. Test with `--email-limit 10` before full run
4. Email bodies automatically truncated to 4000 chars

### Low Accuracy / Many False Positives

**Solutions:**
1. Customize `prompts/system.txt` and `prompts/user.txt`
2. Add specific examples to prompts
3. Adjust confidence threshold when reviewing results
4. Review borderline cases (60-80%) manually
5. Check debug output to verify text extraction

### Slow Processing

**Current speed:** ~2-3 emails/second

**Improvement options:**
1. Use `gpt-4o-mini` (faster than gpt-4)
2. Process multiple directories in parallel manually
3. Set `AZURE_OPENAI_REASONING_EFFORT=minimal` for thinking models

## Ctrl+C Handling

Safe interruption at any time:

```bash
^C
[!] Ctrl+C detected - graceful shutdown...
Processed: 247
Matched:   42
Rejected:  203
Failed:    2
Tokens:    89,234
Cost:      $0.08 USD

Partial results saved.
```

All processed emails are saved. To resume, process remaining files only.

## Best Practices

### 1. Always Test with Limited Emails First

```bash
python llm_email_filter.py ... --email-limit 10
```

Check accuracy and cost before processing thousands of emails.

### 2. Review Confidence Scores

| Confidence | Interpretation | Action |
|------------|----------------|--------|
| 90-100% | Very likely correct | Trust the classification |
| 70-89% | Likely correct | Spot-check a few samples |
| 50-69% | Uncertain | Review manually |
| 0-49% | Likely incorrect | Check if rejection was correct |

### 3. Customize Prompts for Your Use Case

Edit prompts to:
- Add domain-specific keywords
- Include example emails
- Adjust confidence thresholds
- Add language-specific guidance

See [prompts/README.md](../prompts/README.md) for customization guide.

### 4. Monitor Costs

Check costs after each run:

```bash
cat filtered_results/filter_report.json | grep cost_usd
```

### 5. Backup Original Emails

Always preserve the original extraction:

```bash
cp -r extracted_emails extracted_emails_backup
```

## Known Limitations

1. **Sequential processing** - Processes one email at a time (async not yet implemented)
2. **Token limits** - Very long emails truncated to 4000 characters
3. **Cost** - Uses paid API (~$0.09 per 1000 emails with gpt-4o-mini)
4. **No automatic resume** - Must manually process remaining files after interruption

## Related Tools

- **[mbox_email_parser.py](mbox_email_parser.md)** - Extract emails by regex patterns
- **[llm_test.py](llm_test.md)** - Test Azure OpenAI configuration
- **[Prompts Guide](../prompts/README.md)** - Customize LLM analysis criteria

## See Also

- [Quick Start Guide](../QUICKSTART.md)
- [Prompts Configuration](../prompts/README.md)
- [Project README](../README.md)
