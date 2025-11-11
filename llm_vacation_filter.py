#!/usr/bin/env python3
"""
LLM-Based Vacation Email Filter
================================
Uses Azure OpenAI to filter vacation/OOO emails and reduce false positives.

Takes EML files from vacation_email_extractor.py output and uses LLM to
determine which are genuine vacation responses vs. false positives.

Author: Claude
Version: 1.2
"""

import os
import sys
import json
import csv
import time
import signal
import argparse
import email
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from datetime import datetime
import shutil
import re

# Third-party imports
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("[ERROR] python-dotenv not installed. Install with: pip install python-dotenv")
    sys.exit(1)

try:
    from openai import AzureOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[ERROR] openai package not installed. Install with: pip install openai")
    sys.exit(1)

# =============================================================================
# GLOBAL CONFIGURATION
# =============================================================================

# Global counters (for signal handler)
processed_count = 0
matched_count = 0
rejected_count = 0
failed_count = 0
total_input_tokens = 0
total_output_tokens = 0
total_cost_usd = 0.0

# Azure OpenAI client (initialized in main)
openai_client = None
deployment_name = None
price_input = 0.0
price_output = 0.0

# =============================================================================
# QUOTE PATTERNS (reused from vacation_email_extractor.py)
# =============================================================================

QUOTE_PATTERNS = [
    # === Gmail / Standard ===
    r'^On\s+.+\d{4}.+wrote:\s*$',
    r'^On\s+\d{1,2}/\d{1,2}/\d{2,4}.+wrote:\s*$',

    # === Czech Thunderbird / Standard ===
    r'^Dne\s+\d{1,2}\.\d{1,2}\.\d{2,4}.+napsal',
    r'^Dne\s+.+napsal\(a\):',

    # === Outlook ===
    r'^-{3,}.*Original.*Message.*-{3,}',
    r'^_{5,}\s*$',
    r'^From:\s*.+$',

    # === Quote prefix lines ===
    r'^\s*>+',
    r'^\s*\|',

    # === Date-based headers ===
    r'^\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}.+wrote:',
    r'^\[\d{4}-\d{2}-\d{2}',
]

COMPILED_QUOTE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in QUOTE_PATTERNS]

