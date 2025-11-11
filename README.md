# Email Parser Tools

Suite of tools for extracting and filtering vacation/OOO related emails from mbox files for legal case processing.

## Tools

1. **vacation_email_extractor.py** - Extract vacation/OOO emails from mbox files using regex patterns
2. **llm_vacation_filter.py** - Filter false positives using Azure OpenAI LLM analysis
3. **llm_test.py** - Test Azure OpenAI connection and configuration
4. **eml_to_mbox.py** - Convert EML files to MBOX format

## Funkce

- ✅ Prohledává celé textové tělo emailu (plain text + HTML)
- ✅ Filtruje podle emailové adresy v From/To/Cc/Reply-To
- ✅ Detekuje české i anglické vacation/OOO keywords
- ✅ Ukládá kompletní emaily jako EML (včetně příloh)
- ✅ Collision handling s incrementálním suffixem
- ✅ Charset fallback (cp1250 → utf-8 → latin1)
- ✅ CSV logging s detaily
- ✅ Graceful Ctrl+C handling
- ✅ Dry-run mode pro testování
- ✅ Email limit pro částečné zpracování

## Instalace

### 1. Python Requirements

Vyžaduje Python 3.7+

```bash
# Instalace dependencies
pip install -r requirements.txt
```

### 2. Ověření instalace

```bash
python vacation_email_extractor.py --help
```

## Použití

### Základní použití

```bash
python vacation_email_extractor.py --mbox archive.mbox --email jan.novak@firma.cz
```

### Pokročilé použití

```bash
# S vlastním output adresářem
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --output ./results

# Dry run (pouze spočítat matches)
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --dry-run

# Zpracovat pouze prvních 100 emailů
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --email-limit 100

# Všechny parametry dohromady
python vacation_email_extractor.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --output ./legal_case_001 \
    --log-file case_001_log.csv \
    --email-limit 1000
```

## Parametry

### Povinné

- `--mbox PATH` - Cesta k mbox souboru
- `--email EMAIL` - Cílový email (case-insensitive)

### Volitelné

- `--output DIR` - Output adresář (default: `./output`)
- `--email-limit N` - Zpracovat max N emailů
- `--dry-run` - Pouze spočítat matches, neukládat soubory
- `--log-file PATH` - Cesta k CSV logu (default: `extraction_log.csv`)

## Output struktura

```
output/
├── 20240115_143022_jan.novak_abc123_dovolen.eml
├── 20240128_091544_petr.svoboda_xyz456_nemocenska.eml
├── 20240203_162315_marie.nova_def789_ooo_001.eml  ← collision suffix
└── failed/
    ├── failed_email_0001.eml  ← nedekódovatelné emaily
    └── failed_email_0002.eml

extraction_log.csv  ← Detailní log všech matchů
```

## CSV Log formát

Log obsahuje následující sloupce:

| Sloupec | Popis |
|---------|-------|
| `filename` | Skutečný název uloženého souboru |
| `original_filename` | Původně generovaný název |
| `collision` | TRUE/FALSE - byla kolize? |
| `date` | Datum emailu |
| `from` | Odesílatel |
| `to` | Příjemce |
| `subject` | Předmět |
| `matched_keywords` | Nalezené klíčová slova |
| `match_positions` | Pozice matchů v textu |

## Detekované keywords

Script detekuje tyto typy vacation/OOO zpráv:

### České výrazy
- Dovolená, dov., čerpám dovolenou
- Prázdniny
- Volno
- Nepřítomen, nepřítomnost
- Mimo kancelář, mimo provoz
- Nemocenská, PN, pracovní neschopnost
- Zdravotní volno
- Absence
- Nedostupný
- Rodičovská, mateřská, otcovská
- Vrátím se, budu zpět
- K dispozici, k zastižení

### Anglické výrazy
- Vacation, holiday
- Out of office, OOO
- Sick leave, sick day
- Time off, PTO
- Unavailable, away
- Autoreply, automatic reply

