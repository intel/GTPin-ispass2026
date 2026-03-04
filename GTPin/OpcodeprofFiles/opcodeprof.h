/*========================== begin_copyright_notice ============================
Copyright (C) 2018-2024 Intel Corporation

SPDX-License-Identifier: MIT
============================= end_copyright_notice ===========================*/

/*!
 * @file Opcodeprof tool definitions
 */

#ifndef OPCODEPROF_H_
#define OPCODEPROF_H_

#include <map>
#include <vector>
#include <string>
#include <tuple>

#include "gtpin_api.h"
#include "gtpin_tool_utils.h"
#include "opcodeprof_utils.h"

using namespace gtpin;


/* ============================================================================================= */
// Class Opcodeprof
/* ============================================================================================= */
/*!
 * Implementation of the IGtTool interface for the opcodeprof tool
 */
class Opcodeprof : public GtTool
{
public:
    /// Implementation of the IGtTool interface
    const char* Name() const { return "opcodeprof"; }

    void OnKernelBuild(IGtKernelInstrument& instrumentor);
    void OnKernelRun(IGtKernelDispatch& dispatcher);
    void OnKernelComplete(IGtKernelDispatch& dispatcher);

public:

    static Opcodeprof* Instance();               ///< @return Single instance of this class
    static void OnFini() { Instance()->Fini(); } ///< Callback function registered with atexit()

private:
    Opcodeprof() = default;
    Opcodeprof(const Opcodeprof&) = delete;
    Opcodeprof& operator = (const Opcodeprof&) = delete;
    ~Opcodeprof() = default;

    void Fini();              /// Post process and dump profiling data

private:
    std::map<GtKernelId, OpcodeprofKernelProfile> _kernels;  ///< Collection of kernel profiles
};

#endif