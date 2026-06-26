from __future__ import annotations

import numpy as np


class SolarSynthesisResonator:
    """
    Conceptual macro-scale solar layer of the EDK software architecture.

    The implementation keeps the following states independent:

    R_t != C(t)
    current_dissipation_flux != accumulated_dissipation
    macro_light_flux != J_flux
    dynamic retention != frozen state

    R_t is a phase synchronization indicator calculated from the plasma
    phases. C_t is the independently supplied general endogenous structural
    coherence. macro_light_flux is the local output of this solar module and
    is not the through massless channel J_flux.
    """

    STABLE_APPEARANCE = "STABLE SOLAR APPEARANCE"
    PARTIAL_APPEARANCE = "PARTIAL SOLAR APPEARANCE"
    WEAK_APPEARANCE = "WEAK OR UNSTABLE SOLAR APPEARANCE"

    RETAINED_SYNTHESIS = "DYNAMICALLY RETAINED SYNTHESIS REGIME"
    TRANSITIONAL_SYNTHESIS = "TRANSITIONAL SYNTHESIS REGIME"
    UNRETAINED_PLASMA = "UNRETAINED FLUCTUATING PLASMA REGIME"
    EDC_BOUNDARY = "ENDOGENOUS DYNAMIC CRITICALITY"
    DEGRADATION_DRIFT = "DEGRADATION DRIFT"

    def __init__(
        self,
        num_plasma_domains: int = 64,
        coupling_strength_k: float = 45.0,
        C_t: float = 0.90,
        P_t: float = 0.35,
        initial_omega: float = 0.0,
        amplitude_min: float = 10.0,
        amplitude_max: float = 2000.0,
        amplitude_baseline: float = 550.0,
        amplitude_relaxation: float = 0.08,
        forcing_amplitude_gain: float = 2.0,
        amplitude_noise_strength: float = 50.0,
        forcing_phase_gain: float = 0.08,
        phase_noise_strength: float = 0.02,
        amplitude_dissipation_coefficient: float = 0.01,
        pressure_dissipation_coefficient: float = 0.5,
        mismatch_dissipation_coefficient: float = 0.02,
        structural_input_coefficient: float = 0.08,
        omega_coherence_gain: float = 8.0,
        omega_work_gain: float = 0.02,
        omega_decay: float = 0.25,
        omega_threshold: float = 0.25,
        work_threshold: float = 0.50,
        phase_support_threshold: float = 0.50,
        radiation_efficiency: float = 0.85,
        critical_tolerance: float = 1.0e-12,
        seed: int | None = None,
    ) -> None:
        """Initialize the solar synthesis resonator."""
        if isinstance(num_plasma_domains, bool):
            raise ValueError("num_plasma_domains must be an integer.")

        try:
            converted_domains = int(num_plasma_domains)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                "num_plasma_domains must be an integer."
            ) from exc

        if converted_domains != num_plasma_domains:
            raise ValueError("num_plasma_domains must be an integer.")

        if converted_domains <= 0:
            raise ValueError("num_plasma_domains must be positive.")

        self.num_domains = converted_domains

        self.K = self._non_negative_finite(
            "coupling_strength_k",
            coupling_strength_k,
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

        self.Omega_t = self._bounded_finite(
            "initial_omega",
            initial_omega,
            0.0,
            1.0,
        )

        self.amplitude_min = self._positive_finite(
            "amplitude_min",
            amplitude_min,
        )

        self.amplitude_max = self._positive_finite(
            "amplitude_max",
            amplitude_max,
        )

        if self.amplitude_max <= self.amplitude_min:
            raise ValueError(
                "amplitude_max must be greater than amplitude_min."
            )

        self.amplitude_baseline = self._bounded_finite(
            "amplitude_baseline",
            amplitude_baseline,
            self.amplitude_min,
            self.amplitude_max,
        )

        self.amplitude_relaxation = self._non_negative_finite(
            "amplitude_relaxation",
            amplitude_relaxation,
        )

        self.forcing_amplitude_gain = self._non_negative_finite(
            "forcing_amplitude_gain",
            forcing_amplitude_gain,
        )

        self.amplitude_noise_strength = self._non_negative_finite(
            "amplitude_noise_strength",
            amplitude_noise_strength,
        )

        self.forcing_phase_gain = self._non_negative_finite(
            "forcing_phase_gain",
            forcing_phase_gain,
        )

        self.phase_noise_strength = self._non_negative_finite(
            "phase_noise_strength",
            phase_noise_strength,
        )

        self.amplitude_dissipation_coefficient = (
            self._non_negative_finite(
                "amplitude_dissipation_coefficient",
                amplitude_dissipation_coefficient,
            )
        )

        self.pressure_dissipation_coefficient = (
            self._non_negative_finite(
                "pressure_dissipation_coefficient",
                pressure_dissipation_coefficient,
            )
        )

        self.mismatch_dissipation_coefficient = (
            self._non_negative_finite(
                "mismatch_dissipation_coefficient",
                mismatch_dissipation_coefficient,
            )
        )

        self.structural_input_coefficient = (
            self._non_negative_finite(
                "structural_input_coefficient",
                structural_input_coefficient,
            )
        )

        self.omega_coherence_gain = self._non_negative_finite(
            "omega_coherence_gain",
            omega_coherence_gain,
        )

        self.omega_work_gain = self._non_negative_finite(
            "omega_work_gain",
            omega_work_gain,
        )

        self.omega_decay = self._non_negative_finite(
            "omega_decay",
            omega_decay,
        )

        self.omega_threshold = self._bounded_finite(
            "omega_threshold",
            omega_threshold,
            0.0,
            1.0,
        )

        self.work_threshold = self._non_negative_finite(
            "work_threshold",
            work_threshold,
        )

        self.phase_support_threshold = self._bounded_finite(
            "phase_support_threshold",
            phase_support_threshold,
            0.0,
            1.0,
        )

        self.radiation_efficiency = self._non_negative_finite(
            "radiation_efficiency",
            radiation_efficiency,
        )

        self.critical_tolerance = self._non_negative_finite(
            "critical_tolerance",
            critical_tolerance,
        )

        self.rng = np.random.default_rng(seed)

        self.plasma_amplitudes = self.rng.uniform(
            self.amplitude_min,
            self.amplitude_max,
            self.num_domains,
        ).astype(np.float64)

        self.plasma_phases = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            self.num_domains,
        ).astype(np.float64)

        self.R_t = self.calculate_phase_synchronization()

        self.mean_plasma_amplitude = float(
            np.mean(self.plasma_amplitudes)
        )

        self.positive_structural_work_rate = 0.0
        self.accumulated_positive_structural_work = 0.0
        self.current_dissipation_flux = 0.0
        self.accumulated_dissipation = 0.0
        self.macro_light_flux = 0.0
        self.synthesis_window_open = False
        self.appearance_index = 0.0
        self.tact_index = 0

        # Backward-compatible aliases used by earlier repository layers.
        self.accumulated_work = 0.0
        self.total_dissipation_flux = 0.0

        self._validate_complete_state()

    @staticmethod
    def _finite_scalar(
        name: str,
        value: float,
    ) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"{name} must be a finite scalar."
            ) from exc

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
                f"{name} must be within [{lower}, {upper}]."
            )

        return scalar

    def set_system_state(
        self,
        C_t: float,
        P_t: float,
    ) -> None:
        """Set the independent system-level values C(t) and P(t)."""
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

    def calculate_phase_synchronization(self) -> float:
        """
        Calculate the Kuramoto-type phase synchronization indicator R_t.
        """
        if self.plasma_phases.shape != (self.num_domains,):
            raise RuntimeError(
                "plasma_phases has an invalid shape."
            )

        if not np.all(
            np.isfinite(self.plasma_phases)
        ):
            raise FloatingPointError(
                "plasma_phases contains non-finite values."
            )

        order_parameter = np.mean(
            np.exp(
                1j * self.plasma_phases
            )
        )

        R_t = float(
            np.clip(
                abs(order_parameter),
                0.0,
                1.0,
            )
        )

        if not np.isfinite(R_t):
            raise FloatingPointError(
                "R_t became non-finite."
            )

        return R_t

    def _update_plasma_amplitudes(
        self,
        external_forcing_density: float,
        dt: float,
    ) -> None:
        target_amplitude = np.clip(
            self.amplitude_baseline
            + self.forcing_amplitude_gain
            * external_forcing_density,
            self.amplitude_min,
            self.amplitude_max,
        )

        amplitude_drive = self.amplitude_relaxation * (
            target_amplitude
            - self.plasma_amplitudes
        )

        amplitude_noise = self.rng.normal(
            loc=0.0,
            scale=(
                self.amplitude_noise_strength
                * np.sqrt(dt)
            ),
            size=self.num_domains,
        )

        self.plasma_amplitudes = np.clip(
            self.plasma_amplitudes
            + dt * amplitude_drive
            + amplitude_noise,
            self.amplitude_min,
            self.amplitude_max,
        )

    def _update_plasma_phases(
        self,
        external_forcing_density: float,
        dt: float,
    ) -> None:
        phase_difference = (
            self.plasma_phases[None, :]
            - self.plasma_phases[:, None]
        )

        phase_coupling = (
            self.K
            * np.sum(
                np.sin(phase_difference),
                axis=1,
            )
            / self.num_domains
        )

        external_phase_drive = (
            -self.forcing_phase_gain
            * external_forcing_density
            * np.sin(self.plasma_phases)
        )

        phase_noise = self.rng.normal(
            loc=0.0,
            scale=(
                self.phase_noise_strength
                * np.sqrt(dt)
            ),
            size=self.num_domains,
        )

        self.plasma_phases = (
            self.plasma_phases
            + dt
            * (
                phase_coupling
                + external_phase_drive
            )
            + phase_noise
        ) % (
            2.0 * np.pi
        )

    def _calculate_current_dissipation_flux(
        self,
    ) -> float:
        amplitude_dissipation = (
            self.amplitude_dissipation_coefficient
            * self.mean_plasma_amplitude
        )

        pressure_dissipation = (
            self.pressure_dissipation_coefficient
            * self.P_t
        )

        mismatch_dissipation = (
            self.mismatch_dissipation_coefficient
            * (
                1.0
                - self.R_t
            )
            * self.mean_plasma_amplitude
        )

        current_flux = (
            amplitude_dissipation
            + pressure_dissipation
            + mismatch_dissipation
        )

        return self._non_negative_finite(
            "current_dissipation_flux",
            current_flux,
        )

    def _calculate_positive_structural_work_rate(
        self,
        external_forcing_density: float,
    ) -> float:
        forcing_factor = (
            1.0
            + np.log1p(
                external_forcing_density
            )
        )

        structural_input_rate = (
            self.structural_input_coefficient
            * self.mean_plasma_amplitude
            * self.C_t
            * self.R_t
            * forcing_factor
        )

        work_rate = max(
            structural_input_rate
            - self.current_dissipation_flux,
            0.0,
        )

        return self._non_negative_finite(
            "positive_structural_work_rate",
            work_rate,
        )

    def _update_phase_transition_window(
        self,
        dt: float,
    ) -> None:
        coherence_margin = max(
            self.C_t
            - self.P_t,
            0.0,
        )

        window_drive = (
            self.omega_coherence_gain
            * coherence_margin
            + self.omega_work_gain
            * self.positive_structural_work_rate
            - self.omega_decay
            * self.Omega_t
        )

        self.Omega_t = float(
            np.clip(
                self.Omega_t
                + dt
                * window_drive,
                0.0,
                1.0,
            )
        )

    def _update_synthesis_window_state(
        self,
    ) -> None:
        self.synthesis_window_open = bool(
            self.C_t
            > self.P_t
            and self.Omega_t
            >= self.omega_threshold
            and self.accumulated_positive_structural_work
            >= self.work_threshold
            and self.R_t
            >= self.phase_support_threshold
        )

    def _calculate_macro_light_flux(
        self,
    ) -> float:
        if self.synthesis_window_open:
            window_factor = (
                1.0
                + self.Omega_t
            )
        else:
            window_factor = max(
                self.Omega_t,
                0.05,
            )

        macro_light_flux = (
            self.radiation_efficiency
            * self.current_dissipation_flux
            * window_factor
        )

        return self._non_negative_finite(
            "macro_light_flux",
            macro_light_flux,
        )

    def _calculate_appearance_index(
        self,
    ) -> float:
        appearance_index = (
            self.C_t
            * self.R_t
            * np.log1p(
                self.mean_plasma_amplitude
            )
            * np.log1p(
                self.macro_light_flux
            )
            * (
                1.0
                + self.Omega_t
            )
        )

        return self._non_negative_finite(
            "appearance_index",
            appearance_index,
        )

    def process_micro_interval(
        self,
        external_forcing_density: float,
        dt: float = 0.005,
    ) -> float:
        """
        Process one complete tact of solar computational dynamics.

        Returns
        -------
        float
            Phase synchronization indicator R_t.
        """
        external_forcing_density = (
            self._non_negative_finite(
                "external_forcing_density",
                external_forcing_density,
            )
        )

        dt = self._positive_finite(
            "dt",
            dt,
        )

        self.K = self._non_negative_finite(
            "K",
            self.K,
        )

        self._update_plasma_amplitudes(
            external_forcing_density,
            dt,
        )

        self._update_plasma_phases(
            external_forcing_density,
            dt,
        )

        self.mean_plasma_amplitude = float(
            np.mean(
                self.plasma_amplitudes
            )
        )

        self.R_t = (
            self.calculate_phase_synchronization()
        )

        self.current_dissipation_flux = (
            self._calculate_current_dissipation_flux()
        )

        self.positive_structural_work_rate = (
            self._calculate_positive_structural_work_rate(
                external_forcing_density
            )
        )

        self.accumulated_positive_structural_work += (
            dt
            * self.positive_structural_work_rate
        )

        self.accumulated_dissipation += (
            dt
            * self.current_dissipation_flux
        )

        self._update_phase_transition_window(
            dt
        )

        self._update_synthesis_window_state()

        self.macro_light_flux = (
            self._calculate_macro_light_flux()
        )

        self.appearance_index = (
            self._calculate_appearance_index()
        )

        self.tact_index += 1

        # Backward-compatible aliases.
        self.accumulated_work = (
            self.accumulated_positive_structural_work
        )

        self.total_dissipation_flux = (
            self.macro_light_flux
        )

        self._validate_complete_state()

        return self.R_t

    def calculate_solar_appearance(
        self,
    ) -> dict[str, float | str | bool]:
        """
        Return the current diagnostic solar appearance state.
        """
        if self.appearance_index >= 8.0:
            brightness_regime = (
                self.STABLE_APPEARANCE
            )
        elif self.appearance_index >= 3.0:
            brightness_regime = (
                self.PARTIAL_APPEARANCE
            )
        else:
            brightness_regime = (
                self.WEAK_APPEARANCE
            )

        return {
            "appearance_index": float(
                self.appearance_index
            ),
            "brightness_regime": brightness_regime,
            "phase_status": self.get_dynamic_status(),
            "R_t": float(self.R_t),
            "C_t": float(self.C_t),
            "P_t": float(self.P_t),
            "Omega_t": float(self.Omega_t),
            "macro_light_flux": float(
                self.macro_light_flux
            ),
            "synthesis_window_open": bool(
                self.synthesis_window_open
            ),
        }

    def get_dynamic_status(
        self,
    ) -> str:
        """
        Return the current dynamic system status.
        """
        margin = (
            self.C_t
            - self.P_t
        )

        if margin < -self.critical_tolerance:
            return self.DEGRADATION_DRIFT

        if abs(margin) <= self.critical_tolerance:
            return self.EDC_BOUNDARY

        if self.synthesis_window_open:
            return self.RETAINED_SYNTHESIS

        if (
            self.Omega_t > 0.0
            or self.accumulated_positive_structural_work
            > 0.0
        ):
            return self.TRANSITIONAL_SYNTHESIS

        return self.UNRETAINED_PLASMA

    def check_system_freeze_status(
        self,
    ) -> str:
        """
        Backward-compatible alias returning a dynamic status.

        The method name is retained for compatibility only. The returned
        status never describes the system as frozen.
        """
        return self.get_dynamic_status()

    def _validate_complete_state(
        self,
    ) -> None:
        arrays = {
            "plasma_amplitudes": (
                self.plasma_amplitudes
            ),
            "plasma_phases": (
                self.plasma_phases
            ),
        }

        for name, values in arrays.items():
            if not np.all(
                np.isfinite(values)
            ):
                raise FloatingPointError(
                    f"{name} contains non-finite values."
                )

        if self.plasma_amplitudes.shape != (
            self.num_domains,
        ):
            raise RuntimeError(
                "plasma_amplitudes has an invalid shape."
            )

        if self.plasma_phases.shape != (
            self.num_domains,
        ):
            raise RuntimeError(
                "plasma_phases has an invalid shape."
            )

        scalar_state = {
            "K": self.K,
            "C_t": self.C_t,
            "P_t": self.P_t,
            "Omega_t": self.Omega_t,
            "R_t": self.R_t,
            "mean_plasma_amplitude": (
                self.mean_plasma_amplitude
            ),
            "positive_structural_work_rate": (
                self.positive_structural_work_rate
            ),
            "accumulated_positive_structural_work": (
                self.accumulated_positive_structural_work
            ),
            "current_dissipation_flux": (
                self.current_dissipation_flux
            ),
            "accumulated_dissipation": (
                self.accumulated_dissipation
            ),
            "macro_light_flux": (
                self.macro_light_flux
            ),
            "appearance_index": (
                self.appearance_index
            ),
        }

        for name, value in scalar_state.items():
            if not np.isfinite(value):
                raise FloatingPointError(
                    f"{name} is non-finite."
                )

        if not 0.0 <= self.C_t <= 1.0:
            raise RuntimeError(
                "C_t left the interval [0, 1]."
            )

        if self.P_t < 0.0:
            raise RuntimeError(
                "P_t became negative."
            )

        if not 0.0 <= self.Omega_t <= 1.0:
            raise RuntimeError(
                "Omega_t left the interval [0, 1]."
            )

        if not 0.0 <= self.R_t <= 1.0:
            raise RuntimeError(
                "R_t left the interval [0, 1]."
            )

        non_negative_fields = (
            self.positive_structural_work_rate,
            self.accumulated_positive_structural_work,
            self.current_dissipation_flux,
            self.accumulated_dissipation,
            self.macro_light_flux,
            self.appearance_index,
        )

        if any(
            value < 0.0
            for value in non_negative_fields
        ):
            raise RuntimeError(
                "A non-negative state field became negative."
            )


