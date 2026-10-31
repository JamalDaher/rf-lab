import copy
import hashlib
import json
import pytest
from rf_lab.benchmark_reports import validate_summary,compare_summaries,verify_artifacts
from rf_lab.benchmark_pdf import build_pdf

def example():
    cases=[]
    for mesh in (7,9):
        nec=complex(50+mesh,4)
        efie=complex(45+mesh,5)
        deck=f"deck-{mesh}".encode()
        output=f"output-{mesh}".encode()
        cases.append({"segments_per_element":mesh,
                      "nec_real_ohm":nec.real,"nec_imag_ohm":nec.imag,
                      "efie_real_ohm":efie.real,"efie_imag_ohm":efie.imag,
                      "absolute_error_ohm":abs(efie-nec),
                      "relative_error":abs(efie-nec)/abs(nec),
                      "deck_sha256":hashlib.sha256(deck).hexdigest(),
                      "output_sha256":hashlib.sha256(output).hexdigest()})
    return {"kind":"rf-lab-nec2c-mesh-benchmark","schema_version":1,
            "solver_version":"test build","frequency_mhz":146,
            "wire_radius_mm":2,"lengths_m":[1,.9,.8],
            "positions_m":[0,.2,.4],"mesh_sizes":[7,9],"cases":cases,
            "caveats":["Not validated"]}

def test_validation_and_pdf():
    summary=example()
    assert validate_summary(json.dumps(summary))["mesh_sizes"]==[7,9]
    pdf=build_pdf(summary)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf)>1000

def test_historical_comparison_and_pdf():
    old=example()
    new=copy.deepcopy(old)
    new["solver_version"]="new"
    result=compare_summaries(old,new)
    assert result["changes"][0]["impedance_error_change_ohm"]==0
    assert build_pdf(new,old).startswith(b"%PDF-")

def test_reject_incompatible_history():
    old=example()
    new=copy.deepcopy(old)
    new["frequency_mhz"]=147
    with pytest.raises(ValueError,match="incompatible"):
        compare_summaries(old,new)

@pytest.mark.parametrize("change",[
    lambda x:x.update(mesh_sizes=[9,7]),
    lambda x:x["cases"][0].update(absolute_error_ohm=99),
    lambda x:x["cases"][0].update(deck_sha256="fake"),
    lambda x:x["cases"][0].update(nec_real_ohm=float("nan")),
    lambda x:x.update(solver_version=""),
])
def test_reject_malformed_summary(change):
    x=example()
    change(x)
    with pytest.raises(ValueError):
        validate_summary(x)

def test_verify_real_bytes_not_just_claimed_hashes():
    x=example()
    files={}
    for mesh in (7,9):
        files[f"mesh-{mesh:02d}/model.nec"]=f"deck-{mesh}".encode()
        files[f"mesh-{mesh:02d}/solver-output.txt"]=f"output-{mesh}".encode()
    assert verify_artifacts(x,files)["all_verified"]
    files["mesh-07/model.nec"]=b"tampered"
    assert not verify_artifacts(x,files)["all_verified"]

def test_json_rejects_nonfinite_constants():
    with pytest.raises(ValueError):
        validate_summary('{"schema_version":1,"kind":"rf-lab-nec2c-mesh-benchmark","x":NaN}')
