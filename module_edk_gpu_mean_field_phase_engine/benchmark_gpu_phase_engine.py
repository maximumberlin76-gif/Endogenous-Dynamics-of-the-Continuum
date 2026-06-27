from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

import numpy as np

try:
    from .edk_gpu_mean_field_phase_engine import (
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
            sys.path.insert(
                0,
                str(repo_root),
            )

        from module_edk_gpu_mean_field_phase_engine.edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
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


def _atomic_write_json(
    file_path: Path,
    payload: dict[str, Any],
) -> None:
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def _synchronize(
    engine: EDKGPUMeanFieldPhaseEngine,
) -> None:
    engine.synchronize_backend()


def _persistent_state_bytes(
    engine: EDKGPUMeanFieldPhaseEngine,
) -> int:
    arrays = (
        engine.phases,
        engine.amplitudes,
        engine.natural_frequencies,
        engine.phase_velocity,
        engine.amplitude_velocity,
        engine.phase_noise_increment,
        engine.amplitude_noise_increment,
    )

    return int(
        sum(
            int(
                array.nbytes
            )
            for array in arrays
        )
    )


def _memory_report(
    engine: EDKGPUMeanFieldPhaseEngine,
) -> dict[str, Any]:
    float_itemsize = int(
        np.dtype(
            engine.config.dtype
        ).itemsize
    )

    complex_itemsize = int(
        np.dtype(
            "complex64"
            if engine.config.dtype == "float32"
            else "complex128"
        ).itemsize
    )

    persistent_bytes = _persistent_state_bytes(
        engine
    )

    persistent_bytes_per_domain = (
        persistent_bytes
        / engine.N
    )

    conservative_working_bytes_per_domain = (
        persistent_bytes_per_domain
        + 6
        * float_itemsize
        + 2
        * complex_itemsize
    )

    unallocated_pairwise_matrix_bytes = int(
        engine.N
        * engine.N
        * float_itemsize
    )

    report: dict[str, Any] = {
        "backend_name": engine.backend_name,
        "backend_library": engine.backend_library,
        "using_gpu": engine.using_gpu,
        "device_id": engine.active_device_id,
        "dtype": engine.config.dtype,
        "num_domains": engine.N,
        "float_itemsize": float_itemsize,
        "complex_itemsize": complex_itemsize,
        "persistent_state_bytes": persistent_bytes,
        "persistent_state_mebibytes": (
            persistent_bytes
            / 1024**2
        ),
        "persistent_bytes_per_domain": persistent_bytes_per_domain,
        "conservative_working_bytes_per_domain": (
            conservative_working_bytes_per_domain
        ),
        "unallocated_pairwise_matrix_bytes": (
            unallocated_pairwise_matrix_bytes
        ),
        "unallocated_pairwise_matrix_gibibytes": (
            unallocated_pairwise_matrix_bytes
            / 1024**3
        ),
    }

    if engine.using_gpu:
        xp = engine.xp

        _synchronize(
            engine
        )

        free_bytes, total_bytes = (
            xp.cuda.runtime.memGetInfo()
        )

        memory_pool = (
            xp.get_default_memory_pool()
        )

        device_properties = (
            xp.cuda.runtime.getDeviceProperties(
                engine.active_device_id
            )
        )

        device_name = device_properties.get(
            "name",
            device_properties.get(
                b"name",
                "unknown",
            ),
        )

        if isinstance(
            device_name,
            bytes,
        ):
            device_name = device_name.decode(
                "utf-8",
                errors="replace",
            )

        safe_available_bytes = int(
            free_bytes
            * 0.8
        )

        estimated_maximum_domains = int(
            safe_available_bytes
            / max(
                conservative_working_bytes_per_domain,
                1.0,
            )
        )

        report.update(
            {
                "device_name": str(
                    device_name
                ),
                "device_total_bytes": int(
                    total_bytes
                ),
                "device_free_bytes": int(
                    free_bytes
                ),
                "device_used_bytes": int(
                    total_bytes
                    - free_bytes
                ),
                "cupy_memory_pool_used_bytes": int(
                    memory_pool.used_bytes()
                ),
                "cupy_memory_pool_reserved_bytes": int(
                    memory_pool.total_bytes()
                ),
                "estimated_maximum_domains_at_80_percent_free_memory": (
                    estimated_maximum_domains
                ),
            }
        )

    return report


def _validate_runtime_inputs(
    warmup_tacts: int,
    measured_tacts: int,
    forcing: float,
    forcing_phase: float,
    dt: float,
) -> None:
    if warmup_tacts < 0:
        raise ValueError(
            "warmup_tacts must be non-negative."
        )

    if measured_tacts < 1:
        raise ValueError(
            "measured_tacts must be at least 1."
        )

    if not math.isfinite(
        forcing
    ):
        raise ValueError(
            "forcing must be finite."
        )

    if not math.isfinite(
        forcing_phase
    ):
        raise ValueError(
            "forcing_phase must be finite."
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


def _run_warmup(
    engine: EDKGPUMeanFieldPhaseEngine,
    warmup_tacts: int,
    forcing: float,
    forcing_phase: float,
    dt: float,
) -> None:
    for _ in range(
        warmup_tacts
    ):
        engine.process_micro_interval(
            external_forcing_density=forcing,
            external_forcing_phase=forcing_phase,
            dt=dt,
        )

    _synchronize(
        engine
    )


def _benchmark_tacts(
    engine: EDKGPUMeanFieldPhaseEngine,
    measured_tacts: int,
    forcing: float,
    forcing_phase: float,
    dt: float,
) -> dict[str, float]:
    _synchronize(
        engine
    )

    host_start = time.perf_counter()

    if engine.using_gpu:
        xp = engine.xp

        start_event = xp.cuda.Event()
        end_event = xp.cuda.Event()

        start_event.record()

        for _ in range(
            measured_tacts
        ):
            engine.process_micro_interval(
                external_forcing_density=forcing,
                external_forcing_phase=forcing_phase,
                dt=dt,
            )

        end_event.record()
        end_event.synchronize()

        device_seconds = float(
            xp.cuda.get_elapsed_time(
                start_event,
                end_event,
            )
            / 1000.0
        )

    else:
        for _ in range(
            measured_tacts
        ):
            engine.process_micro_interval(
                external_forcing_density=forcing,
                external_forcing_phase=forcing_phase,
                dt=dt,
            )

        device_seconds = 0.0

    _synchronize(
        engine
    )

    host_seconds = (
        time.perf_counter()
        - host_start
    )

    average_host_seconds = (
        host_seconds
        / measured_tacts
    )

    average_device_seconds = (
        device_seconds
        / measured_tacts
        if engine.using_gpu
        else 0.0
    )

    domain_updates_per_second = (
        engine.N
        * measured_tacts
        / host_seconds
    )

    return {
        "measured_tacts": float(
            measured_tacts
        ),
        "host_wall_seconds": host_seconds,
        "average_host_seconds_per_tact": average_host_seconds,
        "average_host_milliseconds_per_tact": (
            average_host_seconds
            * 1000.0
        ),
        "device_event_seconds": device_seconds,
        "average_device_seconds_per_tact": average_device_seconds,
        "average_device_milliseconds_per_tact": (
            average_device_seconds
            * 1000.0
        ),
        "domain_updates_per_second": domain_updates_per_second,
    }


def _benchmark_field_transfer(
    engine: EDKGPUMeanFieldPhaseEngine,
) -> tuple[
    dict[str, float],
    dict[str, np.ndarray],
]:
    _synchronize(
        engine
    )

    start_time = time.perf_counter()

    field_snapshot = (
        engine.export_field_snapshot()
    )

    _synchronize(
        engine
    )

    transfer_seconds = (
        time.perf_counter()
        - start_time
    )

    total_field_bytes = int(
        sum(
            int(
                array.nbytes
            )
            for array in field_snapshot.values()
        )
    )

    return (
        {
            "field_transfer_seconds": transfer_seconds,
            "field_transfer_milliseconds": (
                transfer_seconds
                * 1000.0
            ),
            "field_snapshot_bytes": float(
                total_field_bytes
            ),
            "field_snapshot_mebibytes": (
                total_field_bytes
                / 1024**2
            ),
        },
        field_snapshot,
    )


def _benchmark_serialization(
    engine: EDKGPUMeanFieldPhaseEngine,
    field_snapshot: dict[str, np.ndarray],
) -> dict[str, float]:
    with tempfile.TemporaryDirectory(
        prefix="edk_gpu_benchmark_"
    ) as temporary_directory:
        directory = Path(
            temporary_directory
        )

        json_path = (
            directory
            / "benchmark_metrics.json"
        )

        npz_path = (
            directory
            / "benchmark_field.npz"
        )

        json_start = time.perf_counter()

        _atomic_write_json(
            json_path,
            {
                "metrics": engine.get_metrics(),
            },
        )

        json_seconds = (
            time.perf_counter()
            - json_start
        )

        npz_start = time.perf_counter()

        with npz_path.open(
            "wb",
        ) as stream:
            np.savez_compressed(
                stream,
                **field_snapshot,
            )

            stream.flush()

            os.fsync(
                stream.fileno()
            )

        npz_seconds = (
            time.perf_counter()
            - npz_start
        )

        json_bytes = int(
            json_path.stat().st_size
        )

        npz_bytes = int(
            npz_path.stat().st_size
        )

    return {
        "json_serialization_seconds": json_seconds,
        "json_serialization_milliseconds": (
            json_seconds
            * 1000.0
        ),
        "json_file_bytes": float(
            json_bytes
        ),
        "npz_serialization_seconds": npz_seconds,
        "npz_serialization_milliseconds": (
            npz_seconds
            * 1000.0
        ),
        "npz_file_bytes": float(
            npz_bytes
        ),
        "npz_file_mebibytes": (
            npz_bytes
            / 1024**2
        ),
    }


def run_benchmark(
    config: MeanFieldPhaseConfig,
    warmup_tacts: int,
    measured_tacts: int,
    forcing: float,
    forcing_phase: float,
    dt: float,
    measure_field_io: bool,
) -> dict[str, Any]:
    _validate_runtime_inputs(
        warmup_tacts=warmup_tacts,
        measured_tacts=measured_tacts,
        forcing=forcing,
        forcing_phase=forcing_phase,
        dt=dt,
    )

    config.validate()

    engine = EDKGPUMeanFieldPhaseEngine(
        config
    )

    _run_warmup(
        engine=engine,
        warmup_tacts=warmup_tacts,
        forcing=forcing,
        forcing_phase=forcing_phase,
        dt=dt,
    )

    timing_report = _benchmark_tacts(
        engine=engine,
        measured_tacts=measured_tacts,
        forcing=forcing,
        forcing_phase=forcing_phase,
        dt=dt,
    )

    report: dict[str, Any] = {
        "module": "module_edk_gpu_mean_field_phase_engine",
        "benchmark": "benchmark_gpu_phase_engine",
        "backend": {
            "name": engine.backend_name,
            "library": engine.backend_library,
            "using_gpu": engine.using_gpu,
            "device_id": engine.active_device_id,
        },
        "configuration": {
            **asdict(
                config
            ),
            "warmup_tacts": warmup_tacts,
            "warmup_steps": warmup_tacts,
            "measured_tacts": measured_tacts,
            "measured_steps": measured_tacts,
            "dt": dt,
            "external_forcing_density": forcing,
            "external_forcing_phase": forcing_phase,
        },
        "timing": timing_report,
        "memory": _memory_report(
            engine
        ),
        "final_metrics": engine.get_metrics(),
    }

    if measure_field_io:
        (
            transfer_report,
            field_snapshot,
        ) = _benchmark_field_transfer(
            engine
        )

        serialization_report = (
            _benchmark_serialization(
                engine,
                field_snapshot,
            )
        )

        report["field_transfer"] = transfer_report
        report["serialization"] = serialization_report

    return report


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark the EDK GPU mean-field phase engine."
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
        "--warmup-tacts",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--measured-tacts",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--measured-steps",
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
        "--skip-field-io",
        action="store_true",
    )

    parser.add_argument(
        "--output",
        default="benchmark_gpu_phase_engine.json",
    )

    return parser


def main() -> None:
    parser = _build_argument_parser()
    args = parser.parse_args()

    warmup_tacts = (
        args.warmup_tacts
        if args.warmup_tacts is not None
        else args.warmup_steps
        if args.warmup_steps is not None
        else 3
    )

    measured_tacts = (
        args.measured_tacts
        if args.measured_tacts is not None
        else args.measured_steps
        if args.measured_steps is not None
        else 20
    )

    if args.num_domains < 2:
        raise ValueError(
            "num_domains must be at least 2."
        )

    _validate_runtime_inputs(
        warmup_tacts=warmup_tacts,
        measured_tacts=measured_tacts,
        forcing=args.forcing,
        forcing_phase=args.forcing_phase,
        dt=args.dt,
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

    report = run_benchmark(
        config=config,
        warmup_tacts=warmup_tacts,
        measured_tacts=measured_tacts,
        forcing=args.forcing,
        forcing_phase=args.forcing_phase,
        dt=args.dt,
        measure_field_io=(
            not args.skip_field_io
        ),
    )

    output_path = Path(
        args.output
    )

    _atomic_write_json(
        output_path,
        report,
    )

    timing = report["timing"]
    memory = report["memory"]
    backend = report["backend"]

    print(
        "EDK GPU mean-field phase benchmark completed."
    )

    print(
        f"backend={backend['name']} "
        f"backend_library={backend['library']} "
        f"device_id={backend['device_id']} "
        f"domains={config.num_domains}"
    )

    print(
        "measured_tacts="
        f"{int(timing['measured_tacts'])}"
    )

    print(
        "average_host_time_per_tact_ms="
        f"{timing['average_host_milliseconds_per_tact']:.6f}"
    )

    if backend["using_gpu"]:
        print(
            "average_device_time_per_tact_ms="
            f"{timing['average_device_milliseconds_per_tact']:.6f}"
        )

    print(
        "domain_updates_per_second="
        f"{timing['domain_updates_per_second']:.3f}"
    )

    print(
        "persistent_state_mib="
        f"{memory['persistent_state_mebibytes']:.3f}"
    )

    print(
        "avoided_pairwise_matrix_gib="
        f"{memory['unallocated_pairwise_matrix_gibibytes']:.3f}"
    )

    print(
        f"report={output_path}"
    )


if __name__ == "__main__":
    main()
