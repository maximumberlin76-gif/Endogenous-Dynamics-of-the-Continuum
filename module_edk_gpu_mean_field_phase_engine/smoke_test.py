from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

try:
    from .benchmark_gpu_phase_engine import run_benchmark
    from .edk_gpu_mean_field_phase_engine import (
        EDKGPUMeanFieldLogger,
        EDKGPUMeanFieldPhaseEngine,
        MeanFieldPhaseConfig,
    )
except ImportError:
    try:
        from benchmark_gpu_phase_engine import run_benchmark
        from edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldLogger,
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
        )
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]

        if str(repo_root) not in sys.path:
            sys.path.insert(
                0,
                str(repo_root),
            )

        from module_edk_gpu_mean_field_phase_engine.benchmark_gpu_phase_engine import (
            run_benchmark,
        )
        from module_edk_gpu_mean_field_phase_engine.edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldLogger,
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
        )


def _assert_finite(
    value: object,
    name: str,
) -> float:
    numeric_value = float(
        value
    )

    if not math.isfinite(
        numeric_value
    ):
        raise RuntimeError(
            f"Non-finite value: {name}={numeric_value}"
        )

    return numeric_value


def _assert_unit_interval(
    value: object,
    name: str,
) -> None:
    numeric_value = _assert_finite(
        value,
        name,
    )

    if not 0.0 <= numeric_value <= 1.0:
        raise RuntimeError(
            f"Value outside [0, 1]: {name}={numeric_value}"
        )


def _assert_field_snapshot(
    field: dict[str, np.ndarray],
    num_domains: int,
    dtype: np.dtype,
) -> None:
    required_fields = (
        "phases",
        "amplitudes",
        "natural_frequencies",
        "phase_velocity",
        "amplitude_velocity",
        "phase_noise_increment",
        "amplitude_noise_increment",
    )

    for key in required_fields:
        if key not in field:
            raise RuntimeError(
                f"Missing field snapshot array: {key}"
            )

        array = np.asarray(
            field[key]
        )

        if array.shape != (
            num_domains,
        ):
            raise RuntimeError(
                f"Unexpected shape for {key}: {array.shape}"
            )

        if array.dtype != dtype:
            raise RuntimeError(
                f"Unexpected dtype for {key}: {array.dtype}"
            )

        if not np.all(
            np.isfinite(
                array
            )
        ):
            raise RuntimeError(
                f"Non-finite values in field array: {key}"
            )


def _assert_no_pairwise_state_matrix(
    engine: EDKGPUMeanFieldPhaseEngine,
) -> None:
    for name, value in vars(
        engine
    ).items():
        shape = getattr(
            value,
            "shape",
            None,
        )

        if shape == (
            engine.N,
            engine.N,
        ):
            raise RuntimeError(
                f"Unexpected N x N state matrix: {name}"
            )


