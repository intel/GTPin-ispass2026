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
Download the HeCBench repository at a specific commit and populate the
HeCBench/ directory with only the benchmark sources needed for the ISPASS
2026 artifact.

Downloads a tarball from GitHub's archive API and selectively extracts
only the required ``src/`` subdirectories (and shared data), keeping the
checkout small.  No ``git`` binary is required.

Usage (from the project root):
    python3 scripts/setup_hecbench.py
    python3 scripts/setup_hecbench.py --help
"""

import argparse
import io
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

HECBENCH_REPO_OWNER = "zjin-lcf"
HECBENCH_REPO_NAME = "HeCBench"
HECBENCH_COMMIT = "b59cdcc3755c3a0cd39b4b9925ac5aa76b1d1171"
HECBENCH_DIR_NAME = "HeCBench"
TARBALL_URL = (
    f"https://github.com/{HECBENCH_REPO_OWNER}/{HECBENCH_REPO_NAME}"
    f"/archive/{HECBENCH_COMMIT}.tar.gz"
)

# Only the benchmark directories actually used in this artifact.
# These must match the names referenced in scripts/specs.yaml.
BENCHMARKS = [
    "atomicReduction",
    "b+tree",
    "burger",
    "convolutionSeparable",
    "dense-embedding",
    "eigenvalue",
    "floydwarshall",
    "fpc",
    "hmm",
    "hwt1d",
    "inversek2j",
    "matrix-rotate",
    "maxpool3d",
    "nn",
    "winograd",
]

# Programming-model suffixes to include for each benchmark.
SUFFIXES = ["sycl"]

# Additional top-level paths inside the repo that are needed.
EXTRA_PATHS = [
    "src/data",
]

# Top-level files (relative to the repo root) that we also need.
TOP_LEVEL_FILES = [
    "LICENSE",
]


def project_root() -> Path:
    """Return the project root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def _wanted_prefixes() -> list[str]:
    """Build the list of path prefixes (inside the tarball) we want to keep.

    GitHub tarballs contain a single top-level directory named
    ``<repo>-<commit>/``.  The prefixes returned here already include that
    leading component so they can be matched directly against tarball member
    names.
    """
    root_in_tar = f"{HECBENCH_REPO_NAME}-{HECBENCH_COMMIT}"
    prefixes = []
    for bench in BENCHMARKS:
        for suffix in SUFFIXES:
            prefixes.append(f"{root_in_tar}/src/{bench}-{suffix}/")
    for extra in EXTRA_PATHS:
        prefixes.append(f"{root_in_tar}/{extra}/")
    return prefixes


def _wanted_files() -> list[str]:
    """Top-level files we want, with the tarball root prefix."""
    root_in_tar = f"{HECBENCH_REPO_NAME}-{HECBENCH_COMMIT}"
    return [f"{root_in_tar}/{f}" for f in TOP_LEVEL_FILES]


def _member_wanted(name: str, prefixes: list[str], files: list[str]) -> bool:
    """Return True if *name* is under one of the wanted prefixes or is an
    exact match for one of the wanted files."""
    for p in prefixes:
        if name.startswith(p):
            return True
    return name in files


def setup_hecbench(hecbench_dir: Path, force: bool = False) -> None:
    # --- Guard -----------------------------------------------------------
    if hecbench_dir.exists():
        has_src = (hecbench_dir / "src").is_dir()
        has_license = (hecbench_dir / "LICENSE").is_file()
        if has_src and has_license:
            if not force:
                print(
                    f"HeCBench already set up at {hecbench_dir}.\n"
                    "  Use --force to re-clone."
                )
                return
            print("  Cleaning existing HeCBench checkout ...")
            for child in hecbench_dir.iterdir():
                if child.name == "README.md":
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()

    hecbench_dir.mkdir(parents=True, exist_ok=True)

    # --- Download tarball ------------------------------------------------
    print(f"[1/2] Downloading tarball for commit {HECBENCH_COMMIT[:12]} ...")
    print(f"  URL: {TARBALL_URL}")
    try:
        response = urllib.request.urlopen(TARBALL_URL)
        tarball_bytes = response.read()
    except Exception as exc:
        print(f"ERROR: failed to download tarball: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  Downloaded {len(tarball_bytes) / 1_048_576:.1f} MiB")

    # --- Extract only the needed paths -----------------------------------
    print("[2/2] Extracting selected benchmarks ...")
    prefixes = _wanted_prefixes()
    files = _wanted_files()
    root_in_tar = f"{HECBENCH_REPO_NAME}-{HECBENCH_COMMIT}"
    strip = len(root_in_tar) + 1  # +1 for the trailing '/'

    extracted = 0
    with tarfile.open(fileobj=io.BytesIO(tarball_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not _member_wanted(member.name, prefixes, files):
                continue
            # Strip the top-level directory from the path
            rel = member.name[strip:]
            if not rel:
                continue
            dest = hecbench_dir / rel
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src_f:
                    if src_f is not None:
                        dest.write_bytes(src_f.read())
                        extracted += 1

    print(f"  Extracted {extracted} files into {hecbench_dir}")
    print(f"\nDone. HeCBench benchmarks are ready at: {hecbench_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clone HeCBench at a specific commit and populate the HeCBench/ "
            "directory with only the benchmarks needed for this artifact."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing HeCBench/ before cloning.",
    )
    args = parser.parse_args()

    root = project_root()
    hecbench_dir = root / HECBENCH_DIR_NAME

    setup_hecbench(hecbench_dir, force=args.force)


if __name__ == "__main__":
    main()
