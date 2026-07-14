from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

from .validation import normalize_truth_map


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _scatter(frame: pd.DataFrame, value: str, title: str, label: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    plot = ax.scatter(frame["id_RMS_A"], frame["iq_RMS_A"], c=frame[value])
    ax.set_xlabel("Id RMS (A)")
    ax.set_ylabel("Iq RMS (A)")
    ax.set_title(title)
    fig.colorbar(plot, ax=ax, label=label)
    ax.grid(True, alpha=0.25)
    _save(fig, path)


def _contour(frame: pd.DataFrame, value: str, title: str, label: str, path: Path) -> None:
    points = frame[["id_RMS_A", "iq_RMS_A"]].to_numpy(float)
    values = pd.to_numeric(frame[value], errors="coerce").to_numpy(float)
    finite = np.isfinite(points).all(axis=1) & np.isfinite(values)
    points, values = points[finite], values[finite]
    if len(points) < 4:
        _scatter(frame, value, title, label, path)
        return
    x = np.linspace(points[:, 0].min(), points[:, 0].max(), 120)
    y = np.linspace(points[:, 1].min(), points[:, 1].max(), 120)
    xx, yy = np.meshgrid(x, y)
    zz = griddata(points, values, (xx, yy), method="linear")
    fig, ax = plt.subplots(figsize=(8, 6))
    plot = ax.contourf(xx, yy, zz, levels=18)
    ax.scatter(points[:, 0], points[:, 1], s=10)
    ax.set_xlabel("Id RMS (A)")
    ax.set_ylabel("Iq RMS (A)")
    ax.set_title(title)
    fig.colorbar(plot, ax=ax, label=label)
    _save(fig, path)


def generate_truth_map_plots(input_csv: str | Path, output_dir: str | Path) -> list[Path]:
    frame = normalize_truth_map(pd.read_csv(input_csv))
    output = Path(output_dir)
    outputs: list[Path] = []

    fig, ax = plt.subplots(figsize=(8, 6))
    for (solver, temp), group in frame.groupby(["source_solver", "temperature_C"], dropna=False):
        ax.scatter(group["id_RMS_A"], group["iq_RMS_A"], label=f"{solver}, {temp:g} C")
    ax.set_xlabel("Id RMS (A)")
    ax.set_ylabel("Iq RMS (A)")
    ax.set_title("Id-Iq sampling coverage")
    ax.grid(True, alpha=0.25)
    ax.legend()
    path = output / "01_id_iq_sampling_coverage.png"
    _save(fig, path)
    outputs.append(path)

    plot_specs = [
        ("torque_Nm", "Torque map", "Torque (Nm)", "02_torque_contours.png"),
        ("psiD_Wb", "D-axis flux linkage", "PsiD (Wb)", "03_psid_contours.png"),
        ("psiQ_Wb", "Q-axis flux linkage", "PsiQ (Wb)", "04_psiq_contours.png"),
        ("Ld_H", "D-axis inductance", "Ld (H)", "05_ld_contours.png"),
        ("Lq_H", "Q-axis inductance", "Lq (H)", "06_lq_contours.png"),
        ("Bmax_T", "Peak flux-density map", "Bmax (T)", "07_bmax_saturation_map.png"),
    ]
    for column, title, label, filename in plot_specs:
        if column in frame and pd.to_numeric(frame[column], errors="coerce").notna().any():
            path = output / filename
            _contour(frame, column, title, label, path)
            outputs.append(path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate common PMSM truth-map visualizations.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    for path in generate_truth_map_plots(args.input, args.output_dir):
        print(f"Wrote {path.resolve()}")


if __name__ == "__main__":
    main()
