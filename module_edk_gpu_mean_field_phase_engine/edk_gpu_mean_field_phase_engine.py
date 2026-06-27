from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

import numpy as np

try:
    import cupy as _cupy
except Exception:
    _cupy = None


BackendMode = Literal["auto", "gpu", "cpu"]


@dataclass(frozen=True)
class MeanFieldPhaseConfig:
    num_domains: int = 16384
    coupling_strength_k: float = 120.0
    sakaguchi_phase_lag_alpha: float = 0.0

    natural_frequency_mean: float = 0.0
    natural_frequency_std: float = 0.1

    external_forcing_phase: float = 0.0
    phase_noise_strength: float = 0.0

    amplitude_growth_rate: float = 1.0
    amplitude_saturation_rate: float = 1.0
    amplitude_noise_strength: float = 0.1

    amplitude_minimum: float = 0.1
    amplitude_maximum: float = 5.0

    initial_amplitude_minimum: float = 0.5
    initial_amplitude_maximum: float = 1.5

    seed: int = 42
    dtype: str = "float32"
    backend: BackendMode = "auto"
    device_id: int = 0

    def validate(self) -> None:
        if self.num_domains < 2:
            raise ValueError(
                "num_domains must be at least 2."
            )

        finite_fields = {
            "coupling_strength_k": self.coupling_strength_k,
            "sakaguchi_phase_lag_alpha": self.sakaguchi_phase_lag_alpha,
            "natural_frequency_mean": self.natural_frequency_mean,
            "natural_frequency_std": self.natural_frequency_std,
            "external_forcing_phase": self.external_forcing_phase,
            "phase_noise_strength": self.phase_noise_strength,
            "amplitude_growth_rate": self.amplitude_growth_rate,
            "amplitude_saturation_rate": self.amplitude_saturation_rate,
            "amplitude_noise_strength": self.amplitude_noise_strength,
            "amplitude_minimum": self.amplitude_minimum,
            "amplitude_maximum": self.amplitude_maximum,
            "initial_amplitude_minimum": self.initial_amplitude_minimum,
            "initial_amplitude_maximum": self.initial_amplitude_maximum,
        }

        for name, value in finite_fields.items():
            if not math.isfinite(
                float(value)
            ):
                raise ValueError(
                    f"{name} must be finite."
                )

        if self.natural_frequency_std < 0.0:
            raise ValueError(
                "natural_frequency_std must be non-negative."
            )

        if self.phase_noise_strength < 0.0:
            raise ValueError(
                "phase_noise_strength must be non-negative."
            )

        if self.amplitude_noise_strength < 0.0:
            raise ValueError(
                "amplitude_noise_strength must be non-negative."
            )

        if self.amplitude_saturation_rate < 0.0:
            raise ValueError(
                "amplitude_saturation_rate must be non-negative."
            )

        if self.amplitude_minimum <= 0.0:
            raise ValueError(
                "amplitude_minimum must be positive."
            )

        if self.amplitude_maximum <= self.amplitude_minimum:
            raise ValueError(
                "amplitude_maximum must be greater than amplitude_minimum."
            )

        if self.initial_amplitude_minimum < self.amplitude_minimum:
            raise ValueError(
                "initial_amplitude_minimum must not be smaller than amplitude_minimum."
            )

        if self.initial_amplitude_maximum > self.amplitude_maximum:
            raise ValueError(
                "initial_amplitude_maximum must not exceed amplitude_maximum."
            )

        if self.initial_amplitude_maximum <= self.initial_amplitude_minimum:
            raise ValueError(
                "initial_amplitude_maximum must be greater than initial_amplitude_minimum."
            )

        if self.dtype not in {
            "float32",
            "float64",
        }:
            raise ValueError(
                "dtype must be 'float32' or 'float64'."
            )

        if self.backend not in {
            "auto",
            "gpu",
            "cpu",
        }:
            raise ValueError(
                "backend must be 'auto', 'gpu', or 'cpu'."
            )

        if self.device_id < 0:
            raise ValueError(
                "device_id must be non-negative."
            )


