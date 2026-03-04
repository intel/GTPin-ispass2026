/*========================== begin_copyright_notice ============================
Copyright (C) 2024-2026 Intel Corporation

SPDX-License-Identifier: MIT
============================= end_copyright_notice ===========================*/

/*!
 * @file Opcodeprof tool utilities and definitions
 */

#ifndef OPCODEPROF_UTILS_H_
#define OPCODEPROF_UTILS_H_

#include <map>
#include <chrono>

#include "gtpin_api.h"
#include "gtpin_tool_utils.h"

extern Knob<bool>  knobInstrumentPerIns;
extern Knob<bool>  knobRunOriginalModule;

/*!
 * Layout of data records collected by the opcodeprof tool for each basic block
 */
struct OpcodeprofRecord
{
    uint32_t freq; ///< Total number of BBL executions
};

/* ============================================================================================= */
//  class OpcodeprofHistogram
/* ============================================================================================= */
/// Histogram of integer values indexed by {dataType, simdWidth, opcode} keys
class OpcodeprofHistogram
{
public:
    /// Construct an (empty) histogram with zero values for all keys
    OpcodeprofHistogram() = default;

    /// @return Histogram value for the {dataType, simdWidth, opcode} key.
    uint64_t operator()(GtDataType dataType, uint32_t simdWidth, GtOpcode opcode) const;

    /// Addition assignment operator
    OpcodeprofHistogram& operator+=(const OpcodeprofHistogram& rh);

    /// Add 'addVal' to the value associated with the the {dataType, simdWidth, opcode} key.
    uint64_t Add(GtDataType dataType, uint32_t simdWidth, GtOpcode opcode, uint64_t addVal);

    /// @return Sum of all values for all keys
    uint64_t Total() const;

    /*!
     * Convert this histogram to string. Optionally, include data of another histogram, if specified
     * @param[in]       title               Title of the histogram
     * @param[in, opt]  otherHistogram      Other histogram's data to be included, if specified
     */
    std::string ToString(const std::string& title, const OpcodeprofHistogram* otherHistogram = nullptr) const;

private:
    using Key = std::tuple<GED_DATA_TYPE, uint32_t, GED_OPCODE>; // {dataType, simdWidth, opcode}
    std::map<Key, uint64_t> _data;
};

/* ============================================================================================= */
// Struct InsInfo
/* ============================================================================================= */
/*!
 * Properties of a GEN instruction used in the Opcodeprof analysis
 */
struct InsInfo
{
    InsInfo(const IGtIns& ins);

    InsId       insId;      ///< Instruction ID
    GtOpcode    opcode;     ///< Opcode
    uint32_t    simdWidth;  ///< SIMD width
    GtDataType  dataType;   ///< Data type
};

/* ============================================================================================= */
// Class OpcodeprofKernelProfile
/* ============================================================================================= */
/*!
 * Aggregated profile of all instrumented kernel dispatches
 */
class OpcodeprofKernelProfile
{
public:
    OpcodeprofKernelProfile(const IGtKernel& kernel, const IGtCfg& cfg, const GtProfileArray& profileArray);

    std::string            GetName()            const { return _name; }         ///< @return Kernel's name
    std::string            GetUniqueName()      const { return _uniqueName; }   ///< @return Kernel's unique name
    const GtProfileArray&  GetProfileArray()    const { return _profileArray; } ///< @return Profile buffer accessor
    std::vector<uint64_t>& GetBblFreq()               { return _bblFreq; }      ///< @return Bbl frequency counter array

    void                  DumpAsm()             const;  ///< Dump kernel's assembly text to file
    std::string           GetAsmWithCounters()  const;  ///< @return Kernel's assembly with dynamic instruction counters

    /// Accumulate profile counters collected in the specified BBL
    void Accumulate(const OpcodeprofRecord& record, BblId bblId);

    /*!
     * Add dynamic/static instruction counters of this kernel to the specified histogram
     * @param[out] histogram    Histogram that receives dynamic/static instruction counters
     * @return Total number of dynamic/static instruction in the kernel
     */
    uint64_t AddDynamicCountersTo(OpcodeprofHistogram& histogram) const;
    uint64_t AddStaticCountersTo(OpcodeprofHistogram& histogram)  const;

    void StartTimer()
    {
        _start = std::chrono::steady_clock::now();
    }

    void StopTimer()
    {
        _end = std::chrono::steady_clock::now();
        _totalTime = _end - _start;
    }

    double GetElapsedTime() const
    {
        return _totalTime.count();
    }

private:
    std::string                         _name;              ///< Kernel's name
    std::string                         _uniqueName;        ///< Kernel's unique name
    std::vector<std::vector<InsInfo>>   _bblInfo;           ///< Arrays of BBL instructions indexed by BBL ID
    std::string                         _asmText;           ///< Kernel's assembly text
    std::map<InsId, std::string>        _asmLines;          ///< Instrucitons assembly, indexed by instruction ID

    GtProfileArray                      _profileArray;      ///< Profile buffer accessor
    std::vector<uint64_t>               _bblFreq;           ///< BBL execution counters, indexed by BBL ID

    std::chrono::steady_clock::time_point _start;
    std::chrono::steady_clock::time_point _end;
    std::chrono::duration<double>         _totalTime = {};
};

// Dump results utilities
void DumpProfile(const std::map<GtKernelId, OpcodeprofKernelProfile>& kernels); ///< Dump text representation of the profile data
void DumpAsm(const std::map<GtKernelId, OpcodeprofKernelProfile>& kernels);     ///< Dump assembly text of profiled kernels to files


#endif