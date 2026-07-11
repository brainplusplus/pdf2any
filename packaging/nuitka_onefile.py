"""Nuitka build configuration for onefile mode.

Onefile mode produces a single self-contained executable. This is the
recommended mode for distribution — users get one file with no
dependencies.

Build command (onefile):
    python -m nuitka \\
        --mode=onefile \\
        --output-dir=build/onefile \\
        --output-filename=pdf2any \\
        --include-package=pdf2any \\
        --enable-plugin=anti-bloat \\
        --onefile-tempdir-spec="{CACHE_DIR}/pdf2any" \\
        --follow-import-to=pdf2any \\
        pdf2any/__main__.py

Note: The onefile executable extracts itself to a temp directory at
runtime. The --onefile-tempdir-spec controls where this extraction
happens (default: system temp, which may be cleaned up).
"""

from __future__ import annotations

# Nuitka command template for onefile build
ONEFILE_COMMAND = [
    "python", "-m", "nuitka",
    "--mode=onefile",
    "--output-dir=build/onefile",
    "--output-filename=pdf2any",
    "--include-package=pdf2any",
    "--enable-plugin=anti-bloat",
    "--onefile-tempdir-spec={CACHE_DIR}/pdf2any",
    "--follow-import-to=pdf2any",
    "--no-pyi-file",
    "pdf2any/__main__.py",
]

# Onefile-specific options
ONEFILE_OPTIONS = {
    "tempdir_spec": "{CACHE_DIR}/pdf2any",
    # Use {CACHE_DIR} for persistent extraction (survives reboots)
    # Alternatives:
    #   {TEMP}       — system temp (may be cleaned)
    #   {CACHE_DIR}  — user cache dir (persistent)
    #   {HOME}       — user home dir
}

# Platform-specific output filename suffixes
PLATFORM_SUFFIXES = {
    "linux": "",
    "windows": ".exe",
    "macos": "",
}
