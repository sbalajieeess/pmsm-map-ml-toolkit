from __future__ import annotations

import argparse
import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .validation import normalize_truth_map


def _voltage_rms(row: pd.Series, speed_rpm: float, pole_pairs: int, rs_ohm: float) -> float:
    omega_e = speed_rpm * 2.0 * math.pi / 60.0 * pole_pairs
    vd = rs_ohm * float(row["id_RMS_A"]) - omega_e * float(row["psiQ_Wb"])
    vq = rs_ohm * float(row["iq_RMS_A"]) + omega_e * float(row["psiD_Wb"])
    return math.hypot(vd, vq)


def build_controller_dataset(
    truth_map: pd.DataFrame,
    torques_nm: list[float],
    speeds_rpm: list[float],
    vdc_values: list[float],
    temperatures_c: list[float],
    pole_pairs: int,
    rs_ohm: float,
    modulation_index: float = 0.95,
) -> pd.DataFrame:
    frame = normalize_truth_map(truth_map)
    frame = frame[frame["converged"].astype(str).str.lower().isin(["true", "1", "yes", "pass"])]
    rows: list[dict[str, object]] = []
    for torque_req, speed, vdc, temp in itertools.product(
        torques_nm, speeds_rpm, vdc_values, temperatures_c
    ):
        available_temps = pd.to_numeric(frame["temperature_C"], errors="coerce")
        effective_temp = float(
            available_temps.iloc[(available_temps - temp).abs().argsort().iloc[0]]
        )
        candidates = frame[available_temps == effective_temp].copy()
        candidates["Is_RMS_A"] = np.hypot(candidates["id_RMS_A"], candidates["iq_RMS_A"])
        candidates["Vphase_RMS_est"] = candidates.apply(
            _voltage_rms, axis=1, args=(speed, pole_pairs, rs_ohm)
        )
        vmax = modulation_index * vdc / math.sqrt(6.0)
        candidates["voltage_margin_RMS_V"] = vmax - candidates["Vphase_RMS_est"]
        candidates["torque_error_Nm"] = (candidates["torque_Nm"] - torque_req).abs()
        feasible = candidates[
            (candidates["voltage_margin_RMS_V"] >= 0.0) & (candidates["torque_Nm"] >= torque_req)
        ]
        if not feasible.empty:
            selected = feasible.sort_values(["Is_RMS_A", "torque_error_Nm"]).iloc[0]
            mode = (
                "MTPA" if speed <= 0 or selected["voltage_margin_RMS_V"] > 0.05 * vmax else "MTPV"
            )
        else:
            voltage_ok = candidates[candidates["voltage_margin_RMS_V"] >= 0.0]
            pool = voltage_ok if not voltage_ok.empty else candidates
            selected = pool.sort_values(["torque_error_Nm", "Is_RMS_A"]).iloc[0]
            mode = "LIMITED"
        rows.append(
            {
                "torque_req_Nm": torque_req,
                "speed_rpm": speed,
                "vdc_V": vdc,
                "temp_C": temp,
                "effective_temp_C": effective_temp,
                "id_star_RMS_A": float(selected["id_RMS_A"]),
                "iq_star_RMS_A": float(selected["iq_RMS_A"]),
                "torque_map_Nm": float(selected["torque_Nm"]),
                "torque_error_Nm": float(selected["torque_error_Nm"]),
                "Is_RMS_A": float(selected["Is_RMS_A"]),
                "Vphase_RMS_est": float(selected["Vphase_RMS_est"]),
                "Vmax_RMS_est": vmax,
                "voltage_margin_RMS_V": float(selected["voltage_margin_RMS_V"]),
                "psiD_Wb": float(selected["psiD_Wb"]),
                "psiQ_Wb": float(selected["psiQ_Wb"]),
                "mode": mode,
                "source": str(selected["source_solver"]),
            }
        )
    return pd.DataFrame(rows)


def _floats(value: str) -> list[float]:
    return [float(item) for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a controller dataset from a PMSM truth map."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--torques", default="5,10,20,30,40,50,60")
    parser.add_argument("--speeds", default="500,1000,2000,4000,6000,8000,10000")
    parser.add_argument("--vdc", default="350,400,450")
    parser.add_argument("--temperatures", default="60,100")
    parser.add_argument("--pole-pairs", type=int, default=4)
    parser.add_argument("--rs-ohm", type=float, default=0.01)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = build_controller_dataset(
        pd.read_csv(args.input),
        _floats(args.torques),
        _floats(args.speeds),
        _floats(args.vdc),
        _floats(args.temperatures),
        args.pole_pairs,
        args.rs_ohm,
    )
    result.to_csv(output, index=False)
    print(f"Wrote {output.resolve()} ({len(result)} rows)")


if __name__ == "__main__":
    main()
