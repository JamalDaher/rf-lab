"""Generate NEC-2 input decks and run a locally installed compatible solver.

Never run untrusted executables from uploads. Executable must be configured
by the operator and is not available on Streamlit Community Cloud by default.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import re
import subprocess
import tempfile

@dataclass(frozen=True)
class NEC2Run:
    deck: str
    output: str
    returncode: int

def generate_yagi_nec2(frequency_mhz, lengths_m, positions_m,
                       wire_radius_mm=2.0, segments_per_element=9):
    """Create free-space z-wire Yagi with center-segment voltage excitation.

    NOTE: NEC wire geometry/excitation may differ from RF Lab EFIE feed model.
    """
    lengths=tuple(float(x) for x in lengths_m)
    positions=tuple(float(x) for x in positions_m)
    if (len(lengths)!=3 or len(positions)!=3 or
        not all(math.isfinite(x) for x in lengths+positions) or
        not all(x>0 for x in lengths) or
        not positions[0]<positions[1]<positions[2]):
        raise ValueError("invalid Yagi geometry")
    if (not math.isfinite(frequency_mhz) or frequency_mhz<=0 or
        not math.isfinite(wire_radius_mm) or wire_radius_mm<=0 or
        wire_radius_mm/1000>=min(lengths)/10):
        raise ValueError("invalid frequency or wire radius")
    if (isinstance(segments_per_element,bool) or
        not isinstance(segments_per_element,int) or
        segments_per_element<5 or segments_per_element>31 or
        segments_per_element%2!=1):
        raise ValueError("segments must be odd, 5..31")
    r=wire_radius_mm/1000
    lines=["CM RF Lab NEC-2 free-space Yagi reference deck",
           "CM Verify geometry and excitation conventions before comparison",
           "CE"]
    for i,(length,x) in enumerate(zip(lengths,positions),1):
        lines.append(f"GW {i} {segments_per_element} {x:.9f} 0 {-length/2:.9f} "
                     f"{x:.9f} 0 {length/2:.9f} {r:.9f}")
    lines.extend(["GE 0",
                  "GN -1",
                  f"EX 0 2 {(segments_per_element+1)//2} 0 1 0",
                  f"FR 0 1 0 0 {frequency_mhz:.9f} 0",
                  "RP 0 91 181 1000 0 0 2 2",
                  "EN"])
    return "\n".join(lines)+"\n"

def parse_nec2_input_impedance(output):
    """Extract NEC input impedance from common NEC-2 INPUT PARAMETERS table.

    Explicitly fail on absent/ambiguous formats instead of inventing values.
    """
    marker="ANTENNA INPUT PARAMETERS"
    if marker not in output.upper():
        raise ValueError("NEC input-parameters section not found")
    section=output.upper().split(marker)[-1]
    # NEC-2 standard table includes a line starting with TAG SEG VOLTAGE ...
    # and a row of numeric values: TAG SEG Vreal Vimag Ireal Iimag Zreal Zimag ...
    lines=section.splitlines()
    for i,line in enumerate(lines):
        if "IMPEDANCE" in line and "RESISTANCE" not in line:
            for candidate in lines[i+1:i+8]:
                nums=re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?",candidate)
                if len(nums)>=8 and nums[0].isdigit() and nums[1].isdigit():
                    return complex(float(nums[6]),float(nums[7]))
    raise ValueError("NEC impedance table format not recognized; inspect raw output")

def run_nec2(deck, executable, timeout_seconds=30):
    """Execute trusted locally configured NEC binary using file arguments only."""
    exe=Path(executable)
    if not exe.is_file() or not exe.exists():
        raise ValueError("configured NEC executable does not exist")
    if not 1<=timeout_seconds<=120:
        raise ValueError("timeout must be between 1 and 120 seconds")
    with tempfile.TemporaryDirectory(prefix="rf-lab-nec-") as temp:
        input_file=Path(temp)/"model.nec"
        output_file=Path(temp)/"model.out"
        input_file.write_text(deck,encoding="utf-8")
        # Many command-line NEC-2 builds accept an input path; CLI variants
        # may require an adapter. No shell is used.
        result=subprocess.run([str(exe.resolve()),str(input_file)],
                              cwd=temp,capture_output=True,text=True,
                              timeout=timeout_seconds,check=False)
        output=output_file.read_text(errors="replace") if output_file.exists() else result.stdout
        return NEC2Run(deck,output,result.returncode)
