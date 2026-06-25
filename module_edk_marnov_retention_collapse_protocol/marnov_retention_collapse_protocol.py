from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal, Sequence

import numpy as np

try:
    from module_edk_gpu_mean_field_phase_engine import (
        EDKGPUMeanFieldPhaseEngine,
        MeanFieldPhaseConfig,
    )
except ImportError:
    try:
        from edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
        )
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]

        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        from module_edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
        )


PressureSchedule = Literal[
    "step",
    "linear_ramp",
    "smooth_ramp",
    "external_sequence",
]

ExposureRecoveryMode = Literal[
    "persistent",
    "decaying",
]

CouplingQuenchMode = Literal[
    "instantaneous",
    "exponential",
]

CollapseLogic = Literal[
    "any",
    "all",
]


@dataclass(frozen=True)
class MarnovRetentionCollapseConfig:
    formation_maximum_tacts: int = 4000
    formation_confirmation_tacts: int = 20
    retained_verification_tacts: int = 20
    critical_loading_maximum_tacts: int = 4000
    maximum_post_unlock_tacts: int = 4000
    minimum_post_unlock_tacts: int = 1

    R_form_min: float = 0.80
    phase_amplitude_form_min: float = 0.80
    phase_velocity_dispersion_form_max: float = 0.50
    amplitude_dispersion_form_max: float = 0.25

    coherence_weight_R: float = 0.35
    coherence_weight_phase_amplitude: float = 0.35
    coherence_weight_phase_velocity: float = 0.15
    coherence_weight_amplitude: float = 0.15

    phase_velocity_reference: float = 1.0
    amplitude_dispersion_reference: float = 0.10

    retained_boundary_tolerance: float = 0.02

    pressure_schedule: PressureSchedule = "step"
    pressure_hold: float = 0.05
    pressure_collapse: float = 1.0
    pressure_ramp_rate: float = 1.0

    delay_base_tau_0: float = 0.20
    pressure_velocity_coefficient_mu: float = 1.0
    delay_regularization_epsilon: float = 1.0e-9
    minimum_delay_tau: float = 1.0e-6

    critical_exposure_threshold: float = 1.0
    exposure_recovery_mode: ExposureRecoveryMode = "decaying"
    exposure_recovery_rate: float = 0.25

    coupling_quench_mode: CouplingQuenchMode = "exponential"
    coupling_floor: float = 0.10
    coupling_quench_tau: float = 0.05

    post_unlock_phase_noise_multiplier: float = 4.0
    post_unlock_frequency_dispersion_multiplier: float = 8.0
    post_unlock_amplitude_decay_scale: float = 2.0

    phase_order_collapse_threshold: float = 0.10
    phase_order_collapse_fraction: float = 0.50
    phase_amplitude_collapse_threshold: float = 0.10
    phase_velocity_dispersion_collapse_threshold: float = 5.0
    collapse_logic: CollapseLogic = "any"

    log_every: int = 1
    field_every: int = 0

    def validate(
        self,
        initial_coupling_strength: float,
    ) -> None:
        integer_fields = {
            "formation_maximum_tacts": self.formation_maximum_tacts,
            "formation_confirmation_tacts": (
                self.formation_confirmation_tacts
            ),
            "retained_verification_tacts": (
                self.retained_verification_tacts
            ),
            "critical_loading_maximum_tacts": (
                self.critical_loading_maximum_tacts
            ),
            "maximum_post_unlock_tacts": (
                self.maximum_post_unlock_tacts
            ),
            "minimum_post_unlock_tacts": (
                self.minimum_post_unlock_tacts
            ),
        }

        for name, value in integer_fields.items():
            if value < 1:
                raise ValueError(
                    f"{name} must be at least 1."
                )

        if (
            self.formation_confirmation_tacts
            > self.formation_maximum_tacts
        ):
            raise ValueError(
                "formation_confirmation_tacts exceeds "
                "formation_maximum_tacts."
            )

        bounded_fields = {
            "R_form_min": self.R_form_min,
            "phase_amplitude_form_min": (
                self.phase_amplitude_form_min
            ),
            "pressure_hold": self.pressure_hold,
            "pressure_collapse": self.pressure_collapse,
            "phase_order_collapse_threshold": (
                self.phase_order_collapse_threshold
            ),
            "phase_order_collapse_fraction": (
                self.phase_order_collapse_fraction
            ),
            "phase_amplitude_collapse_threshold": (
                self.phase_amplitude_collapse_threshold
            ),
        }

        for name, value in bounded_fields.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be within [0, 1]."
                )

        non_negative_fields = {
            "phase_velocity_dispersion_form_max": (
                self.phase_velocity_dispersion_form_max
            ),
            "amplitude_dispersion_form_max": (
                self.amplitude_dispersion_form_max
            ),
            "phase_velocity_dispersion_collapse_threshold": (
                self.phase_velocity_dispersion_collapse_threshold
            ),
            "retained_boundary_tolerance": (
                self.retained_boundary_tolerance
            ),
            "pressure_ramp_rate": self.pressure_ramp_rate,
            "exposure_recovery_rate": (
                self.exposure_recovery_rate
            ),
            "coupling_floor": self.coupling_floor,
            "post_unlock_phase_noise_multiplier": (
                self.post_unlock_phase_noise_multiplier
            ),
            "post_unlock_frequency_dispersion_multiplier": (
                self.post_unlock_frequency_dispersion_multiplier
            ),
            "post_unlock_amplitude_decay_scale": (
                self.post_unlock_amplitude_decay_scale
            ),
        }

        for name, value in non_negative_fields.items():
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    f"{name} must be finite and non-negative."
                )

        positive_fields = {
            "phase_velocity_reference": (
                self.phase_velocity_reference
            ),
            "amplitude_dispersion_reference": (
                self.amplitude_dispersion_reference
            ),
            "delay_base_tau_0": self.delay_base_tau_0,
            "pressure_velocity_coefficient_mu": (
                self.pressure_velocity_coefficient_mu
            ),
            "delay_regularization_epsilon": (
                self.delay_regularization_epsilon
            ),
            "minimum_delay_tau": self.minimum_delay_tau,
            "critical_exposure_threshold": (
                self.critical_exposure_threshold
            ),
            "coupling_quench_tau": (
                self.coupling_quench_tau
            ),
        }

        for name, value in positive_fields.items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(
                    f"{name} must be a positive finite value."
                )

        weights = (
            self.coherence_weight_R,
            self.coherence_weight_phase_amplitude,
            self.coherence_weight_phase_velocity,
            self.coherence_weight_amplitude,
        )

        if any(
            weight < 0.0
            for weight in weights
        ):
            raise ValueError(
                "Coherence-proxy weights must be non-negative."
            )

        if not math.isclose(
            sum(weights),
            1.0,
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        ):
            raise ValueError(
                "Coherence-proxy weights must sum to 1."
            )

        if (
            self.coupling_floor
            > initial_coupling_strength
        ):
            raise ValueError(
                "coupling_floor exceeds the initial "
                "coupling strength."
            )

        if self.pressure_schedule not in {
            "step",
            "linear_ramp",
            "smooth_ramp",
            "external_sequence",
        }:
            raise ValueError(
                "Unsupported pressure_schedule."
            )

        if self.exposure_recovery_mode not in {
            "persistent",
            "decaying",
        }:
            raise ValueError(
                "Unsupported exposure_recovery_mode."
            )

        if self.coupling_quench_mode not in {
            "instantaneous",
            "exponential",
        }:
            raise ValueError(
                "Unsupported coupling_quench_mode."
            )

        if self.collapse_logic not in {
            "any",
            "all",
        }:
            raise ValueError(
                "collapse_logic must be 'any' or 'all'."
            )

        if self.log_every < 0:
            raise ValueError(
                "log_every must be non-negative."
            )

        if self.field_every < 0:
            raise ValueError(
                "field_every must be non-negative."
            )


