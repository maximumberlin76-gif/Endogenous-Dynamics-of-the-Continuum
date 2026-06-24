from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import numpy as np

try:
    from .edk_spatiotemporal_phase_delay import (
        EDKDelayLogger,
        EDKSpatiotemporalPhaseDelayEngine,
        PhaseDelayConfig,
    )
except ImportError:
    from edk_spatiotemporal_phase_delay import (
        EDKDelayLogger,
        EDKSpatiotemporalPhaseDelayEngine,
        PhaseDelayConfig,
    )


def _assert_finite_metric(
    metrics: dict[str, float],
    key: str,
) -> None:
    value = float(metrics[key])

    if not math.isfinite(value):
        raise RuntimeError(
            f"Non-finite metric: {key}={value}"
        )


def _assert_interval(
    metrics: dict[str, float],
    key: str,
    lower: float,
    upper: float,
) -> None:
    value = float(metrics[key])

    if not lower <= value <= upper:
        raise RuntimeError(
            f"Metric outside [{lower}, {upper}]: "
            f"{key}={value}"
        )


def main() -> None:
    config = PhaseDelayConfig(
        num_domains=128,
        neighbor_count=12,
        coupling_strength_k=25.0,
        sakaguchi_phase_lag_alpha=0.15,
        wave_velocity_c=12.0,
        coordinate_half_extent=2.0,
        natural_frequency_mean=0.0,
        natural_frequency_std=0.05,
        knn_chunk_size=32,
        delay_safety_margin=3,
        seed=7,
        dtype="float32",
        backend="cpu",
    )

    engine = EDKSpatiotemporalPhaseDelayEngine(
        config
    )

    initial_natural_frequencies = np.asarray(
        engine.natural_frequencies
    ).copy()

    dt = 0.01
    metrics: dict[str, float] = {}

    for _ in range(8):
        metrics = engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=dt,
        )

    required_metrics = (
        "R_t_phase_order",
        "global_mean_phase",
        "delayed_local_phase_order",
        "mean_phase_velocity",
        "phase_velocity_dispersion",
        "mean_delay",
        "maximum_delay",
        "delay_dispersion",
        "delayed_coupling_energy_proxy",
        "history_buffer_depth",
    )

    for key in required_metrics:
        if key not in metrics:
            raise RuntimeError(
                f"Missing metric: {key}"
            )

        _assert_finite_metric(
            metrics,
            key,
        )

    _assert_interval(
        metrics,
        "R_t_phase_order",
        0.0,
        1.0,
    )

    _assert_interval(
        metrics,
        "delayed_local_phase_order",
        0.0,
        1.0,
    )

    _assert_interval(
        metrics,
        "global_mean_phase",
        -math.pi,
        math.pi,
    )

    _assert_interval(
        metrics,
        "delayed_coupling_energy_proxy",
        -1.0,
        1.0,
    )

    if metrics["phase_velocity_dispersion"] < 0.0:
        raise RuntimeError(
            "phase_velocity_dispersion must be non-negative."
        )

    if metrics["mean_delay"] <= 0.0:
        raise RuntimeError(
            "mean_delay must be positive."
        )

    if metrics["maximum_delay"] < metrics["mean_delay"]:
        raise RuntimeError(
            "maximum_delay must not be smaller than mean_delay."
        )

    if metrics["delay_dispersion"] < 0.0:
        raise RuntimeError(
            "delay_dispersion must be non-negative."
        )

    expected_minimum_history_depth = (
        math.ceil(
            engine.maximum_delay
            / dt
        )
        + config.delay_safety_margin
    )

    actual_history_depth = int(
        round(
            metrics["history_buffer_depth"]
        )
    )

    if actual_history_depth < expected_minimum_history_depth:
        raise RuntimeError(
            "History buffer is shallower than required "
            "by the maximum metric delay."
        )

    if not np.array_equal(
        np.asarray(
            engine.natural_frequencies
        ),
        initial_natural_frequencies,
    ):
        raise RuntimeError(
            "Natural frequencies changed during simulation."
        )

    phases = np.asarray(
        engine.phases
    )

    if not np.all(
        np.isfinite(
            phases
        )
    ):
        raise RuntimeError(
            "Phase array contains non-finite values."
        )

    phase_tolerance = 1e-6

    if np.any(
        phases < -np.pi - phase_tolerance
    ) or np.any(
        phases >= np.pi + phase_tolerance
    ):
        raise RuntimeError(
            "Wrapped phases are outside [-pi, pi)."
        )

    if engine._delay_floor_steps is None:
        raise RuntimeError(
            "Integer delay steps were not initialized."
        )

    if engine._delay_fractions is None:
        raise RuntimeError(
            "Fractional delay weights were not initialized."
        )

    delay_floor_steps = np.asarray(
        engine._delay_floor_steps
    )

    delay_fractions = np.asarray(
        engine._delay_fractions
    )

    if np.any(
        delay_floor_steps < 0
    ):
        raise RuntimeError(
            "Negative integer delay step found."
        )

    if np.any(
        delay_fractions < 0.0
    ) or np.any(
        delay_fractions >= 1.0
    ):
        raise RuntimeError(
            "Fractional delay weights are outside [0, 1)."
        )

    field = engine.export_field_snapshot()

    expected_shapes = {
        "coords_3d": (
            config.num_domains,
            3,
        ),
        "phases": (
            config.num_domains,
        ),
        "natural_frequencies": (
            config.num_domains,
        ),
        "neighbor_indices": (
            config.num_domains,
            config.neighbor_count,
        ),
        "edge_distances": (
            config.num_domains,
            config.neighbor_count,
        ),
        "tau_ij": (
            config.num_domains,
            config.neighbor_count,
        ),
        "neighbor_weights": (
            config.num_domains,
            config.neighbor_count,
        ),
        "delayed_neighbor_phases": (
            config.num_domains,
            config.neighbor_count,
        ),
        "phase_velocity": (
            config.num_domains,
        ),
    }

    for key, expected_shape in expected_shapes.items():
        if key not in field:
            raise RuntimeError(
                f"Missing field: {key}"
            )

        array = np.asarray(
            field[key]
        )

        if array.shape != expected_shape:
            raise RuntimeError(
                f"Unexpected shape for {key}: "
                f"{array.shape} != {expected_shape}"
            )

        if not np.all(
            np.isfinite(
                array
            )
        ):
            raise RuntimeError(
                f"Non-finite values in field: {key}"
            )

    neighbor_indices = np.asarray(
        field["neighbor_indices"]
    )

    if np.any(
        neighbor_indices < 0
    ) or np.any(
        neighbor_indices >= config.num_domains
    ):
        raise RuntimeError(
            "neighbor_indices contains an out-of-range index."
        )

    row_indices = np.arange(
        config.num_domains
    )[:, None]

    if np.any(
        neighbor_indices == row_indices
    ):
        raise RuntimeError(
            "Self-coupling was found in the neighbor graph."
        )

    neighbor_weight_sums = np.sum(
        np.asarray(
            field["neighbor_weights"]
        ),
        axis=1,
    )

    if not np.allclose(
        neighbor_weight_sums,
        1.0,
        rtol=1e-5,
        atol=1e-6,
    ):
        raise RuntimeError(
            "Spatial coupling weights are not normalized."
        )

    if np.any(
        np.asarray(
            field["edge_distances"]
        )
        <= 0.0
    ):
        raise RuntimeError(
            "Non-positive edge distance found."
        )

    if np.any(
        np.asarray(
            field["tau_ij"]
        )
        <= 0.0
    ):
        raise RuntimeError(
            "Non-positive propagation delay found."
        )

    delayed_neighbor_phases = np.asarray(
        field["delayed_neighbor_phases"]
    )

    if np.any(
        delayed_neighbor_phases
        < -np.pi - phase_tolerance
    ) or np.any(
        delayed_neighbor_phases
        >= np.pi + phase_tolerance
    ):
        raise RuntimeError(
            "Delayed phases are outside [-pi, pi)."
        )

    try:
        engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=dt * 2.0,
        )
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Changing dt after delay-history initialization "
            "did not raise ValueError."
        )

    with tempfile.TemporaryDirectory(
        prefix="edk_delay_smoke_"
    ) as temp_dir:
        output_dir = Path(
            temp_dir
        )

        logger = EDKDelayLogger(
            str(
                output_dir
            )
        )

        logger.log_step(
            step_id=1,
            engine=engine,
            include_field=True,
        )

        json_path = (
            output_dir
            / "delay_step_000001.json"
        )

        field_path = (
            output_dir
            / "delay_field_000001.npz"
        )

        if not json_path.is_file():
            raise RuntimeError(
                "JSON metric snapshot was not created."
            )

        if not field_path.is_file():
            raise RuntimeError(
                "NPZ field snapshot was not created."
            )

        with json_path.open(
            "r",
            encoding="utf-8",
        ) as stream:
            record = json.load(
                stream
            )

        if record.get(
            "step"
        ) != 1:
            raise RuntimeError(
                "Incorrect step identifier in JSON snapshot."
            )

        if record.get(
            "backend"
        ) != "cpu":
            raise RuntimeError(
                "Incorrect backend identifier in JSON snapshot."
            )

        if "metrics" not in record:
            raise RuntimeError(
                "Metrics are missing from JSON snapshot."
            )

        for key in required_metrics:
            if key not in record["metrics"]:
                raise RuntimeError(
                    f"Metric {key} is missing "
                    "from JSON snapshot."
                )

        with np.load(
            field_path,
            allow_pickle=False,
        ) as saved_field:
            for key, expected_shape in expected_shapes.items():
                if key not in saved_field.files:
                    raise RuntimeError(
                        f"{key} missing from NPZ field snapshot."
                    )

                if saved_field[key].shape != expected_shape:
                    raise RuntimeError(
                        f"Incorrect shape for {key} "
                        "in NPZ snapshot."
                    )

                if not np.all(
                    np.isfinite(
                        saved_field[key]
                    )
                ):
                    raise RuntimeError(
                        f"Non-finite values in saved field: {key}"
                    )

    print(
        "EDK spatiotemporal phase-delay smoke test passed."
    )

    print(
        metrics
    )


if __name__ == "__main__":
    main()
