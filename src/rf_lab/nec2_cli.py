"""Run a local NEC-2 comparison and save traceable artifacts.

Example:
python -m rf_lab.nec2_cli --executable /usr/local/bin/nec2++ \\
  --solver-version "locally verified build" --output-dir ./nec-results

The solver must accept an input filename as its first argument.
"""
import argparse
from pathlib import Path
from .nec2_pipeline import run_benchmark, report_json

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--adapter",choices=["generic","nec2c"],default="nec2c")
    p.add_argument("--executable",required=True,
                   help="Trusted local NEC-2 executable (never an uploaded binary)")
    p.add_argument("--solver-version",required=True)
    p.add_argument("--output-dir",required=True)
    p.add_argument("--frequency-mhz",type=float,default=146.0)
    p.add_argument("--segments",type=int,default=9)
    p.add_argument("--radius-mm",type=float,default=2.0)
    p.add_argument("--timeout",type=int,default=30)
    args=p.parse_args(argv)
    wavelength=299792458/(args.frequency_mhz*1e6)
    lengths=[.505*wavelength,.475*wavelength,.45*wavelength]
    positions=[0,.2*wavelength,.35*wavelength]
    result=run_benchmark(args.frequency_mhz,lengths,positions,args.executable,
                         args.solver_version,wire_radius_mm=args.radius_mm,
                         segments_per_element=args.segments,
                         timeout_seconds=args.timeout,adapter=args.adapter)
    destination=Path(args.output_dir)
    destination.mkdir(parents=True,exist_ok=True)
    (destination/"model.nec").write_text(result.deck,encoding="utf-8")
    (destination/"solver-output.txt").write_text(result.raw_output,encoding="utf-8")
    (destination/"comparison.json").write_text(report_json(result),encoding="utf-8")
    print(f"Saved NEC comparison artifacts to {destination.resolve()}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
