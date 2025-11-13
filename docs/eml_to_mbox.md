# eml_to_mbox.py

Convert individual EML files back to MBOX format.

## Overview

`eml_to_mbox.py` is a utility that converts extracted `.eml` files back into `.mbox` format, making them importable into email clients like Thunderbird.

**Use cases:**
- Import extracted emails back into email client
- Create custom mailboxes from filtered results
- Archive processed emails in MBOX format

## Features

- ✅ Batch conversion with glob patterns
- ✅ Preserves complete email structure (headers, body, attachments)
- ✅ Compatible with Thunderbird and other MBOX clients
- ✅ Progress tracking and statistics
- ✅ Error handling (failed files don't stop processing)
- ✅ Verbose logging mode

## Installation

No additional dependencies required beyond standard Python 3.7+.

## Usage

### Basic Usage

Convert all EML files in a directory:

```bash
python eml_to_mbox.py --input "./output/*.eml" --output archive.mbox
```

### With Verbose Output

See detailed progress:

```bash
python eml_to_mbox.py --input "./output/*.eml" --output archive.mbox --verbose
```

### Convert Filtered Results

Convert only matched emails:

```bash
python eml_to_mbox.py --input "./filtered_results/matched/*.eml" --output matched.mbox
```

### Convert Specific Pattern

Use glob patterns for selective conversion:

```bash
# Only high-confidence matches (90%+)
python eml_to_mbox.py --input "./filtered_results/matched/9*.eml" --output high_confidence.mbox

# Specific sender
python eml_to_mbox.py --input "./output/*jan.novak*.eml" --output jan_novak_emails.mbox

# Date range
python eml_to_mbox.py --input "./output/202401*.eml" --output january_2024.mbox
```

## Parameters

### Required

| Parameter | Description |
|-----------|-------------|
| `--input PATTERN` | Glob pattern for input EML files (e.g., `"./dir/*.eml"`) |
| `--output FILE` | Output MBOX file path |

### Optional

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--verbose` | Enable detailed logging | False |

## Example Output

### Standard Output

```
==================================================
EML TO MBOX CONVERTER
==================================================

Input pattern:  ./output/*.eml
Output file:    archive.mbox

Converting...
[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] 100% (150/150)

==================================================
CONVERSION COMPLETE
==================================================
Processed:  150
Failed:     2
Skipped:    0

Output: archive.mbox (3.2 MB)
==================================================
```

### Verbose Output

```
==================================================
EML TO MBOX CONVERTER
==================================================

Input pattern:  ./output/*.eml
Output file:    archive.mbox

[10:30:15] [INFO] Found 150 EML files
[10:30:15] [INFO] Added: 20240115_jan.novak_abc123_dovolen.eml
[10:30:15] [INFO] Added: 20240128_petr.svoboda_xyz456_nemocenska.eml
[10:30:15] [ERROR] Failed to read corrupted_email.eml: Invalid format
[10:30:16] [INFO] Added: 20240203_marie.nova_def789_ooo.eml
...
[10:30:45] [INFO] Conversion complete

==================================================
CONVERSION COMPLETE
==================================================
Processed:  148
Failed:     2
Skipped:    0

Output: archive.mbox (3.2 MB)
==================================================
```

## Use Cases

### 1. Import to Thunderbird

```bash
# Convert extracted emails
python eml_to_mbox.py --input "./output/*.eml" --output vacation_emails.mbox

# In Thunderbird:
# 1. Tools → Import → Mail → Import mbox file directly
# 2. Select vacation_emails.mbox
# 3. Emails appear in new folder
```

### 2. Archive Filtered Results

```bash
# Archive only genuine matches
python eml_to_mbox.py \
  --input "./filtered_results/matched/*.eml" \
  --output "case_001_genuine_vacation_emails.mbox"
```

### 3. Create Separate Archives by Confidence

```bash
# High confidence (90-100%)
python eml_to_mbox.py --input "./matched/9*.eml" --output high_confidence.mbox

# Medium confidence (70-89%)
python eml_to_mbox.py --input "./matched/[7-8]*.eml" --output medium_confidence.mbox

# Low confidence (50-69%)
python eml_to_mbox.py --input "./matched/[5-6]*.eml" --output low_confidence.mbox
```

### 4. Consolidate Multiple Extractions

```bash
# Combine results from multiple runs
python eml_to_mbox.py --input "./case_001/output/*.eml" --output combined.mbox
python eml_to_mbox.py --input "./case_002/output/*.eml" --output combined.mbox  # Appends!
```

## Error Handling

### Failed Files

Files that fail to convert are logged but don't stop processing:

```
[10:30:15] [ERROR] Failed to read corrupted_email.eml: Invalid format
```

The conversion continues with remaining files.

### Common Errors

**Error: "No files matching pattern"**

```
Error: No files found matching pattern: ./output/*.eml
```

**Solution:** Check path and pattern:
```bash
# Verify files exist
ls ./output/*.eml

# Use absolute path if needed
python eml_to_mbox.py --input "/full/path/to/output/*.eml" --output archive.mbox
```

**Error: "Permission denied"**

**Solution:** Check file permissions or run with appropriate privileges.

## MBOX Format

The output `.mbox` file uses standard MBOX format:
- Compatible with Thunderbird, Apple Mail, Gmail import
- Preserves all headers, body, and attachments
- Each message separated by `From ` line
- Can be directly imported into email clients

## Performance

Typical conversion speed:
- **Small emails** (< 100 KB): ~100 emails/second
- **Large emails** (1-10 MB): ~10 emails/second
- **With attachments**: Depends on attachment size

## Limitations

1. **Append mode only** - Running multiple times on same output file appends (doesn't overwrite)
2. **No deduplication** - Duplicate EML files will create duplicate MBOX entries
3. **Memory usage** - Very large EML files may consume significant memory

## Related Tools

- **[mbox_email_parser.py](mbox_email_parser.md)** - Extract emails from MBOX to EML
- **[llm_email_filter.py](llm_email_filter.md)** - Filter EML files

## Typical Workflow

```bash
# 1. Extract emails from MBOX
python mbox_email_parser.py --mbox archive.mbox --email jan@firma.cz --output ./extracted

# 2. Filter with LLM
python llm_email_filter.py --input-dir ./extracted ... --output-dir ./filtered

# 3. Convert back to MBOX for archiving
python eml_to_mbox.py --input "./filtered/matched/*.eml" --output filtered_archive.mbox
```

## See Also

- [Project README](../README.md)
- [mbox_email_parser.py Documentation](mbox_email_parser.md)
