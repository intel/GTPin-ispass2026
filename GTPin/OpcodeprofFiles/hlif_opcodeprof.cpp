/*========================== begin_copyright_notice ============================
Copyright (C) 2024-2026 Intel Corporation

SPDX-License-Identifier: MIT
============================= end_copyright_notice ===========================*/

/*!
 * @file Opcodeprof tool implementation that demonstrates HLIF interface
 */

#include "gtpin_api.h"
#include "gtpin_tool_utils.h"
#include "opcodeprof_utils.h"

using namespace gtpin;
using namespace std;


/* ============================================================================================= */
// Class HlifOpcodeprof
/* ============================================================================================= */
/*!
 * Implementation of the IGtTool interface for the opcodeprof tool with HLIF
 */
class HlifOpcodeprof : public GtTool
{
public:
    // Implementation of the IGtTool interface
    const char* Name()          const                   override { return "HLIF opcodeprof"; }
    void        OnKernelBuild(IGtKernelInstrument&)     override;
    void        OnKernelRun(IGtKernelDispatch&)         override;
    void        OnKernelComplete(IGtKernelDispatch&)    override;

    void                   LoadHliLibrary();            ///< Compile and load library of HLI functions
    static HlifOpcodeprof* Instance();                  ///< Return single instance of this class
    static void OnFini() { Instance()->Fini(); }        ///< Callback function registered with atexit()

    void Fini();                                        /// Post process and dump profiling data

private:
    HlifOpcodeprof() : _atomicIncFunc("AtomicInc"), _hliModule(nullptr) {} ///< Constructor

    GtHliFunction<uint64_t, uint64_t*>  _atomicIncFunc; ///< Instrumentation function: uint64_t AtomicInc(uint64_t* ptr);
    IGtHliModuleHandle                  _hliModule;     ///< Module of HLI functions

    using KernelProfile = std::vector<uint64_t>;               ///< Vector of execution counters indexed by basic block IDs
    std::map<GtKernelId, OpcodeprofKernelProfile> _kernels;    ///< Collection of kernel profiles
};

/* ============================================================================================= */
// HlifOpcodeprof implementation
/* ============================================================================================= */
HlifOpcodeprof* HlifOpcodeprof::Instance()
{
    static HlifOpcodeprof instance;
    return &instance;
}

void HlifOpcodeprof::LoadHliLibrary()
{
    std::string installDir = GetKnobValue<std::string>("installDir");
    _hliModule = GTPin_GetCore()->HliLibrary().CompileModuleFromFile(JoinPath(installDir, "Examples", "hli_sample.cl").c_str());
    GTPIN_ASSERT(_hliModule != nullptr);
}

void HlifOpcodeprof::Fini()
{
    DumpProfile(_kernels);
    DumpAsm(_kernels);
}

void HlifOpcodeprof::OnKernelBuild(IGtKernelInstrument& instrumentor)
{
    // Create OpcodeprofKernelProfile object that represents profile of this kernel
    const IGtKernel& kernel = instrumentor.Kernel();
    auto             result = _kernels.emplace(kernel.Id(), OpcodeprofKernelProfile(kernel, instrumentor.Cfg(), GtProfileArray()));

    GTPIN_ASSERT(result.second);
    KernelProfile& profile = result.first->second.GetBblFreq();

    // Share profile data between host and device memory
    instrumentor.MemoryMapper().Map(profile);

    // Link the kernel with the library of HLI functions
    instrumentor.LinkHliModule(_hliModule);

    // Instrument basic blocks
    for (auto bblPtr : instrumentor.Cfg().Bbls())
    {
        if (!((uint32_t)knobMinInstrumentBbl <= bblPtr->Id() && bblPtr->Id() <= (uint32_t)knobMaxInstrumentBbl))
        {
            continue;
        }
        if (!bblPtr->IsEmpty())
        {
            GTPIN_ASSERT(bblPtr->Id() < profile.size());

            if (knobInstrumentPerIns)
            {
                for (auto insPtr : bblPtr->Instructions())
                {
                    if (!((uint32_t)knobMinInstrumentIns <= insPtr->Id() && insPtr->Id() <= (uint32_t)knobMaxInstrumentIns))
                    {
                        continue;
                    }
                    _atomicIncFunc.InsertCallAtInstruction(instrumentor, *insPtr, GtIpoint::Before(),
                                                            NullReg(),                       // Unused return value
                                                            profile.data() + bblPtr->Id());  // arg[0]: Counter to be incremented
                }
            }
            else
            {
                _atomicIncFunc.InsertCallAtBbl(instrumentor, *bblPtr, GtIpoint::Before(),
                                                NullReg(),                       // Unused return value
                                                profile.data() + bblPtr->Id());  // arg[0]: Counter to be incremented
            }
        }
    }
}

void HlifOpcodeprof::OnKernelRun(IGtKernelDispatch& dispatcher)
{
    // Tell GTPin to run instrumented code
    if (knobRunOriginalModule)
    {
        dispatcher.SetProfilingMode(false); // Run original module without instrumentation
    }
    else
    {
        dispatcher.SetProfilingMode(true);  // Run instrumented module
    }

    // Start timer for this kernel dispatch
    const IGtKernel& kernel = dispatcher.Kernel();
    auto it = _kernels.find(kernel.Id());
    if (it != _kernels.end())
    {
        it->second.StartTimer();
    }
}

void HlifOpcodeprof::OnKernelComplete(IGtKernelDispatch& dispatcher)
{
    // Stop timer for this kernel dispatch
    const IGtKernel& kernel = dispatcher.Kernel();
    auto it = _kernels.find(kernel.Id());
    if (it != _kernels.end())
    {
        it->second.StopTimer();
    }

    if (!dispatcher.IsProfilingEnabled())
    {
        return; // Do nothing with unprofiled kernel dispatches
    }

    // No need to accumulate results - increment is executed directly to the profile's counters vector
}

/* ============================================================================================= */
// GTPin_Entry
/* ============================================================================================= */
EXPORT_C_FUNC void GTPin_Entry(int argc, const char *argv[])
{
    // Parse command line and configure GTPin
    ConfigureGTPin(argc, argv);

    // Register the tool (callbacks) with the GTPin core
    HlifOpcodeprof::Instance()->Register();

    // Compile and load library of HLI functions
    HlifOpcodeprof::Instance()->LoadHliLibrary();

    // Register the termination function
    atexit(HlifOpcodeprof::OnFini);
}
