from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
from typing import Any

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


def _extract_step_from_path(path: str) -> int:
    stem = Path(path).stem
    suffix = stem.rsplit("_", maxsplit=1)[-1]

    try:
        return int(suffix)
    except ValueError as exc:
        raise ValueError(
            f"Unable to extract numeric step identifier from '{path}'."
        ) from exc


def load_delay_metrics(
    snapshot_dir: str = "edk_delay_snapshots",
) -> dict[str, np.ndarray]:
    search_path = os.path.join(
        snapshot_dir,
        "delay_step_*.json",
    )

    files = sorted(
        glob.glob(search_path),
        key=_extract_step_from_path,
    )

    if not files:
        raise FileNotFoundError(
            f"No delay metric snapshots found in '{snapshot_dir}'."
        )

    steps: list[int] = []

    metric_history: dict[str, list[float]] = {
        key: []
        for key in REQUIRED_METRIC_KEYS
    }

    for filename in files:
        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as stream:
            record = json.load(
                stream
            )

        if "step" not in record:
            raise KeyError(
                f"Missing 'step' in '{filename}'."
            )

        if "metrics" not in record:
            raise KeyError(
                f"Missing 'metrics' in '{filename}'."
            )

        metrics = record["metrics"]

        missing_keys = [
            key
            for key in REQUIRED_METRIC_KEYS
            if key not in metrics
        ]

        if missing_keys:
            raise KeyError(
                f"Missing metric keys in '{filename}': "
                f"{missing_keys}"
            )

        steps.append(
            int(
                record["step"]
            )
        )

        for key in REQUIRED_METRIC_KEYS:
            value = float(
                metrics[key]
            )

            if not np.isfinite(
                value
            ):
                raise ValueError(
                    f"Non-finite metric '{key}' "
                    f"in '{filename}': {value}"
                )

            metric_history[key].append(
                value
            )

    result: dict[str, np.ndarray] = {
        "steps": np.asarray(
            steps,
            dtype=int,
        )
    }

    for key, values in metric_history.items():
        result[key] = np.asarray(
            values,
            dtype=float,
        )

    return result


def load_latest_delay_field(
    snapshot_dir: str = "edk_delay_snapshots",
) -> dict[str, np.ndarray] | None:
    search_path = os.path.join(
        snapshot_dir,
        "delay_field_*.npz",
    )

    files = sorted(
        glob.glob(search_path),
        key=_extract_step_from_path,
    )

    if not files:
        return None

    with np.load(
        files[-1],
        allow_pickle=False,
    ) as archive:
        field = {
            key: np.asarray(
                archive[key]
            )
            for key in archive.files
        }

    required_keys = (
        "coords_3d",
        "phases",
        "neighbor_indices",
        "tau_ij",
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
    coords = field["coords_3d"]
    phases = field["phases"]
    neighbor_indices = field["neighbor_indices"]
    tau_ij = field["tau_ij"]
    phase_velocity = field["phase_velocity"]

    if coords.ndim != 2 or coords.shape[1] != 3:
        raise ValueError(
            "coords_3d must have shape (N, 3), "
            f"received {coords.shape}."
        )

    domain_count = coords.shape[0]

    if phases.shape != (
        domain_count,
    ):
        raise ValueError(
            f"phases must have shape ({domain_count},), "
            f"received {phases.shape}."
        )

    if phase_velocity.shape != (
        domain_count,
    ):
        raise ValueError(
            "phase_velocity must have shape "
            f"({domain_count},), "
            f"received {phase_velocity.shape}."
        )

    if neighbor_indices.ndim != 2:
        raise ValueError(
            "neighbor_indices must have shape (N, k)."
        )

    if neighbor_indices.shape[0] != domain_count:
        raise ValueError(
            "neighbor_indices domain count "
            "does not match coords_3d."
        )

    if tau_ij.shape != neighbor_indices.shape:
        raise ValueError(
            "tau_ij shape must match "
            "neighbor_indices shape."
        )

    if np.any(
        neighbor_indices < 0
    ) or np.any(
        neighbor_indices >= domain_count
    ):
        raise ValueError(
            "neighbor_indices contains "
            "an out-of-range domain index."
        )

    for key, array in field.items():
        numeric_array = np.asarray(
            array
        )

        if np.issubdtype(
            numeric_array.dtype,
            np.number,
        ) and not np.all(
            np.isfinite(
                numeric_array
            )
        ):
            raise ValueError(
                f"Field '{key}' contains "
                "non-finite values."
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
    coords = field["coords_3d"]
    phases = field["phases"]
    neighbor_indices = field["neighbor_indices"]
    tau_ij = field["tau_ij"]

    node_indices = _downsample_indices(
        coords.shape[0],
        maximum_nodes,
    )

    selected_coords = coords[
        node_indices
    ]

    selected_phases = phases[
        node_indices
    ]

    scatter = axis.scatter(
        selected_coords[:, 0],
        selected_coords[:, 1],
        selected_coords[:, 2],
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
        for (
            local_neighbor_index,
            target_index,
        ) in enumerate(
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

    if edge_candidates and maximum_edges > 0:
        edge_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        retained_edges = edge_candidates[
            :maximum_edges
        ]

        edge_delays = np.asarray(
            [
                edge[0]
                for edge in retained_edges
            ],
            dtype=float,
        )

        delay_min = float(
            edge_delays.min()
        )

        delay_range = float(
            np.ptp(
                edge_delays
            )
        ) + 1e-12

        for (
            delay_value,
            source_index,
            target_index,
        ) in retained_edges:
            source = coords[
                source_index
            ]

            target = coords[
                target_index
            ]

            normalized_delay = (
                delay_value
                -
                delay_min
            ) / delay_range

            axis.plot(
                (
                    source[0],
                    target[0],
                ),
                (
                    source[1],
                    target[1],
                ),
                (
                    source[2],
                    target[2],
                ),
                alpha=(
                    0.08
                    +
                    0.42
                    *
                    normalized_delay
                ),
                linewidth=(
                    0.4
                    +
                    1.2
                    *
                    normalized_delay
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
    snapshot_dir: str = "edk_delay_snapshots",
    output_path: str = "edk_delay_diagnostics.png",
    maximum_nodes: int = 500,
    maximum_edges: int = 1200,
    show: bool = True,
) -> None:
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

    steps = metrics[
        "steps"
    ]

    axis_1 = figure.add_subplot(
        grid[
            0,
            0,
        ]
    )

    axis_1.plot(
        steps,
        metrics[
            "R_t_phase_order"
        ],
        marker="o",
        label="R(t): global phase order",
    )

    axis_1.plot(
        steps,
        metrics[
            "delayed_local_phase_order"
        ],
        marker="s",
        label="Delayed local phase order",
    )

    axis_1.set_xlabel(
        "Tact-by-tact simulation step"
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
        steps,
        metrics[
            "mean_phase_velocity"
        ],
        marker="o",
        label="Mean phase velocity",
    )

    axis_2.plot(
        steps,
        metrics[
            "phase_velocity_dispersion"
        ],
        marker="s",
        label="Phase-velocity dispersion",
    )

    axis_2.set_xlabel(
        "Tact-by-tact simulation step"
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
        steps,
        metrics[
            "delayed_coupling_energy_proxy"
        ],
        marker="o",
        label="Delayed coupling-energy proxy",
    )

    axis_3.set_xlabel(
        "Tact-by-tact simulation step"
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
        f"Saved delay diagnostic panel "
        f"to '{output}'."
    )

    if show:
        plt.show()

    else:
        plt.close(
            figure
        )


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
