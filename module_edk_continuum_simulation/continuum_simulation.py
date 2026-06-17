import numpy as np


class ContinuumSimulation:
    """
    Core simulation module for the Endogenous Dynamics of the Continuum.

    This module models the open nonlinear dissipative dynamic Continuum
    through:
    - a multiplet of coupled phase layers,
    - the Phi phase-locking operator,
    - endogenous structural coherence C(t),
    - manifested mass M(t),
    - the dynamic interface tensor T_int,
    - the dissipative flow channel J_flux,
    - the Continuum appearance layer,
    - Marnov Protocol demolition under excessive external pressure.

    The module is conceptual and intended for numerical sandbox experiments.
    """

    def __init__(
        self,
        num_layers: int = 5,
        dt: float = 0.01,
        seed: int | None = None,
    ):
        """
        Initialize the open nonlinear dissipative dynamic Continuum.

        Parameters
        ----------
        num_layers:
            Number of phase / quantum layers in the multiplet.
        dt:
            Discrete simulation time step.
        seed:
            Optional random seed for reproducible experiments.
        """
        if num_layers <= 0:
            raise ValueError("num_layers must be positive.")
        if dt <= 0:
            raise ValueError("dt must be positive.")

        self.num_layers = num_layers
        self.dt = dt
        self.rng = np.random.default_rng(seed)

        # Initial phase state of the multiplet layers.
        self.phases = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            num_layers,
        )

        # Intrinsic angular frequencies of the layers.
        self.omega = self.rng.uniform(
            5.0,
            15.0,
            num_layers,
        )

        # Endogenous structural coherence.
        self.C = 1.0

        # Manifested mass / local invariant anchor.
        self.M = 0.0

        # Dynamic interface tensor of 3D manifestation.
        self.T_int = np.eye(3, dtype=np.float64)

        # Massless dissipative flow channel.
        self.J_flux = 0.0

        # Latest dynamic state parameters.
        self.last_phase_coherence = 0.0
        self.last_external_pressure = 0.0

        # Continuum appearance layer:
        # numerical indicator of retained local manifestation.
        self.continuum_appearance_index = 0.0

    def calculate_phi_operator(self, coupling_strength: float) -> float:
        """
        Calculate the Phi operator as a phase-frequency synchronizer.

        The Phi operator is implemented as a Kuramoto-style nonlinear
        synchronization mechanism across the multiplet phase layers.

        Parameters
        ----------
        coupling_strength:
            Coupling strength K of the phase layers.

        Returns
        -------
        float:
            Phase coherence order parameter r in the range [0, 1].
        """
        phase_difference = (
            self.phases[None, :]
            - self.phases[:, None]
        )

        phase_velocity = (
            self.omega
            + (coupling_strength / self.num_layers)
            * np.sum(np.sin(phase_difference), axis=1)
        )

        self.phases = (
            self.phases + phase_velocity * self.dt
        ) % (2.0 * np.pi)

        order_parameter = np.abs(
            np.mean(np.exp(1j * self.phases))
        )

        self.last_phase_coherence = float(order_parameter)

        return float(order_parameter)

    def update_state(
        self,
        coupling_strength: float,
        external_pressure: float,
    ) -> float:
        """
        Advance the Continuum state by one recursive po-tactive dynamic step.

        Parameters
        ----------
        coupling_strength:
            Coupling strength K of the phase layers.
        external_pressure:
            External parasitic pressure P_ext acting against coherence.

        Returns
        -------
        float:
            Current phase coherence of the multiplet layers.
        """
        if external_pressure < 0:
            raise ValueError("external_pressure must be non-negative.")

        self.last_external_pressure = float(external_pressure)

        # 1. Phi operator:
        # phase-frequency synchronization of multiplet layers.
        phase_coherence = self.calculate_phi_operator(
            coupling_strength=coupling_strength,
        )

        # 2. Endogenous structural coherence:
        # phase coherence increases C(t), external pressure suppresses it.
        self.C = phase_coherence / (1.0 + external_pressure)

        # 3. Resonance-window phase transition:
        # when coherence exceeds the threshold, manifested mass and T_int appear.
        if self.C > 0.8:
            self.M = self.C * 10.0
            self.T_int = np.eye(3, dtype=np.float64) * self.C
        else:
            # Loss of coherence leads to partial demanifestation.
            self.M *= 0.1
            self.T_int *= self.C

        # 4. Current dissipative / exchange flow channel.
        self.J_flux = self.M * phase_coherence

        # 5. Update local Continuum appearance.
        self._update_continuum_appearance()

        return float(phase_coherence)

    def _update_continuum_appearance(self) -> None:
        """
        Update the Continuum appearance index.

        The Continuum appearance index describes how strongly the local
        dynamic interface is manifested as a retained form regime.

        It combines:
        - phase coherence of the multiplet,
        - endogenous structural coherence C(t),
        - manifested mass M(t),
        - trace of the interface tensor T_int,
        - external pressure as destabilizing factor,
        - J_flux as exchange / dissipative channel.
        """
        tensor_trace = float(np.trace(self.T_int))

        pressure_penalty = 1.0 / (
            1.0 + self.last_external_pressure
        )

        tensor_factor = np.log1p(
            max(tensor_trace, 0.0)
        )

        mass_factor = np.log1p(
            max(self.M, 0.0)
        )

        flux_factor = np.log1p(
            max(self.J_flux, 0.0)
        )

        self.continuum_appearance_index = float(
            self.last_phase_coherence
            * self.C
            * (1.0 + tensor_factor)
            * (1.0 + mass_factor)
            * (1.0 + flux_factor)
            * pressure_penalty
        )

    def calculate_continuum_appearance(self) -> dict[str, float | str]:
        """
        Calculate the current appearance state of the local Continuum domain.

        Returns
        -------
        dict[str, float | str]:
            Continuum appearance index, manifestation regime, coherence,
            mass, tensor trace, J_flux, and external pressure.
        """
        if self.continuum_appearance_index >= 6.0:
            manifestation_regime = "STABLE CONTINUUM FORM MANIFESTATION"
        elif self.continuum_appearance_index >= 3.0:
            manifestation_regime = "PARTIAL CONTINUUM FORM MANIFESTATION"
        else:
            manifestation_regime = "WEAK OR UNSTABLE CONTINUUM FORM MANIFESTATION"

        return {
            "continuum_appearance_index": float(
                self.continuum_appearance_index
            ),
            "manifestation_regime": manifestation_regime,
            "phase_coherence": float(self.last_phase_coherence),
            "endogenous_structural_coherence": float(self.C),
            "manifested_mass": float(self.M),
            "tensor_trace": float(np.trace(self.T_int)),
            "j_flux": float(self.J_flux),
            "external_pressure": float(self.last_external_pressure),
        }

    def run_marnov_demolition(
        self,
        external_pressure: float,
        mu: float = 0.5,
        min_coherence: float = 1e-5,
        max_steps: int = 10_000,
    ) -> None:
        """
        Run the Marnov Protocol.

        The Marnov Protocol represents recursive po-tactive demolition
        of the local dynamic interface when external pressure strongly
        exceeds endogenous structural coherence.

        Parameters
        ----------
        external_pressure:
            External parasitic pressure P_ext.
        mu:
            Drift coefficient for the tension-wave velocity.
        min_coherence:
            Stop threshold for C(t).
        max_steps:
            Safety limit preventing infinite loops.
        """
        if external_pressure <= 0:
            raise ValueError("external_pressure must be positive.")
        if mu <= 0:
            raise ValueError("mu must be positive.")
        if min_coherence < 0:
            raise ValueError("min_coherence must be non-negative.")
        if max_steps <= 0:
            raise ValueError("max_steps must be positive.")

        self.last_external_pressure = float(external_pressure)

        print(
            "[START] Marnov Protocol activated. "
            f"External pressure P = {external_pressure:.4f}"
        )

        step = 0

        while self.C > min_coherence and step < max_steps:
            step += 1

            # Drift velocity of the tension wave.
            velocity = mu * external_pressure

            # Delay Scaling Law:
            # t_delay ~ v^(-1/3)
            t_delay = velocity ** (-1.0 / 3.0)

            # Recursive po-tactive decrease of endogenous structural coherence.
            self.C -= (external_pressure * t_delay) * self.dt
            self.C = max(self.C, 0.0)

            # Interface tensor demolition:
            # T_int approaches zero as coherence collapses.
            self.T_int *= self.C

            # Mass gradient:
            # manifested mass tends toward zero with loss of coherence.
            mass_gradient = self.M * self.C

            # Mass demanifestation:
            # the invariant anchor breaks, and energy is redirected into J_flux.
            self.J_flux = self.M * (1.0 - self.C)

            self.M = mass_gradient

            self._update_continuum_appearance()

            print(
                f"Tick {step:02d} | "
                f"t_delay: {t_delay:.5f} | "
                f"C: {self.C:.4f} | "
                f"Mass: {self.M:.4f} | "
                f"J flux: {self.J_flux:.4f} | "
                f"Appearance: {self.continuum_appearance_index:.4f}"
            )

        # Mathematical closure:
        # the dynamic interface is fully demanifested.
        self.T_int = np.zeros((3, 3), dtype=np.float64)
        self.M = 0.0
        self.J_flux = 0.0
        self.continuum_appearance_index = 0.0

        print(
            "[SHUTDOWN] Interface T_int -> 0. "
            "Matter is fully demanifested into the background modes "
            "of the Continuum."
        )


if __name__ == "__main__":
    system = ContinuumSimulation(
        num_layers=8,
        dt=0.01,
        seed=42,
    )

    print("=== CONTINUUM CORE WITH APPEARANCE LAYER ===")

    for tick in range(5):
        coherence = system.update_state(
            coupling_strength=15.0,
            external_pressure=0.1,
        )

        appearance_state = system.calculate_continuum_appearance()

        print(
            f"Step {tick} | "
            f"Layer phase coherence: {coherence:.4f} | "
            f"Manifested mass: {system.M:.4f} | "
            f"J flux: {system.J_flux:.4f}"
        )

        print(
            f"       -> Continuum appearance index: "
            f"{appearance_state['continuum_appearance_index']:.4f}"
        )

        print(
            f"       -> Manifestation regime: "
            f"{appearance_state['manifestation_regime']}"
        )

    print("\n=== CRITICAL CONTINUUM OVERLOAD ===")

    system.update_state(
        coupling_strength=2.0,
        external_pressure=50.0,
    )

    system.run_marnov_demolition(
        external_pressure=50.0,
    )
    
