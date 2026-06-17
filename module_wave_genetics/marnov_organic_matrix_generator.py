import numpy as np
import matplotlib.pyplot as plt


class MarnovOrganicMatrixGenerator:
    def __init__(self, grid_size=64, dx=0.05):
        self.grid_size = grid_size
        self.dx = dx
        self.shape = (grid_size, grid_size, grid_size)

        # Initialize the density matrix of organic matter: the bio-matrix.
        self.bio_density = np.zeros(self.shape)

        # Initial point of initiation: ancestor cell or wave focus at the center.
        self.bio_density[
            grid_size // 2,
            grid_size // 2,
            grid_size // 2
        ] = 1.0

    def generate_asymmetric_c3_field(self, epsilon=0.236068):
        """
        Generate the 6D cubic phase lock C^3 with Golden Ratio irrationality.

        epsilon = 0.236068 is derived from the Golden Ratio
        and introduces living asymmetry into the field.
        """
        x, y, z = np.indices(self.shape)

        cx = self.grid_size // 2
        cy = self.grid_size // 2
        cz = self.grid_size // 2

        # Build the base toroidal field.
        r_tor = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        d_tor = np.sqrt((r_tor - self.grid_size // 5) ** 2 + (z - cz) ** 2)

        # Introduce irrational angular asymmetry.
        theta = np.arctan2(y - cy, x - cx)
        asymmetry_factor = 1.0 + epsilon * np.sin(3.0 * theta + z * 0.1)

        # Resulting cubic phase lock of volumetric retention.
        c3_field = asymmetry_factor * np.exp(-(d_tor ** 2) / (2.0 * 3.0 ** 2))

        return c3_field

    def grow_organic_matrix(self, c3_field, steps=10):
        """
        Perform recursive tact-by-tact growth of the bio-structure.

        Each step includes nonlinear diffusion and irrational pressure
        introduced by the asymmetric C^3 field.
        """
        dt = 0.1
        diffusion_coefficient = 0.15

        for _ in range(steps):
            # Compute the spatial Laplacian of bio-density using central differences.
            laplacian = np.zeros_like(self.bio_density)

            # Standard 3D diffusion stencil.
            for axis in range(3):
                laplacian += (
                    np.roll(self.bio_density, 1, axis=axis)
                    + np.roll(self.bio_density, -1, axis=axis)
                    - 2.0 * self.bio_density
                ) / (self.dx ** 2)

            # EDS equation of the living matrix:
            # growth = diffusion + retention through C^3 - nonlinear saturation.
            # The nonlinear term limits excessive growth and forms membranes or boundaries.
            growth_rate = (
                diffusion_coefficient * laplacian
                + 2.0 * c3_field * (1.0 - self.bio_density)
            )

            self.bio_density += dt * growth_rate

            # Recursive fractal budding shift:
            # at each step, C^3 asymmetry forms fractal channels inside the bio-mass.
            self.bio_density = np.clip(self.bio_density, 0.0, 1.0)

    def visualize_organic_slice(self, output_file="marnov_organic_matrix_slices.png"):
        """
        Visualize and save the generated living matrix through 2D observational slices.

        The saved image is mandatory because repository execution,
        mobile execution or headless environments may not display plt.show().
        """
        mid_z = self.grid_size // 2
        mid_y = self.grid_size // 2

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        fig.suptitle(
            "Marnov Protocol — Manifestation of the Organic Matrix (3D)",
            fontsize=13,
            fontweight="bold"
        )

        # Horizontal XY slice.
        im1 = ax1.imshow(
            self.bio_density[:, :, mid_z],
            cmap="YlGnBu",
            origin="lower"
        )
        ax1.set_title("Bio-Matrix XY Slice")
        ax1.set_xlabel("X Projection")
        ax1.set_ylabel("Y Projection")
        fig.colorbar(im1, ax=ax1, label="Organic Tissue Density")

        # Vertical XZ slice.
        im2 = ax2.imshow(
            self.bio_density[mid_y, :, :],
            cmap="YlGnBu",
            origin="lower"
        )
        ax2.set_title("Bio-Matrix XZ Slice")
        ax2.set_xlabel("Z Projection")
        ax2.set_ylabel("X Projection")
        fig.colorbar(im2, ax=ax2, label="Organic Tissue Density")

        plt.tight_layout()

        # Mandatory file output.
        plt.savefig(output_file, dpi=300, bbox_inches="tight")

        # Optional interactive display when the environment supports it.
        plt.show()


if __name__ == "__main__":
    generator = MarnovOrganicMatrixGenerator(grid_size=64)

    print("1. Activating the 6D phase lock with Golden Ratio irrationality...")
    c3_field = generator.generate_asymmetric_c3_field()

    print("2. Running the recursive growth cascade of the organic matrix for 15 tacts...")
    generator.grow_organic_matrix(c3_field, steps=15)

    print("3. Saving and displaying the fractal observational slices of the living system...")
    generator.visualize_organic_slice(
        output_file="marnov_organic_matrix_slices.png"
    )

