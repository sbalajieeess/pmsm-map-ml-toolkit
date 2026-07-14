from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .nn import INPUT_COLUMNS, OUTPUT_COLUMNS
from .nn_common import infer_float, load_model, save_model


def prune(model: dict[str, np.ndarray], sparsity: float) -> dict[str, np.ndarray]:
    if not 0.0 <= sparsity < 1.0:
        raise ValueError("sparsity must be in [0, 1).")
    result = {name: value.copy() for name, value in model.items()}
    weight_names = sorted(name for name in model if name.startswith("w"))
    all_weights = np.concatenate([np.abs(model[name]).ravel() for name in weight_names])
    threshold = np.quantile(all_weights, sparsity)
    for name in weight_names:
        result[name][np.abs(result[name]) <= threshold] = 0.0
    result["target_sparsity"] = np.array([sparsity], dtype=np.float32)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Magnitude-prune a PMSM MLP model.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--sparsity", type=float, default=0.5)
    args = parser.parse_args()
    model = prune(load_model(args.model), args.sparsity)
    save_model(args.output, model)
    data = pd.read_csv(args.dataset)
    prediction = infer_float(model, data[INPUT_COLUMNS].to_numpy(float))
    target = data[OUTPUT_COLUMNS].to_numpy(float)
    error = prediction - target
    weights = np.concatenate(
        [value.ravel() for name, value in model.items() if name.startswith("w")]
    )
    metrics = {
        "target_sparsity": args.sparsity,
        "actual_sparsity": float(np.mean(weights == 0.0)),
        "id_mae_A": float(np.abs(error[:, 0]).mean()),
        "iq_mae_A": float(np.abs(error[:, 1]).mean()),
    }
    Path(args.metrics).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
