from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import ALIASES, TRUTH_MAP_REQUIRED, ValidationIssue


def normalize_truth_map(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.loc[:, ~data.columns.str.startswith("Unnamed:")].copy()
    rename = {name: ALIASES[name] for name in frame.columns if name in ALIASES}
    frame = frame.rename(columns=rename)
    if "case_id" not in frame:
        frame["case_id"] = [f"P{index + 1:05d}" for index in range(len(frame))]
    if "source_solver" not in frame:
        frame["source_solver"] = "UNKNOWN"
    if "geometry_id" not in frame:
        frame["geometry_id"] = "UNKNOWN"
    if "converged" not in frame:
        frame["converged"] = True
    if "current_magnitude_RMS_A" not in frame and {"id_RMS_A", "iq_RMS_A"} <= set(frame):
        frame["current_magnitude_RMS_A"] = np.hypot(frame["id_RMS_A"], frame["iq_RMS_A"])
    if "current_angle_deg" not in frame and {"id_RMS_A", "iq_RMS_A"} <= set(frame):
        frame["current_angle_deg"] = np.degrees(np.arctan2(frame["id_RMS_A"], frame["iq_RMS_A"]))
    return frame


def validate_truth_map(data: pd.DataFrame) -> list[ValidationIssue]:
    frame = normalize_truth_map(data)
    issues: list[ValidationIssue] = []
    missing = [column for column in TRUTH_MAP_REQUIRED if column not in frame]
    if missing:
        issues.append(ValidationIssue("error", "missing_columns", f"Missing: {missing}"))
        return issues
    numeric = ["temperature_C", "id_RMS_A", "iq_RMS_A", "torque_Nm", "psiD_Wb", "psiQ_Wb"]
    for column in numeric:
        converted = pd.to_numeric(frame[column], errors="coerce")
        count = int(converted.isna().sum())
        if count:
            issues.append(
                ValidationIssue("error", "non_numeric", f"{column} has {count} invalid values")
            )
    duplicate_columns = ["source_solver", "geometry_id", "temperature_C", "id_RMS_A", "iq_RMS_A"]
    duplicates = int(frame.duplicated(duplicate_columns, keep=False).sum())
    if duplicates:
        issues.append(
            ValidationIssue(
                "warning", "duplicate_points", f"{duplicates} rows share an operating point"
            )
        )
    converged = frame["converged"].astype(str).str.lower().isin(["true", "1", "yes", "pass"])
    failed = int((~converged).sum())
    if failed:
        issues.append(ValidationIssue("error", "not_converged", f"{failed} rows are not converged"))
    if not issues:
        issues.append(ValidationIssue("info", "ok", "Truth map passed the baseline checks"))
    return issues


def validation_report(input_path: str | Path) -> dict[str, object]:
    source = Path(input_path)
    frame = normalize_truth_map(pd.read_csv(source))
    issues = validate_truth_map(frame)
    return {
        "input": str(source.resolve()),
        "rows": len(frame),
        "temperatures_C": sorted(
            pd.to_numeric(frame.get("temperature_C", pd.Series()), errors="coerce")
            .dropna()
            .unique()
            .tolist()
        ),
        "issues": [issue.__dict__ for issue in issues],
        "pass": not any(issue.severity == "error" for issue in issues),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a canonical PMSM truth-map CSV.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    report = validation_report(args.input)
    text = json.dumps(report, indent=2)
    if args.report:
        output = Path(args.report)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Wrote {output.resolve()}")
    else:
        print(text)
    raise SystemExit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()
