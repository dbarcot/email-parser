# mbox_email_parser.py

Extract emails from mbox files using customizable regex patterns.

## Overview

`mbox_email_parser.py` is the core email extraction tool that searches through mbox archives and extracts emails matching specified patterns. By default, it's configured for vacation/OOO detection but can be customized for any keyword-based email search.

**Primary use case:** Legal case processing, compliance auditing, content discovery

## Features

- ✅ **Full-text search** - Searches complete email body (plain text + HTML converted to text)
- ✅ **Email filtering** - Filter by email address in From/To/Cc/Reply-To headers
- ✅ **Customizable patterns** - Default: 60+ vacation/OOO keywords (Czech & English), fully customizable
- ✅ **Complete email preservation** - Saves full EML files including all attachments
- ✅ **Collision handling** - Automatic incremental suffix (_001, _002) for duplicate filenames
- ✅ **Charset fallback** - Robust encoding detection (cp1250 → utf-8 → latin1)
- ✅ **CSV logging** - Detailed log of all matches with metadata
- ✅ **Graceful interruption** - Safe Ctrl+C handling, partial results saved
- ✅ **Dry-run mode** - Test pattern matching without saving files
- ✅ **Batch processing** - Email limit for processing large archives in chunks

## Installation

### Requirements
- Python 3.7+
- BeautifulSoup4 (optional, for HTML parsing)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Verify Installation

```bash
python mbox_email_parser.py --help
```

## Usage

### Basic Usage

Extract emails matching default patterns (vacation/OOO):

```bash
python mbox_email_parser.py --mbox archive.mbox --email jan.novak@firma.cz
```

### Search All Emails (No Email Filter)

Search patterns across all emails without filtering by address:

```bash
python mbox_email_parser.py --mbox archive.mbox
```

### Custom Output Directory

```bash
python mbox_email_parser.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --output ./case_2024_001
```

### Dry Run (Count Matches Only)

Test without saving any files:

```bash
python mbox_email_parser.py \
    --mbox archive.mbox \
    --email jan.novak@firma.cz \
    --dry-run
```

**Sample Output:**
```
==================================================
MBOX EMAIL PARSER v2.0
==================================================
[*] Loaded 60 patterns from search_patterns.txt

[*] Opening mbox file: archive.mbox
[*] Target email: jan.novak@firma.cz
[*] Filter mode: From/To/Cc/Reply-To fields
[*] Output dir: ./output
[*] DRY RUN MODE - no files will be saved

[*] Processing emails...

Progress: 5,234/5,234 (100.0%) | Matches: 23 | Failed: 2 | Speed: 87.2 emails/s

==================================================
EXTRACTION COMPLETE
==================================================
Total processed: 5,234
Matches found:   23
Failed emails:   2

Output dir:      ./output
Time elapsed:    60.02 seconds
==================================================
```

### Process First N Emails

For testing or large archives:

```bash
python mbox_email_parser.py \
    --mbox huge_archive.mbox \
    --email person@company.com \
    --email-limit 1000
```

### Custom Pattern File

Use your own search patterns:

```bash
python mbox_email_parser.py \
    --mbox archive.mbox \
    --email person@company.com \
    --patterns custom_patterns.txt
```

### Filter Only From Field

Only match emails FROM the target address (ignore To/Cc):

```bash
python mbox_email_parser.py \
    --mbox archive.mbox \
    --email person@company.com \
    --from-only
```

### Search Immediate Reply Only

Filter out quoted email history, search only the immediate reply:

```bash
python mbox_email_parser.py \
    --mbox archive.mbox \
    --email person@company.com \
    --reply-only
```

### Complete Example

```bash
python mbox_email_parser.py \
    --mbox /path/to/legal_archive.mbox \
    --email subject.person@company.com \
    --output ./case_2024_001 \
    --log-file case_001_extraction.csv \
    --email-limit 10000 \
    --patterns custom_legal_terms.txt
```

## Parameters

### Required

| Parameter | Description |
|-----------|-------------|
| `--mbox PATH` | Path to mbox file to process |

