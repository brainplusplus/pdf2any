#!/bin/sh
# install.sh — pdf2any installer for Linux and macOS
#
# Usage:
#   curl -sL https://github.com/brainplusplus/pdf2any/releases/latest/download/install.sh | sh
#
# Or download and run:
#   sh install.sh
#
# This script:
#   1. Detects OS and architecture
#   2. Downloads the latest pdf2any binary from GitHub Releases
#   3. Installs it to /usr/local/bin (or ~/.local/bin as fallback)
#   4. Makes it executable
#   5. Verifies the installation

set -e

# --- Configuration -------------------------------------------------------

REPO="brainplusplus/pdf2any"
GITHUB_API="https://api.github.com/repos/${REPO}/releases/latest"

# --- Helper functions ----------------------------------------------------

info() {
    printf "\033[1;34m==>\033[0m %s\n" "$1"
}

success() {
    printf "\033[1;32m==>\033[0m %s\n" "$1"
}

error() {
    printf "\033[1;31mError:\033[0m %s\n" "$1" >&2
    exit 1
}

# --- Detect platform -----------------------------------------------------

detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    case "$OS" in
        Linux)  OS="linux" ;;
        Darwin) OS="macos" ;;
        *)      error "Unsupported OS: $OS (only Linux and macOS are supported)" ;;
    esac

    case "$ARCH" in
        x86_64|amd64) ARCH="amd64" ;;
        aarch64|arm64) ARCH="arm64" ;;
        *)             error "Unsupported architecture: $ARCH (only amd64 and arm64 are supported)" ;;
    esac

    PLATFORM="${OS}-${ARCH}"
    info "Detected platform: $PLATFORM"
}

# --- Determine install location -----------------------------------------

determine_install_dir() {
    # Try /usr/local/bin first (system-wide)
    if [ -w "/usr/local/bin" ] || sudo -n true 2>/dev/null; then
        INSTALL_DIR="/usr/local/bin"
    elif [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
        INSTALL_DIR="$HOME/.local/bin"
        info "Installing to $INSTALL_DIR (user-local, no sudo)"
        info "Make sure $INSTALL_DIR is in your PATH"
    else
        error "Cannot find a writable install directory. Try: sudo sh install.sh"
    fi
}

# --- Fetch latest release info ------------------------------------------

fetch_download_url() {
    info "Fetching latest release info..."

    # Use curl or wget
    if command -v curl >/dev/null 2>&1; then
        FETCHER="curl"
    elif command -v wget >/dev/null 2>&1; then
        FETCHER="wget"
    else
        error "Neither curl nor wget is installed. Please install one and retry."
    fi

    # GitHub releases use consistent artifact names
    ARTIFACT="pdf2any-${PLATFORM}"
    DOWNLOAD_URL="https://github.com/${REPO}/releases/latest/download/${ARTIFACT}"

    info "Downloading: $DOWNLOAD_URL"
}

# --- Download binary ----------------------------------------------------

download_binary() {
    TMPFILE="$(mktemp -t pdf2any-XXXXXX)"

    case "$FETCHER" in
        curl)
            curl -sL --fail -o "$TMPFILE" "$DOWNLOAD_URL" || error "Download failed"
            ;;
        wget)
            wget -q -O "$TMPFILE" "$DOWNLOAD_URL" || error "Download failed"
            ;;
    esac

    # Verify we got a real binary (not a 404 HTML page)
    FILE_SIZE=$(wc -c < "$TMPFILE" 2>/dev/null || echo 0)
    if [ "$FILE_SIZE" -lt 1000000 ]; then
        error "Downloaded file is too small ($FILE_SIZE bytes). The binary may not exist for $PLATFORM."
    fi

    info "Downloaded $(echo "$FILE_SIZE" | awk '{printf "%.1f MB", $1/1048576}')"
}

# --- Install binary -----------------------------------------------------

install_binary() {
    TARGET="${INSTALL_DIR}/pdf2any"

    # If installing to /usr/local/bin and not writable, use sudo
    if [ "$INSTALL_DIR" = "/usr/local/bin" ] && [ ! -w "/usr/local/bin" ]; then
        info "Installing to $INSTALL_DIR (requires sudo)"
        sudo install -m 755 "$TMPFILE" "$TARGET"
    else
        install -m 755 "$TMPFILE" "$TARGET"
    fi

    rm -f "$TMPFILE"
}

# --- Verify installation ------------------------------------------------

verify_installation() {
    if command -v pdf2any >/dev/null 2>&1; then
        success "pdf2any installed successfully!"
        pdf2any --version
        echo ""
        echo "Quick start:"
        echo "  pdf2any input.pdf -t markdown -o out.md"
        echo "  pdf2any --list-output-formats"
        echo ""
        echo "Documentation: https://github.com/${REPO}#readme"
    else
        success "pdf2any installed to $TARGET"
        echo ""
        echo "Note: $INSTALL_DIR may not be in your PATH."
        echo "Add it to your shell profile:"
        echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
        echo ""
        echo "Or run directly:"
        echo "  $TARGET --version"
    fi
}

# --- Main ----------------------------------------------------------------

main() {
    echo ""
    echo "  ╔═══════════════════════════════════════╗"
    echo "  ║         pdf2any installer             ║"
    echo "  ║  Pandoc-style PDF converter           ║"
    echo "  ╚═══════════════════════════════════════╝"
    echo ""

    detect_platform
    determine_install_dir
    fetch_download_url
    download_binary
    install_binary
    verify_installation
}

main "$@"
