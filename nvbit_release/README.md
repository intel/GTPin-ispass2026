# NVBit Release

This directory is **not** shipped with the repository. It is populated at
setup time by downloading the upstream
[NVBit v1.7.4](https://github.com/NVlabs/NVBit) release.

## Setup

From the **project root**, run:

```bash
python3 scripts/setup_nvbit.py
```

This will:
1. Download `nvbit-Linux-x86_64-1.7.4.tar.bz2` from the NVBit GitHub releases.
2. Extract it into this directory (`nvbit_release/`).
3. Patch `tools/opcode_hist/opcode_hist.cu` with the version modified for
   the ISPASS 2026 experiments (adds per-kernel host-side timing).

The patched source file is stored in [`nvbit_patches/opcode_hist.cu`](../nvbit_patches/opcode_hist.cu).

## License

NVBit is covered by the NVIDIA CUDA Toolkit End User License Agreement.
Individual source files are licensed under the BSD 3-Clause License.
See the `LICENSE` and `EULA.txt` files that are included in the extracted
release for full details.
