from __future__ import annotations

import json
import math
import sys
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
    try:
        from edk_spatiotemporal_phase_delay import (
            EDKDelayLogger,
            EDKSpatiotemporalPhaseDelayEngine,
            PhaseDelayConfig,
        )
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]

        if str(repo_root) not in sys.path:
            sys.path.insert(
                0,
                str(repo_root),
            )

        from module_edk_spatiotemporal_phase_delay.edk_spatiotemporal_phase_delay import (
            EDKDelayLogger,
            EDKSpatiotemporalPhaseDelayEngine,
            PhaseDelayConfig,
        )


def _assert_finite_metric(
    metrics: dict[str, float],
    key: str,
) -> None:
    value = float(
        metrics[
            key
        ]
    )

    if not math.isfinite(
        value
    ):
        raise RuntimeError(
            f"Non-finite metric: {key}={value}"
        )


def _assert_interval(
    metrics: dict[str, float],
    key: str,
    lower: float,
    upper: float,
) -> None:
    value = float(
        metrics[
            key
        ]
    )

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

    for _ in range(
        8
    ):
        metrics = engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=dt,
        )

    required_metrics = (
        "tact_index",
        "step",
        "simulation_time",
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

    tact = int(
        metrics[
            "tact_index"
        ]
    )

    if tact != int(
        engine.tact_index
    ):
        raise RuntimeError(
            "metrics.tact_index does not match engine.tact_index."
        )

    if int(
        metrics[
            "step"
        ]
    ) != tact:
        raise RuntimeError(
            "metrics.step does not match metrics.tact_index."
        )

    expected_time = (
        tact
        * dt
    )

    if not math.isclose(
        float(
            metrics[
                "simulation_time"
            ]
        ),
        expected_time,
        rel_tol=1.0e-9,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "simulation_time does not match tact_index * dt."
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

    if metrics[
        "phase_velocity_dispersion"
    ] < 0.0:
        raise RuntimeError(
            "phase_velocity_dispersion must be non-negative."
        )

    if metrics[
        "mean_delay"
    ] <= 0.0:
        raise RuntimeError(
            "mean_delay must be positive."
        )

    if metrics[
        "maximum_delay"
    ] < metrics[
        "mean_delay"
    ]:
        raise RuntimeError(
            "maximum_delay must not be smaller than mean_delay."
        )

    if metrics[
        "delay_dispersion"
    ] < 0.0:
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
            metrics[
                "history_buffer_depth"
            ]
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

    phase_tolerance = 1.0e-6

    if np.any(
        phases
        < -np.pi
        - phase_tolerance
    ) or np.any(
        phases
        >= np.pi
        + phase_tolerance
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
        delay_floor_steps
        < 0
    ):
        raise RuntimeError(
            "Negative integer delay step found."
        )

    if np.any(
        delay_fractions
        < 0.0
    ) or np.any(
        delay_fractions
        >= 1.0
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
        "edge_vectors": (
            config.num_domains,
            config.neighbor_count,
            3,
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
            field[
                key
            ]
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
        field[
            "neighbor_indices"
        ]
    )

    if np.any(
        neighbor_indices
        < 0
    ) or np.any(
        neighbor_indices
        >= config.num_domains
    ):
        raise RuntimeError(
            "neighbor_indices contains an out-of-range index."
        )

    row_indices = np.arange(
        config.num_domains
    )[
        :,
        None,
    ]

    if np.any(
        neighbor_indices
        == row_indices
    ):
        raise RuntimeError(
            "Self-coupling was found in the neighbor graph."
        )

    neighbor_weight_sums = np.sum(
        np.asarray(
            field[
                "neighbor_weights"
            ]
        ),
        axis=1,
    )

    if not np.allclose(
        neighbor_weight_sums,
        1.0,
        rtol=1.0e-5,
        atol=1.0e-6,
    ):
        raise RuntimeError(
            "Spatial coupling weights are not normalized."
        )

    if np.any(
        np.asarray(
            field[
                "edge_distances"
            ]
        )
        <= 0.0
    ):
        raise RuntimeError(
            "Non-positive edge distance found."
        )

    if np.any(
        np.asarray(
            field[
                "tau_ij"
            ]
        )
        <= 0.0
    ):
        raise RuntimeError(
            "Non-positive propagation delay found."
        )

    delayed_neighbor_phases = np.asarray(
        field[
            "delayed_neighbor_phases"
        ]
    )

    if np.any(
        delayed_neighbor_phases
        < -np.pi
        - phase_tolerance
    ) or np.any(
        delayed_neighbor_phases
        >= np.pi
        + phase_tolerance
    ):
        raise RuntimeError(
            "Delayed phases are outside [-pi, pi)."
        )

    try:
        engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=dt
            * 2.0,
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

        metrics_path, field_path = logger.log_tact(
            tact_id=tact,
            engine=engine,
            include_field=True,
        )

        tact_json_path = (
            output_dir
            / f"delay_tact_{tact:06d}.json"
        )

        step_json_path = (
            output_dir
            / f"delay_step_{tact:06d}.json"
        )

        expected_field_path = (
            output_dir
            / f"delay_field_{tact:06d}.npz"
        )

        if metrics_path != tact_json_path:
            raise RuntimeError(
                "log_tact did not return the primary tact JSON path."
            )

        if field_path != expected_field_path:
            raise RuntimeError(
                "log_tact did not return the expected field path."
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
            tact_record = json.load(
                stream
            )

        with step_json_path.open(
            "r",
            encoding="utf-8",
        ) as stream:
            step_record = json.load(
                stream
            )

        if tact_record != step_record:
            raise RuntimeError(
                "Primary tact JSON and compatibility step JSON differ."
            )

        if tact_record.get(
            "tact"
        ) != tact:
            raise RuntimeError(
                "Incorrect tact identifier in JSON snapshot."
            )

        if tact_record.get(
            "step"
        ) != tact:
            raise RuntimeError(
                "Incorrect step compatibility identifier in JSON snapshot."
            )

        if tact_record.get(
            "tact_index"
        ) != tact:
            raise RuntimeError(
                "Incorrect tact_index in JSON snapshot."
            )

        if not math.isclose(
            float(
                tact_record.get(
                    "simulation_time"
                )
            ),
            float(
                engine.simulation_time
            ),
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        ):
            raise RuntimeError(
                "Incorrect simulation_time in JSON snapshot."
            )

        if tact_record.get(
            "backend"
        ) != "cpu":
            raise RuntimeError(
                "Incorrect backend identifier in JSON snapshot."
            )

        if tact_record.get(
            "engine_class"
        ) != "EDKSpatiotemporalPhaseDelayEngine":
            raise RuntimeError(
                "Incorrect engine_class in JSON snapshot."
            )

        if "metrics" not in tact_record:
            raise RuntimeError(
                "Metrics are missing from JSON snapshot."
            )

        if "config" not in tact_record:
            raise RuntimeError(
                "Config is missing from JSON snapshot."
            )

        for key in required_metrics:
            if key not in tact_record[
                "metrics"
            ]:
                raise RuntimeError(
                    f"Metric {key} is missing "
                    "from JSON snapshot."
                )

        if int(
            tact_record[
                "metrics"
            ][
                "tact_index"
            ]
        ) != tact:
            raise RuntimeError(
                "metrics.tact_index does not match tact."
            )

        if int(
            tact_record[
                "metrics"
            ][
                "step"
            ]
        ) != tact:
            raise RuntimeError(
                "metrics.step does not match tact."
            )

        if not math.isclose(
            float(
                tact_record[
                    "metrics"
                ][
                    "simulation_time"
                ]
            ),
            float(
                engine.simulation_time
            ),
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        ):
            raise RuntimeError(
                "metrics.simulation_time does not match engine time."
            )

        with np.load(
            expected_field_path,
            allow_pickle=False,
        ) as saved_field:
            for key, expected_shape in expected_shapes.items():
                if key not in saved_field.files:
                    raise RuntimeError(
                        f"{key} missing from NPZ field snapshot."
                    )

                if saved_field[
                    key
                ].shape != expected_shape:
                    raise RuntimeError(
                        f"Incorrect shape for {key} "
                        "in NPZ snapshot."
                    )

                if not np.all(
                    np.isfinite(
                        saved_field[
                            key
                        ]
                    )
                ):
                    raise RuntimeError(
                        f"Non-finite values in saved field: {key}"
                    )

        if list(
            output_dir.glob(
                "*.tmp"
            )
        ):
            raise RuntimeError(
                "Temporary files were left after atomic writes."
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

    print(
        "EDK spatiotemporal phase-delay smoke test passed."
    )

    print(
        metrics
    )


if __name__ == "__main__":
    main()
