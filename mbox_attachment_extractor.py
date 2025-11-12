#!/usr/bin/env python3
"""
MBOX Attachment Extractor by Regex
===================================
Extract emails with attachments matching regex patterns from mbox files.

Author: Claude
Version: 1.0
"""

import mailbox
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.generator import BytesGenerator
import re
import argparse
import os
import sys
import csv
import signal
import uuid
from pathlib import Path
from datetime import datetime
import time
import mimetypes

# Try to import tqdm for progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# =============================================================================
# GLOBAL COUNTERS (for signal handler)
# =============================================================================
processed_count = 0
matched_count = 0
failed_count = 0
attachment_count = 0

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

    def update(self, processed, matched, failed, attachments):
        """
        Update progress bar.

        Args:
            processed: Number of emails processed
            matched: Number of matches found
            failed: Number of failed emails
            attachments: Total attachments extracted
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
            f"Attachments: {attachments} | "
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
        text: Input text (may contain Czech/accented characters)

    Returns:
        Normalized text (lowercase, no diacritics)
    """
    if not text:
        return ""

    # Mapping of diacritics to ASCII (Czech + common European)
    replacements = {
        'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a', 'ã': 'a', 'å': 'a',
        'č': 'c', 'ç': 'c', 'ć': 'c',
        'ď': 'd',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'ě': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ň': 'n', 'ñ': 'n',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o', 'õ': 'o', 'ø': 'o',
        'ř': 'r',
        'š': 's', 'ś': 's',
        'ť': 't',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u', 'ů': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ž': 'z', 'ź': 'z', 'ż': 'z'
    }

    text = text.lower()
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)

    return text

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
# ATTACHMENT EXTRACTION
# =============================================================================

def get_attachment_filename(part):
    """
    Extract filename from email part (handles both Content-Disposition and Content-Type).

    Args:
        part: email.message.Message part

    Returns:
        Decoded filename or None
    """
    filename = None

    # Try Content-Disposition first (most common)
    if part.get_content_disposition():
        filename = part.get_filename()

    # Try Content-Type name parameter (for inline attachments)
    if not filename:
        content_type = part.get_content_type()
        if part.get_param('name'):
            filename = part.get_param('name')

    if not filename:
        return None

    # Decode filename (may be RFC 2231 encoded)
    try:
        # Handle RFC 2231 encoding (e.g., filename*=utf-8''file%20name.pdf)
        if isinstance(filename, tuple):
            filename = filename[2]

        # Decode if it's encoded-word format
        filename = decode_header_value(filename)

        return filename
    except:
        return str(filename) if filename else None

def extract_attachments(msg, pattern, case_sensitive=False):
    """
    Extract all attachments from email that match the regex pattern.

    Args:
        msg: email.message.Message object
        pattern: Compiled regex pattern
        case_sensitive: Whether original matching was case-sensitive

    Returns:
        List of tuples: (normalized_filename, original_filename, payload, content_type)
    """
    attachments = []

    try:
        # Walk through all parts
        for part in msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == 'multipart':
                continue

            # Get filename
            filename = get_attachment_filename(part)
            if not filename:
                continue

            # Store original filename
            original_filename = filename

            # Normalize filename for pattern matching
            normalized_filename = normalize_text(filename)

            # Check if filename matches pattern
            if pattern.search(normalized_filename):
                # Get payload
                payload = part.get_payload(decode=True)
                if payload:
                    content_type = part.get_content_type()
                    attachments.append((
                        normalized_filename,
                        original_filename,
                        payload,
                        content_type
                    ))

    except Exception as e:
        # If attachment extraction fails, return what we have so far
        pass

    return attachments

# =============================================================================
# EMAIL SAVING
# =============================================================================

def save_email_as_eml(msg, output_dir, uuid_str):
    """
    Save email message as EML file.

    Args:
        msg: email.message.Message object
        output_dir: Output directory
        uuid_str: UUID string for filename

    Returns:
        Filename if successful, None otherwise
    """
    try:
        filename = f"{uuid_str}.eml"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            gen = BytesGenerator(f)
            gen.flatten(msg)

        return filename
    except Exception as e:
        print(f"[ERROR] Failed to save email: {e}")
        return None

