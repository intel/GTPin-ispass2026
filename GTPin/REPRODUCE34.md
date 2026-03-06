# Reproducing Figure 3 and Figure 4

This guide explains how to reproduce Figures 3 and 4 from the GTPin-ispass2026 paper on an Intel&reg; GPU system.

## Prerequisites

It is assumed you followed the instructions in the GTPin-ispass2026/README.md up to number 6

NOTE: Make sure you are running in an environment *WITHOUT* oneAPI loaded

## Figure 3: Memory cache tests
For this test we use the ze_gemm sample application
### Setup
Starting from the GTPin-ispass2026 folder
```bash
cd ./pti-gpu/samples/ze_gemm/
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
./ze_gemm
```

### Run
Starting from the GTPin-ispass2026 folder
```bash
python3 ./scripts/intel_memory_cache_model.py
python3 ./scripts/intel_print_memory_cache_model.py
```

## Figure 4: Race condition detection
For this test we use an application that simulates memory race conditions

### Setup
Starting from the GTPin-ispass2026 folder

```bash
cd ./GTPin/race_condition
make clean
make
```
### Run
Starting from the GTPin-ispass2026 folder
```bash
python3 ./scripts/intel_detect_race_condition.py
python3 ./scripts/intel_print_detect_race_condition.py
```