# =============================================================================
# SIGNAL HANDLER (Ctrl+C)
# =============================================================================

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n[!] Ctrl+C detected - graceful shutdown...")
    print(f"Processed: {processed_count}")
    print(f"Matched:   {matched_count}")
    print(f"Rejected:  {rejected_count}")
    print(f"Failed:    {failed_count}")
    print(f"Tokens:    {total_input_tokens + total_output_tokens:,}")
    print(f"Cost:      ${total_cost_usd:.4f} USD")
    print("\nPartial results saved.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

# =============================================================================
# HELPER FUNCTIONS (reused from vacation_email_extractor.py)
# =============================================================================

def decode_header_value(header_value):
    """Decode email header value (handles encoded words)."""
    if not header_value:
        return ""

    try:
        decoded_parts = decode_header(header_value)
        result = []

        for content, charset in decoded_parts:
            if isinstance(content, bytes):
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

def decode_with_fallback(payload, charset):
    """Decode payload with charset fallback."""
    if not payload:
        return ""

    charsets_to_try = [charset, 'cp1250', 'utf-8', 'latin1']

    for cs in charsets_to_try:
        if cs is None:
            continue
        try:
            return payload.decode(cs)
        except:
            continue

    return payload.decode('latin1', errors='ignore')

def html_to_text(html):
    """Convert HTML to plain text (simple version without BeautifulSoup)."""
    if not html:
        return ""

    # Simple HTML tag removal
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_email_body(msg):
    """Extract complete text body from email."""
    text_parts = []

    try:
        if msg.is_multipart():
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
        pass

    return ' '.join(text_parts)

def extract_immediate_reply(body_text):
    """Extract only the immediate reply from email body, filtering out quoted history."""
    if not body_text or len(body_text.strip()) < 10:
        return body_text

    lines = body_text.split('\n')
    immediate_lines = []
    quote_detected = False

    for line in lines:
        is_quote_line = False

        for pattern in COMPILED_QUOTE_PATTERNS:
            if pattern.match(line):
                is_quote_line = True
                quote_detected = True
                break

        if is_quote_line:
            break

        immediate_lines.append(line)

    immediate_text = '\n'.join(immediate_lines).strip()

    MIN_REPLY_LENGTH = 20

    if quote_detected:
        return immediate_text if immediate_text else body_text
    elif len(immediate_text) < MIN_REPLY_LENGTH:
        return body_text
    else:
        return immediate_text

# =============================================================================
# EML FILE READING
# =============================================================================

def read_eml_file(filepath):
    """
    Read EML file and return parsed message.

    Args:
        filepath: Path to EML file

    Returns:
        email.message.Message object or None on error
    """
    try:
        with open(filepath, 'rb') as f:
            msg = email.message_from_binary_file(f)
        return msg
    except Exception as e:
        print(f"[ERROR] Failed to read {filepath}: {e}")
        return None

# =============================================================================
# AZURE OPENAI CLIENT
# =============================================================================

def initialize_azure_openai():
    """
    Initialize Azure OpenAI client from .env configuration.

    Returns:
        Tuple: (client, deployment_name, price_input, price_output) or (None, None, 0, 0) on error
    """
    global openai_client, deployment_name, price_input, price_output

    # Load .env file
    if not load_dotenv():
        print("[WARNING] No .env file found in current directory")

    # Get configuration from environment
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

    # Pricing (USD per 1 million tokens)
    price_in = float(os.getenv('AZURE_OPENAI_PRICE_INPUT', '0.15'))
    price_out = float(os.getenv('AZURE_OPENAI_PRICE_OUTPUT', '0.60'))

    # Validate required fields
    if not endpoint:
        print("[ERROR] AZURE_OPENAI_ENDPOINT not set in .env")
        return None, None, 0, 0

    if not api_key:
        print("[ERROR] AZURE_OPENAI_API_KEY not set in .env")
        return None, None, 0, 0

    if not deployment:
        print("[ERROR] AZURE_OPENAI_DEPLOYMENT not set in .env")
        return None, None, 0, 0

    # Create client
    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )

        print(f"[✓] Azure OpenAI configured: {deployment}")
        return client, deployment, price_in, price_out

    except Exception as e:
        print(f"[ERROR] Failed to initialize Azure OpenAI: {e}")
        return None, None, 0, 0

# =============================================================================
# LLM ANALYSIS
# =============================================================================

