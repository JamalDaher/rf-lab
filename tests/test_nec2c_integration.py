"""Real nec2c integration smoke test; run only with installed executable.

This tests genuine execution and captures actual output. It does not assert
physical accuracy or silently replace a failed parser with mock numbers.
"""
import shutil
import pytest
from rf_lab.nec2_runner import generate_yagi_nec2
from rf_lab.nec2c_adapter import run_nec2c

@pytest.mark.skipif(shutil.which("nec2c") is None,reason="nec2c not installed")
def test_real_nec2c_executes_yagi():
    wavelength=299792458/146e6
    deck=generate_yagi_nec2(146,[.505*wavelength,.475*wavelength,.45*wavelength],
                            [0,.2*wavelength,.35*wavelength])
    result=run_nec2c(deck,"nec2c",timeout_seconds=60)
    assert result.returncode==0, result.output[-3000:]
    assert "ANTENNA INPUT PARAMETERS" in result.output.upper()
    assert len(result.output)>100

def test_missing_nec2c_fails_clearly():
    with pytest.raises(ValueError,match="not installed"):
        run_nec2c("EN\n","/nonexistent/rf-lab-nec2c-binary")