### Optional

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--email EMAIL` | Target email address (case-insensitive). If not specified, searches all emails | None (all emails) |
| `--output DIR` | Output directory for matched emails | `./output` |
| `--email-limit N` | Process maximum N emails (useful for testing) | Unlimited |
| `--dry-run` | Count matches only, don't save files | False |
| `--log-file PATH` | CSV log file path | `extraction_log.csv` |
| `--from-only` | Filter only by From field (ignore To/Cc/Reply-To) | False |
| `--patterns FILE` | Custom pattern file | `search_patterns.txt` or built-in |
| `--reply-only` | Search only immediate reply (filter quoted history) | False |

## Output Structure

After running the tool, you'll find:

```
output/
├── 20240115_143022_jan.novak_abc123_dovolen.eml
├── 20240128_091544_petr.svoboda_xyz456_nemocenska.eml
├── 20240203_162315_marie.nova_def789_ooo.eml
├── 20240203_162315_marie.nova_def789_ooo_001.eml    ← collision suffix
├── 20240210_100530_tomas.dvorak_ghi012_absence.eml
└── failed/
    ├── failed_email_0001.eml  ← corrupted/undecod able emails
    └── failed_email_0002.eml

extraction_log.csv  ← Detailed log of all matches
```

### Filename Format

```
{date}_{time}_{from}_{message_id}_{subject}.eml
```

- **date/time**: Email's Date header (YYYYMMDD_HHMMSS)
- **from**: Username part of From address
- **message_id**: Unique message ID (first 20 chars)
- **subject**: Sanitized subject line (first 30 chars)

## CSV Log Format

The `extraction_log.csv` contains detailed information about each match:

| Column | Description |
|--------|-------------|
| `filename` | Actual saved filename (with collision suffix if needed) |
| `original_filename` | Originally generated filename |
| `collision` | `TRUE`/`FALSE` - was there a filename collision? |
| `date` | Email Date header |
| `from_address` | From field |
| `to` | To field |
| `subject` | Email subject |
| `matched_keywords` | Comma-separated list of keywords found |
| `match_positions` | Positions where keywords were found in text |

**Sample CSV:**
```csv
filename,original_filename,collision,date,from_address,to,subject,matched_keywords,match_positions
20240115_143022_jan.novak_abc123_dovolen.eml,20240115_143022_jan.novak_abc123_dovolen.eml,FALSE,"Mon, 15 Jan 2024 14:30:22 +0100",jan.novak@firma.cz,team@firma.cz,Dovolená,"dovolene, vratim",45, 128
```

## Default Pattern Detection

By default, the tool detects vacation/OOO keywords:

### Czech Terms
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

### English Terms
- Vacation, holiday
- Out of office, OOO
- Sick leave, sick day
- Time off, PTO
- Unavailable, away
- Autoreply, automatic reply

### Time Indicators
- Od 15.5., do 31.8.
- Až do pondělí
- Vrátím 1.6.

**Note:** All patterns are customizable via `search_patterns.txt` or `--patterns` parameter.

## Customizing Search Patterns

### Edit Default Patterns

Edit `search_patterns.txt`:

```bash
# Add your custom patterns
\bcontract
\bagreement
\bconfidential
\bNDA\b
```

### Create Custom Pattern File

```bash
# Create custom_patterns.txt
cat > custom_patterns.txt << 'EOF'
# Legal terms
\bcontract
\bagreement
\blawsuit
\blitigation

# Compliance keywords
\bconfidential
\bproprietary
\bNDA\b
\bGDPR\b
EOF

# Use custom patterns
python mbox_email_parser.py --mbox archive.mbox --patterns custom_patterns.txt
```

## Troubleshooting

### "BeautifulSoup not installed" Warning

HTML emails will be processed as plain text (less accurate).

**Fix:**
```bash
pip install beautifulsoup4
```

### Large MBOX File (10GB+)

Use `--email-limit` to process in chunks:

```bash
# Process first 10,000 emails
python mbox_email_parser.py --mbox huge.mbox --email jan@firma.cz --email-limit 10000

