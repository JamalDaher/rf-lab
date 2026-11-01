"""Regression tests for SDR signal laboratory."""
import numpy as np
import pytest
from rf_lab.sdr_lab import constellation,simulate,iq_spectrum,waterfall,read_iq_bytes

@pytest.mark.parametrize("mod,bits", [("BPSK",1),("QPSK",2),("16-QAM",4)])
def test_constellation_and_clean_channel(mod,bits):
    points=constellation(mod)
    assert len(points)==2**bits
    assert np.mean(abs(points)**2)==pytest.approx(1)
    result=simulate(mod,2048,40)
    assert result["ber"]==0
    assert result["ser"]==0
    assert result["evm_percent"]<2

def test_seed_is_reproducible_and_noise_impacts_errors():
    a=simulate("QPSK",2048,10)
    b=simulate("QPSK",2048,10)
    assert np.array_equal(a["received"],b["received"])
    assert simulate("QPSK",2048,-10)["ber"]>0

def test_complex_fft_peak():
    n=1024
    samples=np.exp(2j*np.pi*128*np.arange(n)/1024)
    f,db=iq_spectrum(samples,1024)
    assert f[np.argmax(db)]==pytest.approx(128)

def test_waterfall_dimensions():
    x=np.exp(2j*np.pi*100*np.arange(2048)/2048)
    t,f,z=waterfall(x,2048,256,128)
    assert z.shape==(len(f),len(t))
    assert np.all(np.isfinite(z))

def test_complex64_import_roundtrip():
    samples=np.arange(128,dtype=np.float32).reshape(64,2)
    result=read_iq_bytes(samples.astype("<f4").tobytes(),"complex64")
    assert np.array_equal(result.real,samples[:,0])
    assert np.array_equal(result.imag,samples[:,1])

def test_cs8_import():
    raw=np.array([127,-128]*64,dtype=np.int8).tobytes()
    samples=read_iq_bytes(raw,"cs8")
    assert np.all(samples.real==127/128)
    assert np.all(samples.imag==-1)

@pytest.mark.parametrize("data,fmt",[
    (b"123","complex64"),(b"123","cs8"),
    (b"x"*524289,"cs8"),(b"","cs8"),
    (b"12345678","unknown")])
def test_invalid_iq_rejected(data,fmt):
    with pytest.raises(ValueError):
        read_iq_bytes(data,fmt)

def test_invalid_modulation_and_parameters():
    with pytest.raises(ValueError):
        constellation("8-PSK")
    with pytest.raises(ValueError):
        simulate(symbols=100000)
    with pytest.raises(ValueError):
        simulate(snr_db=float("nan"))
