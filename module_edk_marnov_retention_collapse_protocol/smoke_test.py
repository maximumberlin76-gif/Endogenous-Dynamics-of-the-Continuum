from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

try:
    from .marnov_retention_collapse_protocol import (
        EDKMarnovProtocolLogger,
        EDKMarnovRetentionCollapseProtocol,
        MarnovRetentionCollapseConfig,
    )
    from .marnov_retention_diagnostics import (
        load_marnov_snapshots,
        plot_marnov_diagnostics,
    )
except ImportError:
    from marnov_retention_collapse_protocol import (
        EDKMarnovProtocolLogger,
        EDKMarnovRetentionCollapseProtocol,
        MarnovRetentionCollapseConfig,
    )
    from marnov_retention_diagnostics import (
        load_marnov_snapshots,
        plot_marnov_diagnostics,
    )

try:
    from module_edk_gpu_mean_field_phase_engine import (
        EDKGPUMeanFieldPhaseEngine,
        MeanFieldPhaseConfig,
    )
except ImportError:
    from edk_gpu_mean_field_phase_engine import (
        EDKGPUMeanFieldPhaseEngine,
        MeanFieldPhaseConfig,
    )


def _assert_finite(
    value: Any,
    name: str,
) -> float:
    numeric_value = float(value)

    if not math.isfinite(numeric_value):
        raise RuntimeError(
            f"Non-finite value: {name}={numeric_value}"
        )

    return numeric_value


def _assert_unit_interval(
    value: Any,
    name: str,
) -> float:
    numeric_value = _assert_finite(
        value,
        name,
    )

    if not 0.0 <= numeric_value <= 1.0:
        raise RuntimeError(
            f"Value outside [0, 1]: "
            f"{name}={numeric_value}"
        )

    return numeric_value


def _build_engine(
    seed: int,
    num_domains: int = 256,
) -> EDKGPUMeanFieldPhaseEngine:
    return EDKGPUMeanFieldPhaseEngine(
        MeanFieldPhaseConfig(
            num_domains=num_domains,
            coupling_strength_k=18.0,
            sakaguchi_phase_lag_alpha=0.0,
            natural_frequency_mean=0.0,
            natural_frequency_std=0.05,
            external_forcing_phase=0.0,
            phase_noise_strength=0.02,
            amplitude_growth_rate=1.0,
            amplitude_saturation_rate=1.0,
            amplitude_noise_strength=0.01,
            amplitude_minimum=0.1,
            amplitude_maximum=3.0,
            initial_amplitude_minimum=0.8,
            initial_amplitude_maximum=1.2,
            seed=seed,
            dtype="float32",
            backend="cpu",
            device_id=0,
        )
    )


def _build_collapse_config(
    log_every: int,
    field_every: int,
) -> MarnovRetentionCollapseConfig:
    return MarnovRetentionCollapseConfig(
        formation_maximum_tacts=500,
        formation_confirmation_tacts=3,
        retained_verification_tacts=2,
        critical_loading_maximum_tacts=500,
        maximum_post_unlock_tacts=300,
        minimum_post_unlock_tacts=2,
        R_form_min=0.70,
        phase_amplitude_form_min=0.70,
        phase_velocity_dispersion_form_max=3.0,
        amplitude_dispersion_form_max=0.20,
        coherence_weight_R=0.40,
        coherence_weight_phase_amplitude=0.40,
        coherence_weight_phase_velocity=0.10,
        coherence_weight_amplitude=0.10,
        phase_velocity_reference=2.0,
        amplitude_dispersion_reference=0.20,
        retained_boundary_tolerance=0.02,
        pressure_schedule="step",
        pressure_hold=0.05,
        pressure_collapse=1.0,
        pressure_ramp_rate=1.0,
        delay_base_tau_0=0.02,
        pressure_velocity_coefficient_mu=5.0,
        delay_regularization_epsilon=1.0e-9,
        minimum_delay_tau=1.0e-6,
        critical_exposure_threshold=0.50,
        exposure_recovery_mode="decaying",
        exposure_recovery_rate=0.25,
        coupling_quench_mode="exponential",
        coupling_floor=0.0,
        coupling_quench_tau=0.01,
        post_unlock_phase_noise_multiplier=100.0,
        post_unlock_frequency_dispersion_multiplier=100.0,
        post_unlock_amplitude_decay_scale=2.0,
        phase_order_collapse_threshold=0.05,
        phase_order_collapse_fraction=0.50,
        phase_amplitude_collapse_threshold=0.0,
        phase_velocity_dispersion_collapse_threshold=1.0e9,
        collapse_logic="any",
        log_every=log_every,
        field_every=field_every,
    )


