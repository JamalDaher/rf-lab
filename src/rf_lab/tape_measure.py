"""Tape-measure Yagi construction planning (heuristic, not EM validated)."""
import math
from rf_lab.yagi import design_yagi
from rf_lab.construction import construction_plan

MOUNT_OPTIONS = {
    "PVC cross fittings": "Three PVC cross fittings on a nonconductive boom; secure flexible tape safely.",
    "Insulated brackets": "Nonconductive brackets with rounded clamps and strain relief for each tape blade.",
}
STEPS = (
    "Wear gloves and eye protection; steel tape blades have sharp edges and spring-back risk.",
    "Cut four tape-blade pieces with extra trimming allowance; deburr and round sharp ends.",
    "Mark reflector, driven and director centerlines from the boom's physical end.",
    "Dry-fit three insulated mounts and mechanically restrain each flexible blade.",
    "Mount two driven arms symmetrically with a controlled feed gap; avoid shorts through hardware.",
    "Fit coax, strain relief and a matching/balun arrangement selected from measured impedance.",
    "Check continuity and isolation, and keep the assembly well clear of overhead power lines.",
    "Measure resonance and SWR at low power; trim in small symmetric increments and log results.",
    "Weatherproof connections and verify secure mounting before field use.",
)

def tape_measure_plan(frequency_mhz=146.0, feed_gap_mm=12.0,
                      trim_allowance_mm=10.0, boom_end_margin_mm=50.0,
                      tape_width_mm=25.0, mount="PVC cross fittings"):
    """Return a Yagi and an auditable tape-measure build packet.

    Tape width is informational only; it does not modify heuristic RF dimensions.
    The margin is added at both physical ends of the boom.
    """
    if mount not in MOUNT_OPTIONS:
        raise ValueError("Unknown mount option")
    for value, name, low, high in (
        (boom_end_margin_mm, "Boom end margin", 0, 500),
        (tape_width_mm, "Tape width", 5, 100),
    ):
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{name} outside supported range")
    design = design_yagi(frequency_mhz, feed_gap_mm)
    plan = construction_plan(design, trim_allowance_mm)
    plan["boom_stock_m"] = plan["boom_length_m"] + 2 * boom_end_margin_mm / 1000
    plan["boom_end_margin_mm"] = boom_end_margin_mm
    plan["tape_width_mm"] = tape_width_mm
    plan["mount"] = mount
    plan["positions_from_boom_end"] = [
        (name, position + boom_end_margin_mm / 1000)
        for name, position in plan["positions"]
    ]
    plan["total_tape_m"] = sum(
        cut["initial_cut_m"] * cut["quantity"] for cut in plan["cuts"]
    )
    plan["materials"] = [
        ("Steel tape blade", 4, f"{tape_width_mm:g} mm nominal width; "
         f"at least {plan['total_tape_m']:.2f} m before cutting waste"),
        ("Nonconductive PVC boom", 1,
         f"At least {plan['boom_stock_m']:.3f} m; verify stiffness"),
        ("Element mounting fittings", 3, MOUNT_OPTIONS[mount]),
        ("Insulated driven-element supports", 2, "Preserve feed gap"),
        ("Rounded clamps and fasteners", 1, "Prevent shorts and sharp edges"),
        ("Coax, connector and strain relief", 1, "Choose for operating frequency"),
        ("Feed matching or balun", 1, "Determine from actual impedance measurements"),
        ("Edge protection and weatherproofing", 1, "Protect blade ends and feedpoint"),
    ]
    plan["steps"] = STEPS
    return design, plan
