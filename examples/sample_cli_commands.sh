#!/usr/bin/env bash
# Cookbook of pdf2any CLI invocations.
# These examples demonstrate all common usage patterns.

set -euo pipefail

echo "=== pdf2any CLI Cookbook ==="
echo ""

# --- Basic conversions ---
echo "1. PDF → Markdown"
pdf2any input.pdf -t markdown -o out.md

echo "2. PDF → HTML (fragment)"
pdf2any input.pdf -t html -o out.html

echo "3. PDF → HTML (standalone document)"
pdf2any input.pdf -t html -o out.html --standalone

echo "4. PDF → ProseMirror JSON"
pdf2any input.pdf -t prosemirror -o out.json

echo "5. PDF → raw IR JSON"
pdf2any input.pdf -t json -o out.ir.json

echo "6. PDF → plain text"
pdf2any input.pdf -t txt -o out.txt

echo "7. PDF → DOCX (requires pdf2docx)"
pdf2any input.pdf -t docx -o out.docx

echo "8. PDF → page images (PNG)"
pdf2any input.pdf -t png --pages 1-3 -o page-%d.png

echo "9. PDF → page images (JPG)"
pdf2any input.pdf -t jpg --pages 1-3 -o page-%d.jpg

# --- Output to stdout ---
echo "10. PDF → Markdown to stdout (no -o)"
pdf2any input.pdf -t markdown

echo "11. Stdin input (pipe)"
cat input.pdf | pdf2any -t markdown > out.md

# --- Page selection ---
echo "12. Specific pages"
pdf2any input.pdf -t markdown --pages 1,3,5 -o out.md

echo "13. Page range"
pdf2any input.pdf -t markdown --pages 2-5 -o out.md

echo "14. Start/end flags"
pdf2any input.pdf -t markdown --start 1 --end 3 -o out.md

# --- Formatting options ---
echo "15. Pretty-printed JSON"
pdf2any input.pdf -t prosemirror -o out.json --pretty

echo "16. Pretty-printed HTML"
pdf2any input.pdf -t html -o out.html --standalone --pretty

# --- Machine-readable output ---
echo "17. JSON metadata on success"
pdf2any input.pdf -t markdown -o out.md --json

echo "18. JSON metadata on error (file not found)"
pdf2any nonexistent.pdf -t markdown --json || true

# --- Information flags ---
echo "19. List output formats"
pdf2any --list-output-formats

echo "20. List input formats"
pdf2any --list-input-formats

echo "21. Version"
pdf2any --version

echo "22. Debug mode"
pdf2any input.pdf -t markdown -o out.md --debug

echo ""
echo "=== All examples complete ==="
