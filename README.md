# ISPASS 2026 GTPin Artifact – Environment & Execution Guide

This document describes how to set up and run the ISPASS 2026 GTPin artifact on Intel ORTCE infrastructure for both **AMD MI250** and **NVIDIA A100** platforms.

---

## Prerequisites

### Intel ORTCE Environment
- **Required permissions**:
  - `sudo`
  - `debug`
- **Target machines**:
  - `ortce-amdgpu-mi250`
  - `ortce-a100-80G1`

---

## Connecting to ORTCE

### Login to ORTCE Lab
```bash
ssh rburstei@ortce-skl.jf.intel.com
```

---

## AMD MI250 Setup

### Connect to AMD MI250 Node
```bash
srun -w ortce-amdgpu-mi250 --pty bash
```

### Long Runs (Debug Queue)
For long executions, use the debug queue (requires re-approval):
```bash
srun -p debug --qos=debug -w ortce-amdgpu-mi250 --time=2000 --pty /bin/bash
```

---

### Repository Setup
Clone the repository or move to your existing environment:
```bash
cd /nfs/pdx/home/rburstei/gtpin/gtpin-ispass2026/
```

---

### Run Docker Container (AMD)

> **Note:** `sudo` permissions are required.

```bash
sudo docker run --rm -it   -v $PWD:/work/   --device=/dev/kfd   --device=/dev/dri/   --privileged   --security-opt seccomp=unconfined   --shm-size=16G   --cap-add=SYS_PTRACE   --ipc=host   intel-gtpin-ispass-2026-artifact   /bin/bash
```

Alternative container image:
```bash
sudo docker run --rm -it   -v $PWD:/work/   --device=/dev/kfd   --device=/dev/dri/   --privileged   --security-opt seccomp=unconfined   --shm-size=16G   --cap-add=SYS_PTRACE   --ipc=host   containers.rc.northeastern.edu/luthier/ispass-2025-artifact   /bin/bash
```

---

### Build SYCL Applications (AMD Only)
If required:
```bash
python3 scripts/compile_benchmarks.py --action clean
```

---

### Run Experiments (AMD)

Default run:
```bash
python3 scripts/amd_opcode_histogram.py --dump_stdout_stderr
```

Reduced specification set:
```bash
python3 scripts/amd_opcode_histogram.py --dump_stdout_stderr --specs_yaml scripts/specs_reduced.yaml
```

---

## NVIDIA A100 Setup

### Connect to NVIDIA A100 Node
```bash
srun -w ortce-a100-80G1 --pty bash
```

### Long Runs (Debug Queue)
```bash
srun -p debug --qos=debug -w ortce-a100-80G1 --time=2000 --pty /bin/bash
```

---

### Run Docker Container (NVIDIA)

```bash
docker run --gpus all -it   -v $(pwd):/work   containers.rc.northeastern.edu/luthier/ispass-2025-artifact:latest
```

---

## Notes
- Ensure you are running on the correct node (AMD vs. NVIDIA) before launching Docker.
- Debug queue usage may require prior approval.
- Paths and permissions assume Intel ORTCE infrastructure.

---