def main() -> None:
    num_domains = 256
    dt = 0.01
    tacts = 10

    config = MeanFieldPhaseConfig(
        num_domains=num_domains,
        coupling_strength_k=12.0,
        sakaguchi_phase_lag_alpha=0.2,
        natural_frequency_mean=0.0,
        natural_frequency_std=0.08,
        external_forcing_phase=0.35,
        phase_noise_strength=0.02,
        amplitude_growth_rate=1.0,
        amplitude_saturation_rate=1.0,
        amplitude_noise_strength=0.03,
        amplitude_minimum=0.1,
        amplitude_maximum=3.0,
        initial_amplitude_minimum=0.5,
        initial_amplitude_maximum=1.5,
        seed=17,
        dtype="float32",
        backend="cpu",
        device_id=0,
    )

    engine = EDKGPUMeanFieldPhaseEngine(
        config
    )

    duplicate_engine = EDKGPUMeanFieldPhaseEngine(
        config
    )

    initial_field = engine.export_field_snapshot()
    duplicate_field = duplicate_engine.export_field_snapshot()

    for key in (
        "phases",
        "amplitudes",
        "natural_frequencies",
    ):
        if not np.array_equal(
            initial_field[key],
            duplicate_field[key],
        ):
            raise RuntimeError(
                f"Initialization is not deterministic for {key}."
            )

    fixed_natural_frequencies = initial_field[
        "natural_frequencies"
    ].copy()

    metrics: dict[str, object] = {}

    for _ in range(
        tacts
    ):
        metrics = engine.process_micro_interval(
            external_forcing_density=1.75,
            external_forcing_phase=0.35,
            dt=dt,
        )

    required_metrics = (
        "R_t_phase_order",
        "global_mean_phase",
        "phase_amplitude_order_proxy",
        "mean_phase_velocity",
        "phase_velocity_dispersion",
        "mean_amplitude",
        "amplitude_dispersion",
        "minimum_amplitude",
        "maximum_amplitude",
        "coupling_energy_proxy",
        "external_forcing_density",
        "external_forcing_phase",
        "coupling_strength_k",
        "sakaguchi_phase_lag_alpha",
        "active_domains",
        "backend_name",
        "backend_library",
        "device_id",
        "simulation_time",
        "tact_index",
        "step",
    )

    for key in required_metrics:
        if key not in metrics:
            raise RuntimeError(
                f"Missing metric: {key}"
            )

    for key in (
        "R_t_phase_order",
        "global_mean_phase",
        "phase_amplitude_order_proxy",
        "mean_phase_velocity",
        "phase_velocity_dispersion",
        "mean_amplitude",
        "amplitude_dispersion",
        "minimum_amplitude",
        "maximum_amplitude",
        "coupling_energy_proxy",
        "external_forcing_density",
        "external_forcing_phase",
        "coupling_strength_k",
        "sakaguchi_phase_lag_alpha",
        "simulation_time",
    ):
        _assert_finite(
            metrics[key],
            key,
        )

    _assert_unit_interval(
        metrics["R_t_phase_order"],
        "R_t_phase_order",
    )

    _assert_unit_interval(
        metrics["phase_amplitude_order_proxy"],
        "phase_amplitude_order_proxy",
    )

    global_mean_phase = float(
        metrics["global_mean_phase"]
    )

    if not -math.pi <= global_mean_phase <= math.pi:
        raise RuntimeError(
            "global_mean_phase is outside [-pi, pi]."
        )

    coupling_energy_proxy = float(
        metrics["coupling_energy_proxy"]
    )

    if not -1.0 <= coupling_energy_proxy <= 1.0:
        raise RuntimeError(
            "coupling_energy_proxy is outside [-1, 1]."
        )

    for key in (
        "phase_velocity_dispersion",
        "amplitude_dispersion",
    ):
        if float(
            metrics[key]
        ) < 0.0:
            raise RuntimeError(
                f"Negative dispersion: {key}"
            )

    if metrics["backend_name"] != "cpu":
        raise RuntimeError(
            "Explicit CPU backend did not select cpu backend_name."
        )

    if metrics["backend_library"] != "numpy":
        raise RuntimeError(
            "Explicit CPU backend did not select NumPy backend_library."
        )

    if metrics["device_id"] is not None:
        raise RuntimeError(
            "CPU backend must not report a CUDA device ID."
        )

    if int(
        metrics["active_domains"]
    ) != num_domains:
        raise RuntimeError(
            "Incorrect active-domain count."
        )

    if int(
        metrics["tact_index"]
    ) != tacts:
        raise RuntimeError(
            "Incorrect tact index."
        )

    if int(
        metrics["step"]
    ) != tacts:
        raise RuntimeError(
            "Incorrect step compatibility index."
        )

    if not math.isclose(
        float(
            metrics["simulation_time"]
        ),
        tacts
        * dt,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ):
        raise RuntimeError(
            "Incorrect accumulated simulation time."
        )

    field = engine.export_field_snapshot()

    _assert_field_snapshot(
        field=field,
        num_domains=num_domains,
        dtype=np.dtype(
            "float32"
        ),
    )

    if not np.array_equal(
        field["natural_frequencies"],
        fixed_natural_frequencies,
    ):
        raise RuntimeError(
            "Natural frequencies changed during simulation."
        )

    phase_tolerance = 1.0e-6

    if np.any(
        field["phases"]
        < -math.pi
        - phase_tolerance
    ) or np.any(
        field["phases"]
        >= math.pi
        + phase_tolerance
    ):
        raise RuntimeError(
            "Wrapped phases are outside [-pi, pi)."
        )

    if np.any(
        field["amplitudes"]
        < config.amplitude_minimum
        - phase_tolerance
    ) or np.any(
        field["amplitudes"]
        > config.amplitude_maximum
        + phase_tolerance
    ):
        raise RuntimeError(
            "Amplitudes are outside configured bounds."
        )

    _assert_no_pairwise_state_matrix(
        engine
    )

    engine.set_coupling_strength(
        7.5
    )

    engine.set_phase_lag(
        0.1
    )

    if not math.isclose(
        engine.K,
        7.5,
    ):
        raise RuntimeError(
            "Coupling-strength update failed."
        )

    if not math.isclose(
        engine.alpha,
        0.1,
    ):
        raise RuntimeError(
            "Phase-lag update failed."
        )

    try:
        engine.process_micro_interval(
            external_forcing_density=1.0,
            external_forcing_phase=0.0,
            dt=0.0,
        )
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Non-positive dt did not raise ValueError."
        )

    with tempfile.TemporaryDirectory(
        prefix="edk_gpu_mean_field_smoke_"
    ) as temporary_directory:
        output_dir = Path(
            temporary_directory
        )

        logger = EDKGPUMeanFieldLogger(
            output_dir
        )

        tact = int(
            engine.tact_index
        )

        metrics_path, field_path = logger.log_tact(
            tact_id=tact,
            engine=engine,
            include_field=True,
        )

        tact_json_path = (
            output_dir
            / f"gpu_mean_field_tact_{tact:06d}.json"
        )

        step_json_path = (
            output_dir
            / f"gpu_mean_field_step_{tact:06d}.json"
        )

        expected_field_path = (
            output_dir
            / f"gpu_mean_field_field_{tact:06d}.npz"
        )

        if metrics_path != tact_json_path:
            raise RuntimeError(
                "log_tact returned an unexpected metrics path."
            )

        if field_path != expected_field_path:
            raise RuntimeError(
                "log_tact returned an unexpected field path."
            )

        if not tact_json_path.is_file():
            raise RuntimeError(
                "Primary tact JSON metric snapshot was not created."
            )

        if not step_json_path.is_file():
            raise RuntimeError(
                "Compatibility step JSON metric snapshot was not created."
            )

        if not expected_field_path.is_file():
            raise RuntimeError(
                "NPZ field snapshot was not created."
            )

        with tact_json_path.open(
            "r",
            encoding="utf-8",
        ) as stream:
            tact_payload = json.load(
                stream
            )

        with step_json_path.open(
            "r",
            encoding="utf-8",
        ) as stream:
            step_payload = json.load(
                stream
            )

        if tact_payload != step_payload:
            raise RuntimeError(
                "Primary tact JSON and compatibility step JSON differ."
            )

        if tact_payload.get(
            "module"
        ) != "module_edk_gpu_mean_field_phase_engine":
            raise RuntimeError(
                "Incorrect module identifier in JSON snapshot."
            )

        if tact_payload.get(
            "engine_class"
        ) != "EDKGPUMeanFieldPhaseEngine":
            raise RuntimeError(
                "Incorrect engine identifier in JSON snapshot."
            )

        if tact_payload.get(
            "tact"
        ) != tact:
            raise RuntimeError(
                "Incorrect tact identifier in JSON snapshot."
            )

        if tact_payload.get(
            "step"
        ) != tact:
            raise RuntimeError(
                "Incorrect step compatibility identifier in JSON snapshot."
            )

        if tact_payload.get(
            "tact_index"
        ) != tact:
            raise RuntimeError(
                "Incorrect tact_index in JSON snapshot."
            )

        if not math.isclose(
            float(
                tact_payload.get(
                    "simulation_time"
                )
            ),
            float(
                engine.simulation_time
            ),
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise RuntimeError(
                "Incorrect simulation_time in JSON snapshot."
            )

        if tact_payload["backend"]["name"] != "cpu":
            raise RuntimeError(
                "Incorrect backend name in JSON snapshot."
            )

        if tact_payload["backend"]["library"] != "numpy":
            raise RuntimeError(
                "Incorrect backend library in JSON snapshot."
            )

        if tact_payload["backend"]["device_id"] is not None:
            raise RuntimeError(
                "CPU JSON snapshot must not contain CUDA device_id."
            )

        if "configuration" not in tact_payload:
            raise RuntimeError(
                "Configuration is missing from JSON snapshot."
            )

        if "metrics" not in tact_payload:
            raise RuntimeError(
                "Metrics are missing from JSON snapshot."
            )

        if tact_payload["metrics"]["tact_index"] != tact:
            raise RuntimeError(
                "metrics.tact_index does not match tact."
            )

        if tact_payload["metrics"]["step"] != tact:
            raise RuntimeError(
                "metrics.step does not match tact."
            )

        with np.load(
            expected_field_path,
            allow_pickle=False,
        ) as saved_field:
            saved_arrays = {
                key: saved_field[key]
                for key in saved_field.files
            }

        _assert_field_snapshot(
            field=saved_arrays,
            num_domains=num_domains,
            dtype=np.dtype(
                "float32"
            ),
        )

        alias_metrics_path, alias_field_path = logger.log_step(
            step_id=tact,
            engine=engine,
            include_field=False,
        )

        if alias_metrics_path != tact_json_path:
            raise RuntimeError(
                "log_step compatibility alias returned an unexpected path."
            )

        if alias_field_path is not None:
            raise RuntimeError(
                "log_step unexpectedly returned a field path."
            )

        if list(
            output_dir.glob(
                "*.tmp"
            )
        ):
            raise RuntimeError(
                "Temporary files were left after atomic writes."
            )

    auto_config = MeanFieldPhaseConfig(
        num_domains=64,
        coupling_strength_k=4.0,
        sakaguchi_phase_lag_alpha=0.05,
        phase_noise_strength=0.0,
        amplitude_noise_strength=0.0,
        seed=23,
        dtype="float32",
        backend="auto",
        device_id=0,
    )

    auto_engine = EDKGPUMeanFieldPhaseEngine(
        auto_config
    )

    auto_metrics = auto_engine.process_micro_interval(
        external_forcing_density=0.5,
        external_forcing_phase=0.0,
        dt=0.01,
    )

    if auto_engine.backend_name not in {
        "cpu",
        "gpu",
    }:
        raise RuntimeError(
            "Automatic backend selection returned an invalid backend_name."
        )

    if auto_engine.backend_library not in {
        "numpy",
        "cupy",
    }:
        raise RuntimeError(
            "Automatic backend selection returned an invalid backend_library."
        )

    _assert_unit_interval(
        auto_metrics["R_t_phase_order"],
        "auto.R_t_phase_order",
    )

    auto_engine.synchronize_backend()

    benchmark_config = MeanFieldPhaseConfig(
        num_domains=128,
        coupling_strength_k=6.0,
        sakaguchi_phase_lag_alpha=0.1,
        phase_noise_strength=0.0,
        amplitude_noise_strength=0.0,
        seed=31,
        dtype="float32",
        backend="cpu",
        device_id=0,
    )

    benchmark_report = run_benchmark(
        config=benchmark_config,
        warmup_tacts=1,
        measured_tacts=3,
        forcing=0.75,
        forcing_phase=0.2,
        dt=0.01,
        measure_field_io=False,
    )

    if benchmark_report["backend"]["name"] != "cpu":
        raise RuntimeError(
            "CPU benchmark did not use cpu backend_name."
        )

    if benchmark_report["backend"]["library"] != "numpy":
        raise RuntimeError(
            "CPU benchmark did not use NumPy backend_library."
        )

    timing_report = benchmark_report[
        "timing"
    ]

    if float(
        timing_report["measured_tacts"]
    ) != 3.0:
        raise RuntimeError(
            "Benchmark measured-tact count is incorrect."
        )

    if float(
        timing_report["host_wall_seconds"]
    ) <= 0.0:
        raise RuntimeError(
            "Benchmark host time must be positive."
        )

    if float(
        timing_report["domain_updates_per_second"]
    ) <= 0.0:
        raise RuntimeError(
            "Benchmark throughput must be positive."
        )

    memory_report = benchmark_report[
        "memory"
    ]

    if int(
        memory_report["persistent_state_bytes"]
    ) <= 0:
        raise RuntimeError(
            "Persistent-state memory estimate must be positive."
        )

    if int(
        memory_report["unallocated_pairwise_matrix_bytes"]
    ) <= 0:
        raise RuntimeError(
            "Avoided pairwise-matrix estimate must be positive."
        )

    print(
        "EDK GPU mean-field phase engine smoke test passed."
    )

    print(
        engine.get_metrics()
    )


if __name__ == "__main__":
    main()
