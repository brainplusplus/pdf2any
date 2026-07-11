# pdf2any

> **Pandoc for PDF semantics** — A CLI-first, developer-friendly, automation-ready converter that turns PDF into structured, useful output formats.

[![Release](https://github.com/brainplusplus/pdf2any/actions/workflows/release.yml/badge.svg)](https://github.com/brainplusplus/pdf2any/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Table of Contents

1. [What pdf2any Is](#1-what-pdf2any-is)
2. [What pdf2any Is NOT](#2-what-pdf2any-is-not)
3. [Positioning Statement](#3-positioning-statement)
4. [Installation](#4-installation)
5. [CLI Examples](#5-cli-examples)
6. [Architecture Overview](#6-architecture-overview)
7. [Supported Formats](#7-supported-formats)
8. [Capability Matrix](#8-capability-matrix)
9. [Limitations](#9-limitations)
10. [Build and Release Instructions](#10-build-and-release-instructions)
11. [Multi-OS / Multi-Arch Strategy](#11-multi-os--multi-arch-strategy)
12. [Node.js and Go Integration](#12-nodejs-and-go-integration)
13. [ProseMirror Output](#prosemirror-output)
14. [OCR](#ocr)
15. [Roadmap](#roadmap)

---

## 1. What pdf2any Is

`pdf2any` is a **CLI-first semantic PDF converter**. It reads PDF files and produces structured output formats — Markdown, HTML, ProseMirror JSON, DOCX, JSON, TXT, and page images — using a modular converter framework with an internal Intermediate Representation (IR).

**Key characteristics:**
- **CLI-first**: Designed for the terminal, shell scripts, and CI/CD pipelines.
- **Developer-friendly**: Type-hinted Python, clean module boundaries, comprehensive tests.
- **Automation-ready**: Machine-readable `--json` output, stable exit codes, no interactive prompts.
- **Extensible**: Plugin-style renderer registry; adding a new output format is one file.
- **Honest**: Does not claim perfect conversion. Explicitly documents that PDF is presentation-oriented and semantic recovery is heuristic.

## 2. What pdf2any Is NOT

- ❌ **Not a PDF editor** — cannot modify or annotate PDFs.
- ❌ **Not a PDF viewer** — cannot render or display PDFs interactively.
- ❌ **Not an Adobe clone** — does not aim for feature parity with Acrobat.
- ❌ **Not a general-purpose 1000-format conversion hub** — focused on PDF input only.
- ❌ **Not a web-first PDF toolbox** — no web UI, no REST API (by default).

## 3. Positioning Statement

> Think: **"Pandoc for PDF semantics"**
>
> Not: "Adobe replacement"
> Not: "self-hosted PDF toolbox"
> Not: "1000-format universal converter"

`pdf2any` focuses on turning PDF into structured and useful output formats. It prioritizes **semantic usefulness over pixel-perfect mimicry**. The internal IR captures document structure (headings, paragraphs, lists, tables, images) and all text/structured outputs render from that IR.

---

## 4. Installation

### Option A: One-line installer (recommended — no Python needed)

**Linux / macOS:**
```bash
curl -sL https://github.com/brainplusplus/pdf2any/releases/latest/download/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://github.com/brainplusplus/pdf2any/releases/latest/download/install.ps1 | iex
```

The installer auto-detects your OS and architecture, downloads the latest binary from GitHub Releases, installs it to your PATH, and verifies the installation.

### Option B: Download a standalone binary

Pre-built binaries are available on the [GitHub Releases](https://github.com/brainplusplus/pdf2any/releases) page for:

| Platform | Artifact |
|----------|----------|
| Linux x86_64 | `pdf2any-linux-amd64` |
| Linux ARM64 | `pdf2any-linux-arm64` |
| Windows x86_64 | `pdf2any-windows-amd64.exe` |
| macOS Intel | `pdf2any-macos-amd64` |
| macOS Apple Silicon | `pdf2any-macos-arm64` |

Download, extract, and run — no Python installation required.

**Unix:** `chmod +x pdf2any-* && ./pdf2any-linux-amd64 --version`
**Windows:** `pdf2any-windows-amd64.exe --version`

### Option C: pip install (Python package)

```bash
# Core (text extraction + rendering only)
pip install pdf2any

# With table extraction (pdfplumber)
pip install pdf2any[tables]

# With DOCX output (pdf2docx)
pip install pdf2any[docx]

# With OCR — Tesseract (requires system Tesseract binary)
pip install pdf2any[ocr-tesseract]

# With OCR — EasyOCR (Python-native, GPU optional)
pip install pdf2any[ocr-easyocr]

# With OCR — LLM vision (OpenAI, Anthropic, Gemini)
pip install pdf2any[ocr-llm]

# With all OCR engines
pip install pdf2any[ocr-all]

# Everything (tables + docx + all OCR)
pip install pdf2any[all]

# Development
pip install pdf2any[dev]
```

> **Note:** The standalone binary (Option A/B) already bundles tables, DOCX, Tesseract wrapper, and LLM OCR. EasyOCR is excluded from the binary (adds ~2 GB via PyTorch) — install it separately with `pip install pdf2any[ocr-easyocr]` if needed.

### Option D: Docker

```bash
# Pull and run
docker run --rm -v $(pwd):/work ghcr.io/brainplusplus/pdf2any input.pdf -t markdown -o /work/out.md
```

---

## 5. CLI Examples

The command style intentionally resembles Pandoc:

```bash
# Basic conversions
pdf2any input.pdf -t markdown -o out.md
pdf2any input.pdf -t html -o out.html
pdf2any input.pdf -t html -o out.html --standalone      # full HTML document
pdf2any input.pdf -t prosemirror -o out.json
pdf2any input.pdf -t docx -o out.docx
pdf2any input.pdf -t json -o out.ir.json                 # raw IR export
pdf2any input.pdf -t txt -o out.txt

# Page images
pdf2any input.pdf -t png --pages 1-3 -o page-%d.png
pdf2any input.pdf -t jpg --pages 1-3 -o page-%d.jpg

# Output to stdout (text formats only)
pdf2any input.pdf -t markdown
cat input.pdf | pdf2any -t markdown > out.md

# Page selection
pdf2any input.pdf -t markdown --pages 1,3,5 -o out.md
pdf2any input.pdf -t markdown --pages 2-5 -o out.md
pdf2any input.pdf -t markdown --start 1 --end 3 -o out.md

# Pretty-printing
pdf2any input.pdf -t prosemirror -o out.json --pretty
pdf2any input.pdf -t html -o out.html --standalone --pretty

# Machine-readable metadata
pdf2any input.pdf -t markdown -o out.md --json

# Information
pdf2any --list-output-formats
pdf2any --list-input-formats
pdf2any --version
pdf2any --help

# Debug mode
pdf2any input.pdf -t markdown -o out.md --debug
```

### CLI Flags

| Flag | Description |
|------|-------------|
| `input` (positional) | Input PDF path. If omitted, reads from stdin. |
| `-f, --from` | Input format (default: `pdf`). |
| `-t, --to` | Output format (required). |
| `-o, --output` | Output file. If omitted, text output goes to stdout. |
| `--pages` | Page range, e.g. `1-3,5,7-9`. |
| `--start` | Start page (1-indexed). |
| `--end` | End page (1-indexed). |
| `--ocr` | Enable OCR (hybrid mode — OCR only for scanned pages). See [OCR](#ocr). |
| `--ocr-force` | Force OCR on all pages (implies `--ocr`). |
| `--ocr-engine` | OCR engine: `auto`, `tesseract`, `easyocr`, `llm` (default: `auto`). |
| `--ocr-provider` | LLM provider: `openai`, `anthropic`, `gemini` (default: `openai`). |
| `--ocr-model` | Model name for LLM OCR (e.g. `gpt-4o`, `claude-sonnet-4-20250514`). |
| `--ocr-lang` | OCR language code (default: `eng`). |
| `--ocr-base-url` | Custom API URL for OpenAI-compatible endpoints. |
| `--ocr-dpi` | Render DPI for OCR (default: 300). |
| `--extract-images` | Extract embedded images. |
| `--standalone` | Full HTML document (with `<html>` wrapper). |
| `--pretty` | Pretty-print output. |
| `--json` | Emit machine-readable metadata JSON. |
| `--debug` | Verbose logging to stderr. |
| `--list-input-formats` | List supported input formats. |
| `--list-output-formats` | List supported output formats. |
| `--version` | Print version. |
| `--help` | Print help. |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Conversion error (parse, extraction, render) |
| 2 | Usage error (bad arguments) |
| 3 | Capability error (feature not installed) |

### `--json` Output

**Success:**
```json
{
  "ok": true,
  "input": "report.pdf",
  "output_format": "markdown",
  "output_path": "out.md",
  "pages_processed": 12,
  "duration_ms": 3420,
  "ir_version": "1.0",
  "pdf2any_version": "0.1.0",
  "warnings": [],
  "error": null
}
```

**Error:**
```json
{
  "ok": false,
  "input": "report.pdf",
  "output_format": "prosemirror",
  "output_path": null,
  "pages_processed": 0,
  "duration_ms": 15,
  "ir_version": "1.0",
  "pdf2any_version": "0.1.0",
  "warnings": [],
  "error": {
    "code": "PARSE_ERROR",
    "message": "Failed to open PDF: file is encrypted",
    "type": "PDFParseError"
  }
}
```

---

## 6. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                         CLI (cli.py)                       │
│  argparse → registry lookup → pipeline orchestration     │
└──────────────┬───────────────────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │    PDFParser         │  pypdfium2 + pypdf
    │  (reading + text)    │  (+ pdfplumber for tables)
    └──────────┬──────────┘
               │ raw pages + spans
    ┌──────────▼──────────┐
    │ SemanticNormalizer   │  heading detection, list detection,
    │  (heuristic recovery)│  table normalization
    └──────────┬──────────┘
               │ IRDocument (dataclasses)
    ┌──────────▼──────────┐
    │   IR (ir.py)        │  Document → Page → Block nodes
    │  (intermediate rep)  │  → Inline nodes (Text + Marks)
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  FormatRegistry     │  routes -t <format> to renderer
    └────┬──────┬────┬────┘
         │      │    │
    ┌────▼─┐ ┌──▼─┐ ┌▼──────┐ ┌────────┐ ┌────────┐
    │  MD  │ │HTML│ │ProseM │ │  JSON  │ │  TXT   │
    └──────┘ └────┘ └───────┘ └────────┘ └────────┘
         │
    ┌────▼──────────────┐ ┌──────────────┐
    │  DOCX (pdf2docx)  │ │ Image (PNG)  │
    │  (isolated backend)│ │ (pypdfium2)  │
    └───────────────────┘ └──────────────┘
```

### Pipeline Stages

1. **PDF reading** — `pypdfium2` opens the PDF, renders pages, extracts text with position info.
2. **Text extraction** — Character-level spans with bounding boxes and font info.
3. **Layout extraction** — Spans grouped into lines, lines into blocks by vertical proximity.
4. **Semantic normalization** — Heuristic heading detection (font size + bold), list detection, table extraction.
5. **IR construction** — Build `IRDocument` with typed node dataclasses.
6. **Rendering** — Format-specific renderers convert IR to output (Markdown, HTML, ProseMirror, etc.).

### Internal IR

The IR captures document structure with these node types:

| Block Nodes | Inline Nodes | Marks |
|-------------|-------------|-------|
| `Heading` | `Text` | `Emphasis` |
| `Paragraph` | | `Strong` |
| `BulletList` / `OrderedList` | | `Code` |
| `ListItem` | | `Link` |
| `Blockquote` | | |
| `Table` / `TableRow` / `TableCell` | | |
| `Image` | | |
| `CodeBlock` | | |
| `PageBreak` / `LineBreak` | | |

All text/structured outputs render from this IR. The IR is versioned (`ir_version: "1.0"`) and serializable via `to_dict()` / `from_dict()`.

---

## 7. Supported Formats

### Input Formats

| Format | Status |
|--------|--------|
| `pdf` | ✅ Supported |

### Output Formats

| Format | Flag | Binary | Description |
|--------|------|--------|-------------|
| Markdown | `-t markdown` | No | Semantic Markdown |
| HTML | `-t html` | No | HTML fragment (`--standalone` for full doc) |
| ProseMirror | `-t prosemirror` | No | ProseMirror JSON (`{"type":"doc","content":[...]}`) |
| JSON | `-t json` | No | Raw IR JSON export |
| TXT | `-t txt` | No | Plain text |
| DOCX | `-t docx` | Yes | Via pdf2docx (isolated backend) |
| PNG | `-t png` | Yes | Page images (pypdfium2 rendering) |
| JPG | `-t jpg` | Yes | Page images (pypdfium2 rendering) |

---

## 8. Capability Matrix

| Format | Headings | Paragraphs | Lists | Tables | Images | Inline marks | Links | Page breaks |
|--------|:--------:|:----------:|:-----:|:------:|:------:|:------------:|:-----:|:-----------:|
| markdown | ✅ | ✅ | ✅ | ✅ | ✅ ref | ✅ | ✅ | ✅ `---` |
| html | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `<hr>` |
| prosemirror | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `hr` |
| json | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| txt | ✅ | ✅ | ✅ | ⚠️ plain | ❌ | ❌ | ❌ | ✅ `\f` |
| docx | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| png/jpg | — | — | — | — | — (page render) | — | — | — |

**Legend:** ✅ = fully supported, ⚠️ = degraded/simplified, ❌ = not supported, ref = reference only

---

## 9. Limitations

> **PDF is presentation-oriented. Semantic recovery is heuristic, not perfect.**

1. **Scanned PDFs** — Use `--ocr` (hybrid mode: OCR only for scanned pages) or `--ocr-force` (OCR all pages). Supports Tesseract, EasyOCR, and LLM vision (GPT-4o, Claude, Gemini). See [OCR](#ocr) below.

2. **Multi-column layouts** — Text may interleave between columns. The layout extractor uses vertical proximity grouping, which works for single-column documents but may misorder multi-column text.

3. **Tables** — Complex merged cells, nested tables, and borderless tables may be missed or malformed. Table extraction uses pdfplumber (optional) and is best-effort.

4. **Complex typography** — Font-based heading detection is heuristic. Unusual fonts or inconsistent sizing may cause headings to be misclassified as paragraphs or vice versa.

5. **Nested visual structures** — Text boxes, annotations, form fields, and embedded diagrams are not fully captured as semantic structures.

6. **Images** — Extracted as references (e.g., Markdown `![](path)`, HTML `<img>`). Use `--ocr` to extract text from scanned pages or images via Tesseract, EasyOCR, or LLM vision. See [OCR](#ocr).

7. **ProseMirror tables** — Full `prosemirror-tables` schema supported (`table > table_row > table_header | table_cell > paragraph > text`). Requires the `prosemirror-tables` plugin in your editor to render.

---

## 10. Build and Release Instructions

### Building from Source

```bash
# Clone the repository
git clone https://github.com/brainplusplus/pdf2any.git
cd pdf2any

# Install with dev dependencies
pip install -e ".[dev,tables,docx]"

# Run tests
pytest tests/ -v

# Run linting
ruff check pdf2any/
mypy pdf2any/
```

### Nuitka Builds

#### Standalone mode (folder with executable + deps)

```bash
python scripts/build_standalone.py
# Output: build/standalone/pdf2any.dist/
```

#### Onefile mode (single executable)

```bash
python scripts/build_onefile.py
# Output: build/onefile/pdf2any
```

#### Building for a specific target

```bash
python scripts/build_onefile.py --target linux-amd64
python scripts/build_onefile.py --target windows-amd64
```

#### Raw Nuitka commands

```bash
# Standalone
python -m nuitka \
    --mode=standalone \
    --output-dir=build/standalone \
    --output-filename=pdf2any \
    --include-package=pdf2any \
    --enable-plugin=anti-bloat \
    --follow-import-to=pdf2any \
    --no-pyi-file \
    pdf2any/__main__.py

# Onefile
python -m nuitka \
    --mode=onefile \
    --output-dir=build/onefile \
    --output-filename=pdf2any \
    --include-package=pdf2any \
    --enable-plugin=anti-bloat \
    --onefile-tempdir-spec="{CACHE_DIR}/pdf2any" \
    --follow-import-to=pdf2any \
    --no-pyi-file \
    pdf2any/__main__.py
```

### Generating Checksums

```bash
python scripts/generate_checksums.py build/onefile/
# Output: build/onefile/checksums.txt
```

### Release Process

1. Tag a release: `git tag v0.1.0 && git push origin v0.1.0`
2. GitHub Actions `release.yml` triggers automatically:
   - Builds binaries for all 5 targets (linux/macOS × amd64/arm64, windows-amd64)
   - Generates SHA256 checksums
   - Creates a draft GitHub Release with all artifacts
3. Review and publish the release.

---

## 11. Multi-OS / Multi-Arch Strategy

### Binary Artifacts

Binaries are built **per OS/architecture** — there is no universal binary. Each target runs only on its native platform.

| Target | Artifact Name | Runs On |
|--------|--------------|--------|
| linux-amd64 | `pdf2any-linux-amd64` | Linux x86_64 |
| linux-arm64 | `pdf2any-linux-arm64` | Linux ARM64 |
| windows-amd64 | `pdf2any-windows-amd64.exe` | Windows x86_64 |
| macos-amd64 | `pdf2any-macos-amd64` | macOS Intel |
| macos-arm64 | `pdf2any-macos-arm64` | macOS Apple Silicon |

### Platform-Specific Notes

- **Windows**: Artifacts have `.exe` extension. No special permissions needed.
- **Unix (Linux/macOS)**: Artifacts need `chmod +x` after download.
- **macOS**: May need `xattr -d com.apple.quarantine pdf2any-macos-*` to bypass Gatekeeper.

### Docker Multi-Arch

Docker images support `linux/amd64` and `linux/arm64` via Docker Buildx + QEMU:

```bash
# Build multi-arch image
docker buildx build --platform linux/amd64,linux/arm64 -t pdf2any . --push

# Pull and run
docker run --rm -v $(pwd):/work pdf2any input.pdf -t markdown
```

> **Note:** Multi-arch Docker images use QEMU emulation for non-native architectures. This is different from native standalone binaries, which run without emulation and are faster. For production performance, use the native binary for your platform.

---

## 12. Node.js and Go Integration

### Node.js (child_process.execFile)

```javascript
const { execFile } = require('child_process');
const path = require('path');

// Platform resolution
function getBinaryPath() {
  const osMap = { darwin: 'macos', linux: 'linux', win32: 'windows' };
  const archMap = { x64: 'amd64', arm64: 'arm64' };
  const os = osMap[process.platform] || process.platform;
  const arch = archMap[process.arch] || process.arch;
  const ext = process.platform === 'win32' ? '.exe' : '';
  return path.join(__dirname, 'bin', `pdf2any-${os}-${arch}${ext}`);
}

execFile(getBinaryPath(), ['input.pdf', '-t', 'markdown', '-o', 'out.md'],
  (err, stdout, stderr) => {
    if (err) {
      console.error(`Exit code ${err.code}: ${stderr}`);
      process.exit(err.code || 1);
    }
    console.log(stdout);
  }
);
```

**Platform resolution:** `process.platform` (`darwin`/`linux`/`win32`) + `process.arch` (`x64`/`arm64`)

See: [`examples/node_wrapper.js`](examples/node_wrapper.js)

### Go (exec.Command)

```go
package main

import (
    "fmt"
    "os"
    "os/exec"
    "runtime"
)

func main() {
    osMap := map[string]string{
        "linux": "linux", "darwin": "macos", "windows": "windows",
    }
    osName := osMap[runtime.GOOS]
    binaryName := fmt.Sprintf("pdf2any-%s-%s", osName, runtime.GOARCH)
    if runtime.GOOS == "windows" {
        binaryName += ".exe"
    }

    cmd := exec.Command(binaryName, "input.pdf", "-t", "markdown", "-o", "out.md")
    stdout, err := cmd.Output()
    if err != nil {
        if exitErr, ok := err.(*exec.ExitError); ok {
            fmt.Fprintf(os.Stderr, "Exit %d: %s\n", exitErr.ExitCode(), exitErr.Stderr)
            os.Exit(exitErr.ExitCode())
        }
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
    fmt.Print(string(stdout))
}
```

**Platform resolution:** `runtime.GOOS` (`linux`/`darwin`/`windows`) + `runtime.GOARCH` (`amd64`/`arm64`)

See: [`examples/go_wrapper.go`](examples/go_wrapper.go)

---

## ProseMirror Output

The ProseMirror renderer outputs valid ProseMirror-style JSON with a root `doc` node:

```json
{
  "type": "doc",
  "content": [
    { "type": "heading", "attrs": { "level": 1 }, "content": [
      { "type": "text", "text": "Document Title" }
    ]},
    { "type": "paragraph", "content": [
      { "type": "text", "text": "A paragraph with " },
      { "type": "text", "text": "bold", "marks": [{ "type": "strong" }] },
      { "type": "text", "text": " text." }
    ]},
    { "type": "bullet_list", "content": [
      { "type": "list_item", "content": [
        { "type": "paragraph", "content": [
          { "type": "text", "text": "First item" }
        ]}
      ]}
    ]},
    { "type": "table", "content": [
      { "type": "table_row", "content": [
        { "type": "table_header", "content": [
          { "type": "paragraph", "content": [
            { "type": "text", "text": "Name" }
          ]}
        ]},
        { "type": "table_header", "content": [
          { "type": "paragraph", "content": [
            { "type": "text", "text": "Value" }
          ]}
        ]}
      ]},
      { "type": "table_row", "content": [
        { "type": "table_cell", "content": [
          { "type": "paragraph", "content": [
            { "type": "text", "text": "Alpha" }
          ]}
        ]},
        { "type": "table_cell", "content": [
          { "type": "paragraph", "content": [
            { "type": "text", "text": "100" }
          ]}
        ]}
      ]}
    ]},
    { "type": "horizontal_rule" }
  ]
}
```

See: [`examples/prosemirror_sample.json`](examples/prosemirror_sample.json) for a complete sample.

**Schema notes:**
- `doc` contains block nodes
- `paragraph` contains inline content (text nodes)
- `list_item` contains block content (paragraphs)
- `table` uses prosemirror-tables schema: `table > table_row > table_header | table_cell > paragraph > text`
- Page breaks render as `horizontal_rule` nodes
- Unsupported structures degrade to paragraphs

---

## OCR

pdf2any supports OCR for scanned PDFs via three pluggable engines:

| Engine | Install | System Dep | GPU | Accuracy | Speed |
|--------|---------|-----------|-----|----------|-------|
| **Tesseract** | `pip install pdf2any[ocr-tesseract]` | Yes (Tesseract binary) | ❌ | Good | Fast |
| **EasyOCR** | `pip install pdf2any[ocr-easyocr]` | No | ✅ CUDA | Better | Medium |
| **LLM Vision** | `pip install pdf2any[ocr-llm]` | No (API key) | N/A | Best | Slow (API) |

### Two OCR Modes

```bash
# Hybrid (default) — OCR only for pages with little/no text, use text layer otherwise
pdf2any scanned.pdf -t markdown --ocr

# Force — OCR every page, ignore text layer entirely
pdf2any scanned.pdf -t markdown --ocr-force
```

Hybrid mode is smart: it checks each page's text layer and only OCRs pages that are empty or near-empty (< 10 chars). This handles mixed PDFs (some pages text-based, some scanned) transparently.

### Tesseract

```bash
# Install
pip install pdf2any[ocr-tesseract]
# Also install Tesseract system binary:
#   Ubuntu/Debian: sudo apt install tesseract-ocr
#   macOS:         brew install tesseract
#   Windows:       https://github.com/UB-Mannheim/tesseract/wiki

# Usage
pdf2any scan.pdf -t markdown --ocr --ocr-engine tesseract --ocr-lang eng
```

### EasyOCR

```bash
# Install
pip install pdf2any[ocr-easyocr]

# Usage (auto-detects CUDA)
pdf2any scan.pdf -t markdown --ocr --ocr-engine easyocr --ocr-lang eng
```

### LLM Vision OCR

Supports OpenAI, Anthropic, and Google Gemini — plus any OpenAI-compatible endpoint (OpenRouter, Groq, Ollama, vLLM).

```bash
# Install
pip install pdf2any[ocr-llm]

# OpenAI (GPT-4o)
export OPENAI_API_KEY="sk-..."
pdf2any scan.pdf -t markdown --ocr --ocr-engine llm --ocr-provider openai --ocr-model gpt-4o

# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."
pdf2any scan.pdf -t markdown --ocr --ocr-engine llm --ocr-provider anthropic --ocr-model claude-sonnet-4-20250514

# Google Gemini
export GOOGLE_API_KEY="AI..."
pdf2any scan.pdf -t markdown --ocr --ocr-engine llm --ocr-provider gemini --ocr-model gemini-2.5-flash

# Custom endpoint (OpenAI-compatible: OpenRouter, Groq, Ollama)
pdf2any scan.pdf -t markdown --ocr-force \
  --ocr-engine llm --ocr-provider openai \
  --ocr-model qwen2-vl-72b \
  --ocr-base-url https://openrouter.ai/api/v1
```

### All CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--ocr` | off | Enable OCR (hybrid mode) |
| `--ocr-force` | off | Force OCR on all pages (implies `--ocr`) |
| `--ocr-engine` | `auto` | `auto`, `tesseract`, `easyocr`, `llm` |
| `--ocr-provider` | `openai` | LLM provider: `openai`, `anthropic`, `gemini` |
| `--ocr-model` | per-provider | Model name (e.g. `gpt-4o`, `claude-sonnet-4-20250514`) |
| `--ocr-lang` | `eng` | Language code (`eng`, `fra`, `deu`, `ind`, `ch_sim`, ...) |
| `--ocr-base-url` | SDK default | Custom API URL (OpenAI-compatible) |
| `--ocr-concurrency` | `1` | Parallel API calls (LLM only) |
| `--ocr-dpi` | `300` | Render DPI for OCR (higher = more accurate) |

---

## Roadmap

| Phase | Features |
|-------|----------|
| **v0.1** | markdown, html, prosemirror, json, txt, docx, png/jpg; CLI; IR; tests; packaging; installer scripts |
| **v0.2** (current) | **OCR (Tesseract + EasyOCR + LLM vision: OpenAI/Anthropic/Gemini)**; hybrid + force modes; custom base URL for OpenAI-compatible endpoints |
| **v0.3** | Improved table detection; `epub` output format |
| **v0.4** | `latex` output format; custom AST plugin API |
| **v0.5** | User-defined renderer plugins; optional server mode |

---

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Contributions are welcome. Please:

1. Run `ruff check pdf2any/` and `pytest tests/ -v` before submitting.
2. Add tests for new renderers or features.
3. Keep the CLI contract stable — flags should not change between minor versions.
4. Document limitations honestly.
