/*========================== begin_copyright_notice ============================
Copyright (C) 2018-2026 Intel Corporation

SPDX-License-Identifier: MIT
============================= end_copyright_notice ===========================*/

/*!
 * @file Implementation of the Opcodeprof tool
 */

#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <functional>

#include "opcodeprof.h"

using namespace gtpin;

/* ============================================================================================= */
// Configuration
/* ============================================================================================= */
Knob<int>  knobNumThreadBuckets("num_thread_buckets", 32, "Number of thread buckets. 0 - maximum thread buckets");

/* ============================================================================================= */
// Opcodeprof implementation
/* ============================================================================================= */
Opcodeprof* Opcodeprof::Instance()
{
    static Opcodeprof instance;
    return &instance;
}

void Opcodeprof::OnKernelBuild(IGtKernelInstrument& instrumentor)
{
    const IGtKernel&           kernel    = instrumentor.Kernel();
    const IGtCfg&              cfg       = instrumentor.Cfg();
    const IGtGenCoder&         coder     = instrumentor.Coder();
    const IGtGenModel&         genModel  = kernel.GenModel();
    IGtProfileBufferAllocator& allocator = instrumentor.ProfileBufferAllocator();
    IGtVregFactory&            vregs     = coder.VregFactory();
    IGtInsFactory&             insF      = coder.InstructionFactory();

    // Initialize virtual registers
    GtReg addrReg = vregs.Make(VREG_TYPE_PTR, VREG_FLAG_MSG_ADDR_SCRATCH, 0);
    // GtReg addrReg = vregs.MakeAddrRegScratch(); ///< Virtual register that holds address within profile buffer

    // Allocate the profile buffer. It will hold single OpcodeprofRecord per each basic block in each thread bucket
    uint32_t numThreadBuckets = (knobNumThreadBuckets == 0) ? genModel.MaxThreadBuckets() : knobNumThreadBuckets;
    uint32_t numRecords = cfg.NumBbls();
    GtProfileArray profileArray(sizeof(OpcodeprofRecord), numRecords, numThreadBuckets);
    profileArray.Allocate(allocator);

    // Instrument basic blocks
    for (auto bblPtr : cfg.Bbls())
    {
        if (!bblPtr->IsEmpty())
        {
            GtGenProcedure proc;
            uint32_t recordNum = bblPtr->Id();

            // addrReg =  address of the current thread's OpcodeprofRecord in the profile buffer
            profileArray.ComputeAddress(coder, proc, addrReg, recordNum);

            // [addrReg].freq++
            if (!knobInstrumentPerIns || bblPtr->Instructions().size() == 1)
            {
                proc += insF.MakeAtomicInc(NullReg(), addrReg, GED_DATA_TYPE_ud);
            }
            if (!proc.empty()) { proc.front()->AppendAnnotation(__func__); }
            InstrumentBbl(instrumentor , *bblPtr, GtIpoint::Before(), proc);

            // Instrument each instruction with atomic increment, if requested
            if (knobInstrumentPerIns && bblPtr->Instructions().size() > 1)
            {
                for (auto insPtr : bblPtr->Instructions())
                {
                    GtGenProcedure insProc;
                    // [addrReg].freq++
                    insProc += insF.MakeAtomicInc(NullReg(), addrReg, GED_DATA_TYPE_ud);
                    if (!insProc.empty()) { insProc.front()->AppendAnnotation(__func__); }

                    InstrumentInstruction(instrumentor, *insPtr, GtIpoint::Before(), insProc);
                }
            }
        }
    }

    // Create OpcodeprofKernelProfile object that represents profile of this kernel
    _kernels.emplace(kernel.Id(), OpcodeprofKernelProfile(kernel, cfg, profileArray));
}

void Opcodeprof::OnKernelRun(IGtKernelDispatch& dispatcher)
{
    bool isProfileEnabled = false;
  
    const IGtKernel& kernel = dispatcher.Kernel();
    GtKernelExecDesc execDesc; dispatcher.GetExecDescriptor(execDesc);
    if (kernel.IsInstrumented() && IsKernelExecProfileEnabled(execDesc, kernel.GpuPlatform(), kernel.Name().Get()))
    {
        auto it = _kernels.find(kernel.Id());

        if (it != _kernels.end())
        {
            IGtProfileBuffer*          buffer        = dispatcher.CreateProfileBuffer(); GTPIN_ASSERT(buffer);
            OpcodeprofKernelProfile&   kernelProfile = it->second;
            const GtProfileArray&      profileArray  = kernelProfile.GetProfileArray();
            if (profileArray.Initialize(*buffer))
            {
                isProfileEnabled = true;
            }
            else
            {
                GTPIN_ERROR_MSG("OPCODEPROF: " + std::string(kernel.Name()) + " : Failed to write into memory buffer");
            }
        }
    }

    if (knobRunOriginalModule)
    {
        isProfileEnabled = false; // Run original module without instrumentation
    }

    dispatcher.SetProfilingMode(isProfileEnabled);

    // Start timer for this kernel dispatch
    auto it = _kernels.find(kernel.Id());
    if (it != _kernels.end())
    {
        it->second.StartTimer();
    }
}

void Opcodeprof::OnKernelComplete(IGtKernelDispatch& dispatcher)
{
    // Stop timer for this kernel dispatch
    const IGtKernel& kernel1 = dispatcher.Kernel();
    auto it1 = _kernels.find(kernel1.Id());
    if (it1 != _kernels.end())
    {
        it1->second.StopTimer();
    }

    if (!dispatcher.IsProfilingEnabled())
    {
        return; // Do nothing with unprofiled kernel dispatches
    }

    const IGtKernel& kernel = dispatcher.Kernel();
    auto it = _kernels.find(kernel.Id());

    if (it != _kernels.end())
    {
        const IGtProfileBuffer*  buffer        = dispatcher.GetProfileBuffer(); GTPIN_ASSERT(buffer);
        OpcodeprofKernelProfile& kernelProfile = it->second;
        const GtProfileArray&    profileArray  = kernelProfile.GetProfileArray();

        for (uint32_t recordNum = 0; recordNum != profileArray.NumRecords(); ++recordNum)
        {
            for (uint32_t threadBucket = 0; threadBucket < profileArray.NumThreadBuckets(); ++threadBucket)
            {
                OpcodeprofRecord record;
                if (!profileArray.Read(*buffer, &record, recordNum, 1, threadBucket))
                {
                    GTPIN_ERROR_MSG("OPCODEPROF: " + std::string(kernel.Name()) + " : Failed to read from memory buffer");
                }
                else
                {
                    kernelProfile.Accumulate(record, (BblId)recordNum);
                }
            }
        }
    }
}

void Opcodeprof::Fini()
{
    DumpProfile(_kernels);
    DumpAsm(_kernels);
}

/* ============================================================================================= */
// GTPin_Entry
/* ============================================================================================= */
EXPORT_C_FUNC void GTPin_Entry(int argc, const char* argv[])
{
    ConfigureGTPin(argc, argv);
    Opcodeprof::Instance()->Register();
    atexit(Opcodeprof::OnFini);
}
