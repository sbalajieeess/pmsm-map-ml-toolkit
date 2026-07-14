# Sign and coordinate conventions

- `Id` is negative for field weakening in the accepted motor convention.
- `Iq` is positive for positive motoring operation.
- `torque_Nm` in the canonical map is positive for positive motoring, regardless of a
  solver's internal torque sign.
- Currents and flux-linkage fields use RMS values unless a column explicitly says peak.
- Mechanical skew angles must not be confused with electrical current angle.

Solver adapters are responsible for converting raw outputs into this convention before
exporting the canonical map.
