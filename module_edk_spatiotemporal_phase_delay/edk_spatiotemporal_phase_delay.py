from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

try:
    import cupy as _cupy
except Exception:
    _cupy = None


BackendName = Literal["auto", "cpu", "gpu"]


@dataclass(slots=True)
class PhaseDelayConfig:
    num_domains: int = 4096
    neighbor_count: int = 24
    coupling_strength_k: float = 150.0
    sakaguchi_phase_lag_alpha: float = 0.15
    wave_velocity_c: float = 12.0
    coordinate_half_extent: float = 5.0
    natural_frequency_mean: float = 0.0
    natural_frequency_std: float = 0.05
    knn_chunk_size: int = 128
    delay_safety_margin: int = 3
    seed: int = 42
    dtype: str = "float32"
    backend: BackendName = "auto"


class EDKSpatiotemporalPhaseDelayEngine:
    """
    Spatially distributed delayed Kuramoto-Sakaguchi engine.

    The engine preserves the distinction between:

    - the Kuramoto phase-order parameter R(t);
    - delayed local phase order;
    - complete phase coherence;
    - complete endogenous structural coherence C(t).

    This module does not calculate complete C(t).
    """

    def __init__(
        self,
        config: PhaseDelayConfig | None = None,
    ):
        self.config = config or PhaseDelayConfig()

        self.xp, self.backend_name = self._select_backend(
            self.config.backend
        )

        if self.config.num_domains < 4:
            raise ValueError(
                "num_domains must be at least 4."
            )

        if not 1 <= self.config.neighbor_count < self.config.num_domains:
            raise ValueError(
                "neighbor_count must be at least 1 "
                "and smaller than num_domains."
            )

        if self.config.wave_velocity_c <= 0:
            raise ValueError(
                "wave_velocity_c must be positive."
            )

        if self.config.knn_chunk_size < 1:
            raise ValueError(
                "knn_chunk_size must be positive."
            )

        if self.config.delay_safety_margin < 2:
            raise ValueError(
                "delay_safety_margin must be at least 2."
            )

        if self.config.dtype not in {
            "float32",
            "float64",
        }:
            raise ValueError(
                "dtype must be 'float32' or 'float64'."
            )

        self.dtype = getattr(
            self.xp,
            self.config.dtype,
        )

        self.N = int(
            self.config.num_domains
        )

        self.k = int(
            self.config.neighbor_count
        )

        self.K = float(
            self.config.coupling_strength_k
        )

        self.alpha = float(
            self.config.sakaguchi_phase_lag_alpha
        )

        self.c = float(
            self.config.wave_velocity_c
        )

        self.xp.random.seed(
            self.config.seed
        )

        self.phases = self.xp.random.uniform(
            -self.xp.pi,
            self.xp.pi,
            self.N,
        ).astype(
            self.dtype
        )

        self.natural_frequencies = self.xp.random.normal(
            self.config.natural_frequency_mean,
            self.config.natural_frequency_std,
            self.N,
        ).astype(
            self.dtype
        )

        half_extent = float(
            self.config.coordinate_half_extent
        )

        self.coords_3d = self.xp.random.uniform(
            -half_extent,
            half_extent,
            (
                self.N,
                3,
            ),
        ).astype(
            self.dtype
        )

        (
            self.neighbor_indices,
            self.edge_vectors,
            self.edge_distances,
        ) = self._build_knn_graph()

        sigma = self.xp.median(
            self.edge_distances
        )

        sigma = self.xp.maximum(
            sigma,
            self.dtype(
                10.0 * self._eps
            ),
        )

        raw_weights = self.xp.exp(
            -(
                self.edge_distances ** 2
            )
            /
            (
                2.0 * sigma ** 2
            )
        )

        self.neighbor_weights = (
            raw_weights
            /
            (
                self.xp.sum(
                    raw_weights,
                    axis=1,
                    keepdims=True,
                )
                +
                self._eps
            )
        )

        self.tau_ij = (
            self.edge_distances
            /
            self.c
        ).astype(
            self.dtype
        )

        self.mean_delay = self._scalar(
            self.xp.mean(
                self.tau_ij
            )
        )

        self.maximum_delay = self._scalar(
            self.xp.max(
                self.tau_ij
            )
        )

        self.delay_dispersion = self._scalar(
            self.xp.std(
                self.tau_ij
            )
        )

        self._history_dt: float | None = None
        self._history: Any | None = None
        self._history_head = 0
        self._delay_floor_steps: Any | None = None
        self._delay_fractions: Any | None = None

        self.delayed_neighbor_phases = self.xp.zeros(
            (
                self.N,
                self.k,
            ),
            dtype=self.dtype,
        )

        self.phase_velocity = self.xp.zeros(
            self.N,
            dtype=self.dtype,
        )

        self.R_t_phase_order = 0.0
        self.global_mean_phase = 0.0
        self.delayed_local_phase_order = 0.0
        self.mean_phase_velocity = 0.0
        self.phase_velocity_dispersion = 0.0
        self.delayed_coupling_energy_proxy = 0.0

        self._update_global_phase_metrics()

    @property
    def _eps(self) -> float:
        return float(
            np.finfo(
                np.dtype(
                    self.config.dtype
                )
            ).eps
        )

    @staticmethod
    def _select_backend(
        backend: BackendName,
    ):
        if backend not in {
            "auto",
            "cpu",
            "gpu",
        }:
            raise ValueError(
                "backend must be 'auto', 'cpu', or 'gpu'."
            )

        if backend == "cpu":
            return np, "cpu"

        if _cupy is None:
            if backend == "gpu":
                raise RuntimeError(
                    "GPU backend requested, "
                    "but CuPy is not installed."
                )

            return np, "cpu"

        try:
            device_count = int(
                _cupy.cuda.runtime.getDeviceCount()
            )
        except Exception:
            device_count = 0

        if device_count < 1:
            if backend == "gpu":
                raise RuntimeError(
                    "GPU backend requested, "
                    "but no CUDA device is available."
                )

            return np, "cpu"

        return _cupy, "gpu"

    def _to_numpy(
        self,
        value: Any,
    ) -> np.ndarray:
        if self.backend_name == "gpu":
            return _cupy.asnumpy(
                value
            )

        return np.asarray(
            value
        )

    def _scalar(
        self,
        value: Any,
    ) -> float:
        if self.backend_name == "gpu":
            return float(
                _cupy.asnumpy(
                    value
                )
            )

        return float(
            value
        )

    def _build_knn_graph(
        self,
    ):
        xp = self.xp
        n = self.N
        k = self.k

        chunk_size = int(
            self.config.knn_chunk_size
        )

        neighbor_indices = xp.empty(
            (
                n,
                k,
            ),
            dtype=xp.int32,
        )

        edge_vectors = xp.empty(
            (
                n,
                k,
                3,
            ),
            dtype=self.dtype,
        )

        edge_distances = xp.empty(
            (
                n,
                k,
            ),
            dtype=self.dtype,
        )

        all_coords = self.coords_3d

        for start in range(
            0,
            n,
            chunk_size,
        ):
            stop = min(
                start + chunk_size,
                n,
            )

            query = all_coords[
                start:stop
            ]

            displacement = (
                all_coords[
                    None,
                    :,
                    :,
                ]
                -
                query[
                    :,
                    None,
                    :,
                ]
            )

            squared_distance = xp.sum(
                displacement
                *
                displacement,
                axis=-1,
            )

            local_rows = xp.arange(
                stop - start
            )

            global_rows = xp.arange(
                start,
                stop,
            )

            squared_distance[
                local_rows,
                global_rows,
            ] = xp.inf

            candidate_indices = xp.argpartition(
                squared_distance,
                kth=k - 1,
                axis=1,
            )[
                :,
                :k,
            ]

            candidate_squared_distance = xp.take_along_axis(
                squared_distance,
                candidate_indices,
                axis=1,
            )

            order = xp.argsort(
                candidate_squared_distance,
                axis=1,
            )

            selected_indices = xp.take_along_axis(
                candidate_indices,
                order,
                axis=1,
            )

            selected_squared_distance = xp.take_along_axis(
                candidate_squared_distance,
                order,
                axis=1,
            )

            selected_coords = all_coords[
                selected_indices
            ]

            selected_vectors = (
                selected_coords
                -
                query[
                    :,
                    None,
                    :,
                ]
            )

            neighbor_indices[
                start:stop
            ] = selected_indices

            edge_vectors[
                start:stop
            ] = selected_vectors

            edge_distances[
                start:stop
            ] = xp.sqrt(
                selected_squared_distance
            ).astype(
                self.dtype
            )

        return (
            neighbor_indices,
            edge_vectors,
            edge_distances,
        )

    def _initialize_delay_history(
        self,
        dt: float,
    ) -> None:
        if dt <= 0:
            raise ValueError(
                "dt must be positive."
            )

        history_depth = int(
            math.ceil(
                self.maximum_delay
                /
                dt
            )
        ) + int(
            self.config.delay_safety_margin
        )

        history_depth = max(
            history_depth,
            3,
        )

        exact_delay_steps = (
            self.tau_ij
            /
            self.dtype(
                dt
            )
        )

        self._delay_floor_steps = self.xp.floor(
            exact_delay_steps
        ).astype(
            self.xp.int32
        )

        self._delay_fractions = (
            exact_delay_steps
            -
            self._delay_floor_steps
        ).astype(
            self.dtype
        )

        max_required_index = (
            self._delay_floor_steps
            +
            1
        )

        if self._scalar(
            self.xp.max(
                max_required_index
            )
        ) >= history_depth:
            history_depth = int(
                self._scalar(
                    self.xp.max(
                        max_required_index
                    )
                )
            ) + 1

        self._history = self.xp.empty(
            (
                history_depth,
                self.N,
            ),
            dtype=self.dtype,
        )

        self._history[:] = self.phases[
            None,
            :,
        ]

        self._history_head = 0
        self._history_dt = float(
            dt
        )

    def _reconstruct_delayed_neighbor_phases(
        self,
        dt: float,
    ):
        if self._history is None:
            self._initialize_delay_history(
                dt
            )

        elif not math.isclose(
            float(
                dt
            ),
            float(
                self._history_dt
            ),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "dt changed after delay-history initialization. "
                "Create a new engine or keep dt constant."
            )

        floor_steps = self._delay_floor_steps
        fractions = self._delay_fractions

        history_size = self._history.shape[
            0
        ]

        newer_indices = (
            self._history_head
            -
            floor_steps
        ) % history_size

        older_indices = (
            self._history_head
            -
            floor_steps
            -
            1
        ) % history_size

        newer_phases = self._history[
            newer_indices,
            self.neighbor_indices,
        ]

        older_phases = self._history[
            older_indices,
            self.neighbor_indices,
        ]

        newer_complex = self.xp.exp(
            1j
            *
            newer_phases
        )

        older_complex = self.xp.exp(
            1j
            *
            older_phases
        )

        interpolated_complex = (
            (
                1.0
                -
                fractions
            )
            *
            newer_complex
            +
            fractions
            *
            older_complex
        )

        magnitude = self.xp.abs(
            interpolated_complex
        )

        fallback = (
            magnitude
            <
            self._eps
        )

        interpolated_complex = self.xp.where(
            fallback,
            newer_complex,
            interpolated_complex,
        )

        return self.xp.angle(
            interpolated_complex
        ).astype(
            self.dtype
        )

    def _update_global_phase_metrics(
        self,
    ) -> None:
        order_parameter = self.xp.mean(
            self.xp.exp(
                1j
                *
                self.phases
            )
        )

        self.R_t_phase_order = self._scalar(
            self.xp.abs(
                order_parameter
            )
        )

        self.global_mean_phase = self._scalar(
            self.xp.angle(
                order_parameter
            )
        )

    def process_delayed_interval(
        self,
        external_forcing_density: float,
        dt: float,
        external_forcing_phase: float | None = None,
    ) -> dict[str, float]:
        """
        Advance the delayed phase system by one tact-by-tact interval.
        """

        if not math.isfinite(
            external_forcing_density
        ):
            raise ValueError(
                "external_forcing_density must be finite."
            )

        if external_forcing_phase is not None:
            if not math.isfinite(
                external_forcing_phase
            ):
                raise ValueError(
                    "external_forcing_phase must be finite."
                )

        delayed_neighbor_phases = (
            self._reconstruct_delayed_neighbor_phases(
                dt
            )
        )

        phase_difference = (
            delayed_neighbor_phases
            -
            self.phases[
                :,
                None,
            ]
            -
            self.alpha
        )

        coupling_term = (
            self.K
            *
            self.xp.sum(
                self.neighbor_weights
                *
                self.xp.sin(
                    phase_difference
                ),
                axis=1,
            )
        )

        if external_forcing_phase is None:
            forcing_phase = self.global_mean_phase
        else:
            forcing_phase = float(
                external_forcing_phase
            )

        forcing_term = (
            float(
                external_forcing_density
            )
            *
            self.xp.sin(
                forcing_phase
                -
                self.phases
            )
        )

        self.phase_velocity = (
            self.natural_frequencies
            +
            coupling_term
            +
            forcing_term
        ).astype(
            self.dtype
        )

        self.phases = (
            self.phases
            +
            self.phase_velocity
            *
            self.dtype(
                dt
            )
            +
            self.xp.pi
        ) % (
            2.0
            *
            self.xp.pi
        ) - self.xp.pi

        self._history_head = (
            self._history_head
            +
            1
        ) % self._history.shape[
            0
        ]

        self._history[
            self._history_head
        ] = self.phases

        self.delayed_neighbor_phases = (
            delayed_neighbor_phases
        )

        local_delayed_order = self.xp.abs(
            self.xp.sum(
                self.neighbor_weights
                *
                self.xp.exp(
                    1j
                    *
                    delayed_neighbor_phases
                ),
                axis=1,
            )
        )

        self.delayed_local_phase_order = self._scalar(
            self.xp.clip(
                self.xp.mean(
                    local_delayed_order
                ),
                0.0,
                1.0,
            )
        )

        self.mean_phase_velocity = self._scalar(
            self.xp.mean(
                self.phase_velocity
            )
        )

        self.phase_velocity_dispersion = self._scalar(
            self.xp.std(
                self.phase_velocity
            )
        )

        self.delayed_coupling_energy_proxy = self._scalar(
            self.xp.clip(
                self.xp.mean(
                    self.xp.sum(
                        self.neighbor_weights
                        *
                        self.xp.cos(
                            phase_difference
                        ),
                        axis=1,
                    )
                ),
                -1.0,
                1.0,
            )
        )

        self._update_global_phase_metrics()

        return self.metrics()

    def metrics(
        self,
    ) -> dict[str, float]:
        history_depth = (
            int(
                self._history.shape[
                    0
                ]
            )
            if self._history is not None
            else 0
        )

        return {
            "R_t_phase_order": (
                self.R_t_phase_order
            ),
            "global_mean_phase": (
                self.global_mean_phase
            ),
            "delayed_local_phase_order": (
                self.delayed_local_phase_order
            ),
            "mean_phase_velocity": (
                self.mean_phase_velocity
            ),
            "phase_velocity_dispersion": (
                self.phase_velocity_dispersion
            ),
            "mean_delay": (
                self.mean_delay
            ),
            "maximum_delay": (
                self.maximum_delay
            ),
            "delay_dispersion": (
                self.delay_dispersion
            ),
            "delayed_coupling_energy_proxy": (
                self.delayed_coupling_energy_proxy
            ),
            "history_buffer_depth": float(
                history_depth
            ),
        }

    def export_field_snapshot(
        self,
    ) -> dict[str, np.ndarray]:
        return {
            "coords_3d": self._to_numpy(
                self.coords_3d
            ),
            "phases": self._to_numpy(
                self.phases
            ),
            "natural_frequencies": self._to_numpy(
                self.natural_frequencies
            ),
            "neighbor_indices": self._to_numpy(
                self.neighbor_indices
            ),
            "edge_distances": self._to_numpy(
                self.edge_distances
            ),
            "tau_ij": self._to_numpy(
                self.tau_ij
            ),
            "neighbor_weights": self._to_numpy(
                self.neighbor_weights
            ),
            "delayed_neighbor_phases": self._to_numpy(
                self.delayed_neighbor_phases
            ),
            "phase_velocity": self._to_numpy(
                self.phase_velocity
            ),
        }


