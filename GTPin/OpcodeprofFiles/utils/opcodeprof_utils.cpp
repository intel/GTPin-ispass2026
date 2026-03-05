/*========================== begin_copyright_notice ============================
Copyright (C) 2024-2026 Intel Corporation

SPDX-License-Identifier: MIT
============================= end_copyright_notice ===========================*/

/*!
 * @file Implementation of the Opcodeprof tool utilities and definitions
 */

#include "opcodeprof_utils.h"

Knob<bool> knobTotalOnly("total_only", false, "opcodeprof: provide only aggregated data over all kernels over entire workload");
Knob<bool> knobInstrumentPerIns("instrument_per_ins", false, "opcodeprof: instrument each instruction with separate counter instead of sharing counter per basic block");
Knob<bool> knobRunOriginalModule("run_original_module", false, "opcodeprof: run original module without instrumentation");

using namespace gtpin;

/* ============================================================================================= */
// class OpcodeprofHistogram
/* ============================================================================================= */
uint64_t OpcodeprofHistogram::operator()(GtDataType dataType, uint32_t simdWidth, GtOpcode opcode) const
{
    auto it = _data.find({dataType, simdWidth, opcode});
    return ((it == _data.end()) ? 0 : it->second);
}

OpcodeprofHistogram& OpcodeprofHistogram::operator+=(const OpcodeprofHistogram& rh)
{
    for (auto& entry: rh._data)
    {
        const Key& key = entry.first;
        Add(std::get<0>(key), std::get<1>(key), std::get<2>(key), entry.second);
    }
    return *this;
}

uint64_t OpcodeprofHistogram::Add(GtDataType dataType, uint32_t simdWidth, GtOpcode opcode, uint64_t addVal)
{
    uint64_t value = 0;
    if (addVal != 0)
    {
        auto ret = _data.insert({{dataType, simdWidth, opcode}, 0});
        value = (ret.first->second += addVal);
    }
    return value;
}

uint64_t OpcodeprofHistogram::Total() const
{
    uint64_t total = 0; for (auto& entry: _data) { total += entry.second; } return total;
}

std::string OpcodeprofHistogram::ToString(const std::string& title, const OpcodeprofHistogram* otherHistogram) const
{
    std::ostringstream os;

    uint64_t total      = Total();
    uint64_t otherTotal = (otherHistogram == nullptr) ? 0 : otherHistogram->Total();

    // For each data type, sort histogram keys in descending order of the corresponding values
    std::map<GED_DATA_TYPE, std::multimap<uint64_t, Key, std::greater<uint64_t>>> sortedHistogram;
    for (auto& entry: _data)
    {
        const Key& key      = entry.first;
        GtDataType dataType = std::get<0>(key);
        uint64_t   value    = entry.second;

        auto ret = sortedHistogram.insert({dataType, decltype(sortedHistogram)::mapped_type()});
        ret.first->second.insert({value, key});
    }

    // For each data type, convert entries of the sorted histogram into strings
    for (auto& entry: sortedHistogram)
    {
        GtDataType dataType = entry.first;
        os << "DATA TYPE: " << dataType.ToString() << std::endl << std::endl << title << std::endl;

        for (const auto& dtEntry: entry.second)
        {
            uint64_t    value     = dtEntry.first;
            const Key&  key       = dtEntry.second;
            uint32_t    simdWidth = std::get<1>(key);
            GtOpcode    opcode    = std::get<2>(key);

            os << std::setw(23) << opcode.ToString() << std::setw(6) << simdWidth;
            if (otherTotal != 0)
            {
                uint64_t otherValue = (*otherHistogram)(dataType, simdWidth, opcode);
                os << std::setw(15) << otherValue;
                os << " (" << std::fixed << std::setw(4) << std::setprecision(1) << (100 * (float)otherValue / (float)otherTotal) << "%)";
            }

            GTPIN_ASSERT(total != 0);
            os << std::setw(15) << value;
            os << " (" << std::fixed << std::setw(4) << std::setprecision(1) << (100 * (float)value / (float)total) << "%)";
            os << std::endl;
        }
        os << std::endl << std::endl;
    }
    return os.str();
}

