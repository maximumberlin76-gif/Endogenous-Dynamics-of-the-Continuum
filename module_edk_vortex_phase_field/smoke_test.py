from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import numpy as np

try:
    from .edk_vortex_phase_field import (
        EDKVortexLogger,
        EDKVortexPhaseFieldEngine,
        VortexEngineConfig,
    )
except ImportError:
    from edk_vortex_phase_field import (
        EDKVortexLogger,
        EDKVortexPhaseFieldEngine,
        VortexEngineConfig,
    )


def _assert_finite_metric(
    metrics: dict[str, float],
    key: str,
) -> None:
    value = metrics[key]

    if not math.isfinite(value):
        raise RuntimeError(
            f"Non-finite metric: {key}={value}"
        )


def _assert_unit_interval(
    metrics: dict[str, float],
    key: str,
) -> None:
    value = metrics[key]

    if not 0.0 <= value <= 1.0:
        raise RuntimeError(
            f"Metric outside [0, 1]: {key}={value}"
        )


def main() -> None:
    config = VortexEngineConfig(
        num_domains=128,
        neighbor_count=12,
        coupling_strength_k=25.0,
        vortex_current_strength_xi=2.5,
        vortex_feedback_kappa=0.35,
        backend="cpu",
        knn_chunk_size=32,
        seed=7,
    )

    engine = EDKVortexPhaseFieldEngine(
        config
    )

    metrics: dict[str, float] = {}

    for _ in range(5):
        metrics = (
            engine.process_vortex_delayed_interval(
                external_forcing_density=1.5,
                external_pressure=0.1,
                dt=0.01,
            )
        )

    required_metrics = (
        "R_t_phase_order",
        "phase_amplitude_coherence",
        "local_phase_coherence",
        "amplitude_retention",
        "C_proxy_t",
        "interface_retention_proxy",
        "M_proxy_t",
        "mean_vorticity_abs",
        "mean_vorticity_signed",
        "vortex_alignment",
        "continuum_appearance_index",
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

    for key in (
        "R_t_phase_order",
        "phase_amplitude_coherence",
        "local_phase_coherence",
        "amplitude_retention",
        "C_proxy_t",
        "interface_retention_proxy",
    ):
        _assert_unit_interval(
            metrics,
            key,
        )

    if not -1.0 <= metrics["vortex_alignment"] <= 1.0:
        raise RuntimeError(
            "vortex_alignment outside [-1, 1]: "
            f"{metrics['vortex_alignment']}"
        )

    if metrics["M_proxy_t"] < 0.0:
        raise RuntimeError(
            "M_proxy_t must be non-negative."
        )

    if metrics["continuum_appearance_index"] < 0.0:
        raise RuntimeError(
            "continuum_appearance_index must be non-negative."
        )

    if metrics["mean_vorticity_abs"] <= 0.0:
        raise RuntimeError(
            "Discrete curl field remained identically zero."
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
        "amplitudes": (
            config.num_domains,
        ),
        "node_exchange_current": (
            config.num_domains,
            3,
        ),
        "curl_J": (
            config.num_domains,
            3,
        ),
        "signed_vorticity": (
            config.num_domains,
        ),
        "local_axes": (
            config.num_domains,
            3,
        ),
    }

    for key, expected_shape in expected_shapes.items():
        array = np.asarray(
            field[key]
        )

        if array.shape != expected_shape:
            raise RuntimeError(
                f"Unexpected shape for {key}: "
                f"{array.shape} != {expected_shape}"
            )

        if not np.all(
            np.isfinite(array)
        ):
            raise RuntimeError(
                f"Non-finite values in field: {key}"
            )

    if np.allclose(
        field["curl_J"],
        0.0,
    ):
        raise RuntimeError(
            "Exported curl_J field is identically zero."
        )

    with tempfile.TemporaryDirectory(
        prefix="edk_vortex_smoke_"
    ) as temp_dir:
        output_dir = Path(
            temp_dir
        )

        logger = EDKVortexLogger(
            str(output_dir)
        )

        logger.log_step(
            step_id=1,
            engine=engine,
            include_field=True,
        )

        json_path = (
            output_dir
            / "vortex_step_000001.json"
        )

        field_path = (
            output_dir
            / "vortex_field_000001.npz"
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

        if record.get("step") != 1:
            raise RuntimeError(
                "Incorrect step identifier in JSON snapshot."
            )

        if record.get("backend") != "cpu":
            raise RuntimeError(
                "Incorrect backend identifier in JSON snapshot."
            )

        with np.load(
            field_path
        ) as saved_field:
            if "curl_J" not in saved_field.files:
                raise RuntimeError(
                    "curl_J missing from NPZ field snapshot."
                )

            if saved_field["curl_J"].shape != (
                config.num_domains,
                3,
            ):
                raise RuntimeError(
                    "Incorrect curl_J shape in NPZ snapshot."
                )

    print(
        "EDK vortex phase-field smoke test passed."
    )

    print(
        metrics
    )


if __name__ == "__main__":
    main()