def _json_safe(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        np.ndarray,
    ):
        if value.ndim == 0:
            return _json_safe(
                value.item()
            )

        return {
            "__array__": True,
            "dtype": str(value.dtype),
            "shape": list(value.shape),
        }

    if isinstance(
        value,
        np.generic,
    ):
        return _json_safe(
            value.item()
        )

    if isinstance(
        value,
        Path,
    ):
        return str(value)

    if isinstance(
        value,
        complex,
    ):
        return {
            "real": float(value.real),
            "imag": float(value.imag),
        }

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    return repr(value)


class _BackendRandom:
    def __init__(
        self,
        xp: Any,
        seed: int,
        using_gpu: bool,
    ) -> None:
        self.xp = xp
        self.using_gpu = using_gpu

        if using_gpu:
            self.generator = xp.random.RandomState(
                seed
            )
        else:
            self.generator = np.random.default_rng(
                seed
            )

    def uniform(
        self,
        low: float,
        high: float,
        size: int,
        dtype: Any,
    ) -> Any:
        values = self.generator.uniform(
            low,
            high,
            size=size,
        )

        return self.xp.asarray(
            values,
            dtype=dtype,
        )

    def normal(
        self,
        mean: float,
        std: float,
        size: int,
        dtype: Any,
    ) -> Any:
        values = self.generator.normal(
            mean,
            std,
            size=size,
        )

        return self.xp.asarray(
            values,
            dtype=dtype,
        )


