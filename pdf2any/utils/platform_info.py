"""Platform and architecture detection for wrapper-side documentation.

Provides the platform ID string and artifact name for the current or
a specified OS/arch pair. Used by packaging scripts and documented in
the README for Node.js and Go wrapper integration.
"""

from __future__ import annotations

import platform


def get_platform_id() -> str:
    """Get the platform identifier string like 'linux-amd64'.

    Maps Python's ``platform.system()`` and ``platform.machine()``
    to the pdf2any artifact naming convention.
    """
    os_map = {
        "Linux": "linux",
        "Windows": "windows",
        "Darwin": "macos",
    }
    arch_map = {
        "x86_64": "amd64",
        "AMD64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    os_name = os_map.get(platform.system(), platform.system().lower())
    arch = arch_map.get(platform.machine(), platform.machine().lower())
    return f"{os_name}-{arch}"


def get_artifact_name(os_arch: str | None = None) -> str:
    """Get the expected artifact name for a platform.

    Args:
        os_arch: Platform string like 'linux-amd64'. If None, uses current platform.

    Returns:
        Artifact filename like 'pdf2any-linux-amd64' or 'pdf2any-windows-amd64.exe'.
    """
    if os_arch is None:
        os_arch = get_platform_id()

    if os_arch.startswith("windows"):
        return f"pdf2any-{os_arch}.exe"
    return f"pdf2any-{os_arch}"


def print_platform_docs() -> None:
    """Print platform resolution documentation for wrapper authors."""
    print("Platform resolution for wrapper integrations:")
    print()
    print("Node.js:")
    print("  process.platform → 'darwin' | 'linux' | 'win32'")
    print("  process.arch     → 'x64' | 'arm64'")
    print("  Map: darwin→macos, linux→linux, win32→windows; x64→amd64")
    print()
    print("Go:")
    print("  runtime.GOOS   → 'linux' | 'darwin' | 'windows'")
    print("  runtime.GOARCH → 'amd64' | 'arm64'")
    print()
    print("Current platform:", get_platform_id())
    print("Expected artifact:", get_artifact_name())


if __name__ == "__main__":
    print_platform_docs()
