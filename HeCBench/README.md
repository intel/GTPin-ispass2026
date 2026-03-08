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
1. Download a tarball from GitHub's archive API for the pinned commit
   (no `git` binary required).
2. Selectively extract only the 15 SYCL benchmark directories and the
   `LICENSE` file.
3. Download the `nn` and `b+tree` data archives (`src/data/nn/nn.tar.bz`
   and `src/data/b+tree/b+tree.tar.bz`) from the `master` branch and
   extract them into `src/data/nn/` and `src/data/b+tree/`.

Only the following SYCL benchmarks are extracted:
atomicReduction, b+tree, burger, convolutionSeparable, dense-embedding,
eigenvalue, floydwarshall, fpc, hmm, hwt1d, inversek2j, matrix-rotate,
maxpool3d, nn, winograd — plus shared data under `src/data/nn/` and
`src/data/b+tree/`.

## License

HeCBench is licensed under the **BSD 3-Clause License**.
Copyright (c) 2020-2023 Zheming Jin. See the `LICENSE` file (created after
running the setup script) for full details.

Individual benchmark source files may carry additional upstream copyright
notices and licenses (e.g. AMD BSD-3-Clause, AMD MIT, NVIDIA EULA)