### Časové fráze
- Od 15.5., do 31.8.
- Až do pondělí
- Vrátím 1.6.

## Troubleshooting

### Problem: "BeautifulSoup not installed"

```bash
pip install beautifulsoup4
```

### Problem: Velký mbox soubor (10GB+)

```bash
# Zpracuj po částech s --email-limit
python vacation_email_extractor.py --mbox huge.mbox --email jan@firma.cz --email-limit 10000
# Pak pokračuj od místa přerušení (zatím není implementováno - bude v v2.0)
```

### Problem: Script běží pomalu

HTML emaily jsou pomalé na konverzi. Pokud není potřeba HTML konverze:
- Odinstaluj BeautifulSoup - script bude rychlejší ale méně přesný

### Problem: Charset errors i s fallbackem

Velmi vzácné - pokud se stane:
1. Email se uloží do `failed/` složky
2. Můžeš ho ručně otevřít v email klientovi
3. Script pokračuje dál

## Progress tracking

Script vypisuje progress každých 100 emailů:

```
Processed: 1,200 | Matches: 23 | Failed: 2
Processed: 1,300 | Matches: 25 | Failed: 2
```

## Ctrl+C handling

Script lze kdykoliv bezpečně přerušit Ctrl+C:

```
^C
[!] Ctrl+C detected - graceful shutdown...
Processed: 1,247
Matches:   24
Failed:    2

Partial results saved.
```

Všechny doposud zpracované emaily jsou uložené.

## Známá omezení

1. **Deduplikace**: Script nedetekuje duplicitní emaily (by design - pro legal case)
2. **Resume**: Nelze pokračovat od místa přerušení (plánováno v2.0)
3. **Multiprocessing**: Single-threaded processing (pro jednoduchost a bezpečnost)
4. **Velké přílohy**: Emaily s velmi velkými přílohami (100MB+) mohou být pomalé

## Best practices pro legal cases

### 1. Vždy použij dry-run nejdřív

```bash
# Zjisti počet matchů bez ukládání
python vacation_email_extractor.py --mbox archive.mbox --email jan@firma.cz --dry-run
```

### 2. Uchovej originální mbox

Nikdy nepřepisuj originální mbox soubor!

### 3. Dokumentuj parametry

```bash
# Vytvoř script pro reprodukovatelnost
cat > extract_case_001.sh << 'EOF'
#!/bin/bash
python vacation_email_extractor.py \
    --mbox /path/to/archive.mbox \
    --email subject@firma.cz \
    --output ./case_001_results \
    --log-file case_001_extraction.csv
EOF
chmod +x extract_case_001.sh
```

### 4. Ověř výsledky

```bash
# Zkontroluj CSV log
head -n 20 extraction_log.csv

# Zkontroluj počet souborů
ls -la output/*.eml | wc -l

# Otevři pár náhodných EML v Outlook/Thunderbird
```

## Technické detaily

### Encoding handling

1. Script používá deklarovaný charset z email headeru
2. Pokud selže → fallback na cp1250 (Windows Czech)
3. Pokud selže → fallback na utf-8
4. Pokud selže → fallback na latin1 (nikdy neselže)

### HTML konverze

- BeautifulSoup odstraňuje `<script>` a `<style>` tagy
- Extrahuje jen viditelný text
- Zachovává mezery mezi elementy

### Filename sanitization

- Odstraňuje neplatné znaky pro Windows: `< > : " / \ | ? *`
- Maximální délka: 255 znaků
- Collision handling: `_001`, `_002`, atd.

## Výkon

Typické časy zpracování:

- **Malý mbox** (1,000 emailů): ~30 sekund
- **Střední mbox** (10,000 emailů): ~5 minut
- **Velký mbox** (100,000 emailů): ~45 minut

*Závisí na velikosti emailů, počtu HTML emailů a rychlosti disku.*

---

# LLM Vacation Filter

## Overview

