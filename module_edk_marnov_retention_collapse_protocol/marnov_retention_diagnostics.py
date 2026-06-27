from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Iterable

os.environ.setdefault(
    "MPLBACKEND",
    "Agg",
)

import matplotlib.pyplot as plt
import numpy as np


_REQUIRED_METRICS = (
    "tact_index",
    "simulation_time",
    "protocol_state",
    "R_t_phase_order",
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
    "critical_exposure_threshold",
    "initial_coupling_K",
    "effective_coupling_K",
    "coupling_floor_K",
)

_STATE_ORDER = (
    "INITIALIZED",
    "FORMING_ATTRACTOR",
    "RETAINED_ATTRACTOR",
    "CRITICAL_APPROACH",
    "CRITICAL_EXPOSURE",
    "PHASE_NODE_UNLOCKED",
    "COLLAPSE_ACTIVE",
    "DEGRADED_PHASE_REGIME",
    "COLLAPSE_COMPLETED",
    "COLLAPSE_NOT_REACHED",
    "ATTRACTOR_NOT_FORMED",
    "ATTRACTOR_NOT_VERIFIED",
    "CRITICAL_BOUNDARY_NOT_REACHED",
    "UNLOCK_NOT_TRIGGERED",
    "NUMERICAL_INSTABILITY",
    "NON_FINITE_STATE",
)


def _numeric_suffix(
    path: Path,
) -> int:
    match = re.search(
        r"(\d+)(?=\.json$)",
        path.name,
    )

    return (
        int(
            match.group(1)
        )
        if match
        else -1
    )


def _as_float(
    value: Any,
    name: str,
) -> float:
    if value is None:
        return math.nan

    try:
        number = float(
            value
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Metric {name!r} is not numeric: {value!r}"
        ) from exc

    if not math.isfinite(
        number
    ):
        raise ValueError(
            f"Metric {name!r} is not finite: {number!r}"
        )

    return number


def _optional_float_value(
    value: Any,
    name: str,
) -> float | None:
    if value is None:
        return None

    return _as_float(
        value,
        name,
    )


def _optional_int_value(
    value: Any,
    name: str,
) -> int | None:
    if value is None:
        return None

    try:
        number = float(
            value
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Metric {name!r} is not integer-compatible: {value!r}"
        ) from exc

    if not math.isfinite(
        number
    ):
        raise ValueError(
            f"Metric {name!r} is not finite: {number!r}"
        )

    integer = int(
        number
    )

    if not math.isclose(
        number,
        float(
            integer
        ),
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ):
        raise ValueError(
            f"Metric {name!r} is not integer-compatible: {value!r}"
        )

    return integer


def _load_json(
    path: Path,
) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as stream:
        payload = json.load(
            stream
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            f"JSON root must be an object: {path}"
        )

    return payload


def _extract_metadata_tact(
    payload: dict[str, Any],
    path: Path,
) -> int | None:
    for key in (
        "tact",
        "tact_index",
        "step",
    ):
        if key in payload:
            return _optional_int_value(
                payload.get(
                    key
                ),
                (
                    f"{key} in "
                    f"{path.name}"
                ),
            )

    return None


def _validate_tact_metadata(
    *,
    filename_tact: int,
    metadata_tact: int | None,
    metrics_tact: int | None,
    path: Path,
) -> int:
    candidates = [
        value
        for value in (
            metadata_tact,
            metrics_tact,
            (
                filename_tact
                if filename_tact >= 0
                else None
            ),
        )
        if value is not None
    ]

    if not candidates:
        raise ValueError(
            f"Unable to resolve tact index for {path}"
        )

    resolved = candidates[0]

    if (
        filename_tact >= 0
        and filename_tact != resolved
    ):
        raise ValueError(
            (
                "Tact metadata mismatch in "
                f"{path.name}: filename={filename_tact}, "
                f"resolved={resolved}"
            )
        )

    if (
        metadata_tact is not None
        and metadata_tact != resolved
    ):
        raise ValueError(
            (
                "Top-level tact metadata mismatch in "
                f"{path.name}: metadata={metadata_tact}, "
                f"resolved={resolved}"
            )
        )

    if (
        metrics_tact is not None
        and metrics_tact != resolved
    ):
        raise ValueError(
            (
                "Metrics tact_index mismatch in "
                f"{path.name}: metrics={metrics_tact}, "
                f"resolved={resolved}"
            )
        )

    return resolved


