import numpy as np


class EDKContinuumDemolition:
    """
    EDK Continuum Demolition Module.

    This module describes the demolition / demanifestation regime of a local
    dynamic interface inside the open nonlinear dissipative dynamic Continuum.

    The module is focused on the Marnov Protocol:

    P_ext >> C(t)

    Under excessive external pressure, endogenous structural coherence C(t)
    collapses, the dynamic interface tensor T_int approaches zero, manifested
    mass M(t) is demanifested, and the dissipative flow channel J_flux registers
    the transition of the local manifested form back into the background modes
    of the Continuum.

    The module is a standalone Python simulation layer.
    """

    def __init__(
        self,
        initial_coherence: float = 1.0,
        initial_mass: float = 10.0,
        dt: float = 0.01,
    ):
        """
        Initialize the continuum demolition module.

        Parameters
        ----------
        initial_coherence:
            Initial endogenous structural coherence C(t).
        initial_mass:
            Initial manifested mass M(t).
        dt:
            Discrete simulation time step.
        """
        if initial_coherence < 0:
            raise ValueError("initial_coherence must be non-negative.")
        if initial_mass < 0:
            raise ValueError("initial_mass must be non-negative.")
        if dt <= 0:
            raise ValueError("dt must be positive.")

        self.C = float(initial_coherence)
        self.M = float(initial_mass)
        self.dt = float(dt)

        # Dynamic interface tensor of local manifestation.
        self.T_int = np.eye(3, dtype=np.float64) * self.C

        # Dissipative / exchange flow channel.
        self.J_flux = 0.0

        # External parasitic pressure.
        self.external_pressure = 0.0

        # Demolition / appearance indicators.
        self.demolition_index = 0.0
        self.continuum_appearance_index = 0.0
        self.last_delay_time = 0.0
        self.last_velocity = 0.0

    def calculate_delay_scaling(
        self,
        external_pressure: float,
        mu: float = 0.5,
    ) -> float:
        """
        Calculate the delay scaling law for the demolition wave.

        The delay scaling law is represented as:

        velocity = mu * external_pressure
        t_delay = velocity ** (-1/3)

        Parameters
        ----------
        external_pressure:
            External parasitic pressure P_ext.
        mu:
            Drift coefficient of the tension-wave velocity.

        Returns
        -------
        float:
            Delay time t_delay.
        """
        if external_pressure <= 0:
            raise ValueError("external_pressure must be positive.")
        if mu <= 0:
            raise ValueError("mu must be positive.")

        velocity = mu * external_pressure
        t_delay = velocity ** (-1.0 / 3.0)

        self.last_velocity = float(velocity)
        self.last_delay_time = float(t_delay)

        return float(t_delay)

    def update_demolition_state(
        self,
        external_pressure: float,
        mu: float = 0.5,
    ) -> dict[str, float | str]:
        """
        Advance the demolition state by one recursive po-tactive step.

        Parameters
        ----------
        external_pressure:
            External parasitic pressure P_ext.
        mu:
            Drift coefficient of the tension-wave velocity.

        Returns
        -------
        dict[str, float | str]:
            Current demolition state.
        """
        if external_pressure <= 0:
            raise ValueError("external_pressure must be positive.")

        self.external_pressure = float(external_pressure)

        t_delay = self.calculate_delay_scaling(
            external_pressure=external_pressure,
            mu=mu,
        )

        # Recursive po-tactive decrease of endogenous structural coherence.
        coherence_loss = external_pressure * t_delay * self.dt
        self.C = max(self.C - coherence_loss, 0.0)

        # Dynamic interface tensor demolition.
        self.T_int *= self.C

        # Mass demanifestation.
        previous_mass = self.M
        self.M = self.M * self.C

        # Dissipative / exchange flow channel.
        self.J_flux = previous_mass * (1.0 - self.C)

        self._update_demolition_index()
        self._update_continuum_appearance()

        return self.calculate_demolition_state()

    def _update_demolition_index(self) -> None:
        """
        Update the demolition index.

        The demolition index increases when external pressure dominates
        endogenous structural coherence and manifested mass begins to collapse.
        """
        pressure_factor = self.external_pressure / (1.0 + self.C)
        tensor_collapse = 1.0 / (1.0 + max(float(np.trace(self.T_int)), 0.0))
        flux_factor = np.log1p(max(self.J_flux, 0.0))

        self.demolition_index = float(
            pressure_factor
            * tensor_collapse
            * (1.0 + flux_factor)
        )

    def _update_continuum_appearance(self) -> None:
        """
        Update the Continuum appearance index after demolition pressure.

        The appearance index decreases when C(t), M(t), and T_int collapse.
        """
        tensor_trace = float(np.trace(self.T_int))

        coherence_factor = max(self.C, 0.0)
        mass_factor = np.log1p(max(self.M, 0.0))
        tensor_factor = np.log1p(max(tensor_trace, 0.0))
        pressure_penalty = 1.0 / (1.0 + self.external_pressure)

        self.continuum_appearance_index = float(
            coherence_factor
            * (1.0 + mass_factor)
            * (1.0 + tensor_factor)
            * pressure_penalty
        )

    def calculate_demolition_state(self) -> dict[str, float | str]:
        """
        Return the current demolition state.

        Returns
        -------
        dict[str, float | str]:
            Current values of C(t), M(t), T_int, J_flux, delay scaling,
            demolition index, and regime.
        """
        if self.C <= 1e-5 and self.M <= 1e-5:
            demolition_regime = "FULL CONTINUUM INTERFACE DEMANIFESTATION"
        elif self.demolition_index >= 10.0:
            demolition_regime = "CRITICAL CONTINUUM DEMOLITION"
        elif self.demolition_index >= 3.0:
            demolition_regime = "ACTIVE CONTINUUM DEMOLITION"
        else:
            demolition_regime = "PARTIAL CONTINUUM DEMOLITION"

        return {
            "endogenous_structural_coherence": float(self.C),
            "manifested_mass": float(self.M),
            "tensor_trace": float(np.trace(self.T_int)),
            "j_flux": float(self.J_flux),
            "external_pressure": float(self.external_pressure),
            "delay_time": float(self.last_delay_time),
            "tension_wave_velocity": float(self.last_velocity),
            "demolition_index": float(self.demolition_index),
            "continuum_appearance_index": float(
                self.continuum_appearance_index
            ),
            "demolition_regime": demolition_regime,
        }

    def run_marnov_protocol(
        self,
        external_pressure: float,
        mu: float = 0.5,
        min_coherence: float = 1e-5,
        max_steps: int = 10_000,
    ) -> list[dict[str, float | str]]:
        """
        Run the Marnov Protocol until the local interface is demanifested.

        Parameters
        ----------
        external_pressure:
            External parasitic pressure P_ext.
        mu:
            Drift coefficient for the tension-wave velocity.
        min_coherence:
            Stop threshold for endogenous structural coherence C(t).
        max_steps:
            Safety limit preventing infinite loops.

        Returns
        -------
        list[dict[str, float | str]]:
            Full demolition trajectory.
        """
        if external_pressure <= 0:
            raise ValueError("external_pressure must be positive.")
        if mu <= 0:
            raise ValueError("mu must be positive.")
        if min_coherence < 0:
            raise ValueError("min_coherence must be non-negative.")
        if max_steps <= 0:
            raise ValueError("max_steps must be positive.")

        trajectory = []

        print(
            "[START] Marnov Protocol activated. "
            f"External pressure P = {external_pressure:.4f}"
        )

        step = 0

        while self.C > min_coherence and step < max_steps:
            step += 1

            state = self.update_demolition_state(
                external_pressure=external_pressure,
                mu=mu,
            )

            trajectory.append(state)

            print(
                f"Tick {step:02d} | "
                f"t_delay: {state['delay_time']:.5f} | "
                f"C: {state['endogenous_structural_coherence']:.4f} | "
                f"Mass: {state['manifested_mass']:.4f} | "
                f"J flux: {state['j_flux']:.4f} | "
                f"Demolition: {state['demolition_index']:.4f} | "
                f"Appearance: {state['continuum_appearance_index']:.4f}"
            )

        # Mathematical closure:
        # the local dynamic interface is fully demanifested.
        self.C = 0.0
        self.M = 0.0
        self.T_int = np.zeros((3, 3), dtype=np.float64)
        self.J_flux = 0.0
        self.continuum_appearance_index = 0.0

        closure_state = self.calculate_demolition_state()
        trajectory.append(closure_state)

        print(
            "[SHUTDOWN] Interface T_int -> 0. "
            "Matter is fully demanifested into the background modes "
            "of the Continuum."
        )

        return trajectory


if __name__ == "__main__":
    demolition_module = EDKContinuumDemolition(
        initial_coherence=1.0,
        initial_mass=10.0,
        dt=0.01,
    )

    print("=== EDK CONTINUUM DEMOLITION MODULE ===")

    initial_state = demolition_module.calculate_demolition_state()

    print(
        f"Initial C: "
        f"{initial_state['endogenous_structural_coherence']:.4f}"
    )

    print(
        f"Initial mass: "
        f"{initial_state['manifested_mass']:.4f}"
    )

    print("\n=== MARNOV PROTOCOL DEMOLITION RUN ===")

    demolition_module.run_marnov_protocol(
        external_pressure=50.0,
        mu=0.5,
    )
