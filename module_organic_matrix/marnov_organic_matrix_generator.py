from __future__ import annotations

from typing import Any

import numpy as np


class MarnovOrganicMatrixGenerator:
    """
    Conceptual generator of a recursive three-dimensional organic matrix.

    The module implements tact-by-tact growth of an organic-density field
    from an asymmetric toroidal cubic-retention field C3.

    The numerical model combines:
    - central initiation;
    - asymmetric toroidal retention;
    - nonlinear diffusion;
    - density-limited local growth;
    - nonlinear saturation;
    - recursive phase-shifted branching modulation;
    - organic appearance diagnostics.
    """

    STABLE_MANIFESTATION = "STABLE ORGANIC MATRIX MANIFESTATION"
    PARTIAL_MANIFESTATION = "PARTIAL ORGANIC MATRIX MANIFESTATION"
    WEAK_MANIFESTATION = "WEAK OR EMERGING ORGANIC MATRIX MANIFESTATION"

    def __init__(
        self,
        grid_size: int = 64,
        dx: float = 0.05,
    ) -> None:
        """
        Initialize the three-dimensional organic matrix.

        Parameters
        ----------
        grid_size:
            Number of cells along each spatial axis.
        dx:
            Spatial discretization interval.
        """
        if isinstance(grid_size, bool):
            raise ValueError("grid_size must be an integer.")

        try:
            converted_grid_size = int(grid_size)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("grid_size must be an integer.") from exc

        if converted_grid_size != grid_size:
            raise ValueError("grid_size must be an integer.")

        if converted_grid_size < 8:
            raise ValueError("grid_size must be at least 8.")

        self.grid_size = converted_grid_size
        self.dx = self._positive_finite("dx", dx)

        self.shape = (
            self.grid_size,
            self.grid_size,
            self.grid_size,
        )

        self.bio_density = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        center = self.grid_size // 2
        self.center_x = center
        self.center_y = center
        self.center_z = center

        self.bio_density[
            self.center_x,
            self.center_y,
            self.center_z,
        ] = 1.0

        x, y, z = np.indices(
            self.shape,
            dtype=np.float64,
        )

        self.x_offset = x - self.center_x
        self.y_offset = y - self.center_y
        self.z_offset = z - self.center_z

        self.radial_distance = np.sqrt(
            self.x_offset ** 2
            + self.y_offset ** 2
        )

        self.theta = np.arctan2(
            self.y_offset,
            self.x_offset,
        )

        self.C3_field = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        self.organic_appearance_index = 0.0
        self.active_density_fraction = 0.0
        self.branching_contrast = 0.0
        self.mean_bio_density = float(np.mean(self.bio_density))
        self.toroidal_retention = 0.0
        self.completed_tacts = 0

        # Backward-compatible alias used by the existing README and scripts.
        self.completed_steps = 0

        self._validate_complete_state()

    @staticmethod
    def _finite_scalar(
        name: str,
        value: float,
    ) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _positive_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    @classmethod
    def _non_negative_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")

        return scalar

    @classmethod
    def _bounded_finite(
        cls,
        name: str,
        value: float,
        lower: float,
        upper: float,
    ) -> float:
        scalar = cls._finite_scalar(name, value)

        if not lower <= scalar <= upper:
            raise ValueError(f"{name} must be within [{lower}, {upper}].")

        return scalar

    def _validate_field(
        self,
        field: np.ndarray,
        name: str,
    ) -> np.ndarray:
        array = np.asarray(field, dtype=np.float64)

        if array.shape != self.shape:
            raise ValueError(
                f"{name} shape must be {self.shape}, received {array.shape}."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} contains non-finite values.")

        return array

    def generate_asymmetric_c3_field(
        self,
        epsilon: float = 0.236068,
        torus_radius: float | None = None,
        torus_width: float = 3.0,
    ) -> np.ndarray:
        """
        Generate an asymmetric toroidal cubic-retention field C3.

        Parameters
        ----------
        epsilon:
            Strength of angular and vertical asymmetry.
        torus_radius:
            Major radius of the toroidal field in grid cells. If omitted,
            grid_size / 5 is used.
        torus_width:
            Gaussian width of the toroidal retention region.

        Returns
        -------
        np.ndarray:
            Three-dimensional asymmetric toroidal field C3.
        """
        epsilon = self._non_negative_finite("epsilon", epsilon)
        torus_width = self._positive_finite("torus_width", torus_width)

        if torus_radius is None:
            torus_radius = self.grid_size / 5.0

        torus_radius = self._positive_finite(
            "torus_radius",
            torus_radius,
        )

        toroidal_distance = np.sqrt(
            (self.radial_distance - torus_radius) ** 2
            + self.z_offset ** 2
        )

        toroidal_envelope = np.exp(
            -toroidal_distance ** 2
            / (2.0 * torus_width ** 2)
        )

        asymmetry_factor = (
            1.0
            + epsilon
            * np.sin(
                3.0 * self.theta
                + 0.1 * self.z_offset
            )
        )

        self.C3_field = np.clip(
            asymmetry_factor * toroidal_envelope,
            0.0,
            None,
        )

        if not np.all(np.isfinite(self.C3_field)):
            raise FloatingPointError("C3_field contains non-finite values.")

        return self.C3_field.copy()

    def _calculate_laplacian(
        self,
        field: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the three-dimensional discrete Laplacian.

        Periodic boundary conditions are produced by numpy.roll.
        """
        field = self._validate_field(field, "field")

        laplacian = np.zeros_like(
            field,
            dtype=np.float64,
        )

        for axis in range(3):
            laplacian += (
                np.roll(field, 1, axis=axis)
                + np.roll(field, -1, axis=axis)
                - 2.0 * field
            ) / (self.dx ** 2)

        if not np.all(np.isfinite(laplacian)):
            raise FloatingPointError("laplacian contains non-finite values.")

        return laplacian

    def _resolve_tact_count(
        self,
        steps: int | None,
        tacts: int | None,
    ) -> int:
        if tacts is not None:
            count = tacts
        elif steps is not None:
            count = steps
        else:
            count = 15

        if isinstance(count, bool):
            raise ValueError("tact count must be an integer.")

        try:
            converted = int(count)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("tact count must be an integer.") from exc

        if converted != count:
            raise ValueError("tact count must be an integer.")

        if converted <= 0:
            raise ValueError("tact count must be positive.")

        return converted

    def grow_organic_matrix(
        self,
        C3: np.ndarray,
        steps: int | None = 15,
        diffusion_coefficient: float = 0.15,
        growth_strength: float = 2.0,
        saturation_strength: float = 0.35,
        branching_strength: float = 0.12,
        cfl_safety: float = 0.9,
        tacts: int | None = None,
    ) -> np.ndarray:
        """
        Execute recursive tact-by-tact growth of the organic matrix.

        Each tact combines:
        - nonlinear spatial diffusion;
        - retention pressure from C3;
        - density-limited local growth;
        - nonlinear saturation;
        - phase-shifted asymmetric branching modulation.
        """
        C3 = self._validate_field(C3, "C3")
        tact_count = self._resolve_tact_count(steps=steps, tacts=tacts)

        diffusion_coefficient = self._non_negative_finite(
            "diffusion_coefficient",
            diffusion_coefficient,
        )
        growth_strength = self._non_negative_finite(
            "growth_strength",
            growth_strength,
        )
        saturation_strength = self._non_negative_finite(
            "saturation_strength",
            saturation_strength,
        )
        branching_strength = self._non_negative_finite(
            "branching_strength",
            branching_strength,
        )
        cfl_safety = self._bounded_finite(
            "cfl_safety",
            cfl_safety,
            0.0,
            1.0,
        )

        if cfl_safety == 0.0:
            raise ValueError("cfl_safety must be greater than zero.")

        self.C3_field = C3.copy()

        if diffusion_coefficient > 0.0:
            dt = (
                cfl_safety
                * self.dx ** 2
                / (6.0 * diffusion_coefficient)
            )
        else:
            dt = 0.01

        golden_phase_increment = np.pi * (3.0 - np.sqrt(5.0))

        for local_tact_index in range(tact_count):
            global_tact_index = self.completed_tacts + local_tact_index

            laplacian = self._calculate_laplacian(self.bio_density)

            branching_modulation = (
                1.0
                + branching_strength
                * np.sin(
                    3.0 * self.theta
                    + 0.17 * self.z_offset
                    + global_tact_index * golden_phase_increment
                )
            )

            available_capacity = 1.0 - self.bio_density

            retained_growth = (
                growth_strength
                * C3
                * branching_modulation
                * available_capacity
            )

            nonlinear_saturation = saturation_strength * self.bio_density ** 2

            growth_rate = (
                diffusion_coefficient * laplacian
                + retained_growth
                - nonlinear_saturation
            )

            if not np.all(np.isfinite(growth_rate)):
                raise FloatingPointError("growth_rate contains non-finite values.")

            self.bio_density = np.clip(
                self.bio_density + dt * growth_rate,
                0.0,
                1.0,
            )

        self.completed_tacts += tact_count
        self.completed_steps = self.completed_tacts

        self._update_organic_appearance()
        self._validate_complete_state()

        return self.bio_density.copy()

    def calculate_density_channel_proxy(self) -> dict[str, np.ndarray | float]:
        """
        Calculate a density-channel proxy from the organic-density gradient.
        """
        gradients = np.gradient(self.bio_density, self.dx)
        gradient_x, gradient_y, gradient_z = gradients

        channel_x = -gradient_x
        channel_y = -gradient_y
        channel_z = -gradient_z

        channel_magnitude = np.sqrt(
            channel_x ** 2
            + channel_y ** 2
            + channel_z ** 2
        )

        if not np.all(np.isfinite(channel_magnitude)):
            raise FloatingPointError("density channel contains non-finite values.")

        return {
            "channel_x": channel_x,
            "channel_y": channel_y,
            "channel_z": channel_z,
            "channel_magnitude": channel_magnitude,
            "mean_channel_magnitude": float(np.mean(channel_magnitude)),
            "max_channel_magnitude": float(np.max(channel_magnitude)),
        }

    def _update_organic_appearance(self) -> None:
        """
        Update the organic appearance layer.
        """
        self.mean_bio_density = float(np.mean(self.bio_density))

        self.active_density_fraction = float(
            np.mean(self.bio_density > 0.05)
        )

        self.branching_contrast = float(np.std(self.bio_density))

        C3_normalization = float(np.sum(self.C3_field))

        if C3_normalization > 0.0:
            self.toroidal_retention = float(
                np.sum(self.bio_density * self.C3_field) / C3_normalization
            )
        else:
            self.toroidal_retention = 0.0

        self.organic_appearance_index = float(
            self.mean_bio_density
            * (1.0 + self.active_density_fraction)
            * (1.0 + self.branching_contrast)
            * (1.0 + self.toroidal_retention)
        )

        scalar_state = (
            self.mean_bio_density,
            self.active_density_fraction,
            self.branching_contrast,
            self.toroidal_retention,
            self.organic_appearance_index,
        )

        if any(not np.isfinite(value) for value in scalar_state):
            raise FloatingPointError("organic appearance state became non-finite.")

    def calculate_organic_appearance(self) -> dict[str, float | int | str]:
        """
        Return the current organic appearance state.
        """
        if self.organic_appearance_index >= 0.50:
            manifestation_regime = self.STABLE_MANIFESTATION
        elif self.organic_appearance_index >= 0.10:
            manifestation_regime = self.PARTIAL_MANIFESTATION
        else:
            manifestation_regime = self.WEAK_MANIFESTATION

        return {
            "organic_appearance_index": float(self.organic_appearance_index),
            "manifestation_regime": manifestation_regime,
            "mean_bio_density": float(self.mean_bio_density),
            "active_density_fraction": float(self.active_density_fraction),
            "branching_contrast": float(self.branching_contrast),
            "toroidal_retention": float(self.toroidal_retention),
            "completed_tacts": int(self.completed_tacts),
            "completed_steps": int(self.completed_steps),
        }

    def visualize_organic_slice(
        self,
        show: bool = True,
    ) -> Any:
        """
        Visualize horizontal and vertical slices of the organic matrix.

        Returns
        -------
        matplotlib.figure.Figure
            The generated figure object.
        """
        import matplotlib.pyplot as plt

        mid_z = self.grid_size // 2
        mid_y = self.grid_size // 2

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        ax_xy, ax_xz = axes

        fig.suptitle(
            "Marnov Protocol — Organic Matrix Manifestation",
            fontsize=13,
            fontweight="bold",
        )

        image_xy = ax_xy.imshow(
            self.bio_density[:, :, mid_z],
            origin="lower",
            interpolation="nearest",
        )
        ax_xy.set_title("XY Organic-Matrix Slice")
        ax_xy.set_xlabel("X Projection")
        ax_xy.set_ylabel("Y Projection")
        fig.colorbar(
            image_xy,
            ax=ax_xy,
            label="Organic Density",
        )

        image_xz = ax_xz.imshow(
            self.bio_density[mid_y, :, :],
            origin="lower",
            interpolation="nearest",
        )
        ax_xz.set_title("XZ Organic-Matrix Slice")
        ax_xz.set_xlabel("Z Projection")
        ax_xz.set_ylabel("X Projection")
        fig.colorbar(
            image_xz,
            ax=ax_xz,
            label="Organic Density",
        )

        plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))

        if show:
            plt.show()

        return fig

    def _validate_complete_state(self) -> None:
        fields = {
            "bio_density": self.bio_density,
            "C3_field": self.C3_field,
        }

        for name, field in fields.items():
            if field.shape != self.shape:
                raise RuntimeError(f"{name} has an invalid shape.")

            if not np.all(np.isfinite(field)):
                raise FloatingPointError(f"{name} contains non-finite values.")

        if np.any(self.bio_density < 0.0) or np.any(self.bio_density > 1.0):
            raise RuntimeError("bio_density left the interval [0, 1].")

        scalars = {
            "organic_appearance_index": self.organic_appearance_index,
            "active_density_fraction": self.active_density_fraction,
            "branching_contrast": self.branching_contrast,
            "mean_bio_density": self.mean_bio_density,
            "toroidal_retention": self.toroidal_retention,
        }

        for name, value in scalars.items():
            if not np.isfinite(value):
                raise FloatingPointError(f"{name} is non-finite.")


def run_demo() -> None:
    generator = MarnovOrganicMatrixGenerator(
        grid_size=64,
        dx=0.05,
    )

    print("1. Activating asymmetric toroidal cubic-retention field C3...")

    C3_field = generator.generate_asymmetric_c3_field(
        epsilon=0.236068,
    )

    print("2. Starting recursive organic-matrix growth for 15 tacts...")

    generator.grow_organic_matrix(
        C3=C3_field,
        steps=15,
    )

    appearance_state = generator.calculate_organic_appearance()
    channel_state = generator.calculate_density_channel_proxy()

    print(
        "3. Organic appearance index: "
        f"{appearance_state['organic_appearance_index']:.6f}"
    )
    print(
        "4. Manifestation regime: "
        f"{appearance_state['manifestation_regime']}"
    )
    print(
        "5. Active density fraction: "
        f"{appearance_state['active_density_fraction']:.6f}"
    )
    print(
        "6. Mean density-channel magnitude: "
        f"{channel_state['mean_channel_magnitude']:.6f}"
    )
    print("7. Displaying horizontal and vertical organic-matrix slices...")

    generator.visualize_organic_slice(show=True)


if __name__ == "__main__":
    run_demo()
