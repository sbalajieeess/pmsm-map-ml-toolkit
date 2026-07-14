# PMSM Public Repository Usage Guide

Date: 2026-07-14

This guide explains how to use the public PMSM repositories:

1. `pmsm-map-ml-toolkit`
2. `pmsm-femm-to-tinyml`
3. `pmsm-elmer2d-gmsh-to-tinyml`

The private Elmer 3D validation handover is maintained separately and is not
required for normal public FEMM or Elmer2D-to-TinyML workflows.

## Repository Roles

| Repository | Purpose |
|---|---|
| `pmsm-map-ml-toolkit` | Shared canonical truth-map validation, visualization, controller-dataset generation, neural-network training, pruning, quantization, and C-header export. |
| `pmsm-femm-to-tinyml` | FEMM model execution, four-skew postprocessing, and FEMM-to-canonical truth-map export. |
| `pmsm-elmer2d-gmsh-to-tinyml` | Gmsh/Elmer2D intake baseline, three-stream scheduling, log parsing, and Elmer2D-to-canonical truth-map export. |

## Architecture

```text
FEMM repository
  -> FEMM-specific raw solving and postprocessing
  -> canonical truth_map_v1.csv
  -> shared toolkit

Elmer2D repository
  -> Gmsh/Elmer2D-specific logs, maps, and postprocessing
  -> canonical truth_map_v1.csv
  -> shared toolkit

Shared toolkit
  -> validation
  -> plots
  -> controller-dataset generation
  -> neural-network training
  -> pruning
  -> quantization
  -> C-header export
```

The central rule is:

```text
Solver-specific repositories stop at the canonical truth-map boundary.
The toolkit owns everything after that boundary.
```

## Recommended Local Layout

```text
D:\FEM_PMSM\GitHub\
  pmsm-map-ml-toolkit\
  pmsm-femm-to-tinyml\
  pmsm-elmer2d-gmsh-to-tinyml\
```

Keep large solver outputs outside the Git repositories. Use `runs` for local
working outputs, and promote only small curated examples or reference summaries
into Git.

## Common Python Setup

Use one virtual environment per repository:

```powershell
cd D:\FEM_PMSM\GitHub\REPOSITORY_NAME
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

For development checks, each repository supports editable installs:

```powershell
pip install -e ".[dev]"
```

For the toolkit neural-network path, install ML extras:

```powershell
pip install -e ".[dev,ml]"
```

## Shared Toolkit

Repository:

```text
https://github.com/sbalajieeess/pmsm-map-ml-toolkit
```

Install:

```powershell
cd D:\FEM_PMSM\GitHub\pmsm-map-ml-toolkit
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,ml]"
```

Check:

```powershell
pytest
ruff check .
python -m build
```

Validate the included truth-map example:

```powershell
pmsm-map-validate `
  --input examples\truth_map_example.csv `
  --report outputs\validation_report.json
```

Generate plots:

```powershell
pmsm-map-visualize `
  --input examples\truth_map_example.csv `
  --output-dir outputs\plots
```

Build a controller dataset:

```powershell
pmsm-map-optimize `
  --input examples\truth_map_example.csv `
  --output outputs\controller_dataset.csv `
  --torques 5,10,20,30 `
  --speeds 500,1000,2000 `
  --vdc 400 `
  --temperatures 100
```

Train and export a small model:

```powershell
pmsm-nn-train `
  --dataset outputs\controller_dataset.csv `
  --model outputs\model_float.npz `
  --metrics outputs\train_metrics.json `
  --predictions outputs\predictions.csv `
  --hidden 8 `
  --seed 21

pmsm-nn-prune `
  --model outputs\model_float.npz `
  --dataset outputs\controller_dataset.csv `
  --output outputs\model_pruned.npz `
  --metrics outputs\prune_metrics.json `
  --sparsity 0.5

pmsm-nn-quantize `
  --model outputs\model_pruned.npz `
  --output outputs\model_int8.npz

pmsm-nn-export `
  --model outputs\model_int8.npz `
  --output outputs\pmsm_model.h
```

