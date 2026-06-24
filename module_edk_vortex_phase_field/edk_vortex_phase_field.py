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
class VortexEngineConfig:
    num_domains: int = 4096
    neighbor_count: int = 24
    coupling_strength_k: float = 150.0
    sakaguchi_phase_lag_alpha: float = 0.15
    wave_velocity_c: float = 12.0
    vortex_current_strength_xi: float = 2.5
    vortex_feedback_kappa: float = 0.35
    amplitude_growth_mu: float = 1.0
    amplitude_coupling: float = 0.15
    amplitude_pressure_damping: float = 0.25
    axis_radial_mix: float = 0.35
    curl_regularization: float = 1e-4
    coordinate_half_extent: float = 5.0
    knn_chunk_size: int = 128
    mass_scale: float = 10.0
    vortex_retention_gain: float = 0.20
    vortex_destabilization_gain: float = 0.20
    seed: int = 42
    dtype: str = "float32"
    backend: BackendName = "auto"


class EDKVortexPhaseFieldEngine:
    """
    Numerical EDK vortex phase-field engine.

    The engine uses:
    - delayed Kuramoto-Sakaguchi coupling;
    - a radial and a tangential pair-current decomposition;
    - a local least-squares estimate of curl J on a 3D neighbor graph;
    - signed vorticity projected onto a local axis field;
    - explicit separation between R(t) and a model-specific C_proxy(t).

    Important:
    R(t) is the Kuramoto phase-order parameter.
    C_proxy(t) is a numerical proxy and is not identified with the complete
    general endogenous structural coherence C(t).
    """

    def __init__(self, config: VortexEngineConfig | None = None):
        self.config = config or VortexEngineConfig()
        self.xp, self.backend_name = self._select_backend(self.config.backend)
        self.dtype = getattr(self.xp, self.config.dtype)

        if self.config.num_domains < 8:
            raise ValueError("num_domains must be at least 8.")

        if not 3 <= self.config.neighbor_count < self.config.num_domains:
            raise ValueError(
                "neighbor_count must be at least 3 and smaller than num_domains."
            )

        if self.config.wave_velocity_c <= 0:
            raise ValueError("wave_velocity_c must be positive.")

        if self.config.knn_chunk_size < 1:
            raise ValueError("knn_chunk_size must be positive.")

        self.N = self.config.num_domains
        self.K = self.config.coupling_strength_k
        self.alpha = self.config.sakaguchi_phase_lag_alpha
        self.c = self.config.wave_velocity_c
        self.xi = self.config.vortex_current_strength_xi
        self.kappa_vortex = self.config.vortex_feedback_kappa

        self.xp.random.seed(self.config.seed)

        self.phases = self.xp.random.uniform(
            -self.xp.pi,
            self.xp.pi,
            self.N,
        ).astype(self.dtype)

        self.amplitudes = self.xp.random.uniform(
            0.8,
            1.2,
            self.N,
        ).astype(self.dtype)

        self.natural_frequencies = self.xp.random.normal(
            0.0,
            0.05,
            self.N,
        ).astype(self.dtype)

        half_extent = self.config.coordinate_half_extent

        self.coords_3d = self.xp.random.uniform(
            -half_extent,
            half_extent,
            (self.N, 3),
        ).astype(self.dtype)

        (
            self.neighbor_indices,
            self.edge_vectors,
            self.edge_distances,
        ) = self._build_knn_graph()

        self.direction_tensors = self.edge_vectors / (
            self.edge_distances[..., None] + self._eps
        )

        self.local_axes = self._build_local_axes()
        self.tangential_directions = self._build_tangential_directions()

        sigma = self.xp.median(self.edge_distances)
        sigma = self.xp.maximum(
            sigma,
            self.dtype(10.0 * self._eps),
        )

        raw_weights = self.xp.exp(
            -(self.edge_distances ** 2) / (2.0 * sigma ** 2)
        )

        self.neighbor_weights = raw_weights / (
            self.xp.sum(raw_weights, axis=1, keepdims=True)
            + self._eps
        )

        self._history_dt: float | None = None
        self._history: Any | None = None
        self._history_head = 0
        self._delay_steps: Any | None = None

        self.R_t = 0.0
        self.phase_amplitude_coherence = 0.0
        self.local_phase_coherence = 0.0
        self.amplitude_retention = 0.0
        self.C_proxy_t = 0.0
        self.interface_retention_proxy = 0.0
        self.M_proxy_t = 0.0
        self.mean_vorticity = 0.0
        self.signed_vorticity_mean = 0.0
        self.vortex_alignment = 0.0
        self.continuum_appearance_index = 0.0

        self.node_exchange_current = self.xp.zeros(
            (self.N, 3),
            dtype=self.dtype,
        )

        self.curl_J = self.xp.zeros(
            (self.N, 3),
            dtype=self.dtype,
        )

        self.signed_vorticity = self.xp.zeros(
            self.N,
            dtype=self.dtype,
        )

        self._update_order_metrics()

    @property
    def _eps(self) -> float:
        return float(
            np.finfo(
                np.dtype(self.config.dtype)
            ).eps
        )

    @staticmethod
    def _select_backend(backend: BackendName):
        if backend not in {"auto", "cpu", "gpu"}:
            raise ValueError(
                "backend must be 'auto', 'cpu', or 'gpu'."
            )

        if backend == "cpu":
            return np, "cpu"

        if _cupy is None:
            if backend == "gpu":
                raise RuntimeError(
                    "GPU backend requested, but CuPy is not installed."
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
                    "GPU backend requested, but no CUDA device is available."
                )

            return np, "cpu"

        return _cupy, "gpu"

    def _to_numpy(self, value: Any) -> np.ndarray:
        if self.backend_name == "gpu":
            return _cupy.asnumpy(value)

        return np.asarray(value)

    def _scalar(self, value: Any) -> float:
        if self.backend_name == "gpu":
            return float(
                _cupy.asnumpy(value)
            )

        return float(value)

    def _build_knn_graph(self):
        xp = self.xp
        n = self.N
        k = self.config.neighbor_count
        chunk_size = self.config.knn_chunk_size

        neighbor_indices = xp.empty(
            (n, k),
            dtype=xp.int32,
        )

        edge_vectors = xp.empty(
            (n, k, 3),
            dtype=self.dtype,
        )

        edge_distances = xp.empty(
            (n, k),
            dtype=self.dtype,
        )

        all_coords = self.coords_3d

        for start in range(0, n, chunk_size):
            stop = min(start + chunk_size, n)

            query = all_coords[start:stop]

            coordinate_difference = (
                all_coords[None, :, :]
                - query[:, None, :]
            )

            squared_distance = xp.sum(
                coordinate_difference
                * coordinate_difference,
                axis=-1,
            )

            local_rows = xp.arange(stop - start)
            global_rows = xp.arange(start, stop)

            squared_distance[
                local_rows,
                global_rows,
            ] = xp.inf

            partial_indices = xp.argpartition(
                squared_distance,
                kth=k - 1,
                axis=1,
            )[:, :k]

            selected_squared_distance = xp.take_along_axis(
                squared_distance,
                partial_indices,
                axis=1,
            )

            order = xp.argsort(
                selected_squared_distance,
                axis=1,
            )

            selected_indices = xp.take_along_axis(
                partial_indices,
                order,
                axis=1,
            )

            selected_squared_distance = xp.take_along_axis(
                selected_squared_distance,
                order,
                axis=1,
            )

            selected_coords = all_coords[
                selected_indices
            ]

            selected_vectors = (
                selected_coords
                - query[:, None, :]
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
            ).astype(self.dtype)

        return (
            neighbor_indices,
            edge_vectors,
            edge_distances,
        )

    def _build_local_axes(self):
        xp = self.xp

        global_axis = xp.asarray(
            [0.0, 0.0, 1.0],
            dtype=self.dtype,
        )

        radial_vectors = (
            self.coords_3d
            - xp.mean(
                self.coords_3d,
                axis=0,
                keepdims=True,
            )
        )

        radial_norm = xp.sqrt(
            xp.sum(
                radial_vectors * radial_vectors,
                axis=1,
                keepdims=True,
            )
        )

        radial_unit_vectors = radial_vectors / (
            radial_norm + self._eps
        )

        axes = (
            global_axis[None, :]
            + self.config.axis_radial_mix
            * radial_unit_vectors
        )

        axis_norm = xp.sqrt(
            xp.sum(
                axes * axes,
                axis=1,
                keepdims=True,
            )
        )

        return axes / (
            axis_norm + self._eps
        )

    def _build_tangential_directions(self):
        xp = self.xp

        axes = self.local_axes[:, None, :]

        tangential_directions = xp.cross(
            axes,
            self.direction_tensors,
            axis=-1,
        )

        tangential_norm = xp.sqrt(
            xp.sum(
                tangential_directions
                * tangential_directions,
                axis=-1,
                keepdims=True,
            )
        )

        fallback_axis_x = xp.asarray(
            [1.0, 0.0, 0.0],
            dtype=self.dtype,
        )

        fallback_x = xp.cross(
            fallback_axis_x[None, None, :],
            self.direction_tensors,
            axis=-1,
        )

        fallback_x_norm = xp.sqrt(
            xp.sum(
                fallback_x * fallback_x,
                axis=-1,
                keepdims=True,
            )
        )

        fallback_axis_y = xp.asarray(
            [0.0, 1.0, 0.0],
            dtype=self.dtype,
        )

        fallback_y = xp.cross(
            fallback_axis_y[None, None, :],
            self.direction_tensors,
            axis=-1,
        )

        use_x_fallback = tangential_norm < 1e-6

        tangential_directions = xp.where(
            use_x_fallback,
            fallback_x,
            tangential_directions,
        )

        tangential_norm = xp.where(
            use_x_fallback,
            fallback_x_norm,
            tangential_norm,
        )

        use_y_fallback = tangential_norm < 1e-6

        tangential_directions = xp.where(
            use_y_fallback,
            fallback_y,
            tangential_directions,
        )

        tangential_norm = xp.sqrt(
            xp.sum(
                tangential_directions
                * tangential_directions,
                axis=-1,
                keepdims=True,
            )
        )

        return tangential_directions / (
            tangential_norm + self._eps
        )

    def _initialize_delay_history(
        self,
        dt: float,
    ) -> None:
        if dt <= 0:
            raise ValueError(
                "dt must be positive."
            )

        max_delay = self._scalar(
            self.xp.max(
                self.edge_distances
                / self.c
            )
        )

        history_size = int(
            math.ceil(
                max_delay / dt
            )
        ) + 2

        self._delay_steps = self.xp.clip(
            self.xp.rint(
                self.edge_distances
                / (self.c * dt)
            ).astype(self.xp.int32),
            0,
            history_size - 1,
        )

        self._history = self.xp.empty(
            (history_size, self.N),
            dtype=self.dtype,
        )

        self._history[:] = self.phases[None, :]
        self._history_head = 0
        self._history_dt = float(dt)

    def _get_delayed_neighbor_phases(
        self,
        dt: float,
    ):
        if self._history is None:
            self._initialize_delay_history(dt)

        elif not math.isclose(
            float(dt),
            float(self._history_dt),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "dt changed after delay history initialization. "
                "Create a new engine or keep dt constant."
            )

        history_indices = (
            self._history_head
            - self._delay_steps
        ) % self._history.shape[0]

        return self._history[
            history_indices,
            self.neighbor_indices,
        ]

    def _estimate_discrete_curl(
        self,
        node_current,
    ):
        xp = self.xp

        edge_vectors = self.edge_vectors

        neighbor_current_difference = (
            node_current[
                self.neighbor_indices
            ]
            - node_current[:, None, :]
        )

        weights = self.neighbor_weights[
            ...,
            None,
        ]

        normal_matrix = xp.einsum(
            "nki,nkj->nij",
            edge_vectors * weights,
            edge_vectors,
        )

        right_hand_matrix = xp.einsum(
            "nki,nkj->nij",
            edge_vectors * weights,
            neighbor_current_difference,
        )

        identity = xp.eye(
            3,
            dtype=self.dtype,
        )[None, :, :]

        normal_matrix = (
            normal_matrix
            + self.config.curl_regularization
            * identity
        )

        current_gradient = xp.linalg.solve(
            normal_matrix,
            right_hand_matrix,
        )

        curl_x = (
            current_gradient[:, 1, 2]
            - current_gradient[:, 2, 1]
        )

        curl_y = (
            current_gradient[:, 2, 0]
            - current_gradient[:, 0, 2]
        )

        curl_z = (
            current_gradient[:, 0, 1]
            - current_gradient[:, 1, 0]
        )

        return xp.stack(
            (
                curl_x,
                curl_y,
                curl_z,
            ),
            axis=1,
        )

    def _compute_pair_and_node_currents(
        self,
        delayed_neighbor_phases,
    ):
        phase_difference = (
            delayed_neighbor_phases
            - self.phases[:, None]
            - self.alpha
        )

        pair_scalar = self.xp.sin(
            phase_difference
        )

        radial_current = (
            pair_scalar[..., None]
            * self.direction_tensors
        )

        tangential_current = (
            self.xi
            * pair_scalar[..., None]
            * self.tangential_directions
        )

        pair_current = (
            radial_current
            + tangential_current
        ) * self.neighbor_weights[..., None]

        node_current = self.xp.sum(
            pair_current,
            axis=1,
        )

        return (
            phase_difference,
            node_current,
        )

    def _update_order_metrics(self) -> None:
        xp = self.xp

        complex_phase_order = xp.mean(
            xp.exp(
                1j * self.phases
            )
        )

        self.R_t = self._scalar(
            xp.abs(
                complex_phase_order
            )
        )

        weighted_complex_order = xp.mean(
            self.amplitudes
            * xp.exp(
                1j * self.phases
            )
        )

        mean_amplitude = xp.mean(
            self.amplitudes
        )

        phase_amplitude_order = (
            xp.abs(
                weighted_complex_order
            )
            / (
                mean_amplitude
                + self._eps
            )
        )

        self.phase_amplitude_coherence = self._scalar(
            xp.clip(
                phase_amplitude_order,
                0.0,
                1.0,
            )
        )

        neighbor_phases = self.phases[
            self.neighbor_indices
        ]

        local_phase_difference = (
            neighbor_phases
            - self.phases[:, None]
        )

        local_order_nodes = xp.abs(
            xp.sum(
                self.neighbor_weights
                * xp.exp(
                    1j * local_phase_difference
                ),
                axis=1,
            )
        )

        self.local_phase_coherence = self._scalar(
            xp.clip(
                xp.mean(
                    local_order_nodes
                ),
                0.0,
                1.0,
            )
        )

        amplitude_variation = (
            xp.std(
                self.amplitudes
            )
            / (
                xp.mean(
                    self.amplitudes
                )
                + self._eps
            )
        )

        self.amplitude_retention = self._scalar(
            xp.clip(
                xp.exp(
                    -amplitude_variation
                ),
                0.0,
                1.0,
            )
        )

        coherence_product = (
            self.phase_amplitude_coherence
            * self.local_phase_coherence
            * self.amplitude_retention
        )

        self.C_proxy_t = float(
            np.clip(
                coherence_product
                ** (1.0 / 3.0),
                0.0,
                1.0,
            )
        )

    def process_vortex_delayed_interval(
        self,
        external_forcing_density: float,
        external_pressure: float,
        dt: float,
        external_forcing_phase: float | None = None,
    ) -> dict[str, float]:
        """
        Advance the system by one tact-by-tact interval.

        The local discrete curl is estimated from the node exchange-current
        field.

        Signed vorticity is the projection of curl J onto the local axis field.

        Positive and negative projections are retained separately in the
        appearance-index calculation.
        """

        if external_pressure < 0:
            raise ValueError(
                "external_pressure must be non-negative."
            )

        xp = self.xp

        delayed_neighbor_phases = (
            self._get_delayed_neighbor_phases(
                dt
            )
        )

        (
            phase_difference,
            node_current,
        ) = self._compute_pair_and_node_currents(
            delayed_neighbor_phases
        )

        curl_j = self._estimate_discrete_curl(
            node_current
        )

        signed_vorticity = xp.sum(
            curl_j
            * self.local_axes,
            axis=1,
        )

        absolute_vorticity = xp.sqrt(
            xp.sum(
                curl_j
                * curl_j,
                axis=1,
            )
        )

        vorticity_scale = (
            xp.median(
                xp.abs(
                    signed_vorticity
                )
            )
            + self._eps
        )

        normalized_signed_vorticity = xp.tanh(
            signed_vorticity
            / vorticity_scale
        )

        self.node_exchange_current = node_current
        self.curl_J = curl_j
        self.signed_vorticity = signed_vorticity

        self.mean_vorticity = self._scalar(
            xp.mean(
                absolute_vorticity
            )
        )

        self.signed_vorticity_mean = self._scalar(
            xp.mean(
                signed_vorticity
            )
        )

        self.vortex_alignment = self._scalar(
            xp.mean(
                normalized_signed_vorticity
            )
        )

        coupling_term = self.K * xp.sum(
            self.neighbor_weights
            * xp.sin(
                phase_difference
            ),
            axis=1,
        )

        vortex_feedback = (
            self.kappa_vortex
            * normalized_signed_vorticity
        )

        if external_forcing_phase is None:
            order_parameter = xp.mean(
                xp.exp(
                    1j * self.phases
                )
            )

            forcing_phase = xp.angle(
                order_parameter
            )

        else:
            forcing_phase = self.dtype(
                external_forcing_phase
            )

        forcing_term = (
            external_forcing_density
            * xp.sin(
                forcing_phase
                - self.phases
            )
        )

        phase_velocity = (
            self.natural_frequencies
            + coupling_term
            + vortex_feedback
            + forcing_term
        )

        neighbor_mean_amplitude = xp.sum(
            self.neighbor_weights
            * self.amplitudes[
                self.neighbor_indices
            ],
            axis=1,
        )

        amplitude_velocity = (
            self.config.amplitude_growth_mu
            * self.amplitudes
            * (
                1.0
                - self.amplitudes ** 2
            )
            + self.config.amplitude_coupling
            * (
                neighbor_mean_amplitude
                - self.amplitudes
            )
            - self.config.amplitude_pressure_damping
            * external_pressure
            * self.amplitudes
        )

        self.phases = (
            self.phases
            + phase_velocity * dt
            + xp.pi
        ) % (
            2.0 * xp.pi
        ) - xp.pi

        self.amplitudes = xp.clip(
            self.amplitudes
            + amplitude_velocity * dt,
            0.05,
            3.0,
        )

        self._history_head = (
            self._history_head + 1
        ) % self._history.shape[0]

        self._history[
            self._history_head
        ] = self.phases

        self._update_order_metrics()

        self.calculate_vortex_appearance(
            external_pressure
        )

        return self.metrics()

    def calculate_vortex_appearance(
        self,
        external_pressure: float,
    ) -> float:
        """
        Calculate a bounded model-specific appearance proxy.

        Vorticity is not assumed to be automatically stabilizing.

        Positive and negative signed alignment contribute separately.
        """

        if external_pressure < 0:
            raise ValueError(
                "external_pressure must be non-negative."
            )

        vorticity_level = (
            self.mean_vorticity
            / (
                1.0
                + self.mean_vorticity
            )
        )

        positive_vortex_support = (
            max(
                self.vortex_alignment,
                0.0,
            )
            * vorticity_level
        )

        negative_vortex_penalty = (
            max(
                -self.vortex_alignment,
                0.0,
            )
            * vorticity_level
        )

        pressure_penalty = (
            1.0
            / (
                1.0
                + external_pressure
            )
        )

        interface_proxy = (
            self.C_proxy_t
            * pressure_penalty
            + self.config.vortex_retention_gain
            * positive_vortex_support
            - self.config.vortex_destabilization_gain
            * negative_vortex_penalty
        )

        self.interface_retention_proxy = float(
            np.clip(
                interface_proxy,
                0.0,
                1.0,
            )
        )

        self.M_proxy_t = (
            self.config.mass_scale
            * self.interface_retention_proxy
            ** 2
        )

        appearance_index = (
            self.R_t
            * self.C_proxy_t
            * self.interface_retention_proxy
            * (
                1.0
                + math.log1p(
                    self.M_proxy_t
                )
            )
            * (
                1.0
                + positive_vortex_support
            )
            / (
                1.0
                + negative_vortex_penalty
            )
        )

        self.continuum_appearance_index = float(
            max(
                appearance_index,
                0.0,
            )
        )

        return self.continuum_appearance_index

    def metrics(self) -> dict[str, float]:
        return {
            "R_t_phase_order": self.R_t,
            "phase_amplitude_coherence": (
                self.phase_amplitude_coherence
            ),
            "local_phase_coherence": (
                self.local_phase_coherence
            ),
            "amplitude_retention": (
                self.amplitude_retention
            ),
            "C_proxy_t": self.C_proxy_t,
            "interface_retention_proxy": (
                self.interface_retention_proxy
            ),
            "M_proxy_t": self.M_proxy_t,
            "mean_vorticity_abs": (
                self.mean_vorticity
            ),
            "mean_vorticity_signed": (
                self.signed_vorticity_mean
            ),
            "vortex_alignment": (
                self.vortex_alignment
            ),
            "continuum_appearance_index": (
                self.continuum_appearance_index
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
            "amplitudes": self._to_numpy(
                self.amplitudes
            ),
            "node_exchange_current": self._to_numpy(
                self.node_exchange_current
            ),
            "curl_J": self._to_numpy(
                self.curl_J
            ),
            "signed_vorticity": self._to_numpy(
                self.signed_vorticity
            ),
            "local_axes": self._to_numpy(
                self.local_axes
            ),
        }


class EDKVortexLogger:
    def __init__(
        self,
        output_dir: str = "edk_vortex_snapshots",
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
        engine: EDKVortexPhaseFieldEngine,
        include_field: bool = False,
    ) -> None:
        snapshot = {
            "step": int(step_id),
            "backend": engine.backend_name,
            "config": asdict(
                engine.config
            ),
            "metrics": engine.metrics(),
        }

        json_path = (
            self.output_dir
            / f"vortex_step_{step_id:06d}.json"
        )

        with json_path.open(
            "w",
            encoding="utf-8",
        ) as stream:
            json.dump(
                snapshot,
                stream,
                indent=2,
                ensure_ascii=False,
            )

        if include_field:
            field_path = (
                self.output_dir
                / f"vortex_field_{step_id:06d}.npz"
            )

            np.savez_compressed(
                field_path,
                **engine.export_field_snapshot(),
            )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "EDK delayed vortex phase-field engine."
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
        default=50,
    )

    parser.add_argument(
        "--dt",
        type=float,
        default=0.005,
    )

    parser.add_argument(
        "--forcing",
        type=float,
        default=8.0,
    )

    parser.add_argument(
        "--pressure",
        type=float,
        default=0.1,
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
        default="edk_vortex_snapshots",
    )

    return parser