class EDKMarnovRetentionCollapseProtocol:
    INITIALIZED = "INITIALIZED"
    FORMING_ATTRACTOR = "FORMING_ATTRACTOR"
    RETAINED_ATTRACTOR = "RETAINED_ATTRACTOR"
    CRITICAL_APPROACH = "CRITICAL_APPROACH"
    CRITICAL_EXPOSURE = "CRITICAL_EXPOSURE"
    PHASE_NODE_UNLOCKED = "PHASE_NODE_UNLOCKED"
    COLLAPSE_ACTIVE = "COLLAPSE_ACTIVE"
    DEGRADED_PHASE_REGIME = "DEGRADED_PHASE_REGIME"
    COLLAPSE_COMPLETED = "COLLAPSE_COMPLETED"
    COLLAPSE_NOT_REACHED = "COLLAPSE_NOT_REACHED"

    ATTRACTOR_NOT_FORMED = "ATTRACTOR_NOT_FORMED"
    ATTRACTOR_NOT_VERIFIED = "ATTRACTOR_NOT_VERIFIED"
    CRITICAL_BOUNDARY_NOT_REACHED = (
        "CRITICAL_BOUNDARY_NOT_REACHED"
    )
    UNLOCK_NOT_TRIGGERED = "UNLOCK_NOT_TRIGGERED"
    NUMERICAL_INSTABILITY = "NUMERICAL_INSTABILITY"
    NON_FINITE_STATE = "NON_FINITE_STATE"

    EDS_RETAINED = "EDS_RETAINED"
    EDC_CRITICAL = "EDC_CRITICAL"
    DEGRADATION = "DEGRADATION"

    def __init__(
        self,
        engine: EDKGPUMeanFieldPhaseEngine,
        config: MarnovRetentionCollapseConfig | None = None,
    ) -> None:
        self.engine = engine

        self.config = (
            config
            if config is not None
            else MarnovRetentionCollapseConfig()
        )

        self.initial_coupling_K = float(
            engine.K
        )

        self.config.validate(
            self.initial_coupling_K
        )

        self.base_natural_frequencies = (
            engine.natural_frequencies.copy()
        )

        self.effective_natural_frequencies = (
            self.base_natural_frequencies.copy()
        )

        self.protocol_state = self.INITIALIZED
        self.final_status = self.INITIALIZED
        self.retention_regime = self.EDS_RETAINED

        self.C_proxy_t = 0.0

        self.external_pressure_P_ext = float(
            self.config.pressure_hold
        )

        self.retention_margin = 0.0
        self.pressure_excess = 0.0

        self.instantaneous_delay_tau = float(
            self.config.delay_base_tau_0
        )

        self.critical_exposure = 0.0

        self.effective_coupling_K = (
            self.initial_coupling_K
        )

        self.effective_phase_noise_strength = float(
            engine.config.phase_noise_strength
        )

        self.effective_frequency_dispersion_multiplier = 1.0
        self.effective_amplitude_decay_rate = 0.0

        self.attractor_formed = False
        self.attractor_verified = False
        self.phase_node_unlocked = False
        self.collapse_detected = False

        self.formation_tact: int | None = None
        self.formation_time: float | None = None

        self.unlock_tact: int | None = None
        self.unlock_time: float | None = None

        self.collapse_tact: int | None = None
        self.collapse_time: float | None = None

        self.first_critical_tact: int | None = None
        self.first_degradation_tact: int | None = None

        self.R_unlock: float | None = None

        self.phase_amplitude_order_unlock: (
            float
            | None
        ) = None

        self.amplitude_mean_unlock: float | None = None

        self.amplitude_dispersion_unlock: (
            float
            | None
        ) = None

        self.C_proxy_unlock: float | None = None
        self.P_ext_unlock: float | None = None

        self.retention_margin_unlock: (
            float
            | None
        ) = None

        self.tau_delay_unlock: float | None = None

        self.phase_order_half_life: (
            float
            | None
        ) = None

        self.amplitude_regime_half_life: (
            float
            | None
        ) = None

        self.attractor_collapse_duration: (
            float
            | None
        ) = None

        self._formation_consecutive_tacts = 0
        self._post_unlock_tacts = 0
        self._last_transition_event: str | None = None

        self.history: list[dict[str, Any]] = []
        self.transition_events: list[dict[str, Any]] = []

        self._refresh_protocol_observables(
            self.config.pressure_hold
        )

    @staticmethod
    def _validate_dt(
        dt: float,
    ) -> None:
        if (
            not math.isfinite(dt)
            or dt <= 0.0
        ):
            raise ValueError(
                "dt must be a positive finite value."
            )

    @staticmethod
    def _validate_forcing(
        density: float,
        phase: float,
    ) -> None:
        if not math.isfinite(density):
            raise ValueError(
                "Forcing density must be finite."
            )

        if not math.isfinite(phase):
            raise ValueError(
                "Forcing phase must be finite."
            )

    @staticmethod
    def _validate_pressure(
        pressure: float,
    ) -> None:
        if not math.isfinite(pressure):
            raise ValueError(
                "external_pressure must be finite."
            )

        if not 0.0 <= pressure <= 1.0:
            raise ValueError(
                "external_pressure must be within [0, 1]."
            )

    def _classify_retention_regime(
        self,
        margin: float,
    ) -> str:
        tolerance = (
            self.config.retained_boundary_tolerance
        )

        if margin > tolerance:
            return self.EDS_RETAINED

        if abs(margin) <= tolerance:
            return self.EDC_CRITICAL

        return self.DEGRADATION

    def _calculate_coherence_proxy(
        self,
        metrics: dict[str, Any],
    ) -> float:
        velocity_stability = 1.0 / (
            1.0
            + float(
                metrics[
                    "phase_velocity_dispersion"
                ]
            )
            / self.config.phase_velocity_reference
        )

        amplitude_stability = 1.0 / (
            1.0
            + float(
                metrics[
                    "amplitude_dispersion"
                ]
            )
            / self.config.amplitude_dispersion_reference
        )

        value = (
            self.config.coherence_weight_R
            * float(
                metrics[
                    "R_t_phase_order"
                ]
            )
            + self.config.coherence_weight_phase_amplitude
            * float(
                metrics[
                    "phase_amplitude_order_proxy"
                ]
            )
            + self.config.coherence_weight_phase_velocity
            * velocity_stability
            + self.config.coherence_weight_amplitude
            * amplitude_stability
        )

        return float(
            np.clip(
                value,
                0.0,
                1.0,
            )
        )

    def _calculate_delay_tau(
        self,
        pressure_excess: float,
    ) -> float:
        velocity = (
            self.config.pressure_velocity_coefficient_mu
            * max(
                pressure_excess,
                0.0,
            )
        )

        tau = (
            self.config.delay_base_tau_0
            / (
                velocity
                + self.config.delay_regularization_epsilon
            )
            ** (
                1.0
                / 3.0
            )
        )

        return max(
            tau,
            self.config.minimum_delay_tau,
        )

    def _refresh_protocol_observables(
        self,
        pressure: float,
    ) -> dict[str, Any]:
        self._validate_pressure(
            pressure
        )

        metrics = self.engine.get_metrics()

        self.C_proxy_t = (
            self._calculate_coherence_proxy(
                metrics
            )
        )

        self.external_pressure_P_ext = float(
            pressure
        )

        self.retention_margin = (
            self.C_proxy_t
            - self.external_pressure_P_ext
        )

        self.pressure_excess = max(
            self.external_pressure_P_ext
            - self.C_proxy_t,
            0.0,
        )

        self.instantaneous_delay_tau = (
            self._calculate_delay_tau(
                self.pressure_excess
            )
        )

        self.retention_regime = (
            self._classify_retention_regime(
                self.retention_margin
            )
        )

        return metrics

    def _formation_criteria_met(
        self,
        metrics: dict[str, Any],
    ) -> bool:
        return bool(
            float(
                metrics[
                    "R_t_phase_order"
                ]
            )
            >= self.config.R_form_min
            and float(
                metrics[
                    "phase_amplitude_order_proxy"
                ]
            )
            >= self.config.phase_amplitude_form_min
            and float(
                metrics[
                    "phase_velocity_dispersion"
                ]
            )
            <= self.config.phase_velocity_dispersion_form_max
            and float(
                metrics[
                    "amplitude_dispersion"
                ]
            )
            <= self.config.amplitude_dispersion_form_max
            and self.retention_margin
            > self.config.retained_boundary_tolerance
        )

    def _pressure_for_loading_tact(
        self,
        loading_tact: int,
        dt: float,
        external_sequence: Sequence[float] | None,
    ) -> float:
        schedule = self.config.pressure_schedule

        if schedule == "step":
            pressure = (
                self.config.pressure_collapse
            )

        elif schedule == "linear_ramp":
            delta = (
                self.config.pressure_collapse
                - self.config.pressure_hold
            )

            direction = (
                1.0
                if delta >= 0.0
                else -1.0
            )

            candidate = (
                self.config.pressure_hold
                + direction
                * self.config.pressure_ramp_rate
                * loading_tact
                * dt
            )

            if direction > 0.0:
                pressure = min(
                    candidate,
                    self.config.pressure_collapse,
                )
            else:
                pressure = max(
                    candidate,
                    self.config.pressure_collapse,
                )

        elif schedule == "smooth_ramp":
            fraction = (
                1.0
                - math.exp(
                    -self.config.pressure_ramp_rate
                    * loading_tact
                    * dt
                )
            )

            pressure = (
                self.config.pressure_hold
                + (
                    self.config.pressure_collapse
                    - self.config.pressure_hold
                )
                * fraction
            )

        elif schedule == "external_sequence":
            if (
                external_sequence is None
                or len(
                    external_sequence
                )
                == 0
            ):
                raise ValueError(
                    "A non-empty external pressure "
                    "sequence is required."
                )

            pressure = float(
                external_sequence[
                    min(
                        loading_tact - 1,
                        len(
                            external_sequence
                        )
                        - 1,
                    )
                ]
            )

        else:
            raise RuntimeError(
                "Unsupported pressure schedule."
            )

        self._validate_pressure(
            pressure
        )

        return float(
            pressure
        )

    def _update_effective_coupling(
        self,
        dt: float,
    ) -> None:
        if not self.phase_node_unlocked:
            self.effective_coupling_K = (
                self.initial_coupling_K
            )

        elif (
            self.config.coupling_quench_mode
            == "instantaneous"
        ):
            self.effective_coupling_K = (
                self.config.coupling_floor
            )

        else:
            self.effective_coupling_K = (
                self.config.coupling_floor
                + (
                    self.effective_coupling_K
                    - self.config.coupling_floor
                )
                * math.exp(
                    -dt
                    / self.config.coupling_quench_tau
                )
            )

        self.effective_coupling_K = max(
            self.config.coupling_floor,
            min(
                self.effective_coupling_K,
                self.initial_coupling_K,
            ),
        )

        self.engine.set_coupling_strength(
            self.effective_coupling_K
        )

    def _prepare_effective_frequencies(
        self,
    ) -> Any:
        xp = self.engine.xp

        multiplier = (
            self.config.post_unlock_frequency_dispersion_multiplier
            if self.phase_node_unlocked
            else 1.0
        )

        self.effective_frequency_dispersion_multiplier = float(
            multiplier
        )

        mean_frequency = xp.mean(
            self.base_natural_frequencies
        )

        self.effective_natural_frequencies = (
            mean_frequency
            + multiplier
            * (
                self.base_natural_frequencies
                - mean_frequency
            )
        ).astype(
            self.engine.dtype,
            copy=False,
        )

        return self.effective_natural_frequencies

    def _effective_phase_noise(
        self,
    ) -> float:
        multiplier = (
            self.config.post_unlock_phase_noise_multiplier
            if self.phase_node_unlocked
            else 1.0
        )

        self.effective_phase_noise_strength = (
            float(
                self.engine.config.phase_noise_strength
            )
            * multiplier
        )

        return self.effective_phase_noise_strength

    def _apply_post_unlock_amplitude_decay(
        self,
        dt: float,
    ) -> None:
        if not self.phase_node_unlocked:
            self.effective_amplitude_decay_rate = 0.0
            return

        rate = (
            self.config.post_unlock_amplitude_decay_scale
            / max(
                self.instantaneous_delay_tau,
                self.config.minimum_delay_tau,
            )
        )

        self.effective_amplitude_decay_rate = float(
            rate
        )

        amplitude_floor = float(
            self.engine.config.amplitude_minimum
        )

        previous_amplitudes = (
            self.engine.amplitudes.copy()
        )

        values = (
            amplitude_floor
            + (
                self.engine.amplitudes
                - amplitude_floor
            )
            * math.exp(
                -rate
                * dt
            )
        )

        self.engine.amplitudes = (
            self.engine.xp.clip(
                values,
                self.engine.config.amplitude_minimum,
                self.engine.config.amplitude_maximum,
            )
            .astype(
                self.engine.dtype,
                copy=False,
            )
        )

        self.engine.amplitude_velocity = (
            self.engine.amplitude_velocity
            + (
                self.engine.amplitudes
                - previous_amplitudes
            )
            / dt
        ).astype(
            self.engine.dtype,
            copy=False,
        )

        self.engine._refresh_diagnostics()

    def _advance_engine(
        self,
        forcing_density: float,
        forcing_phase: float,
        dt: float,
    ) -> dict[str, Any]:
        self._validate_dt(
            dt
        )

        self._validate_forcing(
            forcing_density,
            forcing_phase,
        )

        self._update_effective_coupling(
            dt
        )

        original_config = (
            self.engine.config
        )

        original_frequencies = (
            self.engine.natural_frequencies
        )

        temporary_config = replace(
            original_config,
            phase_noise_strength=(
                self._effective_phase_noise()
            ),
        )

        try:
            self.engine.config = (
                temporary_config
            )

            self.engine.natural_frequencies = (
                self._prepare_effective_frequencies()
            )

            self.engine.process_micro_interval(
                external_forcing_density=(
                    forcing_density
                ),
                external_forcing_phase=(
                    forcing_phase
                ),
                dt=dt,
            )

        finally:
            self.engine.natural_frequencies = (
                original_frequencies
            )

            self.engine.config = (
                original_config
            )

        self._apply_post_unlock_amplitude_decay(
            dt
        )

        return self.engine.get_metrics()

    def _accumulate_critical_exposure(
        self,
        dt: float,
    ) -> None:
        if self.pressure_excess > 0.0:
            self.critical_exposure += (
                dt
                / self.instantaneous_delay_tau
            )

        elif (
            self.config.exposure_recovery_mode
            == "decaying"
        ):
            self.critical_exposure = max(
                0.0,
                self.critical_exposure
                - self.config.exposure_recovery_rate
                * dt,
            )

    def _register_transition(
        self,
        event: str,
    ) -> None:
        self._last_transition_event = event

        self.transition_events.append(
            {
                "event": event,
                "tact_index": int(
                    self.engine.tact_index
                ),
                "simulation_time": float(
                    self.engine.simulation_time
                ),
                "protocol_state": (
                    self.protocol_state
                ),
            }
        )

    def _unlock_phase_node(
        self,
    ) -> None:
        self.phase_node_unlocked = True

        self.unlock_tact = int(
            self.engine.tact_index
        )

        self.unlock_time = float(
            self.engine.simulation_time
        )

        metrics = self.engine.get_metrics()

        self.R_unlock = float(
            metrics[
                "R_t_phase_order"
            ]
        )

        self.phase_amplitude_order_unlock = float(
            metrics[
                "phase_amplitude_order_proxy"
            ]
        )

        self.amplitude_mean_unlock = float(
            metrics[
                "mean_amplitude"
            ]
        )

        self.amplitude_dispersion_unlock = float(
            metrics[
                "amplitude_dispersion"
            ]
        )

        self.C_proxy_unlock = float(
            self.C_proxy_t
        )

        self.P_ext_unlock = float(
            self.external_pressure_P_ext
        )

        self.retention_margin_unlock = float(
            self.retention_margin
        )

        self.tau_delay_unlock = float(
            self.instantaneous_delay_tau
        )

        self.protocol_state = (
            self.PHASE_NODE_UNLOCKED
        )

        self._register_transition(
            self.PHASE_NODE_UNLOCKED
        )

    def _update_half_lives(
        self,
        metrics: dict[str, Any],
    ) -> None:
        if (
            not self.phase_node_unlocked
            or self.unlock_time is None
        ):
            return

        elapsed = float(
            self.engine.simulation_time
            - self.unlock_time
        )

        if (
            self.phase_order_half_life is None
            and self.R_unlock is not None
            and float(
                metrics[
                    "R_t_phase_order"
                ]
            )
            <= 0.5
            * self.R_unlock
        ):
            self.phase_order_half_life = (
                elapsed
            )

        if (
            self.amplitude_regime_half_life
            is None
            and self.amplitude_mean_unlock
            is not None
        ):
            amplitude_floor = float(
                self.engine.config.amplitude_minimum
            )

            unlock_distance = max(
                self.amplitude_mean_unlock
                - amplitude_floor,
                0.0,
            )

            current_distance = max(
                float(
                    metrics[
                        "mean_amplitude"
                    ]
                )
                - amplitude_floor,
                0.0,
            )

            if (
                current_distance
                <= 0.5
                * unlock_distance
            ):
                self.amplitude_regime_half_life = (
                    elapsed
                )

    def _collapse_criteria_met(
        self,
        metrics: dict[str, Any],
    ) -> bool:
        if self.R_unlock is None:
            return False

        phase_limit = max(
            self.config.phase_order_collapse_threshold,
            self.config.phase_order_collapse_fraction
            * self.R_unlock,
        )

        checks = (
            float(
                metrics[
                    "R_t_phase_order"
                ]
            )
            <= phase_limit,
            float(
                metrics[
                    "phase_amplitude_order_proxy"
                ]
            )
            <= self.config.phase_amplitude_collapse_threshold,
            float(
                metrics[
                    "phase_velocity_dispersion"
                ]
            )
            >= self.config.phase_velocity_dispersion_collapse_threshold,
        )

        if self.config.collapse_logic == "all":
            return all(
                checks
            )

        return any(
            checks
        )

    def _validate_numerical_state(
        self,
    ) -> None:
        xp = self.engine.xp

        backend_checks = xp.stack(
            (
                xp.all(
                    xp.isfinite(
                        self.engine.phases
                    )
                ),
                xp.all(
                    xp.isfinite(
                        self.engine.amplitudes
                    )
                ),
                xp.all(
                    xp.isfinite(
                        self.engine.phase_velocity
                    )
                ),
                xp.all(
                    xp.isfinite(
                        self.engine.amplitude_velocity
                    )
                ),
                xp.all(
                    xp.isfinite(
                        self.engine.natural_frequencies
                    )
                ),
                xp.min(
                    self.engine.phases
                ),
                xp.max(
                    self.engine.phases
                ),
                xp.max(
                    xp.abs(
                        self.engine.natural_frequencies
                        - self.base_natural_frequencies
                    )
                ),
            )
        )

        values = self.engine._to_host(
            backend_checks
        )

        if not np.all(
            values[:5].astype(
                bool
            )
        ):
            self.protocol_state = (
                self.NON_FINITE_STATE
            )

            self.final_status = (
                self.NON_FINITE_STATE
            )

            raise FloatingPointError(
                "Non-finite values detected "
                "in the active state arrays."
            )

        minimum_phase = float(
            values[5]
        )

        maximum_phase = float(
            values[6]
        )

        if (
            minimum_phase
            < -math.pi
            - 1.0e-6
            or maximum_phase
            >= math.pi
            + 1.0e-6
        ):
            self.protocol_state = (
                self.NUMERICAL_INSTABILITY
            )

            self.final_status = (
                self.NUMERICAL_INSTABILITY
            )

            raise FloatingPointError(
                "Phase wrapping left [-pi, pi)."
            )

        tolerance = (
            1.0e-6
            if self.engine.config.dtype
            == "float32"
            else 1.0e-12
        )

        if float(
            values[7]
        ) > tolerance:
            self.protocol_state = (
                self.NUMERICAL_INSTABILITY
            )

            self.final_status = (
                self.NUMERICAL_INSTABILITY
            )

            raise FloatingPointError(
                "Base natural frequencies changed "
                "during the protocol."
            )

    def get_metrics(
        self,
    ) -> dict[str, Any]:
        metrics = dict(
            self.engine.get_metrics()
        )

        metrics.update(
            {
                "protocol_state": (
                    self.protocol_state
                ),
                "final_status": (
                    self.final_status
                ),
                "retention_regime": (
                    self.retention_regime
                ),
                "C_proxy_t": (
                    self.C_proxy_t
                ),
                "external_pressure_P_ext": (
                    self.external_pressure_P_ext
                ),
                "retention_margin": (
                    self.retention_margin
                ),
                "pressure_excess": (
                    self.pressure_excess
                ),
                "instantaneous_delay_tau": (
                    self.instantaneous_delay_tau
                ),
                "critical_exposure": (
                    self.critical_exposure
                ),
                "critical_exposure_threshold": (
                    self.config.critical_exposure_threshold
                ),
                "initial_coupling_K": (
                    self.initial_coupling_K
                ),
                "effective_coupling_K": (
                    self.effective_coupling_K
                ),
                "coupling_floor_K": (
                    self.config.coupling_floor
                ),
                "effective_phase_noise_strength": (
                    self.effective_phase_noise_strength
                ),
                "effective_frequency_dispersion_multiplier": (
                    self.effective_frequency_dispersion_multiplier
                ),
                "effective_amplitude_decay_rate": (
                    self.effective_amplitude_decay_rate
                ),
                "attractor_formed": (
                    self.attractor_formed
                ),
                "attractor_verified": (
                    self.attractor_verified
                ),
                "phase_node_unlocked": (
                    self.phase_node_unlocked
                ),
                "collapse_detected": (
                    self.collapse_detected
                ),
                "formation_tact": (
                    self.formation_tact
                ),
                "formation_time": (
                    self.formation_time
                ),
                "unlock_tact": (
                    self.unlock_tact
                ),
                "unlock_time": (
                    self.unlock_time
                ),
                "collapse_tact": (
                    self.collapse_tact
                ),
                "collapse_time": (
                    self.collapse_time
                ),
                "first_critical_tact": (
                    self.first_critical_tact
                ),
                "first_degradation_tact": (
                    self.first_degradation_tact
                ),
                "phase_order_half_life": (
                    self.phase_order_half_life
                ),
                "amplitude_regime_half_life": (
                    self.amplitude_regime_half_life
                ),
                "attractor_collapse_duration": (
                    self.attractor_collapse_duration
                ),
                "transition_event": (
                    self._last_transition_event
                ),
            }
        )

        return metrics

    def export_field_snapshot(
        self,
    ) -> dict[str, np.ndarray]:
        snapshot = (
            self.engine.export_field_snapshot()
        )

        snapshot[
            "effective_natural_frequencies"
        ] = (
            self.engine._to_host(
                self.effective_natural_frequencies
            )
            .copy()
        )

        return snapshot

    def _record_tact(
        self,
        logger: EDKMarnovProtocolLogger | None,
        force_log: bool = False,
    ) -> dict[str, Any]:
        self._validate_numerical_state()

        metrics = self.get_metrics()

        self.history.append(
            dict(
                metrics
            )
        )

        if logger is not None:
            tact = int(
                self.engine.tact_index
            )

            should_log = (
                force_log
                or (
                    self.config.log_every > 0
                    and tact
                    % self.config.log_every
                    == 0
                )
            )

            include_field = (
                self.config.field_every > 0
                and tact
                % self.config.field_every
                == 0
            )

            if (
                should_log
                or include_field
            ):
                logger.log_step(
                    self,
                    include_field=(
                        include_field
                    ),
                )

        self._last_transition_event = None

        return metrics

    def run_protocol(
        self,
        dt: float,
        hold_forcing_density: float,
        hold_forcing_phase: float,
        collapse_forcing_density: float = 0.0,
        collapse_forcing_phase: float = 0.0,
        logger: EDKMarnovProtocolLogger | None = None,
        external_pressure_sequence: Sequence[float] | None = None,
    ) -> dict[str, Any]:
        self._validate_dt(
            dt
        )

        self._validate_forcing(
            hold_forcing_density,
            hold_forcing_phase,
        )

        self._validate_forcing(
            collapse_forcing_density,
            collapse_forcing_phase,
        )

        self.protocol_state = (
            self.FORMING_ATTRACTOR
        )

        self.final_status = (
            self.FORMING_ATTRACTOR
        )

        for _ in range(
            self.config.formation_maximum_tacts
        ):
            metrics = self._advance_engine(
                hold_forcing_density,
                hold_forcing_phase,
                dt,
            )

            self._refresh_protocol_observables(
                self.config.pressure_hold
            )

            if self._formation_criteria_met(
                metrics
            ):
                self._formation_consecutive_tacts += 1
            else:
                self._formation_consecutive_tacts = 0

            transition = False

            if (
                self._formation_consecutive_tacts
                >= self.config.formation_confirmation_tacts
            ):
                self.attractor_formed = True

                self.formation_tact = int(
                    self.engine.tact_index
                )

                self.formation_time = float(
                    self.engine.simulation_time
                )

                self.protocol_state = (
                    self.RETAINED_ATTRACTOR
                )

                self.final_status = (
                    self.RETAINED_ATTRACTOR
                )

                self._register_transition(
                    "ATTRACTOR_FORMED"
                )

                transition = True

            self._record_tact(
                logger,
                force_log=(
                    transition
                ),
            )

            if self.attractor_formed:
                break

        if not self.attractor_formed:
            self.protocol_state = (
                self.ATTRACTOR_NOT_FORMED
            )

            self.final_status = (
                self.ATTRACTOR_NOT_FORMED
            )

            self._register_transition(
                self.ATTRACTOR_NOT_FORMED
            )

            self._record_tact(
                logger,
                force_log=True,
            )

            return self.get_summary()

        for index in range(
            self.config.retained_verification_tacts
        ):
            metrics = self._advance_engine(
                hold_forcing_density,
                hold_forcing_phase,
                dt,
            )

            self._refresh_protocol_observables(
                self.config.pressure_hold
            )

            if not self._formation_criteria_met(
                metrics
            ):
                self.protocol_state = (
                    self.ATTRACTOR_NOT_VERIFIED
                )

                self.final_status = (
                    self.ATTRACTOR_NOT_VERIFIED
                )

                self._register_transition(
                    self.ATTRACTOR_NOT_VERIFIED
                )

                self._record_tact(
                    logger,
                    force_log=True,
                )

                return self.get_summary()

            transition = (
                index + 1
                == self.config.retained_verification_tacts
            )

            if transition:
                self.attractor_verified = True

                self.protocol_state = (
                    self.RETAINED_ATTRACTOR
                )

                self.final_status = (
                    self.RETAINED_ATTRACTOR
                )

                self._register_transition(
                    "ATTRACTOR_VERIFIED"
                )

            self._record_tact(
                logger,
                force_log=(
                    transition
                ),
            )

        self.protocol_state = (
            self.CRITICAL_APPROACH
        )

        self.final_status = (
            self.CRITICAL_APPROACH
        )

        for loading_tact in range(
            1,
            self.config.critical_loading_maximum_tacts
            + 1,
        ):
            pressure = (
                self._pressure_for_loading_tact(
                    loading_tact,
                    dt,
                    external_pressure_sequence,
                )
            )

            self._advance_engine(
                collapse_forcing_density,
                collapse_forcing_phase,
                dt,
            )

            self._refresh_protocol_observables(
                pressure
            )

            transition = False

            if (
                self.first_critical_tact is None
                and self.retention_regime
                == self.EDC_CRITICAL
            ):
                self.first_critical_tact = int(
                    self.engine.tact_index
                )

                self._register_transition(
                    "EDC_BOUNDARY_REACHED"
                )

                transition = True

            if (
                self.first_degradation_tact is None
                and self.retention_regime
                == self.DEGRADATION
            ):
                self.first_degradation_tact = int(
                    self.engine.tact_index
                )

                self._register_transition(
                    "DEGRADATION_REGIME_ENTERED"
                )

                transition = True

            self._accumulate_critical_exposure(
                dt
            )

            if self.pressure_excess > 0.0:
                self.protocol_state = (
                    self.CRITICAL_EXPOSURE
                )
            else:
                self.protocol_state = (
                    self.CRITICAL_APPROACH
                )

            if (
                self.critical_exposure
                >= self.config.critical_exposure_threshold
            ):
                self._unlock_phase_node()
                transition = True

            self._record_tact(
                logger,
                force_log=(
                    transition
                ),
            )

            if self.phase_node_unlocked:
                break

        if not self.phase_node_unlocked:
            if (
                self.first_critical_tact is None
                and self.first_degradation_tact
                is None
            ):
                self.final_status = (
                    self.CRITICAL_BOUNDARY_NOT_REACHED
                )
            else:
                self.final_status = (
                    self.UNLOCK_NOT_TRIGGERED
                )

            self.protocol_state = (
                self.final_status
            )

            self._register_transition(
                self.final_status
            )

            self._record_tact(
                logger,
                force_log=True,
            )

            return self.get_summary()

        self.protocol_state = (
            self.COLLAPSE_ACTIVE
        )

        self.final_status = (
            self.COLLAPSE_ACTIVE
        )

        for post_unlock_tact in range(
            1,
            self.config.maximum_post_unlock_tacts
            + 1,
        ):
            self._post_unlock_tacts = (
                post_unlock_tact
            )

            metrics = self._advance_engine(
                collapse_forcing_density,
                collapse_forcing_phase,
                dt,
            )

            self._refresh_protocol_observables(
                self.config.pressure_collapse
            )

            self._update_half_lives(
                metrics
            )

            if (
                self.retention_regime
                == self.DEGRADATION
            ):
                self.protocol_state = (
                    self.DEGRADED_PHASE_REGIME
                )
            else:
                self.protocol_state = (
                    self.COLLAPSE_ACTIVE
                )

            transition = False

            if (
                post_unlock_tact
                >= self.config.minimum_post_unlock_tacts
                and self._collapse_criteria_met(
                    metrics
                )
            ):
                self.collapse_detected = True

                self.collapse_tact = int(
                    self.engine.tact_index
                )

                self.collapse_time = float(
                    self.engine.simulation_time
                )

                if self.unlock_time is not None:
                    self.attractor_collapse_duration = (
                        self.collapse_time
                        - self.unlock_time
                    )

                self.protocol_state = (
                    self.COLLAPSE_COMPLETED
                )

                self.final_status = (
                    self.COLLAPSE_COMPLETED
                )

                self._register_transition(
                    self.COLLAPSE_COMPLETED
                )

                transition = True

            self._record_tact(
                logger,
                force_log=(
                    transition
                ),
            )

            if self.collapse_detected:
                break

        if not self.collapse_detected:
            self.protocol_state = (
                self.COLLAPSE_NOT_REACHED
            )

            self.final_status = (
                self.COLLAPSE_NOT_REACHED
            )

            self._register_transition(
                self.COLLAPSE_NOT_REACHED
            )

            self._record_tact(
                logger,
                force_log=True,
            )

        return self.get_summary()

    def get_summary(
        self,
    ) -> dict[str, Any]:
        return {
            "module": (
                "module_edk_marnov_retention_collapse_protocol"
            ),
            "protocol_class": (
                "EDKMarnovRetentionCollapseProtocol"
            ),
            "final_status": (
                self.final_status
            ),
            "protocol_state": (
                self.protocol_state
            ),
            "engine_backend": (
                self.engine.backend_name
            ),
            "device_id": (
                self.engine.active_device_id
            ),
            "active_domains": (
                self.engine.N
            ),
            "attractor_formed": (
                self.attractor_formed
            ),
            "attractor_verified": (
                self.attractor_verified
            ),
            "phase_node_unlocked": (
                self.phase_node_unlocked
            ),
            "collapse_detected": (
                self.collapse_detected
            ),
            "formation_tact": (
                self.formation_tact
            ),
            "formation_time": (
                self.formation_time
            ),
            "unlock_tact": (
                self.unlock_tact
            ),
            "unlock_time": (
                self.unlock_time
            ),
            "collapse_tact": (
                self.collapse_tact
            ),
            "collapse_time": (
                self.collapse_time
            ),
            "phase_order_half_life": (
                self.phase_order_half_life
            ),
            "amplitude_regime_half_life": (
                self.amplitude_regime_half_life
            ),
            "attractor_collapse_duration": (
                self.attractor_collapse_duration
            ),
            "critical_exposure": (
                self.critical_exposure
            ),
            "history_length": len(
                self.history
            ),
            "transition_events": list(
                self.transition_events
            ),
            "final_metrics": (
                self.get_metrics()
            ),
        }