`llm_vacation_filter.py` uses Azure OpenAI to analyze emails extracted by `vacation_email_extractor.py` and filter out false positives. It provides LLM-powered analysis to distinguish genuine vacation/absence responses from casual mentions of vacation in regular correspondence.

## Features

- ✅ Azure OpenAI integration (gpt-4o-mini recommended)
- ✅ Analyzes immediate reply only (filters quoted email history)
- ✅ Structured JSON responses with confidence scores
- ✅ Confidence prefix in output filenames for easy sorting
- ✅ Separates matched/rejected/failed emails into subdirectories
- ✅ Real-time token usage and cost tracking
- ✅ Detailed CSV log + JSON summary report
- ✅ Retry logic with failure tracking
- ✅ Graceful Ctrl+C handling
- ✅ .env configuration for API credentials

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_PRICE_INPUT=0.15
AZURE_OPENAI_PRICE_OUTPUT=0.60
```

### 3. Test Your Connection

Before processing emails, test your Azure OpenAI configuration:

```bash
python llm_test.py
```

**This will verify:**
- ✓ .env file exists and is properly configured
- ✓ All required environment variables are set
- ✓ Azure OpenAI connection works
- ✓ Model deployment is accessible
- ✓ API can analyze a sample vacation email
- ✓ Token usage and cost calculation works

**Example output:**
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
Decision: VACATION RESPONSE
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

**If test fails, check:**
- .env file exists in current directory
- All credentials are correct (copy from Azure Portal)
- Deployment name matches your Azure OpenAI deployment
- API endpoint URL is complete and correct
- Network connectivity to Azure

### 4. Prepare Prompts

Example prompts are provided in `prompts/` directory:
- `prompts/system.txt` - System instructions for the LLM
- `prompts/user.txt` - Analysis criteria and guidelines

You can customize these prompts for your specific use case.

## Usage

### Basic Usage

```bash
python llm_vacation_filter.py \
  --input-dir ./vacation_emails \
  --system-prompt ./prompts/system.txt \
  --user-prompt ./prompts/user.txt \
  --output-dir ./filtered_results \
  --log-file ./filter_log.csv
```

### Test with Limited Emails

```bash
python llm_vacation_filter.py \
  --input-dir ./vacation_emails \
  --system-prompt ./prompts/system.txt \
  --user-prompt ./prompts/user.txt \
  --output-dir ./test_results \
  --log-file ./test_log.csv \
  --email-limit 10
```

### Debug Mode

Use `--debug` to see exactly what text is being sent to the LLM:

```bash
python llm_vacation_filter.py \
  --input-dir ./vacation_emails \
  --system-prompt ./prompts/system.txt \
  --user-prompt ./prompts/user.txt \
  --output-dir ./test_results \
  --log-file ./test_log.csv \
  --email-limit 5 \
  --debug
```

**Debug output shows:**
- Email filename and headers (From, Date, Subject)
- Full body length vs. immediate reply length
- Exact text being sent to LLM (truncated to 500 chars for display)
- Whether text will be truncated to 4000 chars

**Example debug output:**
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
- ✓ Only immediate reply is extracted (no quoted history)
- ✓ Email is from the correct sender
- ✓ Text length is reasonable (not too short/long)
- ✓ Czech characters are decoded correctly

## Parameters

### Required

- `--input-dir DIR` - Directory with EML files from vacation_email_extractor.py
- `--system-prompt FILE` - Path to system prompt file (must exist)
- `--user-prompt FILE` - Path to user prompt file (must exist)
- `--output-dir DIR` - Output directory for filtered results
- `--log-file FILE` - CSV log file path

### Optional

- `--email-limit N` - Process maximum N emails (for testing)
- `--debug` - Show debug output including extracted reply text before sending to LLM

## Output Structure

```
output-dir/
├── matched/
│   ├── 95_20240115_143022_jan.novak_abc123_dovolen.eml
│   ├── 88_20240128_091544_petr.svoboda_xyz456_nemocenska.eml
│   └── 72_20240203_162315_marie.nova_def789_ooo.eml
├── rejected/
│   ├── 15_20240210_103045_false_positive.eml
│   └── 08_20240215_140022_not_vacation.eml
├── failed/
│   ├── failed_20240220_broken_email.eml
│   └── failed_20240221_api_error.eml
└── filter_report.json
```

### Filename Format

All output files include a confidence score prefix (00-99):

```
{confidence}_{original_filename}.eml

