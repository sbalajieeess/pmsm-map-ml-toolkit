from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .nn_common import load_model


def _array(name: str, values: np.ndarray, c_type: str) -> str:
    flat = values.ravel()
    if np.issubdtype(values.dtype, np.integer):
        content = ", ".join(str(int(value)) for value in flat)
    else:
        content = ", ".join(f"{float(value):.9g}f" for value in flat)
    shape = " x ".join(str(size) for size in values.shape)
    return f"// shape: {shape}\nstatic const {c_type} {name}[{len(flat)}] = {{{content}}};\n"


def export_header(model_path: str | Path, output_path: str | Path) -> Path:
    model = load_model(model_path)
    lines = [
        "#ifndef PMSM_TINYML_MODEL_H",
        "#define PMSM_TINYML_MODEL_H",
        "#include <stdint.h>",
        "",
    ]
    for name in sorted(model):
        values = model[name]
        if name.startswith("w") and values.dtype == np.int8:
            lines.append(_array(name, values, "int8_t"))
        elif values.dtype.kind in "f":
            lines.append(_array(name, values.astype(np.float32), "float"))
    lines.append("#endif  // PMSM_TINYML_MODEL_H\n")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a PMSM NPZ model to a C header.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = export_header(args.model, args.output)
    print(f"Wrote {output.resolve()}")


if __name__ == "__main__":
    main()
