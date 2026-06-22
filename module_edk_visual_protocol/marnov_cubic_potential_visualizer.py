import numpy as np
import matplotlib.pyplot as plt


class MarnovCubicPotentialVisualizer:
    """
    Engineering visual simulator for the Marnov phase-lock protocol.

    The module models:

    - three orthogonal two-dimensional phase planes;
    - their tensor-product contraction into an 8x8 multiplet operator U_6D;
    - tact-by-tact suppression of phase mismatch;
    - normalized phase-lock amplitude;
    - cubic retention potential C3;
    - transition through an interface-density barrier;
    - the EDS retention criterion C3 > P;
    - the bifurcation boundary C3 = P.

    The name U_6D refers to a multiplet assembled from three orthogonal
    two-dimensional phase planes. The numerical state itself is represented
    by an 8x8 tensor-product operator, not by six spatial coordinates.
    """

    def __init__(
        self,
        alpha_lock: float = 1.2,
        base_support: float = 1.0,
        epsilon: float = 0.15,
        dt: float = 0.05,
        num_steps: int = 50,
        gamma: float = 0.4,
        noise_strength: float = 0.03,
        psi_amplitude: float = 1.5,
        dissipation_coefficient: float = 0.5,
        seed: int | None = 42,
    ):
        """
        Initialize the engineering visual simulator.

        Parameters
        ----------
        alpha_lock:
            Base phase-lock coupling coefficient.
        base_support:
            Initial coherence-support parameter R(n).
        epsilon:
            Micro-asymmetry angle of the pair-lock matrix.
        dt:
            Discrete tact duration.
        num_steps:
            Number of tact-by-tact stabilization steps.
        gamma:
            Nonlinear restoring-force coefficient.
        noise_strength:
            Standard intensity of external dissipative phase noise.
        psi_amplitude:
            Scalar field amplitude used in the cubic-potential calculation.
        dissipation_coefficient:
            Coefficient of the environmental dissipation level P.
        seed:
            Optional random seed for reproducible simulations.
        """
        if alpha_lock < 0.0:
            raise ValueError("alpha_lock must be non-negative.")
        if base_support < 0.0:
            raise ValueError("base_support must be non-negative.")
        if dt <= 0.0:
            raise ValueError("dt must be positive.")
        if num_steps <= 0:
            raise ValueError("num_steps must be positive.")
        if gamma < 0.0:
            raise ValueError("gamma must be non-negative.")
        if noise_strength < 0.0:
            raise ValueError("noise_strength must be non-negative.")
        if psi_amplitude <= 0.0:
            raise ValueError("psi_amplitude must be positive.")
        if dissipation_coefficient < 0.0:
            raise ValueError(
                "dissipation_coefficient must be non-negative."
            )

        self.alpha_lock = alpha_lock
        self.base_support = base_support
        self.epsilon = epsilon
        self.dt = dt
        self.num_steps = num_steps
        self.gamma = gamma
        self.noise_strength = noise_strength
        self.psi_amplitude = psi_amplitude
        self.dissipation_coefficient = dissipation_coefficient

        self.rng = np.random.default_rng(seed)

        self.history_steps = np.empty(0, dtype=np.int64)
        self.history_phi = np.empty((0, 3), dtype=np.float64)
        self.history_lock_amplitude = np.empty(0, dtype=np.float64)
        self.history_c3 = np.empty(0, dtype=np.float64)

        self.x_coordinates = np.empty(0, dtype=np.float64)
        self.support_profile = np.empty(0, dtype=np.float64)
        self.interface_c3 = np.empty(0, dtype=np.float64)
        self.interface_dissipation = np.empty(0, dtype=np.float64)
        self.bifurcation_points = np.empty(0, dtype=np.float64)

    def build_pair_lock(
        self,
        delta_phi: float,
        kappa: float,
        support: float = 1.0,
    ) -> np.ndarray:
        """
        Build one phase lock on a two-dimensional phase plane.

        The operator contains:

        - opposite phase propagation in the two counter-directed channels;
        - an asymmetric rotation matrix;
        - a coherence-support amplitude.

        Parameters
        ----------
        delta_phi:
            Phase difference between counter-directed wave channels.
        kappa:
            Local nonlinear phase-lock strength.
        support:
            Local coherence-support parameter R(n).

        Returns
        -------
        np.ndarray:
            Complex 2x2 pair-lock operator.
        """
        if support < 0.0:
            raise ValueError("support must be non-negative.")

        phase_angle = kappa * np.sin(delta_phi)

        phase_operator = np.array(
            [
                [np.exp(1j * phase_angle), 0.0],
                [0.0, np.exp(-1j * phase_angle)],
            ],
            dtype=np.complex128,
        )

        asymmetry_operator = np.array(
            [
                [
                    np.cos(self.epsilon),
                    np.sin(self.epsilon),
                ],
                [
                    -np.sin(self.epsilon),
                    np.cos(self.epsilon),
                ],
            ],
            dtype=np.complex128,
        )

        support_amplitude = np.sqrt(support)

        return support_amplitude * (
            phase_operator @ asymmetry_operator
        )

    def calculate_u_6d(
        self,
        delta_phi: np.ndarray,
        kappa: float,
        support: float = 1.0,
    ) -> np.ndarray:
        """
        Contract three orthogonal two-dimensional phase locks into U_6D.

        The tensor product of three 2x2 pair-lock operators produces
        one complex 8x8 multiplet operator.

        Parameters
        ----------
        delta_phi:
            Three phase differences for the X, Y, and Z phase planes.
        kappa:
            Local nonlinear phase-lock strength.
        support:
            Local coherence-support parameter R(n).

        Returns
        -------
        np.ndarray:
            Complex 8x8 tensor-product operator U_6D.
        """
        delta_phi = np.asarray(
            delta_phi,
            dtype=np.float64,
        )

        if delta_phi.shape != (3,):
            raise ValueError(
                "delta_phi must contain exactly three phase differences."
            )

        lock_x = self.build_pair_lock(
            delta_phi=delta_phi[0],
            kappa=kappa,
            support=support,
        )

        lock_y = self.build_pair_lock(
            delta_phi=delta_phi[1],
            kappa=kappa,
            support=support,
        )

        lock_z = self.build_pair_lock(
            delta_phi=delta_phi[2],
            kappa=kappa,
            support=support,
        )

        return np.kron(
            np.kron(
                lock_x,
                lock_y,
            ),
            lock_z,
        )

    @staticmethod
    def calculate_lock_amplitude(
        multiplet_operator: np.ndarray,
    ) -> float:
        """
        Calculate the normalized phase-lock amplitude.

        The raw trace is normalized by the operator dimension so that
        the resulting amplitude can be compared across simulation stages.

        Parameters
        ----------
        multiplet_operator:
            Complex square multiplet operator.

        Returns
        -------
        float:
            Normalized lock amplitude.
        """
        multiplet_operator = np.asarray(
            multiplet_operator,
            dtype=np.complex128,
        )

        if multiplet_operator.ndim != 2:
            raise ValueError(
                "multiplet_operator must be a two-dimensional matrix."
            )

        rows, columns = multiplet_operator.shape

        if rows != columns:
            raise ValueError(
                "multiplet_operator must be square."
            )

        return float(
            np.abs(
                np.trace(multiplet_operator)
            )
            / rows
        )

    def calculate_cubic_potential(
        self,
        lock_amplitude: float,
    ) -> float:
        """
        Calculate the cubic retention potential C3.

        C3 is defined as the cubic saturation of the normalized
        phase-lock amplitude, scaled by the field intensity.

        Parameters
        ----------
        lock_amplitude:
            Normalized phase-lock amplitude.

        Returns
        -------
        float:
            Cubic retention potential C3.
        """
        lock_amplitude = max(
            float(lock_amplitude),
            0.0,
        )

        return float(
            self.psi_amplitude**2
            * lock_amplitude**3
        )

    def calculate_dissipation_level(self) -> float:
        """
        Calculate the environmental dissipation level P.

        Returns
        -------
        float:
            Dissipation level P.
        """
        return float(
            self.dissipation_coefficient
            * self.psi_amplitude**3
        )

    def simulate_temporal_dynamics(
        self,
        initial_phi: np.ndarray | None = None,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """
        Simulate tact-by-tact phase stabilization.

        The phase state evolves through:

        - nonlinear sinusoidal restoring force;
        - external dissipative noise;
        - recursive inheritance of the preceding phase state.

        The noise increment is scaled by sqrt(dt), preventing the stochastic
        forcing from changing incorrectly when the tact duration changes.

        Parameters
        ----------
        initial_phi:
            Initial phase differences on the three phase planes.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
            Tact indices, phase history, lock-amplitude history,
            and cubic-potential history.
        """
        if initial_phi is None:
            current_phi = np.array(
                [0.8, -0.7, 0.5],
                dtype=np.float64,
            )
        else:
            current_phi = np.asarray(
                initial_phi,
                dtype=np.float64,
            ).copy()

        if current_phi.shape != (3,):
            raise ValueError(
                "initial_phi must contain exactly three phase differences."
            )

        history_steps: list[int] = []
        history_phi: list[np.ndarray] = []
        history_lock_amplitude: list[float] = []
        history_c3: list[float] = []

        kappa = (
            self.alpha_lock
            * self.base_support
        )

        for step in range(self.num_steps):
            multiplet_operator = self.calculate_u_6d(
                delta_phi=current_phi,
                kappa=kappa,
                support=self.base_support,
            )

            lock_amplitude = self.calculate_lock_amplitude(
                multiplet_operator
            )

            cubic_potential = self.calculate_cubic_potential(
                lock_amplitude
            )

            history_steps.append(step)
            history_phi.append(current_phi.copy())
            history_lock_amplitude.append(lock_amplitude)
            history_c3.append(cubic_potential)

            restoring_increment = (
                -self.gamma
                * np.sin(current_phi)
                * self.dt
            )

            noise_increment = self.rng.normal(
                loc=0.0,
                scale=(
                    self.noise_strength
                    * np.sqrt(self.dt)
                ),
                size=3,
            )

            current_phi += (
                restoring_increment
                + noise_increment
            )

            current_phi = (
                current_phi
                + np.pi
            ) % (
                2.0 * np.pi
            ) - np.pi

        self.history_steps = np.asarray(
            history_steps,
            dtype=np.int64,
        )

        self.history_phi = np.asarray(
            history_phi,
            dtype=np.float64,
        )

        self.history_lock_amplitude = np.asarray(
            history_lock_amplitude,
            dtype=np.float64,
        )

        self.history_c3 = np.asarray(
            history_c3,
            dtype=np.float64,
        )

        return (
            self.history_steps.copy(),
            self.history_phi.copy(),
            self.history_lock_amplitude.copy(),
            self.history_c3.copy(),
        )

    def calculate_interface_profile(
        self,
        x_start: float = 0.0,
        x_end: float = 10.0,
        num_points: int = 200,
        barrier_center: float = 5.0,
        barrier_width: float = 1.5,
        barrier_depth: float = 0.8,
        fixed_phi: np.ndarray | None = None,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """
        Calculate the phase-lock stability profile across an interface barrier.

        The coherence-support profile R(n) decreases inside the barrier
        and recovers outside it.

        The local lock strength is:

        kappa_local = alpha_lock * R(n)

        The cubic potential is:

        C3 = psi_amplitude^2 * lock_amplitude^3

        The EDS retention condition is:

        C3 > P

        The critical boundary is:

        C3 = P

        Parameters
        ----------
        x_start:
            Initial spatial coordinate.
        x_end:
            Final spatial coordinate.
        num_points:
            Number of spatial sampling points.
        barrier_center:
            Center coordinate of the interface barrier.
        barrier_width:
            Gaussian width of the barrier.
        barrier_depth:
            Maximum decrease of the coherence-support profile.
        fixed_phi:
            Phase differences used for the spatial interface calculation.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
            Spatial coordinates, support profile, C3 profile,
            and dissipation profile.
        """
        if x_end <= x_start:
            raise ValueError(
                "x_end must be greater than x_start."
            )
        if num_points < 2:
            raise ValueError(
                "num_points must be at least 2."
            )
        if barrier_width <= 0.0:
            raise ValueError(
                "barrier_width must be positive."
            )
        if not 0.0 <= barrier_depth < 1.0:
            raise ValueError(
                "barrier_depth must be in the interval [0, 1)."
            )

        if fixed_phi is None:
            fixed_phase_state = np.array(
                [0.1, -0.1, 0.05],
                dtype=np.float64,
            )
        else:
            fixed_phase_state = np.asarray(
                fixed_phi,
                dtype=np.float64,
            )

        if fixed_phase_state.shape != (3,):
            raise ValueError(
                "fixed_phi must contain exactly three phase differences."
            )

        x_coordinates = np.linspace(
            x_start,
            x_end,
            num_points,
        )

        support_profile = (
            self.base_support
            - barrier_depth
            * np.exp(
                -(
                    (
                        x_coordinates
                        - barrier_center
                    )
                    / barrier_width
                ) ** 2
            )
        )

        support_profile = np.clip(
            support_profile,
            0.0,
            None,
        )

        cubic_potential_values: list[float] = []

        dissipation_level = (
            self.calculate_dissipation_level()
        )

        for local_support in support_profile:
            local_kappa = (
                self.alpha_lock
                * local_support
            )

            local_operator = self.calculate_u_6d(
                delta_phi=fixed_phase_state,
                kappa=local_kappa,
                support=local_support,
            )

            local_lock_amplitude = (
                self.calculate_lock_amplitude(
                    local_operator
                )
            )

            local_cubic_potential = (
                self.calculate_cubic_potential(
                    local_lock_amplitude
                )
            )

            cubic_potential_values.append(
                local_cubic_potential
            )

        cubic_potential_profile = np.asarray(
            cubic_potential_values,
            dtype=np.float64,
        )

        dissipation_profile = np.full_like(
            cubic_potential_profile,
            fill_value=dissipation_level,
            dtype=np.float64,
        )

        self.x_coordinates = x_coordinates
        self.support_profile = support_profile
        self.interface_c3 = cubic_potential_profile
        self.interface_dissipation = dissipation_profile

        self.bifurcation_points = (
            self._find_bifurcation_points(
                x_coordinates=x_coordinates,
                cubic_potential=cubic_potential_profile,
                dissipation=dissipation_profile,
            )
        )

        return (
            self.x_coordinates.copy(),
            self.support_profile.copy(),
            self.interface_c3.copy(),
            self.interface_dissipation.copy(),
        )

    @staticmethod
    def _find_bifurcation_points(
        x_coordinates: np.ndarray,
        cubic_potential: np.ndarray,
        dissipation: np.ndarray,
    ) -> np.ndarray:
        """
        Find approximate coordinates where C3 crosses P.

        Linear interpolation is used between neighboring samples.

        Parameters
        ----------
        x_coordinates:
            Spatial coordinates.
        cubic_potential:
            Cubic-retention potential profile.
        dissipation:
            Dissipation profile.

        Returns
        -------
        np.ndarray:
            Approximate bifurcation coordinates.
        """
        difference = (
            cubic_potential
            - dissipation
        )

        crossing_indices = np.where(
            np.signbit(difference[:-1])
            != np.signbit(difference[1:])
        )[0]

        crossing_points: list[float] = []

        for index in crossing_indices:
            x_left = x_coordinates[index]
            x_right = x_coordinates[index + 1]

            y_left = difference[index]
            y_right = difference[index + 1]

            denominator = (
                y_right
                - y_left
            )

            if denominator == 0.0:
                crossing_coordinate = x_left
            else:
                crossing_coordinate = (
                    x_left
                    - y_left
                    * (
                        x_right
                        - x_left
                    )
                    / denominator
                )

            crossing_points.append(
                float(crossing_coordinate)
            )

        return np.asarray(
            crossing_points,
            dtype=np.float64,
        )

    def visualize_engineering_data(self) -> None:
        """
        Visualize temporal phase dynamics, phase-space trajectory,
        cubic-potential dynamics, and the interface stability map.
        """
        if self.history_steps.size == 0:
            raise RuntimeError(
                "Temporal dynamics have not been simulated."
            )

        if self.x_coordinates.size == 0:
            raise RuntimeError(
                "The interface profile has not been calculated."
            )

        figure = plt.figure(
            figsize=(16, 11),
        )

        figure.suptitle(
            "Marnov Protocol Engineering Simulator — U_6D / C3 Core",
            fontsize=14,
            fontweight="bold",
        )

        phase_axis = figure.add_subplot(
            2,
            2,
            1,
        )

        phase_space_axis = figure.add_subplot(
            2,
            2,
            2,
            projection="3d",
        )

        lock_axis = figure.add_subplot(
            2,
            2,
            3,
        )

        interface_axis = figure.add_subplot(
            2,
            2,
            4,
        )

        phase_axis.plot(
            self.history_steps,
            self.history_phi[:, 0],
            label="X axis: delta_phi_1",
            linewidth=2.0,
        )

        phase_axis.plot(
            self.history_steps,
            self.history_phi[:, 1],
            label="Y axis: delta_phi_2",
            linewidth=2.0,
        )

        phase_axis.plot(
            self.history_steps,
            self.history_phi[:, 2],
            label="Z axis: delta_phi_3",
            linewidth=2.0,
        )

        phase_axis.axhline(
            0.0,
            linestyle="--",
            alpha=0.5,
        )

        phase_axis.set_title(
            "Tact-by-Tact Suppression of Phase Mismatch"
        )

        phase_axis.set_xlabel(
            "Self-Assembly Tact"
        )

        phase_axis.set_ylabel(
            "Counter-Wave Phase Difference"
        )

        phase_axis.grid(
            True,
            alpha=0.3,
        )

        phase_axis.legend()

        phase_space_axis.plot(
            self.history_phi[:, 0],
            self.history_phi[:, 1],
            self.history_phi[:, 2],
            linewidth=2.0,
        )

        phase_space_axis.scatter(
            self.history_phi[0, 0],
            self.history_phi[0, 1],
            self.history_phi[0, 2],
            marker="o",
            s=45,
            label="Initial state",
        )

        phase_space_axis.scatter(
            self.history_phi[-1, 0],
            self.history_phi[-1, 1],
            self.history_phi[-1, 2],
            marker="x",
            s=60,
            label="Final state",
        )

        phase_space_axis.set_title(
            "Three-Plane Phase-Space Trajectory"
        )

        phase_space_axis.set_xlabel(
            "delta_phi_1"
        )

        phase_space_axis.set_ylabel(
            "delta_phi_2"
        )

        phase_space_axis.set_zlabel(
            "delta_phi_3"
        )

        phase_space_axis.legend()

        lock_axis.plot(
            self.history_steps,
            self.history_lock_amplitude,
            linewidth=2.5,
            label="Normalized lock amplitude",
        )

        lock_axis.set_title(
            "U_6D Phase-Lock Amplitude"
        )

        lock_axis.set_xlabel(
            "Self-Assembly Tact"
        )

        lock_axis.set_ylabel(
            "Normalized abs(Tr(U_6D))"
        )

        lock_axis.grid(
            True,
            alpha=0.3,
        )

        cubic_axis = lock_axis.twinx()

        cubic_axis.plot(
            self.history_steps,
            self.history_c3,
            linestyle="--",
            linewidth=2.0,
            label="C3 potential",
        )

        cubic_axis.set_ylabel(
            "Cubic Retention Potential C3"
        )

        lock_lines, lock_labels = (
            lock_axis.get_legend_handles_labels()
        )

        cubic_lines, cubic_labels = (
            cubic_axis.get_legend_handles_labels()
        )

        lock_axis.legend(
            lock_lines + cubic_lines,
            lock_labels + cubic_labels,
            loc="best",
        )

        interface_axis.plot(
            self.x_coordinates,
            self.interface_c3,
            linewidth=2.5,
            label="C3 cubic retention potential",
        )

        interface_axis.plot(
            self.x_coordinates,
            self.interface_dissipation,
            linestyle="--",
            linewidth=2.0,
            label="Environmental dissipation P",
        )

        interface_axis.fill_between(
            self.x_coordinates,
            self.interface_c3,
            self.interface_dissipation,
            where=(
                self.interface_c3
                < self.interface_dissipation
            ),
            alpha=0.2,
            label="Breakdown domain: C3 <= P",
        )

        interface_axis.fill_between(
            self.x_coordinates,
            self.interface_c3,
            self.interface_dissipation,
            where=(
                self.interface_c3
                >= self.interface_dissipation
            ),
            alpha=0.2,
            label="Retention domain: C3 > P",
        )

        for point in self.bifurcation_points:
            interface_axis.axvline(
                point,
                linestyle=":",
                alpha=0.8,
            )

        interface_axis.set_title(
            "EDS Criterion Across the Interface Barrier"
        )

        interface_axis.set_xlabel(
            "Spatial Transition Coordinate X"
        )

        interface_axis.set_ylabel(
            "Retention Potential / Dissipation"
        )

        interface_axis.grid(
            True,
            alpha=0.3,
        )

        interface_axis.legend()

        plt.tight_layout(
            rect=(
                0.0,
                0.0,
                1.0,
                0.96,
            )
        )

        plt.show()

    def run_visual_simulation(self) -> None:
        """
        Run the complete temporal and spatial engineering simulation.
        """
        self.simulate_temporal_dynamics(
            initial_phi=np.array(
                [0.8, -0.7, 0.5],
                dtype=np.float64,
            )
        )

        self.calculate_interface_profile(
            x_start=0.0,
            x_end=10.0,
            num_points=200,
            barrier_center=5.0,
            barrier_width=1.5,
            barrier_depth=0.8,
            fixed_phi=np.array(
                [0.1, -0.1, 0.05],
                dtype=np.float64,
            ),
        )

        print(
            "=== MARNOV U_6D / C3 ENGINEERING SIMULATOR ==="
        )

        print(
            "Initial lock amplitude: "
            f"{self.history_lock_amplitude[0]:.6f}"
        )

        print(
            "Final lock amplitude: "
            f"{self.history_lock_amplitude[-1]:.6f}"
        )

        print(
            "Initial cubic potential C3: "
            f"{self.history_c3[0]:.6f}"
        )

        print(
            "Final cubic potential C3: "
            f"{self.history_c3[-1]:.6f}"
        )

        print(
            "Environmental dissipation P: "
            f"{self.calculate_dissipation_level():.6f}"
        )

        if self.bifurcation_points.size > 0:
            formatted_points = ", ".join(
                f"{point:.4f}"
                for point in self.bifurcation_points
            )

            print(
                "Bifurcation coordinates C3 = P: "
                f"{formatted_points}"
            )
        else:
            print(
                "No C3 = P bifurcation crossing was detected."
            )

        self.visualize_engineering_data()


if __name__ == "__main__":
    simulator = MarnovCubicPotentialVisualizer(
        alpha_lock=1.2,
        base_support=1.0,
        epsilon=0.15,
        dt=0.05,
        num_steps=50,
        gamma=0.4,
        noise_strength=0.03,
        psi_amplitude=1.5,
        dissipation_coefficient=0.5,
        seed=42,
    )

    simulator.run_visual_simulation()