class EDKMarnovProtocolLogger:
    def __init__(
        self,
        output_dir: str | os.PathLike[str] = (
            "edk_marnov_snapshots"
        ),
    ) -> None:
        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _atomic_json_write(
        path: Path,
        payload: dict[str, Any],
    ) -> None:
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                json.dump(
                    payload,
                    stream,
                    ensure_ascii=False,
                    indent=2,
                )

                stream.flush()

                os.fsync(
                    stream.fileno()
                )

                temporary_path = Path(
                    stream.name
                )

            os.replace(
                temporary_path,
                path,
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()

    @staticmethod
    def _atomic_npz_write(
        path: Path,
        arrays: dict[str, np.ndarray],
    ) -> None:
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w+b",
                dir=path.parent,
                prefix=f".{path.stem}.",
                suffix=".npz.tmp",
                delete=False,
            ) as stream:
                np.savez_compressed(
                    stream,
                    **arrays,
                )

                stream.flush()

                os.fsync(
                    stream.fileno()
                )

                temporary_path = Path(
                    stream.name
                )

            os.replace(
                temporary_path,
                path,
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()

    def log_step(
        self,
        protocol: EDKMarnovRetentionCollapseProtocol,
        include_field: bool = False,
    ) -> tuple[Path, Path | None]:
        tact = int(
            protocol.engine.tact_index
        )

        metrics_path = (
            self.output_dir
            / f"marnov_step_{tact:06d}.json"
        )

        field_path = (
            self.output_dir
            / f"marnov_field_{tact:06d}.npz"
            if include_field
            else None
        )

        payload = {
            "step": tact,
            "module": (
                "module_edk_marnov_retention_collapse_protocol"
            ),
            "protocol_class": (
                "EDKMarnovRetentionCollapseProtocol"
            ),
            "engine_class": (
                "EDKGPUMeanFieldPhaseEngine"
            ),
            "backend": {
                "name": (
                    protocol.engine.backend_name
                ),
                "using_gpu": (
                    protocol.engine.using_gpu
                ),
                "device_id": (
                    protocol.engine.active_device_id
                ),
            },
            "engine_configuration": asdict(
                protocol.engine.config
            ),
            "protocol_configuration": asdict(
                protocol.config
            ),
            "metrics": (
                protocol.get_metrics()
            ),
            "transition_events": list(
                protocol.transition_events
            ),
        }

        self._atomic_json_write(
            metrics_path,
            payload,
        )

        if field_path is not None:
            self._atomic_npz_write(
                field_path,
                protocol.export_field_snapshot(),
            )

        return (
            metrics_path,
            field_path,
        )

    def log_summary(
        self,
        protocol: EDKMarnovRetentionCollapseProtocol,
    ) -> Path:
        summary_path = (
            self.output_dir
            / "marnov_protocol_summary.json"
        )

        self._atomic_json_write(
            summary_path,
            protocol.get_summary(),
        )

        return summary_path


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the EDK Marnov "
            "Retention-Collapse Protocol."
        )
    )

    parser.add_argument(
        "--backend",
        choices=(
            "auto",
            "gpu",
            "cpu",
        ),
        default="auto",
    )

    parser.add_argument(
        "--device-id",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--num-domains",
        type=int,
        default=16384,
    )

    parser.add_argument(
        "--dtype",
        choices=(
            "float32",
            "float64",
        ),
        default="float32",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--dt",
        type=float,
        default=0.005,
    )

    parser.add_argument(
        "--coupling",
        type=float,
        default=120.0,
    )

    parser.add_argument(
        "--coupling-floor",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--coupling-quench-tau",
        type=float,
        default=0.05,
    )

    parser.add_argument(
        "--phase-lag",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--hold-forcing",
        type=float,
        default=6.5,
    )

    parser.add_argument(
        "--hold-forcing-phase",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--collapse-forcing",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--collapse-forcing-phase",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--pressure-hold",
        type=float,
        default=0.05,
    )

    parser.add_argument(
        "--pressure-collapse",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--pressure-schedule",
        choices=(
            "step",
            "linear_ramp",
            "smooth_ramp",
        ),
        default="step",
    )

    parser.add_argument(
        "--pressure-ramp-rate",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--formation-maximum-tacts",
        type=int,
        default=4000,
    )

    parser.add_argument(
        "--formation-confirmation-tacts",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--retained-verification-tacts",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--critical-loading-maximum-tacts",
        type=int,
        default=4000,
    )

    parser.add_argument(
        "--maximum-post-unlock-tacts",
        type=int,
        default=4000,
    )

    parser.add_argument(
        "--phase-noise-strength",
        type=float,
        default=0.01,
    )

    parser.add_argument(
        "--amplitude-noise-strength",
        type=float,
        default=0.03,
    )

    parser.add_argument(
        "--natural-frequency-std",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--log-every",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--field-every",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--output-dir",
        default="edk_marnov_snapshots",
    )

    return parser