def _validate_simulation_time_metadata(
    *,
    metadata_time: float | None,
    metrics_time: float | None,
    path: Path,
) -> float | None:
    if (
        metadata_time is None
        and metrics_time is None
    ):
        return None

    if metadata_time is None:
        return metrics_time

    if metrics_time is None:
        return metadata_time

    if not math.isclose(
        metadata_time,
        metrics_time,
        rel_tol=1.0e-9,
        abs_tol=1.0e-12,
    ):
        raise ValueError(
            (
                "simulation_time metadata mismatch in "
                f"{path.name}: top_level={metadata_time}, "
                f"metrics={metrics_time}"
            )
        )

    return metrics_time


def load_marnov_snapshots(
    snapshot_dir: str | Path,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any] | None,
]:
    directory = Path(
        snapshot_dir
    )

    if not directory.is_dir():
        raise FileNotFoundError(
            f"Snapshot directory does not exist: {directory}"
        )

    snapshot_paths = sorted(
        directory.glob(
            "marnov_step_*.json"
        ),
        key=_numeric_suffix,
    )

    if not snapshot_paths:
        raise FileNotFoundError(
            "No marnov_step_*.json files found "
            f"in {directory}"
        )

    records: list[dict[str, Any]] = []

    for path in snapshot_paths:
        payload = _load_json(
            path
        )

        metrics = payload.get(
            "metrics"
        )

        if not isinstance(
            metrics,
            dict,
        ):
            raise ValueError(
                f"Missing metrics object in {path}"
            )

        record = dict(
            metrics
        )

        filename_tact = _numeric_suffix(
            path
        )

        metadata_tact = (
            _extract_metadata_tact(
                payload,
                path,
            )
        )

        metrics_tact = (
            _optional_int_value(
                record.get(
                    "tact_index"
                ),
                (
                    f"metrics.tact_index in "
                    f"{path.name}"
                ),
            )
            if "tact_index" in record
            else None
        )

        resolved_tact = (
            _validate_tact_metadata(
                filename_tact=filename_tact,
                metadata_tact=metadata_tact,
                metrics_tact=metrics_tact,
                path=path,
            )
        )

        record[
            "tact_index"
        ] = resolved_tact

        metadata_time = (
            _optional_float_value(
                payload.get(
                    "simulation_time"
                ),
                (
                    f"top-level simulation_time "
                    f"in {path.name}"
                ),
            )
            if "simulation_time" in payload
            else None
        )

        metrics_time = (
            _optional_float_value(
                record.get(
                    "simulation_time"
                ),
                (
                    f"metrics.simulation_time "
                    f"in {path.name}"
                ),
            )
            if "simulation_time" in record
            else None
        )

        resolved_time = (
            _validate_simulation_time_metadata(
                metadata_time=metadata_time,
                metrics_time=metrics_time,
                path=path,
            )
        )

        if resolved_time is not None:
            record[
                "simulation_time"
            ] = resolved_time

        missing = [
            key
            for key in _REQUIRED_METRICS
            if key not in record
        ]

        if missing:
            raise ValueError(
                f"Missing required metrics in {path}: "
                f"{', '.join(missing)}"
            )

        record[
            "_source_path"
        ] = str(
            path
        )

        record[
            "_top_level_tact"
        ] = metadata_tact

        record[
            "_filename_tact"
        ] = filename_tact

        record[
            "_transition_events"
        ] = payload.get(
            "transition_events",
            [],
        )

        record[
            "_protocol_configuration"
        ] = payload.get(
            "protocol_configuration",
            {},
        )

        record[
            "_engine_configuration"
        ] = payload.get(
            "engine_configuration",
            {},
        )

        records.append(
            record
        )

    records.sort(
        key=lambda item: int(
            item[
                "tact_index"
            ]
        )
    )

    summary_path = (
        directory
        / "marnov_protocol_summary.json"
    )

    summary = (
        _load_json(
            summary_path
        )
        if summary_path.is_file()
        else None
    )

    return records, summary


