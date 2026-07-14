from __future__ import annotations

import argparse

import numpy as np

from .nn_common import load_model, save_model


def quantize(model: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    for name, value in model.items():
        if name.startswith("w"):
            maximum = float(np.max(np.abs(value)))
            scale = maximum / 127.0 if maximum > 0 else 1.0
            result[name] = np.clip(np.rint(value / scale), -127, 127).astype(np.int8)
            result[f"{name}_scale"] = np.array([scale], dtype=np.float32)
        else:
            result[name] = value
    result["quantized"] = np.array([1], dtype=np.int8)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Symmetric int8 weight quantization.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = save_model(args.output, quantize(load_model(args.model)))
    print(f"Wrote {output.resolve()}")


if __name__ == "__main__":
    main()
