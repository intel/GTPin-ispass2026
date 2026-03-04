

# Setup Environment
source /opt/intel/oneapi/setvars.sh

GTPIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$GTPIN_DIR")"
HECBENCH_DIR="$BASE_DIR/HeCBench"
SCRIPTS_DIR="$BASE_DIR/scripts"

echo "Base Directory: $BASE_DIR"
echo "GTPin Directory: $GTPIN_DIR"
echo "HeCBench Directory: $HECBENCH_DIR"
echo "Scripts Directory: $SCRIPTS_DIR"

cd "$BASE_DIR"

# Compile Applications
python3 "$SCRIPTS_DIR/compile_benchmarks.py" --action build --programming_model sycl-intel --hecbench_dir "$HECBENCH_DIR"

# Compile GTPin tools
cd "$GTPIN_DIR"
rm -rf ./Profilers
if ! ls ./*.tar.xz 1> /dev/null 2>&1; then
    wget https://downloadmirror.intel.com/913776/external-release-gtpin-4.7-linux.tar.xz
fi
tar -xf ./*.tar.xz
mkdir Profilers/Examples/build
cd Profilers/Examples/build
cp "$GTPIN_DIR/OpcodeprofFiles/"* ../ -r # Copy modified opcodeprof files to GTPin kit
# Note - must pass full path to GTPIN kit
cmake .. -DCMAKE_BUILD_TYPE=Release -DARCH=intel64 -DGTPIN_KIT="$GTPIN_DIR/Profilers/"
make -j 8 install
cd "$BASE_DIR"

# Run GTPin tools to collect opcode profiles
echo "*******************************************************"
echo "Running GTPin Opcodeprof on HeCBench applications"
echo "*******************************************************"
CMD_LINE="python3 \"$SCRIPTS_DIR/gtpin_opcodeprof.py\" --hecbench_dir \"$HECBENCH_DIR\" --gtpin_profiler_path \"$GTPIN_DIR/Profilers/\" --specs_yaml \"$SCRIPTS_DIR/specs_reduced.yaml\" --overwrite_results"
echo $CMD_LINE
eval $CMD_LINE

# Convert GTPin output to CSV for analysis
echo "*******************************************************"
echo "Converting GTPin Opcodeprof output to CSV"
echo "*******************************************************"
CMD_LINE="python3 \"$SCRIPTS_DIR/gtpin_print_opcodeprof.py\" --hecbench \"$HECBENCH_DIR\" --specs_yaml \"$SCRIPTS_DIR/specs_reduced.yaml\""
echo $CMD_LINE
eval $CMD_LINE