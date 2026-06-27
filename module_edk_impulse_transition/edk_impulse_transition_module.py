from __future__ import annotations

from typing import Any

import numpy as np


class EDKProtocolSimulation:
    """
    Cascade emulator of the EDK impulse-transition protocol.

    The numerical grid is a three-dimensional projection screen for the
    higher-order recursive, phase-coherent, retention, manifestation, and
    reduced impulse-flow layers of the EDK cascade.

    Controlled distinctions preserved by this module:
    - C(t) is the general endogenous structural coherence.
    - C3 is the cubic volumetric retention support.
    - R(t) is a reduced phase synchronization indicator.
    - J is a local reduced directed impulse-flow proxy.
    - J is not the through EDK exchange-flow channel J_flux.
    """

    EDS_RETENTION = "EDS_RETENTION"
    EDC_CRITICAL_BOUNDARY = "EDC_CRITICAL_BOUNDARY"
    DEGRADATION = "DEGRADATION"

    def __init__(
        self,
        grid_size: int = 32,
        dt: float = 0.01,
        dx: float = 0.1,
        c: float = 1.0,
        chi: float = 0.5,
        gamma: float = 0.1,
        beta: float = 0.05,
        critical_tolerance: float = 1.0e-9,
        random_seed: int | None = 76,
    ) -> None:
        """
        Initialize the projected numerical Continuum of the EDK protocol.

        Parameters
        ----------
        grid_size:
            Number of cells along each spatial axis.
        dt:
            Tact duration of the numerical cascade.
        dx:
            Spatial step of the projected grid.
        c:
            Propagation coefficient of the Omega(t) window update.
        chi:
            Coupling coefficient between window geometry and C3-derived support.
        gamma:
            Coupling coefficient of background non-resonant mode gradients.
        beta:
            Damping coefficient coupling C3 to the reduced local impulse proxy J.
        critical_tolerance:
            Numerical tolerance for the boundary C(t) = P(t).
        random_seed:
            Optional deterministic seed for the background rho_cont field.
        """
        self.grid_size = self._validate_integer("grid_size", grid_size, lower=8)
        self.dt = self._positive_finite("dt", dt)
        self.dx = self._positive_finite("dx", dx)
        self.c = self._positive_finite("c", c)
        self.chi = self._non_negative_finite("chi", chi)
        self.gamma = self._non_negative_finite("gamma", gamma)
        self.beta = self._non_negative_finite("beta", beta)
        self.critical_tolerance = self._positive_finite(
            "critical_tolerance",
            critical_tolerance,
        )

        self.shape = (
            self.grid_size,
            self.grid_size,
            self.grid_size,
        )

        self.Omega_prev = np.zeros(self.shape, dtype=np.float64)
        self.Omega_curr = np.zeros(self.shape, dtype=np.float64)
        self.Omega_next = np.zeros(self.shape, dtype=np.float64)

        rng = np.random.default_rng(random_seed)
        self.rho_cont = rng.normal(
            loc=1.0,
            scale=0.05,
            size=self.shape,
        ).astype(np.float64)

        self.J = np.zeros((3, *self.shape), dtype=np.float64)

        self.C_t = 1.0
        self.P_t = 0.0
        self.C3_field = np.zeros(self.shape, dtype=np.float64)
        self.mass_field = np.zeros(self.shape, dtype=np.float64)
        self.retention_support = np.zeros(self.shape, dtype=np.float64)
        self.eds_mask = np.zeros(self.shape, dtype=bool)
        self.dynamic_regime = self.EDS_RETENTION
        self.completed_tacts = 0

        self._validate_state()

    @staticmethod
    def _finite_scalar(name: str, value: float) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _positive_finite(cls, name: str, value: float) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    @classmethod
    def _non_negative_finite(cls, name: str, value: float) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")

        return scalar

    @staticmethod
    def _validate_integer(name: str, value: int, lower: int) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{name} must be an integer.")

        try:
            integer = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be an integer.") from exc

        if integer != value:
            raise ValueError(f"{name} must be an integer.")

        if integer < lower:
            raise ValueError(f"{name} must be at least {lower}.")

        return integer

    def _validate_field(self, field: Any, name: str) -> np.ndarray:
        array = np.asarray(field, dtype=np.float64)

        if array.shape != self.shape:
            raise ValueError(f"{name} must have shape {self.shape}.")

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must contain only finite values.")

        return array

    def _scalar_or_field(self, value: Any, name: str) -> tuple[float, np.ndarray]:
        array = np.asarray(value, dtype=np.float64)

        if array.ndim == 0:
            scalar = self._non_negative_finite(name, float(array))
            return scalar, np.full(self.shape, scalar, dtype=np.float64)

        if array.shape != self.shape:
            raise ValueError(f"{name} must be a scalar or a field with shape {self.shape}.")

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must contain only finite values.")

        if np.any(array < 0.0):
            raise ValueError(f"{name} must be non-negative.")

        return float(np.mean(array)), array.astype(np.float64, copy=True)

    @staticmethod
    def _normalize_field(field: np.ndarray) -> np.ndarray:
        array = np.asarray(field, dtype=np.float64)
        minimum = float(np.min(array))
        maximum = float(np.max(array))

        if maximum <= minimum:
            return np.zeros_like(array, dtype=np.float64)

        return (array - minimum) / (maximum - minimum)

    def classify_dynamic_regime(self, C_t: Any, P_t: Any) -> str:
        """
        Classify the global EDS / EDC / degradation state using C(t) and P(t).
        """
        C_value, _ = self._scalar_or_field(C_t, "C_t")
        P_value, _ = self._scalar_or_field(P_t, "P_t")
        difference = C_value - P_value

        if difference > self.critical_tolerance:
            return self.EDS_RETENTION

        if abs(difference) <= self.critical_tolerance:
            return self.EDC_CRITICAL_BOUNDARY

        return self.DEGRADATION

    def step_7d_recursive_inheritance(
        self,
        Q_n: Any,
        D_n: Any,
        R_n: Any,
        A_n: Any,
        E_medium: Any,
        P_t: Any,
    ) -> complex:
        """
        Stage 1: recursive inheritance in the 7D layer.

        Psi_7D = Phi(Q(n), D(n), A(n))
        """
        Q_value = self._finite_scalar("Q_n", float(np.mean(Q_n)))
        D_value = self._non_negative_finite("D_n", float(np.mean(D_n)))
        R_value = self._finite_scalar("R_n", float(np.mean(R_n)))
        A_value = self._finite_scalar("A_n", float(np.mean(A_n)))
        E_value = self._finite_scalar("E_medium", float(np.mean(E_medium)))
        P_value = self._non_negative_finite("P_t", float(np.mean(P_t)))

        alpha = 0.1
        inheritance_filter = 1.0 / (1.0 + alpha * D_value * abs(E_value))

        Psi_7D = (Q_value * A_value * inheritance_filter) * np.exp(
            1j * (R_value - P_value)
        )

        if not np.isfinite(Psi_7D.real) or not np.isfinite(Psi_7D.imag):
            raise FloatingPointError("Psi_7D became non-finite.")

        return complex(Psi_7D)

    def step_6d_phase_lock(self, Psi_7D: complex) -> np.ndarray:
        """
        Stage 2: phase lock in the 6D layer.

        Psi_coh = U_6D Psi_7D
        C3 = trace(abs(Psi_coh)^2) in the abstract layer and a cubic
        volumetric retention-support field in the projected numerical layer.
        """
        Psi_7D = complex(Psi_7D)

        if not np.isfinite(Psi_7D.real) or not np.isfinite(Psi_7D.imag):
            raise ValueError("Psi_7D must be finite.")

        phase_7D = np.angle(Psi_7D)
        amplitude_7D = abs(Psi_7D)

        kappa = 2.5
        epsilon = 0.15
        delta_phi = np.sin(2.0 * phase_7D)
        asymmetric_amplitude = amplitude_7D * (1.0 + epsilon * np.sin(phase_7D))

        Psi_coh = asymmetric_amplitude * np.exp(
            1j * (phase_7D + kappa * delta_phi)
        )

        cubic_retention_amplitude = float(abs(Psi_coh) ** 3)

        x, y, z = np.indices(self.shape, dtype=np.float64)
        center = (self.grid_size - 1.0) / 2.0
        x_offset = x - center
        y_offset = y - center
        z_offset = z - center

        radial_distance = np.sqrt(x_offset ** 2 + y_offset ** 2)
        torus_radius = max(self.grid_size / 4.0, 1.0)
        torus_width = max(self.grid_size / 8.0, 1.0)
        toroidal_distance = np.sqrt((radial_distance - torus_radius) ** 2 + z_offset ** 2)

        theta = np.arctan2(y_offset, x_offset)
        asymmetry = 1.0 + 0.236068 * np.sin(3.0 * theta + 0.1 * z_offset)
        toroidal_envelope = np.exp(-(toroidal_distance ** 2) / (2.0 * torus_width ** 2))

        C3_spatial = np.clip(
            cubic_retention_amplitude * asymmetry * toroidal_envelope,
            0.0,
            None,
        )

        self.C3_field = self._validate_field(C3_spatial, "C3_field")

        return self.C3_field.copy()

    def step_5d_4d_3d_cascade(
        self,
        C3: Any,
        C_t: Any,
        P_t: Any,
        P_intent_vector: Any,
        omega_threshold: float = 0.1,
    ) -> np.ndarray:
        """
        Stages 3, 4, and 5:
        - 5D resonance-window filtering;
        - 4D retention condition C(t) > P(t);
        - 3D manifested mass-field calculation.
        """
        C3 = self._validate_field(C3, "C3")
        C_value, C_field = self._scalar_or_field(C_t, "C_t")
        P_value, P_field = self._scalar_or_field(P_t, "P_t")
        P_intent_value = self._finite_scalar("P_intent_vector", float(np.mean(P_intent_vector)))
        omega_threshold = self._non_negative_finite("omega_threshold", omega_threshold)

        self.C_t = C_value
        self.P_t = P_value
        self.dynamic_regime = self.classify_dynamic_regime(C_value, P_value)

        grad_C3_x, grad_C3_y, grad_C3_z = np.gradient(C3, self.dx)
        div_C3 = grad_C3_x + grad_C3_y + grad_C3_z

        mu = 0.2
        v_drift = mu * P_intent_value
        drift_term = v_drift * div_C3

        grad_Omega_x, grad_Omega_y, grad_Omega_z = np.gradient(
            self.Omega_curr,
            self.dx,
        )

        laplacian_Omega = (
            np.gradient(grad_Omega_x, self.dx)[0]
            + np.gradient(grad_Omega_y, self.dx)[1]
            + np.gradient(grad_Omega_z, self.dx)[2]
        )

        source_term = self.chi * div_C3 - drift_term

        self.Omega_next = (
            2.0 * self.Omega_curr
            - self.Omega_prev
            + (self.c * self.dt) ** 2 * laplacian_Omega
            - (self.c ** 2 * self.dt ** 2) * source_term
        )

        self.Omega_prev = self.Omega_curr.copy()
        self.Omega_curr = self.Omega_next.copy()

        normalized_Omega = self._normalize_field(self.Omega_curr)
        normalized_C3 = self._normalize_field(C3)

        self.retention_support = np.clip(
            0.5 * normalized_Omega + 0.5 * normalized_C3,
            0.0,
            1.0,
        )

        self.eds_mask = (
            (C_field > P_field)
            & (self.retention_support > omega_threshold)
        )

        grad_rho_x, grad_rho_y, grad_rho_z = np.gradient(self.rho_cont, self.dx)
        grad_rho_magnitude = np.sqrt(
            grad_rho_x ** 2
            + grad_rho_y ** 2
            + grad_rho_z ** 2
        )

        self.mass_field = np.zeros(self.shape, dtype=np.float64)
        self.mass_field[self.eds_mask] = (
            grad_rho_magnitude[self.eds_mask]
            * C3[self.eds_mask]
        ) / (self.c ** 2)

        self._validate_state()

        return self.eds_mask.copy()

    def step_1d_2d_flux_dynamics(self, eds_mask: Any, C3: Any) -> float:
        """
        Stage 6: reduction to the 2D / 1D impulse-flow layer.

        partial_t J + (J · grad)J = -gamma · grad rho_cont - beta · C3 · J
        """
        eds_mask = np.asarray(eds_mask, dtype=bool)

        if eds_mask.shape != self.shape:
            raise ValueError(f"eds_mask must have shape {self.shape}.")

        C3 = self._validate_field(C3, "C3")
        grad_rho = np.array(np.gradient(self.rho_cont, self.dx), dtype=np.float64)
        convective_J = np.zeros_like(self.J, dtype=np.float64)

        for axis in range(3):
            grad_J_x, grad_J_y, grad_J_z = np.gradient(self.J[axis], self.dx)
            convective_J[axis] = (
                self.J[0] * grad_J_x
                + self.J[1] * grad_J_y
                + self.J[2] * grad_J_z
            )

        for axis in range(3):
            rhs = -self.gamma * grad_rho[axis] - self.beta * C3 * self.J[axis]
            self.J[axis] = self.J[axis] + self.dt * (-convective_J[axis] + rhs)

        for axis in range(3):
            self.J[axis][~eds_mask] *= 0.98

        if np.any(eds_mask):
            masked_flow = np.sqrt(
                self.J[0][eds_mask] ** 2
                + self.J[1][eds_mask] ** 2
                + self.J[2][eds_mask] ** 2
            )
            total_flow = np.sqrt(self.J[0] ** 2 + self.J[1] ** 2 + self.J[2] ** 2)
            denominator = float(np.mean(total_flow) + 1.0e-12)
            R_t = float(np.clip(np.mean(masked_flow) / denominator, 0.0, 1.0))
        else:
            R_t = 0.0

        self._validate_state()

        return R_t

    def execute_full_cycle(
        self,
        Q_n: Any,
        D_n: Any,
        R_n: Any,
        A_n: Any,
        E_medium: Any,
        C_t: Any,
        P_t: Any,
        P_intent: Any,
    ) -> tuple[float, float]:
        """
        Execute one full tact of the EDK impulse-transition cascade.
        """
        Psi_7D = self.step_7d_recursive_inheritance(
            Q_n=Q_n,
            D_n=D_n,
            R_n=R_n,
            A_n=A_n,
            E_medium=E_medium,
            P_t=P_t,
        )

        C3 = self.step_6d_phase_lock(Psi_7D)

        eds_mask = self.step_5d_4d_3d_cascade(
            C3=C3,
            C_t=C_t,
            P_t=P_t,
            P_intent_vector=P_intent,
        )

        R_t = self.step_1d_2d_flux_dynamics(
            eds_mask=eds_mask,
            C3=C3,
        )

        total_manifested_mass = float(np.sum(self.mass_field) * (self.dx ** 3))
        self.completed_tacts += 1
        self._validate_state()

        return total_manifested_mass, R_t

    def calculate_state_summary(self) -> dict[str, float | int | str]:
        """
        Return a compact diagnostic summary of the current cascade state.
        """
        J_magnitude = np.sqrt(self.J[0] ** 2 + self.J[1] ** 2 + self.J[2] ** 2)

        return {
            "completed_tacts": int(self.completed_tacts),
            "dynamic_regime": self.dynamic_regime,
            "C_t": float(self.C_t),
            "P_t": float(self.P_t),
            "retained_fraction": float(np.mean(self.eds_mask)),
            "total_manifested_mass": float(np.sum(self.mass_field) * (self.dx ** 3)),
            "mean_J_magnitude": float(np.mean(J_magnitude)),
            "max_J_magnitude": float(np.max(J_magnitude)),
            "mean_C3": float(np.mean(self.C3_field)),
            "mean_retention_support": float(np.mean(self.retention_support)),
        }

    def _validate_state(self) -> None:
        fields = {
            "Omega_prev": self.Omega_prev,
            "Omega_curr": self.Omega_curr,
            "Omega_next": self.Omega_next,
            "rho_cont": self.rho_cont,
            "C3_field": self.C3_field,
            "mass_field": self.mass_field,
            "retention_support": self.retention_support,
        }

        for name, field in fields.items():
            if field.shape != self.shape:
                raise RuntimeError(f"{name} has invalid shape.")

            if not np.all(np.isfinite(field)):
                raise FloatingPointError(f"{name} contains non-finite values.")

        if self.J.shape != (3, *self.shape):
            raise RuntimeError("J has invalid shape.")

        if not np.all(np.isfinite(self.J)):
            raise FloatingPointError("J contains non-finite values.")

        if not np.all(np.isfinite(self.mass_field)):
            raise FloatingPointError("mass_field contains non-finite values.")

        if np.any(self.C3_field < 0.0):
            raise RuntimeError("C3_field must be non-negative.")

        if np.any(self.mass_field < 0.0):
            raise RuntimeError("mass_field must be non-negative.")


