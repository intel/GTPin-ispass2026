# HeCBench

This directory is **not** shipped with the repository. It is populated at
setup time by cloning the upstream
[HeCBench](https://github.com/zjin-lcf/HeCBench) repository at commit
[`b59cdcc`](https://github.com/zjin-lcf/HeCBench/commit/b59cdcc3755c3a0cd39b4b9925ac5aa76b1d1171).

## Setup

From the **project root**, run:

```bash
python3 scripts/setup_hecbench.py
```

This will:
1. Sparse-clone the HeCBench repository (only the benchmarks used in this
   artifact are materialized).
2. Check out the exact commit used for the paper experiments.
3. Remove the `.git` directory so the result is a plain source tree.

Only the following SYCL benchmarks are checked out:
atomicReduction, b+tree, burger, convolutionSeparable, dense-embedding,
eigenvalue, floydwarshall, fpc, hmm, hwt1d, inversek2j, matrix-rotate,
maxpool3d, nn, winograd — plus shared `src/data/`.

## License

HeCBench is licensed under the **BSD 3-Clause License**.
Copyright (c) 2020-2023 Zheming Jin. See the `LICENSE` file (created after
running the setup script) for full details.

Individual benchmark source files may carry additional upstream copyright
notices and licenses (e.g. AMD BSD-3-Clause, AMD MIT, NVIDIA EULA)