def _series(
    records: Iterable[dict[str, Any]],
    key: str,
) -> np.ndarray:
    return np.asarray(
        [
            _as_float(
                record.get(
                    key
                ),
                key,
            )
            for record in records
        ],
        dtype=float,
    )


def _optional_scalar(
    records: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    key: str,
) -> float | None:
    if summary is not None:
        value = summary.get(
            key
        )

        if value is not None:
            return float(
                value
            )

        final_metrics = summary.get(
            "final_metrics"
        )

        if isinstance(
            final_metrics,
            dict,
        ):
            value = final_metrics.get(
                key
            )

            if value is not None:
                return float(
                    value
                )

    for record in reversed(
        records
    ):
        value = record.get(
            key
        )

        if value is not None:
            return float(
                value
            )

    return None


def _optional_tact(
    records: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    key: str,
) -> int | None:
    value = _optional_scalar(
        records,
        summary,
        key,
    )

    return (
        int(
            value
        )
        if value is not None
        else None
    )


def _transition_tacts(
    records: list[dict[str, Any]],
    summary: dict[str, Any] | None,
) -> dict[str, int]:
    events: list[dict[str, Any]] = []

    if summary is not None:
        summary_events = summary.get(
            "transition_events",
            [],
        )

        if isinstance(
            summary_events,
            list,
        ):
            events.extend(
                item
                for item in summary_events
                if isinstance(
                    item,
                    dict,
                )
            )

    if not events:
        seen: set[
            tuple[str, int]
        ] = set()

        for record in records:
            record_events = record.get(
                "_transition_events",
                [],
            )

            if not isinstance(
                record_events,
                list,
            ):
                continue

            for event in record_events:
                if not isinstance(
                    event,
                    dict,
                ):
                    continue

                name = str(
                    event.get(
                        "event",
                        "",
                    )
                )

                tact = event.get(
                    "tact_index"
                )

                if (
                    not name
                    or tact is None
                ):
                    continue

                event_key = (
                    name,
                    int(
                        tact
                    ),
                )

                if event_key not in seen:
                    seen.add(
                        event_key
                    )

                    events.append(
                        event
                    )

    transitions: dict[
        str,
        int,
    ] = {}

    for event in events:
        name = str(
            event.get(
                "event",
                "",
            )
        )

        tact = event.get(
            "tact_index"
        )

        if (
            name
            and tact is not None
        ):
            transitions[
                name
            ] = int(
                tact
            )

    return transitions


def _add_vertical_marker(
    axes: Iterable[Any],
    tact: int | None,
    label: str,
) -> None:
    if tact is None:
        return

    axis_list = list(
        axes
    )

    for axis in axis_list:
        axis.axvline(
            tact,
            linestyle="--",
            linewidth=1.0,
            alpha=0.6,
        )

    if axis_list:
        first_axis = axis_list[0]

        top = first_axis.get_ylim()[1]

        first_axis.text(
            tact,
            top,
            f" {label}",
            rotation=90,
            va="top",
            ha="left",
            fontsize=8,
        )