def run_demo() -> None:
    sim = EDKProtocolSimulation(
        grid_size=16,
        dt=0.01,
        dx=0.1,
        random_seed=76,
    )

    Q_initial = 1.0
    D_initial = [0.02]
    R_initial = 0.95
    A_initial = 1.2
    E_medium = 0.4
    C_initial = 0.9
    P_t = 0.5
    P_intent_vector = 0.8

    print("--- START OF THE EDK IMPULSE-TRANSITION CASCADE ---")

    for tact_index in range(1, 6):
        mass, R_sync = sim.execute_full_cycle(
            Q_n=Q_initial,
            D_n=D_initial,
            R_n=R_initial,
            A_n=A_initial,
            E_medium=E_medium,
            C_t=C_initial,
            P_t=P_t,
            P_intent=P_intent_vector,
        )

        summary = sim.calculate_state_summary()

        print(
            f"Tact #{tact_index}: "
            f"regime = {summary['dynamic_regime']} | "
            f"manifested mass = {mass:.6f} | "
            f"R(t) = {R_sync:.6f} | "
            f"retained fraction = {summary['retained_fraction']:.6f}"
        )

        Q_initial = Q_initial * 0.99 + R_sync * 0.01
        R_initial = R_initial * 0.95 + (1.0 if mass > 0.0 else 0.0) * 0.05
        D_initial = [float(np.mean(sim.J ** 2))]


if __name__ == "__main__":
    run_demo()