/* ============================================================================================= */
// InsInfo implementation
/* ============================================================================================= */
InsInfo::InsInfo(const IGtIns& ins)
{
    insId  = ins.Id();      GTPIN_ASSERT(insId.IsValid());
    opcode = ins.Opcode();  GTPIN_ASSERT(opcode.IsValid());

    GtExecSize execSize = ins.ExecSize();
    simdWidth = execSize.IsValid() ? (uint32_t)execSize : 0;

    if (ins.SrcRegFile(0).IsReg())
    {
        dataType = ins.SrcRegOperand(0).DataType();
    }
    else if (ins.SrcRegFile(0).IsImm())
    {
        dataType = ins.SrcImmOperand(0).DataType();
    }
    if (!dataType.IsValid())
    {
        dataType = GED_DATA_TYPE_ud;
    }
}

/* ============================================================================================= */
// OpcodeprofKernelProfile implementation
/* ============================================================================================= */
OpcodeprofKernelProfile::OpcodeprofKernelProfile(const IGtKernel& kernel, const IGtCfg& cfg, const GtProfileArray& profileArray) :
    _name(GlueString(kernel.Name())), _uniqueName(kernel.UniqueName()), _bblInfo(cfg.NumBbls()),
    _asmText(CfgAsmText(cfg)), _profileArray(profileArray), _bblFreq(cfg.NumBbls(), 0)
{
    for (auto bblPtr : cfg.Bbls())
    {
        BblId bblId = bblPtr->Id();
        for (auto insPtr : bblPtr->Instructions())
        {
            _bblInfo[bblId].emplace_back(*insPtr);
            _asmLines.emplace(insPtr->Id(), insPtr->ToString());
        }
    }
}

void OpcodeprofKernelProfile::DumpAsm() const
{
    DumpKernelAsmText(_name, _uniqueName, _asmText);
}

std::string OpcodeprofKernelProfile::GetAsmWithCounters() const
{
    std::ostringstream ostr;

    GTPIN_ASSERT(_bblFreq.size() == _bblInfo.size());
    for (uint32_t bblId = 0; bblId != _bblInfo.size(); bblId++)
    {
        for (const auto& insInfo : _bblInfo[bblId])
        {
            uint64_t freq = _bblFreq[bblId];
            if (knobInstrumentPerIns)
            {
                freq = _bblFreq[bblId] / _bblInfo[bblId].size();
            }
            ostr << "[" << std::setw(15) << freq << "]     " << _asmLines.at(insInfo.insId) << std::endl;
        }
    }
    return ostr.str();
}

void OpcodeprofKernelProfile::Accumulate(const OpcodeprofRecord& record, BblId bblId)
{
    GTPIN_ASSERT(bblId < _bblFreq.size());
    _bblFreq[bblId] += record.freq;
}

uint64_t OpcodeprofKernelProfile::AddDynamicCountersTo(OpcodeprofHistogram& histogram) const
{
    uint64_t icount = 0;

    GTPIN_ASSERT(_bblFreq.size() == _bblInfo.size());
    for (uint32_t bblId = 0; bblId < _bblInfo.size(); bblId++)
    {
        if (_bblFreq[bblId])
        {
            for (const auto& insInfo: _bblInfo[bblId])
            {
                uint64_t freq = _bblFreq[bblId];
                if (knobInstrumentPerIns)
                {
                    freq = _bblFreq[bblId] / _bblInfo[bblId].size();
                }
                icount += freq;
                histogram.Add(insInfo.dataType, insInfo.simdWidth, insInfo.opcode, freq);
            }
        }
    }
    return icount;
}

uint64_t OpcodeprofKernelProfile::AddStaticCountersTo(OpcodeprofHistogram& histogram) const
{
    uint64_t icount = 0;
    for (const auto& bblInstructions: _bblInfo)
    {
        for (const auto& insInfo: bblInstructions)
        {
            ++icount;
            histogram.Add(insInfo.dataType, insInfo.simdWidth, insInfo.opcode, 1);
        }
    }
    return icount;
}

