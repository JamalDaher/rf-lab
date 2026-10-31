# Three-element tape-measure Yagi designer

The v0.2.0 Yagi module generates **approximate starting geometry**, not a
validated construction plan or numerical electromagnetic simulation.

## Parameters

- Frequency: MHz, positive finite value (presets: 146 MHz and 435 MHz)
- Feed gap: mm, positive and shorter than the driven element
- Speed of light: 299,792,458 m/s
- Wavelength: speed of light / frequency in Hz

## Heuristic dimensions

| Element | Length / wavelength | Boom position / wavelength |
|---|---:|---:|
| Reflector | 0.505 | 0.00 |
| Driven | 0.475 | 0.20 |
| Director | 0.450 | 0.35 |

The driven element is split into two arms separated by the chosen feed gap:
each arm = (total driven length - feed gap) / 2.

Boom length is the distance from reflector center to director center, **not**
the physical stock length needed for clamps, mounting, or end margins.

## Important construction limitations

These are illustrative free-space ratios, **not calibrated tape-measure
antenna dimensions**. Flexible tape material, element width, boom dielectric,
mounting hardware, feed gap, nearby objects, and the matching network change
resonance and impedance. The application does not calculate SWR, forward gain,
front-to-back ratio, pattern, bandwidth, or safe transmit power for this Yagi.

Start with extra stock and tune with an antenna analyzer at low power before
transmitting. A split driven element typically needs a suitable feed/matching
arrangement and common-mode control. Keep antenna elements clear of overhead
power lines; avoid mounting near energized conductors.

## Export

The dashboard exports a CSV cutting list with inches and centimeters. Use the
boom diagram for relative placement, not a full-size fabrication template.
