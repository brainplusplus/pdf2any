# Dockerfile for pdf2any CLI usage.
#
# Multi-stage build:
#   1. Builder stage: install dependencies and build the executable with Nuitka
#   2. Runtime stage: minimal image with just the executable
#
# Usage:
#   docker build -t pdf2any .
#   docker run --rm -v $(pwd):/work pdf2any input.pdf -t markdown -o /work/out.md
#
# Multi-arch build (amd64 + arm64):
#   docker buildx build --platform linux/amd64,linux/arm64 -t pdf2any . --push
#
# Note: Multi-arch Docker images use QEMU emulation for non-native architectures.
# This is different from native standalone binaries, which run without emulation.

# ── Builder stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install build dependencies for Nuitka
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy project files
COPY pyproject.toml .
COPY pdf2any/ pdf2any/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[tables,docx]"
RUN pip install --no-cache-dir nuitka

# Build onefile executable
RUN python -m nuitka \
    --mode=onefile \
    --output-dir=/build \
    --output-filename=pdf2any \
    --include-package=pdf2any \
    --enable-plugin=anti-bloat \
    --onefile-tempdir-spec="{CACHE_DIR}/pdf2any" \
    --follow-import-to=pdf2any \
    --no-pyi-file \
    pdf2any/__main__.py

# ── Runtime stage ──────────────────────────────────────────────────────────
FROM debian:bookworm-slim

# Copy the built executable
COPY --from=builder /build/pdf2any /usr/local/bin/pdf2any
RUN chmod +x /usr/local/bin/pdf2any

# Create a working directory for mounted files
WORKDIR /work

# Show help by default
ENTRYPOINT ["pdf2any"]
CMD ["--help"]
