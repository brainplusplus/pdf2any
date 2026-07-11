#!/usr/bin/env python3
"""Build script for Nuitka standalone mode.

Usage:
    python scripts/build_standalone.py
    python scripts/build_standalone.py --target linux-amd64

Produces a build/standalone/ directory with the executable and
its dependencies in a .dist folder.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packaging.artifact_naming import get_artifact_name, list_targets


def build_standalone(target: str | None = None) -> int:
    """Build a standalone executable using Nuitka.

    Args:
        target: Optional target platform (e.g. 'linux-amd64').
                If None, builds for the current platform.

    Returns:
        Exit code from Nuitka (0 = success).
    """
    entry_point = str(PROJECT_ROOT / "pdf2any" / "__main__.py")
    output_dir = PROJECT_ROOT / "build" / "standalone"

    # Determine output filename
    if target:
        try:
            output_name = get_artifact_name(target)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        # Use platform default
        output_name = "pdf2any"

    cmd = [
        sys.executable, "-m", "nuitka",
        "--mode=standalone",
        f"--output-dir={output_dir}",
        f"--output-filename={output_name}",
        "--include-package=pdf2any",
        "--enable-plugin=anti-bloat",
        "--follow-import-to=pdf2any",
        "--no-pyi-file",
        entry_point,
    ]

    print(f"Building standalone executable: {output_name}")
    print(f"Command: {' '.join(cmd)}")
    print()

    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build pdf2any standalone executable")
    parser.add_argument(
        "--target",
        choices=list_targets() + [None],
        default=None,
        help="Target platform (default: current platform)",
    )
    args = parser.parse_args()
    return build_standalone(args.target)


if __name__ == "__main__":
    sys.exit(main())
