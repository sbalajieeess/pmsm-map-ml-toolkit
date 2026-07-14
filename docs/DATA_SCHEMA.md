# Canonical data schema

The canonical map is the contract between a solver repository and the shared toolkit.

## Required columns

| Column | Meaning |
|---|---|
| `case_id` | Stable operating-point identifier |
| `source_solver` | `FEMM` or `ELMER2D` |
| `geometry_id` | Versioned geometry identifier |
| `temperature_C` | Model temperature |
| `id_RMS_A`, `iq_RMS_A` | RMS dq currents |
| `torque_Nm` | Positive motoring torque magnitude |
| `psiD_Wb`, `psiQ_Wb` | RMS dq flux linkages |
| `converged` | Solver/result acceptance flag |

Recommended optional fields include slice count or ID, Ld/Lq, Bmax, iteration count,
runtime, and input/config hashes. The JSON schema in `schemas/truth_map_v1.schema.json`
is the machine-readable reference.