/* ============================================================================================= */
// Dump results utilities implementation
/* ============================================================================================= */
void DumpProfile(const std::map<GtKernelId, OpcodeprofKernelProfile>& kernels)
{
    std::ostringstream os;
    std::string profileDir = GTPin_GetCore()->ProfileDir();

    // Dynamic insruction counters of all kernels
    OpcodeprofHistogram totalDynamicHistogram;
    uint64_t    totalDynamicIcount = 0; // Total number of executed instructions in all kernels
    std::string totalAsmText;           // Assembly texts of all kernels
    uint32_t    numKernels  = 0;        // Number of executed kernels

    // Dump per-kernel profile data and assembly text
    for (auto& k : kernels)
    {
        const OpcodeprofKernelProfile& kernel = k.second;

        // Dynamic insruction counters of the current kernel
        OpcodeprofHistogram dynamicHistogram;
        uint64_t dynamicIcount = kernel.AddDynamicCountersTo(dynamicHistogram);
        if (dynamicIcount == 0)
        {
            continue;   // This kernel was not executed
        }
        std::string asmText = kernel.GetAsmWithCounters(); // Assembly text of the current kernel

        ++numKernels;
        totalDynamicIcount     += dynamicIcount;
        totalDynamicHistogram  += dynamicHistogram;
        totalAsmText           += asmText;

        if (!knobTotalOnly)
        {
            // Static insruction counters of the current kernel
            OpcodeprofHistogram staticHistogram;
            uint64_t staticIcount = kernel.AddStaticCountersTo(staticHistogram);

            std::string   dir = MakeSubDirectory(profileDir, kernel.GetUniqueName());
            std::ofstream fs(JoinPath(dir, "opcodeprof__total.txt"));
            if (fs.is_open())
            {
                fs << "DYNAMIC OPCODE HISTOGRAMS PER EXECUTION DATA TYPES" << std::endl
                    << "==================================================" << std::endl << std::endl;

                fs << dynamicHistogram.ToString("OPCODE Report :  Opcode  SIMD         Static (%)            Dynamic (%)",
                                                &staticHistogram);
                fs << "// kernel name:    " << kernel.GetName() << std::endl << std::endl;
                fs << "Static  instruction count = " << std::dec << staticIcount  << std::endl;
                fs << "Dynamic instruction count = " << std::dec << dynamicIcount << std::endl;
                fs << std::endl << std::endl << asmText;
            }
        }
    }

    // Dump total profile data and assembly texts for all kernels
    std::ofstream fs(JoinPath(profileDir, "opcodeprof_total.txt"));
    if (fs.is_open())
    {
        fs << "Total number of kernels:      " << std::dec << numKernels << std::endl;
        fs << "Total number of instructions: " << std::dec << totalDynamicIcount << std::endl << std::endl;
        fs << "DYNAMIC OPCODE HISTOGRAMS PER EXECUTION DATA TYPES" << std::endl
            << "==================================================" << std::endl << std::endl;

        fs << totalDynamicHistogram.ToString("OPCODE Report :  Opcode  SIMD        Dynamic (%)");
        fs << std::endl << std::endl << totalAsmText;
    }

    // Aggregated total time of all kernel executions
    double totalTime = 0;
    for (auto& k : kernels)
    {
        const OpcodeprofKernelProfile& kernel = k.second;
        totalTime += kernel.GetElapsedTime();
    }
    std::cout << "Total kernel run time (sec): " << totalTime << std::endl;

    // print total number of instructions
    std::cout << "Total number of counted instructions: " << totalDynamicIcount << std::endl;

}

void DumpAsm(const std::map<GtKernelId, OpcodeprofKernelProfile>& kernels)
{
    for (auto& kernel : kernels)
    {
        kernel.second.DumpAsm();
    }
}