class EDKDelayLogger:
    def __init__(
        self,
        output_dir: str = "edk_delay_snapshots",
    ):
        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def log_step(
        self,
        step_id: int,
        engine: EDKSpatiotemporalPhaseDelayEngine,
        include_field: bool = False,
    ) -> None:
        record = {
            "step": int(
                step_id
            ),
            "backend": (
                engine.backend_name
            ),
            "config": asdict(
                engine.config
            ),
            "metrics": (
                engine.metrics()
            ),
        }

        json_path = (
            self.output_dir
            /
            f"delay_step_{step_id:06d}.json"
        )

        with json_path.open(
            "w",
            encoding="utf-8",
        ) as stream:
            json.dump(
                record,
                stream,
                indent=2,
                ensure_ascii=False,
            )

        if include_field:
            field_path = (
                self.output_dir
                /
                f"delay_field_{step_id:06d}.npz"
            )

            np.savez_compressed(
                field_path,
                **engine.export_field_snapshot(),
            )


def build_argument_parser(
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "EDK spatial-temporal delayed "
            "Kuramoto-Sakaguchi engine."
        )
    )

    parser.add_argument(
        "--domains",
        type=int,
        default=1024,
    )

    parser.add_argument(
        "--neighbors",
        type=int,
        default=24,
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--dt",
        type=float,
        default=0.005,
    )

    parser.add_argument(
        "--forcing",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--forcing-phase",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--backend",
        choices=[
            "auto",
            "cpu",
            "gpu",
        ],
        default="auto",
    )

    parser.add_argument(
        "--log-every",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--field-every",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--output-dir",
        default="edk_delay_snapshots",
    )

    return parser


