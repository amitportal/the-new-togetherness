#!/usr/bin/env python3
"""
correct_line_changes.py

Collates lines in text documents:
- Removes single line breaks inside paragraphs
- Preserves paragraph breaks (double line breaks)

Usage:
    python correct_line_changes.py --text "your raw text here"
    python correct_line_changes.py --file input.txt
    python correct_line_changes.py --file input.md --output output.txt
"""

import argparse
import sys
from pathlib import Path


def collate_lines(input_text: str) -> str:
    """
    Collates lines in a text document:
    - Removes single line breaks inside paragraphs
    - Preserves paragraph breaks (double line breaks)
    """
    # Split into paragraphs by double newlines
    paragraphs = input_text.strip().split("\n\n")

    # For each paragraph, join lines with spaces
    cleaned_paragraphs = [" ".join(p.splitlines()) for p in paragraphs]

    # Rejoin paragraphs with double newlines
    return "\n\n".join(cleaned_paragraphs)


def process_file(file_path: Path) -> str:
    """
    Reads a file and returns cleaned text.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        raw_text = f.read()
    return collate_lines(raw_text)


def main():
    parser = argparse.ArgumentParser(
        description="Correct line changes in text or files, preserving paragraphs."
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Direct text input to process."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a .txt or .md file to process."
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional output file path. If not provided, prints to stdout."
    )

    args = parser.parse_args()

    if args.text:
        cleaned = collate_lines(args.text)
    elif args.file:
        cleaned = process_file(Path(args.file))
    else:
        parser.error("You must provide either --text or --file.")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(cleaned)
    else:
        sys.stdout.write(cleaned + "\n")


if __name__ == "__main__":
    main()
    