Examples:
95_email.eml  → 95% confidence
72_email.eml  → 72% confidence
08_email.eml  → 8% confidence
```

**Benefits:**
- Easy sorting by confidence in file explorer
- Quick visual identification of borderline cases
- Simple pattern filtering: `ls 9*_*.eml` shows 90%+ confidence

## Output Files

### CSV Log (filter_log.csv)

Detailed per-email results:

| Column | Description |
|--------|-------------|
| `filename` | Original EML filename |
| `processed_at` | Processing timestamp |
| `llm_decision` | true/false/error |
| `confidence` | Confidence score (0.0-1.0) |
| `reasoning` | LLM explanation |
| `prompt_tokens` | Input tokens used |
| `completion_tokens` | Output tokens used |
| `total_tokens` | Total tokens |
| `processing_time_ms` | Processing time in milliseconds |
| `error_message` | Error details (if any) |
| `retried` | Whether retry was attempted |
| `from_address` | Email sender |
| `subject` | Email subject |
| `output_filename` | Output filename with confidence prefix |

### JSON Report (filter_report.json)

Summary statistics:

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
    "input_dir": "./vacation_emails",
    "system_prompt": "./prompts/system.txt",
    "user_prompt": "./prompts/user.txt",
    "output_dir": "./filtered_results",
    "model": "gpt-4o-mini",
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

## Real-time Status Display

During processing:

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

### Step 1: Extract vacation emails with regex

```bash
python vacation_email_extractor.py \
  --mbox archive.mbox \
  --email jan.novak@firma.cz \
  --output ./vacation_emails
```

Result: 500 potential vacation emails extracted

### Step 2: Filter with LLM

```bash
python llm_vacation_filter.py \
  --input-dir ./vacation_emails \
  --system-prompt ./prompts/system.txt \
  --user-prompt ./prompts/user.txt \
  --output-dir ./filtered_results \
  --log-file ./filter_log.csv
```

Result:
- ✓ 45 genuine vacation responses (matched/)
- ✗ 453 false positives (rejected/)
- ⚠ 2 processing errors (failed/)

### Step 3: Review results

```bash
# Review high-confidence matches (90%+)
ls filtered_results/matched/9*_*.eml

# Review borderline cases (60-80%)
ls filtered_results/matched/[6-8]*_*.eml

