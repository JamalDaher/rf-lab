"""Adapter for the documented nec2c -i/-o command line.

See https://manpages.ubuntu.com/manpages/bionic/man1/nec2c.1.html
"""
from pathlib import Path
import subprocess
import tempfile

from .nec2_runner import NEC2Run

def run_nec2c(deck: str, executable: str="nec2c", timeout_seconds: int=30) -> NEC2Run:
    if not isinstance(deck,str) or not deck.strip() or len(deck)>100_000:
        raise ValueError("deck must be a nonempty bounded text input")
    if not isinstance(timeout_seconds,int) or not 1<=timeout_seconds<=120:
        raise ValueError("timeout must be 1..120 seconds")
    if not isinstance(executable,str) or not executable.strip():
        raise ValueError("executable must be a configured trusted command")
    with tempfile.TemporaryDirectory(prefix="rf-lab-nec2c-") as folder:
        source=Path(folder)/"model.nec"
        target=Path(folder)/"model.out"
        source.write_text(deck,encoding="utf-8")
        # nec2c supports -i<file> -o<file>. Never invoke a shell.
        try:
            process=subprocess.run([executable,"-i"+str(source),"-o"+str(target)],
                                   cwd=folder,capture_output=True,text=True,
                                   timeout=timeout_seconds,check=False)
        except FileNotFoundError as exc:
            raise ValueError("nec2c executable not installed or not found") from exc
        output=target.read_text(encoding="utf-8",errors="replace") if target.exists() else process.stdout
        return NEC2Run(deck,output,process.returncode)
