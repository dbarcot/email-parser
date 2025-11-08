#!/usr/bin/env python3
"""
EML to MBOX Converter
=====================
Converts individual .eml files to mbox format compatible with Thunderbird.

Author: Claude
Version: 1.0
"""

import mailbox
import email
import os
import sys
import argparse
import glob
from pathlib import Path
from datetime import datetime


class EMLToMboxConverter:
    """Converter for EML files to mbox format."""

    def __init__(self, verbose=False):
        """
        Initialize converter.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.processed = 0
        self.failed = 0
        self.skipped = 0

    def log(self, message, level="INFO"):
        """
        Log message if verbose is enabled.

        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        if self.verbose or level in ["WARNING", "ERROR"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def read_eml_file(self, eml_path):
        """
        Read and parse EML file.

        Args:
            eml_path: Path to .eml file

        Returns:
            email.message.Message object or None on failure
        """
        try:
            with open(eml_path, 'rb') as f:
                msg = email.message_from_binary_file(f)
            return msg

        except Exception as e:
            self.log(f"Failed to read {eml_path}: {e}", "ERROR")
            return None

    def add_to_mbox(self, mbox, msg, source_file):
        """
        Add email message to mbox.

        Args:
            mbox: mailbox.mbox object
            msg: email.message.Message object
            source_file: Source file path (for logging)

        Returns:
            Success boolean
        """
        try:
            # Add message to mbox
            mbox.add(msg)
            self.processed += 1
            self.log(f"Added: {os.path.basename(source_file)}")
            return True

        except Exception as e:
            self.log(f"Failed to add {source_file} to mbox: {e}", "ERROR")
            self.failed += 1
            return False

    def convert(self, input_pattern, output_path):
        """
        Convert EML files matching pattern to mbox.

        Args:
            input_pattern: Glob pattern for input .eml files
            output_path: Output .mbox file path

        Returns:
            Statistics dict
        """
        start_time = datetime.now()

        # Expand glob pattern
        self.log(f"Searching for files matching: {input_pattern}")
        eml_files = sorted(glob.glob(input_pattern, recursive=True))

        if not eml_files:
            self.log(f"No .eml files found matching pattern: {input_pattern}", "WARNING")
            return {
                'processed': 0,
                'failed': 0,
                'skipped': 0,
                'elapsed': 0
            }

        self.log(f"Found {len(eml_files)} .eml file(s)")

        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            self.log(f"Output directory: {output_dir}")

        # Create/open mbox file
        self.log(f"Creating mbox: {output_path}")

        try:
            mbox = mailbox.mbox(output_path)
            mbox.lock()

        except Exception as e:
            self.log(f"Failed to create mbox file: {e}", "ERROR")
            return None

        # Process each EML file
        self.log(f"\nProcessing {len(eml_files)} files...\n")

        for i, eml_file in enumerate(eml_files, 1):
            if self.verbose:
                print(f"\r[{i}/{len(eml_files)}] Processing...", end='', flush=True)
            elif i % 10 == 0:
                print(f"\rProcessed: {i}/{len(eml_files)}", end='', flush=True)

            # Check file extension
            if not eml_file.lower().endswith('.eml'):
                self.log(f"Skipping non-EML file: {eml_file}", "WARNING")
                self.skipped += 1
                continue

            # Read EML file
            msg = self.read_eml_file(eml_file)
            if msg is None:
                self.failed += 1
                continue

            # Add to mbox
            self.add_to_mbox(mbox, msg, eml_file)

        # Finalize
        print()  # New line after progress
        mbox.unlock()
        mbox.close()

        elapsed = (datetime.now() - start_time).total_seconds()

        self.log(f"\nConversion complete!")
        self.log(f"Output file: {output_path}")

        return {
            'processed': self.processed,
            'failed': self.failed,
            'skipped': self.skipped,
            'elapsed': elapsed
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert EML files to mbox format (Thunderbird-compatible)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all .eml files in directory
  python eml_to_mbox.py --input ./emails/*.eml --output archive.mbox

  # Convert with verbose output
  python eml_to_mbox.py --input ./emails/*.eml --output ./output/archive.mbox --verbose

  # Recursive search
  python eml_to_mbox.py --input ./emails/**/*.eml --output archive.mbox

  # Convert specific files
  python eml_to_mbox.py --input ./email1.eml --output single.mbox
        """
    )

    # Required arguments
    parser.add_argument(
        '--input',
        required=True,
        help='Input EML file(s) - supports glob patterns (e.g., ./emails/*.eml)'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output mbox file path (e.g., ./output/archive.mbox)'
    )

    # Optional arguments
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Validate output file extension
    if not args.output.lower().endswith('.mbox'):
        print("[WARNING] Output file should have .mbox extension")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Run conversion
    print("\n" + "="*60)
    print("EML TO MBOX CONVERTER v1.0")
    print("="*60 + "\n")

    converter = EMLToMboxConverter(verbose=args.verbose)
    stats = converter.convert(args.input, args.output)

    if stats is None:
        sys.exit(1)

    # Print summary
    print("\n" + "="*60)
    print("CONVERSION SUMMARY")
    print("="*60)
    print(f"Total processed: {stats['processed']}")
    print(f"Failed:          {stats['failed']}")
    print(f"Skipped:         {stats['skipped']}")
    print(f"Time elapsed:    {stats['elapsed']:.2f} seconds")
    print("="*60 + "\n")

    if stats['failed'] > 0:
        print("[WARNING] Some files failed to convert. Check errors above.")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