def save_attachment(payload, output_dir, uuid_str, counter, original_filename):
    """
    Save attachment to file.

    Args:
        payload: Attachment bytes
        output_dir: Output directory
        uuid_str: UUID string for filename
        counter: Attachment counter (1-indexed)
        original_filename: Original filename (for extension)

    Returns:
        Tuple: (saved_filename, file_size) or (None, 0) on error
    """
    try:
        # Extract extension from original filename
        _, ext = os.path.splitext(original_filename)
        if not ext:
            # Try to guess extension from content
            ext = '.bin'

        # Create filename: UUID_001.ext, UUID_002.ext, etc.
        filename = f"{uuid_str}_{counter:03d}{ext}"
        filepath = os.path.join(output_dir, filename)

        # Save payload
        with open(filepath, 'wb') as f:
            f.write(payload)

        file_size = len(payload)
        return (filename, file_size)

    except Exception as e:
        print(f"[ERROR] Failed to save attachment: {e}")
        return (None, 0)

# =============================================================================
# CSV LOGGER
# =============================================================================

class CSVLogger:
    """CSV logger for extraction results."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.fieldnames = [
            'uuid',
            'eml_filename',
            'date',
            'from_address',
            'subject',
            'message_id',
            'attachment_count',
            'attachment_names',
            'attachment_sizes',
            'attachment_types',
            'total_size_bytes',
            'processing_time_ms'
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
    print(f"Processed:   {processed_count}")
    print(f"Matches:     {matched_count}")
    print(f"Attachments: {attachment_count}")
    print(f"Failed:      {failed_count}")
    print("\nPartial results saved.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_mbox(mbox_path, pattern_str, output_dir, failed_dir, log_file,
                 email_limit=None, dry_run=False, case_sensitive=False):
    """
    Main processing function.

    Args:
        mbox_path: Path to mbox file
        pattern_str: Regex pattern string
        output_dir: Output directory for matched emails and attachments
        failed_dir: Directory for failed emails
        log_file: CSV log file path
        email_limit: Maximum emails to process (None = unlimited)
        dry_run: If True, only count matches without saving
        case_sensitive: If True, case-sensitive regex matching

    Returns:
        Statistics dict
    """
    global processed_count, matched_count, failed_count, attachment_count

    # Initialize counters
    processed_count = 0
    matched_count = 0
    failed_count = 0
    attachment_count = 0

    # Compile regex pattern
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(pattern_str, flags)
    except Exception as e:
        print(f"[ERROR] Invalid regex pattern: {e}")
        return None

    # Initialize CSV logger
    csv_logger = CSVLogger(log_file) if not dry_run else None

    # Open mbox file
    print(f"\n[*] Opening mbox file: {mbox_path}")
    try:
        mbox = mailbox.mbox(mbox_path)
    except Exception as e:
        print(f"[ERROR] Failed to open mbox file: {e}")
        return None

    print(f"[*] Pattern: {pattern_str}")
    print(f"[*] Case sensitive: {case_sensitive}")
    print(f"[*] Output dir: {output_dir}")
    if dry_run:
        print(f"[*] DRY RUN MODE - no files will be saved")
    if email_limit:
        print(f"[*] Email limit: {email_limit}")

    print(f"\n[*] Processing emails...\n")

    start_time = time.time()

    # Initialize progress bar (no total count - avoids pre-scanning entire mbox)
    progress = ProgressBar(total=None, enable=True)

    # Process each email
    for msg in mbox:
        # Check email limit
        if email_limit and processed_count >= email_limit:
            progress.finish()
            print(f"[*] Email limit ({email_limit}) reached. Stopping.")
            break

        processed_count += 1

        # Update progress bar
        progress.update(processed_count, matched_count, failed_count, attachment_count)

        try:
            # Extract attachments that match pattern
            start_process_time = time.time()
            attachments = extract_attachments(msg, pattern, case_sensitive)

            if not attachments:
                continue

            # === MATCH FOUND! ===
            matched_count += 1
            attachment_count += len(attachments)

            if not dry_run:
                # Generate UUID for this email
                uuid_str = str(uuid.uuid4())

                # Save email as EML
                eml_filename = save_email_as_eml(msg, output_dir, uuid_str)

                if not eml_filename:
                    failed_count += 1
                    continue

                # Save all matching attachments
                attachment_filenames = []
                attachment_sizes = []
                attachment_types = []
                total_size = 0

                for idx, (norm_name, orig_name, payload, content_type) in enumerate(attachments, start=1):
                    att_filename, att_size = save_attachment(
                        payload, output_dir, uuid_str, idx, orig_name
                    )

                    if att_filename:
                        attachment_filenames.append(orig_name)
                        attachment_sizes.append(str(att_size))
                        attachment_types.append(content_type)
                        total_size += att_size

                # Calculate processing time
                process_time_ms = int((time.time() - start_process_time) * 1000)

                # Log to CSV
                csv_logger.log(
                    uuid=uuid_str,
                    eml_filename=eml_filename,
                    date=msg.get('Date', ''),
                    from_address=msg.get('From', ''),
                    subject=decode_header_value(msg.get('Subject', '(No Subject)')),
                    message_id=msg.get('Message-ID', ''),
                    attachment_count=len(attachments),
                    attachment_names=' | '.join(attachment_filenames),
                    attachment_sizes=' | '.join(attachment_sizes),
                    attachment_types=' | '.join(attachment_types),
                    total_size_bytes=total_size,
                    processing_time_ms=process_time_ms
                )

        except Exception as e:
            # Handle failed emails
            failed_count += 1

            print(f"\n[ERROR] Failed to process email #{processed_count}: {e}")

            if not dry_run:
                # Try to save to failed directory
                try:
                    failed_uuid = str(uuid.uuid4())
                    save_email_as_eml(msg, failed_dir, failed_uuid)
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
    print(f"Total processed:  {processed_count:,}")
    print(f"Matches found:    {matched_count}")
    print(f"Attachments:      {attachment_count}")
    print(f"Failed emails:    {failed_count}")
    print(f"\nOutput dir:       {output_dir}")
    if not dry_run:
        print(f"Log file:         {log_file}")
    print(f"\nTime elapsed:     {elapsed:.2f} seconds")
    if matched_count > 0:
        print(f"Avg per match:    {elapsed/matched_count:.2f} seconds")
    print("="*50 + "\n")

    return {
        'processed': processed_count,
        'matched': matched_count,
        'attachments': attachment_count,
        'failed': failed_count,
        'elapsed': elapsed
    }

# =============================================================================
# DIRECTORY PROCESSING
# =============================================================================

def find_mbox_files(input_path):
    """
    Find all mbox files in input path (file or directory).

    Args:
        input_path: Path to mbox file or directory

    Returns:
        List of mbox file paths
    """
    input_path = Path(input_path)

    if input_path.is_file():
        return [str(input_path)]

    elif input_path.is_dir():
        # Find all .mbox files in directory (non-recursive)
        mbox_files = list(input_path.glob('*.mbox'))
        # Also check for files without extension (common for mbox)
        for item in input_path.iterdir():
            if item.is_file() and item.suffix == '':
                # Check if it looks like an mbox file (starts with "From ")
                try:
                    with open(item, 'r', encoding='latin1', errors='ignore') as f:
                        first_line = f.readline()
                        if first_line.startswith('From '):
                            mbox_files.append(item)
                except:
                    pass

        return [str(f) for f in mbox_files]

    else:
        return []

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point."""

    # Custom formatter to preserve formatting in epilog
    class CustomFormatter(argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(
        description='Extract emails with attachments matching regex patterns from mbox files',
        formatter_class=CustomFormatter,
        epilog="""
Regex Examples:
  --name "\\.pdf$"                      All PDF files
  --name "invoice.*\\.xlsx?"            Excel invoices (xlsx or xls)
  --name "report_\\d{4}\\.docx"         report_2024.docx format
  --name "(?i)faktura"                  Case-insensitive "faktura" (or use without --case-sensitive)
  --name "^contract.*\\.(pdf|docx)$"    Contracts (PDF or DOCX)
  --name "logo.*\\.png"                 Logo images (including inline)
  --name "attachment.*"                 Any file starting with "attachment"
  --name "\\.(zip|rar|7z)$"             Archives
  --name "^[A-Z]{2}\\d{6}"              Format like AB123456

Examples:
  # Basic usage - single mbox file
  python mbox_attachment_extractor.py --name "\\.pdf$" --input archive.mbox --output ./results --log extraction.csv

  # Directory of mbox files (auto-detect all .mbox files)
  python mbox_attachment_extractor.py --name "invoice" --input ./mbox_dir --output ./results --log extraction.csv

  # Dry run to count matches
  python mbox_attachment_extractor.py --name "\\.docx$" --input archive.mbox --output ./results --log extraction.csv --dry-run

  # Case-sensitive matching
  python mbox_attachment_extractor.py --name "CONTRACT" --input archive.mbox --output ./results --log extraction.csv --case-sensitive

  # Process only first 100 emails for testing
  python mbox_attachment_extractor.py --name "\\.pdf$" --input archive.mbox --output ./results --log extraction.csv --email-limit 100

  # Extract logo images (including inline attachments)
  python mbox_attachment_extractor.py --name "logo.*\\.png" --input archive.mbox --output ./results --log extraction.csv

Note:
  - Attachment names are normalized to lowercase ASCII before regex matching (removes accents: č→c, ž→z, etc.)
  - Regex is case-insensitive by default (use --case-sensitive for exact case matching)
  - Both regular and inline attachments are extracted if they match the pattern
  - Emails saved as UUID.eml, attachments as UUID_001.ext, UUID_002.ext, etc.
  - All encoding variants (base64, quoted-printable, etc.) are handled automatically
        """
    )

    # Required arguments
    parser.add_argument(
        '--name',
        required=True,
        help='Regex pattern for attachment filename matching'
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Path to mbox file or directory containing mbox files'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for extracted emails and attachments'
    )

    parser.add_argument(
        '--log',
        required=True,
        help='CSV log file path'
    )

    # Optional arguments
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
        '--case-sensitive',
        action='store_true',
        help='Use case-sensitive regex matching (default: case-insensitive)'
    )

    args = parser.parse_args()

    # Validate input path
    if not os.path.exists(args.input):
        print(f"[ERROR] Input path not found: {args.input}")
        sys.exit(1)

    # Find mbox files
    mbox_files = find_mbox_files(args.input)

    if not mbox_files:
        print(f"[ERROR] No mbox files found in: {args.input}")
        sys.exit(1)

    print(f"\n[*] Found {len(mbox_files)} mbox file(s)")
    for mf in mbox_files:
        print(f"    - {mf}")

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

    # Print header
    print("\n" + "="*50)
    print("MBOX ATTACHMENT EXTRACTOR v1.0")
    print("="*50)

    # Process each mbox file
    total_stats = {
        'processed': 0,
        'matched': 0,
        'attachments': 0,
        'failed': 0,
        'elapsed': 0
    }

    for mbox_path in mbox_files:
        stats = process_mbox(
            mbox_path=mbox_path,
            pattern_str=args.name,
            output_dir=output_dir,
            failed_dir=failed_dir,
            log_file=args.log,
            email_limit=args.email_limit,
            dry_run=args.dry_run,
            case_sensitive=args.case_sensitive
        )

        if stats is None:
            sys.exit(1)

        # Accumulate stats
        for key in total_stats:
            total_stats[key] += stats[key]

    # Print final summary if multiple files
    if len(mbox_files) > 1:
        print("\n" + "="*50)
        print("TOTAL SUMMARY (ALL FILES)")
        print("="*50)
        print(f"Total processed:  {total_stats['processed']:,}")
        print(f"Matches found:    {total_stats['matched']}")
        print(f"Attachments:      {total_stats['attachments']}")
        print(f"Failed emails:    {total_stats['failed']}")
        print(f"\nTotal time:       {total_stats['elapsed']:.2f} seconds")
        print("="*50 + "\n")

    sys.exit(0)

if __name__ == '__main__':
    main()