Tips:

- Install with `.[dev,ml]` when using neural-network training.
- Use the toolkit only after a solver repo exports canonical `truth_map_v1.csv`.
- The visualization CLI uses a headless plotting backend, so it works in normal
  shell and CI-style runs.
- Keep generated plots, datasets, models, and headers under `outputs` or `runs`.

## FEMM To TinyML

Repository:

```text
https://github.com/sbalajieeess/pmsm-femm-to-tinyml
```

Install:

```powershell
cd D:\FEM_PMSM\GitHub\pmsm-femm-to-tinyml
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pip install -e D:\FEM_PMSM\GitHub\pmsm-map-ml-toolkit
```

Optional FEMM support:

```powershell
pip install -e ".[windows]"
```

Check:

```powershell
pytest
ruff check .
python -m build
```

Check FEMM environment:

```powershell
python scripts\check_environment.py --config configs\one_eighth_100C.toml
```

Run FEMM smoke when FEMM and pyFEMM are installed:

```powershell
scripts\run_smoke_100C.cmd
```

Export a generated FEMM summary:

```powershell
python scripts\export_canonical_truth_map.py `
  --input runs\YOUR_RUN\summary.csv `
  --output runs\YOUR_RUN\femm_truth_map_v1.csv `
  --geometry-id oneEighth_reference_v1
```

Export the packaged historical reference map:

```powershell
python scripts\export_canonical_truth_map.py `
  --input reference\summaries\400V_100C_fea_map.csv `
  --output runs\reference_100C\femm_truth_map_v1.csv `
  --geometry-id oneEighth_reference_v1
```

Validate with the toolkit:

```powershell
pmsm-map-validate `
  --input runs\reference_100C\femm_truth_map_v1.csv `
  --report runs\reference_100C\validation_report.json
```

Tips:

- New team work should use `configs`, `scripts`, and `src`, not edit the archived
  `legacy/femm_skew` scripts.
- The archival `legacy/femm_skew` folder is excluded from full Ruff checks on
  purpose.
- Always run a small smoke map before a dense FEMM sweep.
- Keep raw FEMM outputs under `runs`; commit only curated examples, summaries, or
  reference artifacts.
- The historical reference-map exporter handles legacy column names and normalizes
  torque sign to positive motoring.

## Elmer2D/Gmsh To TinyML

Repository:

```text
https://github.com/sbalajieeess/pmsm-elmer2d-gmsh-to-tinyml
```

Install:

```powershell
cd D:\FEM_PMSM\GitHub\pmsm-elmer2d-gmsh-to-tinyml
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,vtu]"
pip install -e D:\FEM_PMSM\GitHub\pmsm-map-ml-toolkit
```

Check:

```powershell
pytest
ruff check .
python -m build
```

First project-machine intake step:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\collect_local_validated_assets.ps1
```

This copies candidate local Elmer/Gmsh assets into an intake-review area. It
does not delete or modify the original solver workspaces.

Run the three-stream scheduler:

```powershell
pmsm-elmer-run3 `
  --cases runs\YOUR_CASES.csv `
  --summary runs\YOUR_RUN\three_stream_summary.csv
```

Parse Elmer logs:

```powershell
pmsm-elmer-logs `
  --log-dir runs\YOUR_RUN\logs `
  --output runs\YOUR_RUN\log_summary.csv
```

Export an accepted Elmer map:

```powershell
pmsm-elmer-export `
  --input runs\YOUR_RUN\accepted_elmer_map.csv `
  --output runs\YOUR_RUN\elmer_truth_map_v1.csv `
  --geometry-id elmer2d_reference_v1
```

Validate with the toolkit:

```powershell
pmsm-map-validate `
  --input runs\YOUR_RUN\elmer_truth_map_v1.csv `
  --report runs\YOUR_RUN\validation_report.json
```