def main() -> None:
    args = build_argument_parser().parse_args()

    config = VortexEngineConfig(
        num_domains=args.domains,
        neighbor_count=args.neighbors,
        backend=args.backend,
    )

    engine = EDKVortexPhaseFieldEngine(
        config
    )

    logger = EDKVortexLogger(
        args.output_dir
    )

    print(
        "[EDK VORTEX ENGINE] "
        f"backend={engine.backend_name}, "
        f"domains={engine.N}, "
        f"neighbors={config.neighbor_count}"
    )

    for step in range(
        1,
        args.steps + 1,
    ):
        metrics = (
            engine.process_vortex_delayed_interval(
                external_forcing_density=(
                    args.forcing
                ),
                external_pressure=(
                    args.pressure
                ),
                dt=args.dt,
            )
        )

        if step % args.log_every == 0:
            include_field = (
                args.field_every > 0
                and step % args.field_every == 0
            )

            logger.log_step(
                step,
                engine,
                include_field=include_field,
            )

        print(
            f"[step {step:04d}] "
            f"R={metrics['R_t_phase_order']:.4f} | "
            f"C_proxy={metrics['C_proxy_t']:.4f} | "
            f"|curl J|={metrics['mean_vorticity_abs']:.6f} | "
            f"alignment={metrics['vortex_alignment']:.4f} | "
            f"CAI={metrics['continuum_appearance_index']:.4f}"
        )


if __name__ == "__main__":
    main()
