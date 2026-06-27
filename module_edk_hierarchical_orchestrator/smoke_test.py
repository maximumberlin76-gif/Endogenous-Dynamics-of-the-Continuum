from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
import argparse
import json
import math
import os
import shutil
import tempfile

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

try:
    from .edk_hierarchical_orchestrator import (
        DynamicRegime,
        EDKFeedbackPacket,
        EDKForwardCascadePacket,
        EDKHierarchicalLogger,
        EDKHierarchicalOrchestrator,
        EDKHierarchicalState,
        EDKModuleRegistry,
        EDKOrchestratorError,
        ExecutionMode,
        RunStatus,
        STAGE_ORDER,
    )
except ImportError:
    from edk_hierarchical_orchestrator import (
        DynamicRegime,
        EDKFeedbackPacket,
        EDKForwardCascadePacket,
        EDKHierarchicalLogger,
        EDKHierarchicalOrchestrator,
        EDKHierarchicalState,
        EDKModuleRegistry,
        EDKOrchestratorError,
        ExecutionMode,
        RunStatus,
        STAGE_ORDER,
    )


StageOperation = Callable[
    [
        EDKForwardCascadePacket,
        EDKHierarchicalState,
        float,
    ],
    Mapping[str, Any],
]


@dataclass
class SyntheticStageAdapter:
    module_name: str
    stage_name: str
    required_inputs: tuple[str, ...]
    provided_outputs: tuple[str, ...]
    operation: StageOperation
    mandatory: bool = True
    backend: str = "numpy"
    execution_count: int = 0
    last_output: dict[str, Any] = field(
        default_factory=dict
    )

    def validate_input(
        self,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
    ) -> bool:
        del state

        for field_name in self.required_inputs:
            if field_name not in packet.payload:
                return False

            if packet.payload[field_name] is None:
                return False

        return True

    def step(
        self,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
        dt: float,
    ) -> Mapping[str, Any]:
        output = dict(
            self.operation(
                packet,
                state,
                dt,
            )
        )

        self.execution_count += 1

        self.last_output = _copy_mapping(
            output
        )

        return output

    def validate_output(
        self,
        output: Mapping[str, Any],
    ) -> bool:
        return all(
            field_name in output
            for field_name
            in self.provided_outputs
        )

    def export_state(
        self,
    ) -> Mapping[str, Any]:
        return {
            "stage_name": self.stage_name,
            "execution_count": (
                self.execution_count
            ),
            "last_output_fields": sorted(
                self.last_output
            ),
            "module_feedback": {
                "module_name": self.module_name,
                "stage_name": self.stage_name,
                "execution_count": (
                    self.execution_count
                ),
            },
        }


def _as_scalar(
    value: Any,
) -> float:
    if isinstance(
        value,
        np.ndarray,
    ):
        if value.size == 0:
            raise ValueError(
                "Cannot reduce an empty array to a scalar."
            )

        if np.iscomplexobj(
            value
        ):
            return float(
                np.mean(
                    np.abs(
                        value
                    )
                )
            )

        return float(
            np.mean(
                value
            )
        )

    if isinstance(
        value,
        np.generic,
    ):
        return float(
            value.item()
        )

    if isinstance(
        value,
        complex,
    ):
        return float(
            abs(
                value
            )
        )

    return float(
        value
    )