def main() -> None:
    args = (
        _build_argument_parser()
        .parse_args()
    )

    engine = EDKGPUMeanFieldPhaseEngine(
        MeanFieldPhaseConfig(
            num_domains=(
                args.num_domains
            ),
            coupling_strength_k=(
                args.coupling
            ),
            sakaguchi_phase_lag_alpha=(
                args.phase_lag
            ),
            natural_frequency_mean=0.0,
            natural_frequency_std=(
                args.natural_frequency_std
            ),
            external_forcing_phase=(
                args.hold_forcing_phase
            ),
            phase_noise_strength=(
                args.phase_noise_strength
            ),
            amplitude_growth_rate=1.0,
            amplitude_saturation_rate=1.0,
            amplitude_noise_strength=(
                args.amplitude_noise_strength
            ),
            amplitude_minimum=0.1,
            amplitude_maximum=5.0,
            initial_amplitude_minimum=0.8,
            initial_amplitude_maximum=1.2,
            seed=args.seed,
            dtype=args.dtype,
            backend=args.backend,
            device_id=(
                args.device_id
            ),
        )
    )

    protocol = EDKMarnovRetentionCollapseProtocol(
        engine,
        MarnovRetentionCollapseConfig(
            formation_maximum_tacts=(
                args.formation_maximum_tacts
            ),
            formation_confirmation_tacts=(
                args.formation_confirmation_tacts
            ),
            retained_verification_tacts=(
                args.retained_verification_tacts
            ),
            critical_loading_maximum_tacts=(
                args.critical_loading_maximum_tacts
            ),
            maximum_post_unlock_tacts=(
                args.maximum_post_unlock_tacts
            ),
            pressure_schedule=(
                args.pressure_schedule
            ),
            pressure_hold=(
                args.pressure_hold
            ),
            pressure_collapse=(
                args.pressure_collapse
            ),
            pressure_ramp_rate=(
                args.pressure_ramp_rate
            ),
            coupling_floor=(
                args.coupling_floor
            ),
            coupling_quench_tau=(
                args.coupling_quench_tau
            ),
            log_every=(
                args.log_every
            ),
            field_every=(
                args.field_every
            ),
        ),
    )

    logger = EDKMarnovProtocolLogger(
        args.output_dir
    )

    summary = protocol.run_protocol(
        dt=args.dt,
        hold_forcing_density=(
            args.hold_forcing
        ),
        hold_forcing_phase=(
            args.hold_forcing_phase
        ),
        collapse_forcing_density=(
            args.collapse_forcing
        ),
        collapse_forcing_phase=(
            args.collapse_forcing_phase
        ),
        logger=logger,
    )

    summary_path = logger.log_summary(
        protocol
    )

    print(
        "EDK Marnov Retention-Collapse "
        "Protocol completed."
    )

    print(
        f"backend={engine.backend_name} "
        f"device_id={engine.active_device_id} "
        f"domains={engine.N}"
    )

    print(
        f"final_status="
        f"{summary['final_status']}"
    )

    print(
        f"attractor_formed="
        f"{summary['attractor_formed']}"
    )

    print(
        f"attractor_verified="
        f"{summary['attractor_verified']}"
    )

    print(
        f"phase_node_unlocked="
        f"{summary['phase_node_unlocked']}"
    )

    print(
        f"collapse_detected="
        f"{summary['collapse_detected']}"
    )

    print(
        f"summary={summary_path}"
    )


if __name__ == "__main__":
    main()
