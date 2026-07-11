# install.ps1 — pdf2any installer for Windows
#
# Usage:
#   irm https://github.com/brainplusplus/pdf2any/releases/latest/download/install.ps1 | iex
#
# Or download and run:
#   powershell -ExecutionPolicy Bypass -File install.ps1
#
# This script:
#   1. Detects architecture (amd64 only on Windows for now)
#   2. Downloads the latest pdf2any binary from GitHub Releases
#   3. Installs it to $env:USERPROFILE\bin (user-local, no admin needed)
#   4. Adds install dir to user PATH if not already there
#   5. Verifies the installation

#Requires -Version 5.0

$ErrorActionPreference = "Stop"

# --- Configuration -------------------------------------------------------

$Repo = "brainplusplus/pdf2any"
$InstallDir = "$env:USERPROFILE\bin"
$BinaryName = "pdf2any.exe"
$BinaryPath = Join-Path $InstallDir $BinaryName

# --- Helper functions ----------------------------------------------------

function Write-Info {
    param([string]$Message)
    Write-Host "==> " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "==> " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Err {
    param([string]$Message)
    Write-Host "Error: " -ForegroundColor Red -NoNewline
    Write-Host $Message
    exit 1
}

# --- Detect architecture -------------------------------------------------

function Detect-Platform {
    $arch = $env:PROCESSOR_ARCHITECTURE

    if ($arch -eq "AMD64") {
        $script:Platform = "windows-amd64"
    } elseif ($arch -eq "ARM64") {
        Write-Err "Windows ARM64 is not yet supported. Please open an issue: https://github.com/$Repo/issues"
    } else {
        Write-Err "Unsupported architecture: $arch"
    }

    Write-Info "Detected platform: $script:Platform"
}

# --- Download binary ----------------------------------------------------

function Download-Binary {
    Write-Info "Fetching latest release..."

    $artifactName = "pdf2any-$script:Platform.exe"
    $downloadUrl = "https://github.com/$Repo/releases/latest/download/$artifactName"

    Write-Info "Downloading: $downloadUrl"

    # Create install directory if it doesn't exist
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    # Download to temp first, then move (avoids partial downloads)
    $tempFile = [System.IO.Path]::GetTempFileName()

    try {
        # Use .NET WebClient for better progress and reliability
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($downloadUrl, $tempFile)
    } catch {
        Write-Err "Download failed: $_"
    }

    # Verify download size (should be > 1MB)
    $fileSize = (Get-Item $tempFile).Length
    if ($fileSize -lt 1048576) {
        Write-Err "Downloaded file is too small ($fileSize bytes). The binary may not exist for $script:Platform."
    }

    $sizeMB = [math]::Round($fileSize / 1MB, 1)
    Write-Info "Downloaded $sizeMB MB"

    # Move to final location
    if (Test-Path $BinaryPath) {
        Remove-Item $BinaryPath -Force
    }
    Move-Item $tempFile $BinaryPath -Force

    # Unblock the downloaded file (removes Windows "downloaded from internet" flag)
    Unblock-File $BinaryPath -ErrorAction SilentlyContinue
}

# --- Add to PATH --------------------------------------------------------

function Add-To-Path {
    # Check if already in PATH
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -split ";" -contains $InstallDir) {
        return
    }

    Write-Info "Adding $InstallDir to user PATH..."

    $newPath = if ($userPath) { "$userPath;$InstallDir" } else { $InstallDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")

    # Also update current session PATH
    $env:Path = "$env:Path;$InstallDir"

    Write-Info "PATH updated. You may need to restart your terminal for changes to take effect."
}

# --- Verify installation ------------------------------------------------

function Verify-Installation {
    Write-Success "pdf2any installed successfully!"

    try {
        & $BinaryPath --version
    } catch {
        Write-Info "Binary installed at: $BinaryPath"
        Write-Info "Run: $BinaryPath --version"
    }

    Write-Host ""
    Write-Host "Quick start:"
    Write-Host "  pdf2any input.pdf -t markdown -o out.md"
    Write-Host "  pdf2any --list-output-formats"
    Write-Host ""
    Write-Host "Documentation: https://github.com/$Repo#readme"
}

# --- Main ----------------------------------------------------------------

Write-Host ""
Write-Host "  ========================================"
Write-Host "  |         pdf2any installer             |"
Write-Host "  |  Pandoc-style PDF converter           |"
Write-Host "  ========================================"
Write-Host ""

Detect-Platform
Download-Binary
Add-To-Path
Verify-Installation