class EDKGPUMeanFieldPhaseEngine:
    """
    High-density global mean-field phase engine.

    The engine uses the exact Kuramoto-Sakaguchi
    mean-field identity.

    State-memory complexity: O(N).
    Computational complexity per tact: O(N).

    The engine does not construct an N x N
    phase-difference matrix.
    """

    def __init__(
        self,
        config: MeanFieldPhaseConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else MeanFieldPhaseConfig()
        )

        self.config.validate()

        (
            self.xp,
            self.backend_name,
            self.backend_library,
            self.using_gpu,
            self.active_device_id,
        ) = self._select_backend(
            backend=self.config.backend,
            device_id=self.config.device_id,
        )

        self.dtype = self.xp.dtype(
            self.config.dtype
        )

        if self.config.dtype == "float32":
            self.complex_dtype = self.xp.complex64
        else:
            self.complex_dtype = self.xp.complex128

        self.rng = _BackendRandom(
            xp=self.xp,
            seed=self.config.seed,
            using_gpu=self.using_gpu,
        )

        self.N = int(
            self.config.num_domains
        )

        self.K = float(
            self.config.coupling_strength_k
        )

        self.alpha = float(
            self.config.sakaguchi_phase_lag_alpha
        )

        self.phases = self.rng.uniform(
            low=-math.pi,
            high=math.pi,
            size=self.N,
            dtype=self.dtype,
        )

        self.amplitudes = self.rng.uniform(
            low=self.config.initial_amplitude_minimum,
            high=self.config.initial_amplitude_maximum,
            size=self.N,
            dtype=self.dtype,
        )

        self.natural_frequencies = self.rng.normal(
            mean=self.config.natural_frequency_mean,
            std=self.config.natural_frequency_std,
            size=self.N,
            dtype=self.dtype,
        )

        self.phase_velocity = self.xp.zeros(
            self.N,
            dtype=self.dtype,
        )

        self.amplitude_velocity = self.xp.zeros(
            self.N,
            dtype=self.dtype,
        )

        self.phase_noise_increment = self.xp.zeros(
            self.N,
            dtype=self.dtype,
        )

        self.amplitude_noise_increment = self.xp.zeros(
            self.N,
            dtype=self.dtype,
        )

        self.R_t_phase_order = 0.0
        self.global_mean_phase = 0.0
        self.phase_amplitude_order_proxy = 0.0

        self.mean_phase_velocity = 0.0
        self.phase_velocity_dispersion = 0.0

        self.mean_amplitude = 0.0
        self.amplitude_dispersion = 0.0
        self.minimum_amplitude = 0.0
        self.maximum_amplitude = 0.0

        self.coupling_energy_proxy = 0.0

        self.external_forcing_density = 0.0
        self.external_forcing_phase = float(
            self.config.external_forcing_phase
        )

        self.simulation_time = 0.0
        self.tact_index = 0
        self.step_index = 0

        self._refresh_diagnostics()
        self._validate_numerical_state()

    @staticmethod
    def _select_backend(
        backend: BackendMode,
        device_id: int,
    ) -> tuple[Any, str, str, bool, int | None]:
        if backend == "cpu":
            return (
                np,
                "cpu",
                "numpy",
                False,
                None,
            )

        if _cupy is None:
            if backend == "gpu":
                raise RuntimeError(
                    "GPU backend requested, but CuPy could not be imported."
                )

            return (
                np,
                "cpu",
                "numpy",
                False,
                None,
            )

        try:
            device_count = int(
                _cupy.cuda.runtime.getDeviceCount()
            )

            if device_count < 1:
                raise RuntimeError(
                    "No CUDA device is available."
                )

            if device_id >= device_count:
                raise RuntimeError(
                    f"device_id={device_id} is outside the available CUDA device range 0..{device_count - 1}."
                )

            _cupy.cuda.Device(
                device_id
            ).use()

            return (
                _cupy,
                "gpu",
                "cupy",
                True,
                device_id,
            )

        except Exception as exc:
            if backend == "gpu":
                raise RuntimeError(
                    "GPU backend requested, but CUDA initialization failed."
                ) from exc

            return (
                np,
                "cpu",
                "numpy",
                False,
                None,
            )

    def _scalar(
        self,
        value: Any,
    ) -> float:
        if self.using_gpu:
            return float(
                self.xp.asnumpy(
                    value
                )
            )

        return float(
            value
        )

    def _to_host(
        self,
        array: Any,
    ) -> np.ndarray:
        if self.using_gpu:
            return self.xp.asnumpy(
                array
            )

        return np.asarray(
            array
        )

    def _finite_array(
        self,
        array: Any,
    ) -> bool:
        return bool(
            self._scalar(
                self.xp.all(
                    self.xp.isfinite(
                        array
                    )
                )
            )
        )

    def _validate_numerical_state(
        self,
    ) -> None:
        arrays = {
            "phases": self.phases,
            "amplitudes": self.amplitudes,
            "natural_frequencies": self.natural_frequencies,
            "phase_velocity": self.phase_velocity,
            "amplitude_velocity": self.amplitude_velocity,
            "phase_noise_increment": self.phase_noise_increment,
            "amplitude_noise_increment": self.amplitude_noise_increment,
        }

        for name, array in arrays.items():
            if not self._finite_array(
                array
            ):
                raise FloatingPointError(
                    f"Non-finite values detected in {name}."
                )

        phase_min = self._scalar(
            self.xp.min(
                self.phases
            )
        )

        phase_max = self._scalar(
            self.xp.max(
                self.phases
            )
        )

        if (
            phase_min < -math.pi - 1.0e-6
            or phase_max >= math.pi + 1.0e-6
        ):
            raise FloatingPointError(
                "Phase wrapping left [-pi, pi)."
            )

        amplitude_min = self._scalar(
            self.xp.min(
                self.amplitudes
            )
        )

        amplitude_max = self._scalar(
            self.xp.max(
                self.amplitudes
            )
        )

        if amplitude_min < self.config.amplitude_minimum - 1.0e-6:
            raise FloatingPointError(
                "Amplitude minimum bound was violated."
            )

        if amplitude_max > self.config.amplitude_maximum + 1.0e-6:
            raise FloatingPointError(
                "Amplitude maximum bound was violated."
            )

        scalar_diagnostics = (
            self.R_t_phase_order,
            self.global_mean_phase,
            self.phase_amplitude_order_proxy,
            self.mean_phase_velocity,
            self.phase_velocity_dispersion,
            self.mean_amplitude,
            self.amplitude_dispersion,
            self.minimum_amplitude,
            self.maximum_amplitude,
            self.coupling_energy_proxy,
            self.external_forcing_density,
            self.external_forcing_phase,
            self.simulation_time,
        )

        for value in scalar_diagnostics:
            if not math.isfinite(
                float(value)
            ):
                raise FloatingPointError(
                    "Non-finite scalar diagnostic detected."
                )

    def _calculate_order_parameter(
        self,
    ) -> tuple[Any, Any, Any]:
        unit_phasors = self.xp.exp(
            1j
            * self.phases
        ).astype(
            self.complex_dtype,
            copy=False,
        )

        complex_order_parameter = self.xp.mean(
            unit_phasors
        )

        R_t = self.xp.clip(
            self.xp.abs(
                complex_order_parameter
            ),
            0.0,
            1.0,
        )

        mean_phase = self.xp.angle(
            complex_order_parameter
        )

        return (
            complex_order_parameter,
            R_t,
            mean_phase,
        )

    def _calculate_phase_amplitude_order_proxy(
        self,
    ) -> Any:
        weighted_phasors = (
            self.amplitudes
            * self.xp.exp(
                1j
                * self.phases
            )
        )

        amplitude_sum = self.xp.sum(
            self.amplitudes
        )

        host_dtype = (
            np.float32
            if self.config.dtype == "float32"
            else np.float64
        )

        epsilon = self.xp.asarray(
            np.finfo(
                host_dtype
            ).eps,
            dtype=self.dtype,
        )

        normalized_weighted_order = (
            self.xp.sum(
                weighted_phasors
            )
            / self.xp.maximum(
                amplitude_sum,
                epsilon,
            )
        )

        return self.xp.clip(
            self.xp.abs(
                normalized_weighted_order
            ),
            0.0,
            1.0,
        )

    def _refresh_diagnostics(
        self,
    ) -> None:
        (
            _,
            R_t,
            mean_phase,
        ) = self._calculate_order_parameter()

        phase_amplitude_proxy = (
            self._calculate_phase_amplitude_order_proxy()
        )

        coupling_energy = self.xp.clip(
            self.xp.mean(
                self.xp.cos(
                    mean_phase
                    - self.phases
                    - self.alpha
                )
            ),
            -1.0,
            1.0,
        )

        self.R_t_phase_order = self._scalar(
            R_t
        )

        self.global_mean_phase = self._scalar(
            mean_phase
        )

        self.phase_amplitude_order_proxy = (
            self._scalar(
                phase_amplitude_proxy
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

        self.mean_amplitude = self._scalar(
            self.xp.mean(
                self.amplitudes
            )
        )

        self.amplitude_dispersion = self._scalar(
            self.xp.std(
                self.amplitudes
            )
        )

        self.minimum_amplitude = self._scalar(
            self.xp.min(
                self.amplitudes
            )
        )

        self.maximum_amplitude = self._scalar(
            self.xp.max(
                self.amplitudes
            )
        )

        self.coupling_energy_proxy = self._scalar(
            coupling_energy
        )

    def set_coupling_strength(
        self,
        coupling_strength_k: float,
    ) -> None:
        if not math.isfinite(
            coupling_strength_k
        ):
            raise ValueError(
                "coupling_strength_k must be finite."
            )

        self.K = float(
            coupling_strength_k
        )

    def set_phase_lag(
        self,
        sakaguchi_phase_lag_alpha: float,
    ) -> None:
        if not math.isfinite(
            sakaguchi_phase_lag_alpha
        ):
            raise ValueError(
                "sakaguchi_phase_lag_alpha must be finite."
            )

        self.alpha = float(
            sakaguchi_phase_lag_alpha
        )

    def process_micro_interval(
        self,
        external_forcing_density: float,
        dt: float,
        external_forcing_phase: float | None = None,
    ) -> dict[str, float | int | str | None]:
        if not math.isfinite(
            external_forcing_density
        ):
            raise ValueError(
                "external_forcing_density must be finite."
            )

        if (
            not math.isfinite(
                dt
            )
            or dt <= 0.0
        ):
            raise ValueError(
                "dt must be a positive finite value."
            )

        forcing_phase = (
            self.config.external_forcing_phase
            if external_forcing_phase is None
            else external_forcing_phase
        )

        if not math.isfinite(
            forcing_phase
        ):
            raise ValueError(
                "external_forcing_phase must be finite."
            )

        (
            _,
            R_t,
            mean_phase,
        ) = self._calculate_order_parameter()

        coupling_term = (
            self.K
            * R_t
            * self.xp.sin(
                mean_phase
                - self.phases
                - self.alpha
            )
        )

        forcing_term = (
            float(
                external_forcing_density
            )
            * self.xp.sin(
                float(
                    forcing_phase
                )
                - self.phases
            )
        )

        deterministic_phase_velocity = (
            self.natural_frequencies
            + coupling_term
            + forcing_term
        )

        if self.config.phase_noise_strength > 0.0:
            self.phase_noise_increment = (
                self.config.phase_noise_strength
                * math.sqrt(
                    dt
                )
                * self.rng.normal(
                    mean=0.0,
                    std=1.0,
                    size=self.N,
                    dtype=self.dtype,
                )
            )
        else:
            self.phase_noise_increment.fill(
                0.0
            )

        self.phase_velocity = (
            deterministic_phase_velocity
            + self.phase_noise_increment
            / dt
        ).astype(
            self.dtype,
            copy=False,
        )

        self.phases = (
            (
                self.phases
                + deterministic_phase_velocity
                * dt
                + self.phase_noise_increment
                + math.pi
            )
            % (
                2.0
                * math.pi
            )
            - math.pi
        ).astype(
            self.dtype,
            copy=False,
        )

        amplitude_drift = (
            self.config.amplitude_growth_rate
            * self.amplitudes
            - self.config.amplitude_saturation_rate
            * self.amplitudes
            * self.amplitudes
            * self.amplitudes
        )

        if self.config.amplitude_noise_strength > 0.0:
            self.amplitude_noise_increment = (
                self.config.amplitude_noise_strength
                * math.sqrt(
                    dt
                )
                * self.rng.normal(
                    mean=0.0,
                    std=1.0,
                    size=self.N,
                    dtype=self.dtype,
                )
            )
        else:
            self.amplitude_noise_increment.fill(
                0.0
            )

        self.amplitude_velocity = (
            amplitude_drift
            + self.amplitude_noise_increment
            / dt
        ).astype(
            self.dtype,
            copy=False,
        )

        self.amplitudes = self.xp.clip(
            self.amplitudes
            + amplitude_drift
            * dt
            + self.amplitude_noise_increment,
            self.config.amplitude_minimum,
            self.config.amplitude_maximum,
        ).astype(
            self.dtype,
            copy=False,
        )

        self.external_forcing_density = float(
            external_forcing_density
        )

        self.external_forcing_phase = float(
            forcing_phase
        )

        self.simulation_time += float(
            dt
        )

        self.tact_index += 1
        self.step_index = self.tact_index

        self._refresh_diagnostics()
        self._validate_numerical_state()

        return self.get_metrics()

    def get_metrics(
        self,
    ) -> dict[str, float | int | str | None]:
        return {
            "R_t_phase_order": self.R_t_phase_order,
            "global_mean_phase": self.global_mean_phase,
            "phase_amplitude_order_proxy": self.phase_amplitude_order_proxy,
            "mean_phase_velocity": self.mean_phase_velocity,
            "phase_velocity_dispersion": self.phase_velocity_dispersion,
            "mean_amplitude": self.mean_amplitude,
            "amplitude_dispersion": self.amplitude_dispersion,
            "minimum_amplitude": self.minimum_amplitude,
            "maximum_amplitude": self.maximum_amplitude,
            "coupling_energy_proxy": self.coupling_energy_proxy,
            "external_forcing_density": self.external_forcing_density,
            "external_forcing_phase": self.external_forcing_phase,
            "coupling_strength_k": self.K,
            "sakaguchi_phase_lag_alpha": self.alpha,
            "active_domains": self.N,
            "backend_name": self.backend_name,
            "backend_library": self.backend_library,
            "device_id": self.active_device_id,
            "simulation_time": self.simulation_time,
            "tact_index": self.tact_index,
            "step": self.step_index,
        }

    def export_field_snapshot(
        self,
    ) -> dict[str, np.ndarray]:
        return {
            "phases": self._to_host(
                self.phases
            ).copy(),
            "amplitudes": self._to_host(
                self.amplitudes
            ).copy(),
            "natural_frequencies": self._to_host(
                self.natural_frequencies
            ).copy(),
            "phase_velocity": self._to_host(
                self.phase_velocity
            ).copy(),
            "amplitude_velocity": self._to_host(
                self.amplitude_velocity
            ).copy(),
            "phase_noise_increment": self._to_host(
                self.phase_noise_increment
            ).copy(),
            "amplitude_noise_increment": self._to_host(
                self.amplitude_noise_increment
            ).copy(),
        }

    def synchronize_backend(
        self,
    ) -> None:
        if self.using_gpu:
            self.xp.cuda.Stream.null.synchronize()


class EDKGPUMeanFieldLogger:
    def __init__(
        self,
        output_dir: str | os.PathLike[str] = (
            "edk_gpu_mean_field_snapshots"
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
        file_path: Path,
        payload: dict[str, Any],
    ) -> None:
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=file_path.parent,
                prefix=f".{file_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                json.dump(
                    _json_safe(
                        payload
                    ),
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )

                temporary_file.write(
                    "\n"
                )

                temporary_file.flush()

                os.fsync(
                    temporary_file.fileno()
                )

                temporary_path = Path(
                    temporary_file.name
                )

            os.replace(
                temporary_path,
                file_path,
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()

    @staticmethod
    def _atomic_npz_write(
        file_path: Path,
        arrays: dict[str, np.ndarray],
    ) -> None:
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w+b",
                dir=file_path.parent,
                prefix=f".{file_path.stem}.",
                suffix=".npz.tmp",
                delete=False,
            ) as temporary_file:
                np.savez_compressed(
                    temporary_file,
                    **arrays,
                )

                temporary_file.flush()

                os.fsync(
                    temporary_file.fileno()
                )

                temporary_path = Path(
                    temporary_file.name
                )

            os.replace(
                temporary_path,
                file_path,
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()

    def log_tact(
        self,
        tact_id: int,
        engine: EDKGPUMeanFieldPhaseEngine,
        include_field: bool = False,
    ) -> tuple[Path, Path | None]:
        tact = int(
            tact_id
        )

        if tact < 0:
            raise ValueError(
                "tact_id must be non-negative."
            )

        if tact != int(
            engine.tact_index
        ):
            raise ValueError(
                "tact_id must match engine.tact_index."
            )

        metrics_path = (
            self.output_dir
            / f"gpu_mean_field_tact_{tact:06d}.json"
        )

        compatibility_path = (
            self.output_dir
            / f"gpu_mean_field_step_{tact:06d}.json"
        )

        field_path = (
            self.output_dir
            / f"gpu_mean_field_field_{tact:06d}.npz"
            if include_field
            else None
        )

        payload = {
            "tact": tact,
            "step": tact,
            "tact_index": tact,
            "simulation_time": float(
                engine.simulation_time
            ),
            "module": "module_edk_gpu_mean_field_phase_engine",
            "engine_class": "EDKGPUMeanFieldPhaseEngine",
            "backend": {
                "name": engine.backend_name,
                "library": engine.backend_library,
                "using_gpu": engine.using_gpu,
                "device_id": engine.active_device_id,
            },
            "configuration": asdict(
                engine.config
            ),
            "metrics": engine.get_metrics(),
        }

        self._atomic_json_write(
            metrics_path,
            payload,
        )

        self._atomic_json_write(
            compatibility_path,
            payload,
        )

        if field_path is not None:
            self._atomic_npz_write(
                field_path,
                engine.export_field_snapshot(),
            )

        return (
            metrics_path,
            field_path,
        )

    def log_step(
        self,
        step_id: int,
        engine: EDKGPUMeanFieldPhaseEngine,
        include_field: bool = False,
    ) -> tuple[Path, Path | None]:
        """
        Compatibility alias for older scripts and tests.

        Internally this represents one tact of the
        GPU mean-field phase engine.
        """

        return self.log_tact(
            tact_id=step_id,
            engine=engine,
            include_field=include_field,
        )


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the EDK GPU mean-field phase engine."
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
        "--tacts",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=None,
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
        "--phase-lag",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--forcing",
        type=float,
        default=6.5,
    )

    parser.add_argument(
        "--forcing-phase",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
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
        "--output-dir",
        default="edk_gpu_mean_field_snapshots",
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

    return parser


def main() -> None:
    parser = _build_argument_parser()
    args = parser.parse_args()

    total_tacts = (
        args.tacts
        if args.tacts is not None
        else args.steps
        if args.steps is not None
        else 5
    )

    if total_tacts < 1:
        raise ValueError(
            "tacts must be at least 1."
        )

    if (
        not math.isfinite(
            args.dt
        )
        or args.dt <= 0.0
    ):
        raise ValueError(
            "dt must be a positive finite value."
        )

    if args.log_every < 0:
        raise ValueError(
            "log_every must be non-negative."
        )

    if args.field_every < 0:
        raise ValueError(
            "field_every must be non-negative."
        )

    config = MeanFieldPhaseConfig(
        num_domains=args.num_domains,
        coupling_strength_k=args.coupling,
        sakaguchi_phase_lag_alpha=args.phase_lag,
        external_forcing_phase=args.forcing_phase,
        seed=args.seed,
        dtype=args.dtype,
        backend=args.backend,
        device_id=args.device_id,
    )

    engine = EDKGPUMeanFieldPhaseEngine(
        config
    )

    logger = EDKGPUMeanFieldLogger(
        args.output_dir
    )

    print(
        "EDK GPU mean-field phase engine initialized."
    )

    print(
        f"backend={engine.backend_name} "
        f"backend_library={engine.backend_library} "
        f"device_id={engine.active_device_id} "
        f"domains={engine.N}"
    )

    for _ in range(
        total_tacts
    ):
        metrics = engine.process_micro_interval(
            external_forcing_density=args.forcing,
            external_forcing_phase=args.forcing_phase,
            dt=args.dt,
        )

        tact = int(
            metrics["tact_index"]
        )

        should_log = (
            args.log_every > 0
            and tact % args.log_every == 0
        )

        should_export_field = (
            args.field_every > 0
            and tact % args.field_every == 0
        )

        if should_log or should_export_field:
            logger.log_tact(
                tact_id=tact,
                engine=engine,
                include_field=should_export_field,
            )

        print(
            f"[tact {tact}] "
            f"R(t)="
            f"{metrics['R_t_phase_order']:.6f} "
            f"phase_amplitude_proxy="
            f"{metrics['phase_amplitude_order_proxy']:.6f} "
            f"mean_amplitude="
            f"{metrics['mean_amplitude']:.6f}"
        )


if __name__ == "__main__":
    main()
