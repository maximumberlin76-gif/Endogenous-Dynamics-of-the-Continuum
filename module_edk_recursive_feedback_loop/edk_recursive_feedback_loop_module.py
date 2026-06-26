from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np


class EDKRecursiveFeedbackLoopSimulation:
    """
    Closed tact-by-tact recursive feedback loop for the
    Endogenous Dynamics of the Continuum Protocol.

    The implementation preserves the distinctions:

    C(t) != C3
    R_n != C(t)
    R_t != C(t)
    J != J_flux
    T_int != M(t)
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
        omega_threshold: float = 0.05,
        alpha_filter: float = 0.2,
        kappa_base: float = 3.0,
        lambda_D: float = 0.05,
        eta_Q: float = 1.0,
        eta_R: float = 0.5,
        D_capacity: float = 1.0,
        eta_feedback: float = 0.05,
        R_min: float = 0.0,
        R_max: float = 1.0,
        interface_relaxation: float = 1.0,
        interface_pressure_coupling: float = 1.0,
        flux_interface_weight: float = 0.25,
        flux_mass_weight: float = 1.0,
        flux_local_exchange_weight: float = 0.1,
        flux_dissipative_weight: float = 0.1,
        flux_damping: float = 0.2,
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
        self.lambda_D = float(lambda_D)
        self.eta_Q = float(eta_Q)
        self.eta_R = float(eta_R)
        self.D_capacity = float(D_capacity)
        self.eta_feedback = float(eta_feedback)
        self.R_min = float(R_min)
        self.R_max = float(R_max)
        self.interface_relaxation = float(interface_relaxation)
        self.interface_pressure_coupling = float(
            interface_pressure_coupling
        )
        self.flux_interface_weight = float(flux_interface_weight)
        self.flux_mass_weight = float(flux_mass_weight)
        self.flux_local_exchange_weight = float(
            flux_local_exchange_weight
        )
        self.flux_dissipative_weight = float(
            flux_dissipative_weight
        )
        self.flux_damping = float(flux_damping)

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

        self.T_int = np.eye(
            3,
            dtype=np.float64,
        )

        self.J_flux = 0.0

        self.tact_index = 0
        self.current_C_t = 1.0
        self.current_P_t = 0.0
        self.last_D_step = 0.0
        self.last_D_n_next = 0.0
        self.last_R_t = 0.0
        self.last_total_mass = 0.0

        axis = np.linspace(
            -1.0,
            1.0,
            self.grid_size,
            dtype=np.float64,
        )

        self._coordinate_grid = np.stack(
            np.meshgrid(
                axis,
                axis,
                axis,
                indexing="ij",
            ),
            axis=0,
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
            EDKRecursiveFeedbackLoopSimulation
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

    def _validate_configuration(self) -> None:
        if self.grid_size < 4:
            raise ValueError(
                "grid_size must be at least 4."
            )

        for name in (
            "dt",
            "dx",
            "c",
            "D_capacity",
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
            "lambda_D",
            "eta_Q",
            "eta_R",
            "eta_feedback",
            "interface_relaxation",
            "interface_pressure_coupling",
            "flux_interface_weight",
            "flux_mass_weight",
            "flux_local_exchange_weight",
            "flux_dissipative_weight",
            "flux_damping",
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

        if (
            not np.isfinite(self.R_min)
            or not np.isfinite(self.R_max)
        ):
            raise ValueError(
                "R_min and R_max must be finite."
            )

        if self.R_min >= self.R_max:
            raise ValueError(
                "R_max must be greater than R_min."
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

    def _validate_interface_tensor(
        self,
        T_int: np.ndarray,
    ) -> np.ndarray:
        tensor = self._validate_field(
            "T_int",
            T_int,
            (3, 3),
        )

        return 0.5 * (
            tensor
            + tensor.T
        )

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
        D_n: float,
        R_n: float,
        A_n: float,
        E_medium: float,
        P_t: float,
    ) -> complex:
        """
        Initiate the 7D multiplet invariant
        through recursive inheritance.

        Phi =
        M_inher
        · [I + alpha · D_n · E_medium]^-1
        · A_attr(R_n, P_t)
        """
        Q_n = self._finite_scalar(
            "Q_n",
            Q_n,
        )

        D_n = self._non_negative_scalar(
            "D_n",
            D_n,
        )

        R_n = self._finite_scalar(
            "R_n",
            R_n,
        )

        A_n = self._non_negative_scalar(
            "A_n",
            A_n,
        )

        E_medium = self._non_negative_scalar(
            "E_medium",
            E_medium,
        )

        P_t = self._non_negative_scalar(
            "P_t",
            P_t,
        )

        if not (
            self.R_min
            <= R_n
            <= self.R_max
        ):
            raise ValueError(
                "R_n must remain within the configured "
                "phase-support bounds."
            )

        immune_filter = (
            1.0
            /
            (
                1.0
                + self.alpha_filter
                * D_n
                * E_medium
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
                    - P_t
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
        Form the 6D toroidal phase lock
        and the independent C3 field.

        C3 is cubic nonlinear saturation,
        compression, and delay.

        C3 is not the general endogenous
        structural coherence C(t).
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

        epsilon = 0.15

        H_asym_factor = (
            abs(Psi_7D)
            * (
                1.0
                + epsilon
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
        Update Omega(t), determine EDC and EDS,
        and manifest mass.

        Retention is determined by C(t) > P(t).

        C3 shapes the phase-transition window
        and manifested-mass density.
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
        Update the local vector exchange field J
        and calculate the phase synchronization
        indicator R_t.

        J remains distinct from the through
        massless channel J_flux.
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

    def calculate_upward_feedback(
        self,
        D_n: float,
    ) -> tuple[float, float]:
        """
        Calculate the 1D -> 7D
        dissipative feedback.

        D_step is the spatial trace formed
        during the current tact.

        D_n_next is the recursively accumulated
        dissipative trace.
        """
        D_n = self._non_negative_scalar(
            "D_n",
            D_n,
        )

        alpha_fric = 0.5
        beta_loss = 0.3

        (
            dJx_dx,
            dJx_dy,
            dJx_dz,
        ) = np.gradient(
            self.J[0],
            self.dx,
        )

        (
            dJy_dx,
            dJy_dy,
            dJy_dz,
        ) = np.gradient(
            self.J[1],
            self.dx,
        )

        (
            dJz_dx,
            dJz_dy,
            dJz_dz,
        ) = np.gradient(
            self.J[2],
            self.dx,
        )

        curl_J_x = (
            dJz_dy
            - dJy_dz
        )

        curl_J_y = (
            dJx_dz
            - dJz_dx
        )

        curl_J_z = (
            dJy_dx
            - dJx_dy
        )

        curl_J_sq = (
            curl_J_x ** 2
            + curl_J_y ** 2
            + curl_J_z ** 2
        )

        div_J_sq = (
            dJx_dx
            + dJy_dy
            + dJz_dz
        ) ** 2

        d_1D = (
            alpha_fric
            * curl_J_sq
            + beta_loss
            * div_J_sq
        )

        D_step = float(
            np.mean(
                d_1D
                * self.rho_cont
            )
        )

        recovery_factor = max(
            0.0,
            1.0
            - self.lambda_D
            * self.dt,
        )

        D_n_next = max(
            0.0,
            recovery_factor
            * D_n
            + self.dt
            * D_step,
        )

        if (
            not np.isfinite(D_step)
            or not np.isfinite(D_n_next)
        ):
            raise FloatingPointError(
                "The dissipative feedback became non-finite."
            )

        self.last_D_step = D_step
        self.last_D_n_next = D_n_next

        return (
            D_step,
            D_n_next,
        )

    def update_interface_tensor(
        self,
        T_int: np.ndarray,
        C_t: float,
        C3: np.ndarray,
        D_n_next: float,
        P_t: float,
    ) -> np.ndarray:
        """
        Update T_int as an independent
        dynamic interface tensor.
        """
        tensor = self._validate_interface_tensor(
            T_int
        )

        C_t = self._finite_scalar(
            "C_t",
            C_t,
        )

        D_n_next = self._non_negative_scalar(
            "D_n_next",
            D_n_next,
        )

        P_t = self._non_negative_scalar(
            "P_t",
            P_t,
        )

        C3 = self._validate_field(
            "C3",
            C3,
            self.shape,
        )

        positive_window = np.maximum(
            self.Omega_curr,
            0.0,
        )

        weights = (
            np.maximum(
                C3,
                0.0,
            )
            * (
                1.0
                + positive_window
            )
        )

        weight_sum = float(
            np.sum(weights)
        )

        if weight_sum <= 1.0e-15:
            shape_tensor = np.eye(
                3,
                dtype=np.float64,
            )

        else:
            weighted_center = np.asarray(
                [
                    np.sum(
                        weights
                        * self._coordinate_grid[
                            axis
                        ]
                    )
                    / weight_sum
                    for axis in range(3)
                ],
                dtype=np.float64,
            )

            centered = (
                self._coordinate_grid
                - weighted_center.reshape(
                    3,
                    1,
                    1,
                    1,
                )
            )

            covariance = np.empty(
                (3, 3),
                dtype=np.float64,
            )

            for row in range(3):
                for column in range(3):
                    covariance[
                        row,
                        column,
                    ] = float(
                        np.sum(
                            weights
                            * centered[row]
                            * centered[column]
                        )
                        / weight_sum
                    )

            covariance_trace = float(
                np.trace(covariance)
            )

            if covariance_trace <= 1.0e-15:
                shape_tensor = np.eye(
                    3,
                    dtype=np.float64,
                )

            else:
                shape_tensor = (
                    3.0
                    * covariance
                    / covariance_trace
                )

        retention_scale = max(
            0.0,
            C_t
            / (
                1.0
                + D_n_next
            ),
        )

        T_target = (
            retention_scale
            * shape_tensor
        )

        T_int_next = (
            tensor
            + self.dt
            * (
                self.interface_relaxation
                * (
                    T_target
                    - tensor
                )
                - self.interface_pressure_coupling
                * P_t
                * tensor
            )
        )

        T_int_next = 0.5 * (
            T_int_next
            + T_int_next.T
        )

        (
            eigenvalues,
            eigenvectors,
        ) = np.linalg.eigh(
            T_int_next
        )

        eigenvalues = np.maximum(
            eigenvalues,
            0.0,
        )

        T_int_next = (
            eigenvectors
            @ np.diag(eigenvalues)
            @ eigenvectors.T
        )

        return self._validate_interface_tensor(
            T_int_next
        )

    def update_massless_exchange_channel(
        self,
        J_flux: float,
        T_int_previous: np.ndarray,
        T_int_next: np.ndarray,
        M_previous: float,
        M_current: float,
        J: np.ndarray,
        D_step: float,
    ) -> float:
        """
        Update J_flux independently from
        the local vector exchange field J.
        """
        J_flux = self._non_negative_scalar(
            "J_flux",
            J_flux,
        )

        T_previous = (
            self._validate_interface_tensor(
                T_int_previous
            )
        )

        T_next = (
            self._validate_interface_tensor(
                T_int_next
            )
        )

        M_previous = self._non_negative_scalar(
            "M_previous",
            M_previous,
        )

        M_current = self._non_negative_scalar(
            "M_current",
            M_current,
        )

        J = self._validate_field(
            "J",
            J,
            (3, *self.shape),
        )

        D_step = self._non_negative_scalar(
            "D_step",
            D_step,
        )

        interface_drive = float(
            np.linalg.norm(
                T_next
                - T_previous,
                ord="fro",
            )
        )

        mass_transition_drive = abs(
            M_current
            - M_previous
        )

        local_exchange_drive = float(
            np.mean(
                np.linalg.norm(
                    J,
                    axis=0,
                )
            )
        )

        total_drive = (
            self.flux_interface_weight
            * interface_drive
            + self.flux_mass_weight
            * mass_transition_drive
            + self.flux_local_exchange_weight
            * local_exchange_drive
            + self.flux_dissipative_weight
            * D_step
        )

        J_flux_next = max(
            0.0,
            J_flux
            + self.dt
            * (
                total_drive
                - self.flux_damping
                * J_flux
            ),
        )

        if not np.isfinite(
            J_flux_next
        ):
            raise FloatingPointError(
                "J_flux became non-finite."
            )

        return float(
            J_flux_next
        )

    def recalculate_recursive_state(
        self,
        Q_n: float,
        R_n: float,
        E_medium: float,
        D_n_next: float,
        R_t: float,
    ) -> tuple[float, float]:
        """
        Recalculate Q(n+1) and R(n+1)
        through one recurrence system.
        """
        Q_n = self._finite_scalar(
            "Q_n",
            Q_n,
        )

        R_n = self._finite_scalar(
            "R_n",
            R_n,
        )

        E_medium = self._non_negative_scalar(
            "E_medium",
            E_medium,
        )

        D_n_next = self._non_negative_scalar(
            "D_n_next",
            D_n_next,
        )

        R_t = self._finite_scalar(
            "R_t",
            R_t,
        )

        Q_n_next = (
            Q_n
            * np.exp(
                -self.eta_Q
                * D_n_next
            )
            + R_n
            * np.tanh(
                E_medium
                / (
                    1.0
                    + D_n_next
                )
            )
        )

        R_n_next = float(
            np.clip(
                R_n
                * (
                    1.0
                    - self.eta_R
                    * D_n_next
                    / self.D_capacity
                )
                + self.eta_feedback
                * R_t,
                self.R_min,
                self.R_max,
            )
        )

        if (
            not np.isfinite(Q_n_next)
            or not np.isfinite(R_n_next)
        ):
            raise FloatingPointError(
                "The recursive state update became non-finite."
            )

        return (
            float(Q_n_next),
            R_n_next,
        )

    def execute_full_cycle(
        self,
        Q_n: float,
        D_n: float,
        R_n: float,
        A_n: float,
        E_medium: float,
        C_t: float,
        P_t: float,
        P_intent: float
        | Sequence[float]
        | np.ndarray,
        T_int: np.ndarray | None = None,
        J_flux: float | None = None,
    ) -> tuple[
        float,
        float,
        float,
        float,
        float,
        np.ndarray,
        float,
    ]:
        """
        Execute one complete closed
        tact-by-tact recursive cycle.

        Returns:

        total_mass
        R_t
        D_n_next
        Q_n_next
        R_n_next
        T_int_next
        J_flux_next
        """
        T_int_previous = (
            self._validate_interface_tensor(
                self.T_int
                if T_int is None
                else T_int
            )
        )

        J_flux_previous = (
            self._non_negative_scalar(
                "J_flux",
                self.J_flux
                if J_flux is None
                else J_flux,
            )
        )

        M_previous = (
            self.last_total_mass
        )

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

        (
            D_step,
            D_n_next,
        ) = self.calculate_upward_feedback(
            D_n
        )

        T_int_next = (
            self.update_interface_tensor(
                T_int_previous,
                C_t,
                C3,
                D_n_next,
                P_t,
            )
        )

        J_flux_next = (
            self.update_massless_exchange_channel(
                J_flux_previous,
                T_int_previous,
                T_int_next,
                M_previous,
                total_mass,
                self.J,
                D_step,
            )
        )

        (
            Q_n_next,
            R_n_next,
        ) = self.recalculate_recursive_state(
            Q_n,
            R_n,
            E_medium,
            D_n_next,
            R_t,
        )

        self.T_int = (
            T_int_next.copy()
        )

        self.J_flux = (
            J_flux_next
        )

        self.last_total_mass = (
            total_mass
        )

        self.tact_index += 1

        self._validate_complete_state()

        return (
            total_mass,
            R_t,
            D_n_next,
            Q_n_next,
            R_n_next,
            T_int_next.copy(),
            J_flux_next,
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
            "T_int": self.T_int,
        }

        for name, values in arrays.items():
            if not np.all(
                np.isfinite(values)
            ):
                raise FloatingPointError(
                    f"{name} contains non-finite values."
                )

        scalars = {
            "J_flux": self.J_flux,
            "current_C_t": self.current_C_t,
            "current_P_t": self.current_P_t,
            "last_D_step": self.last_D_step,
            "last_D_n_next": self.last_D_n_next,
            "last_R_t": self.last_R_t,
            "last_total_mass": self.last_total_mass,
        }

        for name, value in scalars.items():
            if not np.isfinite(value):
                raise FloatingPointError(
                    f"{name} is non-finite."
                )

    def visualize_state(
        self,
        tact_index: int,
        Q_n: float,
        D_n: float,
        R_n: float,
        C_t: float,
        P_t: float,
        J_flux: float,
    ) -> None:
        """
        Visualize the distinct operational
        layers of the current tact.
        """
        mid_z = (
            self.grid_size
            // 2
        )

        J_magnitude = np.linalg.norm(
            self.J,
            axis=0,
        )

        figure, axes = plt.subplots(
            2,
            3,
            figsize=(15, 9),
        )

        figure.suptitle(
            "EDK Recursive Feedback Loop — "
            f"Tact #{int(tact_index)}\n"
            f"Q={Q_n:.6f} | "
            f"D={D_n:.6f} | "
            f"R={R_n:.6f} | "
            f"C(t)={C_t:.6f} | "
            f"P(t)={P_t:.6f} | "
            f"M(t)={self.last_total_mass:.6f} | "
            f"J_flux={J_flux:.6f}",
            fontsize=11,
            fontweight="bold",
        )

        layers = (
            (
                self.C3_field[
                    :,
                    :,
                    mid_z,
                ],
                (
                    "C3: cubic nonlinear saturation, "
                    "compression, and delay"
                ),
                "magma",
            ),
            (
                self.Omega_curr[
                    :,
                    :,
                    mid_z,
                ],
                "Omega(t): phase-transition window",
                "coolwarm",
            ),
            (
                self.eds_mask[
                    :,
                    :,
                    mid_z,
                ].astype(
                    np.float64
                ),
                "EDS retention contour",
                "gray",
            ),
            (
                self.mass_field[
                    :,
                    :,
                    mid_z,
                ],
                "M(t): manifested-mass field",
                "viridis",
            ),
            (
                J_magnitude[
                    :,
                    :,
                    mid_z,
                ],
                (
                    "J: local vector exchange "
                    "field magnitude"
                ),
                "plasma",
            ),
        )

        for (
            axis,
            (
                field,
                title,
                color_map,
            ),
        ) in zip(
            axes.flat[:5],
            layers,
        ):
            image = axis.imshow(
                field,
                cmap=color_map,
                origin="lower",
            )

            axis.set_title(
                title
            )

            figure.colorbar(
                image,
                ax=axis,
            )

        tensor_axis = axes.flat[5]

        tensor_image = (
            tensor_axis.imshow(
                self.T_int,
                cmap="cividis",
                origin="lower",
            )
        )

        tensor_axis.set_title(
            "T_int: dynamic interface tensor"
        )

        tensor_axis.set_xticks(
            (0, 1, 2)
        )

        tensor_axis.set_yticks(
            (0, 1, 2)
        )

        figure.colorbar(
            tensor_image,
            ax=tensor_axis,
        )

        plt.tight_layout(
            rect=(
                0.0,
                0.0,
                1.0,
                0.93,
            )
        )

        plt.show()


if __name__ == "__main__":
    simulation = (
        EDKRecursiveFeedbackLoopSimulation(
            grid_size=32,
            dt=0.01,
            dx=0.1,
            seed=42,
        )
    )

    Q_n = 1.5
    D_n = 0.001
    R_n = 0.99
    A_n = 1.5
    E_medium = 0.4
    C_t = 0.90
    P_t = 0.35
    P_intent = 0.95

    T_int = np.eye(
        3,
        dtype=np.float64,
    )

    J_flux = 0.0

    print(
        "=== Start of the complete recursive "
        "tact-by-tact feedback loop ==="
    )

    for tact_index in range(
        1,
        5,
    ):
        (
            total_mass,
            R_t,
            D_n_next,
            Q_n_next,
            R_n_next,
            T_int_next,
            J_flux_next,
        ) = simulation.execute_full_cycle(
            Q_n=Q_n,
            D_n=D_n,
            R_n=R_n,
            A_n=A_n,
            E_medium=E_medium,
            C_t=C_t,
            P_t=P_t,
            P_intent=P_intent,
            T_int=T_int,
            J_flux=J_flux,
        )

        print(
            f"Tact #{tact_index}: "
            f"M(t)={total_mass:.6f} | "
            f"R_t={R_t:.6f} | "
            f"D(n+1)={D_n_next:.6f} | "
            f"Q(n+1)={Q_n_next:.6f} | "
            f"R(n+1)={R_n_next:.6f} | "
            f"J_flux={J_flux_next:.6f}"
        )

        simulation.visualize_state(
            tact_index=tact_index,
            Q_n=Q_n,
            D_n=D_n,
            R_n=R_n,
            C_t=C_t,
            P_t=P_t,
            J_flux=J_flux_next,
        )

        D_n = D_n_next
        Q_n = Q_n_next
        R_n = R_n_next
        T_int = T_int_next
        J_flux = J_flux_next
