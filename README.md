# MBOX Email Parser

General-purpose toolkit for extracting and filtering emails from MBOX files based on customizable search patterns.

## 🎯 What This Project Does

This toolkit helps you extract specific emails from large MBOX archives using pattern matching and AI-powered filtering. Designed for legal case processing, compliance auditing, and content discovery.

**Primary use case:** Extract vacation/OOO emails from mailbox archives with high accuracy

**Other use cases:** Any keyword-based email search (legal terms, compliance keywords, project-specific content)

## ✨ Key Features

- **Customizable pattern matching** - Default: 60+ vacation/OOO keywords (Czech & English)
- **AI-powered false positive filtering** - Uses Azure OpenAI to reduce false matches
- **Complete email preservation** - Saves full EML files with attachments
- **Robust charset handling** - Works with Czech, English, and mixed encodings
- **Legal case ready** - CSV logging, reproducible extraction, audit trails
- **Production tested** - Handles large archives (100K+ emails)

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate test data
python create_test_mbox.py

# 3. Test extraction (should find 6 matches)
python mbox_email_parser.py --mbox test_emails.mbox --email jan.novak@firma.cz --dry-run

# 4. Extract from real archive
python mbox_email_parser.py --mbox your_archive.mbox --email target@email.com --output ./results
```

See **[QUICKSTART.md](QUICKSTART.md)** for detailed getting started guide.

## 🛠️ Tools

### Core Tools

#### 1. **mbox_email_parser.py** - Email Extraction
Extract emails from MBOX files using regex pattern matching.

```bash
python mbox_email_parser.py --mbox archive.mbox --email person@company.com
```

**[→ Full Documentation](docs/mbox_email_parser.md)**

**Key features:**
- Customizable search patterns
- Filter by email address (From/To/Cc/Reply-To)
- Saves complete EML files with attachments
- CSV logging with match details
- Dry-run mode for testing

---

#### 2. **llm_email_filter.py** - AI-Powered Filtering
Filter false positives using Azure OpenAI LLM analysis.

```bash
python llm_email_filter.py \
  --input-dir ./results \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./filtered \
  --log-file ./filter.csv
```

**[→ Full Documentation](docs/llm_email_filter.md)**

**Key features:**
- Azure OpenAI integration (gpt-4o-mini recommended)
- Confidence scoring (0-100%)
- Real-time cost tracking (~$0.09 per 1000 emails)
- Customizable prompts for any classification task
- Separates matched/rejected/failed emails

---

#### 3. **llm_test.py** - Azure OpenAI Testing
Test your Azure OpenAI configuration before processing.

```bash
python llm_test.py
```

**[→ Full Documentation](docs/llm_test.md)**

**Verifies:**
- .env configuration
- Azure credentials
- Model deployment
- API connectivity
- Cost estimation

### Utility Tools

#### 4. **mbox_attachment_extractor.py** - Attachment-Based Extraction
Extract emails by attachment name patterns.

**[→ Full Documentation](docs/mbox_attachment_extractor.md)**

---

#### 5. **eml_to_mbox.py** - EML to MBOX Conversion
Convert extracted EML files back to MBOX format.

```bash
python eml_to_mbox.py --input "./results/*.eml" --output archive.mbox
```

**[→ Full Documentation](docs/eml_to_mbox.md)**

---

#### 6. **create_test_mbox.py** - Test Data Generator
Generate sample MBOX file for testing and validation.

```bash
python create_test_mbox.py
```

**[→ Full Documentation](docs/create_test_mbox.md)**

## 📖 Documentation

### Getting Started
- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Search Patterns](search_patterns.txt)** - Customize keyword matching
- **[LLM Prompts Guide](prompts/README.md)** - Customize AI filtering

### Tool Documentation
- **[mbox_email_parser.py](docs/mbox_email_parser.md)** - Email extraction guide
- **[llm_email_filter.py](docs/llm_email_filter.md)** - AI filtering guide
- **[llm_test.py](docs/llm_test.md)** - Azure OpenAI testing
- **[mbox_attachment_extractor.py](docs/mbox_attachment_extractor.md)** - Attachment extraction
- **[eml_to_mbox.py](docs/eml_to_mbox.md)** - EML conversion utility
- **[create_test_mbox.py](docs/create_test_mbox.md)** - Test data generator

## 💼 Common Workflows

### Workflow 1: Basic Extraction (Pattern Matching Only)

```bash
# Extract emails matching patterns
python mbox_email_parser.py \
  --mbox archive.mbox \
  --email person@company.com \
  --output ./extracted
```

**Result:** All emails matching search patterns (may include false positives)

---

### Workflow 2: High-Accuracy Extraction (Pattern + AI Filtering)

```bash
# Step 1: Extract with patterns
python mbox_email_parser.py \
  --mbox archive.mbox \
  --email person@company.com \
  --output ./extracted

# Step 2: Filter with AI
python llm_email_filter.py \
  --input-dir ./extracted \
  --system-prompt ./prompts/vacation/system.txt \
  --user-prompt ./prompts/vacation/user.txt \
  --output-dir ./filtered \
  --log-file ./filter.csv
```

**Result:** High-accuracy matches in `./filtered/matched/` directory

---

### Workflow 3: Custom Pattern Search

```bash
# Create custom patterns
cat > legal_terms.txt << 'EOF'
\bcontract
\bagreement
\blawsuit
\bconfidential
EOF

# Extract with custom patterns
python mbox_email_parser.py \
  --mbox archive.mbox \
  --patterns legal_terms.txt \
  --output ./legal_matches
```

## 🔧 Installation

### Requirements
- Python 3.7+
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `beautifulsoup4>=4.12.0` - HTML email parsing
- `openai>=1.0.0` - Azure OpenAI integration (for LLM filtering)
- `python-dotenv>=1.0.0` - Environment configuration (for LLM filtering)
- `tqdm>=4.65.0` - Progress bars

### Azure OpenAI Setup (Optional, for LLM Filtering)

1. Copy configuration template:
```bash
cp .env.example .env
```

2. Edit `.env` with your Azure credentials:
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

3. Test connection:
```bash
python llm_test.py
```

## 📊 Performance

| Archive Size | Emails | Extraction Time | LLM Filtering |
|--------------|--------|-----------------|---------------|
| Small | 1,000 | ~30 seconds | ~7 minutes ($0.09) |
| Medium | 10,000 | ~5 minutes | ~70 minutes ($0.90) |
| Large | 100,000 | ~45 minutes | ~700 minutes ($9.00) |

**Notes:**
- Extraction time depends on HTML ratio and disk speed
- LLM filtering cost based on gpt-4o-mini pricing
- Process in batches for better control

## 🤝 Support

- **Issues:** Check tool-specific documentation in [docs/](docs/)
- **Questions:** See [QUICKSTART.md](QUICKSTART.md) for common scenarios
- **Troubleshooting:** Each tool doc includes troubleshooting section

## 📝 Version

**Current Version:** 2.0
**Status:** Production Ready
**License:** Internal Use

**Major Changes in v2.0:**
- Generalized from vacation-specific to customizable patterns
- Added AI-powered filtering with Azure OpenAI
- Restructured documentation
- Added customizable prompt system

---

**🎊 Start extracting!** See [QUICKSTART.md](QUICKSTART.md) to get started.