def _assert_state_arrays(
    protocol: EDKMarnovRetentionCollapseProtocol,
) -> None:
    engine = protocol.engine
    field = protocol.export_field_snapshot()

    expected_fields = {
        "phases",
        "amplitudes",
        "natural_frequencies",
        "effective_natural_frequencies",
        "phase_velocity",
        "amplitude_velocity",
        "phase_noise_increment",
        "amplitude_noise_increment",
    }

    if set(field) != expected_fields:
        raise RuntimeError(
            "Unexpected field-snapshot key set."
        )

    for key, array in field.items():
        values = np.asarray(array)

        if values.shape != (engine.N,):
            raise RuntimeError(
                f"Unexpected shape for {key}: {values.shape}"
            )

        if values.dtype != np.dtype(
            engine.config.dtype
        ):
            raise RuntimeError(
                f"Unexpected dtype for {key}: {values.dtype}"
            )

        if not np.all(
            np.isfinite(values)
        ):
            raise RuntimeError(
                f"Non-finite values in {key}."
            )

    phase_tolerance = 1.0e-6
    phases = np.asarray(
        field["phases"]
    )

    if np.any(
        phases < -math.pi - phase_tolerance
    ) or np.any(
        phases >= math.pi + phase_tolerance
    ):
        raise RuntimeError(
            "Wrapped phases are outside [-pi, pi)."
        )

    amplitudes = np.asarray(
        field["amplitudes"]
    )

    if np.any(
        amplitudes
        < engine.config.amplitude_minimum
        - phase_tolerance
    ) or np.any(
        amplitudes
        > engine.config.amplitude_maximum
        + phase_tolerance
    ):
        raise RuntimeError(
            "Amplitudes are outside configured bounds."
        )


def _assert_history(
    protocol: EDKMarnovRetentionCollapseProtocol,
) -> None:
    if not protocol.history:
        raise RuntimeError(
            "Protocol history is empty."
        )

    required_numeric_metrics = (
        "R_t_phase_order",
        "global_mean_phase",
        "phase_amplitude_order_proxy",
        "phase_velocity_dispersion",
        "mean_amplitude",
        "amplitude_dispersion",
        "C_proxy_t",
        "external_pressure_P_ext",
        "retention_margin",
        "pressure_excess",
        "instantaneous_delay_tau",
        "critical_exposure",
        "initial_coupling_K",
        "effective_coupling_K",
        "coupling_floor_K",
    )

    previous_tact = -1
    previous_time = -1.0

    for record in protocol.history:
        tact = int(
            record["tact_index"]
        )

        simulation_time = _assert_finite(
            record["simulation_time"],
            "simulation_time",
        )

        if tact <= previous_tact:
            raise RuntimeError(
                "Protocol tact indices are not "
                "strictly increasing."
            )

        if simulation_time <= previous_time:
            raise RuntimeError(
                "Protocol simulation time is not "
                "strictly increasing."
            )

        previous_tact = tact
        previous_time = simulation_time

        for key in required_numeric_metrics:
            _assert_finite(
                record[key],
                key,
            )

        C_proxy = _assert_unit_interval(
            record["C_proxy_t"],
            "C_proxy_t",
        )

        pressure = _assert_unit_interval(
            record["external_pressure_P_ext"],
            "external_pressure_P_ext",
        )

        if not math.isclose(
            float(
                record["retention_margin"]
            ),
            C_proxy - pressure,
            rel_tol=1.0e-7,
            abs_tol=1.0e-7,
        ):
            raise RuntimeError(
                "Retention margin is inconsistent with "
                "C_proxy(t) - P_ext(t)."
            )

        expected_excess = max(
            pressure - C_proxy,
            0.0,
        )

        if not math.isclose(
            float(
                record["pressure_excess"]
            ),
            expected_excess,
            rel_tol=1.0e-7,
            abs_tol=1.0e-7,
        ):
            raise RuntimeError(
                "Pressure excess is inconsistent with "
                "max(P_ext(t) - C_proxy(t), 0)."
            )

        if float(
            record["instantaneous_delay_tau"]
        ) <= 0.0:
            raise RuntimeError(
                "instantaneous_delay_tau must be positive."
            )

        if float(
            record["critical_exposure"]
        ) < 0.0:
            raise RuntimeError(
                "critical_exposure must be non-negative."
            )


