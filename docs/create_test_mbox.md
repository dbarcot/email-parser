# create_test_mbox.py

Generate sample MBOX file for testing email extraction tools.

## Overview

`create_test_mbox.py` generates a test MBOX file containing 8 sample emails (Czech and English) designed to test the email parser's pattern matching capabilities.

**Use cases:**
- Verify installation and configuration
- Test pattern matching before processing real data
- Validate extraction accuracy
- Demo the tool's capabilities

## Features

- ✅ 8 diverse test emails (Czech + English)
- ✅ Mix of vacation, sick leave, and normal emails
- ✅ Tests pattern matching (6 should match, 2 should not)
- ✅ Tests charset handling (UTF-8, Windows-1250)
- ✅ Tests HTML email processing
- ✅ Tests email filtering by address
- ✅ Instant generation (< 1 second)

## Usage

### Generate Test File

```bash
python create_test_mbox.py
```

No parameters required. Creates `test_emails.mbox` in current directory.

### Example Output

```
[✓] Created test mbox: test_emails.mbox
[✓] Total emails: 8
[✓] Expected matches for jan.novak@firma.cz: 6
    - Email 1: Dovolená (from jan.novak)
    - Email 2: Out of office (to jan.novak)
    - Email 3: Nemocenská (to jan.novak)
    - Email 4: NO MATCH (no keywords)
    - Email 5: Mimo kancelář HTML (to jan.novak)
    - Email 6: FW with vacation (to jan.novak)
    - Email 7: NO MATCH (not involving jan.novak)
    - Email 8: Řádná dovolená (to jan.novak)

[*] Test the parser:
    python mbox_email_parser.py --mbox test_emails.mbox --email jan.novak@firma.cz --dry-run
```

## Test Emails Included

### Email 1: Czech Vacation
- **From:** jan.novak@firma.cz
- **To:** team@firma.cz
- **Subject:** Dovolená
- **Keywords:** dovolená, vrátím
- **Should match:** ✓ Yes

### Email 2: English OOO
- **From:** jane.smith@company.com
- **To:** jan.novak@firma.cz
- **Subject:** Out of Office
- **Keywords:** out of office, contact colleague
- **Should match:** ✓ Yes

### Email 3: Sick Leave
- **From:** petr.svoboda@firma.cz
- **To:** jan.novak@firma.cz, marie.nova@firma.cz
- **Subject:** Nemocenská
- **Keywords:** nemocenská, vrátím se
- **Should match:** ✓ Yes

### Email 4: Normal Email (No Keywords)
- **From:** karel@firma.cz
- **To:** jan.novak@firma.cz
- **Subject:** Dotaz na zprávu
- **Keywords:** None
- **Should match:** ✗ No

### Email 5: HTML Email (Mimo kancelář)
- **From:** marie.nova@firma.cz
- **To:** jan.novak@firma.cz
- **Cc:** team@firma.cz
- **Subject:** Automatická odpověď: mimo kancelář
- **Format:** HTML multipart
- **Should match:** ✓ Yes

### Email 6: Forwarded Email
- **From:** anna@firma.cz
- **To:** jan.novak@firma.cz
- **Subject:** FW: Info o dovolené
- **Keywords:** dovolená (in forwarded content)
- **Should match:** ✓ Yes

### Email 7: Not Involving Target Email
- **From:** random@other.com
- **To:** someone@other.com
- **Subject:** Dovolená plány
- **Keywords:** dovolená (but not involving jan.novak)
- **Should match:** ✗ No

### Email 8: Windows-1250 Charset
- **From:** tomas.dvorak@firma.cz
- **To:** jan.novak@firma.cz
- **Subject:** Řádná dovolená
- **Charset:** Windows-1250 (Czech charset test)
- **Should match:** ✓ Yes

## Testing Workflow

### Step 1: Generate Test File

```bash
python create_test_mbox.py
```

### Step 2: Test with Dry Run

```bash
python mbox_email_parser.py \
    --mbox test_emails.mbox \
    --email jan.novak@firma.cz \
    --dry-run
```

**Expected output:**
```
Total processed: 8
Matches found:   6
Failed emails:   0
```

### Step 3: Test Actual Extraction

```bash
python mbox_email_parser.py \
    --mbox test_emails.mbox \
    --email jan.novak@firma.cz \
    --output ./test_results
```

**Expected:** 6 EML files in `./test_results/`

### Step 4: Verify Results

```bash
# Check extracted files
ls -la test_results/*.eml | wc -l  # Should be 6

# Check CSV log
cat extraction_log.csv

# Open random email
# (Mac) open test_results/*.eml
# (Windows) start test_results\*.eml
# (Linux) xdg-open test_results/*.eml
```

## What This Tests

1. **Pattern matching accuracy**
   - Czech keywords: dovolená, nemocenská, mimo kancelář
   - English keywords: out of office
   - Should find 6 matches, ignore 2

2. **Email filtering**
   - Correctly filters by From/To/Cc/Reply-To
   - Email 7 should be ignored (doesn't involve jan.novak)

3. **Charset handling**
   - UTF-8 (Email 1-6)
   - Windows-1250 (Email 8)
   - Czech diacritics: č, ř, á, é, ů, ě, ď

4. **HTML processing**
   - Email 5 is HTML multipart
   - Should extract text correctly

5. **Forwarded emails**
   - Email 6 contains forwarded content
   - Should match keywords in forwarded text

## Troubleshooting

### Only 5 Matches Found (Missing Email 5)

**Issue:** HTML email not processed correctly

**Solution:**
```bash
pip install beautifulsoup4
```

### 0 Matches Found

**Issue:** Target email doesn't match

**Solution:** Use exact email:
```bash
python mbox_email_parser.py --mbox test_emails.mbox --email jan.novak@firma.cz --dry-run
```

### 7 or 8 Matches (Too Many)

**Issue:** Email 4 or 7 incorrectly matching

**Possible causes:**
- Custom patterns too broad
- Check `search_patterns.txt` or `--patterns` parameter

## Customizing Test File

Edit `create_test_mbox.py` to add your own test cases:

```python
# Add new test email
msg_new = MIMEText('Your test content', 'plain', 'utf-8')
msg_new['From'] = 'test@example.com'
msg_new['To'] = 'jan.novak@firma.cz'
msg_new['Subject'] = 'Test Subject'
msg_new['Date'] = email.utils.formatdate(datetime.now().timestamp(), localtime=True)
msg_new['Message-ID'] = '<test123@server.com>'
mbox.add(msg_new)
```

## Use in Automated Testing

```bash
#!/bin/bash

# Generate test data
python create_test_mbox.py

# Run extraction
python mbox_email_parser.py \
    --mbox test_emails.mbox \
    --email jan.novak@firma.cz \
    --output ./test_results \
    --dry-run

# Verify results
if [ $? -eq 0 ]; then
    echo "✓ Test passed"
else
    echo "✗ Test failed"
    exit 1
fi
```

## File Size

- **test_emails.mbox:** ~5 KB
- **Extracted EML files:** ~3-4 KB total
- Generation time: < 1 second

## Related Tools

- **[mbox_email_parser.py](mbox_email_parser.md)** - Test this tool with generated file
- **[llm_email_filter.py](llm_email_filter.md)** - Test LLM filtering on extracted results

## See Also

- [Quick Start Guide](../QUICKSTART.md)
- [mbox_email_parser.py Documentation](mbox_email_parser.md)
- [Project README](../README.md)
