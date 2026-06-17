import numpy as np


class SolarSynthesisResonator:
    """
    Conceptual macro-scale solar synthesis module.

    The module represents the Sun as an ultra-stable macro-scale phase node
    retained in the synthesis phase. The plasma amplitude layer remains
    turbulent and stochastic, while the phase layer is stabilized through
    strong endogenous coupling.

    Within the open nonlinear dissipative dynamic Continuum, the Sun is
    modeled as a system that accumulates positive structural work, opens a
    resonance window of synthesis, dissipates excess work as radiation, and
    retains the appearance of a stable solar form through phase coherence.
    """

    def __init__(
        self,
        num_plasma_domains: int = 64,
        coupling_strength_k: float = 45.0,
        seed: int | None = None,
    ):
        """
        Initialize the solar synthesis resonator.

        Parameters
        ----------
        num_plasma_domains:
            Number of plasma domains or macro-resonant cells.
        coupling_strength_k:
            Endogenous phase-coupling strength K.
        seed:
            Optional random seed for reproducible experiments.
        """
        if num_plasma_domains <= 0:
            raise ValueError("num_plasma_domains must be positive.")

        if coupling_strength_k < 0:
            raise ValueError("coupling_strength_k must be non-negative.")

        self.num_domains = num_plasma_domains
        self.K = coupling_strength_k
        self.rng = np.random.default_rng(seed)

        self.plasma_amplitudes = self.rng.uniform(
            100.0,
            1000.0,
            num_plasma_domains,
        )

        self.plasma_phases = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            num_plasma_domains,
        )

        self.accumulated_work = 0.0
        self.synthesis_window_open = False
        self.total_dissipation_flux = 0.0

        # Appearance layer:
        # numerical indicator of manifested solar brightness / visible stability.
        self.appearance_index = 0.0

    def process_micro_interval(
        self,
        external_forcing_density: float,
        dt: float = 0.005,
    ) -> float:
        """
        Process one micro-interval of solar phase dynamics.

        Parameters
        ----------
        external_forcing_density:
            Forcing density of the surrounding Continuum.
        dt:
            Discrete time step.

        Returns
        -------
        float:
            Endogenous phase coherence of the solar plasma domains.
        """
        if external_forcing_density < 0:
            raise ValueError("external_forcing_density must be non-negative.")

        if dt <= 0:
            raise ValueError("dt must be positive.")

        amplitude_noise = self.rng.normal(
            loc=0.0,
            scale=50.0,
            size=self.num_domains,
        )

        self.plasma_amplitudes = np.clip(
            self.plasma_amplitudes + amplitude_noise,
            10.0,
            2000.0,
        )

        phase_difference = (
            self.plasma_phases[None, :]
            - self.plasma_phases[:, None]
        )

        phase_acceleration = (
            np.sum(self.K * np.sin(phase_difference), axis=1)
            / self.num_domains
        )

        forcing_effect = external_forcing_density * np.sin(
            self.plasma_phases
        )

        self.plasma_phases = (
            self.plasma_phases
            + (phase_acceleration + forcing_effect) * dt
        ) % (2.0 * np.pi)

        endogenous_coherence = np.abs(
            np.mean(np.exp(1j * self.plasma_phases))
        )

        mean_amplitude = float(np.mean(self.plasma_amplitudes))

        self.accumulated_work = mean_amplitude * endogenous_coherence

        if endogenous_coherence > 0.95 and self.accumulated_work > 500.0:
            self.synthesis_window_open = True

            self.total_dissipation_flux = self.accumulated_work * 0.98
            self.accumulated_work -= self.total_dissipation_flux
        else:
            self.synthesis_window_open = False

            self.total_dissipation_flux = mean_amplitude * (
                1.0 - endogenous_coherence
            )

        # Appearance layer:
        # the visible solar form appears when amplitude intensity is retained
        # by phase coherence and released through stable dissipation.
        self.appearance_index = (
            endogenous_coherence
            * np.log1p(mean_amplitude)
            * (1.0 + np.log1p(self.total_dissipation_flux))
        )

        return float(endogenous_coherence)

    def calculate_solar_appearance(self) -> dict[str, float | str]:
        """
        Calculate the current appearance state of the solar resonator.

        Returns
        -------
        dict[str, float | str]:
            Appearance index, brightness regime, and phase status.
        """
        if self.appearance_index >= 50.0:
            brightness_regime = "STABLE SOLAR MANIFESTATION"
        elif self.appearance_index >= 20.0:
            brightness_regime = "PARTIAL SOLAR MANIFESTATION"
        else:
            brightness_regime = "WEAK OR UNSTABLE SOLAR MANIFESTATION"

        return {
            "appearance_index": float(self.appearance_index),
            "brightness_regime": brightness_regime,
            "phase_status": self.check_system_freeze_status(),
        }

    def check_system_freeze_status(self) -> str:
        """
        Return the current phase status of the solar resonator.

        Returns
        -------
        str:
            Human-readable system status.
        """
        if self.synthesis_window_open:
            return (
                "FROZEN IN SYNTHESIS "
                "(ultra-stable phase node, maximal dissipation)"
            )

        return (
            "FLUCTUATING PLASMA "
            "(searching for retained phase coupling)"
        )


if __name__ == "__main__":
    sun = SolarSynthesisResonator(
        num_plasma_domains=128,
        coupling_strength_k=80.0,
        seed=42,
    )

    print("=== COSMIC SCALE: SOLAR SYNTHESIS WITH APPEARANCE LAYER ===")

    for tick in range(5):
        coherence = sun.process_micro_interval(
            external_forcing_density=5.0,
            dt=0.005,
        )

        appearance_state = sun.calculate_solar_appearance()

        print(
            f"Tick {tick:02d} | "
            f"Phase coherence: {coherence:.5f} | "
            f"Mean amplitude: {np.mean(sun.plasma_amplitudes):.2f} | "
            f"Dissipation flux: {sun.total_dissipation_flux:.2f} | "
            f"Appearance index: {appearance_state['appearance_index']:.4f}"
        )

        print(
            f"       -> Brightness regime: "
            f"{appearance_state['brightness_regime']}"
        )

        print(
            f"       -> Phase status: "
            f"{appearance_state['phase_status']}\n"
        )

    print("=== EXPERIMENT: INTERRUPTION OF CONTINUUM FORCING ===")

    sun.K = 0.5

    coherence = sun.process_micro_interval(
        external_forcing_density=0.0,
        dt=0.005,
    )

    appearance_state = sun.calculate_solar_appearance()

    print(f"[REACTION] Coherence after forcing interruption: {coherence:.4f}")
    print(f"[REACTION] Appearance index: {appearance_state['appearance_index']:.4f}")
    print(f"[REACTION] Brightness regime: {appearance_state['brightness_regime']}")
    print(f"[REACTION] System status: {appearance_state['phase_status']}")
    print(
        "[INFO] The macro-scale phase node is unlocked. "
        "The structure dissipates toward the background regime."
    )