def _assert_exposure_and_unlock(
    protocol: EDKMarnovRetentionCollapseProtocol,
) -> None:
    positive_exposure_records = [
        record
        for record in protocol.history
        if float(
            record["critical_exposure"]
        ) > 0.0
    ]

    if len(
        positive_exposure_records
    ) < 2:
        raise RuntimeError(
            "Critical exposure did not accumulate "
            "over multiple tacts."
        )

    first_positive = (
        positive_exposure_records[0]
    )

    if float(
        first_positive["critical_exposure"]
    ) >= protocol.config.critical_exposure_threshold:
        raise RuntimeError(
            "The first positive exposure already "
            "exceeded the configured threshold."
        )

    if bool(
        first_positive["phase_node_unlocked"]
    ):
        raise RuntimeError(
            "The phase node unlocked before "
            "the exposure threshold."
        )

    unlock_records = [
        record
        for record in protocol.history
        if bool(
            record["phase_node_unlocked"]
        )
    ]

    if not unlock_records:
        raise RuntimeError(
            "No unlocked protocol record was produced."
        )

    first_unlock = unlock_records[0]

    if float(
        first_unlock["critical_exposure"]
    ) < protocol.config.critical_exposure_threshold:
        raise RuntimeError(
            "The phase node unlocked below "
            "the exposure threshold."
        )


def _assert_monotonic_coupling_quench(
    protocol: EDKMarnovRetentionCollapseProtocol,
) -> None:
    coupling_values = [
        float(
            record["effective_coupling_K"]
        )
        for record in protocol.history
        if bool(
            record["phase_node_unlocked"]
        )
    ]

    if len(coupling_values) < 3:
        raise RuntimeError(
            "Insufficient post-unlock coupling records."
        )

    if not all(
        next_value
        <= current_value + 1.0e-12
        for current_value, next_value in zip(
            coupling_values,
            coupling_values[1:],
        )
    ):
        raise RuntimeError(
            "Effective coupling is not "
            "monotonically decreasing."
        )

    if coupling_values[-1] < (
        protocol.config.coupling_floor
        - 1.0e-12
    ):
        raise RuntimeError(
            "Effective coupling fell below "
            "the configured floor."
        )


def _assert_logged_outputs(
    directory: Path,
    protocol: EDKMarnovRetentionCollapseProtocol,
) -> None:
    json_paths = sorted(
        directory.glob(
            "marnov_step_*.json"
        )
    )

    npz_paths = sorted(
        directory.glob(
            "marnov_field_*.npz"
        )
    )

    summary_path = (
        directory
        / "marnov_protocol_summary.json"
    )

    if not json_paths:
        raise RuntimeError(
            "No JSON protocol snapshots were created."
        )

    if not npz_paths:
        raise RuntimeError(
            "No NPZ field snapshots were created."
        )

    if not summary_path.is_file():
        raise RuntimeError(
            "Protocol summary was not created."
        )

    with json_paths[-1].open(
        "r",
        encoding="utf-8",
    ) as stream:
        payload = json.load(
            stream
        )

    if payload.get(
        "module"
    ) != (
        "module_edk_marnov_"
        "retention_collapse_protocol"
    ):
        raise RuntimeError(
            "Incorrect module identifier "
            "in JSON snapshot."
        )

    if payload.get(
        "protocol_class"
    ) != (
        "EDKMarnovRetentionCollapseProtocol"
    ):
        raise RuntimeError(
            "Incorrect protocol identifier "
            "in JSON snapshot."
        )

    if not isinstance(
        payload.get("metrics"),
        dict,
    ):
        raise RuntimeError(
            "Metrics are missing from JSON snapshot."
        )

    with np.load(
        npz_paths[-1],
        allow_pickle=False,
    ) as field:
        saved_arrays = {
            key: field[key]
            for key in field.files
        }

    if saved_arrays[
        "phases"
    ].shape != (
        protocol.engine.N,
    ):
        raise RuntimeError(
            "Incorrect phase-array shape "
            "in NPZ snapshot."
        )

    if saved_arrays[
        "effective_natural_frequencies"
    ].shape != (
        protocol.engine.N,
    ):
        raise RuntimeError(
            "Incorrect effective-frequency shape "
            "in NPZ snapshot."
        )

    temporary_artifacts = [
        path
        for path in directory.iterdir()
        if path.name.startswith(".")
        or path.suffix == ".tmp"
    ]

    if temporary_artifacts:
        raise RuntimeError(
            "Atomic logging left temporary files behind."
        )