def analyze_email_with_llm(system_prompt, user_prompt, email_data, max_retries=1):
    """
    Send email to LLM for analysis.

    Args:
        system_prompt: System prompt text
        user_prompt: User prompt text
        email_data: Dict with email metadata
        max_retries: Number of retries on failure (default: 1)

    Returns:
        Dict with keys: success, decision, confidence, reasoning,
                       input_tokens, output_tokens, error
    """
    global openai_client, deployment_name, total_input_tokens, total_output_tokens, total_cost_usd, price_input, price_output

    # Construct full user message
    user_message = f"""{user_prompt}

EMAIL TO ANALYZE:
From: {email_data['from']}
Date: {email_data['date']}
Subject: {email_data['subject']}

{email_data['body']}

Respond with JSON only:
{{"is_vacation_response": true/false, "confidence": 0.95, "reasoning": "brief explanation"}}"""

    # Try API call with retries
    for attempt in range(max_retries + 1):
        try:
            response = openai_client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_completion_tokens=500
            )

            # Extract tokens
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # Update global counters
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens

            # Calculate cost
            cost = (input_tokens / 1_000_000 * price_input) + (output_tokens / 1_000_000 * price_output)
            total_cost_usd += cost

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            # Validate result structure
            if 'is_vacation_response' not in result or 'confidence' not in result:
                raise ValueError("Invalid JSON structure from LLM")

            return {
                'success': True,
                'decision': result['is_vacation_response'],
                'confidence': result['confidence'],
                'reasoning': result.get('reasoning', ''),
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'error': None
            }

        except Exception as e:
            error_msg = str(e)

            # If this is not the last attempt, retry
            if attempt < max_retries:
                print(f"[WARN] API call failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                time.sleep(2)  # Wait before retry
                continue

            # Last attempt failed
            return {
                'success': False,
                'decision': False,
                'confidence': 0.0,
                'reasoning': '',
                'input_tokens': 0,
                'output_tokens': 0,
                'error': error_msg
            }

    # Should not reach here
    return {
        'success': False,
        'decision': False,
        'confidence': 0.0,
        'reasoning': '',
        'input_tokens': 0,
        'output_tokens': 0,
        'error': 'Unknown error'
    }

# =============================================================================
# FILE OPERATIONS
# =============================================================================

def copy_with_confidence_prefix(src_path, dest_dir, confidence):
    """
    Copy EML file to destination with confidence score prefix.

    Args:
        src_path: Source file path
        dest_dir: Destination directory
        confidence: Confidence score (0.0-1.0)

    Returns:
        New filename or None on error
    """
    try:
        # Get original filename
        original_name = os.path.basename(src_path)

        # Convert confidence to 0-100 integer
        confidence_int = int(confidence * 100)

        # Create new filename with confidence prefix
        new_name = f"{confidence_int:02d}_{original_name}"

        # Ensure destination directory exists
        Path(dest_dir).mkdir(parents=True, exist_ok=True)

        # Copy file
        dest_path = os.path.join(dest_dir, new_name)
        shutil.copy2(src_path, dest_path)

        return new_name

    except Exception as e:
        print(f"[ERROR] Failed to copy {src_path}: {e}")
        return None

# =============================================================================
# CSV LOGGER
# =============================================================================

class CSVLogger:
    """CSV logger for filtering results."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.fieldnames = [
            'filename',
            'processed_at',
            'llm_decision',
            'confidence',
            'reasoning',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'processing_time_ms',
            'error_message',
            'retried',
            'from_address',
            'subject',
            'output_filename'
        ]

        # Create with headers
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()

    def log(self, **kwargs):
        """Log a result to CSV."""
        try:
            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerow(kwargs)
        except Exception as e:
            print(f"[ERROR] Failed to write to log: {e}")

# =============================================================================
# PROGRESS TRACKING
# =============================================================================

class ProgressTracker:
    """Track and display progress."""

    def __init__(self, total):
        self.total = total
        self.start_time = time.time()
        self.last_update = 0

    def update(self, processed, matched, rejected, failed):
        """Update progress display."""
        current_time = time.time()

        # Update every 0.5 seconds
        if current_time - self.last_update < 0.5 and processed != self.total:
            return

        self.last_update = current_time
        elapsed = current_time - self.start_time

        # Calculate stats
        percentage = (processed / self.total * 100) if self.total > 0 else 0
        speed = processed / elapsed if elapsed > 0 else 0

        # Calculate ETA
        if speed > 0 and processed < self.total:
            remaining = (self.total - processed) / speed
            eta_str = f"| ETA: {self._format_time(remaining)}"
        else:
            eta_str = ""

        # Build status line
        status = (
            f"\rProcessing: {processed}/{self.total} ({percentage:.1f}%) | "
            f"✓ Matched: {matched} | ✗ Rejected: {rejected} | ⚠ Failed: {failed}\n"
            f"Tokens: {total_input_tokens + total_output_tokens:,} "
            f"(in: {total_input_tokens:,}, out: {total_output_tokens:,}) | "
            f"Cost: ${total_cost_usd:.4f} | "
            f"Speed: {speed:.1f}/s {eta_str}"
        )

        print(status + " " * 10, end='', flush=True)

    def finish(self):
        """Finish progress tracking."""
        print("\n")

    def _format_time(self, seconds):
        """Format seconds to human readable time."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_emails(input_dir, system_prompt_path, user_prompt_path,
                   output_dir, log_file, email_limit=None, debug=False):
    """
    Main processing function.

    Args:
        input_dir: Input directory with EML files
        system_prompt_path: Path to system prompt file
        user_prompt_path: Path to user prompt file
        output_dir: Output directory
        log_file: CSV log file path
        email_limit: Maximum emails to process (None = unlimited)
        debug: Show debug output (default: False)

    Returns:
        Statistics dict
    """
    global processed_count, matched_count, rejected_count, failed_count
    global total_input_tokens, total_output_tokens, total_cost_usd

    # Reset counters
    processed_count = 0
    matched_count = 0
    rejected_count = 0
    failed_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0

    # Load prompt files
    print(f"\n[*] Loading prompts...")

    try:
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
        print(f"[✓] System prompt: {system_prompt_path} ({len(system_prompt)} chars)")
    except Exception as e:
        print(f"[ERROR] Failed to read system prompt: {e}")
        return None

    try:
        with open(user_prompt_path, 'r', encoding='utf-8') as f:
            user_prompt = f.read().strip()
        print(f"[✓] User prompt: {user_prompt_path} ({len(user_prompt)} chars)")
    except Exception as e:
        print(f"[ERROR] Failed to read user prompt: {e}")
        return None

    # Get list of EML files
    eml_files = list(Path(input_dir).glob('*.eml'))

    if email_limit:
        eml_files = eml_files[:email_limit]

    total_files = len(eml_files)

    if total_files == 0:
        print(f"[ERROR] No EML files found in {input_dir}")
        return None

    print(f"[✓] Input directory: {total_files} EML files found")

    # Create output directories
    matched_dir = os.path.join(output_dir, 'matched')
    rejected_dir = os.path.join(output_dir, 'rejected')
    failed_dir = os.path.join(output_dir, 'failed')

    Path(matched_dir).mkdir(parents=True, exist_ok=True)
    Path(rejected_dir).mkdir(parents=True, exist_ok=True)
    Path(failed_dir).mkdir(parents=True, exist_ok=True)

    # Initialize CSV logger
    csv_logger = CSVLogger(log_file)

    # Initialize progress tracker
    progress = ProgressTracker(total_files)

    print(f"\n[*] Processing emails...\n")

    start_time = time.time()

    # Process each EML file
    for eml_path in eml_files:
        processing_start = time.time()
        processed_count += 1

        filename = eml_path.name

        # Read EML file
        msg = read_eml_file(eml_path)
        if not msg:
            failed_count += 1

            # Copy to failed directory
            try:
                shutil.copy2(eml_path, os.path.join(failed_dir, f"failed_{filename}"))
            except:
                pass

            # Log failure
            csv_logger.log(
                filename=filename,
                processed_at=datetime.now().isoformat(),
                llm_decision='error',
                confidence=0.0,
                reasoning='',
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                processing_time_ms=0,
                error_message='Failed to read EML file',
                retried='false',
                from_address='',
                subject='',
                output_filename=f"failed_{filename}"
            )

            progress.update(processed_count, matched_count, rejected_count, failed_count)
            continue

        # Extract email data
        try:
            from_addr = decode_header_value(msg.get('From', ''))
            subject = decode_header_value(msg.get('Subject', ''))
            date_str = msg.get('Date', '')
            body = extract_email_body(msg)
            immediate_reply = extract_immediate_reply(body)

            # Debug output
            if debug:
                print("\n" + "=" * 80)
                print(f"[DEBUG] Email: {filename}")
                print("=" * 80)
                print(f"From: {from_addr}")
                print(f"Date: {date_str}")
                print(f"Subject: {subject}")
                print(f"\nFull body length: {len(body):,} chars")
                print(f"Immediate reply length: {len(immediate_reply):,} chars")

                # Show truncation info if applicable
                if len(immediate_reply) > 4000:
                    print(f"(Will be truncated to 4000 chars for LLM)")

                print("\n--- Immediate Reply Text (sent to LLM) ---")
                display_text = immediate_reply[:4000] if len(immediate_reply) > 4000 else immediate_reply
                # Limit display to 500 chars for readability
                if len(display_text) > 500:
                    print(display_text[:500])
                    print(f"\n... [{len(display_text) - 500} more chars] ...")
                else:
                    print(display_text)
                print("--- End of Immediate Reply ---\n")

            email_data = {
                'from': from_addr,
                'date': date_str,
                'subject': subject,
                'body': immediate_reply[:4000]  # Limit to 4000 chars to avoid token limits
            }

        except Exception as e:
            failed_count += 1

            # Copy to failed directory
            try:
                shutil.copy2(eml_path, os.path.join(failed_dir, f"failed_{filename}"))
            except:
                pass

            # Log failure
            csv_logger.log(
                filename=filename,
                processed_at=datetime.now().isoformat(),
                llm_decision='error',
                confidence=0.0,
                reasoning='',
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                processing_time_ms=int((time.time() - processing_start) * 1000),
                error_message=f'Failed to extract email data: {str(e)}',
                retried='false',
                from_address='',
                subject='',
                output_filename=f"failed_{filename}"
            )

            progress.update(processed_count, matched_count, rejected_count, failed_count)
            continue

        # Analyze with LLM
        result = analyze_email_with_llm(system_prompt, user_prompt, email_data)

        processing_time_ms = int((time.time() - processing_start) * 1000)

        # Handle result
        if not result['success']:
            failed_count += 1

            # Copy to failed directory
            try:
                shutil.copy2(eml_path, os.path.join(failed_dir, f"failed_{filename}"))
            except:
                pass

            output_filename = f"failed_{filename}"

        else:
            # Successful analysis
            decision = result['decision']
            confidence = result['confidence']

            if decision:
                matched_count += 1
                dest_dir = matched_dir
            else:
                rejected_count += 1
                dest_dir = rejected_dir

            # Copy with confidence prefix
            output_filename = copy_with_confidence_prefix(eml_path, dest_dir, confidence)

            if not output_filename:
                failed_count += 1
                output_filename = f"failed_{filename}"

        # Log result
        csv_logger.log(
            filename=filename,
            processed_at=datetime.now().isoformat(),
            llm_decision=str(result['decision']).lower() if result['success'] else 'error',
            confidence=result['confidence'],
            reasoning=result['reasoning'][:200] if result['reasoning'] else '',  # Truncate long reasoning
            prompt_tokens=result['input_tokens'],
            completion_tokens=result['output_tokens'],
            total_tokens=result['input_tokens'] + result['output_tokens'],
            processing_time_ms=processing_time_ms,
            error_message=result['error'] if result['error'] else '',
            retried='false',  # We retry once automatically in analyze_email_with_llm
            from_address=email_data['from'][:100],
            subject=email_data['subject'][:100],
            output_filename=output_filename if output_filename else ''
        )

        # Update progress
        progress.update(processed_count, matched_count, rejected_count, failed_count)

    # Finish progress
    progress.finish()

    # Calculate elapsed time
    elapsed = time.time() - start_time

    # Print summary
    print("=" * 80)
    print("FILTERING COMPLETE")
    print("=" * 80)
    print(f"Total processed:   {processed_count}")
    print(f"✓ Matched:         {matched_count} ({matched_count/processed_count*100:.1f}%) → {matched_dir}")
    print(f"✗ Rejected:        {rejected_count} ({rejected_count/processed_count*100:.1f}%) → {rejected_dir}")
    print(f"⚠ Failed:          {failed_count} ({failed_count/processed_count*100:.1f}%) → {failed_dir}")
    print()
    print("Token usage:")
    print(f"  Input tokens:    {total_input_tokens:,}")
    print(f"  Output tokens:   {total_output_tokens:,}")
    print(f"  Total tokens:    {total_input_tokens + total_output_tokens:,}")
    print()
    print(f"Cost:              ${total_cost_usd:.4f} USD")
    print(f"Time elapsed:      {elapsed:.1f} seconds")
    print(f"Average speed:     {processed_count/elapsed:.1f} emails/s")
    print()
    print(f"Log file:          {log_file}")

    # Generate JSON report
    report_path = os.path.join(output_dir, 'filter_report.json')
    try:
        report = {
            'summary': {
                'total_processed': processed_count,
                'matched': matched_count,
                'rejected': rejected_count,
                'failed': failed_count,
                'total_tokens': total_input_tokens + total_output_tokens,
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_cost_usd': round(total_cost_usd, 4),
                'processing_time_seconds': round(elapsed, 2),
                'average_speed_emails_per_sec': round(processed_count / elapsed, 2)
            },
            'configuration': {
                'input_dir': input_dir,
                'system_prompt': system_prompt_path,
                'user_prompt': user_prompt_path,
                'output_dir': output_dir,
                'model': deployment_name,
                'timestamp': datetime.now().isoformat()
            }
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"JSON report:       {report_path}")

    except Exception as e:
        print(f"[WARN] Failed to generate JSON report: {e}")

    print("=" * 80)
    print()

    return {
        'processed': processed_count,
        'matched': matched_count,
        'rejected': rejected_count,
        'failed': failed_count,
        'tokens': total_input_tokens + total_output_tokens,
        'cost': total_cost_usd,
        'elapsed': elapsed
    }

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Filter vacation emails using Azure OpenAI LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python llm_vacation_filter.py \\
    --input-dir ./vacation_emails \\
    --system-prompt ./prompts/system.txt \\
    --user-prompt ./prompts/user.txt \\
    --output-dir ./filtered_results \\
    --log-file ./filter_log.csv

  # Process limited number of emails for testing
  python llm_vacation_filter.py \\
    --input-dir ./vacation_emails \\
    --system-prompt ./prompts/system.txt \\
    --user-prompt ./prompts/user.txt \\
    --output-dir ./test_results \\
    --email-limit 10

  # Debug mode - show extracted reply text before sending to LLM
  python llm_vacation_filter.py \\
    --input-dir ./vacation_emails \\
    --system-prompt ./prompts/system.txt \\
    --user-prompt ./prompts/user.txt \\
    --output-dir ./test_results \\
    --log-file ./test_log.csv \\
    --email-limit 5 \\
    --debug

