import numpy as np
import matplotlib.pyplot as plt

from module_edk_visual_protocol.marnov_cubic_potential_visualizer import (
    MarnovCubicPotentialVisualizer,
)


class MarnovPoyntingFluxTransition(MarnovCubicPotentialVisualizer):
    """
    Engineering simulator of the transition from internal U_6D / C3
    retention to a directed axial output-flux state.

    The module extends the U_6D / C3 visual protocol with:

    - a normalized phase-opening gradient G_phi;
    - a controlled opening function g_open;
    - a reduced directed output-flux density S_1D;
    - an axial output vector S_model;
    - a retained-energy balance;
    - an optional physical Poynting-vector calculation E cross H;
    - controlled phase and eccentricity displacement;
    - tact-by-tact restoration of the retained contour.

    The reduced quantity S_1D is an EDK output-flux proxy.

    It must not be interpreted as the physical electromagnetic Poynting
    vector unless electric and magnetic fields are explicitly defined
    and the relation S = E cross H is calculated.
    """

    def __init__(
        self,
        alpha_lock: float = 1.2,
        base_support: float = 1.0,
        equilibrium_epsilon: float = 0.15,
        dt: float = 0.05,
        num_steps: int = 60,
        gamma: float = 0.4,
        noise_strength: float = 0.02,
        psi_amplitude: float = 1.5,
        dissipation_coefficient: float = 0.5,
        phase_opening_sensitivity: float = 1.0,
        epsilon_opening_sensitivity: float = 1.0,
        release_efficiency: float = 0.5,
        eccentricity_restoring_rate: float = 0.6,
        output_area: float = 1.0,
        input_power: float | None = None,
        seed: int | None = 42,
    ):
        """
        Initialize the directed-output transition simulator.

        Parameters
        ----------
        alpha_lock:
            Base phase-lock coupling coefficient.
        base_support:
            Coherence-support parameter R(n).
        equilibrium_epsilon:
            Equilibrium micro-asymmetry or eccentricity parameter.
        dt:
            Discrete tact duration.
        num_steps:
            Number of simulation tacts.
        gamma:
            Nonlinear phase-restoring coefficient.
        noise_strength:
            Standard intensity of external dissipative phase noise.
        psi_amplitude:
            Retained-state amplitude used in the C3 calculation.
        dissipation_coefficient:
            Coefficient of environmental dissipation P.
        phase_opening_sensitivity:
            Sensitivity of the output opening to phase mismatch.
        epsilon_opening_sensitivity:
            Sensitivity of the output opening to eccentricity displacement.
        release_efficiency:
            Conversion coefficient from retained C3 into directed output.
        eccentricity_restoring_rate:
            Rate at which epsilon returns to its equilibrium value.
        output_area:
            Effective output area used in the retained-energy balance.
        input_power:
            External input power. If omitted, it is set equal to the
            environmental dissipation level.
        seed:
            Optional random seed for reproducible simulations.
        """
        if phase_opening_sensitivity < 0.0:
            raise ValueError(
                "phase_opening_sensitivity must be non-negative."
            )
        if epsilon_opening_sensitivity < 0.0:
            raise ValueError(
                "epsilon_opening_sensitivity must be non-negative."
            )
        if release_efficiency < 0.0:
            raise ValueError(
                "release_efficiency must be non-negative."
            )
        if eccentricity_restoring_rate < 0.0:
            raise ValueError(
                "eccentricity_restoring_rate must be non-negative."
            )
        if output_area <= 0.0:
            raise ValueError("output_area must be positive.")

        super().__init__(
            alpha_lock=alpha_lock,
            base_support=base_support,
            epsilon=equilibrium_epsilon,
            dt=dt,
            num_steps=num_steps,
            gamma=gamma,
            noise_strength=noise_strength,
            psi_amplitude=psi_amplitude,
            dissipation_coefficient=dissipation_coefficient,
            seed=seed,
        )

        self.equilibrium_epsilon = float(equilibrium_epsilon)
        self.current_epsilon = float(equilibrium_epsilon)

        self.phase_opening_sensitivity = float(
            phase_opening_sensitivity
        )
        self.epsilon_opening_sensitivity = float(
            epsilon_opening_sensitivity
        )
        self.release_efficiency = float(release_efficiency)
        self.eccentricity_restoring_rate = float(
            eccentricity_restoring_rate
        )
        self.output_area = float(output_area)

        if input_power is None:
            self.input_power = self.calculate_dissipation_level()
        else:
            if input_power < 0.0:
                raise ValueError(
                    "input_power must be non-negative."
                )
            self.input_power = float(input_power)

        self.output_axis = np.array(
            [0.0, 0.0, 1.0],
            dtype=np.float64,
        )

        self.control_step = 0

        self.history_opening_gradient = np.empty(
            0,
            dtype=np.float64,
        )
        self.history_opening_function = np.empty(
            0,
            dtype=np.float64,
        )
        self.history_output_flux = np.empty(
            0,
            dtype=np.float64,
        )
        self.history_output_vector = np.empty(
            (0, 3),
            dtype=np.float64,
        )
        self.history_retained_energy = np.empty(
            0,
            dtype=np.float64,
        )
        self.history_epsilon = np.empty(
            0,
            dtype=np.float64,
        )
        self.history_regime: list[str] = []

    @staticmethod
    def normalize_axis(axis: np.ndarray) -> np.ndarray:
        """
        Normalize an output-axis vector.

        Parameters
        ----------
        axis:
            Three-dimensional output-axis vector.

        Returns
        -------
        np.ndarray:
            Unit vector of the selected output axis.
        """
        axis = np.asarray(
            axis,
            dtype=np.float64,
        )

        if axis.shape != (3,):
            raise ValueError(
                "axis must contain exactly three components."
            )

        axis_norm = float(np.linalg.norm(axis))

        if axis_norm == 0.0:
            raise ValueError(
                "axis must not be the zero vector."
            )

        return axis / axis_norm

    @staticmethod
    def calculate_phase_opening_gradient(
        delta_phi: np.ndarray,
    ) -> float:
        """
        Calculate the normalized phase-opening gradient G_phi.

        G_phi =
        sqrt(
            sin(delta_phi_1)^2
            + sin(delta_phi_2)^2
            + sin(delta_phi_3)^2
        )
        / sqrt(3)

        Parameters
        ----------
        delta_phi:
            Three phase differences.

        Returns
        -------
        float:
            Normalized phase-opening gradient in the interval [0, 1].
        """
        delta_phi = np.asarray(
            delta_phi,
            dtype=np.float64,
        )

        if delta_phi.shape != (3,):
            raise ValueError(
                "delta_phi must contain exactly three phase differences."
            )

        gradient = (
            np.linalg.norm(np.sin(delta_phi))
            / np.sqrt(3.0)
        )

        return float(
            np.clip(
                gradient,
                0.0,
                1.0,
            )
        )

    def calculate_opening_function(
        self,
        delta_phi: np.ndarray,
        epsilon: float,
    ) -> tuple[float, float]:
        """
        Calculate the controlled opening function g_open.

        The opening combines:

        - the normalized phase-opening gradient;
        - displacement of epsilon from its retained equilibrium value.

        Parameters
        ----------
        delta_phi:
            Three phase differences.
        epsilon:
            Current eccentricity parameter.

        Returns
        -------
        tuple[float, float]:
            Phase-opening gradient G_phi and opening function g_open.
        """
        phase_gradient = self.calculate_phase_opening_gradient(
            delta_phi=delta_phi,
        )

        epsilon_displacement = abs(
            float(epsilon)
            - self.equilibrium_epsilon
        )

        opening_function = np.clip(
            self.phase_opening_sensitivity * phase_gradient
            + self.epsilon_opening_sensitivity
            * epsilon_displacement,
            0.0,
            1.0,
        )

        return (
            float(phase_gradient),
            float(opening_function),
        )

    def calculate_directed_output_flux(
        self,
        cubic_potential: float,
        opening_function: float,
    ) -> float:
        """
        Calculate the reduced directed output-flux density S_1D.

        S_1D =
        release_efficiency
        * C3
        * g_open

        Parameters
        ----------
        cubic_potential:
            Current cubic retention potential C3.
        opening_function:
            Current controlled opening value g_open.

        Returns
        -------
        float:
            Directed axial output-flux density.
        """
        if cubic_potential < 0.0:
            raise ValueError(
                "cubic_potential must be non-negative."
            )
        if not 0.0 <= opening_function <= 1.0:
            raise ValueError(
                "opening_function must be in the interval [0, 1]."
            )

        return float(
            self.release_efficiency
            * cubic_potential
            * opening_function
        )

    def calculate_output_vector(
        self,
        output_flux_density: float,
        axis: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Calculate the directed output vector S_model.

        S_model =
        S_1D
        * n_axis

        Parameters
        ----------
        output_flux_density:
            Directed scalar output-flux density S_1D.
        axis:
            Optional three-dimensional output axis.

        Returns
        -------
        np.ndarray:
            Three-dimensional directed output vector.
        """
        if output_flux_density < 0.0:
            raise ValueError(
                "output_flux_density must be non-negative."
            )

        if axis is None:
            normalized_axis = self.output_axis
        else:
            normalized_axis = self.normalize_axis(axis)

        return output_flux_density * normalized_axis

    @staticmethod
    def calculate_physical_poynting_vector(
        electric_field: np.ndarray,
        magnetic_field_h: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the physical electromagnetic Poynting vector.

        S_EM =
        E cross H

        Parameters
        ----------
        electric_field:
            Three-dimensional electric-field vector E.
        magnetic_field_h:
            Three-dimensional magnetic-field vector H.

        Returns
        -------
        np.ndarray:
            Physical electromagnetic Poynting vector.
        """
        electric_field = np.asarray(
            electric_field,
            dtype=np.float64,
        )

        magnetic_field_h = np.asarray(
            magnetic_field_h,
            dtype=np.float64,
        )

        if electric_field.shape != (3,):
            raise ValueError(
                "electric_field must contain exactly three components."
            )

        if magnetic_field_h.shape != (3,):
            raise ValueError(
                "magnetic_field_h must contain exactly three components."
            )

        return np.cross(
            electric_field,
            magnetic_field_h,
        )

    def calculate_axial_physical_flux(
        self,
        electric_field: np.ndarray,
        magnetic_field_h: np.ndarray,
        axis: np.ndarray | None = None,
    ) -> float:
        """
        Calculate the axial component of the physical Poynting vector.

        S_axis =
        (E cross H)
        dot n_axis

        Parameters
        ----------
        electric_field:
            Three-dimensional electric-field vector E.
        magnetic_field_h:
            Three-dimensional magnetic-field vector H.
        axis:
            Optional output-axis vector.

        Returns
        -------
        float:
            Signed axial electromagnetic energy-flux density.
        """
        physical_vector = self.calculate_physical_poynting_vector(
            electric_field=electric_field,
            magnetic_field_h=magnetic_field_h,
        )

        if axis is None:
            normalized_axis = self.output_axis
        else:
            normalized_axis = self.normalize_axis(axis)

        return float(
            np.dot(
                physical_vector,
                normalized_axis,
            )
        )

    @staticmethod
    def classify_operational_regime(
        cubic_potential: float,
        dissipation: float,
        opening_function: float,
    ) -> str:
        """
        Classify the current retention and output regime.

        Parameters
        ----------
        cubic_potential:
            Cubic retention potential C3.
        dissipation:
            Environmental dissipation P.
        opening_function:
            Controlled opening value g_open.

        Returns
        -------
        str:
            Current operational regime.
        """
        tolerance = 1e-9

        if cubic_potential < dissipation - tolerance:
            return "BREAKDOWN DOMAIN"

        if abs(
            cubic_potential
            - dissipation
        ) <= tolerance:
            return "CRITICAL BOUNDARY"

        if opening_function <= 0.05:
            return "CLOSED RETENTION"

        return "CONTROLLED DIRECTED RELEASE"

    def simulate_impulse_transition(
        self,
        initial_phi: np.ndarray | None = None,
        control_step: int = 30,
        phase_impulse: np.ndarray | None = None,
        epsilon_impulse: float = 0.08,
        output_axis: np.ndarray | None = None,
        initial_retained_energy: float | None = None,
    ) -> dict[str, np.ndarray | list[str]]:
        """
        Simulate the transition from internal retention to directed output.

        A controlled phase and eccentricity displacement is introduced
        at control_step.

        After the displacement:

        - phase mismatch increases;
        - the opening function increases;
        - the directed output flux increases;
        - the retained energy decreases;
        - nonlinear restoring dynamics close the contour again.

        Parameters
        ----------
        initial_phi:
            Initial phase-difference vector.
        control_step:
            Tact at which the controlled opening impulse is applied.
        phase_impulse:
            Three-component phase displacement.
        epsilon_impulse:
            Controlled displacement of the eccentricity parameter.
        output_axis:
            Direction of the output vector.
        initial_retained_energy:
            Initial retained-energy reservoir. If omitted, it is initialized
            from the first calculated cubic potential.

        Returns
        -------
        dict[str, np.ndarray | list[str]]:
            Complete temporal history of the transition.
        """
        if not 0 <= control_step < self.num_steps:
            raise ValueError(
                "control_step must be inside the simulated tact interval."
            )

        if initial_phi is None:
            current_phi = np.array(
                [0.5, -0.4, 0.3],
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

        if phase_impulse is None:
            control_phase_impulse = np.array(
                [0.8, 0.8, 0.8],
                dtype=np.float64,
            )
        else:
            control_phase_impulse = np.asarray(
                phase_impulse,
                dtype=np.float64,
            )

        if control_phase_impulse.shape != (3,):
            raise ValueError(
                "phase_impulse must contain exactly three components."
            )

        if output_axis is not None:
            self.output_axis = self.normalize_axis(
                output_axis
            )

        self.control_step = int(control_step)

        self.current_epsilon = float(
            self.equilibrium_epsilon
        )
        self.epsilon = self.current_epsilon

        history_steps: list[int] = []
        history_phi: list[np.ndarray] = []
        history_lock_amplitude: list[float] = []
        history_c3: list[float] = []
        history_opening_gradient: list[float] = []
        history_opening_function: list[float] = []
        history_output_flux: list[float] = []
        history_output_vector: list[np.ndarray] = []
        history_retained_energy: list[float] = []
        history_epsilon: list[float] = []
        history_regime: list[str] = []

        dissipation = self.calculate_dissipation_level()

        retained_energy: float | None = None

        if initial_retained_energy is not None:
            if initial_retained_energy < 0.0:
                raise ValueError(
                    "initial_retained_energy must be non-negative."
                )

            retained_energy = float(
                initial_retained_energy
            )

        kappa = (
            self.alpha_lock
            * self.base_support
        )

        print(
            "=== MARNOV DIRECTED OUTPUT-FLUX TRANSITION ==="
        )

        for step in range(self.num_steps):
            if step == self.control_step:
                print(
                    f"[TACT {step:02d}] "
                    "Controlled phase-opening impulse activated."
                )

                current_phi += control_phase_impulse
                self.current_epsilon += float(
                    epsilon_impulse
                )

            self.epsilon = self.current_epsilon

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

            if retained_energy is None:
                retained_energy = cubic_potential

            (
                opening_gradient,
                opening_function,
            ) = self.calculate_opening_function(
                delta_phi=current_phi,
                epsilon=self.current_epsilon,
            )

            output_flux_density = (
                self.calculate_directed_output_flux(
                    cubic_potential=cubic_potential,
                    opening_function=opening_function,
                )
            )

            output_vector = self.calculate_output_vector(
                output_flux_density=output_flux_density,
            )

            output_power = (
                self.output_area
                * output_flux_density
            )

            retained_energy_change = (
                self.input_power
                - dissipation
                - output_power
            ) * self.dt

            retained_energy = max(
                retained_energy
                + retained_energy_change,
                0.0,
            )

            regime = self.classify_operational_regime(
                cubic_potential=cubic_potential,
                dissipation=dissipation,
                opening_function=opening_function,
            )

            history_steps.append(step)
            history_phi.append(
                current_phi.copy()
            )
            history_lock_amplitude.append(
                lock_amplitude
            )
            history_c3.append(
                cubic_potential
            )
            history_opening_gradient.append(
                opening_gradient
            )
            history_opening_function.append(
                opening_function
            )
            history_output_flux.append(
                output_flux_density
            )
            history_output_vector.append(
                output_vector.copy()
            )
            history_retained_energy.append(
                retained_energy
            )
            history_epsilon.append(
                self.current_epsilon
            )
            history_regime.append(
                regime
            )

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

            epsilon_restoring_increment = (
                -self.eccentricity_restoring_rate
                * (
                    self.current_epsilon
                    - self.equilibrium_epsilon
                )
                * self.dt
            )

            self.current_epsilon += (
                epsilon_restoring_increment
            )

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
        self.history_opening_gradient = np.asarray(
            history_opening_gradient,
            dtype=np.float64,
        )
        self.history_opening_function = np.asarray(
            history_opening_function,
            dtype=np.float64,
        )
        self.history_output_flux = np.asarray(
            history_output_flux,
            dtype=np.float64,
        )
        self.history_output_vector = np.asarray(
            history_output_vector,
            dtype=np.float64,
        )
        self.history_retained_energy = np.asarray(
            history_retained_energy,
            dtype=np.float64,
        )
        self.history_epsilon = np.asarray(
            history_epsilon,
            dtype=np.float64,
        )
        self.history_regime = history_regime

        return {
            "steps": self.history_steps.copy(),
            "phase_history": self.history_phi.copy(),
            "lock_amplitude": self.history_lock_amplitude.copy(),
            "cubic_potential": self.history_c3.copy(),
            "opening_gradient": self.history_opening_gradient.copy(),
            "opening_function": self.history_opening_function.copy(),
            "output_flux": self.history_output_flux.copy(),
            "output_vector": self.history_output_vector.copy(),
            "retained_energy": self.history_retained_energy.copy(),
            "epsilon": self.history_epsilon.copy(),
            "regime": list(self.history_regime),
        }

    def visualize_transition(self) -> None:
        """
        Visualize phase dynamics, C3 retention, opening, output flux,
        and retained-energy redistribution.
        """
        if self.history_steps.size == 0:
            raise RuntimeError(
                "The impulse transition has not been simulated."
            )

        figure, axes = plt.subplots(
            2,
            2,
            figsize=(15, 10),
        )

        figure.suptitle(
            "Marnov Protocol: U_6D / C3 Retention "
            "to Directed Output Flux",
            fontsize=14,
            fontweight="bold",
        )

        phase_axis = axes[0, 0]
        potential_axis = axes[0, 1]
        opening_axis = axes[1, 0]
        output_axis = axes[1, 1]

        phase_axis.plot(
            self.history_steps,
            self.history_phi[:, 0],
            label="delta_phi_1",
        )
        phase_axis.plot(
            self.history_steps,
            self.history_phi[:, 1],
            label="delta_phi_2",
        )
        phase_axis.plot(
            self.history_steps,
            self.history_phi[:, 2],
            label="delta_phi_3",
        )
        phase_axis.axvline(
            self.control_step,
            linestyle=":",
            label="Control impulse",
        )
        phase_axis.axhline(
            0.0,
            linestyle="--",
            alpha=0.5,
        )
        phase_axis.set_title(
            "Tact-by-Tact Phase Dynamics"
        )
        phase_axis.set_xlabel(
            "Simulation Tact"
        )
        phase_axis.set_ylabel(
            "Phase Difference"
        )
        phase_axis.grid(
            True,
            alpha=0.3,
        )
        phase_axis.legend()

        potential_axis.plot(
            self.history_steps,
            self.history_c3,
            linewidth=2.5,
            label="C3 retention potential",
        )
        potential_axis.axhline(
            self.calculate_dissipation_level(),
            linestyle="--",
            label="Environmental dissipation P",
        )
        potential_axis.axvline(
            self.control_step,
            linestyle=":",
            label="Control impulse",
        )
        potential_axis.set_title(
            "Cubic Retention Potential"
        )
        potential_axis.set_xlabel(
            "Simulation Tact"
        )
        potential_axis.set_ylabel(
            "C3 / P"
        )
        potential_axis.grid(
            True,
            alpha=0.3,
        )
        potential_axis.legend()

        opening_axis.plot(
            self.history_steps,
            self.history_opening_gradient,
            label="G_phi",
        )
        opening_axis.plot(
            self.history_steps,
            self.history_opening_function,
            linewidth=2.5,
            label="g_open",
        )
        opening_axis.plot(
            self.history_steps,
            self.history_epsilon,
            linestyle="--",
            label="epsilon",
        )
        opening_axis.axvline(
            self.control_step,
            linestyle=":",
            label="Control impulse",
        )
        opening_axis.set_title(
            "Controlled Phase Opening"
        )
        opening_axis.set_xlabel(
            "Simulation Tact"
        )
        opening_axis.set_ylabel(
            "Normalized Opening State"
        )
        opening_axis.grid(
            True,
            alpha=0.3,
        )
        opening_axis.legend()

        output_axis.fill_between(
            self.history_steps,
            self.history_output_flux,
            alpha=0.25,
        )
        output_axis.plot(
            self.history_steps,
            self.history_output_flux,
            linewidth=2.5,
            label="Directed output flux S_1D",
        )
        output_axis.axvline(
            self.control_step,
            linestyle=":",
            label="Control impulse",
        )
        output_axis.set_title(
            "Directed Axial Output and Retained Energy"
        )
        output_axis.set_xlabel(
            "Simulation Tact"
        )
        output_axis.set_ylabel(
            "Output-Flux Density"
        )
        output_axis.grid(
            True,
            alpha=0.3,
        )

        retained_axis = output_axis.twinx()

        retained_axis.plot(
            self.history_steps,
            self.history_retained_energy,
            linestyle="--",
            linewidth=2.0,
            label="Retained energy",
        )
        retained_axis.set_ylabel(
            "Retained-Energy Reservoir"
        )

        output_lines, output_labels = (
            output_axis.get_legend_handles_labels()
        )
        retained_lines, retained_labels = (
            retained_axis.get_legend_handles_labels()
        )

        output_axis.legend(
            output_lines + retained_lines,
            output_labels + retained_labels,
            loc="best",
        )

        plt.tight_layout(
            rect=(
                0.0,
                0.0,
                1.0,
                0.96,
            )
        )

        plt.show()

    def print_transition_summary(self) -> None:
        """
        Print the main numerical results of the simulated transition.
        """
        if self.history_steps.size == 0:
            raise RuntimeError(
                "The impulse transition has not been simulated."
            )

        peak_index = int(
            np.argmax(
                self.history_output_flux
            )
        )

        print(
            "\n=== DIRECTED OUTPUT TRANSITION SUMMARY ==="
        )
        print(
            "Control tact: "
            f"{self.control_step}"
        )
        print(
            "Initial C3: "
            f"{self.history_c3[0]:.6f}"
        )
        print(
            "C3 at control tact: "
            f"{self.history_c3[self.control_step]:.6f}"
        )
        print(
            "Minimum C3: "
            f"{np.min(self.history_c3):.6f}"
        )
        print(
            "Peak directed output flux: "
            f"{self.history_output_flux[peak_index]:.6f}"
        )
        print(
            "Peak-output tact: "
            f"{self.history_steps[peak_index]}"
        )
        print(
            "Final directed output flux: "
            f"{self.history_output_flux[-1]:.6f}"
        )
        print(
            "Initial retained energy: "
            f"{self.history_retained_energy[0]:.6f}"
        )
        print(
            "Final retained energy: "
            f"{self.history_retained_energy[-1]:.6f}"
        )
        print(
            "Final regime: "
            f"{self.history_regime[-1]}"
        )


if __name__ == "__main__":
    simulator = MarnovPoyntingFluxTransition(
        alpha_lock=1.2,
        base_support=1.0,
        equilibrium_epsilon=0.15,
        dt=0.05,
        num_steps=60,
        gamma=0.4,
        noise_strength=0.02,
        psi_amplitude=1.5,
        dissipation_coefficient=0.5,
        phase_opening_sensitivity=1.0,
        epsilon_opening_sensitivity=1.0,
        release_efficiency=0.5,
        eccentricity_restoring_rate=0.6,
        output_area=1.0,
        seed=42,
    )

    simulator.simulate_impulse_transition(
        initial_phi=np.array(
            [0.5, -0.4, 0.3],
            dtype=np.float64,
        ),
        control_step=30,
        phase_impulse=np.array(
            [0.8, 0.8, 0.8],
            dtype=np.float64,
        ),
        epsilon_impulse=0.08,
        output_axis=np.array(
            [0.0, 0.0, 1.0],
            dtype=np.float64,
        ),
    )

    simulator.print_transition_summary()
    simulator.visualize_transition()
