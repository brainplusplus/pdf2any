"""Artifact naming — maps OS/arch pairs to release artifact filenames.

Target artifacts:
    pdf2any-linux-amd64
    pdf2any-linux-arm64
    pdf2any-windows-amd64.exe
    pdf2any-macos-amd64
    pdf2any-macos-arm64

Binaries are built per OS/architecture — there is no universal binary.
Each target runs only on its native OS/architecture.
"""

from __future__ import annotations

# Mapping of (os, arch) → artifact name
ARTIFACT_NAMES: dict[str, str] = {
    "linux-amd64": "pdf2any-linux-amd64",
    "linux-arm64": "pdf2any-linux-arm64",
    "windows-amd64": "pdf2any-windows-amd64.exe",
    "macos-amd64": "pdf2any-macos-amd64",
    "macos-arm64": "pdf2any-macos-arm64",
}

# All supported targets
SUPPORTED_TARGETS = list(ARTIFACT_NAMES.keys())


def get_artifact_name(target: str) -> str:
    """Get the artifact filename for a target.

    Args:
        target: OS-arch string like 'linux-amd64'.

    Returns:
        Artifact filename like 'pdf2any-linux-amd64' or
        'pdf2any-windows-amd64.exe'.

    Raises:
        ValueError: If the target is not in SUPPORTED_TARGETS.
    """
    if target not in ARTIFACT_NAMES:
        raise ValueError(
            f"Unsupported target: '{target}'. "
            f"Supported: {', '.join(SUPPORTED_TARGETS)}"
        )
    return ARTIFACT_NAMES[target]


def list_targets() -> list[str]:
    """List all supported build targets."""
    return SUPPORTED_TARGETS.copy()


if __name__ == "__main__":
    print("Supported build targets:")
    for target in SUPPORTED_TARGETS:
        print(f"  {target:20s} → {ARTIFACT_NAMES[target]}")
