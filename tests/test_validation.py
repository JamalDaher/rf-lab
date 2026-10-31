import math
import pytest
from rf_lab.validation import short_dipole_directivity_check, mesh_sensitivity


def test_short_dipole_analytical_integral():
    check = short_dipole_directivity_check()
    assert abs(check["numerical_linear"]-1.5) < 0.0001
    assert abs(check["reference_dbi"]-1.76091259056) < 1e-8


def test_integration_resolution_improves():
    coarse = short_dipole_directivity_check(21)
    fine = short_dipole_directivity_check(721)
    assert fine["absolute_error"] < coarse["absolute_error"]


def test_mesh_report_and_changes():
    wavelength = 299792458/(146e6)
    lengths=[.505*wavelength,.475*wavelength,.45*wavelength]
    positions=[0,.2*wavelength,.35*wavelength]
    report=mesh_sensitivity(146,lengths,positions,meshes=(5,7))
    assert len(report.rows)==2
    assert report.rows[0].relative_impedance_change is None
    assert report.rows[1].relative_impedance_change is not None
    assert math.isfinite(report.max_relative_impedance_change)
    assert "NOT physical validation" in report.warning


@pytest.mark.parametrize("meshes",[(5,), (5,5), (7,5), ()])
def test_invalid_meshes(meshes):
    with pytest.raises(ValueError):
        mesh_sensitivity(146,[1,1,1],[0,.4,.8],meshes=meshes)


def test_invalid_analytical_sample_count():
    with pytest.raises(ValueError):
        short_dipole_directivity_check(10)