if __name__ == "__main__":
    sun = SolarSynthesisResonator(
        num_plasma_domains=128,
        coupling_strength_k=80.0,
        C_t=0.90,
        P_t=0.35,
        seed=42,
    )

    print(
        "=== SOLAR SYNTHESIS RESONATOR ==="
    )

    for tact_index in range(
        1,
        13,
    ):
        R_t = sun.process_micro_interval(
            external_forcing_density=8.0,
            dt=0.005,
        )

        appearance_state = (
            sun.calculate_solar_appearance()
        )

        print(
            f"Tact {tact_index:02d} | "
            f"R_t={R_t:.5f} | "
            f"C_t={sun.C_t:.5f} | "
            f"P_t={sun.P_t:.5f} | "
            f"Omega_t={sun.Omega_t:.5f} | "
            f"A_mean={sun.mean_plasma_amplitude:.2f} | "
            f"W_rate={sun.positive_structural_work_rate:.5f} | "
            f"W_acc="
            f"{sun.accumulated_positive_structural_work:.5f} | "
            f"D_flux={sun.current_dissipation_flux:.5f} | "
            f"D_acc={sun.accumulated_dissipation:.5f} | "
            f"macro_light_flux={sun.macro_light_flux:.5f} | "
            f"appearance={sun.appearance_index:.5f}"
        )

        print(
            "       -> Appearance regime: "
            f"{appearance_state['brightness_regime']}"
        )

        print(
            "       -> Dynamic status: "
            f"{appearance_state['phase_status']}"
        )

    print(
        "=== INTERRUPTION EXPERIMENT ==="
    )

    sun.K = 0.5

    sun.set_system_state(
        C_t=0.30,
        P_t=0.55,
    )

    for tact_index in range(
        1,
        6,
    ):
        R_t = sun.process_micro_interval(
            external_forcing_density=0.0,
            dt=0.005,
        )

        print(
            f"Interruption tact {tact_index:02d} | "
            f"R_t={R_t:.5f} | "
            f"Omega_t={sun.Omega_t:.5f} | "
            f"macro_light_flux={sun.macro_light_flux:.5f} | "
            f"status={sun.get_dynamic_status()}"
        )
