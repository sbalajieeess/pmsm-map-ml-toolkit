from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .nn_common import infer_float, save_model

INPUT_COLUMNS = ["torque_req_Nm", "speed_rpm", "vdc_V", "temp_C"]
OUTPUT_COLUMNS = ["id_star_RMS_A", "iq_star_RMS_A"]


def train(
    dataset: pd.DataFrame, hidden: tuple[int, ...], seed: int
) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    try:
        from sklearn.neural_network import MLPRegressor
    except ImportError as exc:
        raise RuntimeError('Install ML dependencies using: pip install -e ".[ml]"') from exc
    x = dataset[INPUT_COLUMNS].to_numpy(float)
    y = dataset[OUTPUT_COLUMNS].to_numpy(float)
    x_mean, x_scale = x.mean(axis=0), x.std(axis=0)
    y_mean, y_scale = y.mean(axis=0), y.std(axis=0)
    x_scale[x_scale == 0] = 1.0
    y_scale[y_scale == 0] = 1.0
    xs = (x - x_mean) / x_scale
    ys = (y - y_mean) / y_scale
    regressor = MLPRegressor(
        hidden_layer_sizes=hidden,
        activation="relu",
        solver="adam",
        max_iter=5000,
        random_state=seed,
        early_stopping=len(dataset) >= 30,
        validation_fraction=0.2,
        n_iter_no_change=100,
    )
    regressor.fit(xs, ys)
    model: dict[str, np.ndarray] = {
        "x_mean": x_mean,
        "x_scale": x_scale,
        "y_mean": y_mean,
        "y_scale": y_scale,
        "n_layers": np.array([len(regressor.coefs_)], dtype=np.int32),
    }
    for index, (weights, bias) in enumerate(zip(regressor.coefs_, regressor.intercepts_)):
        model[f"w{index}"] = np.asarray(weights, dtype=np.float32)
        model[f"b{index}"] = np.asarray(bias, dtype=np.float32)
    predicted = infer_float(model, x)
    error = predicted - y
    metrics = {
        "rows": int(len(dataset)),
        "id_mae_A": float(np.abs(error[:, 0]).mean()),
        "iq_mae_A": float(np.abs(error[:, 1]).mean()),
        "id_max_abs_A": float(np.abs(error[:, 0]).max()),
        "iq_max_abs_A": float(np.abs(error[:, 1]).max()),
    }
    return model, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a float MLP for Id*/Iq* prediction.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--hidden", default="32,32")
    parser.add_argument("--seed", type=int, default=21)
    args = parser.parse_args()
    data = pd.read_csv(args.dataset)
    hidden = tuple(int(item) for item in args.hidden.split(",") if item.strip())
    model, metrics = train(data, hidden, args.seed)
    save_model(args.model, model)
    prediction = infer_float(model, data[INPUT_COLUMNS].to_numpy(float))
    result = data.copy()
    result["id_pred_RMS_A"] = prediction[:, 0]
    result["iq_pred_RMS_A"] = prediction[:, 1]
    result["id_error_A"] = result["id_pred_RMS_A"] - result["id_star_RMS_A"]
    result["iq_error_A"] = result["iq_pred_RMS_A"] - result["iq_star_RMS_A"]
    Path(args.predictions).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.predictions, index=False)
    Path(args.metrics).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
