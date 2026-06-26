from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


class MarnovCubicPotentialVisualizer:
    """
    Engineering visual simulator for the Marnov phase-lock protocol.

    The module models:

    - three orthogonal two-dimensional phase planes;
    - their tensor-product contraction into an 8x8 multiplet operator U_6D;
    - tact-by-tact suppression of phase mismatch;
    - normalized phase-lock amplitude;
    - cubic nonlinear saturation, compression, and delay C3;
    - transition across a local cubic-dissipation barrier P_cubic;
    - the independent system-level relation C(t) to P(t).

    The implementation preserves the distinctions:

    C(t) != C3
    P(t) != P_cubic

    The local equality C3 = P_cubic is a cubic-potential transition
    boundary. It is not the EDS / EDC system boundary.

    The EDS / EDC system relation is determined independently through
    the general endogenous structural coherence C(t) and the
    destabilizing pressure P(t).
    """

    EDS_RETENTION = "ENDOGENOUS_DYNAMIC_STABILITY"
    EDC_BOUNDARY = "ENDOGENOUS_DYNAMIC_CRITICALITY"
    DEGRADATION_DRIFT = "DEGRADATION_DRIFT"

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
        C_t: float = 0.90,
        P_t: float = 0.35,
        critical_tolerance: float = 1.0e-12,
        seed: int | None = 42,
    ) -> None:
        """
        Initialize the engineering visual simulator.

        Parameters
        ----------
        alpha_lock:
            Base phase-lock coupling coefficient.
        base_support:
            Initial phase-support coefficient R(n), constrained to [0, 1].
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
            Scalar field amplitude used in the C3 calculation.
        dissipation_coefficient:
            Coefficient of the local cubic-dissipation level P_cubic.
        C_t:
            General endogenous structural coherence C(t).
        P_t:
            Destabilizing system pressure P(t).
        critical_tolerance:
            Numerical tolerance for the system-level EDC boundary.
        seed:
            Optional random seed for reproducible simulations.
        """
        self.alpha_lock = self._non_negative_finite(
            "alpha_lock",
            alpha_lock,
        )

        self.base_support = self._bounded_finite(
            "base_support",
            base_support,
            0.0,
            1.0,
        )

        self.epsilon = self._finite_scalar(
            "epsilon",
            epsilon,
        )

        self.dt = self._positive_finite(
            "dt",
            dt,
        )

        if isinstance(num_steps, bool) or int(num_steps) != num_steps:
            raise ValueError("num_steps must be an integer.")

        self.num_steps = int(num_steps)

        if self.num_steps <= 0:
            raise ValueError("num_steps must be positive.")

        self.gamma = self._non_negative_finite(
            "gamma",
            gamma,
        )

        self.noise_strength = self._non_negative_finite(
            "noise_strength",
            noise_strength,
        )

        self.psi_amplitude = self._positive_finite(
            "psi_amplitude",
            psi_amplitude,
        )

        self.dissipation_coefficient = self._non_negative_finite(
            "dissipation_coefficient",
            dissipation_coefficient,
        )

        self.C_t = self._bounded_finite(
            "C_t",
            C_t,
            0.0,
            1.0,
        )

        self.P_t = self._non_negative_finite(
            "P_t",
            P_t,
        )

        self.critical_tolerance = self._non_negative_finite(
            "critical_tolerance",
            critical_tolerance,
        )

        self.rng = np.random.default_rng(seed)

        self.history_steps = np.empty(
            0,
            dtype=np.int64,
        )

        self.history_phi = np.empty(
            (0, 3),
            dtype=np.float64,
        )

        self.history_lock_amplitude = np.empty(
            0,
            dtype=np.float64,
        )

        self.history_c3 = np.empty(
            0,
            dtype=np.float64,
        )

        self.x_coordinates = np.empty(
            0,
            dtype=np.float64,
        )

        self.support_profile = np.empty(
            0,
            dtype=np.float64,
        )

        self.interface_c3 = np.empty(
            0,
            dtype=np.float64,
        )

        self.interface_p_cubic = np.empty(
            0,
            dtype=np.float64,
        )

        self.local_cubic_margin = np.empty(
            0,
            dtype=np.float64,
        )

        self.cubic_transition_points = np.empty(
            0,
            dtype=np.float64,
        )

        # Backward-compatible aliases for the previous field names.
        self.interface_dissipation = self.interface_p_cubic
        self.bifurcation_points = self.cubic_transition_points

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

    @classmethod
    def _positive_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(
            name,
            value,
        )

        if scalar <= 0.0:
            raise ValueError(
                f"{name} must be positive."
            )

        return scalar

    @classmethod
    def _non_negative_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(
            name,
            value,
        )

        if scalar < 0.0:
            raise ValueError(
                f"{name} must be non-negative."
            )

        return scalar

    @classmethod
    def _bounded_finite(
        cls,
        name: str,
        value: float,
        lower: float,
        upper: float,
    ) -> float:
        scalar = cls._finite_scalar(
            name,
            value,
        )

        if not lower <= scalar <= upper:
            raise ValueError(
                f"{name} must be within "
                f"[{lower}, {upper}]."
            )

        return scalar

    @staticmethod
    def _finite_vector(
        name: str,
        values: np.ndarray,
        expected_shape: tuple[int, ...],
    ) -> np.ndarray:
        array = np.asarray(
            values,
            dtype=np.float64,
        )

        if array.shape != expected_shape:
            raise ValueError(
                f"{name} must have shape "
                f"{expected_shape}, "
                f"received {array.shape}."
            )

        if not np.all(
            np.isfinite(array)
        ):
            raise ValueError(
                f"{name} contains non-finite values."
            )

        return array

    def set_system_state(
        self,
        C_t: float,
        P_t: float,
    ) -> None:
        """
        Set the independent system-level EDS / EDC state parameters.
        """
        self.C_t = self._bounded_finite(
            "C_t",
            C_t,
            0.0,
            1.0,
        )

        self.P_t = self._non_negative_finite(
            "P_t",
            P_t,
        )

    def classify_system_regime(
        self,
        C_t: float | None = None,
        P_t: float | None = None,
    ) -> str:
        """
        Classify the system-level relation between C(t) and P(t).

        This classification is independent of the local C3 profile.
        """
        coherence = (
            self.C_t
            if C_t is None
            else self._bounded_finite(
                "C_t",
                C_t,
                0.0,
                1.0,
            )
        )

        pressure = (
            self.P_t
            if P_t is None
            else self._non_negative_finite(
                "P_t",
                P_t,
            )
        )

        margin = (
            coherence
            - pressure
        )

        if margin > self.critical_tolerance:
            return self.EDS_RETENTION

        if margin < -self.critical_tolerance:
            return self.DEGRADATION_DRIFT

        return self.EDC_BOUNDARY

    def build_pair_lock(
        self,
        delta_phi: float,
        kappa: float,
        support: float = 1.0,
    ) -> np.ndarray:
        """
        Build one phase lock on a two-dimensional phase plane.
        """
        delta_phi = self._finite_scalar(
            "delta_phi",
            delta_phi,
        )

        kappa = self._non_negative_finite(
            "kappa",
            kappa,
        )

        support = self._bounded_finite(
            "support",
            support,
            0.0,
            1.0,
        )

        phase_angle = (
            kappa
            * np.sin(delta_phi)
        )

        phase_operator = np.array(
            [
                [
                    np.exp(
                        1j
                        * phase_angle
                    ),
                    0.0,
                ],
                [
                    0.0,
                    np.exp(
                        -1j
                        * phase_angle
                    ),
                ],
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

        support_amplitude = np.sqrt(
            support
        )

        pair_lock = (
            support_amplitude
            * (
                phase_operator
                @ asymmetry_operator
            )
        )

        if not np.all(
            np.isfinite(pair_lock)
        ):
            raise FloatingPointError(
                "The pair-lock operator "
                "became non-finite."
            )

        return pair_lock

    def calculate_u_6d(
        self,
        delta_phi: np.ndarray,
        kappa: float,
        support: float = 1.0,
    ) -> np.ndarray:
        """
        Contract three orthogonal two-dimensional phase locks into U_6D.
        """
        phase_differences = self._finite_vector(
            "delta_phi",
            delta_phi,
            (3,),
        )

        kappa = self._non_negative_finite(
            "kappa",
            kappa,
        )

        support = self._bounded_finite(
            "support",
            support,
            0.0,
            1.0,
        )

        lock_x = self.build_pair_lock(
            delta_phi=phase_differences[0],
            kappa=kappa,
            support=support,
        )

        lock_y = self.build_pair_lock(
            delta_phi=phase_differences[1],
            kappa=kappa,
            support=support,
        )

        lock_z = self.build_pair_lock(
            delta_phi=phase_differences[2],
            kappa=kappa,
            support=support,
        )

        multiplet_operator = np.kron(
            np.kron(
                lock_x,
                lock_y,
            ),
            lock_z,
        )

        if multiplet_operator.shape != (
            8,
            8,
        ):
            raise RuntimeError(
                "U_6D must be represented "
                "by an 8x8 operator."
            )

        if not np.all(
            np.isfinite(
                multiplet_operator
            )
        ):
            raise FloatingPointError(
                "U_6D became non-finite."
            )

        return multiplet_operator

    @staticmethod
    def calculate_lock_amplitude(
        multiplet_operator: np.ndarray,
    ) -> float:
        """
        Calculate the normalized phase-lock amplitude.
        """
        operator = np.asarray(
            multiplet_operator,
            dtype=np.complex128,
        )

        if operator.ndim != 2:
            raise ValueError(
                "multiplet_operator must be "
                "a two-dimensional matrix."
            )

        rows, columns = operator.shape

        if rows == 0 or columns == 0:
            raise ValueError(
                "multiplet_operator must not be empty."
            )

        if rows != columns:
            raise ValueError(
                "multiplet_operator must be square."
            )

        if not np.all(
            np.isfinite(operator)
        ):
            raise ValueError(
                "multiplet_operator contains "
                "non-finite values."
            )

        amplitude = float(
            np.abs(
                np.trace(operator)
            )
            / rows
        )

        if not np.isfinite(
            amplitude
        ):
            raise FloatingPointError(
                "The normalized lock amplitude "
                "became non-finite."
            )

        return amplitude

    def calculate_cubic_potential(
        self,
        lock_amplitude: float,
    ) -> float:
        """
        Calculate C3 as cubic nonlinear saturation,
        compression, and delay.

        C3 = (psi_amplitude * lock_amplitude)^3
        """
        lock_amplitude = self._non_negative_finite(
            "lock_amplitude",
            lock_amplitude,
        )

        C3 = (
            self.psi_amplitude
            * lock_amplitude
        ) ** 3

        if not np.isfinite(
            C3
        ):
            raise FloatingPointError(
                "C3 became non-finite."
            )

        return float(C3)

    def calculate_cubic_dissipation_level(
        self,
    ) -> float:
        """
        Calculate the local cubic-dissipation level P_cubic.

        P_cubic is not the system-level destabilizing pressure P(t).
        """
        P_cubic = (
            self.dissipation_coefficient
            * self.psi_amplitude ** 3
        )

        if not np.isfinite(
            P_cubic
        ):
            raise FloatingPointError(
                "P_cubic became non-finite."
            )

        return float(P_cubic)

    def calculate_dissipation_level(
        self,
    ) -> float:
        """
        Backward-compatible alias for
        calculate_cubic_dissipation_level.
        """
        return (
            self.calculate_cubic_dissipation_level()
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
        """
        if initial_phi is None:
            current_phi = np.array(
                [
                    0.8,
                    -0.7,
                    0.5,
                ],
                dtype=np.float64,
            )
        else:
            current_phi = self._finite_vector(
                "initial_phi",
                initial_phi,
                (3,),
            ).copy()

        history_steps = np.empty(
            self.num_steps,
            dtype=np.int64,
        )

        history_phi = np.empty(
            (
                self.num_steps,
                3,
            ),
            dtype=np.float64,
        )

        history_lock_amplitude = np.empty(
            self.num_steps,
            dtype=np.float64,
        )

        history_c3 = np.empty(
            self.num_steps,
            dtype=np.float64,
        )

        kappa = (
            self.alpha_lock
            * self.base_support
        )

        for tact_index in range(
            self.num_steps
        ):
            multiplet_operator = (
                self.calculate_u_6d(
                    delta_phi=current_phi,
                    kappa=kappa,
                    support=self.base_support,
                )
            )

            lock_amplitude = (
                self.calculate_lock_amplitude(
                    multiplet_operator
                )
            )

            C3 = (
                self.calculate_cubic_potential(
                    lock_amplitude
                )
            )

            history_steps[
                tact_index
            ] = tact_index

            history_phi[
                tact_index
            ] = current_phi

            history_lock_amplitude[
                tact_index
            ] = lock_amplitude

            history_c3[
                tact_index
            ] = C3

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

            current_phi = (
                current_phi
                + restoring_increment
                + noise_increment
            )

            current_phi = (
                current_phi
                + np.pi
            ) % (
                2.0
                * np.pi
            ) - np.pi

            if not np.all(
                np.isfinite(current_phi)
            ):
                raise FloatingPointError(
                    "The phase state "
                    "became non-finite."
                )

        self.history_steps = (
            history_steps
        )

        self.history_phi = (
            history_phi
        )

        self.history_lock_amplitude = (
            history_lock_amplitude
        )

        self.history_c3 = (
            history_c3
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
        Calculate the local C3 profile across an interface barrier.

        The local comparison C3 to P_cubic is visualized independently
        from the system-level EDS / EDC relation C(t) to P(t).
        """
        x_start = self._finite_scalar(
            "x_start",
            x_start,
        )

        x_end = self._finite_scalar(
            "x_end",
            x_end,
        )

        barrier_center = self._finite_scalar(
            "barrier_center",
            barrier_center,
        )

        barrier_width = self._positive_finite(
            "barrier_width",
            barrier_width,
        )

        barrier_depth = self._bounded_finite(
            "barrier_depth",
            barrier_depth,
            0.0,
            1.0,
        )

        if x_end <= x_start:
            raise ValueError(
                "x_end must be greater than x_start."
            )

        if (
            isinstance(
                num_points,
                bool,
            )
            or int(num_points)
            != num_points
        ):
            raise ValueError(
                "num_points must be an integer."
            )

        num_points = int(
            num_points
        )

        if num_points < 2:
            raise ValueError(
                "num_points must be at least 2."
            )

        if fixed_phi is None:
            fixed_phase_state = np.array(
                [
                    0.1,
                    -0.1,
                    0.05,
                ],
                dtype=np.float64,
            )
        else:
            fixed_phase_state = (
                self._finite_vector(
                    "fixed_phi",
                    fixed_phi,
                    (3,),
                )
            )

        x_coordinates = np.linspace(
            x_start,
            x_end,
            num_points,
            dtype=np.float64,
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
            1.0,
        )

        cubic_potential_profile = np.empty(
            num_points,
            dtype=np.float64,
        )

        for (
            index,
            local_support,
        ) in enumerate(
            support_profile
        ):
            local_kappa = (
                self.alpha_lock
                * local_support
            )

            local_operator = (
                self.calculate_u_6d(
                    delta_phi=(
                        fixed_phase_state
                    ),
                    kappa=local_kappa,
                    support=float(
                        local_support
                    ),
                )
            )

            local_lock_amplitude = (
                self.calculate_lock_amplitude(
                    local_operator
                )
            )

            cubic_potential_profile[
                index
            ] = (
                self.calculate_cubic_potential(
                    local_lock_amplitude
                )
            )

        P_cubic = (
            self.calculate_cubic_dissipation_level()
        )

        cubic_dissipation_profile = np.full(
            num_points,
            P_cubic,
            dtype=np.float64,
        )

        local_cubic_margin = (
            cubic_potential_profile
            - cubic_dissipation_profile
        )

        self.x_coordinates = (
            x_coordinates
        )

        self.support_profile = (
            support_profile
        )

        self.interface_c3 = (
            cubic_potential_profile
        )

        self.interface_p_cubic = (
            cubic_dissipation_profile
        )

        self.local_cubic_margin = (
            local_cubic_margin
        )

        self.cubic_transition_points = (
            self._find_transition_points(
                x_coordinates=(
                    x_coordinates
                ),
                first_profile=(
                    cubic_potential_profile
                ),
                second_profile=(
                    cubic_dissipation_profile
                ),
            )
        )

        # Backward-compatible aliases.
        self.interface_dissipation = (
            self.interface_p_cubic
        )

        self.bifurcation_points = (
            self.cubic_transition_points
        )

        return (
            self.x_coordinates.copy(),
            self.support_profile.copy(),
            self.interface_c3.copy(),
            self.interface_p_cubic.copy(),
        )

    @staticmethod
    def _find_transition_points(
        x_coordinates: np.ndarray,
        first_profile: np.ndarray,
        second_profile: np.ndarray,
    ) -> np.ndarray:
        """
        Find coordinates where two finite one-dimensional profiles are equal.

        Exact equality samples and sign-changing intervals are both retained.
        """
        x = np.asarray(
            x_coordinates,
            dtype=np.float64,
        )

        first = np.asarray(
            first_profile,
            dtype=np.float64,
        )

        second = np.asarray(
            second_profile,
            dtype=np.float64,
        )

        if (
            x.ndim != 1
            or first.ndim != 1
            or second.ndim != 1
        ):
            raise ValueError(
                "Transition profiles must "
                "be one-dimensional."
            )

        if not (
            x.size
            == first.size
            == second.size
        ):
            raise ValueError(
                "Transition profiles must "
                "have equal lengths."
            )

        if x.size < 2:
            raise ValueError(
                "At least two profile "
                "points are required."
            )

        if not (
            np.all(np.isfinite(x))
            and np.all(
                np.isfinite(first)
            )
            and np.all(
                np.isfinite(second)
            )
        ):
            raise ValueError(
                "Transition profiles contain "
                "non-finite values."
            )

        if np.any(
            np.diff(x) <= 0.0
        ):
            raise ValueError(
                "x_coordinates must be "
                "strictly increasing."
            )

        difference = (
            first
            - second
        )

        scale = max(
            1.0,
            float(
                np.max(
                    np.abs(first)
                )
            ),
            float(
                np.max(
                    np.abs(second)
                )
            ),
        )

        tolerance = (
            64.0
            * np.finfo(
                np.float64
            ).eps
            * scale
        )

        points: list[float] = []

        exact_indices = np.where(
            np.abs(
                difference
            ) <= tolerance
        )[0]

        points.extend(
            float(
                x[index]
            )
            for index in exact_indices
        )

        for index in range(
            x.size - 1
        ):
            y_left = (
                difference[index]
            )

            y_right = (
                difference[index + 1]
            )

            if (
                abs(y_left)
                <= tolerance
                or abs(y_right)
                <= tolerance
            ):
                continue

            if (
                np.signbit(y_left)
                == np.signbit(y_right)
            ):
                continue

            x_left = (
                x[index]
            )

            x_right = (
                x[index + 1]
            )

            crossing = (
                x_left
                - y_left
                * (
                    x_right
                    - x_left
                )
                / (
                    y_right
                    - y_left
                )
            )

            points.append(
                float(crossing)
            )

        if not points:
            return np.empty(
                0,
                dtype=np.float64,
            )

        return np.asarray(
            sorted(
                set(points)
            ),
            dtype=np.float64,
        )

    def visualize_engineering_data(
        self,
        show: bool = True,
    ) -> plt.Figure:
        """
        Visualize temporal phase dynamics,
        U_6D, C3, and the interface map.
        """
        if self.history_steps.size == 0:
            raise RuntimeError(
                "Temporal dynamics have not "
                "been simulated."
            )

        if self.x_coordinates.size == 0:
            raise RuntimeError(
                "The interface profile has not "
                "been calculated."
            )

        figure = plt.figure(
            figsize=(
                16,
                11,
            ),
        )

        system_regime = (
            self.classify_system_regime()
        )

        figure.suptitle(
            "Marnov Protocol Engineering Simulator "
            "— U_6D / C3 Core\n"
            f"System relation: "
            f"C(t)={self.C_t:.6f}, "
            f"P(t)={self.P_t:.6f}, "
            f"regime={system_regime}",
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
            self.history_phi[
                :,
                0,
            ],
            label=(
                "X axis: delta_phi_1"
            ),
            linewidth=2.0,
        )

        phase_axis.plot(
            self.history_steps,
            self.history_phi[
                :,
                1,
            ],
            label=(
                "Y axis: delta_phi_2"
            ),
            linewidth=2.0,
        )

        phase_axis.plot(
            self.history_steps,
            self.history_phi[
                :,
                2,
            ],
            label=(
                "Z axis: delta_phi_3"
            ),
            linewidth=2.0,
        )

        phase_axis.axhline(
            0.0,
            linestyle="--",
            alpha=0.5,
        )

        phase_axis.set_title(
            "Tact-by-Tact Suppression "
            "of Phase Mismatch"
        )

        phase_axis.set_xlabel(
            "Structural Self-Organization Tact"
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
            self.history_phi[
                :,
                0,
            ],
            self.history_phi[
                :,
                1,
            ],
            self.history_phi[
                :,
                2,
            ],
            linewidth=2.0,
        )

        phase_space_axis.scatter(
            self.history_phi[
                0,
                0,
            ],
            self.history_phi[
                0,
                1,
            ],
            self.history_phi[
                0,
                2,
            ],
            marker="o",
            s=45,
            label="Initial state",
        )

        phase_space_axis.scatter(
            self.history_phi[
                -1,
                0,
            ],
            self.history_phi[
                -1,
                1,
            ],
            self.history_phi[
                -1,
                2,
            ],
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
            label=(
                "Normalized lock amplitude"
            ),
        )

        lock_axis.set_title(
            "U_6D Phase-Lock Amplitude"
        )

        lock_axis.set_xlabel(
            "Structural Self-Organization Tact"
        )

        lock_axis.set_ylabel(
            "Normalized abs(Tr(U_6D))"
        )

        lock_axis.grid(
            True,
            alpha=0.3,
        )

        cubic_axis = (
            lock_axis.twinx()
        )

        cubic_axis.plot(
            self.history_steps,
            self.history_c3,
            linestyle="--",
            linewidth=2.0,
            label="C3",
        )

        cubic_axis.set_ylabel(
            "C3: Cubic Nonlinear Saturation, "
            "Compression, and Delay"
        )

        (
            lock_lines,
            lock_labels,
        ) = (
            lock_axis
            .get_legend_handles_labels()
        )

        (
            cubic_lines,
            cubic_labels,
        ) = (
            cubic_axis
            .get_legend_handles_labels()
        )

        lock_axis.legend(
            lock_lines
            + cubic_lines,
            lock_labels
            + cubic_labels,
            loc="best",
        )

        interface_axis.plot(
            self.x_coordinates,
            self.interface_c3,
            linewidth=2.5,
            label="C3 profile",
        )

        interface_axis.plot(
            self.x_coordinates,
            self.interface_p_cubic,
            linestyle="--",
            linewidth=2.0,
            label=(
                "Local cubic-dissipation "
                "level P_cubic"
            ),
        )

        interface_axis.fill_between(
            self.x_coordinates,
            self.interface_c3,
            self.interface_p_cubic,
            where=(
                self.interface_c3
                < self.interface_p_cubic
            ),
            alpha=0.2,
            label=(
                "Local cubic-dissipation "
                "dominance"
            ),
        )

        interface_axis.fill_between(
            self.x_coordinates,
            self.interface_c3,
            self.interface_p_cubic,
            where=(
                self.interface_c3
                >= self.interface_p_cubic
            ),
            alpha=0.2,
            label="Local C3 dominance",
        )

        for point in (
            self.cubic_transition_points
        ):
            interface_axis.axvline(
                point,
                linestyle=":",
                alpha=0.8,
            )

        interface_axis.set_title(
            "Local C3 / P_cubic Transition "
            "Across the Interface Barrier"
        )

        interface_axis.set_xlabel(
            "Spatial Transition Coordinate X"
        )

        interface_axis.set_ylabel(
            "C3 / P_cubic"
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
                0.94,
            )
        )

        if show:
            plt.show()

        return figure

    def run_visual_simulation(
        self,
        show: bool = True,
    ) -> plt.Figure:
        """
        Run the complete temporal and spatial engineering visualization.
        """
        self.simulate_temporal_dynamics(
            initial_phi=np.array(
                [
                    0.8,
                    -0.7,
                    0.5,
                ],
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
                [
                    0.1,
                    -0.1,
                    0.05,
                ],
                dtype=np.float64,
            ),
        )

        print(
            "=== MARNOV U_6D / C3 "
            "ENGINEERING VISUALIZER ==="
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
            "Initial C3: "
            f"{self.history_c3[0]:.6f}"
        )

        print(
            "Final C3: "
            f"{self.history_c3[-1]:.6f}"
        )

        print(
            "Local cubic-dissipation level "
            "P_cubic: "
            f"{self.calculate_cubic_dissipation_level():.6f}"
        )

        print(
            "System-level general endogenous "
            "structural coherence C(t): "
            f"{self.C_t:.6f}"
        )

        print(
            "System-level destabilizing "
            "pressure P(t): "
            f"{self.P_t:.6f}"
        )

        print(
            "System regime: "
            f"{self.classify_system_regime()}"
        )

        if (
            self.cubic_transition_points.size
            > 0
        ):
            formatted_points = ", ".join(
                f"{point:.4f}"
                for point in (
                    self.cubic_transition_points
                )
            )

            print(
                "Local transition coordinates "
                "C3 = P_cubic: "
                f"{formatted_points}"
            )
        else:
            print(
                "No local C3 = P_cubic "
                "transition crossing was detected."
            )

        return (
            self.visualize_engineering_data(
                show=show
            )
        )


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
        C_t=0.90,
        P_t=0.35,
        seed=42,
    )

    simulator.run_visual_simulation()
