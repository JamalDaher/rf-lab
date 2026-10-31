"""Run reproducible local NEC-2c mesh sensitivity benchmarks."""
import argparse
from .benchmark_suite import run_suite,write_suite

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable",default="nec2c")
    parser.add_argument("--adapter",choices=("nec2c","generic"),default="nec2c")
    parser.add_argument("--solver-version",required=True)
    parser.add_argument("--frequency-mhz",type=float,default=146.0)
    parser.add_argument("--radius-mm",type=float,default=2.0)
    parser.add_argument("--meshes",type=int,nargs="+",default=[7,9,11,13])
    parser.add_argument("--timeout",type=int,default=30)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args(argv)
    wavelength=299792458/(args.frequency_mhz*1e6)
    suite=run_suite(args.frequency_mhz,
                    [.505*wavelength,.475*wavelength,.45*wavelength],
                    [0,.2*wavelength,.35*wavelength],
                    args.executable,args.solver_version,
                    meshes=args.meshes,wire_radius_mm=args.radius_mm,
                    timeout_seconds=args.timeout,adapter=args.adapter)
    destination=write_suite(suite,args.output_dir)
    print(f"Saved {len(suite.cases)} verified-execution benchmark cases to {destination}")
    print("Physical accuracy status: UNVALIDATED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
