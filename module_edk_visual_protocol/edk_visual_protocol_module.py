from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np


class EDKVisualProtocolSimulation:
    """
    Local tact-by-tact EDK visualization simulation.

    The module preserves the distinctions:

    C(t) != C3
    R(t) != C(t)
    J != J_flux
    T_int != M(t)

    This module visualizes only the local descending cascade and does not
    implement the independent through layers T_int and J_flux.
    """

    def __init__(
        self,
        grid_size: int = 32,
        dt: float = 0.01,
        dx: float = 0.1,
        c: float = 1.0,
        chi: float = 0.5,
        gamma: float = 0.1,
        beta: float = 0.05,
        omega_threshold: float = 0.001,
        alpha_filter: float = 0.1,
        kappa_base: float = 2.5,
        asymmetry_epsilon: float = 0.15,
        seed: int | None = None,
    ) -> None:
        self.grid_size = int(grid_size)
        self.dt = float(dt)
        self.dx = float(dx)
        self.c = float(c)
        self.chi = float(chi)
        self.gamma = float(gamma)
        self.beta = float(beta)
        self.omega_threshold = float(omega_threshold)
        self.alpha_filter = float(alpha_filter)
        self.kappa_base = float(kappa_base)
        self.asymmetry_epsilon = float(asymmetry_epsilon)

        self._validate_configuration()

        self.shape = (
            self.grid_size,
            self.grid_size,
            self.grid_size,
        )

        self.rng = np.random.default_rng(seed)

        self.Omega_prev = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        self.Omega_curr = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        self.Omega_next = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        self.rho_cont = np.clip(
            self.rng.normal(
                1.0,
                0.05,
                self.shape,
            ),
            1.0e-12,
            None,
        )

        self.J = np.zeros(
            (3, *self.shape),
            dtype=np.float64,
        )

        self.C3_field = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        self.mass_field = np.zeros(
            self.shape,
            dtype=np.float64,
        )

        self.eds_mask = np.zeros(
            self.shape,
            dtype=bool,
        )

        self.tact_index = 0
        self.current_C_t = 1.0
        self.current_P_t = 0.0
        self.last_R_t = 0.0
        self.last_total_mass = 0.0

    def _validate_configuration(self) -> None:
        if self.grid_size < 4:
            raise ValueError(
                "grid_size must be at least 4."
            )

        for name in (
            "dt",
            "dx",
            "c",
        ):
            value = getattr(
                self,
                name,
            )

            if (
                not np.isfinite(value)
                or value <= 0.0
            ):
                raise ValueError(
                    f"{name} must be a positive finite value."
                )

        for name in (
            "chi",
            "gamma",
            "beta",
            "omega_threshold",
            "alpha_filter",
            "kappa_base",
            "asymmetry_epsilon",
        ):
            value = getattr(
                self,
                name,
            )

            if (
                not np.isfinite(value)
                or value < 0.0
            ):
                raise ValueError(
                    f"{name} must be finite and non-negative."
                )

        courant_number = (
            self.c
            * self.dt
            / self.dx
        )

        courant_limit = (
            1.0
            / np.sqrt(3.0)
        )

        if courant_number > courant_limit:
            raise ValueError(
                "The 3D FDTD Courant condition is violated: "
                "c * dt / dx must not exceed 1 / sqrt(3)."
            )

    @staticmethod
    def _finite_scalar(
        name: str,
        value: float,
    ) -> float:
        scalar = float(value)

        if not np.isfinite(scalar):
            raise ValueError(
                f"{name} must be finite."
            )

        return scalar

    @staticmethod
    def _non_negative_scalar(
        name: str,
        value: float,
    ) -> float:
        scalar = (
            EDKVisualProtocolSimulation
            ._finite_scalar(
                name,
                value,
            )
        )

        if scalar < 0.0:
            raise ValueError(
                f"{name} must be non-negative."
            )

        return scalar

    def _validate_field(
        self,
        name: str,
        field: np.ndarray,
        expected_shape: tuple[int, ...],
    ) -> np.ndarray:
        array = np.asarray(
            field,
            dtype=np.float64,
        )

        if array.shape != expected_shape:
            raise ValueError(
                f"{name} must have shape {expected_shape}, "
                f"received {array.shape}."
            )

        if not np.all(
            np.isfinite(array)
        ):
            raise ValueError(
                f"{name} contains non-finite values."
            )

        return array

    def _normalize_intent(
        self,
        P_intent: float
        | Sequence[float]
        | np.ndarray,
    ) -> np.ndarray:
        intent = np.asarray(
            P_intent,
            dtype=np.float64,
        )

        if intent.ndim == 0:
            intent_vector = np.full(
                3,
                float(intent),
                dtype=np.float64,
            )

        elif intent.shape == (3,):
            intent_vector = intent.copy()

        else:
            raise ValueError(
                "P_intent must be a finite scalar "
                "or a vector with shape (3,)."
            )

        if not np.all(
            np.isfinite(intent_vector)
        ):
            raise ValueError(
                "P_intent contains non-finite values."
            )

        return intent_vector

    def step_7d_recursive_inheritance(
        self,
        Q_n: float,
        D_n: float
        | Sequence[float]
        | np.ndarray,
        R_n: float,
        A_n: float,
        E_medium: float
        | Sequence[float]
        | np.ndarray,
        P_t: float
        | Sequence[float]
        | np.ndarray,
    ) -> complex:
        """
        Generate the 7D Super-Code through recursive inheritance.
        """
        Q_n = self._finite_scalar(
            "Q_n",
            Q_n,
        )

        R_n = self._finite_scalar(
            "R_n",
            R_n,
        )

        A_n = self._non_negative_scalar(
            "A_n",
            A_n,
        )

        D_array = np.asarray(
            D_n,
            dtype=np.float64,
        )

        E_array = np.asarray(
            E_medium,
            dtype=np.float64,
        )

        P_array = np.asarray(
            P_t,
            dtype=np.float64,
        )

        for name, array in (
            (
                "D_n",
                D_array,
            ),
            (
                "E_medium",
                E_array,
            ),
            (
                "P_t",
                P_array,
            ),
        ):
            if not np.all(
                np.isfinite(array)
            ):
                raise ValueError(
                    f"{name} contains non-finite values."
                )

        D_mean = float(
            np.mean(D_array)
        )

        E_mean = float(
            np.mean(E_array)
        )

        P_mean = float(
            np.mean(P_array)
        )

        if D_mean < 0.0:
            raise ValueError(
                "D_n must be non-negative."
            )

        if E_mean < 0.0:
            raise ValueError(
                "E_medium must be non-negative."
            )

        if P_mean < 0.0:
            raise ValueError(
                "P_t must be non-negative."
            )

        immune_filter = (
            1.0
            /
            (
                1.0
                + self.alpha_filter
                * D_mean
                * E_mean
            )
        )

        Psi_7D = (
            Q_n
            * A_n
            * immune_filter
            * np.exp(
                1j
                * (
                    R_n
                    - P_mean
                )
            )
        )

        if (
            not np.isfinite(Psi_7D.real)
            or not np.isfinite(Psi_7D.imag)
        ):
            raise FloatingPointError(
                "Psi_7D became non-finite."
            )

        return complex(
            Psi_7D
        )

    def step_6d_phase_lock(
        self,
        Psi_7D: complex,
        R_n: float,
    ) -> np.ndarray:
        """
        Form the phase-coherent toroidal configuration and C3 field.

        C3 is cubic nonlinear saturation, compression, and delay.
        It is not the general endogenous structural coherence C(t).
        """
        R_n = self._finite_scalar(
            "R_n",
            R_n,
        )

        phase_7D = float(
            np.angle(Psi_7D)
        )

        kappa = (
            self.kappa_base
            * R_n
        )

        delta_phi = np.sin(
            2.0
            * phase_7D
        )

        H_asym_factor = (
            abs(Psi_7D)
            * (
                1.0
                + self.asymmetry_epsilon
                * np.sin(phase_7D)
            )
        )

        Psi_coh = (
            H_asym_factor
            * np.exp(
                1j
                * (
                    phase_7D
                    + kappa
                    * delta_phi
                )
            )
        )

        C3_scalar = float(
            abs(Psi_coh) ** 3
        )

        x, y, z = np.indices(
            self.shape,
            dtype=np.float64,
        )

        center = (
            self.grid_size
            - 1.0
        ) / 2.0

        major_radius = max(
            self.grid_size
            / 4.0,
            1.0,
        )

        smoothing_radius = max(
            self.grid_size
            / 6.0,
            1.0,
        )

        radial_distance = np.sqrt(
            (x - center) ** 2
            + (y - center) ** 2
        )

        toroidal_distance = np.sqrt(
            (
                radial_distance
                - major_radius
            ) ** 2
            + (
                z
                - center
            ) ** 2
        )

        C3_spatial = (
            C3_scalar
            * np.exp(
                -(
                    toroidal_distance ** 2
                )
                /
                (
                    2.0
                    * smoothing_radius ** 2
                )
            )
        )

        self.C3_field = self._validate_field(
            "C3_field",
            C3_spatial,
            self.shape,
        )

        return self.C3_field.copy()

    def step_5d_4d_3d_cascade(
        self,
        C3: np.ndarray,
        C_t: float,
        P_t: float,
        P_intent: float
        | Sequence[float]
        | np.ndarray,
    ) -> np.ndarray:
        """
        Update Omega(t), evaluate EDC and EDS, and manifest M(t).

        Retention is determined by C(t) > P(t), while C3 shapes the
        phase-transition window and the local manifested-mass density.
        """
        C3 = self._validate_field(
            "C3",
            C3,
            self.shape,
        )

        C_t = self._finite_scalar(
            "C_t",
            C_t,
        )

        P_t = self._non_negative_scalar(
            "P_t",
            P_t,
        )

        if not (
            0.0
            <= C_t
            <= 1.0
        ):
            raise ValueError(
                "C_t must remain within [0, 1]."
            )

        intent_vector = self._normalize_intent(
            P_intent
        )

        grad_C3 = np.gradient(
            C3,
            self.dx,
        )

        div_C3 = (
            grad_C3[0]
            + grad_C3[1]
            + grad_C3[2]
        )

        drift_velocity = (
            0.2
            * intent_vector
        )

        drift_term = (
            drift_velocity[0]
            * grad_C3[0]
            + drift_velocity[1]
            * grad_C3[1]
            + drift_velocity[2]
            * grad_C3[2]
        )

        grad_Omega = np.gradient(
            self.Omega_curr,
            self.dx,
        )

        laplacian_Omega = (
            np.gradient(
                grad_Omega[0],
                self.dx,
                axis=0,
            )
            + np.gradient(
                grad_Omega[1],
                self.dx,
                axis=1,
            )
            + np.gradient(
                grad_Omega[2],
                self.dx,
                axis=2,
            )
        )

        source_term = (
            self.chi
            * div_C3
            - drift_term
        )

        self.Omega_next = (
            2.0
            * self.Omega_curr
            - self.Omega_prev
            + (
                self.c
                * self.dt
            ) ** 2
            * laplacian_Omega
            - self.c ** 2
            * self.dt ** 2
            * source_term
        )

        self._validate_field(
            "Omega_next",
            self.Omega_next,
            self.shape,
        )

        self.Omega_prev = (
            self.Omega_curr.copy()
        )

        self.Omega_curr = (
            self.Omega_next.copy()
        )

        retained_regime = (
            C_t
            > P_t
        )

        self.eds_mask = (
            retained_regime
            & (
                self.Omega_curr
                > self.omega_threshold
            )
        )

        grad_rho = np.gradient(
            self.rho_cont,
            self.dx,
        )

        grad_rho_magnitude = np.sqrt(
            grad_rho[0] ** 2
            + grad_rho[1] ** 2
            + grad_rho[2] ** 2
        )

        self.mass_field.fill(
            0.0
        )

        self.mass_field[
            self.eds_mask
        ] = (
            grad_rho_magnitude[
                self.eds_mask
            ]
            * C3[
                self.eds_mask
            ]
            / self.c ** 2
        )

        self._validate_field(
            "mass_field",
            self.mass_field,
            self.shape,
        )

        self.current_C_t = C_t
        self.current_P_t = P_t

        return self.eds_mask.copy()

    def step_1d_2d_flux_dynamics(
        self,
        eds_mask: np.ndarray,
        C3: np.ndarray,
    ) -> float:
        """
        Update the local vector exchange field J and calculate R_t.

        J remains distinct from the through massless channel J_flux.
        """
        mask = np.asarray(
            eds_mask,
            dtype=bool,
        )

        if mask.shape != self.shape:
            raise ValueError(
                f"eds_mask must have shape {self.shape}."
            )

        C3 = self._validate_field(
            "C3",
            C3,
            self.shape,
        )

        grad_rho = np.asarray(
            np.gradient(
                self.rho_cont,
                self.dx,
            ),
            dtype=np.float64,
        )

        conv_J = np.zeros_like(
            self.J
        )

        for component in range(3):
            grad_component = np.gradient(
                self.J[component],
                self.dx,
            )

            conv_J[component] = (
                self.J[0]
                * grad_component[0]
                + self.J[1]
                * grad_component[1]
                + self.J[2]
                * grad_component[2]
            )

        for component in range(3):
            rhs = (
                -self.gamma
                * grad_rho[component]
                - self.beta
                * C3
                * self.J[component]
            )

            self.J[component] += (
                self.dt
                * (
                    -conv_J[component]
                    + rhs
                )
            )

        self._validate_field(
            "J",
            self.J,
            (3, *self.shape),
        )

        if not np.any(mask):
            R_t = 0.0

        else:
            local_Jx = (
                self.J[0][mask]
            )

            local_Jy = (
                self.J[1][mask]
            )

            local_magnitude = np.hypot(
                local_Jx,
                local_Jy,
            )

            magnitude_sum = float(
                np.sum(local_magnitude)
            )

            if magnitude_sum <= 1.0e-15:
                R_t = 0.0

            else:
                local_phase = np.arctan2(
                    local_Jy,
                    local_Jx,
                )

                weighted_order = (
                    np.sum(
                        local_magnitude
                        * np.exp(
                            1j
                            * local_phase
                        )
                    )
                    / magnitude_sum
                )

                R_t = float(
                    np.clip(
                        abs(weighted_order),
                        0.0,
                        1.0,
                    )
                )

        self.last_R_t = R_t

        return R_t

    def execute_full_cycle(
        self,
        Q_n: float,
        D_n: float
        | Sequence[float]
        | np.ndarray,
        R_n: float,
        A_n: float,
        E_medium: float
        | Sequence[float]
        | np.ndarray,
        C_t: float,
        P_t: float,
        P_intent: float
        | Sequence[float]
        | np.ndarray,
    ) -> tuple[float, float]:
        """
        Execute one full tact of the local descending EDK cascade.
        """
        Psi_7D = (
            self.step_7d_recursive_inheritance(
                Q_n,
                D_n,
                R_n,
                A_n,
                E_medium,
                P_t,
            )
        )

        C3 = self.step_6d_phase_lock(
            Psi_7D,
            R_n,
        )

        eds_mask = (
            self.step_5d_4d_3d_cascade(
                C3,
                C_t,
                P_t,
                P_intent,
            )
        )

        R_t = (
            self.step_1d_2d_flux_dynamics(
                eds_mask,
                C3,
            )
        )

        total_mass = float(
            np.sum(
                self.mass_field
            )
            * self.dx ** 3
        )

        if not np.isfinite(
            total_mass
        ):
            raise FloatingPointError(
                "total_mass became non-finite."
            )

        self.last_total_mass = (
            total_mass
        )

        self.tact_index += 1

        self._validate_complete_state()

        return (
            total_mass,
            R_t,
        )

    def _validate_complete_state(
        self,
    ) -> None:
        arrays = {
            "Omega_prev": self.Omega_prev,
            "Omega_curr": self.Omega_curr,
            "Omega_next": self.Omega_next,
            "rho_cont": self.rho_cont,
            "J": self.J,
            "C3_field": self.C3_field,
            "mass_field": self.mass_field,
        }

        for name, values in arrays.items():
            if not np.all(
                np.isfinite(values)
            ):
                raise FloatingPointError(
                    f"{name} contains non-finite values."
                )

        for name, value in (
            (
                "current_C_t",
                self.current_C_t,
            ),
            (
                "current_P_t",
                self.current_P_t,
            ),
            (
                "last_R_t",
                self.last_R_t,
            ),
            (
                "last_total_mass",
                self.last_total_mass,
            ),
        ):
            if not np.isfinite(value):
                raise FloatingPointError(
                    f"{name} is non-finite."
                )

    def visualize_slice(
        self,
        tact_index: int | None = None,
        show: bool = True,
    ) -> plt.Figure:
        """
        Render central 2D slices of C3 and M(t).
        """
        displayed_tact = (
            self.tact_index
            if tact_index is None
            else int(tact_index)
        )

        if displayed_tact < 0:
            raise ValueError(
                "tact_index must be non-negative."
            )

        mid_z = (
            self.grid_size
            // 2
        )

        figure, (
            axis_c3,
            axis_mass,
        ) = plt.subplots(
            1,
            2,
            figsize=(12, 5),
        )

        figure.suptitle(
            "EDK Visual Protocol — Observation Slice, "
            f"Tact #{displayed_tact}",
            fontsize=14,
            fontweight="bold",
        )

        image_c3 = axis_c3.imshow(
            self.C3_field[
                :,
                :,
                mid_z,
            ],
            cmap="magma",
            origin="lower",
        )

        axis_c3.set_title(
            "6D toroidal field C3"
        )

        axis_c3.set_xlabel(
            "Projection X"
        )

        axis_c3.set_ylabel(
            "Projection Y"
        )

        figure.colorbar(
            image_c3,
            ax=axis_c3,
            label=(
                "Cubic nonlinear saturation, "
                "compression, and delay"
            ),
        )

        image_mass = axis_mass.imshow(
            self.mass_field[
                :,
                :,
                mid_z,
            ],
            cmap="viridis",
            origin="lower",
        )

        axis_mass.set_title(
            "3D manifested-mass field M(t)"
        )

        axis_mass.set_xlabel(
            "Projection X"
        )

        axis_mass.set_ylabel(
            "Projection Y"
        )

        figure.colorbar(
            image_mass,
            ax=axis_mass,
            label="Manifested-mass density",
        )

        figure.tight_layout(
            rect=(
                0.0,
                0.0,
                1.0,
                0.93,
            )
        )

        if show:
            plt.show()

        return figure


