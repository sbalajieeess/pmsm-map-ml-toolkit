from __future__ import annotations

from pathlib import Path

import numpy as np


def load_model(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def save_model(path: str | Path, model: dict[str, np.ndarray]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **model)
    return output


def relu(value: np.ndarray) -> np.ndarray:
    return np.maximum(value, 0.0)


def infer_float(model: dict[str, np.ndarray], x: np.ndarray) -> np.ndarray:
    z = (x - model["x_mean"]) / model["x_scale"]
    hidden_layers = int(model["n_layers"][0]) - 1
    for index in range(hidden_layers):
        z = relu(z @ model[f"w{index}"] + model[f"b{index}"])
    output_index = hidden_layers
    y_scaled = z @ model[f"w{output_index}"] + model[f"b{output_index}"]
    return y_scaled * model["y_scale"] + model["y_mean"]