Tips:

- This repository is a controlled intake baseline. Do not treat collected local
  assets as accepted until reviewed.
- Large 2D sweeps use exactly three independent ElmerSolver streams.
- Do not switch to unvalidated MPI or a different stream count without a new
  validation note.
- Keep `.vtu`, `.pvtu`, mesh, scalar, and large result trees out of Git.
- Use `docs\LOCAL_WORKSPACE_INTAKE.md` before promoting any collected assets.

## End-To-End FEMM Flow

```text
FEMM model/results
  -> pmsm-femm-to-tinyml
  -> femm_truth_map_v1.csv
  -> pmsm-map-ml-toolkit
  -> plots, controller dataset, NN, pruning, quantization, C header
```

Minimal command flow:

```powershell
cd D:\FEM_PMSM\GitHub\pmsm-femm-to-tinyml
.\.venv\Scripts\Activate.ps1

python scripts\export_canonical_truth_map.py `
  --input reference\summaries\400V_100C_fea_map.csv `
  --output runs\reference_100C\femm_truth_map_v1.csv `
  --geometry-id oneEighth_reference_v1

pmsm-map-validate `
  --input runs\reference_100C\femm_truth_map_v1.csv `
  --report runs\reference_100C\validation_report.json

pmsm-map-visualize `
  --input runs\reference_100C\femm_truth_map_v1.csv `
  --output-dir runs\reference_100C\plots
```

## End-To-End Elmer2D Flow

```text
Elmer2D/Gmsh assets
  -> intake review
  -> three-stream solve
  -> log parsing and accepted map
  -> elmer_truth_map_v1.csv
  -> pmsm-map-ml-toolkit
```

Minimal command flow:

```powershell
cd D:\FEM_PMSM\GitHub\pmsm-elmer2d-gmsh-to-tinyml
.\.venv\Scripts\Activate.ps1

pmsm-elmer-export `
  --input runs\YOUR_RUN\accepted_elmer_map.csv `
  --output runs\YOUR_RUN\elmer_truth_map_v1.csv `
  --geometry-id elmer2d_reference_v1

pmsm-map-validate `
  --input runs\YOUR_RUN\elmer_truth_map_v1.csv `
  --report runs\YOUR_RUN\validation_report.json
```

## Common Problems

PowerShell blocks scripts:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

FEMM full lint reports legacy issues:

```text
Update to a commit where legacy/femm_skew is Ruff-excluded.
That directory is archival, not maintained application code.
```

Plotting fails with Tk or Tcl errors:

```text
Update pmsm-map-ml-toolkit. Visualization uses the Agg backend in current main.
```

Package build downloads dependencies:

```text
python -m build uses isolated build environments. It may need network access
for setuptools and wheel if they are not already cached.
```

Git reports dubious ownership:

```powershell
git -c safe.directory='D:/FEM_PMSM/GitHub/REPOSITORY_NAME' status
```

Only add a persistent safe directory if you understand why the Windows ownership
differs:

```powershell
git config --global --add safe.directory D:/FEM_PMSM/GitHub/REPOSITORY_NAME
```

## Maintenance Checklist

Before pushing changes:

```text
1. Check git status.
2. Run tests.
3. Run Ruff.
4. Run one real example or smoke command.
5. Commit only intentional files.
6. Push.
7. Verify remote main.
```

Commands:

```powershell
git status --short --branch
git diff
pytest
ruff check .
python -m build
git add FILES
git commit -m "Short useful message"
git push origin main
git ls-remote origin refs/heads/main
```

## Data Management

Good to commit:

```text
source code
tests
schemas
small examples
small curated reference summaries
documentation
selected final figures
```

Usually do not commit:

```text
.venv
__pycache__
.pytest_cache
.ruff_cache
large solver results
full VTU sweeps
temporary logs
generated local work folders
```

Use external storage, GitHub Releases assets, or a private artifact store for
large result packages.