def _copy_value(
    value: Any,
) -> Any:
    if isinstance(
        value,
        np.ndarray,
    ):
        return value.copy()

    if isinstance(
        value,
        Mapping,
    ):
        return _copy_mapping(
            value
        )

    if isinstance(
        value,
        list,
    ):
        return [
            _copy_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return tuple(
            _copy_value(
                item
            )
            for item in value
        )

    return value


def _copy_mapping(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        str(key): _copy_value(
            item
        )
        for key, item
        in value.items()
    }


def _require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(
            message
        )


def _require_close(
    actual: float,
    expected: float,
    *,
    tolerance: float = 1.0e-12,
    message: str,
) -> None:
    if not math.isclose(
        float(actual),
        float(expected),
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        raise AssertionError(
            (
                f"{message}: "
                f"actual={actual}, "
                f"expected={expected}"
            )
        )


def _solar_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del dt

    phase = (
        0.25
        * float(
            packet.tact_index + 1
        )
    )

    q_scalar = _as_scalar(
        state.Q_n
    )

    solar_phase_vector = np.asarray(
        [
            math.cos(
                phase
            ),
            math.sin(
                phase
            ),
            math.cos(
                0.5 * phase
            ),
        ],
        dtype=np.float64,
    )

    return {
        "solar_drive": (
            1.0
            + 0.05 * q_scalar
        ),
        "solar_phase_vector": (
            solar_phase_vector
        ),
        "solar_tact_signature": float(
            packet.tact_index
        ),
    }


def _planetary_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    solar_drive = _as_scalar(
        packet.payload[
            "solar_drive"
        ]
    )

    phase_vector = np.asarray(
        packet.payload[
            "solar_phase_vector"
        ],
        dtype=np.float64,
    )

    planetary_phase = float(
        math.atan2(
            phase_vector[1],
            phase_vector[0],
        )
    )

    planetary_coupling = (
        solar_drive
        * (
            1.0
            + 0.1
            * math.cos(
                planetary_phase
            )
        )
    )

    return {
        "planetary_phase": (
            planetary_phase
        ),
        "planetary_coupling": (
            planetary_coupling
        ),
        "P_t": (
            0.34
            + 0.01
            * float(
                packet.tact_index
            )
        ),
        "planetary_appearance_index": (
            planetary_coupling
            / (
                1.0
                + abs(
                    planetary_phase
                )
            )
        ),
    }


def _bio_planetary_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state

    coupling = _as_scalar(
        packet.payload[
            "planetary_coupling"
        ]
    )

    planetary_phase = _as_scalar(
        packet.payload[
            "planetary_phase"
        ]
    )

    modulation = (
        coupling
        * (
            1.0
            + 0.05
            * math.sin(
                planetary_phase
                + dt
            )
        )
    )

    return {
        "bio_planetary_modulation": (
            modulation
        ),
        "bio_planetary_modulation_proxy": (
            modulation
        ),
    }


def _continuum_core_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del dt

    modulation = _as_scalar(
        packet.payload[
            "bio_planetary_modulation"
        ]
    )

    pressure = _as_scalar(
        packet.payload[
            "P_t"
        ]
    )

    q_scalar = _as_scalar(
        state.Q_n
    )

    C_t = (
        0.78
        + 0.08 * modulation
        + 0.02 * q_scalar
    )

    C_proxy_t = (
        0.985
        * C_t
    )

    D_n = (
        0.07
        + 0.01 * pressure
    )

    A_n = (
        0.22
        + 0.03 * modulation
    )

    denominator = (
        abs(
            C_t
        )
        + abs(
            pressure
        )
        + 1.0e-12
    )

    R_t_phase_order = float(
        np.clip(
            C_t / denominator,
            0.0,
            1.0,
        )
    )

    return {
        "C_t": C_t,
        "C_proxy_t": C_proxy_t,
        "D_n": D_n,
        "A_n": A_n,
        "R_t_phase_order": (
            R_t_phase_order
        ),
        "continuum_core_state": (
            np.asarray(
                [
                    C_t,
                    pressure,
                    D_n,
                    A_n,
                ],
                dtype=np.float64,
            )
        ),
    }


def _interface_tensor_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    C_t = _as_scalar(
        packet.payload[
            "C_t"
        ]
    )

    pressure = _as_scalar(
        packet.payload[
            "P_t"
        ]
    )

    phase_order = _as_scalar(
        packet.payload[
            "R_t_phase_order"
        ]
    )

    T_int = np.asarray(
        [
            [
                C_t,
                phase_order,
                0.0,
            ],
            [
                phase_order,
                C_t + pressure,
                0.0,
            ],
            [
                0.0,
                0.0,
                C_t - pressure,
            ],
        ],
        dtype=np.float64,
    )

    M_t = float(
        np.linalg.det(
            T_int
        )
    )

    return {
        "T_int": T_int,
        "M_t": M_t,
        "local_mass_formation_proxy": (
            M_t
        ),
    }


def _interface_tensor_without_t_int_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    C_t = _as_scalar(
        packet.payload[
            "C_t"
        ]
    )

    pressure = _as_scalar(
        packet.payload[
            "P_t"
        ]
    )

    return {
        "M_t": (
            C_t
            - pressure
        ),
        "local_mass_formation_proxy": (
            C_t
            - pressure
        ),
    }


def _massless_exchange_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    T_int = np.asarray(
        packet.payload[
            "T_int"
        ],
        dtype=np.float64,
    )

    M_t = _as_scalar(
        packet.payload[
            "M_t"
        ]
    )

    J_vector = np.asarray(
        [
            (
                T_int[0, 0]
                - T_int[1, 1]
            ),
            (
                T_int[0, 1]
                + T_int[1, 0]
            ),
            T_int[2, 2],
        ],
        dtype=np.float64,
    )

    J_flux = float(
        np.trace(
            T_int
        )
        + 0.05 * M_t
    )

    return {
        "J_flux": J_flux,
        "J_vector": J_vector,
        "exchange_activity": float(
            np.linalg.norm(
                J_vector
            )
        ),
    }


def _massless_exchange_without_t_int_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    M_t = _as_scalar(
        packet.payload[
            "M_t"
        ]
    )

    return {
        "J_flux": (
            1.0
            + M_t
        ),
        "J_vector": np.asarray(
            [
                M_t,
                0.0,
                -M_t,
            ],
            dtype=np.float64,
        ),
    }


def _massless_exchange_without_j_flux_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    T_int = np.asarray(
        packet.payload[
            "T_int"
        ],
        dtype=np.float64,
    )

    return {
        "J_vector": np.asarray(
            [
                T_int[0, 0],
                T_int[1, 1],
                T_int[2, 2],
            ],
            dtype=np.float64,
        ),
        "exchange_activity": float(
            np.linalg.norm(
                T_int
            )
        ),
    }


def _wave_genetics_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state

    J_flux = _as_scalar(
        packet.payload[
            "J_flux"
        ]
    )

    phase_order = _as_scalar(
        packet.payload[
            "R_t_phase_order"
        ]
    )

    sample_axis = np.linspace(
        0.0,
        2.0 * math.pi,
        16,
        endpoint=False,
        dtype=np.float64,
    )

    wave_signal = (
        J_flux
        * np.sin(
            sample_axis
            + phase_order
            + float(
                packet.tact_index
            )
            * dt
        )
    )

    return {
        "wave_genetic_signal": (
            wave_signal
        ),
        "wave_genetic_amplitude": float(
            np.sqrt(
                np.mean(
                    np.square(
                        wave_signal
                    )
                )
            )
        ),
        "inherited_qualitative_characteristics": {
            "source_tact": int(
                packet.tact_index
            ),
            "phase_order": (
                phase_order
            ),
            "J_flux": J_flux,
            "signal_norm": float(
                np.linalg.norm(
                    wave_signal
                )
            ),
        },
    }


def _wave_genetics_without_j_flux_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    M_t = _as_scalar(
        packet.payload[
            "M_t"
        ]
    )

    signal = np.asarray(
        [
            M_t,
            -M_t,
            0.5 * M_t,
        ],
        dtype=np.float64,
    )

    return {
        "wave_genetic_signal": (
            signal
        ),
        "wave_genetic_amplitude": float(
            np.linalg.norm(
                signal
            )
        ),
        "inherited_qualitative_characteristics": {
            "source_tact": int(
                packet.tact_index
            ),
            "M_t": M_t,
        },
    }


def _molecular_phase_chemistry_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    signal = np.asarray(
        packet.payload[
            "wave_genetic_signal"
        ],
        dtype=np.float64,
    )

    amplitude = _as_scalar(
        packet.payload[
            "wave_genetic_amplitude"
        ]
    )

    covalent_stability_proxy = float(
        1.0
        / (
            1.0
            + np.var(
                signal
            )
        )
    )

    hydrogen_flexibility_proxy = float(
        amplitude
        / (
            1.0
            + amplitude
        )
    )

    retained_structural_work = float(
        np.mean(
            np.square(
                signal
            )
        )
        * covalent_stability_proxy
    )

    return {
        "covalent_stability_proxy": (
            covalent_stability_proxy
        ),
        "hydrogen_flexibility_proxy": (
            hydrogen_flexibility_proxy
        ),
        "retained_structural_work": (
            retained_structural_work
        ),
        "molecular_phase_state": (
            np.asarray(
                [
                    covalent_stability_proxy,
                    hydrogen_flexibility_proxy,
                    retained_structural_work,
                ],
                dtype=np.float64,
            )
        ),
    }


def _feedback_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    C_t = _as_scalar(
        packet.payload[
            "C_t"
        ]
    )

    P_t = _as_scalar(
        packet.payload[
            "P_t"
        ]
    )

    D_n = _as_scalar(
        packet.payload[
            "D_n"
        ]
    )

    A_n = _as_scalar(
        packet.payload[
            "A_n"
        ]
    )

    J_flux = _as_scalar(
        packet.payload[
            "J_flux"
        ]
    )

    T_int = np.asarray(
        packet.payload[
            "T_int"
        ],
        dtype=np.float64,
    )

    margin = (
        C_t
        - P_t
    )

    if margin > 0.0:
        resonance_window_state = (
            "POSITIVE_SYNTHESIS_WINDOW"
        )

    elif margin < 0.0:
        resonance_window_state = (
            "NEGATIVE_DEGRADATION_WINDOW"
        )

    else:
        resonance_window_state = (
            "CRITICAL_BOUNDARY_WINDOW"
        )

    return {
        "module_feedback": {
            "D_n": D_n,
            "A_n": A_n,
            "J_flux": J_flux,
            "T_int_trace": float(
                np.trace(
                    T_int
                )
            ),
            "retention_margin": (
                margin
            ),
        },
        "resonance_window_state": (
            resonance_window_state
        ),
    }


def _feedback_without_t_int_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    C_t = _as_scalar(
        packet.payload[
            "C_t"
        ]
    )

    P_t = _as_scalar(
        packet.payload[
            "P_t"
        ]
    )

    D_n = _as_scalar(
        packet.payload[
            "D_n"
        ]
    )

    A_n = _as_scalar(
        packet.payload[
            "A_n"
        ]
    )

    J_flux = _as_scalar(
        packet.payload[
            "J_flux"
        ]
    )

    return {
        "module_feedback": {
            "D_n": D_n,
            "A_n": A_n,
            "J_flux": J_flux,
            "retention_margin": (
                C_t
                - P_t
            ),
        },
        "resonance_window_state": (
            "UNRESOLVED_WITHOUT_T_INT"
        ),
    }


def _feedback_without_j_flux_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del state, dt

    return {
        "module_feedback": {
            "D_n": _as_scalar(
                packet.payload[
                    "D_n"
                ]
            ),
            "A_n": _as_scalar(
                packet.payload[
                    "A_n"
                ]
            ),
            "T_int_trace": float(
                np.trace(
                    np.asarray(
                        packet.payload[
                            "T_int"
                        ],
                        dtype=np.float64,
                    )
                )
            ),
        },
        "resonance_window_state": (
            "UNRESOLVED_WITHOUT_J_FLUX"
        ),
    }


def _non_finite_solar_operation(
    packet: EDKForwardCascadePacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Mapping[str, Any]:
    del packet, state, dt

    return {
        "solar_drive": float(
            "nan"
        ),
        "solar_phase_vector": np.asarray(
            [
                1.0,
                0.0,
                0.0,
            ],
            dtype=np.float64,
        ),
        "solar_tact_signature": (
            0.0
        ),
    }


def phi_operator(
    Q_n: Any,
    D_n: Any,
    A_n: Any,
    feedback: EDKFeedbackPacket,
    state: EDKHierarchicalState,
    dt: float,
) -> np.ndarray:
    del state

    q_array = np.asarray(
        Q_n,
        dtype=np.float64,
    )

    D_scalar = _as_scalar(
        D_n
    )

    A_scalar = _as_scalar(
        A_n
    )

    J_scalar = _as_scalar(
        feedback.J_flux
    )

    T_scalar = _as_scalar(
        np.asarray(
            feedback.T_int,
            dtype=np.float64,
        )
    )

    recursive_drive = (
        A_scalar
        - D_scalar
        + 0.01 * J_scalar
        + 0.01 * T_scalar
    )

    return (
        q_array
        + dt * recursive_drive
    )


def failing_phi_operator(
    Q_n: Any,
    D_n: Any,
    A_n: Any,
    feedback: EDKFeedbackPacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Any:
    del (
        Q_n,
        D_n,
        A_n,
        feedback,
        state,
        dt,
    )

    raise RuntimeError(
        "Synthetic Phi failure."
    )


def build_initial_state(
) -> EDKHierarchicalState:
    return EDKHierarchicalState(
        tact_index=0,
        simulation_time=0.0,
        Q_n=np.asarray(
            [
                1.0,
                0.75,
                0.5,
            ],
            dtype=np.float64,
        ),
        D_n=0.08,
        A_n=0.25,
        C_t=0.90,
        C_proxy_t=0.8865,
        P_t=0.34,
        R_t_phase_order=0.72,
        T_int=(
            np.eye(
                3,
                dtype=np.float64,
            )
            * 0.90
        ),
        J_flux=2.70,
        M_t=0.56,
        retention_margin=0.56,
        dynamic_regime=(
            DynamicRegime
            .ENDOGENOUS_DYNAMIC_STABILITY
            .value
        ),
        resonance_window_state=(
            "INITIAL_POSITIVE_WINDOW"
        ),
        operational_fields={
            "retained_structural_work": (
                0.0
            ),
            "inherited_qualitative_characteristics": {
                "source_tact": -1,
                "phase_order": 0.72,
                "J_flux": 2.70,
            },
        },
    )


def build_registry(
    *,
    omit_stage: str | None = None,
    omit_t_int: bool = False,
    omit_j_flux: bool = False,
    backend_mismatch: bool = False,
    non_finite_solar: bool = False,
) -> EDKModuleRegistry:
    registry = EDKModuleRegistry()

    solar_operation = (
        _non_finite_solar_operation
        if non_finite_solar
        else _solar_operation
    )

    stage_adapters: list[
        SyntheticStageAdapter
    ] = [
        SyntheticStageAdapter(
            module_name=(
                "synthetic_solar"
            ),
            stage_name="solar",
            required_inputs=(
                "Q_n",
            ),
            provided_outputs=(
                "solar_drive",
                "solar_phase_vector",
                "solar_tact_signature",
            ),
            operation=solar_operation,
            backend=(
                "cupy"
                if backend_mismatch
                else "numpy"
            ),
        ),
        SyntheticStageAdapter(
            module_name=(
                "synthetic_planetary"
            ),
            stage_name="planetary",
            required_inputs=(
                "solar_drive",
                "solar_phase_vector",
            ),
            provided_outputs=(
                "planetary_phase",
                "planetary_coupling",
                "P_t",
                "planetary_appearance_index",
            ),
            operation=(
                _planetary_operation
            ),
        ),
        SyntheticStageAdapter(
            module_name=(
                "synthetic_bio_planetary"
            ),
            stage_name=(
                "bio_planetary"
            ),
            required_inputs=(
                "planetary_coupling",
                "planetary_phase",
            ),
            provided_outputs=(
                "bio_planetary_modulation",
                "bio_planetary_modulation_proxy",
            ),
            operation=(
                _bio_planetary_operation
            ),
        ),
        SyntheticStageAdapter(
            module_name=(
                "synthetic_continuum_core"
            ),
            stage_name=(
                "continuum_core"
            ),
            required_inputs=(
                "bio_planetary_modulation",
                "Q_n",
                "P_t",
            ),
            provided_outputs=(
                "C_t",
                "C_proxy_t",
                "D_n",
                "A_n",
                "R_t_phase_order",
                "continuum_core_state",
            ),
            operation=(
                _continuum_core_operation
            ),
        ),
    ]

    if omit_t_int:
        stage_adapters.append(
            SyntheticStageAdapter(
                module_name=(
                    "synthetic_interface_tensor"
                ),
                stage_name=(
                    "interface_tensor"
                ),
                required_inputs=(
                    "C_t",
                    "P_t",
                ),
                provided_outputs=(
                    "M_t",
                    "local_mass_formation_proxy",
                ),
                operation=(
                    _interface_tensor_without_t_int_operation
                ),
            )
        )

    else:
        stage_adapters.append(
            SyntheticStageAdapter(
                module_name=(
                    "synthetic_interface_tensor"
                ),
                stage_name=(
                    "interface_tensor"
                ),
                required_inputs=(
                    "C_t",
                    "P_t",
                    "R_t_phase_order",
                ),
                provided_outputs=(
                    "T_int",
                    "M_t",
                    "local_mass_formation_proxy",
                ),
                operation=(
                    _interface_tensor_operation
                ),
            )
        )

    if omit_t_int:
        massless_required_inputs = (
            "M_t",
        )

        massless_operation = (
            _massless_exchange_without_t_int_operation
        )

        massless_outputs = (
            "J_flux",
            "J_vector",
        )

    elif omit_j_flux:
        massless_required_inputs = (
            "T_int",
            "M_t",
        )

        massless_operation = (
            _massless_exchange_without_j_flux_operation
        )

        massless_outputs = (
            "J_vector",
            "exchange_activity",
        )

    else:
        massless_required_inputs = (
            "T_int",
            "M_t",
        )

        massless_operation = (
            _massless_exchange_operation
        )

        massless_outputs = (
            "J_flux",
            "J_vector",
            "exchange_activity",
        )

    stage_adapters.append(
        SyntheticStageAdapter(
            module_name=(
                "synthetic_massless_exchange_channel"
            ),
            stage_name=(
                "massless_exchange_channel"
            ),
            required_inputs=(
                massless_required_inputs
            ),
            provided_outputs=(
                massless_outputs
            ),
            operation=(
                massless_operation
            ),
        )
    )

    if omit_j_flux:
        wave_required_inputs = (
            "M_t",
        )

        wave_operation = (
            _wave_genetics_without_j_flux_operation
        )

    else:
        wave_required_inputs = (
            "J_flux",
            "R_t_phase_order",
        )

        wave_operation = (
            _wave_genetics_operation
        )

    stage_adapters.append(
        SyntheticStageAdapter(
            module_name=(
                "synthetic_wave_genetics"
            ),
            stage_name=(
                "wave_genetics"
            ),
            required_inputs=(
                wave_required_inputs
            ),
            provided_outputs=(
                "wave_genetic_signal",
                "wave_genetic_amplitude",
                "inherited_qualitative_characteristics",
            ),
            operation=(
                wave_operation
            ),
        )
    )

    stage_adapters.append(
        SyntheticStageAdapter(
            module_name=(
                "synthetic_molecular_phase_chemistry"
            ),
            stage_name=(
                "molecular_phase_chemistry"
            ),
            required_inputs=(
                "wave_genetic_signal",
                "wave_genetic_amplitude",
            ),
            provided_outputs=(
                "covalent_stability_proxy",
                "hydrogen_flexibility_proxy",
                "retained_structural_work",
                "molecular_phase_state",
            ),
            operation=(
                _molecular_phase_chemistry_operation
            ),
        )
    )

    if omit_t_int:
        feedback_required_inputs = (
            "D_n",
            "A_n",
            "J_flux",
            "C_t",
            "P_t",
        )

        feedback_operation = (
            _feedback_without_t_int_operation
        )

    elif omit_j_flux:
        feedback_required_inputs = (
            "D_n",
            "A_n",
            "T_int",
        )

        feedback_operation = (
            _feedback_without_j_flux_operation
        )

    else:
        feedback_required_inputs = (
            "D_n",
            "A_n",
            "J_flux",
            "T_int",
            "C_t",
            "P_t",
        )

        feedback_operation = (
            _feedback_operation
        )

    stage_adapters.append(
        SyntheticStageAdapter(
            module_name=(
                "synthetic_feedback"
            ),
            stage_name="feedback",
            required_inputs=(
                feedback_required_inputs
            ),
            provided_outputs=(
                "module_feedback",
                "resonance_window_state",
            ),
            operation=(
                feedback_operation
            ),
        )
    )

    for adapter in stage_adapters:
        if (
            adapter.stage_name
            == omit_stage
        ):
            continue

        registry.register(
            adapter
        )

    return registry


def build_orchestrator(
    output_directory: Path,
    *,
    registry: (
        EDKModuleRegistry | None
    ) = None,
    phi: Callable[..., Any] = (
        phi_operator
    ),
    dt: float = 0.01,
    initial_state: (
        EDKHierarchicalState | None
    ) = None,
) -> EDKHierarchicalOrchestrator:
    return EDKHierarchicalOrchestrator(
        registry=(
            registry
            or build_registry()
        ),
        initial_state=(
            initial_state
            or build_initial_state()
        ),
        phi_operator=phi,
        logger=(
            EDKHierarchicalLogger(
                output_directory
            )
        ),
        dt=dt,
        execution_mode=(
            ExecutionMode.COMPLETE
        ),
        critical_band=1.0e-12,
        required_stages=(
            STAGE_ORDER
        ),
        log_every_tact=True,
    )


def run_success_case(
    output_directory: Path,
    *,
    tact_count: int,
    dt: float,
) -> dict[str, Any]:
    orchestrator = build_orchestrator(
        output_directory,
        dt=dt,
    )

    initial_q = np.asarray(
        orchestrator.state.Q_n,
        dtype=np.float64,
    ).copy()

    summary = orchestrator.run(
        tact_count
    )

    _require(
        (
            summary[
                "status"
            ]
            == RunStatus.COMPLETED.value
        ),
        (
            "Successful integration run "
            "did not complete."
        ),
    )

    _require(
        (
            int(
                summary[
                    "completed_tacts"
                ]
            )
            == tact_count
        ),
        (
            "Completed tact count does "
            "not match the request."
        ),
    )

    _require(
        (
            orchestrator.state.tact_index
            == tact_count
        ),
        (
            "Final tact index "
            "is incorrect."
        ),
    )

    _require_close(
        orchestrator.state.simulation_time,
        tact_count * dt,
        message=(
            "Final simulation time "
            "is incorrect"
        ),
    )

    _require(
        (
            orchestrator.state.dynamic_regime
            == (
                DynamicRegime
                .ENDOGENOUS_DYNAMIC_STABILITY
                .value
            )
        ),
        (
            "The successful test did not "
            "retain dynamic stability."
        ),
    )

    _require(
        (
            orchestrator.state.T_int
            is not None
        ),
        (
            "T_int was not preserved."
        ),
    )

    _require(
        (
            orchestrator.state.J_flux
            is not None
        ),
        (
            "J_flux was not preserved."
        ),
    )

    _require(
        (
            "T_int"
            in orchestrator
            .state
            .field_provenance
        ),
        (
            "T_int provenance "
            "is missing."
        ),
    )

    _require(
        (
            "J_flux"
            in orchestrator
            .state
            .field_provenance
        ),
        (
            "J_flux provenance "
            "is missing."
        ),
    )

    _require(
        not np.allclose(
            np.asarray(
                orchestrator.state.Q_n,
                dtype=np.float64,
            ),
            initial_q,
        ),
        (
            "Phi did not update Q(n)."
        ),
    )

    expected_modules = {
        adapter.module_name
        for adapter
        in orchestrator
        .registry
        .ordered_adapters()
    }

    _require(
        (
            set(
                orchestrator
                .state
                .module_states
            )
            == expected_modules
        ),
        (
            "Module-state inheritance "
            "is incomplete."
        ),
    )

    for tact_index in range(
        1,
        tact_count + 1,
    ):
        json_path = (
            output_directory
            / (
                "hierarchical_step_"
                f"{tact_index:06d}.json"
            )
        )

        npz_path = (
            output_directory
            / (
                "hierarchical_field_"
                f"{tact_index:06d}.npz"
            )
        )

        _require(
            json_path.exists(),
            (
                "Missing JSON log: "
                f"{json_path}"
            ),
        )

        _require(
            npz_path.exists(),
            (
                "Missing NPZ log: "
                f"{npz_path}"
            ),
        )

        _require(
            (
                json_path.stat().st_size
                > 0
            ),
            (
                "Empty JSON log: "
                f"{json_path}"
            ),
        )

        _require(
            (
                npz_path.stat().st_size
                > 0
            ),
            (
                "Empty NPZ log: "
                f"{npz_path}"
            ),
        )

        metadata = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )

        _require(
            (
                metadata[
                    "status"
                ]
                == RunStatus.COMPLETED.value
            ),
            (
                "Unexpected tact status in "
                f"{json_path.name}."
            ),
        )

        _require(
            (
                metadata[
                    "tact"
                ]
                == tact_index
            ),
            (
                "Top-level tact metadata "
                "does not match the log filename."
            ),
        )

        _require(
            (
                metadata[
                    "step"
                ]
                == tact_index
            ),
            (
                "Compatibility step metadata "
                "does not match the log filename."
            ),
        )

        _require(
            (
                metadata[
                    "tact_index"
                ]
                == tact_index
            ),
            (
                "Top-level tact_index metadata "
                "does not match the log filename."
            ),
        )

        _require_close(
            metadata[
                "simulation_time"
            ],
            tact_index * dt,
            message=(
                "Top-level simulation_time "
                "metadata is incorrect"
            ),
        )

        _require(
            (
                metadata[
                    "state"
                ][
                    "tact_index"
                ]
                == tact_index
            ),
            (
                "State tact_index metadata "
                "does not match the log filename."
            ),
        )

        _require_close(
            metadata[
                "state"
            ][
                "simulation_time"
            ],
            tact_index * dt,
            message=(
                "State simulation_time "
                "metadata is incorrect"
            ),
        )

        _require(
            (
                metadata[
                    "state"
                ][
                    "T_int"
                ]
                is not None
            ),
            (
                "T_int metadata is missing in "
                f"{json_path.name}."
            ),
        )

        _require(
            (
                metadata[
                    "state"
                ][
                    "J_flux"
                ]
                is not None
            ),
            (
                "J_flux metadata is missing in "
                f"{json_path.name}."
            ),
        )

        with np.load(
            npz_path,
            allow_pickle=False,
        ) as archive:
            _require(
                (
                    len(
                        archive.files
                    )
                    > 0
                ),
                (
                    "NPZ archive contains "
                    "no numerical fields: "
                    f"{npz_path.name}"
                ),
            )

    summary_path = (
        output_directory
        / "hierarchical_summary.json"
    )

    _require(
        summary_path.exists(),
        (
            "hierarchical_summary.json "
            "is missing."
        ),
    )

    persisted_summary = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    _require(
        (
            persisted_summary[
                "status"
            ]
            == RunStatus.COMPLETED.value
        ),
        (
            "Persisted summary status "
            "is incorrect."
        ),
    )

    return {
        "status": "PASS",
        "tact_count": tact_count,
        "final_tact_index": (
            orchestrator.state.tact_index
        ),
        "final_simulation_time": (
            orchestrator
            .state
            .simulation_time
        ),
        "dynamic_regime": (
            orchestrator
            .state
            .dynamic_regime
        ),
        "final_Q_n": np.asarray(
            orchestrator.state.Q_n,
            dtype=np.float64,
        ).tolist(),
        "T_int_shape": list(
            np.asarray(
                orchestrator.state.T_int
            ).shape
        ),
        "J_flux": _as_scalar(
            orchestrator.state.J_flux
        ),
        "registered_stages": list(
            orchestrator
            .registry
            .registered_stages()
        ),
        "output_directory": str(
            output_directory
        ),
    }


def _expect_orchestrator_error(
    case_name: str,
    expected_status: RunStatus,
    action: Callable[
        [],
        Any,
    ],
) -> dict[str, Any]:
    try:
        action()

    except EDKOrchestratorError as error:
        _require(
            (
                error.status
                is expected_status
            ),
            (
                f"{case_name} returned "
                f"{error.status.value}, "
                "expected "
                f"{expected_status.value}."
            ),
        )

        return {
            "status": "PASS",
            "expected_error": (
                expected_status.value
            ),
            "message": str(
                error
            ),
        }

    raise AssertionError(
        (
            f"{case_name} did not raise "
            f"{expected_status.value}."
        )
    )


def run_negative_cases(
    base_directory: Path,
) -> dict[str, Any]:
    results: dict[
        str,
        Any,
    ] = {}

    missing_stage_directory = (
        base_directory
        / "missing_stage"
    )

    missing_stage_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    missing_stage_orchestrator = (
        build_orchestrator(
            missing_stage_directory,
            registry=build_registry(
                omit_stage=(
                    "wave_genetics"
                )
            ),
        )
    )

    results[
        "missing_stage"
    ] = _expect_orchestrator_error(
        "missing_stage",
        RunStatus.MANDATORY_STAGE_MISSING,
        missing_stage_orchestrator.run_tact,
    )

    missing_t_int_directory = (
        base_directory
        / "missing_t_int"
    )

    missing_t_int_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_without_t_int = (
        build_initial_state()
    )

    state_without_t_int.T_int = None

    state_without_t_int.field_provenance.pop(
        "T_int",
        None,
    )

    missing_t_int_orchestrator = (
        build_orchestrator(
            missing_t_int_directory,
            registry=build_registry(
                omit_t_int=True
            ),
            initial_state=(
                state_without_t_int
            ),
        )
    )

    results[
        "missing_t_int"
    ] = _expect_orchestrator_error(
        "missing_t_int",
        RunStatus.T_INT_MISSING,
        missing_t_int_orchestrator.run_tact,
    )

    missing_j_flux_directory = (
        base_directory
        / "missing_j_flux"
    )

    missing_j_flux_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    state_without_j_flux = (
        build_initial_state()
    )

    state_without_j_flux.J_flux = None

    state_without_j_flux.field_provenance.pop(
        "J_flux",
        None,
    )

    missing_j_flux_orchestrator = (
        build_orchestrator(
            missing_j_flux_directory,
            registry=build_registry(
                omit_j_flux=True
            ),
            initial_state=(
                state_without_j_flux
            ),
        )
    )

    results[
        "missing_j_flux"
    ] = _expect_orchestrator_error(
        "missing_j_flux",
        RunStatus.J_FLUX_MISSING,
        missing_j_flux_orchestrator.run_tact,
    )

    backend_directory = (
        base_directory
        / "backend_mismatch"
    )

    backend_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    backend_orchestrator = (
        build_orchestrator(
            backend_directory,
            registry=build_registry(
                backend_mismatch=True
            ),
        )
    )

    results[
        "backend_mismatch"
    ] = _expect_orchestrator_error(
        "backend_mismatch",
        RunStatus.BACKEND_MISMATCH,
        backend_orchestrator.run_tact,
    )

    non_finite_directory = (
        base_directory
        / "non_finite"
    )

    non_finite_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    non_finite_orchestrator = (
        build_orchestrator(
            non_finite_directory,
            registry=build_registry(
                non_finite_solar=True
            ),
        )
    )

    results[
        "non_finite"
    ] = _expect_orchestrator_error(
        "non_finite",
        RunStatus.NON_FINITE_STATE,
        non_finite_orchestrator.run_tact,
    )

    phi_failure_directory = (
        base_directory
        / "phi_failure"
    )

    phi_failure_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    phi_failure_orchestrator = (
        build_orchestrator(
            phi_failure_directory,
            phi=(
                failing_phi_operator
            ),
        )
    )

    results[
        "phi_failure"
    ] = _expect_orchestrator_error(
        "phi_failure",
        RunStatus.RECURSIVE_UPDATE_FAILED,
        phi_failure_orchestrator.run_tact,
    )

    return results


def run_diagnostics_case(
    output_directory: Path,
    *,
    dt: float,
) -> dict[str, Any]:
    try:
        try:
            from .hierarchical_diagnostics import (
                EDKHierarchicalDiagnostics,
            )

        except ImportError:
            from hierarchical_diagnostics import (
                EDKHierarchicalDiagnostics,
            )

    except ImportError as error:
        raise RuntimeError(
            (
                "hierarchical_diagnostics.py "
                "could not be imported."
            )
        ) from error

    source_directory = (
        output_directory
        / "source"
    )

    diagnostics_directory = (
        output_directory
        / "diagnostics"
    )

    source_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    diagnostics_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    orchestrator = build_orchestrator(
        source_directory,
        dt=dt,
    )

    orchestrator.run(
        1
    )

    diagnostics = (
        EDKHierarchicalDiagnostics(
            input_directory=(
                source_directory
            ),
            output_directory=(
                diagnostics_directory
            ),
            strict=False,
        )
    )

    summary = diagnostics.run(
        create_plots=True,
        create_report=True,
    )

    summary_payload = (
        summary.to_dict()
    )

    _require(
        (
            int(
                summary_payload[
                    "record_count"
                ]
            )
            == 1
        ),
        (
            "Diagnostics did not load "
            "the expected tact record."
        ),
    )

    _require(
        (
            int(
                summary_payload[
                    "issue_counts"
                ].get(
                    "ERROR",
                    0,
                )
            )
            == 0
        ),
        (
            "Diagnostics reported "
            "error-level issues in "
            "the valid smoke run."
        ),
    )

    expected_report_files = (
        (
            diagnostics_directory
            / "hierarchical_diagnostics.json"
        ),
        (
            diagnostics_directory
            / "hierarchical_diagnostics.md"
        ),
        (
            diagnostics_directory
            / "dynamic_regime.png"
        ),
        (
            diagnostics_directory
            / "stage_continuity.png"
        ),
        (
            diagnostics_directory
            / "resonance_window_transitions.png"
        ),
    )

    for path in expected_report_files:
        _require(
            path.exists(),
            (
                "Missing diagnostics output: "
                f"{path}"
            ),
        )

        _require(
            (
                path.stat().st_size
                > 0
            ),
            (
                "Empty diagnostics output: "
                f"{path}"
            ),
        )

    return {
        "status": "PASS",
        "summary": (
            summary_payload
        ),
        "issue_count": len(
            diagnostics.issues
        ),
        "output_directory": str(
            diagnostics_directory
        ),
    }


def run_smoke_suite(
    root_directory: Path,
    *,
    tact_count: int,
    dt: float,
    run_negative_tests: bool,
    run_diagnostics: bool,
) -> dict[str, Any]:
    root_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    result: dict[
        str,
        Any,
    ] = {
        "status": "RUNNING",
        "root_directory": str(
            root_directory
        ),
        "success_case": None,
        "negative_cases": None,
        "diagnostics_case": None,
    }

    result[
        "success_case"
    ] = run_success_case(
        root_directory
        / "success",
        tact_count=tact_count,
        dt=dt,
    )

    if run_negative_tests:
        result[
            "negative_cases"
        ] = run_negative_cases(
            root_directory
            / "negative"
        )

    else:
        result[
            "negative_cases"
        ] = {
            "status": "SKIPPED",
        }

    if run_diagnostics:
        result[
            "diagnostics_case"
        ] = run_diagnostics_case(
            root_directory
            / "diagnostics_integration",
            dt=dt,
        )

    else:
        result[
            "diagnostics_case"
        ] = {
            "status": "SKIPPED",
        }

    result[
        "status"
    ] = "PASS"

    result_path = (
        root_directory
        / "smoke_test_summary.json"
    )

    result_path.write_text(
        (
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ),
        encoding="utf-8",
    )

    return result


def main(
) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete EDK "
            "hierarchical orchestrator "
            "smoke suite."
        )
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--tacts",
        type=int,
        default=None,
        help=(
            "Number of tact-by-tact "
            "hierarchical intervals."
        ),
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help=(
            "Compatibility alias for --tacts. "
            "If --tacts is provided, --tacts "
            "takes priority."
        ),
    )

    parser.add_argument(
        "--dt",
        type=float,
        default=0.01,
    )

    parser.add_argument(
        "--skip-negative-tests",
        action="store_true",
    )

    parser.add_argument(
        "--skip-diagnostics",
        action="store_true",
    )

    parser.add_argument(
        "--keep-temporary-output",
        action="store_true",
    )

    arguments = parser.parse_args()

    total_tacts = (
        arguments.tacts
        if arguments.tacts is not None
        else arguments.steps
        if arguments.steps is not None
        else 3
    )

    if total_tacts <= 0:
        raise ValueError(
            (
                "--tacts must be "
                "greater than zero."
            )
        )

    if (
        not math.isfinite(
            arguments.dt
        )
        or arguments.dt <= 0.0
    ):
        raise ValueError(
            (
                "--dt must be a finite "
                "positive value."
            )
        )

    temporary_directory: (
        tempfile.TemporaryDirectory[
            str
        ]
        | None
    ) = None

    if arguments.output_dir is None:
        temporary_directory = (
            tempfile.TemporaryDirectory(
                prefix=(
                    "edk_hierarchical_"
                    "smoke_test_"
                )
            )
        )

        root_directory = Path(
            temporary_directory.name
        )

    else:
        root_directory = (
            arguments
            .output_dir
            .resolve()
        )

        if (
            root_directory.exists()
            and any(
                root_directory.iterdir()
            )
        ):
            raise FileExistsError(
                (
                    "--output-dir must be "
                    "absent or empty to prevent "
                    "destructive replacement "
                    "of existing data."
                )
            )

        root_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    try:
        result = run_smoke_suite(
            root_directory,
            tact_count=(
                total_tacts
            ),
            dt=(
                arguments.dt
            ),
            run_negative_tests=(
                not arguments
                .skip_negative_tests
            ),
            run_diagnostics=(
                not arguments
                .skip_diagnostics
            ),
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )

        if (
            temporary_directory
            is not None
            and arguments
            .keep_temporary_output
        ):
            retained_directory = (
                Path.cwd()
                / (
                    "edk_hierarchical_"
                    "smoke_output"
                )
            )

            if retained_directory.exists():
                shutil.rmtree(
                    retained_directory
                )

            shutil.copytree(
                root_directory,
                retained_directory,
            )

            print(
                json.dumps(
                    {
                        "retained_output_directory": str(
                            retained_directory
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )

    finally:
        if (
            temporary_directory
            is not None
        ):
            temporary_directory.cleanup()


if __name__ == "__main__":
    main()
