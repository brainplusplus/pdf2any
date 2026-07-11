#!/usr/bin/env python3
"""Build script for Nuitka onefile mode.

Usage:
    python scripts/build_onefile.py
    python scripts/build_onefile.py --target linux-amd64

Produces a single self-contained executable in build/onefile/.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packaging.artifact_naming import get_artifact_name, list_targets


def build_onefile(target: str | None = None) -> int:
    """Build a onefile executable using Nuitka.

    Args:
        target: Optional target platform (e.g. 'linux-amd64').
                If None, builds for the current platform.

    Returns:
        Exit code from Nuitka (0 = success).
    """
    entry_point = str(PROJECT_ROOT / "pdf2any" / "__main__.py")
    output_dir = PROJECT_ROOT / "build" / "onefile"

    if target:
        try:
            output_name = get_artifact_name(target)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        output_name = "pdf2any"

    cmd = [
        sys.executable, "-m", "nuitka",
        "--mode=onefile",
        f"--output-dir={output_dir}",
        f"--output-filename={output_name}",
        "--include-package=pdf2any",
        "--enable-plugin=anti-bloat",
        "--onefile-tempdir-spec={CACHE_DIR}/pdf2any",
        "--follow-import-to=pdf2any",
        "--no-pyi-file",
        entry_point,
    ]

    print(f"Building onefile executable: {output_name}")
    print(f"Command: {' '.join(cmd)}")
    print()

    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build pdf2any onefile executable")
    parser.add_argument(
        "--target",
        choices=list_targets() + [None],
        default=None,
        help="Target platform (default: current platform)",
    )
    args = parser.parse_args()
    return build_onefile(args.target)


if __name__ == "__main__":
    sys.exit(main())
