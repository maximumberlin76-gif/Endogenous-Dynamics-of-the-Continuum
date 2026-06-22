from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


class MetricBridgeSolver:
    """
    Dynamic interface-balance solver for the EDK metric bridge.

    The solver implements the formal chain:

    J_flux
    -> exchange-flow residual R_J
    -> interface projection G_int
    -> projected energy-momentum divergence
    -> metric-deformation proxy

    Exchange-flow residual:

    R_J =
    partial_t J_flux
    + (J_flux dot grad)J_flux
    + gamma * grad(rho_cont)
    + beta * C3 * J_flux

    Flow-evolution form:

    partial_t J_flux =
    -(J_flux dot grad)J_flux
    - gamma * grad(rho_cont)
    - beta * C3 * J_flux

    Interface projection:

    partial_mu T^{mu nu} =
    G_int^{nu}_{lambda}
    * R_J^{lambda}

    The metric update implemented here is a model-specific deformation
    proxy. It is not a numerical solution of the Einstein field equations.
    """

    def __init__(
        self,
        gamma: float,
        beta: float,
        chi: float,
        critical_tolerance: float = 1e-9,
    ):
        """
        Initialize the metric-bridge solver.

        Parameters
        ----------
        gamma:
            Coupling coefficient of the background-mode density gradient.
        beta:
            Coupling coefficient of cubic retention C3.
        chi:
            Plasticity coefficient of the metric-deformation proxy.
        critical_tolerance:
            Numerical tolerance used at the boundary C(t) = P(t).
        """
        if gamma < 0.0:
            raise ValueError("gamma must be non-negative.")

        if beta < 0.0:
            raise ValueError("beta must be non-negative.")

        if chi < 0.0:
            raise ValueError("chi must be non-negative.")

        if critical_tolerance <= 0.0:
            raise ValueError(
                "critical_tolerance must be positive."
            )

        self.gamma = float(gamma)
        self.beta = float(beta)
        self.chi = float(chi)
        self.critical_tolerance = float(
            critical_tolerance
        )

    @staticmethod
    def _validate_vector(
        vector: FloatArray,
        name: str,
    ) -> FloatArray:
        """
        Validate and return a one-dimensional floating-point vector.
        """
        result = np.asarray(
            vector,
            dtype=np.float64,
        )

        if result.ndim != 1:
            raise ValueError(
                f"{name} must be a one-dimensional vector."
            )

        if result.size == 0:
            raise ValueError(
                f"{name} must not be empty."
            )

        if not np.all(np.isfinite(result)):
            raise ValueError(
                f"{name} must contain only finite values."
            )

        return result

    @staticmethod
    def _validate_square_matrix(
        matrix: FloatArray,
        name: str,
    ) -> FloatArray:
        """
        Validate and return a square floating-point matrix.
        """
        result = np.asarray(
            matrix,
            dtype=np.float64,
        )

        if result.ndim != 2:
            raise ValueError(
                f"{name} must be a two-dimensional matrix."
            )

        rows, columns = result.shape

        if rows != columns:
            raise ValueError(
                f"{name} must be square."
            )

        if rows == 0:
            raise ValueError(
                f"{name} must not be empty."
            )

        if not np.all(np.isfinite(result)):
            raise ValueError(
                f"{name} must contain only finite values."
            )

        return result

    def calculate_interface_residual(
        self,
        j_flux: FloatArray,
        grad_j_flux: FloatArray,
        grad_rho_cont: FloatArray,
        c3_potential: float,
        temporal_derivative: FloatArray | None = None,
    ) -> dict[str, FloatArray]:
        """
        Calculate the exchange-flow residual R_J.

        The Jacobian convention is:

        grad_j_flux[i, j] =
        partial J_flux[i] / partial x[j]

        Therefore:

        (J_flux dot grad)J_flux =
        grad_j_flux @ j_flux

        Parameters
        ----------
        j_flux:
            Current exchange-flow vector.
        grad_j_flux:
            Spatial Jacobian of J_flux.
        grad_rho_cont:
            Gradient of background non-resonant modes.
        c3_potential:
            Current cubic retention potential C3.
        temporal_derivative:
            Optional partial_t J_flux vector.
            If omitted, it is treated as zero.

        Returns
        -------
        dict[str, np.ndarray]:
            Individual residual components and the full residual.
        """
        j_flux = self._validate_vector(
            j_flux,
            "j_flux",
        )

        grad_rho_cont = self._validate_vector(
            grad_rho_cont,
            "grad_rho_cont",
        )

        grad_j_flux = self._validate_square_matrix(
            grad_j_flux,
            "grad_j_flux",
        )

        dimension = j_flux.size

        if grad_rho_cont.size != dimension:
            raise ValueError(
                "grad_rho_cont must have the same dimension "
                "as j_flux."
            )

        if grad_j_flux.shape != (
            dimension,
            dimension,
        ):
            raise ValueError(
                "grad_j_flux shape must be "
                "(j_flux.size, j_flux.size)."
            )

        if c3_potential < 0.0:
            raise ValueError(
                "c3_potential must be non-negative."
            )

        if temporal_derivative is None:
            temporal_term = np.zeros(
                dimension,
                dtype=np.float64,
            )
        else:
            temporal_term = self._validate_vector(
                temporal_derivative,
                "temporal_derivative",
            )

            if temporal_term.size != dimension:
                raise ValueError(
                    "temporal_derivative must have the same "
                    "dimension as j_flux."
                )

        convective_term = (
            grad_j_flux
            @ j_flux
        )

        continuum_gradient_term = (
            self.gamma
            * grad_rho_cont
        )

        cubic_retention_term = (
            self.beta
            * float(c3_potential)
            * j_flux
        )

        residual = (
            temporal_term
            + convective_term
            + continuum_gradient_term
            + cubic_retention_term
        )

        return {
            "temporal_term": temporal_term,
            "convective_term": convective_term,
            "continuum_gradient_term": continuum_gradient_term,
            "cubic_retention_term": cubic_retention_term,
            "residual": residual,
        }

    def calculate_exchange_flow_acceleration(
        self,
        j_flux: FloatArray,
        grad_j_flux: FloatArray,
        grad_rho_cont: FloatArray,
        c3_potential: float,
    ) -> FloatArray:
        """
        Calculate partial_t J_flux from the balanced flow equation.

        partial_t J_flux =
        -(J_flux dot grad)J_flux
        - gamma * grad(rho_cont)
        - beta * C3 * J_flux

        Parameters
        ----------
        j_flux:
            Current exchange-flow vector.
        grad_j_flux:
            Spatial Jacobian of J_flux.
        grad_rho_cont:
            Gradient of background modes.
        c3_potential:
            Cubic retention potential C3.

        Returns
        -------
        np.ndarray:
            Tact-by-tact change of J_flux.
        """
        components = self.calculate_interface_residual(
            j_flux=j_flux,
            grad_j_flux=grad_j_flux,
            grad_rho_cont=grad_rho_cont,
            c3_potential=c3_potential,
            temporal_derivative=None,
        )

        return -(
            components["convective_term"]
            + components["continuum_gradient_term"]
            + components["cubic_retention_term"]
        )

    @staticmethod
    def project_interface_residual(
        interface_residual: FloatArray,
        projection_operator: FloatArray,
    ) -> FloatArray:
        """
        Project the internal exchange-flow residual into the target layer.

        projected_residual =
        G_int @ R_J

        Parameters
        ----------
        interface_residual:
            Internal exchange-flow residual R_J.
        projection_operator:
            Interface operator G_int.

            Expected shape:

            target_dimension × flow_dimension

        Returns
        -------
        np.ndarray:
            Projected residual in the target layer.
        """
        interface_residual = np.asarray(
            interface_residual,
            dtype=np.float64,
        )

        projection_operator = np.asarray(
            projection_operator,
            dtype=np.float64,
        )

        if interface_residual.ndim != 1:
            raise ValueError(
                "interface_residual must be a vector."
            )

        if projection_operator.ndim != 2:
            raise ValueError(
                "projection_operator must be a matrix."
            )

        if projection_operator.shape[1] != (
            interface_residual.size
        ):
            raise ValueError(
                "projection_operator input dimension must match "
                "interface_residual dimension."
            )

        if not np.all(
            np.isfinite(projection_operator)
        ):
            raise ValueError(
                "projection_operator must contain only finite values."
            )

        return (
            projection_operator
            @ interface_residual
        )

    def classify_dynamic_regime(
        self,
        endogenous_coherence: float,
        external_pressure: float,
    ) -> str:
        """
        Classify the current EDS / EDC dynamic regime.

        Parameters
        ----------
        endogenous_coherence:
            General endogenous structural coherence C(t).
        external_pressure:
            Environmental pressure P(t).

        Returns
        -------
        str:
            Current dynamic regime.
        """
        if endogenous_coherence < 0.0:
            raise ValueError(
                "endogenous_coherence must be non-negative."
            )

        if external_pressure < 0.0:
            raise ValueError(
                "external_pressure must be non-negative."
            )

        difference = (
            endogenous_coherence
            - external_pressure
        )

        if difference > self.critical_tolerance:
            return "EDS_RETENTION"

        if abs(difference) <= self.critical_tolerance:
            return "EDC_CRITICAL_BOUNDARY"

        return "INVERSE_DISSIPATIVE_CASCADE"

    def recompute_4d_metric(
        self,
        g_mu_nu: FloatArray,
        interface_residual: FloatArray,
        projection_operator: FloatArray,
        endogenous_coherence: float,
        external_pressure: float,
        dt: float = 1.0,
    ) -> dict[str, FloatArray | float | str]:
        """
        Recompute the local metric-deformation proxy.

        The method does not replace the energy-momentum tensor with the
        metric tensor.

        It uses:

        - g_mu_nu as the current metric;
        - G_int @ R_J as the projected interface residual;
        - C(t) and P(t) as the EDS / EDC regime criterion.

        In the retained regime:

        C(t) > P(t)

        the metric is preserved.

        At criticality or during the inverse dissipative cascade:

        C(t) <= P(t)

        the model calculates:

        delta_g_mu_nu =
        chi
        * severity
        * outer(projected_residual, projected_residual)
        * dt

        Parameters
        ----------
        g_mu_nu:
            Current square metric tensor.
        interface_residual:
            Internal exchange-flow residual R_J.
        projection_operator:
            Interface projection operator G_int.
        endogenous_coherence:
            General endogenous structural coherence C(t).
        external_pressure:
            Environmental pressure P(t).
        dt:
            Discrete metric-update interval.

        Returns
        -------
        dict[str, np.ndarray | float | str]:
            Regime, projected residual, metric deformation,
            updated metric, and deformation severity.
        """
        if dt <= 0.0:
            raise ValueError("dt must be positive.")

        g_mu_nu = self._validate_square_matrix(
            g_mu_nu,
            "g_mu_nu",
        )

        regime = self.classify_dynamic_regime(
            endogenous_coherence=endogenous_coherence,
            external_pressure=external_pressure,
        )

        projected_residual = (
            self.project_interface_residual(
                interface_residual=interface_residual,
                projection_operator=projection_operator,
            )
        )

        metric_dimension = g_mu_nu.shape[0]

        if projected_residual.size != metric_dimension:
            raise ValueError(
                "The projected residual dimension must match "
                "the metric dimension."
            )

        if regime == "EDS_RETENTION":
            deformation_severity = 0.0

            delta_g_mu_nu = np.zeros_like(
                g_mu_nu,
                dtype=np.float64,
            )

            updated_metric = g_mu_nu.copy()

        else:
            pressure_scale = max(
                abs(external_pressure),
                self.critical_tolerance,
            )

            if regime == "EDC_CRITICAL_BOUNDARY":
                deformation_severity = 1.0
            else:
                deformation_severity = (
                    1.0
                    + (
                        external_pressure
                        - endogenous_coherence
                    )
                    / pressure_scale
                )

            delta_g_mu_nu = (
                self.chi
                * deformation_severity
                * np.outer(
                    projected_residual,
                    projected_residual,
                )
                * dt
            )

            delta_g_mu_nu = 0.5 * (
                delta_g_mu_nu
                + delta_g_mu_nu.T
            )

            updated_metric = (
                g_mu_nu
                + delta_g_mu_nu
            )

        return {
            "regime": regime,
            "projected_residual": projected_residual,
            "metric_deformation": delta_g_mu_nu,
            "updated_metric": updated_metric,
            "deformation_severity": float(
                deformation_severity
            ),
        }


