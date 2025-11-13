# MBOX Attachment Extractor by Regex

Extract emails with attachments matching regex patterns from mbox files. Perfect for finding invoices, contracts, reports, or any specific attachment type in large email archives.

## Features

- ✅ **Regex pattern matching** - Flexible filename filtering
- ✅ **Auto-detection** - Works with single mbox file or directory
- ✅ **All encodings supported** - Handles base64, quoted-printable, etc.
- ✅ **Accent removal** - Normalizes Czech/European characters (č→c, ž→z)
- ✅ **UUID-based naming** - Prevents filename collisions
- ✅ **Inline attachments** - Extracts both regular and inline attachments
- ✅ **Comprehensive logging** - CSV log with all metadata
- ✅ **Progress tracking** - Real-time stats and ETA
- ✅ **Graceful Ctrl+C** - Safe interruption with partial results
- ✅ **Dry-run mode** - Test patterns without saving files

## Installation

### Requirements

Python 3.7+ with standard library (no extra dependencies for basic usage)

Optional:
```bash
pip install tqdm  # For enhanced progress bar
```

### Verify Installation

```bash
python mbox_attachment_extractor.py --help
```

## Usage

### Basic Usage

```bash
python mbox_attachment_extractor.py \
  --name "\\.pdf$" \
  --input archive.mbox \
  --output ./results \
  --log extraction.csv
```

### Advanced Examples

#### Extract all PDF invoices
```bash
python mbox_attachment_extractor.py \
  --name "invoice.*\\.pdf$" \
  --input ./mbox_files \
  --output ./invoices \
  --log invoice_log.csv
```

#### Extract Excel reports (2023-2024)
```bash
python mbox_attachment_extractor.py \
  --name "report_202[34].*\\.xlsx?$" \
  --input archive.mbox \
  --output ./reports \
  --log report_log.csv
```

#### Extract logo images (including inline)
```bash
python mbox_attachment_extractor.py \
  --name "logo.*\\.(png|jpg|jpeg)$" \
  --input emails.mbox \
  --output ./logos \
  --log logo_log.csv
```

#### Dry run to test pattern
```bash
python mbox_attachment_extractor.py \
  --name "contract" \
  --input archive.mbox \
  --output ./test \
  --log test.csv \
  --dry-run
```

#### Process only first 100 emails (testing)
```bash
python mbox_attachment_extractor.py \
  --name "\\.pdf$" \
  --input archive.mbox \
  --output ./test \
  --log test.csv \
  --email-limit 100
```

#### Case-sensitive matching
```bash
python mbox_attachment_extractor.py \
  --name "CONTRACT" \
  --input archive.mbox \
  --output ./results \
  --log extraction.csv \
  --case-sensitive
```

## Parameters

### Required

| Parameter | Description |
|-----------|-------------|
| `--name REGEX` | Regex pattern for attachment filename matching |
| `--input PATH` | Path to mbox file or directory containing mbox files |
| `--output DIR` | Output directory for extracted emails and attachments |
| `--log FILE` | CSV log file path |

### Optional

| Parameter | Description |
|-----------|-------------|
| `--email-limit N` | Maximum number of emails to process (for testing) |
| `--dry-run` | Count matches only, do not save files |
| `--case-sensitive` | Use case-sensitive regex matching (default: case-insensitive) |

## Regex Pattern Examples

### File Extensions

```bash
# All PDFs
--name "\\.pdf$"

# Excel files (xlsx or xls)
--name "\\.xlsx?$"

# Word documents
--name "\\.(doc|docx)$"

# Archives
--name "\\.(zip|rar|7z)$"

# Images
--name "\\.(jpg|jpeg|png|gif)$"
```

### Filename Patterns

```bash
# Files starting with "invoice"
--name "^invoice"

# Files containing "report"
--name "report"

# Files with year format (2020-2029)
--name "202\\d"

# Format like AB123456
--name "^[A-Z]{2}\\d{6}"

# Date format YYYY-MM-DD
--name "\\d{4}-\\d{2}-\\d{2}"
```

### Combined Patterns

```bash
# Invoice PDFs
--name "invoice.*\\.pdf$"

# Reports from 2023
--name "report.*2023.*\\.xlsx?$"

# Contracts (PDF or DOCX)
--name "contract.*\\.(pdf|docx)$"

# Logos (any image format)
--name "logo.*\\.(png|jpg|jpeg|gif)$"
```

