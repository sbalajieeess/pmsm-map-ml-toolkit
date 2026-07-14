from __future__ import annotations

from dataclasses import dataclass

TRUTH_MAP_REQUIRED = (
    "case_id",
    "source_solver",
    "geometry_id",
    "temperature_C",
    "id_RMS_A",
    "iq_RMS_A",
    "torque_Nm",
    "psiD_Wb",
    "psiQ_Wb",
    "converged",
)

TRUTH_MAP_OPTIONAL = (
    "slice_id",
    "current_magnitude_RMS_A",
    "current_angle_deg",
    "Ld_H",
    "Lq_H",
    "Bmax_T",
    "solver_iterations",
    "runtime_s",
    "model_hash",
    "config_hash",
)

CONTROLLER_DATASET_REQUIRED = (
    "torque_req_Nm",
    "speed_rpm",
    "vdc_V",
    "temp_C",
    "id_star_RMS_A",
    "iq_star_RMS_A",
    "torque_map_Nm",
    "mode",
    "source",
)

ALIASES = {
    "Id_A": "id_RMS_A",
    "Iq_A": "iq_RMS_A",
    "id_rms_a": "id_RMS_A",
    "iq_rms_a": "iq_RMS_A",
    "temperature_c": "temperature_C",
    "temp_C": "temperature_C",
    "torque_abs_Nm": "torque_Nm",
    "torque_positive_motoring_nm": "torque_Nm",
    "psi_d_rms_wb": "psiD_Wb",
    "psi_q_rms_wb": "psiQ_Wb",
    "ld_h": "Ld_H",
    "lq_h": "Lq_H",
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
