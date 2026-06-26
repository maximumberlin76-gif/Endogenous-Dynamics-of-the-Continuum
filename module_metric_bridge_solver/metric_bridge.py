from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]


class MetricBridgeSolver:
    """
    Dynamic interface-balance solver for the EDK metric bridge.

    The solver implements the computational chain:

    J_flux
    -> spatial Jacobian grad_J_flux
    -> convective transport
    -> background-mode gradient
    -> cubic retention C3
    -> exchange-flow residual R_J
    -> interface projection G_int
    -> projected residual
    -> EDS / EDC regime classification
    -> retained metric or metric-deformation proxy
    """

    EDS_RETENTION = "EDS_RETENTION"
    EDC_CRITICAL_BOUNDARY = "EDC_CRITICAL_BOUNDARY"
    INVERSE_DISSIPATIVE_CASCADE = "INVERSE_DISSIPATIVE_CASCADE"

    def __init__(
        self,
        gamma: float = 0.4,
        beta: float = 0.8,
        chi: float = 0.05,
        critical_tolerance: float = 1.0e-9,
    ) -> None:
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
            Numerical tolerance at the boundary C(t) = P(t).
        """
        self.gamma = self._non_negative_finite("gamma", gamma)
        self.beta = self._non_negative_finite("beta", beta)
        self.chi = self._non_negative_finite("chi", chi)
        self.critical_tolerance = self._positive_finite(
            "critical_tolerance",
            critical_tolerance,
        )

    @staticmethod
    def _finite_scalar(
        name: str,
        value: float,
    ) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _positive_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    @classmethod
    def _non_negative_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")

        return scalar

    @staticmethod
    def _validate_vector(
        vector: FloatArray,
        name: str,
    ) -> FloatArray:
        """
        Validate and return a one-dimensional finite vector.
        """
        result = np.asarray(
            vector,
            dtype=np.float64,
        )

        if result.ndim != 1:
            raise ValueError(f"{name} must be a one-dimensional vector.")

        if result.size == 0:
            raise ValueError(f"{name} must not be empty.")

        if not np.all(np.isfinite(result)):
            raise ValueError(f"{name} must contain only finite values.")

        return result

    @staticmethod
    def _validate_square_matrix(
        matrix: FloatArray,
        name: str,
    ) -> FloatArray:
        """
        Validate and return a square finite matrix.
        """
        result = np.asarray(
            matrix,
            dtype=np.float64,
        )

        if result.ndim != 2:
            raise ValueError(f"{name} must be a two-dimensional matrix.")

        rows, columns = result.shape

        if rows != columns:
            raise ValueError(f"{name} must be square.")

        if rows == 0:
            raise ValueError(f"{name} must not be empty.")

        if not np.all(np.isfinite(result)):
            raise ValueError(f"{name} must contain only finite values.")

        return result

    @staticmethod
    def _validate_projection_operator(
        projection_operator: FloatArray,
        flow_dimension: int,
    ) -> FloatArray:
        """
        Validate the interface projection operator G_int.
        """
        operator = np.asarray(
            projection_operator,
            dtype=np.float64,
        )

        if operator.ndim != 2:
            raise ValueError("projection_operator must be a matrix.")

        if operator.shape[0] == 0:
            raise ValueError("projection_operator must have output rows.")

        if operator.shape[1] != flow_dimension:
            raise ValueError(
                "projection_operator input dimension must match "
                "interface_residual dimension."
            )

        if not np.all(np.isfinite(operator)):
            raise ValueError(
                "projection_operator must contain only finite values."
            )

        return operator

    def _resolve_c_p_values(
        self,
        C_t: float | None,
        P_t: float | None,
        endogenous_coherence: float | None,
        external_pressure: float | None,
    ) -> tuple[float, float]:
        """
        Resolve current C(t) and P(t) values from new and legacy names.
        """
        if C_t is None:
            C_t = endogenous_coherence

        if P_t is None:
            P_t = external_pressure

        if C_t is None:
            raise ValueError("C_t must be provided.")

        if P_t is None:
            raise ValueError("P_t must be provided.")

        C_value = self._non_negative_finite("C_t", C_t)
        P_value = self._non_negative_finite("P_t", P_t)

        return C_value, P_value

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

        grad_j_flux[i, j] = partial J_flux[i] / partial x[j]

        Therefore:

        (J_flux · grad)J_flux = grad_j_flux @ j_flux
        """
        j_flux = self._validate_vector(j_flux, "j_flux")
        grad_rho_cont = self._validate_vector(grad_rho_cont, "grad_rho_cont")
        grad_j_flux = self._validate_square_matrix(grad_j_flux, "grad_j_flux")
        c3_value = self._non_negative_finite("c3_potential", c3_potential)

        dimension = j_flux.size

        if grad_rho_cont.size != dimension:
            raise ValueError(
                "grad_rho_cont must have the same dimension as j_flux."
            )

        if grad_j_flux.shape != (dimension, dimension):
            raise ValueError(
                "grad_j_flux shape must be (j_flux.size, j_flux.size)."
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
                    "temporal_derivative must have the same dimension "
                    "as j_flux."
                )

        convective_term = grad_j_flux @ j_flux

        continuum_gradient_term = self.gamma * grad_rho_cont

        cubic_retention_term = self.beta * c3_value * j_flux

        residual = (
            temporal_term
            + convective_term
            + continuum_gradient_term
            + cubic_retention_term
        )

        components = {
            "temporal_term": temporal_term,
            "convective_term": convective_term,
            "continuum_gradient_term": continuum_gradient_term,
            "cubic_retention_term": cubic_retention_term,
            "residual": residual,
        }

        for name, value in components.items():
            if not np.all(np.isfinite(value)):
                raise FloatingPointError(f"{name} contains non-finite values.")

        return components

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
        -(J_flux · grad)J_flux
        - gamma · grad rho_cont
        - beta · C3 · J_flux
        """
        components = self.calculate_interface_residual(
            j_flux=j_flux,
            grad_j_flux=grad_j_flux,
            grad_rho_cont=grad_rho_cont,
            c3_potential=c3_potential,
            temporal_derivative=None,
        )

        acceleration = -(
            components["convective_term"]
            + components["continuum_gradient_term"]
            + components["cubic_retention_term"]
        )

        if not np.all(np.isfinite(acceleration)):
            raise FloatingPointError(
                "exchange-flow acceleration contains non-finite values."
            )

        return acceleration

    @staticmethod
    def project_interface_residual(
        interface_residual: FloatArray,
        projection_operator: FloatArray,
    ) -> FloatArray:
        """
        Project the internal exchange-flow residual into the target layer.

        projected_residual = G_int @ R_J
        """
        residual = np.asarray(
            interface_residual,
            dtype=np.float64,
        )

        if residual.ndim != 1:
            raise ValueError("interface_residual must be a vector.")

        if residual.size == 0:
            raise ValueError("interface_residual must not be empty.")

        if not np.all(np.isfinite(residual)):
            raise ValueError(
                "interface_residual must contain only finite values."
            )

        operator = MetricBridgeSolver._validate_projection_operator(
            projection_operator,
            residual.size,
        )

        projected_residual = operator @ residual

        if not np.all(np.isfinite(projected_residual)):
            raise FloatingPointError(
                "projected_residual contains non-finite values."
            )

        return projected_residual

    def classify_dynamic_regime(
        self,
        C_t: float | None = None,
        P_t: float | None = None,
        *,
        endogenous_coherence: float | None = None,
        external_pressure: float | None = None,
    ) -> str:
        """
        Classify the current EDS / EDC dynamic regime.
        """
        C_value, P_value = self._resolve_c_p_values(
            C_t=C_t,
            P_t=P_t,
            endogenous_coherence=endogenous_coherence,
            external_pressure=external_pressure,
        )

        difference = C_value - P_value

        if difference > self.critical_tolerance:
            return self.EDS_RETENTION

        if abs(difference) <= self.critical_tolerance:
            return self.EDC_CRITICAL_BOUNDARY

        return self.INVERSE_DISSIPATIVE_CASCADE

    def recompute_4d_metric(
        self,
        g_mu_nu: FloatArray,
        interface_residual: FloatArray,
        projection_operator: FloatArray,
        C_t: float | None = None,
        P_t: float | None = None,
        dt: float = 1.0,
        *,
        endogenous_coherence: float | None = None,
        external_pressure: float | None = None,
    ) -> dict[str, FloatArray | float | str]:
        """
        Recompute the local metric-deformation proxy.

        In the retained regime C(t) > P(t), the current metric is preserved.

        At criticality or during the inverse dissipative cascade, the method
        calculates:

        delta_g_mu_nu =
        chi · severity · outer(projected_residual, projected_residual) · dt
        """
        dt = self._positive_finite("dt", dt)

        C_value, P_value = self._resolve_c_p_values(
            C_t=C_t,
            P_t=P_t,
            endogenous_coherence=endogenous_coherence,
            external_pressure=external_pressure,
        )

        g_mu_nu = self._validate_square_matrix(g_mu_nu, "g_mu_nu")

        regime = self.classify_dynamic_regime(
            C_t=C_value,
            P_t=P_value,
        )

        projected_residual = self.project_interface_residual(
            interface_residual=interface_residual,
            projection_operator=projection_operator,
        )

        metric_dimension = g_mu_nu.shape[0]

        if projected_residual.size != metric_dimension:
            raise ValueError(
                "The projected residual dimension must match the metric dimension."
            )

        if regime == self.EDS_RETENTION:
            deformation_severity = 0.0
            delta_g_mu_nu = np.zeros_like(g_mu_nu, dtype=np.float64)
            updated_metric = g_mu_nu.copy()
        else:
            pressure_scale = max(
                abs(P_value),
                self.critical_tolerance,
            )

            if regime == self.EDC_CRITICAL_BOUNDARY:
                deformation_severity = 1.0
            else:
                deformation_severity = 1.0 + (P_value - C_value) / pressure_scale

            delta_g_mu_nu = (
                self.chi
                * deformation_severity
                * np.outer(projected_residual, projected_residual)
                * dt
            )

            delta_g_mu_nu = 0.5 * (delta_g_mu_nu + delta_g_mu_nu.T)
            updated_metric = g_mu_nu + delta_g_mu_nu

        outputs = {
            "projected_residual": projected_residual,
            "metric_deformation": delta_g_mu_nu,
            "updated_metric": updated_metric,
        }

        for name, value in outputs.items():
            if not np.all(np.isfinite(value)):
                raise FloatingPointError(f"{name} contains non-finite values.")

        return {
            "regime": regime,
            "projected_residual": projected_residual,
            "metric_deformation": delta_g_mu_nu,
            "updated_metric": updated_metric,
            "deformation_severity": float(deformation_severity),
            "C_t": float(C_value),
            "P_t": float(P_value),
        }


def run_demo() -> None:
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

    flow_acceleration = solver.calculate_exchange_flow_acceleration(
        j_flux=j_flux,
        grad_j_flux=grad_j_flux,
        grad_rho_cont=grad_rho_cont,
        c3_potential=c3_potential,
    )

    residual_components = solver.calculate_interface_residual(
        j_flux=j_flux,
        grad_j_flux=grad_j_flux,
        grad_rho_cont=grad_rho_cont,
        c3_potential=c3_potential,
        temporal_derivative=flow_acceleration,
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

    g_mu_nu = np.diag([-1.0, 1.0, 1.0, 1.0]).astype(np.float64)

    metric_state = solver.recompute_4d_metric(
        g_mu_nu=g_mu_nu,
        interface_residual=residual_components["residual"],
        projection_operator=projection_operator,
        C_t=0.7,
        P_t=1.0,
        dt=0.05,
    )

    print("=== METRIC BRIDGE SOLVER ===")
    print("Exchange-flow acceleration:", flow_acceleration)
    print("Interface residual:", residual_components["residual"])
    print("Dynamic regime:", metric_state["regime"])
    print("Projected residual:", metric_state["projected_residual"])
    print("Metric deformation:")
    print(metric_state["metric_deformation"])
    print("Updated metric:")
    print(metric_state["updated_metric"])


if __name__ == "__main__":
    run_demo()