### Czech/Accented Characters

**Note:** Attachment names are normalized to lowercase ASCII before matching.

```bash
# Will match: faktura.pdf, FAKTURA.pdf, Faktura.pdf
--name "faktura\\.pdf"

# Will match: smlouva.docx, Smlouva.docx, SMLOUVA.docx
# (č → c automatically)
--name "smlouva"

# Will match: přihláška.pdf (ř → r, í → i)
--name "prihlaska"
```

## Output Structure

```
output/
├── 8f7a3c5e-4d2b-4a1f-9e6c-1b2d3e4f5a6b.eml          # Email 1
├── 8f7a3c5e-4d2b-4a1f-9e6c-1b2d3e4f5a6b_001.pdf      # Attachment 1
├── 8f7a3c5e-4d2b-4a1f-9e6c-1b2d3e4f5a6b_002.xlsx     # Attachment 2
├── a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d.eml          # Email 2
├── a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d_001.pdf      # Attachment 1
└── failed/
    └── f1e2d3c4-b5a6-4f1e-8d2c-3b4a5f6e7d8c.eml      # Failed email

extraction.csv  # Detailed log
```

### Filename Format

- **Emails**: `{UUID}.eml`
- **Attachments**: `{UUID}_{counter}.{ext}`
  - Counter is 3-digit: `001`, `002`, `003`, etc.
  - Extension preserved from original filename

### Benefits of UUID-based naming:
- No filename collisions (guaranteed unique)
- Easy to correlate email with attachments
- Works across different filesystems
- No special character issues

## CSV Log Format

The CSV log contains detailed information about each matched email:

| Column | Description |
|--------|-------------|
| `uuid` | Unique identifier for this email/attachment set |
| `eml_filename` | Email filename (UUID.eml) |
| `date` | Email date |
| `from_address` | Sender email address |
| `subject` | Email subject |
| `message_id` | Email Message-ID header |
| `attachment_count` | Number of matching attachments found |
| `attachment_names` | Original attachment names (pipe-separated) |
| `attachment_sizes` | Attachment sizes in bytes (pipe-separated) |
| `attachment_types` | MIME types (pipe-separated) |
| `total_size_bytes` | Total size of all attachments |
| `processing_time_ms` | Processing time in milliseconds |

### Example CSV Row

```csv
uuid,eml_filename,date,from_address,subject,message_id,attachment_count,attachment_names,attachment_sizes,attachment_types,total_size_bytes,processing_time_ms
8f7a3c5e-4d2b-4a1f-9e6c-1b2d3e4f5a6b,8f7a3c5e-4d2b-4a1f-9e6c-1b2d3e4f5a6b.eml,"Mon, 15 Jan 2024 10:30:00 +0100",jan@firma.cz,Invoice for January,<abc123@mail.gmail.com>,2,invoice_2024_01.pdf | payment_info.xlsx,245678 | 15234,application/pdf | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,260912,156
```

## How It Works

### 1. Attachment Detection

The script finds attachments in two ways:

- **Content-Disposition**: Standard attachment header
  ```
  Content-Disposition: attachment; filename="invoice.pdf"
  ```

- **Content-Type name**: Inline attachments
  ```
  Content-Type: image/png; name="logo.png"
  ```

### 2. Filename Normalization

Before regex matching, filenames are normalized:

```
Original:    Smlouva_Č_2024.pdf
Normalized:  smlouva_c_2024.pdf
```

**Character mapping:**
- Czech: `á→a, č→c, ď→d, é→e, ě→e, í→i, ň→n, ó→o, ř→r, š→s, ť→t, ú→u, ů→u, ý→y, ž→z`
- Other European: `à→a, ä→a, ö→o, ü→u, ñ→n, ç→c`, etc.
- Lowercase: `A→a, B→b`, etc.

### 3. Regex Matching

Pattern is matched against normalized filename:
```python
Pattern: "smlouva.*\\.pdf$"
Matches:
  ✓ smlouva_2024.pdf
  ✓ Smlouva_finalni.pdf
  ✓ SMLOUVA_ПОДПИСЬ.PDF
  ✗ smlouva.docx (wrong extension)
```

### 4. Encoding Handling

All encoding types are automatically decoded:
- **base64** - Most common for binary files
- **quoted-printable** - Text files
- **7bit, 8bit** - Plain text
- **binary** - Raw binary

