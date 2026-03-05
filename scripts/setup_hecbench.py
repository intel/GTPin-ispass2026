#!/usr/bin/env python3
"""
Clone the HeCBench repository at a specific commit and populate the HeCBench/
directory with only the benchmark sources needed for the ISPASS 2026 artifact.

Uses ``git`` sparse-checkout so that only the required ``src/`` subdirectories
(and shared data) are materialized on disk, keeping the checkout small.

Usage (from the project root):
    python3 scripts/setup_hecbench.py
    python3 scripts/setup_hecbench.py --help
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HECBENCH_REPO = "https://github.com/zjin-lcf/HeCBench.git"
HECBENCH_COMMIT = "b59cdcc3755c3a0cd39b4b9925ac5aa76b1d1171"
HECBENCH_DIR_NAME = "HeCBench"

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


def project_root() -> Path:
    """Return the project root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, printing it first, and abort on failure."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"ERROR: command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def sparse_checkout_paths() -> list[str]:
    """Build the list of sparse-checkout include paths."""
    paths = []
    for bench in BENCHMARKS:
        for suffix in SUFFIXES:
            paths.append(f"src/{bench}-{suffix}")
    paths.extend(EXTRA_PATHS)
    # Also include top-level files (LICENSE, README, etc.)
    paths.append("LICENSE")
    paths.append("README.md")
    return paths


def setup_hecbench(hecbench_dir: Path, force: bool = False) -> None:
    # --- Guard -----------------------------------------------------------
    if hecbench_dir.exists():
        # Check if it looks like a populated checkout
        has_src = (hecbench_dir / "src").is_dir()
        has_license = (hecbench_dir / "LICENSE").is_file()
        if has_src and has_license:
            if not force:
                print(
                    f"HeCBench already set up at {hecbench_dir}.\n"
                    "  Use --force to re-clone."
                )
                return
            print(f"  Removing existing {hecbench_dir} (keeping README.md) ...")
            readme = hecbench_dir / "README.md"
            readme_backup = None
            if readme.exists():
                readme_backup = hecbench_dir.parent / ".hecbench_readme_backup"
                shutil.copy2(readme, readme_backup)

            shutil.rmtree(hecbench_dir)

            if readme_backup and readme_backup.exists():
                hecbench_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(readme_backup), str(readme))

    # --- Clone with sparse checkout -------------------------------------
    print("[1/3] Cloning HeCBench (sparse) ...")
    _run([
        "git", "clone",
        "--no-checkout",
        "--filter=blob:none",
        HECBENCH_REPO,
        str(hecbench_dir),
    ])

    # --- Configure sparse checkout --------------------------------------
    print("[2/3] Configuring sparse checkout ...")
    _run(["git", "-C", str(hecbench_dir), "sparse-checkout", "init", "--cone"])
    paths = sparse_checkout_paths()
    _run(["git", "-C", str(hecbench_dir), "sparse-checkout", "set"] + paths)

    # --- Checkout the exact commit --------------------------------------
    print(f"[3/3] Checking out commit {HECBENCH_COMMIT[:12]} ...")
    _run(["git", "-C", str(hecbench_dir), "checkout", HECBENCH_COMMIT])

    # Remove the .git directory to avoid shipping nested repos
    git_dir = hecbench_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
        print("  Removed .git directory from HeCBench/")

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