Configuration:
  Create .env file in current directory with:
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
    AZURE_OPENAI_API_KEY=your-api-key
    AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
    AZURE_OPENAI_API_VERSION=2024-02-15-preview
    AZURE_OPENAI_PRICE_INPUT=0.15
    AZURE_OPENAI_PRICE_OUTPUT=0.60
        """
    )

    # Required arguments
    parser.add_argument(
        '--input-dir',
        required=True,
        help='Input directory with EML files'
    )

    parser.add_argument(
        '--system-prompt',
        required=True,
        help='Path to system prompt file'
    )

    parser.add_argument(
        '--user-prompt',
        required=True,
        help='Path to user prompt file'
    )

    parser.add_argument(
        '--output-dir',
        required=True,
        help='Output directory for filtered results'
    )

    parser.add_argument(
        '--log-file',
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
        '--debug',
        action='store_true',
        help='Show debug output including extracted reply text before sending to LLM'
    )

    args = parser.parse_args()

    # Print header
    print("\n" + "=" * 80)
    print("LLM-BASED VACATION EMAIL FILTER v1.2")
    print("=" * 80)

    # Validate input directory
    if not os.path.exists(args.input_dir):
        print(f"[ERROR] Input directory not found: {args.input_dir}")
        sys.exit(1)

    if not os.path.isdir(args.input_dir):
        print(f"[ERROR] Not a directory: {args.input_dir}")
        sys.exit(1)

    # Validate prompt files
    if not os.path.exists(args.system_prompt):
        print(f"[ERROR] System prompt file not found: {args.system_prompt}")
        print(f"[ERROR] Script cannot continue without system prompt.")
        sys.exit(1)

    if not os.path.isfile(args.system_prompt):
        print(f"[ERROR] Not a file: {args.system_prompt}")
        sys.exit(1)

    if not os.path.exists(args.user_prompt):
        print(f"[ERROR] User prompt file not found: {args.user_prompt}")
        print(f"[ERROR] Script cannot continue without user prompt.")
        sys.exit(1)

    if not os.path.isfile(args.user_prompt):
        print(f"[ERROR] Not a file: {args.user_prompt}")
        sys.exit(1)

    # Initialize Azure OpenAI
    print(f"\n[*] Loading configuration from .env...")

    global openai_client, deployment_name, price_input, price_output
    openai_client, deployment_name, price_input, price_output = initialize_azure_openai()

    if not openai_client:
        print(f"[ERROR] Failed to initialize Azure OpenAI. Check .env configuration.")
        sys.exit(1)

    # Run processing
    stats = process_emails(
        input_dir=args.input_dir,
        system_prompt_path=args.system_prompt,
        user_prompt_path=args.user_prompt,
        output_dir=args.output_dir,
        log_file=args.log_file,
        email_limit=args.email_limit,
        debug=args.debug
    )

    if stats is None:
        sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    main()
