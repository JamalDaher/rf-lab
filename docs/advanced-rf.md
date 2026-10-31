# Advanced RF calculations (v0.3.0)

## Smith chart

The impedance Smith chart uses the complex voltage reflection coefficient

`Γ = (ZL - Z0) / (ZL + Z0)`

for passive complex load `ZL = R + jX` and real positive reference `Z0`.
The plotted point is `(Re Γ, Im Γ)`. The unit circle is the passive-load
boundary. The chart is a reflection-coefficient visualization, **not** a
numerical antenna solver.

## Coax loss

The application uses approximate, illustrative loss figures at 100 MHz:

| Cable | dB per 100 ft at 100 MHz |
|---|---:|
| RG-58 | 4.9 |
| RG-8X | 3.9 |
| RG-213 | 2.2 |
| LMR-400 | 1.5 |

Loss is estimated as `loss_100MHz * sqrt(f_MHz / 100) * length_ft / 100`.
This simple model ignores dielectric-loss frequency dependence, connectors,
VSWR mismatch, temperature and manufacturing differences. It is **not** a
manufacturer datasheet and is not suitable for precision link budgets.

Matched-line output power is `Pout = Pin * 10^(-loss_dB/10)`. For significant
mismatch, this is not the delivered power at the actual antenna.

## L-network matching

The calculator solves **ideal lossless L-networks for unequal positive real
source and load impedances**. It provides two solutions (opposite reactive
signs) and identifies whether the shunt branch belongs on the source or load
side. For equal resistances, no matching network is required.

Series inductance: `L = X / (2πf)` for `X > 0`.
Series capacitance: `C = -1 / (2πf X)` for `X < 0`.
Shunt capacitance: `C = B / (2πf)` for `B > 0`.
Shunt inductance: `L = -1 / (2πf B)` for `B < 0`.

The tool does not solve complex loads, component Q, parasitics, power handling,
harmonics, or bandwidth. Verify designs with simulation and a VNA before
using them with a transmitter.
