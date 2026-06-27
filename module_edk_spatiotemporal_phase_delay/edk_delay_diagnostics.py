from __future__ import annotations

import argparse
import glob
import json
import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLBACKEND",
    "Agg",
)

import matplotlib.pyplot as plt
import numpy as np


REQUIRED_METRIC_KEYS = (
    "R_t_phase_order",
    "delayed_local_phase_order",
    "mean_phase_velocity",
    "phase_velocity_dispersion",
    "mean_delay",
    "maximum_delay",
    "delay_dispersion",
    "delayed_coupling_energy_proxy",
    "history_buffer_depth",
)

TACT_METADATA_KEYS = (
    "tact",
    "step",
    "tact_index",
)


def _extract_tact_from_path(
    path: str | Path,
) -> int:
    stem = Path(path).stem
    suffix = stem.rsplit(
        "_",
        maxsplit=1,
    )[-1]

    try:
        return int(
            suffix
        )
    except ValueError as exc:
        raise ValueError(
            "Unable to extract numeric tact identifier "
            f"from '{path}'."
        ) from exc


def _as_float(
    value: Any,
    name: str,
) -> float:
    try:
        number = float(
            value
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be numeric, received {value!r}."
        ) from exc

    if not math.isfinite(
        number
    ):
        raise ValueError(
            f"{name} must be finite, received {number!r}."
        )

    return number


def _as_int(
    value: Any,
    name: str,
) -> int:
    number = _as_float(
        value,
        name,
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
            f"{name} must be integer-compatible, received {value!r}."
        )

    return integer