### 5. Saving Files

When match is found:
1. Generate UUID for this email
2. Save complete email as `{UUID}.eml`
3. Save each matching attachment as `{UUID}_{counter}.{ext}`
4. Log all details to CSV

## Progress Tracking

During processing, real-time stats are displayed:

```
Progress: 1,234 (82.3%) | Matches: 45 | Attachments: 67 | Failed: 2 | Speed: 8.5 emails/s | ETA: 25s
```

**Stats explained:**
- **Progress**: Emails processed (percentage if total known)
- **Matches**: Emails with matching attachments
- **Attachments**: Total attachments extracted
- **Failed**: Emails that failed to process
- **Speed**: Emails per second
- **ETA**: Estimated time remaining

## Ctrl+C Handling

Script can be safely interrupted at any time:

```
^C
[!] Ctrl+C detected - graceful shutdown...
Processed:   1,247
Matches:     45
Attachments: 67
Failed:      2

Partial results saved.
```

All processed emails are saved. Resume by excluding already processed files.

## Input Options

### Option 1: Single mbox file

```bash
python mbox_attachment_extractor.py \
  --name "\\.pdf$" \
  --input /path/to/archive.mbox \
  --output ./results \
  --log extraction.csv
```

### Option 2: Directory with multiple mbox files

```bash
python mbox_attachment_extractor.py \
  --name "\\.pdf$" \
  --input /path/to/mbox_directory \
  --output ./results \
  --log extraction.csv
```

**Auto-detection:**
- Finds all `*.mbox` files
- Checks files without extension (if they start with `From `)
- Processes each mbox sequentially
- Logs all results to same CSV
- Shows summary per file + total summary

## Best Practices

### 1. Always test with dry-run first

```bash
# Test pattern without saving files
python mbox_attachment_extractor.py \
  --name "invoice" \
  --input archive.mbox \
  --output ./test \
  --log test.csv \
  --dry-run
```

**Output:**
```
Total processed:  10,000
Matches found:    45
Attachments:      67
Failed emails:    2
```

### 2. Use email-limit for quick tests

```bash
# Process only first 100 emails
python mbox_attachment_extractor.py \
  --name "\\.pdf$" \
  --input archive.mbox \
  --output ./test \
  --log test.csv \
  --email-limit 100
```

### 3. Test regex patterns online first

Use tools like:
- https://regex101.com/
- https://regexr.com/

**Set to Python flavor and test against sample filenames!**

### 4. Escape special characters

In regex, these characters need escaping: `. ^ $ * + ? { } [ ] \ | ( )`

```bash
# Wrong: --name ".pdf"     (matches any character + pdf)
# Right: --name "\\.pdf"   (matches literal dot + pdf)

# Wrong: --name "file (1).pdf"
# Right: --name "file \\(1\\)\\.pdf"
```

### 5. Review the CSV log

```bash
# Check log in spreadsheet
libreoffice extraction.csv

# Or view in terminal
head -n 20 extraction.csv
```

Verify:
- Attachment counts are reasonable
- File sizes make sense
- Dates are in expected range

### 6. Backup original mbox files

**Never modify originals!**

```bash
cp archive.mbox archive.mbox.backup
```

## Troubleshooting

### Issue: No matches found

**Possible causes:**
1. Regex pattern is incorrect
2. Case-sensitive matching enabled (try without `--case-sensitive`)
3. Attachment names have different format than expected

**Solutions:**
```bash
# Test with broader pattern
--name "invoice"  # Instead of "invoice_\\d{4}\\.pdf"

# Check what attachments exist (extract all)
--name "."  # Matches any filename
```

### Issue: Too many matches

**Solution:** Narrow down the pattern

```bash
# Too broad
--name "report"

# Better
--name "^report_202[34].*\\.pdf$"
```

### Issue: Accented characters not matching

**Remember:** Names are normalized before matching

```bash
# File: Příloha.pdf
# Normalized: priloha.pdf

# This works:
--name "priloha"

# This doesn't work:
--name "příloha"
```

### Issue: Pattern works in regex tester but not in script

**Cause:** Shell escaping

```bash
# In regex tester:
\.pdf$

# In command line (needs extra backslash):
--name "\\.pdf$"

# Alternative: use single quotes (no escaping needed)
--name '\.pdf$'
```