def plot_marnov_diagnostics(
    snapshot_dir: str | Path,
    output: str | Path | None = None,
    show: bool = True,
) -> Path | None:
    records, summary = (
        load_marnov_snapshots(
            snapshot_dir
        )
    )

    tact = _series(
        records,
        "tact_index",
    )

    time = _series(
        records,
        "simulation_time",
    )

    R_t = _series(
        records,
        "R_t_phase_order",
    )

    phase_amplitude = _series(
        records,
        "phase_amplitude_order_proxy",
    )

    C_proxy = _series(
        records,
        "C_proxy_t",
    )

    pressure = _series(
        records,
        "external_pressure_P_ext",
    )

    retention_margin = _series(
        records,
        "retention_margin",
    )

    pressure_excess = _series(
        records,
        "pressure_excess",
    )

    critical_exposure = _series(
        records,
        "critical_exposure",
    )

    exposure_threshold = _series(
        records,
        "critical_exposure_threshold",
    )

    tau_delay = _series(
        records,
        "instantaneous_delay_tau",
    )

    initial_K = _series(
        records,
        "initial_coupling_K",
    )

    effective_K = _series(
        records,
        "effective_coupling_K",
    )

    floor_K = _series(
        records,
        "coupling_floor_K",
    )

    phase_velocity_dispersion = _series(
        records,
        "phase_velocity_dispersion",
    )

    amplitude_dispersion = _series(
        records,
        "amplitude_dispersion",
    )

    mean_amplitude = _series(
        records,
        "mean_amplitude",
    )

    protocol_states = [
        str(
            record[
                "protocol_state"
            ]
        )
        for record in records
    ]

    state_names = list(
        _STATE_ORDER
    )

    for state in protocol_states:
        if state not in state_names:
            state_names.append(
                state
            )

    state_to_index = {
        name: index
        for index, name in enumerate(
            state_names
        )
    }

    state_values = np.asarray(
        [
            state_to_index[
                state
            ]
            for state in protocol_states
        ],
        dtype=float,
    )

    protocol_config = records[-1].get(
        "_protocol_configuration",
        {},
    )

    engine_config = records[-1].get(
        "_engine_configuration",
        {},
    )

    tolerance = float(
        protocol_config.get(
            "retained_boundary_tolerance",
            0.0,
        )
    )

    amplitude_floor = float(
        engine_config.get(
            "amplitude_minimum",
            0.0,
        )
    )

    transitions = _transition_tacts(
        records,
        summary,
    )

    formation_tact = _optional_tact(
        records,
        summary,
        "formation_tact",
    )

    unlock_tact = _optional_tact(
        records,
        summary,
        "unlock_tact",
    )

    collapse_tact = _optional_tact(
        records,
        summary,
        "collapse_tact",
    )

    phase_half_life = _optional_scalar(
        records,
        summary,
        "phase_order_half_life",
    )

    amplitude_half_life = _optional_scalar(
        records,
        summary,
        "amplitude_regime_half_life",
    )

    collapse_duration = _optional_scalar(
        records,
        summary,
        "attractor_collapse_duration",
    )

    R_unlock: float | None = None
    amplitude_unlock: float | None = None

    if unlock_tact is not None:
        unlock_index = int(
            np.argmin(
                np.abs(
                    tact
                    - unlock_tact
                )
            )
        )

        R_unlock = float(
            R_t[
                unlock_index
            ]
        )

        amplitude_unlock = float(
            mean_amplitude[
                unlock_index
            ]
        )

    figure, axes = plt.subplots(
        4,
        2,
        figsize=(
            16,
            18,
        ),
        constrained_layout=True,
    )

    axis_1 = axes[0, 0]

    axis_1.plot(
        tact,
        R_t,
        label="R(t) phase order",
    )

    axis_1.plot(
        tact,
        phase_amplitude,
        label="Phase-amplitude proxy",
    )

    axis_1.plot(
        tact,
        C_proxy,
        label="C_proxy(t)",
    )

    axis_1.set_title(
        "Phase order and protocol coherence proxy"
    )

    axis_1.set_xlabel(
        "Tact"
    )

    axis_1.set_ylabel(
        "Bounded diagnostic value"
    )

    axis_1.set_ylim(
        -0.05,
        1.05,
    )

    axis_1.grid(
        True,
        alpha=0.3,
    )

    axis_1.legend()

    axis_2 = axes[0, 1]

    axis_2.plot(
        tact,
        pressure,
        label="P_ext(t)",
    )

    axis_2.plot(
        tact,
        retention_margin,
        label="Retention margin",
    )

    axis_2.plot(
        tact,
        pressure_excess,
        label="Pressure excess",
    )

    axis_2.axhline(
        0.0,
        linewidth=1.0,
    )

    axis_2.axhline(
        tolerance,
        linestyle=":",
        linewidth=1.0,
    )

    axis_2.axhline(
        -tolerance,
        linestyle=":",
        linewidth=1.0,
    )

    axis_2.set_title(
        "External pressure and retention boundary"
    )

    axis_2.set_xlabel(
        "Tact"
    )

    axis_2.set_ylabel(
        "Normalized value"
    )

    axis_2.grid(
        True,
        alpha=0.3,
    )

    axis_2.legend()

    axis_3 = axes[1, 0]

    axis_3.plot(
        tact,
        critical_exposure,
        label="Critical exposure",
    )

    axis_3.plot(
        tact,
        exposure_threshold,
        label="Exposure threshold",
    )

    axis_3.set_title(
        "Critical exposure and retardation scale"
    )

    axis_3.set_xlabel(
        "Tact"
    )

    axis_3.set_ylabel(
        "Exposure"
    )

    axis_3.grid(
        True,
        alpha=0.3,
    )

    axis_3.legend(
        loc="upper left"
    )

    axis_3_tau = axis_3.twinx()

    axis_3_tau.plot(
        tact,
        tau_delay,
        linestyle="--",
        label="tau_delay",
    )

    axis_3_tau.set_ylabel(
        "Delay scale"
    )

    axis_3_tau.legend(
        loc="upper right"
    )

    axis_4 = axes[1, 1]

    axis_4.plot(
        tact,
        initial_K,
        label="Initial K",
    )

    axis_4.plot(
        tact,
        effective_K,
        label="Effective K",
    )

    axis_4.plot(
        tact,
        floor_K,
        label="K floor",
    )

    axis_4.set_title(
        "Coupling-quench trajectory"
    )

    axis_4.set_xlabel(
        "Tact"
    )

    axis_4.set_ylabel(
        "Coupling strength"
    )

    axis_4.grid(
        True,
        alpha=0.3,
    )

    axis_4.legend()

    axis_5 = axes[2, 0]

    axis_5.plot(
        tact,
        phase_velocity_dispersion,
        label="Phase-velocity dispersion",
    )

    axis_5.plot(
        tact,
        amplitude_dispersion,
        label="Amplitude dispersion",
    )

    axis_5.set_title(
        "Phase and amplitude disorder"
    )

    axis_5.set_xlabel(
        "Tact"
    )

    axis_5.set_ylabel(
        "Dispersion"
    )

    axis_5.grid(
        True,
        alpha=0.3,
    )

    axis_5.legend()

    axis_6 = axes[2, 1]

    axis_6.plot(
        tact,
        mean_amplitude,
        label="Mean amplitude",
    )

    axis_6.axhline(
        amplitude_floor,
        linestyle=":",
        linewidth=1.0,
        label="Amplitude floor",
    )

    if amplitude_unlock is not None:
        amplitude_half_target = (
            amplitude_floor
            + 0.5
            * (
                amplitude_unlock
                - amplitude_floor
            )
        )

        axis_6.axhline(
            amplitude_half_target,
            linestyle="--",
            linewidth=1.0,
            label=(
                "Amplitude half-life target"
            ),
        )

    axis_6.set_title(
        "Amplitude-regime decay"
    )

    axis_6.set_xlabel(
        "Tact"
    )

    axis_6.set_ylabel(
        "Mean amplitude"
    )

    axis_6.grid(
        True,
        alpha=0.3,
    )

    axis_6.legend()

    axis_7 = axes[3, 0]

    axis_7.step(
        tact,
        state_values,
        where="post",
    )

    axis_7.set_title(
        "Protocol-state trajectory"
    )

    axis_7.set_xlabel(
        "Tact"
    )

    axis_7.set_ylabel(
        "Protocol state"
    )

    axis_7.set_yticks(
        range(
            len(
                state_names
            )
        )
    )

    axis_7.set_yticklabels(
        state_names,
        fontsize=8,
    )

    axis_7.grid(
        True,
        axis="x",
        alpha=0.3,
    )

    axis_8 = axes[3, 1]

    axis_8.plot(
        tact,
        R_t,
        label="R(t)",
    )

    if R_unlock is not None:
        axis_8.axhline(
            0.5
            * R_unlock,
            linestyle="--",
            linewidth=1.0,
            label="R(t) half-life target",
        )

    axis_8.set_title(
        "Collapse timing and measured half-lives"
    )

    axis_8.set_xlabel(
        "Tact"
    )

    axis_8.set_ylabel(
        "R(t)"
    )

    axis_8.set_ylim(
        -0.05,
        1.05,
    )

    axis_8.grid(
        True,
        alpha=0.3,
    )

    axis_8.legend()

    marker_axes = (
        axis_1,
        axis_2,
        axis_3,
        axis_4,
        axis_5,
        axis_6,
        axis_7,
        axis_8,
    )

    _add_vertical_marker(
        marker_axes,
        formation_tact,
        "formation",
    )

    _add_vertical_marker(
        marker_axes,
        unlock_tact,
        "unlock",
    )

    _add_vertical_marker(
        marker_axes,
        collapse_tact,
        "collapse",
    )

    transition_text = "\n".join(
        f"{name}: tact {event_tact}"
        for name, event_tact in sorted(
            transitions.items(),
            key=lambda item: item[1],
        )
    )

    summary_lines = [
        f"Snapshots: {len(records)}",
        f"Final tact: {int(tact[-1])}",
        f"Final time: {time[-1]:.6f}",
        f"Final state: {protocol_states[-1]}",
        (
            "Phase-order half-life: "
            + (
                f"{phase_half_life:.6f}"
                if phase_half_life
                is not None
                else "not reached"
            )
        ),
        (
            "Amplitude-regime half-life: "
            + (
                f"{amplitude_half_life:.6f}"
                if amplitude_half_life
                is not None
                else "not reached"
            )
        ),
        (
            "Collapse duration: "
            + (
                f"{collapse_duration:.6f}"
                if collapse_duration
                is not None
                else "not reached"
            )
        ),
    ]

    if transition_text:
        summary_lines.extend(
            (
                "",
                "Transitions:",
                transition_text,
            )
        )

    axis_8.text(
        1.02,
        0.98,
        "\n".join(
            summary_lines
        ),
        transform=axis_8.transAxes,
        va="top",
        ha="left",
        fontsize=9,
    )

    figure.suptitle(
        "EDK Marnov Retention-Collapse "
        "Protocol Diagnostics",
        fontsize=16,
    )

    output_path: Path | None = None

    if output is not None:
        output_path = Path(
            output
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        figure.savefig(
            output_path,
            dpi=180,
            bbox_inches="tight",
        )

    if show:
        plt.show()
    else:
        plt.close(
            figure
        )

    return output_path


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate diagnostics for the EDK "
            "Marnov Retention-Collapse Protocol."
        )
    )

    parser.add_argument(
        "--snapshot-dir",
        default="edk_marnov_snapshots",
    )

    parser.add_argument(
        "--output",
        default=(
            "marnov_retention_diagnostics.png"
        ),
    )

    parser.add_argument(
        "--no-show",
        action="store_true",
    )

    return parser


def main() -> None:
    args = (
        _build_argument_parser()
        .parse_args()
    )

    output_path = (
        plot_marnov_diagnostics(
            snapshot_dir=(
                args.snapshot_dir
            ),
            output=args.output,
            show=(
                not args.no_show
            ),
        )
    )

    if output_path is not None:
        print(
            f"Diagnostics saved to: "
            f"{output_path}"
        )


if __name__ == "__main__":
    main()