# Check rejected emails with high confidence scores (might be errors)
ls filtered_results/rejected/9*_*.eml
```

## Cost Estimation

### gpt-4o-mini Pricing (Recommended)

- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Typical costs per email:**
- Average email: ~300 input tokens, ~50 output tokens
- Cost per email: ~$0.00009 USD
- 1,000 emails: ~$0.09 USD
- 10,000 emails: ~$0.90 USD

### Other Models

| Model | Input (per 1M) | Output (per 1M) | Cost per 1000 emails |
|-------|----------------|-----------------|---------------------|
| gpt-4o-mini | $0.15 | $0.60 | $0.09 |
| gpt-4o | $2.50 | $10.00 | $1.25 |
| gpt-4-turbo | $10.00 | $30.00 | $4.50 |

## Error Handling

### Retry Logic

- API errors: Retry once automatically
- Network errors: Retry once with 2-second delay
- Parsing errors: Log and move to failed/

### Failed Emails

Failed emails are saved to `output-dir/failed/` with reasons logged in CSV.

Common failure reasons:
- API timeout
- Invalid EML format
- Malformed response from LLM
- Token limit exceeded (>4000 chars)

## Troubleshooting

### Error: "AZURE_OPENAI_ENDPOINT not set"

**Solution:** Create `.env` file in current directory with Azure OpenAI configuration.

```bash
cp .env.example .env
# Edit .env with your credentials
```

### Error: "System prompt file not found"

**Solution:** Prompt files must exist. Use example prompts:

```bash
# Files should exist:
prompts/system.txt
prompts/user.txt
```

### High cost / Many tokens used

**Solutions:**
1. Use gpt-4o-mini instead of gpt-4 (15x cheaper)
2. Shorten prompts (reduce system/user prompt length)
3. Email body is truncated to 4000 chars automatically
4. Test with `--email-limit 10` first

### Low accuracy / Many false positives

**Solutions:**
1. Adjust prompts in `prompts/system.txt` and `prompts/user.txt`
2. Lower confidence threshold when reviewing results
3. Review borderline cases (60-80% confidence) manually
4. Add examples to prompts for better guidance

### Slow processing

**Current speed:** ~2-3 emails/second

**Improvement options:**
1. Use gpt-4o-mini (faster than gpt-4)
2. Run on multiple directories in parallel manually
3. Future: async processing (not yet implemented)

## Ctrl+C Handling

Script can be interrupted safely at any time:

```
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

All processed emails are saved. Resume by processing remaining files only.

## Best Practices

### 1. Always test with limited emails first

```bash
# Test with 10 emails
python llm_vacation_filter.py ... --email-limit 10
```

### 2. Review confidence scores

- 90-100%: Very likely correct
- 70-89%: Likely correct, spot-check a few
- 50-69%: Review manually
- 0-49%: Likely incorrect

### 3. Customize prompts for your use case

Edit `prompts/system.txt` and `prompts/user.txt` to:
- Add specific keywords for your domain
- Include example emails
- Adjust confidence thresholds
- Add language-specific guidance

### 4. Monitor costs

Check `filter_report.json` after each run:

```bash
cat filtered_results/filter_report.json | grep cost
```

### 5. Backup original emails

Always keep original emails from `vacation_email_extractor.py`:

```bash
cp -r vacation_emails vacation_emails_backup
```

## Limitations

1. **Sequential processing**: Processes one email at a time (async not yet implemented)
2. **Token limits**: Very long emails truncated to 4000 chars
3. **Cost**: Processes using paid API (estimate ~$0.09 per 1000 emails with gpt-4o-mini)
4. **No resume**: Cannot resume interrupted sessions (process remaining files manually)

## Changelog

### v1.0 (2025-11-11)
- Initial release
- Azure OpenAI integration
- Confidence-based filename prefixes
- Real-time token and cost tracking
- CSV and JSON logging
- Retry logic with failure tracking
- Graceful Ctrl+C handling

---

## Podpora

Pro bug reporty a feature requesty kontaktujte vývojáře.

## Project Changelog

### vacation_email_extractor.py v1.0 (2025-11-08)
- Initial release
- Kompletní Czech + English keyword detection
- Collision handling
- Charset fallback
- HTML to text conversion
- CSV logging
- Ctrl+C handling
- Dry-run mode

### llm_test.py v1.0 (2025-11-11)
- Initial release
- Test Azure OpenAI connection and configuration
- Verify .env settings
- Send sample vacation email for analysis
- Show token usage and cost estimates
- Provide clear success/failure diagnostics

### llm_vacation_filter.py v1.1 (2025-11-11)
- Add --debug flag to show extracted reply text before sending to LLM
- Verify immediate reply extraction is working correctly

### llm_vacation_filter.py v1.0 (2025-11-11)
- Initial release
- Azure OpenAI integration
- Confidence-based filename prefixes
- Real-time token and cost tracking
- CSV and JSON logging
- Retry logic with failure tracking
- Graceful Ctrl+C handling

## License

Pro interní použití.
