import numpy as np
import matplotlib.pyplot as plt


class MarnovOrganicMatrixGenerator:
    """
    Conceptual generator of a three-dimensional organic matrix.

    The module models recursive tact-by-tact growth of a biological-density
    field from an asymmetric toroidal cubic-retention field C3.

    The numerical model combines:
    - a central initiation point,
    - an asymmetric toroidal retention field,
    - nonlinear diffusion,
    - density-limited growth,
    - recursive phase-shifted branching modulation,
    - an organic appearance layer.

    The module is a numerical sandbox model. It does not simulate a complete
    living organism and does not by itself prove a physical theory of life.
    """

    def __init__(
        self,
        grid_size: int = 64,
        dx: float = 0.05,
    ):
        """
        Initialize the three-dimensional organic matrix.

        Parameters
        ----------
        grid_size:
            Number of cells along each spatial axis.
        dx:
            Spatial discretization interval.
        """
        if grid_size < 8:
            raise ValueError("grid_size must be at least 8.")
        if dx <= 0.0:
            raise ValueError("dx must be positive.")

        self.grid_size = grid_size
        self.dx = dx
        self.shape = (
            grid_size,
            grid_size,
            grid_size,
        )

        # Density field of the organic matrix.
        self.bio_density = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        # Central initiation point:
        # ancestor cell or local wave-focus of structural growth.
        center = grid_size // 2
        self.bio_density[
            center,
            center,
            center,
        ] = 1.0

        # Centered spatial coordinate fields.
        x, y, z = np.indices(
            self.shape,
            dtype=np.float64,
        )

        self.center_x = center
        self.center_y = center
        self.center_z = center

        self.x_offset = x - self.center_x
        self.y_offset = y - self.center_y
        self.z_offset = z - self.center_z

        self.radial_distance = np.sqrt(
            self.x_offset**2
            + self.y_offset**2
        )

        self.theta = np.arctan2(
            self.y_offset,
            self.x_offset,
        )

        # Current asymmetric cubic-retention field.
        self.C3_field = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        # Organic appearance layer.
        self.organic_appearance_index = 0.0
        self.active_density_fraction = 0.0
        self.branching_contrast = 0.0
        self.mean_bio_density = 0.0

        # Number of completed recursive growth tacts.
        self.completed_steps = 0

    def generate_asymmetric_c3_field(
        self,
        epsilon: float = 0.236068,
        torus_radius: float | None = None,
        torus_width: float = 3.0,
    ) -> np.ndarray:
        """
        Generate an asymmetric toroidal cubic-retention field C3.

        The parameter epsilon introduces a persistent angular asymmetry.
        The default value 0.236068 is related to the golden-ratio remainder
        used here as an irrational asymmetry coefficient.

        Parameters
        ----------
        epsilon:
            Strength of angular and vertical asymmetry.
        torus_radius:
            Major radius of the toroidal field in grid cells.
            If omitted, grid_size / 5 is used.
        torus_width:
            Gaussian width of the toroidal retention region.

        Returns
        -------
        np.ndarray:
            Three-dimensional asymmetric toroidal field C3.
        """
        if epsilon < 0.0:
            raise ValueError("epsilon must be non-negative.")
        if torus_width <= 0.0:
            raise ValueError("torus_width must be positive.")

        if torus_radius is None:
            torus_radius = self.grid_size / 5.0

        if torus_radius <= 0.0:
            raise ValueError("torus_radius must be positive.")

        # Distance from every grid point to the toroidal core line.
        toroidal_distance = np.sqrt(
            (self.radial_distance - torus_radius) ** 2
            + self.z_offset**2
        )

        # Persistent three-fold angular asymmetry with vertical phase drift.
        asymmetry_factor = (
            1.0
            + epsilon
            * np.sin(
                3.0 * self.theta
                + 0.1 * self.z_offset
            )
        )

        # Gaussian toroidal retention envelope.
        toroidal_envelope = np.exp(
            -(
                toroidal_distance**2
            )
            / (
                2.0 * torus_width**2
            )
        )

        self.C3_field = (
            asymmetry_factor
            * toroidal_envelope
        )

        # Prevent negative retention values for large custom epsilon values.
        self.C3_field = np.clip(
            self.C3_field,
            0.0,
            None,
        )

        return self.C3_field.copy()

    def _calculate_laplacian(
        self,
        field: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the three-dimensional discrete Laplacian.

        Periodic boundary conditions are produced by numpy.roll.

        Parameters
        ----------
        field:
            Three-dimensional scalar field.

        Returns
        -------
        np.ndarray:
            Discrete spatial Laplacian of the field.
        """
        laplacian = np.zeros_like(
            field,
            dtype=np.float64,
        )

        for axis in range(3):
            laplacian += (
                np.roll(field, 1, axis=axis)
                + np.roll(field, -1, axis=axis)
                - 2.0 * field
            ) / (self.dx**2)

        return laplacian

    def grow_organic_matrix(
        self,
        C3: np.ndarray,
        steps: int = 15,
        diffusion_coefficient: float = 0.15,
        growth_strength: float = 2.0,
        saturation_strength: float = 0.35,
        branching_strength: float = 0.12,
        cfl_safety: float = 0.9,
    ) -> np.ndarray:
        """
        Execute recursive tact-by-tact growth of the organic matrix.

        Each tact combines:
        - nonlinear spatial diffusion,
        - retention pressure from C3,
        - density-limited growth,
        - nonlinear saturation,
        - phase-shifted asymmetric branching modulation.

        Parameters
        ----------
        C3:
            Three-dimensional asymmetric retention field.
        steps:
            Number of recursive growth tacts.
        diffusion_coefficient:
            Diffusion coefficient of the surrounding dynamic medium.
        growth_strength:
            Strength of C3-driven organic growth.
        saturation_strength:
            Nonlinear suppression of excessive local density.
        branching_strength:
            Strength of recursive asymmetric channel formation.
        cfl_safety:
            Stability coefficient for explicit three-dimensional diffusion.

        Returns
        -------
        np.ndarray:
            Updated biological-density field.
        """
        C3 = np.asarray(
            C3,
            dtype=np.float64,
        )

        if C3.shape != self.shape:
            raise ValueError(
                "C3 shape must match the organic matrix shape."
            )
        if steps <= 0:
            raise ValueError("steps must be positive.")
        if diffusion_coefficient < 0.0:
            raise ValueError(
                "diffusion_coefficient must be non-negative."
            )
        if growth_strength < 0.0:
            raise ValueError(
                "growth_strength must be non-negative."
            )
        if saturation_strength < 0.0:
            raise ValueError(
                "saturation_strength must be non-negative."
            )
        if branching_strength < 0.0:
            raise ValueError(
                "branching_strength must be non-negative."
            )
        if not 0.0 < cfl_safety <= 1.0:
            raise ValueError(
                "cfl_safety must be in the interval (0, 1]."
            )

        self.C3_field = C3.copy()

        # Explicit three-dimensional diffusion stability condition:
        #
        # diffusion_coefficient * dt / dx^2 <= 1 / 6
        #
        # The original dt = 0.1 is unstable for:
        # diffusion_coefficient = 0.15 and dx = 0.05.
        if diffusion_coefficient > 0.0:
            stability_limit = (
                self.dx**2
                / (
                    6.0
                    * diffusion_coefficient
                )
            )

            dt = (
                cfl_safety
                * stability_limit
            )
        else:
            dt = 0.01

        # Golden-angle phase increment:
        # introduces a non-repeating recursive angular displacement.
        golden_phase_increment = (
            np.pi
            * (
                3.0
                - np.sqrt(5.0)
            )
        )

        for local_step in range(steps):
            global_step = (
                self.completed_steps
                + local_step
            )

            laplacian = self._calculate_laplacian(
                self.bio_density
            )

            # Recursive asymmetric branching field.
            #
            # The phase changes on every tact and therefore prevents the same
            # angular growth channel from being reproduced identically.
            branching_modulation = (
                1.0
                + branching_strength
                * np.sin(
                    3.0 * self.theta
                    + 0.17 * self.z_offset
                    + global_step
                    * golden_phase_increment
                )
            )

            # Available local capacity before complete density saturation.
            available_capacity = (
                1.0
                - self.bio_density
            )

            # C3-driven structural retention and growth.
            retained_growth = (
                growth_strength
                * C3
                * branching_modulation
                * available_capacity
            )

            # Nonlinear local saturation:
            # prevents unlimited density accumulation and sharpens boundaries.
            nonlinear_saturation = (
                saturation_strength
                * self.bio_density**2
            )

            # Organic-matrix evolution equation.
            growth_rate = (
                diffusion_coefficient
                * laplacian
                + retained_growth
                - nonlinear_saturation
            )

            self.bio_density += (
                dt
                * growth_rate
            )

            self.bio_density = np.clip(
                self.bio_density,
                0.0,
                1.0,
            )

        self.completed_steps += steps

        self._update_organic_appearance()

        return self.bio_density.copy()

    def _update_organic_appearance(self) -> None:
        """
        Update the organic appearance layer.

        The appearance index combines:
        - mean biological density,
        - active-volume fraction,
        - spatial density contrast,
        - retention of density inside the C3 field.
        """
        self.mean_bio_density = float(
            np.mean(self.bio_density)
        )

        self.active_density_fraction = float(
            np.mean(
                self.bio_density > 0.05
            )
        )

        self.branching_contrast = float(
            np.std(self.bio_density)
        )

        C3_normalization = float(
            np.sum(self.C3_field)
        )

        if C3_normalization > 0.0:
            toroidal_retention = float(
                np.sum(
                    self.bio_density
                    * self.C3_field
                )
                / C3_normalization
            )
        else:
            toroidal_retention = 0.0

        self.organic_appearance_index = float(
            self.mean_bio_density
            * (
                1.0
                + self.active_density_fraction
            )
            * (
                1.0
                + self.branching_contrast
            )
            * (
                1.0
                + toroidal_retention
            )
        )

    def calculate_organic_appearance(
        self,
    ) -> dict[str, float | int | str]:
        """
        Return the current organic appearance state.

        Returns
        -------
        dict[str, float | int | str]:
            Organic appearance index and current structural measurements.
        """
        if self.organic_appearance_index >= 0.50:
            manifestation_regime = (
                "STABLE ORGANIC MATRIX MANIFESTATION"
            )
        elif self.organic_appearance_index >= 0.10:
            manifestation_regime = (
                "PARTIAL ORGANIC MATRIX MANIFESTATION"
            )
        else:
            manifestation_regime = (
                "WEAK OR EMERGING ORGANIC MATRIX MANIFESTATION"
            )

        return {
            "organic_appearance_index": float(
                self.organic_appearance_index
            ),
            "manifestation_regime": manifestation_regime,
            "mean_bio_density": float(
                self.mean_bio_density
            ),
            "active_density_fraction": float(
                self.active_density_fraction
            ),
            "branching_contrast": float(
                self.branching_contrast
            ),
            "completed_steps": int(
                self.completed_steps
            ),
        }

    def visualize_organic_slice(self) -> None:
        """
        Visualize horizontal and vertical slices of the organic matrix.
        """
        mid_z = self.grid_size // 2
        mid_y = self.grid_size // 2

        fig, axes = plt.subplots(
            1,
            2,
            figsize=(12, 5),
        )

        ax_xy, ax_xz = axes

        fig.suptitle(
            "Marnov Protocol — Organic Matrix Manifestation",
            fontsize=13,
            fontweight="bold",
        )

        # Horizontal XY slice.
        image_xy = ax_xy.imshow(
            self.bio_density[:, :, mid_z],
            cmap="YlGnBu",
            origin="lower",
            interpolation="nearest",
        )

        ax_xy.set_title(
            "XY Organic-Matrix Slice"
        )
        ax_xy.set_xlabel(
            "X Projection"
        )
        ax_xy.set_ylabel(
            "Y Projection"
        )

        fig.colorbar(
            image_xy,
            ax=ax_xy,
            label="Organic Tissue Density",
        )

        # Vertical XZ slice.
        image_xz = ax_xz.imshow(
            self.bio_density[mid_y, :, :],
            cmap="YlGnBu",
            origin="lower",
            interpolation="nearest",
        )

        ax_xz.set_title(
            "XZ Organic-Matrix Slice"
        )
        ax_xz.set_xlabel(
            "Z Projection"
        )
        ax_xz.set_ylabel(
            "X Projection"
        )

        fig.colorbar(
            image_xz,
            ax=ax_xz,
            label="Organic Tissue Density",
        )

        plt.tight_layout(
            rect=(0.0, 0.0, 1.0, 0.94)
        )
        plt.show()


if __name__ == "__main__":
    generator = MarnovOrganicMatrixGenerator(
        grid_size=64,
        dx=0.05,
    )

    print(
        "1. Activating the asymmetric toroidal "
        "cubic-retention field C3..."
    )

    C3_field = generator.generate_asymmetric_c3_field(
        epsilon=0.236068,
    )

    print(
        "2. Starting the recursive organic-matrix "
        "growth cascade for 15 tacts..."
    )

    generator.grow_organic_matrix(
        C3=C3_field,
        steps=15,
    )

    appearance_state = (
        generator.calculate_organic_appearance()
    )

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
        "6. Displaying horizontal and vertical "
        "organic-matrix slices..."
    )

    generator.visualize_organic_slice()
