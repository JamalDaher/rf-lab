"""Run local NEC-2c benchmarks and compare against a reviewed baseline."""
import argparse
from pathlib import Path
from .benchmark_suite import run_suite,write_suite
from .benchmark_pdf import build_pdf
from .benchmark_reports import validate_summary
from .benchmark_regression import check_regression,result_json

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",required=True)
    p.add_argument("--output-dir",required=True)
    p.add_argument("--executable",default="nec2c")
    p.add_argument("--solver-version",required=True)
    p.add_argument("--max-nec-delta",type=float,default=0.5)
    p.add_argument("--max-efie-delta",type=float,default=0.5)
    p.add_argument("--max-error-delta",type=float,default=0.5)
    args=p.parse_args(argv)
    baseline=validate_summary(Path(args.baseline).read_bytes())
    current=run_suite(baseline["frequency_mhz"],baseline["lengths_m"],
                      baseline["positions_m"],args.executable,args.solver_version,
                      meshes=tuple(baseline["mesh_sizes"]),
                      wire_radius_mm=baseline["wire_radius_mm"],adapter="nec2c")
    destination=write_suite(current,args.output_dir)
    (destination/"benchmark-report.pdf").write_bytes(build_pdf(current.summary,baseline))
    limits={"max_nec_impedance_delta_ohm":args.max_nec_delta,
            "max_efie_impedance_delta_ohm":args.max_efie_delta,
            "max_absolute_error_delta_ohm":args.max_error_delta}
    result=check_regression(baseline,current.summary,limits)
    (destination/"regression.json").write_text(result_json(result),encoding="utf-8")
    print("Numerical regression:", "PASS" if result["passed"] else "FAIL")
    print("Saved comparison artifacts to",destination)
    return 0 if result["passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
