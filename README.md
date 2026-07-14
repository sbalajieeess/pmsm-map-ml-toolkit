# PMSM Map and ML Toolkit

Solver-independent support pipeline shared by:

- `pmsm-femm-to-tinyml`
- `pmsm-elmer2d-gmsh-to-tinyml`

Both solvers must export the same canonical truth-map CSV. From that boundary onward this
repository performs schema validation, map-quality checks, common visualizations,
MTPA/MTPV-style operating-point selection, controller-dataset creation, float neural-network
training, magnitude pruning, symmetric int8 quantization, and C-header export.

## Local installation on Windows

```powershell
cd D:\FEM_PMSM\GitHub\pmsm-map-ml-toolkit
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[ml,dev]"
pytest
```

## Canonical boundary

```text
FEMM truth map  ─┐
                 ├─> canonical truth_map_v1.csv ─> visualization / optimizer / NN / pruning
Elmer truth map ─┘
```

Validate and visualize the included example:

```powershell
pmsm-map-validate --input examples\truth_map_example.csv --report outputs\validation.json
pmsm-map-visualize --input examples\truth_map_example.csv --output-dir outputs\plots
```

See `docs/DATA_SCHEMA.md`, `docs/SIGN_CONVENTIONS.md`, and
`docs/PIPELINE_BOUNDARY.md` before connecting a solver repository.