if __name__ == "__main__":
    solver = MetricBridgeSolver(
        gamma=0.4,
        beta=0.8,
        chi=0.05,
    )

    j_flux = np.array(
        [0.30, -0.10, 0.20],
        dtype=np.float64,
    )

    grad_j_flux = np.array(
        [
            [0.10, 0.02, 0.00],
            [0.01, -0.04, 0.03],
            [0.00, 0.02, 0.05],
        ],
        dtype=np.float64,
    )

    grad_rho_cont = np.array(
        [0.05, -0.02, 0.01],
        dtype=np.float64,
    )

    c3_potential = 1.4

    flow_acceleration = (
        solver.calculate_exchange_flow_acceleration(
            j_flux=j_flux,
            grad_j_flux=grad_j_flux,
            grad_rho_cont=grad_rho_cont,
            c3_potential=c3_potential,
        )
    )

    residual_components = (
        solver.calculate_interface_residual(
            j_flux=j_flux,
            grad_j_flux=grad_j_flux,
            grad_rho_cont=grad_rho_cont,
            c3_potential=c3_potential,
            temporal_derivative=flow_acceleration,
        )
    )

    projection_operator = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.3, 0.3, 0.4],
        ],
        dtype=np.float64,
    )

    g_mu_nu = np.diag(
        [-1.0, 1.0, 1.0, 1.0]
    ).astype(np.float64)

    metric_state = solver.recompute_4d_metric(
        g_mu_nu=g_mu_nu,
        interface_residual=residual_components["residual"],
        projection_operator=projection_operator,
        endogenous_coherence=0.7,
        external_pressure=1.0,
        dt=0.05,
    )

    print("=== METRIC BRIDGE SOLVER ===")

    print(
        "Exchange-flow acceleration:",
        flow_acceleration,
    )

    print(
        "Interface residual:",
        residual_components["residual"],
    )

    print(
        "Dynamic regime:",
        metric_state["regime"],
    )

    print(
        "Projected residual:",
        metric_state["projected_residual"],
    )

    print(
        "Metric deformation:"
    )

    print(
        metric_state["metric_deformation"]
    )

    print(
        "Updated metric:"
    )

    print(
        metric_state["updated_metric"]
    )
