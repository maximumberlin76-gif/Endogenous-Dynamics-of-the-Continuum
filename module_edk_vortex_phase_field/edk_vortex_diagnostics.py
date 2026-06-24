from __future__ import annotations

import argparse
import glob
import json
import os

import matplotlib.pyplot as plt
import numpy as np


def load_vortex_metrics(
    snapshot_dir: str = "edk_vortex_snapshots",
) -> dict[str, np.ndarray]:
    search_path = os.path.join(
        snapshot_dir,
        "vortex_step_*.json",
    )

    files = sorted(
        glob.glob(search_path)
    )

    if not files:
        raise FileNotFoundError(
            f"No vortex metric snapshots found in '{snapshot_dir}'."
        )

    steps: list[int] = []
    metrics: dict[str, list[float]] = {}

    for filename in files:
        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as stream:
            record = json.load(stream)

        steps.append(
            int(record["step"])
        )

        for key, value in record["metrics"].items():
            metrics.setdefault(
                key,
                [],
            ).append(
                float(value)
            )

    result: dict[str, np.ndarray] = {
        "steps": np.asarray(
            steps,
            dtype=int,
        )
    }

    result.update(
        {
            key: np.asarray(
                values,
                dtype=float,
            )
            for key, values in metrics.items()
        }
    )

    return result


def load_latest_field_snapshot(
    snapshot_dir: str = "edk_vortex_snapshots",
) -> dict[str, np.ndarray]:
    search_path = os.path.join(
        snapshot_dir,
        "vortex_field_*.npz",
    )

    files = sorted(
        glob.glob(search_path)
    )

    if not files:
        raise FileNotFoundError(
            f"No vortex field snapshots found in '{snapshot_dir}'. "
            "Run the engine with --field-every greater than zero."
        )

    with np.load(files[-1]) as data:
        return {
            key: np.asarray(data[key])
            for key in data.files
        }


def _downsample_indices(
    count: int,
    max_vectors: int,
) -> np.ndarray:
    if count <= max_vectors:
        return np.arange(
            count,
            dtype=int,
        )

    step = max(
        1,
        count // max_vectors,
    )

    return np.arange(
        0,
        count,
        step,
        dtype=int,
    )[:max_vectors]


def plot_vortex_diagnostics(
    snapshot_dir: str = "edk_vortex_snapshots",
    output_path: str = "edk_vortex_diagnostics.png",
    max_vectors: int = 600,
    show: bool = True,
) -> None:
    metrics = load_vortex_metrics(
        snapshot_dir
    )

    field = load_latest_field_snapshot(
        snapshot_dir
    )

    steps = metrics["steps"]

    figure = plt.figure(
        figsize=(18, 6)
    )

    axis_1 = figure.add_subplot(
        1,
        3,
        1,
    )

    axis_1.plot(
        steps,
        metrics["continuum_appearance_index"],
        marker="o",
        label="CAI proxy",
    )

    axis_1.set_xlabel(
        "Tact-by-tact simulation step"
    )

    axis_1.set_ylabel(
        "Appearance-index proxy"
    )

    axis_1.set_title(
        "Appearance and vortex intensity"
    )

    axis_1_twin = axis_1.twinx()

    axis_1_twin.plot(
        steps,
        metrics["mean_vorticity_abs"],
        marker="s",
        linestyle="--",
        label="mean |curl J|",
    )

    axis_1_twin.set_ylabel(
        "Mean discrete vorticity"
    )

    handles_1, labels_1 = (
        axis_1.get_legend_handles_labels()
    )

    handles_2, labels_2 = (
        axis_1_twin.get_legend_handles_labels()
    )

    axis_1.legend(
        handles_1 + handles_2,
        labels_1 + labels_2,
        loc="best",
    )

    axis_2 = figure.add_subplot(
        1,
        3,
        2,
    )

    axis_2.plot(
        steps,
        metrics["R_t_phase_order"],
        label="R(t): phase order",
    )

    axis_2.plot(
        steps,
        metrics["C_proxy_t"],
        label="C_proxy(t)",
    )

    axis_2.plot(
        steps,
        metrics["interface_retention_proxy"],
        label="interface proxy",
    )

    axis_2.set_xlabel(
        "Tact-by-tact simulation step"
    )

    axis_2.set_ylabel(
        "Normalized value"
    )

    axis_2.set_ylim(
        0.0,
        1.05,
    )

    axis_2.set_title(
        "Phase order and retention proxies"
    )

    axis_2.legend(
        loc="best"
    )

    axis_3 = figure.add_subplot(
        1,
        3,
        3,
        projection="3d",
    )

    coordinates = field["coords_3d"]
    curl_j = field["curl_J"]

    indices = _downsample_indices(
        coordinates.shape[0],
        max_vectors=max_vectors,
    )

    coordinates = coordinates[indices]
    curl_j = curl_j[indices]

    magnitudes = np.linalg.norm(
        curl_j,
        axis=1,
    )

    nonzero = magnitudes > 1e-12

    if np.any(nonzero):
        coordinates = coordinates[nonzero]
        curl_j = curl_j[nonzero]
        magnitudes = magnitudes[nonzero]

        normalized_vectors = (
            curl_j
            / magnitudes[:, None]
        )

        normalized_magnitude = (
            magnitudes
            - magnitudes.min()
        ) / (
            np.ptp(magnitudes)
            + 1e-12
        )

        vector_colors = plt.cm.viridis(
            normalized_magnitude
        )

        axis_3.quiver(
            coordinates[:, 0],
            coordinates[:, 1],
            coordinates[:, 2],
            normalized_vectors[:, 0],
            normalized_vectors[:, 1],
            normalized_vectors[:, 2],
            length=0.45,
            normalize=False,
            colors=vector_colors,
            linewidth=0.7,
        )

        color_map = plt.cm.ScalarMappable(
            cmap="viridis"
        )

        color_map.set_array(
            magnitudes
        )

        color_bar = figure.colorbar(
            color_map,
            ax=axis_3,
            pad=0.1,
            shrink=0.65,
        )

        color_bar.set_label(
            "|curl J|"
        )

    axis_3.set_xlabel("X")
    axis_3.set_ylabel("Y")
    axis_3.set_zlabel("Z")

    axis_3.set_title(
        "Calculated 3D discrete curl field"
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    print(
        f"Saved diagnostic panel to '{output_path}'."
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
            "EDK vortex phase-field engine."
        )
    )

    parser.add_argument(
        "--snapshot-dir",
        default="edk_vortex_snapshots",
    )

    parser.add_argument(
        "--output",
        default="edk_vortex_diagnostics.png",
    )

    parser.add_argument(
        "--max-vectors",
        type=int,
        default=600,
    )

    parser.add_argument(
        "--no-show",
        action="store_true",
    )

    return parser


def main() -> None:
    args = build_argument_parser().parse_args()

    plot_vortex_diagnostics(
        snapshot_dir=args.snapshot_dir,
        output_path=args.output,
        max_vectors=args.max_vectors,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
