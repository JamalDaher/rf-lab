"""Portable, versioned Yagi design files and deterministic frequency sweeps.

No server-side persistence: users retain their JSON design files locally.
"""
import csv
import io
import json
import math
import zipfile
from .mom import solve_yagi_mom
from .nec2_runner import generate_yagi_nec2

SCHEMA="rf-lab-yagi-design"
MAX_FILE_BYTES=100_000

def validate_design(value):
    if isinstance(value,(str,bytes)):
        if len(value)>MAX_FILE_BYTES:
            raise ValueError("design exceeds upload size limit")
        value=json.loads(value,parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if not isinstance(value,dict) or value.get("schema")!=SCHEMA or value.get("version")!=1:
        raise ValueError("unsupported design format")
    name=value.get("name")
    if not isinstance(name,str) or not 1<=len(name.strip())<=80:
        raise ValueError("design name must contain 1–80 characters")
    freq=value.get("frequency_mhz")
    radius=value.get("wire_radius_mm")
    segments=value.get("segments_per_element")
    if any(type(x) not in (float,int) or not math.isfinite(x) for x in (freq,radius)):
        raise ValueError("invalid numeric design settings")
    if type(segments)!=int:
        raise ValueError("segments must be an integer")
    lengths=value.get("lengths_m")
    positions=value.get("positions_m")
    if not isinstance(lengths,list) or not isinstance(positions,list):
        raise ValueError("design geometry must be arrays")
    if len(lengths)!=3 or len(positions)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in lengths+positions):
        raise ValueError("invalid design geometry")
    generate_yagi_nec2(freq,lengths,positions,radius,segments)
    if abs(positions[0])>1e-9:
        raise ValueError("reflector position must be zero")
    return value

def make_design(name,frequency_mhz,lengths_m,positions_m,wire_radius_mm=2.0,segments_per_element=7):
    return validate_design({"schema":SCHEMA,"version":1,"name":name,
        "frequency_mhz":float(frequency_mhz),
        "lengths_m":[float(x) for x in lengths_m],
        "positions_m":[float(x) for x in positions_m],
        "wire_radius_mm":float(wire_radius_mm),
        "segments_per_element":int(segments_per_element)})

def design_json(design):
    return json.dumps(validate_design(design),indent=2,allow_nan=False)+"\n"

def compare_designs(designs):
    if not 1<=len(designs)<=5:
        raise ValueError("compare 1–5 designs")
    validated=[validate_design(d) for d in designs]
    if len({d["name"] for d in validated})!=len(validated):
        raise ValueError("design names must be unique")
    return [{"name":d["name"],"frequency_mhz":d["frequency_mhz"],
             "reflector_mm":round(d["lengths_m"][0]*1000,2),
             "driven_mm":round(d["lengths_m"][1]*1000,2),
             "director_mm":round(d["lengths_m"][2]*1000,2),
             "boom_mm":round(d["positions_m"][2]*1000,2)}
            for d in validated]

def frequency_sweep(design,start_mhz,stop_mhz,points=7):
    d=validate_design(design)
    if (type(points)!=int or not 2<=points<=21 or
        any(type(x) not in (int,float) or not math.isfinite(x) for x in (start_mhz,stop_mhz)) or
        not 0<start_mhz<stop_mhz<=3000):
        raise ValueError("invalid sweep range or point count")
    rows=[]
    for i in range(points):
        freq=start_mhz+(stop_mhz-start_mhz)*i/(points-1)
        result=solve_yagi_mom(freq,d["lengths_m"],d["positions_m"],
            wire_radius_mm=d["wire_radius_mm"],segments_per_element=d["segments_per_element"])
        rows.append({"frequency_mhz":round(freq,6),
                     "resistance_ohm":float(result.feed_impedance_ohm.real),
                     "reactance_ohm":float(result.feed_impedance_ohm.imag),
                     "swr_50":float(result.swr_50)})
    return rows

def package_design(design,sweep=None):
    d=validate_design(design)
    if sweep is None:
        sweep=[]
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("design.json",design_json(d))
        z.writestr("model.nec",generate_yagi_nec2(d["frequency_mhz"],
            d["lengths_m"],d["positions_m"],d["wire_radius_mm"],d["segments_per_element"]))
        stream=io.StringIO()
        writer=csv.DictWriter(stream,fieldnames=["element","length_mm","boom_position_mm"])
        writer.writeheader()
        for label,length,position in zip(("Reflector","Driven","Director"),
                                           d["lengths_m"],d["positions_m"]):
            writer.writerow({"element":label,"length_mm":round(length*1000,2),
                             "boom_position_mm":round(position*1000,2)})
        z.writestr("dimensions.csv",stream.getvalue())
        if sweep:
            stream=io.StringIO()
            writer=csv.DictWriter(stream,fieldnames=["frequency_mhz","resistance_ohm","reactance_ohm","swr_50"])
            writer.writeheader()
            writer.writerows(sweep)
            z.writestr("frequency_sweep.csv",stream.getvalue())
        z.writestr("LIMITATIONS.txt","Experimental EFIE estimates are not validated antenna performance. Verify NEC and measured data before construction.\n")
    return output.getvalue()
