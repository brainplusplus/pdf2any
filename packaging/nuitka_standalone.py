"""Nuitka build configuration for standalone mode.

Standalone mode produces a folder containing the executable and all
its dependencies. This is useful for testing and for deployments
where a folder is acceptable.

Build command (standalone):
    python -m nuitka \\
        --mode=standalone \\
        --output-dir=build/standalone \\
        --output-filename=pdf2any \\
        --include-package=pdf2any \\
        --enable-plugin=anti-bloat \\
        --follow-import-to=pdf2any \\
        pdf2any/__main__.py

Note: The resulting folder (pdf2any.dist/) must be distributed as a
whole. For a single-file executable, use onefile mode instead.
"""

from __future__ import annotations

# Nuitka command template for standalone build
STANDALONE_COMMAND = [
    "python", "-m", "nuitka",
    "--mode=standalone",
    "--output-dir=build/standalone",
    "--output-filename=pdf2any",
    "--include-package=pdf2any",
    "--enable-plugin=anti-bloat",
    "--follow-import-to=pdf2any",
    "--no-pyi-file",
    "pdf2any/__main__.py",
]

# Plugin recommendations
RECOMMENDED_PLUGINS = [
    "--enable-plugin=anti-bloat",  # Removes unnecessary bloat from dependencies
]

# Packages to explicitly include (Nuitka may miss dynamic imports)
INCLUDE_PACKAGES = [
    "--include-package=pdf2any",
    "--include-package=pypdfium2",
    "--include-package=pypdf",
]

# Optional packages (include only if installed)
OPTIONAL_PACKAGES = [
    "pdfplumber",  # for table extraction
    "pdf2docx",    # for DOCX output
]
