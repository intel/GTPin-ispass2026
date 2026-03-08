############################ begin_copyright_notice ############################
### Copyright (C) 2026 Intel Corporation
###
### This software and the related documents are Intel copyrighted materials, and your
### use of them is governed by the express license under which they were provided to
### you ("License"). Unless the License provides otherwise, you may not use, modify,
### copy, publish, distribute, disclose or transmit this software or the related
### documents without Intel's prior written permission.
###
### This software and the related documents are provided as is, with no express or
### implied warranties, other than those that are expressly stated in the License.
############################ end_copyright_notice ##############################

#!/usr/bin/env python3
"""
Download NVBit v1.7.4, extract it, and apply local modifications.

This script replaces shipping the full NVBit binary release in the repository.
After running it, the ``nvbit_release/`` directory will contain the upstream
NVBit release with the project's modified ``opcode_hist.cu`` patched in.

Usage:
    python3 scripts/setup_nvbit.py            # run from the project root
    python3 scripts/setup_nvbit.py --help      # see options
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

NVBIT_URL = (
    "https://github.com/NVlabs/NVBit/releases/download/v1.7.4/"
    "nvbit-Linux-x86_64-1.7.4.tar.bz2"
)
NVBIT_ARCHIVE_NAME = "nvbit-Linux-x86_64-1.7.4.tar.bz2"

# Paths are relative to the project root
NVBIT_DIR_NAME = "nvbit_release"
PATCHES_DIR = Path("nvbit_patches")
PATCHED_FILES = {
    # source (in repo) -> destination (after extraction)
    PATCHES_DIR / "opcode_hist.cu": Path(NVBIT_DIR_NAME) / "tools" / "opcode_hist" / "opcode_hist.cu",
}


def project_root() -> Path:
    """Return the project root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def download_nvbit(dest: Path, url: str = NVBIT_URL) -> Path:
    """Download the NVBit archive to *dest* and return the archive path."""
    archive_path = dest / NVBIT_ARCHIVE_NAME
    if archive_path.exists():
        print(f"  Archive already exists: {archive_path}")
        return archive_path

    print(f"  Downloading {url} ...")
    # Try wget first (typically available on Linux), fall back to urllib
    if shutil.which("wget"):
        subprocess.check_call(
            ["wget", "-q", "--show-progress", "-O", str(archive_path), url]
        )
    else:
        urllib.request.urlretrieve(url, str(archive_path))
    print(f"  Saved to {archive_path}")
    return archive_path


def extract_nvbit(archive_path: Path, dest: Path) -> None:
    """Extract the NVBit archive into *dest*."""
    print(f"  Extracting {archive_path.name} ...")
    with tarfile.open(archive_path, "r:bz2") as tar:
        tar.extractall(path=dest)
    print(f"  Extracted to {dest / NVBIT_DIR_NAME}")


def apply_patches(root: Path) -> None:
    """Copy modified files over the extracted NVBit release."""
    for src_rel, dst_rel in PATCHED_FILES.items():
        src = root / src_rel
        dst = root / dst_rel
        if not src.exists():
            print(f"  WARNING: patch source not found: {src}", file=sys.stderr)
            continue
        print(f"  Patching {dst_rel} ...")
        shutil.copy2(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download NVBit v1.7.4 and apply local modifications."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing nvbit_release/ before downloading.",
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Keep the downloaded .tar.bz2 archive after extraction.",
    )
    args = parser.parse_args()

    root = project_root()
    nvbit_dir = root / NVBIT_DIR_NAME

    # --- Guard -----------------------------------------------------------
    if nvbit_dir.exists() and any(nvbit_dir.iterdir()):
        # Check if it looks like a full extraction (has core/ and tools/)
        if (nvbit_dir / "core").is_dir() and (nvbit_dir / "tools").is_dir():
            if not args.force:
                print(
                    f"NVBit already set up at {nvbit_dir}.\n"
                    "  Use --force to re-download and re-extract."
                )
                return
            print(f"  Removing existing {nvbit_dir} ...")
            # Preserve our README.md
            readme = nvbit_dir / "README.md"
            readme_backup = None
            if readme.exists():
                readme_backup = root / ".nvbit_readme_backup"
                shutil.copy2(readme, readme_backup)

            shutil.rmtree(nvbit_dir)

            if readme_backup and readme_backup.exists():
                nvbit_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(readme_backup), str(readme))

    # --- Download --------------------------------------------------------
    print("[1/3] Downloading NVBit v1.7.4 ...")
    archive_path = download_nvbit(root, NVBIT_URL)

    # --- Extract ---------------------------------------------------------
    print("[2/3] Extracting ...")
    extract_nvbit(archive_path, root)

    if not args.keep_archive:
        archive_path.unlink()
        print(f"  Removed archive {archive_path.name}")

    # --- Patch -----------------------------------------------------------
    print("[3/3] Applying local modifications ...")
    apply_patches(root)

    print("\nDone. NVBit is ready at:", nvbit_dir)


if __name__ == "__main__":
    main()