# Process next batch (manual resumption - see limitations)
```

### Script Runs Slowly

HTML email conversion is slow. If HTML parsing isn't critical:
- Uninstall BeautifulSoup for faster (but less accurate) processing
- Or use `--email-limit` to process in smaller batches

### Charset Errors (Rare)

If charset detection fails:
1. Email is saved to `failed/` directory
2. You can manually open it in an email client
3. Script continues processing remaining emails

### Missing Matches

**Check if:**
- Target email is correctly specified (case-insensitive matching)
- Email appears in From/To/Cc/Reply-To headers
- Email contains search pattern keywords
- Pattern file is loaded correctly (check startup output)

## Progress Tracking

Real-time progress display:

```
Progress: 1,234/5,000 (24.7%) | Matches: 23 | Failed: 2 | Speed: 45.3 emails/s | ETA: 1.4m
```

## Ctrl+C Handling

Safely interrupt processing at any time:

```bash
^C
[!] Ctrl+C detected - graceful shutdown...
Processed: 1,247
Matches:   24
Failed:    2

Partial results saved.
```

All processed emails up to the interruption point are saved.

## Best Practices for Legal Cases

### 1. Always Dry-Run First

```bash
# Get match count without saving files
python mbox_email_parser.py --mbox archive.mbox --email jan@firma.cz --dry-run
```

### 2. Preserve Original MBOX

Never modify the original mbox file! Always work with copies.

### 3. Document Parameters

Create a reproducible extraction script:

```bash
cat > extract_case_001.sh << 'EOF'
#!/bin/bash
python mbox_email_parser.py \
    --mbox /original/path/archive.mbox \
    --email subject@firma.cz \
    --output ./case_001_results \
    --log-file case_001_extraction.csv \
    --patterns case_001_patterns.txt
EOF
chmod +x extract_case_001.sh
```

### 4. Verify Results

```bash
# Check CSV log
head -n 20 extraction_log.csv

# Count extracted files
ls -la output/*.eml | wc -l

# Open random samples in Outlook/Thunderbird
```

### 5. Review Failed Emails

```bash
# Check if any emails failed to process
ls -la output/failed/
```

## Technical Details

### Encoding Handling

Robust charset detection with fallback chain:

1. Use declared charset from email header
2. If fails → fallback to `cp1250` (Windows Czech)
3. If fails → fallback to `utf-8`
4. If fails → fallback to `latin1` (never fails)

### HTML Conversion

When BeautifulSoup is installed:
- Removes `<script>` and `<style>` tags
- Extracts only visible text
- Preserves spaces between elements

Without BeautifulSoup:
- Simple HTML tag removal
- Faster but less accurate

### Filename Sanitization

- Removes invalid Windows characters: `< > : " / \ | ? *`
- Maximum length: 255 characters
- Collision handling: adds `_001`, `_002`, etc.

### Pattern Matching

- Case-insensitive regex matching
- Searches normalized text (diacritics removed for Czech)
- Matches in both subject and body
- Reports all matched keywords and positions

## Performance

Typical processing times:

| MBOX Size | Email Count | Time |
|-----------|-------------|------|
| Small | 1,000 emails | ~30 seconds |
| Medium | 10,000 emails | ~5 minutes |
| Large | 100,000 emails | ~45 minutes |

**Factors affecting speed:**
- Email size
- HTML vs plain text ratio
- Disk I/O speed
- BeautifulSoup installed (slower but more accurate)

## Known Limitations

1. **No deduplication** - Duplicate emails are extracted multiple times (by design for legal cases)
2. **No resume capability** - Cannot continue from interruption point (planned for future)
3. **Single-threaded** - Processes one email at a time (simplicity and safety)
4. **Large attachments** - Emails with 100MB+ attachments may be slow

## Related Tools

- **[llm_email_filter.py](llm_email_filter.md)** - Filter false positives using AI
- **[mbox_attachment_extractor.py](mbox_attachment_extractor.md)** - Extract by attachment names
- **[eml_to_mbox.py](eml_to_mbox.md)** - Convert EML files back to MBOX format

## See Also

- [Quick Start Guide](../QUICKSTART.md)
- [Search Patterns Configuration](../search_patterns.txt)
- [Project README](../README.md)