def _run_collapse_case(
    output_dir: Path,
) -> EDKMarnovRetentionCollapseProtocol:
    engine = _build_engine(
        seed=7
    )

    duplicate_engine = _build_engine(
        seed=7
    )

    first_state = (
        engine.export_field_snapshot()
    )

    duplicate_state = (
        duplicate_engine.export_field_snapshot()
    )

    for key in (
        "phases",
        "amplitudes",
        "natural_frequencies",
    ):
        if not np.array_equal(
            first_state[key],
            duplicate_state[key],
        ):
            raise RuntimeError(
                f"Initialization is not "
                f"deterministic for {key}."
            )

    base_frequencies = np.asarray(
        first_state[
            "natural_frequencies"
        ]
    ).copy()

    protocol = EDKMarnovRetentionCollapseProtocol(
        engine=engine,
        config=_build_collapse_config(
            log_every=2,
            field_every=5,
        ),
    )

    logger = EDKMarnovProtocolLogger(
        output_dir
    )

    summary = protocol.run_protocol(
        dt=0.01,
        hold_forcing_density=8.0,
        hold_forcing_phase=0.0,
        collapse_forcing_density=0.0,
        collapse_forcing_phase=0.0,
        logger=logger,
    )

    logger.log_summary(
        protocol
    )

    if summary[
        "final_status"
    ] != protocol.COLLAPSE_COMPLETED:
        raise RuntimeError(
            "The controlled collapse case "
            "did not complete."
        )

    for key in (
        "attractor_formed",
        "attractor_verified",
        "phase_node_unlocked",
        "collapse_detected",
    ):
        if not bool(
            summary[key]
        ):
            raise RuntimeError(
                f"Expected successful "
                f"protocol flag: {key}."
            )

    formation_tact = int(
        summary["formation_tact"]
    )

    unlock_tact = int(
        summary["unlock_tact"]
    )

    collapse_tact = int(
        summary["collapse_tact"]
    )

    if not (
        formation_tact
        < unlock_tact
        < collapse_tact
    ):
        raise RuntimeError(
            "Protocol transition tacts "
            "are out of order."
        )

    if summary[
        "phase_order_half_life"
    ] is None:
        raise RuntimeError(
            "Phase-order half-life "
            "was not measured."
        )

    if summary[
        "amplitude_regime_half_life"
    ] is None:
        raise RuntimeError(
            "Amplitude-regime half-life "
            "was not measured."
        )

    if summary[
        "attractor_collapse_duration"
    ] is None:
        raise RuntimeError(
            "Attractor-collapse duration "
            "was not measured."
        )

    for key in (
        "phase_order_half_life",
        "amplitude_regime_half_life",
        "attractor_collapse_duration",
    ):
        if float(
            summary[key]
        ) < 0.0:
            raise RuntimeError(
                f"Negative measured duration: {key}."
            )

    _assert_history(
        protocol
    )

    _assert_exposure_and_unlock(
        protocol
    )

    _assert_monotonic_coupling_quench(
        protocol
    )

    _assert_state_arrays(
        protocol
    )

    final_frequencies = np.asarray(
        engine.export_field_snapshot()[
            "natural_frequencies"
        ]
    )

    if not np.array_equal(
        final_frequencies,
        base_frequencies,
    ):
        raise RuntimeError(
            "Base natural frequencies changed "
            "during the protocol."
        )

    if protocol._classify_retention_regime(
        0.10
    ) != protocol.EDS_RETAINED:
        raise RuntimeError(
            "EDS classification failed."
        )

    if protocol._classify_retention_regime(
        0.0
    ) != protocol.EDC_CRITICAL:
        raise RuntimeError(
            "EDC classification failed."
        )

    if protocol._classify_retention_regime(
        -0.10
    ) != protocol.DEGRADATION:
        raise RuntimeError(
            "Degradation classification failed."
        )

    if not (
        protocol._calculate_delay_tau(
            0.80
        )
        < protocol._calculate_delay_tau(
            0.10
        )
    ):
        raise RuntimeError(
            "Delay scale does not decrease "
            "with pressure excess."
        )

    try:
        protocol._validate_pressure(
            1.1
        )
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Out-of-range normalized pressure "
            "was accepted."
        )

    _assert_logged_outputs(
        output_dir,
        protocol,
    )

    records, loaded_summary = (
        load_marnov_snapshots(
            output_dir
        )
    )

    if not records:
        raise RuntimeError(
            "Diagnostic snapshot loader "
            "returned no records."
        )

    if loaded_summary is None:
        raise RuntimeError(
            "Diagnostic snapshot loader "
            "did not load the summary."
        )

    diagnostic_path = (
        output_dir
        / "marnov_diagnostics.png"
    )

    generated_path = (
        plot_marnov_diagnostics(
            snapshot_dir=output_dir,
            output=diagnostic_path,
            show=False,
        )
    )

    if generated_path != diagnostic_path:
        raise RuntimeError(
            "Diagnostic generator returned "
            "an unexpected path."
        )

    if (
        not diagnostic_path.is_file()
        or diagnostic_path.stat().st_size <= 0
    ):
        raise RuntimeError(
            "Diagnostic image was not created."
        )

    return protocol