def main(
) -> None:
    args = build_argument_parser().parse_args()

    if args.steps < 1:
        raise ValueError(
            "--steps must be positive."
        )

    if args.dt <= 0:
        raise ValueError(
            "--dt must be positive."
        )

    if args.log_every < 1:
        raise ValueError(
            "--log-every must be positive."
        )

    if args.field_every < 0:
        raise ValueError(
            "--field-every must be non-negative."
        )

    config = PhaseDelayConfig(
        num_domains=args.domains,
        neighbor_count=args.neighbors,
        backend=args.backend,
    )

    engine = EDKSpatiotemporalPhaseDelayEngine(
        config
    )

    logger = EDKDelayLogger(
        args.output_dir
    )

    print(
        "[EDK DELAY ENGINE] "
        f"backend={engine.backend_name}, "
        f"domains={engine.N}, "
        f"neighbors={engine.k}, "
        f"mean_delay={engine.mean_delay:.6f}, "
        f"maximum_delay={engine.maximum_delay:.6f}"
    )

    for step in range(
        1,
        args.steps + 1,
    ):
        metrics = engine.process_delayed_interval(
            external_forcing_density=(
                args.forcing
            ),
            external_forcing_phase=(
                args.forcing_phase
            ),
            dt=args.dt,
        )

        if step % args.log_every == 0:
            include_field = (
                args.field_every > 0
                and
                step % args.field_every == 0
            )

            logger.log_step(
                step_id=step,
                engine=engine,
                include_field=include_field,
            )

        print(
            f"[step {step:04d}] "
            f"R={metrics['R_t_phase_order']:.4f} | "
            f"R_delay="
            f"{metrics['delayed_local_phase_order']:.4f} | "
            f"mean_dtheta="
            f"{metrics['mean_phase_velocity']:.6f} | "
            f"std_dtheta="
            f"{metrics['phase_velocity_dispersion']:.6f} | "
            f"E_delay_proxy="
            f"{metrics['delayed_coupling_energy_proxy']:.4f}"
        )


if __name__ == "__main__":
    main()
