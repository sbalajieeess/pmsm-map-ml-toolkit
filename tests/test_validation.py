import pandas as pd

from pmsm_map_ml.validation import normalize_truth_map, validate_truth_map


def test_alias_normalization_and_validation():
    frame = pd.DataFrame(
        [
            {
                "case_id": "P1",
                "source_solver": "FEMM",
                "geometry_id": "G1",
                "temp_C": 100,
                "Id_A": -30,
                "Iq_A": 100,
                "torque_abs_Nm": 55.6,
                "psi_d_rms_wb": 0.03,
                "psi_q_rms_wb": 0.04,
                "converged": True,
            }
        ]
    )
    normalized = normalize_truth_map(frame)
    assert normalized.loc[0, "id_RMS_A"] == -30
    assert normalized.loc[0, "current_magnitude_RMS_A"] > 100
    issues = validate_truth_map(normalized)
    assert not any(issue.severity == "error" for issue in issues)
