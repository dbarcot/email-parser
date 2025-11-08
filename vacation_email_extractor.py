#!/usr/bin/env python3
"""
Vacation Email Extractor
========================
Extracts vacation/OOO related emails from mbox files for legal case processing.

Author: Claude
Version: 1.0
"""

import mailbox
import email
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime
from email.generator import BytesGenerator
import re
import argparse
import os
import sys
import csv
import signal
from pathlib import Path
from datetime import datetime
import time

# Try to import BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("[WARNING] BeautifulSoup not installed. HTML emails will be processed as plain text.")
    print("          Install with: pip install beautifulsoup4")

# Try to import tqdm for progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# =============================================================================
# REGEX PATTERNS FOR VACATION KEYWORDS
# =============================================================================

VACATION_PATTERNS = [
    # === DOVOLENÁ ===
    r'\bdovolen[aeouyi][a-z]*',
    r'\bdov\b',
    r'\bdov\.',
    r'\bcerp[aei][a-z]*\s+dovolen',
    r'\bzaslouzen[aeouyi]*\s+dovolen',
    r'\bradn[aeouyi]*\s+dovolen',
    
    # === PRÁZDNINY ===
    r'\bprazdnin[aeouyi]*',
    r'\bprazd\.',
    
    # === VOLNO ===
    r'\bvoln[aeouyi][a-z]*',
    r'\bvoln\b',
    
    # === NEPŘÍTOMNOST ===
    r'\bnepritom[a-z]*',
    r'\bneprit\b',
    r'\bneprit\.',
    
    # === MIMO KANCELÁŘ ===
    r'\bmimo\s+kancela[rz][a-z]*',
    r'\bmimo\s+k\b',
    r'\bmimo\s+k\.',
    r'\bmimo\s+provoz',
    
    # === OUT OF OFFICE ===
    r'\bo+\s*o+\s*o+',
    r'\bout\s+of\s+office',
    r'\bout\s+off',
    
    # === NEMOCENSKÁ / SICK LEAVE ===
    r'\bnemocensk[aeouyi]*',
    r'\bnemoc\b',
    r'\bnemoc\.',
    r'\bnem\b',
    r'\bnem\.',
    r'\bpn\b',
    r'\bp\.?\s*n\.',
    r'\bpracovn[aeouyi]*\s+neschopn',
    r'\bneschopenk[aeouyi]',
    
    # === ZDRAVOTNÍ ===
    r'\bzdravotn[aeouyi][a-z]*',
    r'\bzdr\.',
    r'\bzdr\s+voln',
    r'\bzdr\s+d[uu]vod',
    
    # === ABSENCE ===
    r'\babsen[ct][a-z]*',
    r'\babs\b',
    r'\babs\.',
    
    # === NEDOSTUPNÝ ===
    r'\bnedostupn[aeouyi]*',
    r'\bnedost\b',
    r'\bnedost\.',
    r'\bne\s+budu\s+dostupn',
    
    # === RODIČOVSKÁ/MATEŘSKÁ/OTCOVSKÁ ===
    r'\brodicovsk[aeouyi]*',
    r'\brd\b',
    r'\brd\.',
    r'\br\.?\s*d\.',
    r'\bmatersk[aeouyi]*',
    r'\bmat\b',
    r'\bmat\.',
    r'\botcovsk[aeouyi]*',
    r'\bot\b',
    r'\bot\.',
    
    # === NÁVRAT / VRÁTÍM SE ===
    r'\bvrat[ii][a-z]*\s+se',
    r'\bzpet\s+(od|az|do|v)',
    r'\bnavrat',
    r'\bbudu\s+zpet',
    r'\bbudu\s+zpatky',
    r'\bzpat(ky|ecky)',
    
    # === K DISPOZICI ===
    r'\bk\s+dispozici',
    r'\bdispozic[iei]',
    r'\bne\s+budu\s+k\s+zastiz',
    r'\bk\s+zastiz',
    
    # === UŽÍVÁM SI / BAVÍM SE ===
    r'\buziv[aei][a-z]*',
    r'\bbav[ii][a-z]*\s+se',
    r'\brelax',
    r'\bodpociv[aei]',
    
    # === ANGLICKÉ VÝRAZY ===
    r'\bvacation',
    r'\bholiday',
    r'\bholidays',
    r'\bsick\s+leave',
    r'\bsick\s+day',
    r'\bsickday',
    r'\btime\s+off',
    r'\bpto\b',
    r'\bleave\b',
    r'\bunavailable',
    r'\baway',
    r'\boff\s+work',
    r'\boff\s+duty',
    r'\bautoreply',
    r'\bauto\s+reply',
    r'\bautomatic\s+reply',
    
    # === SPECIFICKÉ FRÁZE ===
    r'\bv\s+dob[ee]\s+m[ee]\s+nepritom',
    r'\bpo\s+dobu\s+m[ee]\s+nepritom',
    r'\bbehem\s+m[ee]\s+nepritom',
    r'\bodpov[ii][a-z]*\s+az\s+po',
    r'\bnemonitor',
    r'\bne\s+check',
    r'\bomezen[aeouyi]*\s+prist',
    r'\blimited\s+access',
    r'\bno\s+access',
    r'\bno\s+email',
    
    # === ČASOVÉ INDIKÁTORY ===
    r'\bod\s+\d+\.\d+',
    r'\bdo\s+\d+\.\d+',
    r'\baz\s+do\s+\d+',
    r'\bvr[aa]t[ii][a-z]*\s+\d+\.',
]