def _load_json_object(
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


def _collect_metric_paths(
    snapshot_dir: str | Path,
) -> list[Path]:
    directory = Path(
        snapshot_dir
    )

    if not directory.is_dir():
        raise FileNotFoundError(
            f"Snapshot directory does not exist: '{directory}'."
        )

    by_tact: dict[int, Path] = {}

    for path in sorted(
        directory.glob(
            "delay_step_*.json"
        ),
        key=_extract_tact_from_path,
    ):
        tact = _extract_tact_from_path(
            path
        )

        by_tact.setdefault(
            tact,
            path,
        )

    for path in sorted(
        directory.glob(
            "delay_tact_*.json"
        ),
        key=_extract_tact_from_path,
    ):
        tact = _extract_tact_from_path(
            path
        )

        by_tact[
            tact
        ] = path

    if not by_tact:
        raise FileNotFoundError(
            "No delay_tact_*.json or delay_step_*.json "
            f"metric snapshots found in '{directory}'."
        )

    return [
        by_tact[
            tact
        ]
        for tact in sorted(
            by_tact
        )
    ]


def _resolve_tact_metadata(
    *,
    filename_tact: int,
    record: dict[str, Any],
    metrics: dict[str, Any],
    filename: str,
) -> int:
    candidates: list[
        tuple[
            str,
            int,
        ]
    ] = [
        (
            "filename",
            filename_tact,
        )
    ]

    for key in TACT_METADATA_KEYS:
        if key in record:
            candidates.append(
                (
                    f"top_level.{key}",
                    _as_int(
                        record[
                            key
                        ],
                        f"top_level.{key} in {filename}",
                    ),
                )
            )

    for key in (
        "tact_index",
        "step",
    ):
        if key in metrics:
            candidates.append(
                (
                    f"metrics.{key}",
                    _as_int(
                        metrics[
                            key
                        ],
                        f"metrics.{key} in {filename}",
                    ),
                )
            )

    resolved = candidates[0][1]

    for name, value in candidates[1:]:
        if value != resolved:
            raise ValueError(
                "Tact metadata mismatch in "
                f"'{filename}': filename={filename_tact}, "
                f"{name}={value}, resolved={resolved}."
            )

    return resolved


def _resolve_simulation_time(
    *,
    record: dict[str, Any],
    metrics: dict[str, Any],
    filename: str,
) -> float:
    top_level_exists = (
        "simulation_time"
        in record
    )

    metric_exists = (
        "simulation_time"
        in metrics
    )

    if not top_level_exists and not metric_exists:
        raise KeyError(
            f"Missing simulation_time in '{filename}'."
        )

    top_level_time = (
        _as_float(
            record[
                "simulation_time"
            ],
            f"top_level.simulation_time in {filename}",
        )
        if top_level_exists
        else None
    )

    metric_time = (
        _as_float(
            metrics[
                "simulation_time"
            ],
            f"metrics.simulation_time in {filename}",
        )
        if metric_exists
        else None
    )

    if (
        top_level_time is not None
        and metric_time is not None
        and not math.isclose(
            top_level_time,
            metric_time,
            rel_tol=1.0e-9,
            abs_tol=1.0e-12,
        )
    ):
        raise ValueError(
            "simulation_time metadata mismatch in "
            f"'{filename}': top_level={top_level_time}, "
            f"metrics={metric_time}."
        )

    return (
        metric_time
        if metric_time is not None
        else float(
            top_level_time
        )
    )


def load_delay_metrics(
    snapshot_dir: str | Path = "edk_delay_snapshots",
) -> dict[str, np.ndarray]:
    files = _collect_metric_paths(
        snapshot_dir
    )

    tacts: list[int] = []
    simulation_times: list[float] = []

    metric_history: dict[str, list[float]] = {
        key: []
        for key in REQUIRED_METRIC_KEYS
    }

    for path in files:
        record = _load_json_object(
            path
        )

        metrics = record.get(
            "metrics"
        )

        if not isinstance(
            metrics,
            dict,
        ):
            raise KeyError(
                f"Missing metrics object in '{path}'."
            )

        filename_tact = _extract_tact_from_path(
            path
        )

        tact = _resolve_tact_metadata(
            filename_tact=filename_tact,
            record=record,
            metrics=metrics,
            filename=str(
                path
            ),
        )

        simulation_time = _resolve_simulation_time(
            record=record,
            metrics=metrics,
            filename=str(
                path
            ),
        )

        missing_keys = [
            key
            for key in REQUIRED_METRIC_KEYS
            if key not in metrics
        ]

        if missing_keys:
            raise KeyError(
                f"Missing metric keys in '{path}': "
                f"{missing_keys}"
            )

        tacts.append(
            tact
        )

        simulation_times.append(
            simulation_time
        )

        for key in REQUIRED_METRIC_KEYS:
            value = _as_float(
                metrics[
                    key
                ],
                f"metrics.{key} in {path}",
            )

            metric_history[
                key
            ].append(
                value
            )

    result: dict[str, np.ndarray] = {
        "tacts": np.asarray(
            tacts,
            dtype=int,
        ),
        "steps": np.asarray(
            tacts,
            dtype=int,
        ),
        "simulation_time": np.asarray(
            simulation_times,
            dtype=float,
        ),
    }

    for key, values in metric_history.items():
        result[
            key
        ] = np.asarray(
            values,
            dtype=float,
        )

    return result


def load_latest_delay_field(
    snapshot_dir: str | Path = "edk_delay_snapshots",
) -> dict[str, np.ndarray] | None:
    search_path = os.path.join(
        str(
            snapshot_dir
        ),
        "delay_field_*.npz",
    )

    files = sorted(
        glob.glob(
            search_path
        ),
        key=_extract_tact_from_path,
    )

    if not files:
        return None

    with np.load(
        files[-1],
        allow_pickle=False,
    ) as archive:
        field = {
            key: np.asarray(
                archive[
                    key
                ]
            )
            for key in archive.files
        }

    required_keys = (
        "coords_3d",
        "phases",
        "natural_frequencies",
        "neighbor_indices",
        "edge_distances",
        "tau_ij",
        "neighbor_weights",
        "delayed_neighbor_phases",
        "phase_velocity",
    )

    missing_keys = [
        key
        for key in required_keys
        if key not in field
    ]

    if missing_keys:
        raise KeyError(
            "Latest delay field snapshot is incomplete. "
            f"Missing keys: {missing_keys}"
        )

    return field


def _validate_field_shapes(
    field: dict[str, np.ndarray],
) -> None:
    coords = field[
        "coords_3d"
    ]

    phases = field[
        "phases"
    ]

    natural_frequencies = field[
        "natural_frequencies"
    ]

    neighbor_indices = field[
        "neighbor_indices"
    ]

    edge_distances = field[
        "edge_distances"
    ]

    tau_ij = field[
        "tau_ij"
    ]

    neighbor_weights = field[
        "neighbor_weights"
    ]

    delayed_neighbor_phases = field[
        "delayed_neighbor_phases"
    ]

    phase_velocity = field[
        "phase_velocity"
    ]

    if (
        coords.ndim != 2
        or coords.shape[
            1
        ]
        != 3
    ):
        raise ValueError(
            "coords_3d must have shape (N, 3), "
            f"received {coords.shape}."
        )

    domain_count = coords.shape[
        0
    ]

    vector_shape = (
        domain_count,
    )

    for key, array in (
        (
            "phases",
            phases,
        ),
        (
            "natural_frequencies",
            natural_frequencies,
        ),
        (
            "phase_velocity",
            phase_velocity,
        ),
    ):
        if array.shape != vector_shape:
            raise ValueError(
                f"{key} must have shape {vector_shape}, "
                f"received {array.shape}."
            )

    if neighbor_indices.ndim != 2:
        raise ValueError(
            "neighbor_indices must have shape (N, k)."
        )

    if neighbor_indices.shape[
        0
    ] != domain_count:
        raise ValueError(
            "neighbor_indices domain count does not match coords_3d."
        )

    edge_shape = neighbor_indices.shape

    for key, array in (
        (
            "edge_distances",
            edge_distances,
        ),
        (
            "tau_ij",
            tau_ij,
        ),
        (
            "neighbor_weights",
            neighbor_weights,
        ),
        (
            "delayed_neighbor_phases",
            delayed_neighbor_phases,
        ),
    ):
        if array.shape != edge_shape:
            raise ValueError(
                f"{key} must have shape {edge_shape}, "
                f"received {array.shape}."
            )

    if "edge_vectors" in field:
        edge_vectors = field[
            "edge_vectors"
        ]

        if edge_vectors.shape != (
            edge_shape[
                0
            ],
            edge_shape[
                1
            ],
            3,
        ):
            raise ValueError(
                "edge_vectors must have shape (N, k, 3), "
                f"received {edge_vectors.shape}."
            )

    if np.any(
        neighbor_indices
        < 0
    ) or np.any(
        neighbor_indices
        >= domain_count
    ):
        raise ValueError(
            "neighbor_indices contains an out-of-range domain index."
        )

    if np.any(
        edge_distances
        <= 0.0
    ):
        raise ValueError(
            "edge_distances must be strictly positive."
        )

    if np.any(
        tau_ij
        < 0.0
    ):
        raise ValueError(
            "tau_ij must be non-negative."
        )

    row_sums = np.sum(
        neighbor_weights,
        axis=1,
    )

    if not np.allclose(
        row_sums,
        1.0,
        rtol=1.0e-5,
        atol=1.0e-6,
    ):
        raise ValueError(
            "neighbor_weights are not normalized per domain."
        )

    for key, array in field.items():
        numeric_array = np.asarray(
            array
        )

        if (
            np.issubdtype(
                numeric_array.dtype,
                np.number,
            )
            and not np.all(
                np.isfinite(
                    numeric_array
                )
            )
        ):
            raise ValueError(
                f"Field '{key}' contains non-finite values."
            )


def _downsample_indices(
    count: int,
    maximum_count: int,
) -> np.ndarray:
    if maximum_count < 1:
        raise ValueError(
            "maximum_count must be positive."
        )

    if count <= maximum_count:
        return np.arange(
            count,
            dtype=int,
        )

    return np.linspace(
        0,
        count - 1,
        maximum_count,
        dtype=int,
    )


def _plot_delay_graph(
    axis: Any,
    field: dict[str, np.ndarray],
    maximum_nodes: int,
    maximum_edges: int,
) -> None:
    coords = field[
        "coords_3d"
    ]

    phases = field[
        "phases"
    ]

    neighbor_indices = field[
        "neighbor_indices"
    ]

    tau_ij = field[
        "tau_ij"
    ]

    node_indices = _downsample_indices(
        coords.shape[
            0
        ],
        maximum_nodes,
    )

    selected_coords = coords[
        node_indices
    ]

    selected_phases = phases[
        node_indices
    ]

    scatter = axis.scatter(
        selected_coords[
            :,
            0,
        ],
        selected_coords[
            :,
            1,
        ],
        selected_coords[
            :,
            2,
        ],
        c=selected_phases,
        cmap="twilight",
        s=18,
        alpha=0.85,
        vmin=-np.pi,
        vmax=np.pi,
    )

    edge_candidates: list[
        tuple[
            float,
            int,
            int,
        ]
    ] = []

    for source_index in node_indices:
        for local_neighbor_index, target_index in enumerate(
            neighbor_indices[
                source_index
            ]
        ):
            edge_candidates.append(
                (
                    float(
                        tau_ij[
                            source_index,
                            local_neighbor_index,
                        ]
                    ),
                    int(
                        source_index
                    ),
                    int(
                        target_index
                    ),
                )
            )

    if (
        edge_candidates
        and maximum_edges > 0
    ):
        edge_candidates.sort(
            key=lambda item: item[
                0
            ],
            reverse=True,
        )

        retained_edges = edge_candidates[
            :maximum_edges
        ]

        edge_delays = np.asarray(
            [
                edge[
                    0
                ]
                for edge in retained_edges
            ],
            dtype=float,
        )

        delay_min = float(
            edge_delays.min()
        )

        delay_range = (
            float(
                np.ptp(
                    edge_delays
                )
            )
            + 1.0e-12
        )

        for delay_value, source_index, target_index in retained_edges:
            source = coords[
                source_index
            ]

            target = coords[
                target_index
            ]

            normalized_delay = (
                delay_value
                - delay_min
            ) / delay_range

            axis.plot(
                (
                    source[
                        0
                    ],
                    target[
                        0
                    ],
                ),
                (
                    source[
                        1
                    ],
                    target[
                        1
                    ],
                ),
                (
                    source[
                        2
                    ],
                    target[
                        2
                    ],
                ),
                alpha=(
                    0.08
                    + 0.42
                    * normalized_delay
                ),
                linewidth=(
                    0.4
                    + 1.2
                    * normalized_delay
                ),
            )

    axis.set_xlabel(
        "X"
    )

    axis.set_ylabel(
        "Y"
    )

    axis.set_zlabel(
        "Z"
    )

    axis.set_title(
        "Calculated 3D phase-delay graph"
    )

    plt.colorbar(
        scatter,
        ax=axis,
        pad=0.1,
        shrink=0.65,
        label="Phase theta",
    )


def plot_delay_diagnostics(
    snapshot_dir: str | Path = "edk_delay_snapshots",
    output_path: str | Path = "edk_delay_diagnostics.png",
    maximum_nodes: int = 500,
    maximum_edges: int = 1200,
    show: bool = True,
) -> Path:
    if maximum_nodes < 1:
        raise ValueError(
            "maximum_nodes must be positive."
        )

    if maximum_edges < 0:
        raise ValueError(
            "maximum_edges must be non-negative."
        )

    metrics = load_delay_metrics(
        snapshot_dir
    )

    field = load_latest_delay_field(
        snapshot_dir
    )

    figure = plt.figure(
        figsize=(
            18,
            11,
        )
    )

    grid = figure.add_gridspec(
        2,
        2,
    )

    tacts = metrics[
        "tacts"
    ]

    axis_1 = figure.add_subplot(
        grid[
            0,
            0,
        ]
    )

    axis_1.plot(
        tacts,
        metrics[
            "R_t_phase_order"
        ],
        marker="o",
        label="R(t): global phase order",
    )

    axis_1.plot(
        tacts,
        metrics[
            "delayed_local_phase_order"
        ],
        marker="s",
        label="Delayed local phase order",
    )

    axis_1.set_xlabel(
        "Tact"
    )

    axis_1.set_ylabel(
        "Normalized phase-order value"
    )

    axis_1.set_ylim(
        0.0,
        1.05,
    )

    axis_1.set_title(
        "Global and delayed local phase order"
    )

    axis_1.legend(
        loc="best"
    )

    axis_1.grid(
        True,
        alpha=0.3,
    )

    axis_2 = figure.add_subplot(
        grid[
            0,
            1,
        ]
    )

    axis_2.plot(
        tacts,
        metrics[
            "mean_phase_velocity"
        ],
        marker="o",
        label="Mean phase velocity",
    )

    axis_2.plot(
        tacts,
        metrics[
            "phase_velocity_dispersion"
        ],
        marker="s",
        label="Phase-velocity dispersion",
    )

    axis_2.set_xlabel(
        "Tact"
    )

    axis_2.set_ylabel(
        "Phase-velocity metric"
    )

    axis_2.set_title(
        "Phase-velocity evolution"
    )

    axis_2.legend(
        loc="best"
    )

    axis_2.grid(
        True,
        alpha=0.3,
    )

    axis_3 = figure.add_subplot(
        grid[
            1,
            0,
        ]
    )

    axis_3.plot(
        tacts,
        metrics[
            "delayed_coupling_energy_proxy"
        ],
        marker="o",
        label="Delayed coupling-energy proxy",
    )

    axis_3.set_xlabel(
        "Tact"
    )

    axis_3.set_ylabel(
        "Coupling proxy"
    )

    axis_3.set_ylim(
        -1.05,
        1.05,
    )

    axis_3.set_title(
        "Delayed coupling agreement"
    )

    axis_3.grid(
        True,
        alpha=0.3,
    )

    delay_summary = (
        f"Final tact: "
        f"{int(tacts[-1])}\n"
        f"Final time: "
        f"{metrics['simulation_time'][-1]:.6f}\n"
        f"Mean delay: "
        f"{metrics['mean_delay'][-1]:.6f}\n"
        f"Maximum delay: "
        f"{metrics['maximum_delay'][-1]:.6f}\n"
        f"Delay dispersion: "
        f"{metrics['delay_dispersion'][-1]:.6f}\n"
        f"History depth: "
        f"{int(round(metrics['history_buffer_depth'][-1]))}"
    )

    axis_3.text(
        0.02,
        0.04,
        delay_summary,
        transform=axis_3.transAxes,
        verticalalignment="bottom",
        bbox={
            "boxstyle": "round",
            "alpha": 0.15,
        },
    )

    axis_3.legend(
        loc="best"
    )

    axis_4 = figure.add_subplot(
        grid[
            1,
            1,
        ],
        projection="3d",
    )

    if field is None:
        axis_4.text2D(
            0.08,
            0.52,
            "No field snapshot found.\n"
            "Run the engine with "
            "--field-every greater than zero.",
            transform=axis_4.transAxes,
        )

        axis_4.set_title(
            "Calculated 3D phase-delay graph"
        )

        axis_4.set_axis_off()

    else:
        _validate_field_shapes(
            field
        )

        _plot_delay_graph(
            axis=axis_4,
            field=field,
            maximum_nodes=maximum_nodes,
            maximum_edges=maximum_edges,
        )

    figure.suptitle(
        "EDK Spatiotemporal Phase-Delay Diagnostics",
        fontsize=15,
    )

    figure.tight_layout(
        rect=(
            0.0,
            0.0,
            1.0,
            0.97,
        )
    )

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
    )

    print(
        f"Saved delay diagnostic panel to '{output}'."
    )

    if show:
        plt.show()

    else:
        plt.close(
            figure
        )

    return output


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot diagnostics from the "
            "EDK spatiotemporal phase-delay engine."
        )
    )

    parser.add_argument(
        "--snapshot-dir",
        default="edk_delay_snapshots",
    )

    parser.add_argument(
        "--output",
        default="edk_delay_diagnostics.png",
    )

    parser.add_argument(
        "--maximum-nodes",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--maximum-edges",
        type=int,
        default=1200,
    )

    parser.add_argument(
        "--no-show",
        action="store_true",
    )

    return parser


def main() -> None:
    args = build_argument_parser().parse_args()

    plot_delay_diagnostics(
        snapshot_dir=args.snapshot_dir,
        output_path=args.output,
        maximum_nodes=args.maximum_nodes,
        maximum_edges=args.maximum_edges,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
