from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from module_edk_visual_protocol.marnov_cubic_potential_visualizer import (
    MarnovCubicPotentialVisualizer,
)


class MarnovPoyntingFluxTransition(MarnovCubicPotentialVisualizer):
    """
    Engineering simulator of the transition from internal U_6D / C3
    retention to a directed axial exchange-flow output.

    Controlled distinctions preserved by this module:
    - S_EM is the physical electromagnetic Poynting vector E cross H.
    - S_1D is the reduced algorithmic directed-output proxy.
    - J_flux is the through massless exchange-flow output of the EDK layer.
    - C(t) is the general endogenous structural coherence.
    - C3 is cubic volumetric retention support.
    - C3 does not replace C(t).
    """

    EDS_CLOSED_RETENTION = "EDS_CLOSED_RETENTION"
    EDC_CRITICAL_BOUNDARY = "EDC_CRITICAL_BOUNDARY"
    CONTROLLED_DIRECTED_RELEASE = "CONTROLLED_DIRECTED_RELEASE"
    DEGRADATION_DOMAIN = "DEGRADATION_DOMAIN"

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
        general_coherence: float = 0.9,
        destabilizing_pressure: float | None = None,
        input_power: float | None = None,
        seed: int | None = 42,
    ) -> None:
        """
        Initialize the directed-output transition simulator.

        Parameters
        ----------
        alpha_lock:
            Base phase-lock coupling coefficient.
        base_support:
            Coherence-support parameter R(n) used by the inherited visual layer.
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
            Environmental dissipation coefficient inherited from the visual layer.
        phase_opening_sensitivity:
            Sensitivity of the output opening to phase mismatch.
        epsilon_opening_sensitivity:
            Sensitivity of the output opening to eccentricity displacement.
        release_efficiency:
            Conversion coefficient from retained C3 support into S_1D.
        eccentricity_restoring_rate:
            Rate at which epsilon returns to its equilibrium value.
        output_area:
            Effective output area used in the retained-energy balance.
        general_coherence:
            Independent general endogenous structural coherence C(t).
        destabilizing_pressure:
            Independent destabilizing pressure P(t). If omitted, it is initialized
            from calculate_dissipation_level().
        input_power:
            External input power. If omitted, it is set equal to the environmental
            dissipation level.
        seed:
            Optional random seed for reproducible simulations.
        """
        self._validate_non_negative("phase_opening_sensitivity", phase_opening_sensitivity)
        self._validate_non_negative("epsilon_opening_sensitivity", epsilon_opening_sensitivity)
        self._validate_non_negative("release_efficiency", release_efficiency)
        self._validate_non_negative("eccentricity_restoring_rate", eccentricity_restoring_rate)
        self._validate_positive("output_area", output_area)

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

        self.phase_opening_sensitivity = float(phase_opening_sensitivity)
        self.epsilon_opening_sensitivity = float(epsilon_opening_sensitivity)
        self.release_efficiency = float(release_efficiency)
        self.eccentricity_restoring_rate = float(eccentricity_restoring_rate)
        self.output_area = float(output_area)

        self.general_coherence = self._validate_non_negative(
            "general_coherence",
            general_coherence,
        )

        if destabilizing_pressure is None:
            self.destabilizing_pressure = self._validate_non_negative(
                "destabilizing_pressure",
                self.calculate_dissipation_level(),
            )
        else:
            self.destabilizing_pressure = self._validate_non_negative(
                "destabilizing_pressure",
                destabilizing_pressure,
            )

        if input_power is None:
            self.input_power = self.calculate_dissipation_level()
        else:
            self.input_power = self._validate_non_negative("input_power", input_power)

        self.output_axis = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        self.control_step = 0

        self.history_steps = np.empty(0, dtype=np.int64)
        self.history_phi = np.empty((0, 3), dtype=np.float64)
        self.history_lock_amplitude = np.empty(0, dtype=np.float64)
        self.history_c3 = np.empty(0, dtype=np.float64)
        self.history_C_t = np.empty(0, dtype=np.float64)
        self.history_P_t = np.empty(0, dtype=np.float64)
        self.history_retention_gate = np.empty(0, dtype=np.float64)
        self.history_opening_gradient = np.empty(0, dtype=np.float64)
        self.history_opening_function = np.empty(0, dtype=np.float64)
        self.history_S_1D = np.empty(0, dtype=np.float64)
        self.history_S_1D_vector = np.empty((0, 3), dtype=np.float64)
        self.history_J_flux = np.empty((0, 3), dtype=np.float64)
        self.history_retained_energy = np.empty(0, dtype=np.float64)
        self.history_epsilon = np.empty(0, dtype=np.float64)
        self.history_regime: list[str] = []

    @staticmethod
    def _validate_finite(name: str, value: float) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _validate_positive(cls, name: str, value: float) -> float:
        scalar = cls._validate_finite(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    @classmethod
    def _validate_non_negative(cls, name: str, value: float) -> float:
        scalar = cls._validate_finite(name, value)

        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")

        return scalar

    @staticmethod
    def normalize_axis(axis: np.ndarray) -> np.ndarray:
        """
        Normalize a three-dimensional output-axis vector.
        """
        axis = np.asarray(axis, dtype=np.float64)

        if axis.shape != (3,):
            raise ValueError("axis must contain exactly three components.")

        if not np.all(np.isfinite(axis)):
            raise ValueError("axis must contain only finite values.")

        axis_norm = float(np.linalg.norm(axis))

        if axis_norm == 0.0:
            raise ValueError("axis must not be the zero vector.")

        return axis / axis_norm

    @staticmethod
    def validate_phase_vector(name: str, vector: np.ndarray) -> np.ndarray:
        """
        Validate a three-component phase vector.
        """
        array = np.asarray(vector, dtype=np.float64)

        if array.shape != (3,):
            raise ValueError(f"{name} must contain exactly three components.")

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must contain only finite values.")

        return array

    @staticmethod
    def calculate_phase_opening_gradient(delta_phi: np.ndarray) -> float:
        """
        Calculate the normalized phase-opening gradient G_phi.

        G_phi = norm(sin(delta_phi)) / sqrt(3)
        """
        delta_phi = MarnovPoyntingFluxTransition.validate_phase_vector(
            "delta_phi",
            delta_phi,
        )

        gradient = np.linalg.norm(np.sin(delta_phi)) / np.sqrt(3.0)

        return float(np.clip(gradient, 0.0, 1.0))

    def calculate_opening_function(
        self,
        delta_phi: np.ndarray,
        epsilon: float,
    ) -> tuple[float, float]:
        """
        Calculate the controlled opening function g_open.
        """
        phase_gradient = self.calculate_phase_opening_gradient(delta_phi=delta_phi)

        epsilon_value = self._validate_finite("epsilon", epsilon)
        epsilon_displacement = abs(epsilon_value - self.equilibrium_epsilon)

        opening_function = np.clip(
            self.phase_opening_sensitivity * phase_gradient
            + self.epsilon_opening_sensitivity * epsilon_displacement,
            0.0,
            1.0,
        )

        return float(phase_gradient), float(opening_function)

    @staticmethod
    def calculate_retention_gate(
        general_coherence: float,
        destabilizing_pressure: float,
        tolerance: float = 1.0e-9,
    ) -> float:
        """
        Calculate the directed-release gate from the independent condition C(t) > P(t).

        C3 is not used to determine this gate.
        """
        C_t = MarnovPoyntingFluxTransition._validate_non_negative(
            "general_coherence",
            general_coherence,
        )
        P_t = MarnovPoyntingFluxTransition._validate_non_negative(
            "destabilizing_pressure",
            destabilizing_pressure,
        )
        tolerance = MarnovPoyntingFluxTransition._validate_positive(
            "tolerance",
            tolerance,
        )

        difference = C_t - P_t

        if difference > tolerance:
            return 1.0

        if abs(difference) <= tolerance:
            return 0.5

        return 0.0

    @staticmethod
    def classify_operational_regime(
        general_coherence: float,
        destabilizing_pressure: float,
        opening_function: float,
        tolerance: float = 1.0e-9,
    ) -> str:
        """
        Classify the current EDK retention and directed-release regime.

        The classification uses C(t) and P(t), not C3.
        """
        C_t = MarnovPoyntingFluxTransition._validate_non_negative(
            "general_coherence",
            general_coherence,
        )
        P_t = MarnovPoyntingFluxTransition._validate_non_negative(
            "destabilizing_pressure",
            destabilizing_pressure,
        )
        opening_value = MarnovPoyntingFluxTransition._validate_non_negative(
            "opening_function",
            opening_function,
        )

        if opening_value > 1.0:
            raise ValueError("opening_function must be in the interval [0, 1].")

        difference = C_t - P_t

        if difference < -tolerance:
            return MarnovPoyntingFluxTransition.DEGRADATION_DOMAIN

        if abs(difference) <= tolerance:
            return MarnovPoyntingFluxTransition.EDC_CRITICAL_BOUNDARY

        if opening_value <= 0.05:
            return MarnovPoyntingFluxTransition.EDS_CLOSED_RETENTION

        return MarnovPoyntingFluxTransition.CONTROLLED_DIRECTED_RELEASE

    def calculate_directed_output_flux(
        self,
        cubic_potential: float,
        opening_function: float,
        retention_gate: float,
    ) -> float:
        """
        Calculate the reduced directed output-flux density S_1D.

        S_1D = release_efficiency · C3 · g_open · retention_gate
        """
        cubic_value = self._validate_non_negative("cubic_potential", cubic_potential)
        opening_value = self._validate_non_negative("opening_function", opening_function)
        gate_value = self._validate_non_negative("retention_gate", retention_gate)

        if opening_value > 1.0:
            raise ValueError("opening_function must be in the interval [0, 1].")

        if gate_value > 1.0:
            raise ValueError("retention_gate must be in the interval [0, 1].")

        return float(
            self.release_efficiency
            * cubic_value
            * opening_value
            * gate_value
        )

    def calculate_output_vector(
        self,
        output_flux_density: float,
        axis: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Calculate the reduced directed output vector S_1D_vector.
        """
        flux_value = self._validate_non_negative(
            "output_flux_density",
            output_flux_density,
        )

        if axis is None:
            normalized_axis = self.output_axis
        else:
            normalized_axis = self.normalize_axis(axis)

        return flux_value * normalized_axis

    def calculate_j_flux(
        self,
        output_flux_density: float,
        axis: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Calculate the EDK exchange-flow output J_flux from S_1D.

        J_flux is the through massless exchange-flow output of this layer.
        It is not the physical electromagnetic Poynting vector.
        """
        return self.calculate_output_vector(
            output_flux_density=output_flux_density,
            axis=axis,
        )

    @staticmethod
    def calculate_physical_poynting_vector(
        electric_field: np.ndarray,
        magnetic_field_h: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the physical electromagnetic Poynting vector S_EM.

        S_EM = E cross H
        """
        electric_field = MarnovPoyntingFluxTransition.validate_phase_vector(
            "electric_field",
            electric_field,
        )
        magnetic_field_h = MarnovPoyntingFluxTransition.validate_phase_vector(
            "magnetic_field_h",
            magnetic_field_h,
        )

        return np.cross(electric_field, magnetic_field_h)

    def calculate_axial_physical_flux(
        self,
        electric_field: np.ndarray,
        magnetic_field_h: np.ndarray,
        axis: np.ndarray | None = None,
    ) -> float:
        """
        Calculate the axial component of the physical Poynting vector.

        This calculation is separate from S_1D and J_flux.
        """
        physical_vector = self.calculate_physical_poynting_vector(
            electric_field=electric_field,
            magnetic_field_h=magnetic_field_h,
        )

        if axis is None:
            normalized_axis = self.output_axis
        else:
            normalized_axis = self.normalize_axis(axis)

        return float(np.dot(physical_vector, normalized_axis))

    def simulate_impulse_transition(
        self,
        initial_phi: np.ndarray | None = None,
        control_step: int = 30,
        phase_impulse: np.ndarray | None = None,
        epsilon_impulse: float = 0.08,
        output_axis: np.ndarray | None = None,
        initial_retained_energy: float | None = None,
        general_coherence: float | None = None,
        destabilizing_pressure: float | None = None,
    ) -> dict[str, np.ndarray | list[str]]:
        """
        Simulate the transition from internal retention to directed output.

        Operational chain:

        U_6D -> C3 -> controlled disclosure -> impulse transition -> S_1D -> J_flux

        The retention gate is governed by C(t) > P(t).
        C3 supports the directed output but does not replace C(t).
        """
        if not 0 <= int(control_step) < self.num_steps:
            raise ValueError("control_step must be inside the simulated tact interval.")

        if initial_phi is None:
            current_phi = np.array([0.5, -0.4, 0.3], dtype=np.float64)
        else:
            current_phi = self.validate_phase_vector("initial_phi", initial_phi).copy()

        if phase_impulse is None:
            control_phase_impulse = np.array([0.8, 0.8, 0.8], dtype=np.float64)
        else:
            control_phase_impulse = self.validate_phase_vector(
                "phase_impulse",
                phase_impulse,
            )

        epsilon_impulse = self._validate_finite("epsilon_impulse", epsilon_impulse)

        if output_axis is not None:
            self.output_axis = self.normalize_axis(output_axis)

        C_t = (
            self.general_coherence
            if general_coherence is None
            else self._validate_non_negative("general_coherence", general_coherence)
        )
        P_t = (
            self.destabilizing_pressure
            if destabilizing_pressure is None
            else self._validate_non_negative("destabilizing_pressure", destabilizing_pressure)
        )

        self.general_coherence = C_t
        self.destabilizing_pressure = P_t
        self.control_step = int(control_step)
        self.current_epsilon = float(self.equilibrium_epsilon)
        self.epsilon = self.current_epsilon

        history_steps: list[int] = []
        history_phi: list[np.ndarray] = []
        history_lock_amplitude: list[float] = []
        history_c3: list[float] = []
        history_C_t: list[float] = []
        history_P_t: list[float] = []
        history_retention_gate: list[float] = []
        history_opening_gradient: list[float] = []
        history_opening_function: list[float] = []
        history_S_1D: list[float] = []
        history_S_1D_vector: list[np.ndarray] = []
        history_J_flux: list[np.ndarray] = []
        history_retained_energy: list[float] = []
        history_epsilon: list[float] = []
        history_regime: list[str] = []

        dissipation = self.calculate_dissipation_level()
        retained_energy: float | None = None

        if initial_retained_energy is not None:
            retained_energy = self._validate_non_negative(
                "initial_retained_energy",
                initial_retained_energy,
            )

        kappa = self.alpha_lock * self.base_support

        print("=== MARNOV S_1D TO J_FLUX TRANSITION ===")

        for step in range(self.num_steps):
            if step == self.control_step:
                print(
                    f"[TACT {step:02d}] "
                    "Controlled phase-opening impulse activated."
                )

                current_phi = current_phi + control_phase_impulse
                self.current_epsilon = self.current_epsilon + epsilon_impulse

            self.epsilon = self.current_epsilon

            multiplet_operator = self.calculate_u_6d(
                delta_phi=current_phi,
                kappa=kappa,
                support=self.base_support,
            )

            lock_amplitude = float(
                self.calculate_lock_amplitude(multiplet_operator)
            )

            cubic_potential = float(
                self.calculate_cubic_potential(lock_amplitude)
            )

            if cubic_potential < 0.0:
                raise FloatingPointError("cubic_potential became negative.")

            if retained_energy is None:
                retained_energy = cubic_potential

            opening_gradient, opening_function = self.calculate_opening_function(
                delta_phi=current_phi,
                epsilon=self.current_epsilon,
            )

            retention_gate = self.calculate_retention_gate(
                general_coherence=C_t,
                destabilizing_pressure=P_t,
            )

            S_1D = self.calculate_directed_output_flux(
                cubic_potential=cubic_potential,
                opening_function=opening_function,
                retention_gate=retention_gate,
            )

            S_1D_vector = self.calculate_output_vector(
                output_flux_density=S_1D,
            )

            J_flux = self.calculate_j_flux(
                output_flux_density=S_1D,
            )

            output_power = self.output_area * S_1D

            retained_energy_change = (
                self.input_power
                - dissipation
                - output_power
            ) * self.dt

            retained_energy = max(retained_energy + retained_energy_change, 0.0)

            regime = self.classify_operational_regime(
                general_coherence=C_t,
                destabilizing_pressure=P_t,
                opening_function=opening_function,
            )

            history_steps.append(step)
            history_phi.append(current_phi.copy())
            history_lock_amplitude.append(lock_amplitude)
            history_c3.append(cubic_potential)
            history_C_t.append(C_t)
            history_P_t.append(P_t)
            history_retention_gate.append(retention_gate)
            history_opening_gradient.append(opening_gradient)
            history_opening_function.append(opening_function)
            history_S_1D.append(S_1D)
            history_S_1D_vector.append(S_1D_vector.copy())
            history_J_flux.append(J_flux.copy())
            history_retained_energy.append(retained_energy)
            history_epsilon.append(self.current_epsilon)
            history_regime.append(regime)

            restoring_increment = -self.gamma * np.sin(current_phi) * self.dt

            noise_increment = self.rng.normal(
                loc=0.0,
                scale=self.noise_strength * np.sqrt(self.dt),
                size=3,
            )

            current_phi = current_phi + restoring_increment + noise_increment
            current_phi = (current_phi + np.pi) % (2.0 * np.pi) - np.pi

            epsilon_restoring_increment = (
                -self.eccentricity_restoring_rate
                * (self.current_epsilon - self.equilibrium_epsilon)
                * self.dt
            )

            self.current_epsilon = self.current_epsilon + epsilon_restoring_increment

        self.history_steps = np.asarray(history_steps, dtype=np.int64)
        self.history_phi = np.asarray(history_phi, dtype=np.float64)
        self.history_lock_amplitude = np.asarray(history_lock_amplitude, dtype=np.float64)
        self.history_c3 = np.asarray(history_c3, dtype=np.float64)
        self.history_C_t = np.asarray(history_C_t, dtype=np.float64)
        self.history_P_t = np.asarray(history_P_t, dtype=np.float64)
        self.history_retention_gate = np.asarray(history_retention_gate, dtype=np.float64)
        self.history_opening_gradient = np.asarray(history_opening_gradient, dtype=np.float64)
        self.history_opening_function = np.asarray(history_opening_function, dtype=np.float64)
        self.history_S_1D = np.asarray(history_S_1D, dtype=np.float64)
        self.history_S_1D_vector = np.asarray(history_S_1D_vector, dtype=np.float64)
        self.history_J_flux = np.asarray(history_J_flux, dtype=np.float64)
        self.history_retained_energy = np.asarray(history_retained_energy, dtype=np.float64)
        self.history_epsilon = np.asarray(history_epsilon, dtype=np.float64)
        self.history_regime = history_regime

        return {
            "steps": self.history_steps.copy(),
            "phase_history": self.history_phi.copy(),
            "lock_amplitude": self.history_lock_amplitude.copy(),
            "cubic_potential": self.history_c3.copy(),
            "C_t": self.history_C_t.copy(),
            "P_t": self.history_P_t.copy(),
            "retention_gate": self.history_retention_gate.copy(),
            "opening_gradient": self.history_opening_gradient.copy(),
            "opening_function": self.history_opening_function.copy(),
            "S_1D": self.history_S_1D.copy(),
            "S_1D_vector": self.history_S_1D_vector.copy(),
            "J_flux": self.history_J_flux.copy(),
            "output_flux": self.history_S_1D.copy(),
            "output_vector": self.history_S_1D_vector.copy(),
            "retained_energy": self.history_retained_energy.copy(),
            "epsilon": self.history_epsilon.copy(),
            "regime": list(self.history_regime),
        }

    def visualize_transition(self) -> None:
        """
        Visualize phase dynamics, C3 retention support, opening, S_1D,
        J_flux magnitude, and retained-energy redistribution.
        """
        if self.history_steps.size == 0:
            raise RuntimeError("The impulse transition has not been simulated.")

        figure, axes = plt.subplots(2, 2, figsize=(15, 10))

        figure.suptitle(
            "Marnov Protocol: U_6D / C3 Retention to S_1D / J_flux",
            fontsize=14,
            fontweight="bold",
        )

        phase_axis = axes[0, 0]
        potential_axis = axes[0, 1]
        opening_axis = axes[1, 0]
        output_axis = axes[1, 1]

        phase_axis.plot(self.history_steps, self.history_phi[:, 0], label="delta_phi_1")
        phase_axis.plot(self.history_steps, self.history_phi[:, 1], label="delta_phi_2")
        phase_axis.plot(self.history_steps, self.history_phi[:, 2], label="delta_phi_3")
        phase_axis.axvline(self.control_step, linestyle=":", label="Control impulse")
        phase_axis.axhline(0.0, linestyle="--", alpha=0.5)
        phase_axis.set_title("Tact-by-Tact Phase Dynamics")
        phase_axis.set_xlabel("Simulation Tact")
        phase_axis.set_ylabel("Phase Difference")
        phase_axis.grid(True, alpha=0.3)
        phase_axis.legend()

        potential_axis.plot(
            self.history_steps,
            self.history_c3,
            linewidth=2.5,
            label="C3 retention support",
        )
        potential_axis.plot(
            self.history_steps,
            self.history_C_t,
            linestyle="--",
            label="C(t)",
        )
        potential_axis.plot(
            self.history_steps,
            self.history_P_t,
            linestyle=":",
            label="P(t)",
        )
        potential_axis.axvline(self.control_step, linestyle=":", label="Control impulse")
        potential_axis.set_title("C3 Support and C(t) / P(t) Retention Condition")
        potential_axis.set_xlabel("Simulation Tact")
        potential_axis.set_ylabel("Operational Value")
        potential_axis.grid(True, alpha=0.3)
        potential_axis.legend()

        opening_axis.plot(self.history_steps, self.history_opening_gradient, label="G_phi")
        opening_axis.plot(
            self.history_steps,
            self.history_opening_function,
            linewidth=2.5,
            label="g_open",
        )
        opening_axis.plot(self.history_steps, self.history_epsilon, linestyle="--", label="epsilon")
        opening_axis.plot(
            self.history_steps,
            self.history_retention_gate,
            linestyle=":",
            label="retention gate",
        )
        opening_axis.axvline(self.control_step, linestyle=":", label="Control impulse")
        opening_axis.set_title("Controlled Phase Opening")
        opening_axis.set_xlabel("Simulation Tact")
        opening_axis.set_ylabel("Normalized Opening State")
        opening_axis.grid(True, alpha=0.3)
        opening_axis.legend()

        J_flux_magnitude = np.linalg.norm(self.history_J_flux, axis=1)

        output_axis.fill_between(self.history_steps, self.history_S_1D, alpha=0.25)
        output_axis.plot(
            self.history_steps,
            self.history_S_1D,
            linewidth=2.5,
            label="S_1D",
        )
        output_axis.plot(
            self.history_steps,
            J_flux_magnitude,
            linestyle="--",
            linewidth=2.0,
            label="|J_flux|",
        )
        output_axis.axvline(self.control_step, linestyle=":", label="Control impulse")
        output_axis.set_title("Directed Output S_1D and J_flux")
        output_axis.set_xlabel("Simulation Tact")
        output_axis.set_ylabel("Directed Output")
        output_axis.grid(True, alpha=0.3)

        retained_axis = output_axis.twinx()
        retained_axis.plot(
            self.history_steps,
            self.history_retained_energy,
            linestyle=":",
            linewidth=2.0,
            label="Retained energy",
        )
        retained_axis.set_ylabel("Retained-Energy Reservoir")

        output_lines, output_labels = output_axis.get_legend_handles_labels()
        retained_lines, retained_labels = retained_axis.get_legend_handles_labels()

        output_axis.legend(
            output_lines + retained_lines,
            output_labels + retained_labels,
            loc="best",
        )

        plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
        plt.show()

    def print_transition_summary(self) -> None:
        """
        Print the main numerical results of the simulated transition.
        """
        if self.history_steps.size == 0:
            raise RuntimeError("The impulse transition has not been simulated.")

        peak_index = int(np.argmax(self.history_S_1D))
        final_J_flux = self.history_J_flux[-1]
        peak_J_flux = self.history_J_flux[peak_index]

        print("\n=== S_1D TO J_FLUX TRANSITION SUMMARY ===")
        print(f"Control tact: {self.control_step}")
        print(f"Initial C3: {self.history_c3[0]:.6f}")
        print(f"C3 at control tact: {self.history_c3[self.control_step]:.6f}")
        print(f"Minimum C3: {np.min(self.history_c3):.6f}")
        print(f"C(t): {self.history_C_t[-1]:.6f}")
        print(f"P(t): {self.history_P_t[-1]:.6f}")
        print(f"Retention gate: {self.history_retention_gate[-1]:.6f}")
        print(f"Peak S_1D: {self.history_S_1D[peak_index]:.6f}")
        print(f"Peak-output tact: {self.history_steps[peak_index]}")
        print(f"Peak J_flux vector: {peak_J_flux}")
        print(f"Final S_1D: {self.history_S_1D[-1]:.6f}")
        print(f"Final J_flux vector: {final_J_flux}")
        print(f"Initial retained energy: {self.history_retained_energy[0]:.6f}")
        print(f"Final retained energy: {self.history_retained_energy[-1]:.6f}")
        print(f"Final regime: {self.history_regime[-1]}")


def run_demo(visualize: bool = False) -> None:
    """
    Run a compact demonstration of the directed S_1D to J_flux transition.
    """
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
        general_coherence=0.9,
        destabilizing_pressure=0.5,
        seed=42,
    )

    simulator.simulate_impulse_transition(
        initial_phi=np.array([0.5, -0.4, 0.3], dtype=np.float64),
        control_step=30,
        phase_impulse=np.array([0.8, 0.8, 0.8], dtype=np.float64),
        epsilon_impulse=0.08,
        output_axis=np.array([0.0, 0.0, 1.0], dtype=np.float64),
    )

    simulator.print_transition_summary()

    if visualize:
        simulator.visualize_transition()


if __name__ == "__main__":
    run_demo(visualize=False)
