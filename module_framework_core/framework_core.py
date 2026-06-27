from __future__ import annotations

from typing import Any

import numpy as np


class ContinuumSimulation:
    """
    Core simulation module for the Endogenous Dynamics of the Continuum.

    The module models a local domain of an open nonlinear dissipative dynamic
    Continuum through:
    - a multiplet of coupled phase layers;
    - a local Phi-support phase-coupling operator;
    - a reduced phase synchronization indicator R(t);
    - phase-coherence support;
    - a reduced proxy of general endogenous structural coherence C(t);
    - manifested mass anchor M(t);
    - dynamic interface tensor T_int;
    - through massless exchange-flow channel J_flux;
    - Continuum appearance layer;
    - controlled demanifestation through the Marnov Protocol under excessive
      destabilizing pressure.

    Controlled distinctions preserved by this module:
    - phase synchronization is not identical to phase coherence;
    - R(t) is not identical to C(t);
    - C(t) is not C3;
    - T_int is not M(t);
    - J is not J_flux.

    The module is conceptual and intended for numerical sandbox experiments.
    """

    STABLE_MANIFESTATION = "STABLE CONTINUUM FORM MANIFESTATION"
    PARTIAL_MANIFESTATION = "PARTIAL CONTINUUM FORM MANIFESTATION"
    WEAK_MANIFESTATION = "WEAK OR UNSTABLE CONTINUUM FORM MANIFESTATION"

    def __init__(
        self,
        num_layers: int = 5,
        dt: float = 0.01,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the local open nonlinear dissipative dynamic Continuum.

        Parameters
        ----------
        num_layers:
            Number of phase or quantum layers in the multiplet.
        dt:
            Discrete simulation tact duration.
        seed:
            Optional random seed for reproducible experiments.
        """
        self.num_layers = self._validate_positive_integer(
            "num_layers",
            num_layers,
        )
        self.dt = self._validate_positive_finite(
            "dt",
            dt,
        )

        self.rng = np.random.default_rng(seed)

        self.phases = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            self.num_layers,
        )

        self.omega = self.rng.uniform(
            5.0,
            15.0,
            self.num_layers,
        )

        self.C = 1.0
        self.M = 0.0
        self.T_int = np.eye(3, dtype=np.float64)
        self.J_flux = 0.0

        self.last_phase_synchronization_indicator = 0.0
        self.last_phase_coherence_support = 0.0
        self.last_external_pressure = 0.0
        self.continuum_appearance_index = 0.0
        self.completed_tacts = 0

        self._validate_state()

    @staticmethod
    def _validate_finite_scalar(name: str, value: Any) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _validate_positive_finite(cls, name: str, value: Any) -> float:
        scalar = cls._validate_finite_scalar(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    @classmethod
    def _validate_non_negative_finite(cls, name: str, value: Any) -> float:
        scalar = cls._validate_finite_scalar(name, value)

        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")

        return scalar

    @staticmethod
    def _validate_positive_integer(name: str, value: Any) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a positive integer.")

        try:
            integer = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a positive integer.") from exc

        if integer != value:
            raise ValueError(f"{name} must be a positive integer.")

        if integer <= 0:
            raise ValueError(f"{name} must be positive.")

        return integer

    @staticmethod
    def _normalize_unit_interval(value: float) -> float:
        return float(np.clip(value, 0.0, 1.0))

    def calculate_phi_operator(self, coupling_strength: float) -> float:
        """
        Calculate the local Phi-support phase-coupling operator.

        In this module, the operator is implemented as a Kuramoto-style
        nonlinear phase-coupling mechanism across the multiplet phase layers.

        The returned value is the reduced observable phase synchronization
        indicator R(t), not the full general endogenous structural coherence C(t).

        Parameters
        ----------
        coupling_strength:
            Coupling strength K of the phase layers.

        Returns
        -------
        float:
            Reduced phase synchronization indicator R(t) in the interval [0, 1].
        """
        coupling_strength = self._validate_non_negative_finite(
            "coupling_strength",
            coupling_strength,
        )

        phase_difference = self.phases[None, :] - self.phases[:, None]

        phase_velocity = (
            self.omega
            + (coupling_strength / self.num_layers)
            * np.sum(np.sin(phase_difference), axis=1)
        )

        self.phases = (self.phases + phase_velocity * self.dt) % (2.0 * np.pi)

        order_parameter = abs(
            np.mean(
                np.exp(1j * self.phases),
            )
        )

        phase_synchronization_indicator = self._normalize_unit_interval(
            float(order_parameter),
        )

        self.last_phase_synchronization_indicator = phase_synchronization_indicator

        return phase_synchronization_indicator

    def calculate_phase_coherence_support(
        self,
        phase_synchronization_indicator: float,
        previous_coherence: float,
    ) -> float:
        """
        Calculate reduced phase-coherence support from the observable
        phase synchronization indicator and the inherited coherence state.

        This is a local executable support value and does not replace the
        full theoretical definition of phase coherence.
        """
        R_t = self._validate_non_negative_finite(
            "phase_synchronization_indicator",
            phase_synchronization_indicator,
        )
        previous_C = self._validate_non_negative_finite(
            "previous_coherence",
            previous_coherence,
        )

        R_t = self._normalize_unit_interval(R_t)
        previous_C = self._normalize_unit_interval(previous_C)

        support = 0.5 * R_t + 0.5 * previous_C

        self.last_phase_coherence_support = self._normalize_unit_interval(support)

        return self.last_phase_coherence_support

    def update_state(
        self,
        coupling_strength: float,
        external_pressure: float,
    ) -> float:
        """
        Advance the local Continuum state by one recursive tact-by-tact
        dynamic step.

        Parameters
        ----------
        coupling_strength:
            Coupling strength K of the phase layers.
        external_pressure:
            Destabilizing pressure P(t) acting against retained coherence.

        Returns
        -------
        float:
            Current reduced phase synchronization indicator R(t).
        """
        external_pressure = self._validate_non_negative_finite(
            "external_pressure",
            external_pressure,
        )

        self.last_external_pressure = external_pressure

        phase_synchronization_indicator = self.calculate_phi_operator(
            coupling_strength=coupling_strength,
        )

        previous_C = float(self.C)

        phase_coherence_support = self.calculate_phase_coherence_support(
            phase_synchronization_indicator=phase_synchronization_indicator,
            previous_coherence=previous_C,
        )

        coherence_gain = phase_coherence_support * (1.0 - previous_C)

        coherence_loss = (
            (1.0 - phase_coherence_support)
            + external_pressure
        ) * previous_C

        self.C = self._normalize_unit_interval(
            previous_C
            + self.dt * (coherence_gain - coherence_loss),
        )

        interface_target = np.eye(3, dtype=np.float64) * self.C

        self.T_int = (
            self.T_int
            + self.dt
            * (
                interface_target
                - self.T_int
                - external_pressure * self.T_int
            )
        )

        previous_M = float(self.M)

        tensor_retention = max(
            float(np.trace(self.T_int)) / 3.0,
            0.0,
        )

        if self.C > 0.8:
            mass_target = 10.0 * tensor_retention

            self.M = max(
                0.0,
                previous_M
                + self.dt * (mass_target - previous_M),
            )
        else:
            demanifestation_rate = external_pressure + (0.8 - self.C)

            self.M = max(
                0.0,
                previous_M
                - self.dt * demanifestation_rate * previous_M,
            )

        mass_release_rate = max(previous_M - self.M, 0.0) / self.dt

        flux_drive = (
            phase_coherence_support * self.C
            + mass_release_rate
            + external_pressure * (1.0 - self.C)
        )

        flux_damping = self.C * float(self.J_flux)

        self.J_flux = max(
            0.0,
            float(self.J_flux)
            + self.dt * (flux_drive - flux_damping),
        )

        self._update_continuum_appearance()

        self.completed_tacts += 1
        self._validate_state()

        return phase_synchronization_indicator

    def _update_continuum_appearance(self) -> None:
        """
        Update the Continuum appearance index.

        The Continuum appearance index describes how strongly the local
        dynamic interface is manifested as a retained form-state.

        It combines:
        - reduced phase synchronization indicator R(t);
        - phase-coherence support;
        - reduced proxy of general endogenous structural coherence C(t);
        - manifested mass anchor M(t);
        - trace of dynamic interface tensor T_int;
        - external pressure as a destabilizing factor;
        - J_flux as the through exchange-flow channel.
        """
        tensor_trace = float(np.trace(self.T_int))

        pressure_penalty = 1.0 / (1.0 + self.last_external_pressure)

        tensor_factor = np.log1p(max(tensor_trace, 0.0))
        mass_factor = np.log1p(max(self.M, 0.0))
        flux_factor = np.log1p(max(self.J_flux, 0.0))

        self.continuum_appearance_index = float(
            self.last_phase_synchronization_indicator
            * self.last_phase_coherence_support
            * self.C
            * (1.0 + tensor_factor)
            * (1.0 + mass_factor)
            * (1.0 + flux_factor)
            * pressure_penalty
        )

    def calculate_continuum_appearance(self) -> dict[str, float | int | str]:
        """
        Calculate the current appearance state of the local Continuum domain.

        Returns
        -------
        dict[str, float | int | str]:
            Continuum appearance index, manifestation regime, coherence,
            mass, tensor trace, J_flux, external pressure, and tact counter.
        """
        if self.continuum_appearance_index >= 6.0:
            manifestation_regime = self.STABLE_MANIFESTATION
        elif self.continuum_appearance_index >= 3.0:
            manifestation_regime = self.PARTIAL_MANIFESTATION
        else:
            manifestation_regime = self.WEAK_MANIFESTATION

        return {
            "completed_tacts": int(self.completed_tacts),
            "continuum_appearance_index": float(self.continuum_appearance_index),
            "manifestation_regime": manifestation_regime,
            "phase_synchronization_indicator": float(
                self.last_phase_synchronization_indicator,
            ),
            "phase_coherence_support": float(self.last_phase_coherence_support),
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
        min_coherence: float = 1.0e-5,
        max_tacts: int = 10_000,
    ) -> None:
        """
        Run the Marnov Protocol.

        The Marnov Protocol represents recursive tact-by-tact controlled
        demanifestation of the local dynamic interface when destabilizing
        pressure strongly exceeds retained coherence capacity.

        Parameters
        ----------
        external_pressure:
            Destabilizing pressure P(t).
        mu:
            Drift coefficient for the tension-wave velocity.
        min_coherence:
            Stop threshold for C(t).
        max_tacts:
            Safety limit preventing an infinite loop.
        """
        external_pressure = self._validate_positive_finite(
            "external_pressure",
            external_pressure,
        )
        mu = self._validate_positive_finite(
            "mu",
            mu,
        )
        min_coherence = self._validate_non_negative_finite(
            "min_coherence",
            min_coherence,
        )
        max_tacts = self._validate_positive_integer(
            "max_tacts",
            max_tacts,
        )

        self.last_external_pressure = external_pressure

        print(
            "[START] Marnov Protocol activated. "
            f"Destabilizing pressure P(t) = {external_pressure:.4f}"
        )

        tact_index = 0

        while self.C > min_coherence and tact_index < max_tacts:
            tact_index += 1

            velocity = mu * external_pressure
            t_delay = velocity ** (-1.0 / 3.0)

            self.C -= external_pressure * t_delay * self.dt
            self.C = max(self.C, 0.0)

            self.T_int *= self.C

            mass_gradient = self.M * self.C

            self.J_flux = self.M * (1.0 - self.C)
            self.M = mass_gradient

            self._update_continuum_appearance()

            print(
                f"Tact {tact_index:02d} | "
                f"t_delay: {t_delay:.5f} | "
                f"C(t): {self.C:.4f} | "
                f"M(t): {self.M:.4f} | "
                f"J_flux: {self.J_flux:.4f} | "
                f"Appearance: {self.continuum_appearance_index:.4f}"
            )

        self.T_int = np.zeros((3, 3), dtype=np.float64)
        self.M = 0.0
        self.J_flux = 0.0
        self.C = 0.0
        self.last_phase_coherence_support = 0.0
        self.last_phase_synchronization_indicator = 0.0
        self.continuum_appearance_index = 0.0

        self._validate_state()

        print(
            "[SHUTDOWN] Interface T_int -> 0. "
            "The local form is fully demanifested into the background modes "
            "of the Continuum."
        )

    def _validate_state(self) -> None:
        if not np.all(np.isfinite(self.phases)):
            raise FloatingPointError("phases contain non-finite values.")

        if not np.all(np.isfinite(self.omega)):
            raise FloatingPointError("omega contains non-finite values.")

        if self.T_int.shape != (3, 3):
            raise RuntimeError("T_int must have shape (3, 3).")

        if not np.all(np.isfinite(self.T_int)):
            raise FloatingPointError("T_int contains non-finite values.")

        scalar_fields = {
            "C": self.C,
            "M": self.M,
            "J_flux": self.J_flux,
            "last_phase_synchronization_indicator": (
                self.last_phase_synchronization_indicator
            ),
            "last_phase_coherence_support": self.last_phase_coherence_support,
            "last_external_pressure": self.last_external_pressure,
            "continuum_appearance_index": self.continuum_appearance_index,
        }

        for name, value in scalar_fields.items():
            if not np.isfinite(float(value)):
                raise FloatingPointError(f"{name} is non-finite.")

        if self.C < 0.0:
            raise RuntimeError("C must be non-negative.")

        if self.M < 0.0:
            raise RuntimeError("M must be non-negative.")

        if self.J_flux < 0.0:
            raise RuntimeError("J_flux must be non-negative.")


def run_demo() -> None:
    system = ContinuumSimulation(
        num_layers=8,
        dt=0.01,
        seed=42,
    )

    print("=== CONTINUUM FRAMEWORK CORE WITH APPEARANCE LAYER ===")

    for tact_index in range(1, 6):
        phase_synchronization_indicator = system.update_state(
            coupling_strength=15.0,
            external_pressure=0.1,
        )

        appearance_state = system.calculate_continuum_appearance()

        print(
            f"Tact {tact_index:02d} | "
            f"R(t): {phase_synchronization_indicator:.4f} | "
            f"C(t): {system.C:.4f} | "
            f"M(t): {system.M:.4f} | "
            f"J_flux: {system.J_flux:.4f}"
        )

        print(
            "       -> Continuum appearance index: "
            f"{appearance_state['continuum_appearance_index']:.4f}"
        )

        print(
            "       -> Manifestation regime: "
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


if __name__ == "__main__":
    run_demo()