def _run_collapse_not_reached_case() -> None:
    engine = _build_engine(
        seed=19,
        num_domains=96,
    )

    config = MarnovRetentionCollapseConfig(
        formation_maximum_tacts=500,
        formation_confirmation_tacts=2,
        retained_verification_tacts=2,
        critical_loading_maximum_tacts=200,
        maximum_post_unlock_tacts=5,
        minimum_post_unlock_tacts=1,
        R_form_min=0.65,
        phase_amplitude_form_min=0.65,
        phase_velocity_dispersion_form_max=3.0,
        amplitude_dispersion_form_max=0.25,
        coherence_weight_R=0.40,
        coherence_weight_phase_amplitude=0.40,
        coherence_weight_phase_velocity=0.10,
        coherence_weight_amplitude=0.10,
        phase_velocity_reference=2.0,
        amplitude_dispersion_reference=0.20,
        retained_boundary_tolerance=0.02,
        pressure_schedule="step",
        pressure_hold=0.05,
        pressure_collapse=1.0,
        delay_base_tau_0=0.01,
        pressure_velocity_coefficient_mu=10.0,
        delay_regularization_epsilon=1.0e-9,
        minimum_delay_tau=1.0e-6,
        critical_exposure_threshold=0.10,
        exposure_recovery_mode="persistent",
        exposure_recovery_rate=0.0,
        coupling_quench_mode="exponential",
        coupling_floor=18.0,
        coupling_quench_tau=0.05,
        post_unlock_phase_noise_multiplier=1.0,
        post_unlock_frequency_dispersion_multiplier=1.0,
        post_unlock_amplitude_decay_scale=0.0,
        phase_order_collapse_threshold=0.0,
        phase_order_collapse_fraction=0.01,
        phase_amplitude_collapse_threshold=0.0,
        phase_velocity_dispersion_collapse_threshold=1.0e9,
        collapse_logic="any",
        log_every=0,
        field_every=0,
    )

    protocol = EDKMarnovRetentionCollapseProtocol(
        engine=engine,
        config=config,
    )

    summary = protocol.run_protocol(
        dt=0.01,
        hold_forcing_density=8.0,
        hold_forcing_phase=0.0,
        collapse_forcing_density=8.0,
        collapse_forcing_phase=0.0,
    )

    if summary[
        "final_status"
    ] != protocol.COLLAPSE_NOT_REACHED:
        raise RuntimeError(
            "COLLAPSE_NOT_REACHED was not "
            "reported for the retained "
            "post-unlock case."
        )

    if not bool(
        summary["phase_node_unlocked"]
    ):
        raise RuntimeError(
            "The non-collapse case never "
            "reached unlocking."
        )

    if bool(
        summary["collapse_detected"]
    ):
        raise RuntimeError(
            "The non-collapse case incorrectly "
            "reported collapse."
        )


def main() -> None:
    with tempfile.TemporaryDirectory(
        prefix="edk_marnov_smoke_"
    ) as temporary_directory:
        protocol = _run_collapse_case(
            Path(
                temporary_directory
            )
        )

    _run_collapse_not_reached_case()

    print(
        "EDK Marnov Retention-Collapse "
        "Protocol smoke test passed."
    )

    print(
        protocol.get_summary()
    )


if __name__ == "__main__":
    main()