### Issue: "No mbox files found"

**Solutions:**
1. Check file extension: `.mbox` or no extension
2. Try absolute path: `/full/path/to/archive.mbox`
3. Verify file is valid mbox (starts with `From `)

```bash
# Check if file is valid mbox
head -n 1 archive.mbox
# Should output: From someone@example.com ...
```

### Issue: High failure rate

**Possible causes:**
1. Corrupted mbox file
2. Non-standard email format
3. Very large attachments causing memory issues

**Check failed emails:**
```bash
ls -lh output/failed/
# Review failed emails manually
```

## Performance

### Typical Processing Speed

- **Small emails** (text only): ~15-20 emails/second
- **Medium emails** (1-2 attachments): ~5-10 emails/second
- **Large emails** (many/large attachments): ~1-3 emails/second

### Factors Affecting Speed

- Attachment size (larger = slower)
- Number of attachments per email
- Disk speed (SSD vs HDD)
- Pattern complexity (simple patterns faster)

### Example Processing Times

| Mbox Size | Email Count | Matches | Time |
|-----------|-------------|---------|------|
| 100 MB | 1,000 | 50 | ~2 minutes |
| 1 GB | 10,000 | 200 | ~15 minutes |
| 10 GB | 100,000 | 1,500 | ~2 hours |

*Times vary based on attachment sizes and system performance*

## Use Cases

### Legal Case - Extract All Contracts

```bash
python mbox_attachment_extractor.py \
  --name "(contract|smlouva|agreement).*\\.(pdf|docx)$" \
  --input /legal/emails/case_001.mbox \
  --output /legal/evidence/contracts \
  --log contracts_log.csv
```

### Accounting - Extract Invoices by Year

```bash
python mbox_attachment_extractor.py \
  --name "(invoice|faktura).*2024.*\\.pdf$" \
  --input /accounting/emails/inbox.mbox \
  --output /accounting/invoices/2024 \
  --log invoices_2024.csv
```

### HR - Extract Resumes

```bash
python mbox_attachment_extractor.py \
  --name "(cv|resume|zivotopis).*\\.(pdf|docx)$" \
  --input /hr/applications.mbox \
  --output /hr/resumes \
  --log resumes.csv
```

### IT - Extract Log Files

```bash
python mbox_attachment_extractor.py \
  --name "\\.(log|txt)$" \
  --input /support/tickets.mbox \
  --output /support/logs \
  --log extracted_logs.csv
```

### Marketing - Extract Logos

```bash
python mbox_attachment_extractor.py \
  --name "logo.*\\.(png|jpg|svg)$" \
  --input /marketing/emails.mbox \
  --output /marketing/logos \
  --log logos.csv
```

## Limitations

1. **Sequential processing**: One email at a time (no parallel processing)
2. **Memory usage**: Very large attachments (1GB+) may cause memory issues
3. **Pattern matching**: Only matches normalized filenames (not content)
4. **No deduplication**: Same attachment in multiple emails extracted multiple times

## Comparison with Existing Tools

### vs mbox_email_parser.py

| Feature | mbox_email_parser | mbox_attachment_extractor |
|---------|------------------|---------------------------|
| Purpose | Extract emails by content patterns | Extract by attachment name |
| Filter | Email content (body/subject) | Attachment filename |
| Pattern | Customizable regex (default: vacation/OOO) | User-defined regex |
| Output | EML files only | EML + extracted attachments |
| Naming | Timestamp-based | UUID-based |

**Use together:**
1. Use `mbox_email_parser.py` to filter emails by content
2. Use `mbox_attachment_extractor.py` to extract specific attachments from results

## Future Enhancements (v2.0 planned)

- [ ] Resume capability (skip already processed emails)
- [ ] Parallel processing for faster extraction
- [ ] Content-based filtering (MIME type)
- [ ] Attachment size filtering (min/max)
- [ ] Deduplication (hash-based)
- [ ] JSON output format
- [ ] Web UI for pattern testing

## Support

For bug reports and feature requests, contact the developer.

## Changelog

### v1.0 (2025-11-12)
- Initial release
- Regex-based attachment filtering
- UUID-based naming
- Auto-detect mbox file or directory
- Inline attachment support
- Czech/European character normalization
- Comprehensive CSV logging
- Real-time progress tracking
- Graceful Ctrl+C handling
- Dry-run mode

## License

For internal use.
