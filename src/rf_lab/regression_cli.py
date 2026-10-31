"""Compare actual NEC-2c benchmark outputs against a reviewed baseline."""
import argparse
import json
from pathlib import Path
from .benchmark_reports import validate_summary
from .benchmark_regression import check_regression,result_json

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",required=True)
    p.add_argument("--candidate",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--max-nec-delta",type=float,default=0.5)
    p.add_argument("--max-efie-delta",type=float,default=0.5)
    p.add_argument("--max-error-delta",type=float,default=0.5)
    args=p.parse_args(argv)
    limits={"max_nec_impedance_delta_ohm":args.max_nec_delta,
            "max_efie_impedance_delta_ohm":args.max_efie_delta,
            "max_absolute_error_delta_ohm":args.max_error_delta}
    baseline=validate_summary(Path(args.baseline).read_bytes())
    candidate=validate_summary(Path(args.candidate).read_bytes())
    result=check_regression(baseline,candidate,limits)
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(result_json(result),encoding="utf-8")
    print("Numerical regression:", "PASS" if result["passed"] else "FAIL")
    for row in result["cases"]:
        print(f"mesh {row['segments_per_element']}: {'PASS' if row['passed'] else 'FAIL'}")
    print("Physical accuracy remains UNVALIDATED")
    return 0 if result["passed"] else 1

if __name__=="__main__":
    raise SystemExit(main())