# Compile patterns once for performance
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in VACATION_PATTERNS]

# =============================================================================
# GLOBAL COUNTERS (for signal handler)
# =============================================================================
processed_count = 0
matched_count = 0
failed_count = 0

# =============================================================================
# PROGRESS BAR
# =============================================================================

class ProgressBar:
    """Simple progress bar for email processing."""

    def __init__(self, total=None, enable=True):
        """
        Initialize progress bar.

        Args:
            total: Total number of items (None if unknown)
            enable: Enable/disable progress display
        """
        self.total = total
        self.enable = enable
        self.last_update = 0
        self.start_time = time.time()

    def update(self, processed, matched, failed):
        """
        Update progress bar.

        Args:
            processed: Number of emails processed
            matched: Number of matches found
            failed: Number of failed emails
        """
        if not self.enable:
            return

        # Update every email or every 0.1 seconds (whichever is less frequent)
        current_time = time.time()
        if current_time - self.last_update < 0.1 and processed != self.total:
            return

        self.last_update = current_time
        elapsed = current_time - self.start_time

        # Calculate speed
        speed = processed / elapsed if elapsed > 0 else 0

        # Build progress line
        if self.total:
            percentage = (processed / self.total) * 100
            progress_str = f"Progress: {processed:,}/{self.total:,} ({percentage:.1f}%)"

            # Estimate time remaining
            if speed > 0:
                remaining = (self.total - processed) / speed
                eta_str = f" | ETA: {self._format_time(remaining)}"
            else:
                eta_str = ""
        else:
            progress_str = f"Processed: {processed:,}"
            eta_str = ""

        # Build status line
        status = (
            f"\r{progress_str} | "
            f"Matches: {matched} | "
            f"Failed: {failed} | "
            f"Speed: {speed:.1f} emails/s"
            f"{eta_str}"
        )

        # Print with padding to clear previous line
        print(status + " " * 10, end='', flush=True)

    def finish(self):
        """Finish progress bar and print newline."""
        if self.enable:
            print()  # New line after progress

    def _format_time(self, seconds):
        """Format seconds to human readable time."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

# =============================================================================
# TEXT NORMALIZATION
# =============================================================================

def normalize_text(text):
    """
    Normalize text by removing diacritics and converting to lowercase ASCII.
    
    Args:
        text: Input text (may contain Czech characters)
    
    Returns:
        Normalized text (lowercase, no diacritics)
    """
    if not text:
        return ""
    
    # Mapping of Czech diacritics to ASCII
    replacements = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
        'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
        'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z'
    }
    
    text = text.lower()
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    
    return text

# =============================================================================
# KEYWORD MATCHING
# =============================================================================

def contains_vacation_keyword(normalized_text):
    """
    Check if normalized text contains any vacation-related keywords.
    
    Args:
        normalized_text: Text already normalized (lowercase, no diacritics)
    
    Returns:
        Tuple: (has_match: bool, matched_keywords: list, match_positions: list)
    """
    matched_keywords = []
    match_positions = []
    
    for pattern in COMPILED_PATTERNS:
        for match in pattern.finditer(normalized_text):
            keyword = match.group(0)
            position = match.start()
            
            # Avoid duplicates
            if keyword not in matched_keywords:
                matched_keywords.append(keyword)
                match_positions.append(str(position))
    
    has_match = len(matched_keywords) > 0
    
    return (has_match, matched_keywords, match_positions)

# =============================================================================
# EMAIL ADDRESS EXTRACTION
# =============================================================================

def extract_email_addresses(header_value):
    """
    Extract email addresses from header value.
    
    Args:
        header_value: Header value (e.g., "Jan Novák <jan@firma.cz>, Petr...")
    
    Returns:
        List of email addresses (normalized to lowercase)
    """
    if not header_value:
        return []
    
    # Decode header first (handles encoded words like =?utf-8?b?...?=)
    decoded_header = decode_header_value(header_value)
    
    # Use email.utils.getaddresses to parse addresses
    addresses = getaddresses([decoded_header])
    
    # Extract only email part and normalize to lowercase
    emails = [addr[1].lower() for addr in addresses if addr[1]]
    
    return emails

# =============================================================================
# HEADER DECODING
# =============================================================================

def decode_header_value(header_value):
    """
    Decode email header value (handles encoded words).
    
    Args:
        header_value: Raw header value
    
    Returns:
        Decoded string
    """
    if not header_value:
        return ""
    
    try:
        decoded_parts = decode_header(header_value)
        result = []
        
        for content, charset in decoded_parts:
            if isinstance(content, bytes):
                # Try to decode with specified charset or fallback
                if charset:
                    try:
                        result.append(content.decode(charset))
                    except:
                        result.append(content.decode('latin1', errors='ignore'))
                else:
                    result.append(content.decode('latin1', errors='ignore'))
            else:
                result.append(content)
        
        return ''.join(result)
    except:
        return str(header_value)

# =============================================================================
# HTML TO TEXT CONVERSION
# =============================================================================

def html_to_text(html):
    """
    Convert HTML to plain text.
    
    Args:
        html: HTML content
    
    Returns:
        Plain text
    """
    if not html:
        return ""
    
    if HAS_BS4:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text with space separator
            text = soup.get_text(separator=' ', strip=True)
            return text
        except:
            pass
    
    # Fallback: simple HTML tag removal
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# =============================================================================
# CHARSET DECODING WITH FALLBACK
# =============================================================================

def decode_with_fallback(payload, charset):
    """
    Decode payload with charset fallback.
    
    Args:
        payload: Bytes to decode
        charset: Declared charset (may be None or wrong)
    
    Returns:
        Decoded string
    """
    if not payload:
        return ""
    
    # Charset fallback order
    charsets_to_try = [charset, 'cp1250', 'utf-8', 'latin1']
    
    for cs in charsets_to_try:
        if cs is None:
            continue
        try:
            return payload.decode(cs)
        except:
            continue
    
    # Last resort - never fails
    return payload.decode('latin1', errors='ignore')

# =============================================================================
# EMAIL BODY EXTRACTION
# =============================================================================

def extract_email_body(msg):
    """
    Extract complete text body from email (plain text + HTML converted to text).
    
    Args:
        msg: email.message.Message object
    
    Returns:
        Complete body text
    """
    text_parts = []
    
    try:
        if msg.is_multipart():
            # Walk through all parts
            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        text = decode_with_fallback(payload, part.get_content_charset())
                        text_parts.append(text)
                
                elif content_type == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = decode_with_fallback(payload, part.get_content_charset())
                        text = html_to_text(html)
                        text_parts.append(text)
        
        else:
            # Single part message
            payload = msg.get_payload(decode=True)
            if payload:
                content_type = msg.get_content_type()
                
                if content_type == 'text/html':
                    html = decode_with_fallback(payload, msg.get_content_charset())
                    text = html_to_text(html)
                    text_parts.append(text)
                else:
                    text = decode_with_fallback(payload, msg.get_content_charset())
                    text_parts.append(text)
    
    except Exception as e:
        # If body extraction fails, return empty string
        pass
    
    return ' '.join(text_parts)

# =============================================================================
# EMAIL FILTERING
# =============================================================================

def email_involves_target(msg, target_email, from_only=False):
    """
    Check if target email is involved in From/To/Cc/Reply-To headers.

    Args:
        msg: email.message.Message object
        target_email: Target email address (normalized lowercase)
        from_only: If True, only check From header; otherwise check all headers

    Returns:
        Boolean
    """
    if from_only:
        headers_to_check = ['From']
    else:
        headers_to_check = ['From', 'To', 'Cc', 'Reply-To']

    for header in headers_to_check:
        header_value = msg.get(header, '')
        if header_value:
            emails = extract_email_addresses(header_value)
            if target_email in emails:
                return True

    return False

# =============================================================================
# FILENAME GENERATION
# =============================================================================

def sanitize_filename_part(text, max_length=50):
    """
    Sanitize text for use in filename.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length
    
    Returns:
        Sanitized text
    """
    if not text:
        return "unknown"
    
    # Remove or replace invalid characters for Windows
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        text = text.replace(char, '_')
    
    # Replace multiple spaces/underscores with single underscore
    text = re.sub(r'[\s_]+', '_', text)
    
    # Remove leading/trailing underscores
    text = text.strip('_')
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text if text else "unknown"

def generate_eml_filename(msg):
    """
    Generate EML filename from email message.
    
    Format: {datetime}_{from}_{message_id}_{subject_snippet}.eml
    
    Args:
        msg: email.message.Message object
    
    Returns:
        Generated filename
    """
    # 1. Date/time
    try:
        date_str = msg.get('Date', '')
        if date_str:
            dt = parsedate_to_datetime(date_str)
            datetime_part = dt.strftime("%Y%m%d_%H%M%S")
        else:
            datetime_part = "00000000_000000"
    except:
        datetime_part = "00000000_000000"
    
    # 2. From (extract email, take username part)
    try:
        from_header = msg.get('From', '')
        from_emails = extract_email_addresses(from_header)
        if from_emails:
            from_email = from_emails[0]
            from_part = from_email.split('@')[0]
            from_part = sanitize_filename_part(from_part, 30)
        else:
            from_part = "unknown"
    except:
        from_part = "unknown"
    
    # 3. Message-ID (extract unique part)
    try:
        message_id = msg.get('Message-ID', '')
        if message_id:
            # Remove < > and take first part before @
            message_id = message_id.strip('<>')
            message_id = message_id.split('@')[0]
            message_id = re.sub(r'[^a-zA-Z0-9]', '', message_id)
            message_id_part = message_id[:20]
        else:
            message_id_part = "nomsgid"
    except:
        message_id_part = "nomsgid"
    
    # 4. Subject snippet
    try:
        subject = decode_header_value(msg.get('Subject', ''))
        if not subject or subject.strip() == '':
            subject_part = "no_subject"
        else:
            subject_part = sanitize_filename_part(subject, 30)
    except:
        subject_part = "no_subject"
    
    # Combine all parts
    filename = f"{datetime_part}_{from_part}_{message_id_part}_{subject_part}.eml"
    
    # Final safety: ensure total length doesn't exceed 255 chars
    if len(filename) > 255:
        filename = filename[:251] + ".eml"
    
    return filename

# =============================================================================
# FILE COLLISION HANDLING
# =============================================================================

def get_unique_filename(output_dir, base_filename):
    """
    Ensure filename is unique by adding incremental suffix if needed.
    
    Args:
        output_dir: Output directory path
        base_filename: Desired filename
    
    Returns:
        Unique filename (may have _001, _002, etc. suffix)
    """
    filepath = os.path.join(output_dir, base_filename)
    
    # If file doesn't exist, use original name
    if not os.path.exists(filepath):
        return base_filename
    
    # File exists - find next available suffix
    name_without_ext, ext = os.path.splitext(base_filename)
    
    counter = 1
    while True:
        new_filename = f"{name_without_ext}_{counter:03d}{ext}"
        new_filepath = os.path.join(output_dir, new_filename)
        
        if not os.path.exists(new_filepath):
            return new_filename
        
        counter += 1
        
        # Safety limit
        if counter > 9999:
            # Fallback: add timestamp
            timestamp = int(time.time() * 1000)
            return f"{name_without_ext}_{timestamp}{ext}"

# =============================================================================
# EMAIL SAVING
# =============================================================================

def save_email_as_eml(msg, output_dir, filename):
    """
    Save email message as EML file (complete with attachments).
    
    Args:
        msg: email.message.Message object
        output_dir: Output directory
        filename: Filename to save as
    
    Returns:
        Success boolean
    """
    try:
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            gen = BytesGenerator(f)
            gen.flatten(msg)
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save email: {e}")
        return False

# =============================================================================
# CSV LOGGER
# =============================================================================

class CSVLogger:
    """CSV logger for extraction results."""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.fieldnames = [
            'filename',
            'original_filename',
            'collision',
            'date',
            'from_address',
            'to',
            'subject',
            'matched_keywords',
            'match_positions'
        ]
        
        # Create with headers if doesn't exist
        if not os.path.exists(filepath):
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def log(self, **kwargs):
        """Log a match to CSV."""
        try:
            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerow(kwargs)
        except Exception as e:
            print(f"[ERROR] Failed to write to log: {e}")

# =============================================================================
# SIGNAL HANDLER (Ctrl+C)
# =============================================================================

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n[!] Ctrl+C detected - graceful shutdown...")
    print(f"Processed: {processed_count}")
    print(f"Matches:   {matched_count}")
    print(f"Failed:    {failed_count}")
    print("\nPartial results saved.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_mbox(mbox_path, target_email, output_dir, failed_dir, log_file,
                 email_limit=None, dry_run=False, from_only=False):
    """
    Main processing function.

    Args:
        mbox_path: Path to mbox file
        target_email: Target email address (normalized lowercase)
        output_dir: Output directory for matched emails
        failed_dir: Directory for failed emails
        log_file: CSV log file path
        email_limit: Maximum emails to process (None = unlimited)
        dry_run: If True, only count matches without saving
        from_only: If True, only filter by From header (ignore To/Cc/Reply-To)

    Returns:
        Statistics dict
    """
    global processed_count, matched_count, failed_count
    
    # Initialize counters
    processed_count = 0
    matched_count = 0
    failed_count = 0
    
    # Initialize CSV logger
    csv_logger = CSVLogger(log_file) if not dry_run else None

    # Open mbox file
    print(f"\n[*] Opening mbox file: {mbox_path}")
    try:
        mbox = mailbox.mbox(mbox_path)
    except Exception as e:
        print(f"[ERROR] Failed to open mbox file: {e}")
        return None

    print(f"[*] Target email: {target_email}")
    if from_only:
        print(f"[*] Filter mode: From field only")
    else:
        print(f"[*] Filter mode: From/To/Cc/Reply-To fields")
    print(f"[*] Output dir: {output_dir}")
    if dry_run:
        print(f"[*] DRY RUN MODE - no files will be saved")
    if email_limit:
        print(f"[*] Email limit: {email_limit}")

    # Try to get total count for progress bar
    total_count = None
    if HAS_TQDM:
        print(f"[*] Counting emails in mbox file...")
        try:
            total_count = len(mbox)
            if email_limit:
                total_count = min(total_count, email_limit)
        except:
            pass  # Some mbox files don't support len()

    print(f"\n[*] Processing emails...\n")

    start_time = time.time()

    # Initialize progress bar
    progress = ProgressBar(total=total_count, enable=True)

    # Process each email
    for msg in mbox:
        # Check email limit
        if email_limit and processed_count >= email_limit:
            progress.finish()
            print(f"[*] Email limit ({email_limit}) reached. Stopping.")
            break

        processed_count += 1

        # Update progress bar
        progress.update(processed_count, matched_count, failed_count)
        
        try:
            # === FILTER 1: Email match ===
            if not email_involves_target(msg, target_email, from_only=from_only):
                continue
            
            # === CONTENT EXTRACTION ===
            # Get subject
            subject = decode_header_value(msg.get('Subject', ''))
            if not subject or subject.strip() == '':
                subject = "(No Subject)"
            
            # Get body
            body = extract_email_body(msg)
            
            # Combine subject and body for searching
            if not body or len(body.strip()) < 10:
                # Body too short or empty - use only subject
                search_text = subject
            else:
                search_text = subject + " " + body
            
            # === NORMALIZE ===
            normalized_text = normalize_text(search_text)
            
            # === FILTER 2: Keyword match ===
            has_match, keywords, positions = contains_vacation_keyword(normalized_text)
            
            if not has_match:
                continue
            
            # === MATCH FOUND! ===
            matched_count += 1
            
            if not dry_run:
                # Generate filename
                base_filename = generate_eml_filename(msg)
                
                # Handle collisions
                actual_filename = get_unique_filename(output_dir, base_filename)
                
                # Log collision if needed
                is_collision = (actual_filename != base_filename)
                if is_collision:
                    print(f"[WARN] Collision: {base_filename} -> {actual_filename}")
                
                # Save email
                success = save_email_as_eml(msg, output_dir, actual_filename)
                
                if success:
                    # Log to CSV
                    csv_logger.log(
                        filename=actual_filename,
                        original_filename=base_filename,
                        collision=str(is_collision),
                        date=msg.get('Date', ''),
                        from_address=msg.get('From', ''),
                        to=msg.get('To', ''),
                        subject=subject,
                        matched_keywords=', '.join(keywords),
                        match_positions=', '.join(positions)
                    )
        
        except Exception as e:
            # Handle failed emails
            failed_count += 1
            
            print(f"[ERROR] Failed to process email #{processed_count}: {e}")
            
            if not dry_run:
                # Try to save to failed directory
                try:
                    failed_filename = f"failed_email_{failed_count:04d}.eml"
                    save_email_as_eml(msg, failed_dir, failed_filename)
                except:
                    pass
    
    # Close mbox
    mbox.close()

    # Finish progress bar
    progress.finish()

    # Calculate elapsed time
    elapsed = time.time() - start_time
    
    # Print summary
    print("\n" + "="*50)
    print("EXTRACTION COMPLETE")
    print("="*50)
    print(f"Total processed: {processed_count:,}")
    print(f"Matches found:   {matched_count}")
    print(f"Failed emails:   {failed_count}")
    print(f"\nOutput dir:      {output_dir}")
    if not dry_run:
        print(f"Log file:        {log_file}")
    print(f"\nTime elapsed:    {elapsed:.2f} seconds")
    print("="*50 + "\n")
    
    return {
        'processed': processed_count,
        'matched': matched_count,
        'failed': failed_count,
        'elapsed': elapsed
    }

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract vacation/OOO related emails from mbox file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python vacation_email_extractor.py --mbox archive.mbox --email jan.novak@firma.cz

  # With custom output directory
  python vacation_email_extractor.py --mbox archive.mbox --email jan@firma.cz --output ./results

  # Filter only emails FROM the target address (ignore To/Cc/Reply-To)
  python vacation_email_extractor.py --mbox archive.mbox --email jan@firma.cz --from-only

  # Dry run (count matches only)
  python vacation_email_extractor.py --mbox archive.mbox --email jan@firma.cz --dry-run

  # Process only first 100 emails
  python vacation_email_extractor.py --mbox archive.mbox --email jan@firma.cz --email-limit 100
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--mbox',
        required=True,
        help='Path to mbox file'
    )
    
    parser.add_argument(
        '--email',
        required=True,
        help='Target email address (case-insensitive)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output',
        default='./output',
        help='Output directory (default: ./output)'
    )
    
    parser.add_argument(
        '--email-limit',
        type=int,
        default=None,
        help='Maximum number of emails to process (default: unlimited)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Count matches only, do not save files'
    )
    
    parser.add_argument(
        '--log-file',
        default='extraction_log.csv',
        help='CSV log file path (default: extraction_log.csv)'
    )

    parser.add_argument(
        '--from-only',
        action='store_true',
        help='Filter emails only by From field (ignore To/Cc/Reply-To)'
    )

    args = parser.parse_args()
    
    # Validate mbox file
    if not os.path.exists(args.mbox):
        print(f"[ERROR] Mbox file not found: {args.mbox}")
        sys.exit(1)
    
    if not os.path.isfile(args.mbox):
        print(f"[ERROR] Not a file: {args.mbox}")
        sys.exit(1)
    
    # Normalize target email
    target_email = args.email.lower().strip()
    
    # Validate email format (basic)
    if '@' not in target_email:
        print(f"[ERROR] Invalid email format: {args.email}")
        sys.exit(1)
    
    # Create output directories
    output_dir = args.output
    failed_dir = os.path.join(output_dir, 'failed')
    
    if not args.dry_run:
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            Path(failed_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Failed to create output directories: {e}")
            sys.exit(1)
    
    # Run processing
    print("\n" + "="*50)
    print("VACATION EMAIL EXTRACTOR v1.0")
    print("="*50)
    
    stats = process_mbox(
        mbox_path=args.mbox,
        target_email=target_email,
        output_dir=output_dir,
        failed_dir=failed_dir,
        log_file=args.log_file,
        email_limit=args.email_limit,
        dry_run=args.dry_run,
        from_only=args.from_only
    )
    
    if stats is None:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