if __name__ == "__main__":
    simulation = (
        EDKVisualProtocolSimulation(
            grid_size=32,
            dt=0.01,
            dx=0.1,
            seed=42,
        )
    )

    Q_n = 1.2
    D_n = 0.01
    R_n = 0.98
    A_n = 1.5
    E_medium = 0.3
    C_t = 0.90
    P_t = 0.40
    P_intent = 0.90

    print(
        "=== Start of the tact-by-tact local cascade "
        "with graphical slice generation ==="
    )

    for tact_index in range(
        1,
        4,
    ):
        (
            total_mass,
            R_t,
        ) = simulation.execute_full_cycle(
            Q_n=Q_n,
            D_n=D_n,
            R_n=R_n,
            A_n=A_n,
            E_medium=E_medium,
            C_t=C_t,
            P_t=P_t,
            P_intent=P_intent,
        )

        print(
            f"Tact #{tact_index}: "
            f"M(t)={total_mass:.6f} | "
            f"R_t={R_t:.6f} | "
            f"retained_cells="
            f"{int(np.count_nonzero(simulation.eds_mask))}"
        )

        simulation.visualize_slice(
            tact_index=tact_index,
            show=True,
        )

        Q_n = (
            Q_n
            * 0.98
            + R_t
            * 0.02
        )

        D_n = float(
            np.mean(
                simulation.J ** 2
            )
        )
