#!/usr/bin/env python3
"""Generate SHA256 checksums for release artifacts.

Usage:
    python scripts/generate_checksums.py build/onefile/

Produces a checksums.txt file listing SHA256 hashes for all artifacts
in the given directory.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def generate_checksums(directory: Path) -> Path:
    """Generate checksums.txt for all files in a directory.

    Args:
        directory: Directory containing release artifacts.

    Returns:
        Path to the generated checksums.txt file.
    """
    output_file = directory / "checksums.txt"

    artifacts = sorted(
        f for f in directory.iterdir()
        if f.is_file() and f.name != "checksums.txt"
    )

    if not artifacts:
        print(f"No artifacts found in {directory}", file=sys.stderr)
        sys.exit(1)

    lines: list[str] = []
    for artifact in artifacts:
        hash_value = compute_sha256(artifact)
        lines.append(f"{hash_value}  {artifact.name}")
        print(f"  {artifact.name}: {hash_value}")

    output_file.write_text("\n".join(lines) + "\n")
    print(f"\nChecksums written to: {output_file}")
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SHA256 checksums for release artifacts")
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing release artifacts",
    )
    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Directory not found: {args.directory}", file=sys.stderr)
        return 1

    generate_checksums(args.directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
