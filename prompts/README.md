# LLM Prompts for Email Classification

This directory contains prompt templates for the LLM-based email filter (`llm_email_filter.py`).

## Directory Structure

```
prompts/
├── README.md           # This file
├── vacation/           # Vacation/OOO specific prompts (default)
│   ├── system.txt     # System prompt for vacation detection
│   └── user.txt       # User prompt for vacation analysis
└── general/            # Generalized prompts for any use case
    ├── system.txt     # General system prompt template
    └── user.txt       # General user prompt template
```

## Prompt Types

### Vacation/OOO Prompts (`vacation/`)
Specialized prompts optimized for detecting vacation and out-of-office responses. These prompts are configured to identify:
- Automated OOO replies
- Manual absence notifications
- Sick leave messages
- Parental leave notices
- General work absence communications

**Use case:** Legal discovery for vacation/absence documentation

### General Prompts (`general/`)
Generic prompt templates that can be customized for any email classification task. These provide a flexible framework for:
- Custom keyword matching
- Domain-specific content detection
- Compliance filtering
- Any pattern-based email analysis

**Use case:** Customize for your specific needs

## Usage

### With Vacation Prompts (Default)
```bash
python llm_email_filter.py \
  --input-dir ./emails \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./filtered_results \
  --log-file ./filter_log.csv
```

### With General Prompts (Customizable)
```bash
python llm_email_filter.py \
  --input-dir ./emails \
  --system-prompt ./prompts/general/system.txt \
  --user-prompt ./prompts/general/user.txt \
  --output-dir ./filtered_results \
  --log-file ./filter_log.csv
```

### Creating Custom Prompts
1. Copy the `general/` directory to a new name (e.g., `legal-terms/`)
2. Edit `system.txt` to define your classification criteria
3. Edit `user.txt` to specify analysis requirements
4. Use your custom prompts with `--system-prompt` and `--user-prompt`

## Prompt Files

### `system.txt`
Defines the LLM's role and classification framework:
- Role definition (what the LLM is supposed to do)
- True positive vs false positive criteria
- Confidence scoring guidelines
- Response format (JSON structure)

### `user.txt`
Specifies the analysis criteria for each email:
- Detailed analysis steps
- Contextual evaluation guidelines
- Red flags for false positives
- Conservative classification instructions

## Tips

1. **Be Specific**: The more specific your criteria, the better the results
2. **Conservative Classification**: Default to false positives rather than false negatives
3. **Test Iteratively**: Test with small batches (--email-limit) and refine prompts
4. **Cost Control**: Use `gpt-4o-mini` for cost-effective classification
5. **Confidence Thresholds**: Review low-confidence matches manually
