import numpy as np

from framework_core import ContinuumSimulation
from module_wave_genetics.wave_genetics_dna_oscillator import (
    WaveGeneticsDNAOscillator,
)
from module_molecular_chemistry.molecular_phase_chemistry import (
    MolecularPhaseChemistry,
)
from module_solar_synthesis.solar_synthesis_resonator import (
    SolarSynthesisResonator,
)


class SchumannPlanetaryResonator:
    """
    Conceptual planetary Schumann-resonance module.

    The module represents the Earth-ionosphere cavity as a macro-scale
    planetary phase catalyst. The Schumann resonance modes are treated as
    a global timing field that can modulate biological phase alignment,
    DNA biophoton emission, and molecular phase chemistry inside liquid media.

    Within the open nonlinear dissipative dynamic Continuum, this module
    introduces a planetary coupling layer between macro-scale solar forcing
    and local biological / molecular structures.

    The module also includes a planetary appearance layer:
    a numerical indicator of how strongly the planetary resonance field
    is manifested as a stable timing interface for biological and molecular
    phase alignment.
    """

    def __init__(
        self,
        schumann_modes: np.ndarray | None = None,
        initial_ionosphere_distortion: float = 0.05,
        seed: int | None = None,
    ):
        """
        Initialize the planetary Schumann resonator.

        Parameters
        ----------
        schumann_modes:
            Electromagnetic eigenmodes of the Earth-ionosphere cavity in Hz.
            If not provided, the classical first Schumann modes are used.
        initial_ionosphere_distortion:
            Initial distortion index of the ionosphere.
        seed:
            Optional random seed for reproducible experiments.
        """
        if initial_ionosphere_distortion < 0:
            raise ValueError(
                "initial_ionosphere_distortion must be non-negative."
            )

        self.rng = np.random.default_rng(seed)

        if schumann_modes is None:
            self.schumann_modes = np.array(
                [7.83, 14.10, 20.30, 26.40, 32.40],
                dtype=np.float64,
            )
        else:
            self.schumann_modes = np.asarray(
                schumann_modes,
                dtype=np.float64,
            )

        if self.schumann_modes.size == 0:
            raise ValueError("schumann_modes must not be empty.")
        if np.any(self.schumann_modes <= 0):
            raise ValueError("all schumann_modes must be positive.")

        self.ionosphere_distortion = float(initial_ionosphere_distortion)
        self.planetary_phase = 0.0

        # Current active Schumann fundamental.
        self.active_fundamental = float(self.schumann_modes[0])

        # Current planetary forcing value.
        self.planetary_forcing_value = 0.0

        # Planetary appearance layer:
        # numerical indicator of manifested planetary timing stability.
        self.planetary_appearance_index = 0.0

    def calculate_planetary_forcing(
        self,
        solar_flux: float,
        dt: float = 0.01,
    ) -> tuple[float, float]:
        """
        Calculate the planetary forcing value.

        Solar flux modulates the ionosphere and slightly shifts the active
        Schumann fundamental. The resulting planetary forcing value is passed
        into biological, quantum, and molecular layers as a timing field.

        Parameters
        ----------
        solar_flux:
            Solar dissipation / radiation flux.
        dt:
            Discrete simulation time step.

        Returns
        -------
        tuple[float, float]:
            Planetary forcing value and active modulated fundamental frequency.
        """
        if dt <= 0:
            raise ValueError("dt must be positive.")

        solar_flux = max(float(solar_flux), 0.0)
        fundamental_frequency = float(self.schumann_modes[0])

        self.planetary_phase = (
            self.planetary_phase
            + fundamental_frequency * 2.0 * np.pi * dt
        ) % (2.0 * np.pi)

        # Solar flux introduces ionospheric distortion.
        self.ionosphere_distortion = float(
            np.clip(
                np.sin(solar_flux * 0.01) * 0.1,
                0.0,
                0.5,
            )
        )

        self.active_fundamental = fundamental_frequency + self.rng.normal(
            loc=0.0,
            scale=self.ionosphere_distortion,
        )

        self.active_fundamental = max(self.active_fundamental, 0.0)

        time_factor = np.sin(self.planetary_phase)

        self.planetary_forcing_value = float(
            np.sin(self.active_fundamental * time_factor)
        )

        self._update_planetary_appearance(
            solar_flux=solar_flux,
        )

        return self.planetary_forcing_value, self.active_fundamental

    def harmonize_brain_and_dna(
        self,
        brain_phase: float,
        dna_signal: np.ndarray | float,
    ) -> tuple[float, np.ndarray | float]:
        """
        Estimate bio-planetary phase alignment and stabilize a DNA signal.

        Parameters
        ----------
        brain_phase:
            Current phase of the biological observer / brain modulator.
        dna_signal:
            DNA biophoton signal array or scalar flux value.

        Returns
        -------
        tuple[float, np.ndarray | float]:
            Bio-planetary coupling coefficient r_geo and stabilized signal.
        """
        phase_delta = self.planetary_phase - brain_phase

        # Bio-planetary phase-coupling coefficient.
        r_geo = float(np.cos(phase_delta))

        # Only constructive coupling strengthens the signal.
        stabilized_signal = dna_signal * (1.0 + max(0.0, r_geo))

        return r_geo, stabilized_signal

    def _update_planetary_appearance(
        self,
        solar_flux: float,
    ) -> None:
        """
        Update the planetary appearance index.

        The planetary appearance index describes how clearly the planetary
        resonance field is manifested as a stable timing interface.

        It combines:
        - stability of the active Schumann fundamental,
        - magnitude of the planetary forcing field,
        - solar flux as macro-scale driving input,
        - ionospheric distortion as a destabilizing factor.
        """
        fundamental_frequency = float(self.schumann_modes[0])

        frequency_stability = 1.0 / (
            1.0 + abs(self.active_fundamental - fundamental_frequency)
        )

        forcing_strength = abs(self.planetary_forcing_value)

        solar_drive = np.log1p(max(solar_flux, 0.0))

        distortion_penalty = 1.0 / (
            1.0 + self.ionosphere_distortion
        )

        self.planetary_appearance_index = float(
            frequency_stability
            * (1.0 + forcing_strength)
            * (1.0 + solar_drive)
            * distortion_penalty
        )

    def calculate_planetary_appearance(self) -> dict[str, float | str]:
        """
        Calculate the current appearance state of the planetary resonator.

        Returns
        -------
        dict[str, float | str]:
            Planetary appearance index, timing regime, active frequency,
            ionospheric distortion, and current forcing value.
        """
        if self.planetary_appearance_index >= 6.0:
            timing_regime = "STABLE PLANETARY TIMING MANIFESTATION"
        elif self.planetary_appearance_index >= 3.0:
            timing_regime = "PARTIAL PLANETARY TIMING MANIFESTATION"
        else:
            timing_regime = "WEAK OR DISTORTED PLANETARY TIMING MANIFESTATION"

        return {
            "planetary_appearance_index": float(
                self.planetary_appearance_index
            ),
            "timing_regime": timing_regime,
            "active_fundamental": float(self.active_fundamental),
            "ionosphere_distortion": float(self.ionosphere_distortion),
            "planetary_forcing_value": float(self.planetary_forcing_value),
        }


if __name__ == "__main__":
    print("=== PLANETARY SCHUMANN RESONANCE WITH APPEARANCE LAYER ===")

    sun = SolarSynthesisResonator(
        num_plasma_domains=32,
        coupling_strength_k=45.0,
        seed=42,
    )

    earth = SchumannPlanetaryResonator(
        initial_ionosphere_distortion=0.05,
        seed=76,
    )

    quantum_core = ContinuumSimulation(
        num_layers=8,
        dt=0.01,
        seed=144,
    )

    dna_oscillator = WaveGeneticsDNAOscillator(
        sequence_length=32,
        base_frequency=320.0,
        seed=233,
    )

    molecular_cluster = MolecularPhaseChemistry(
        num_resonators=32,
        medium_viscosity=0.1,
        seed=377,
    )

    rng = np.random.default_rng(610)
    human_brain_phase = rng.uniform(0.0, 2.0 * np.pi)

    for tick in range(4):
        print(f"\n[SYSTEM TICK {tick:02d}]")

        sun.process_micro_interval(
            external_forcing_density=8.0,
            dt=0.005,
        )

        solar_energy_flux = sun.total_dissipation_flux

        earth_forcing, active_fundamental = earth.calculate_planetary_forcing(
            solar_flux=solar_energy_flux,
            dt=0.01,
        )

        appearance_state = earth.calculate_planetary_appearance()

        print(
            " -> [EARTH] "
            f"Active Schumann fundamental: {active_fundamental:.3f} Hz | "
            f"planetary forcing: {earth_forcing:.4f}"
        )

        print(
            " -> [EARTH APPEARANCE] "
            f"Index: {appearance_state['planetary_appearance_index']:.4f} | "
            f"regime: {appearance_state['timing_regime']}"
        )

        r_geo, _ = earth.harmonize_brain_and_dna(
            brain_phase=human_brain_phase,
            dna_signal=np.ones(32, dtype=np.float64),
        )

        print(
            " -> [BIOLOGY] "
            f"Bio-planetary phase coupling r_geo: {r_geo:.4f}"
        )

        effective_external_pressure = max(
            0.1,
            50.0 - solar_energy_flux - (r_geo * 20.0),
        )

        quantum_coherence = quantum_core.update_state(
            coupling_strength=15.0,
            external_pressure=effective_external_pressure / 10.0,
        )

        j_flux = quantum_core.M * quantum_coherence

        _, stabilized_dna_flux = earth.harmonize_brain_and_dna(
            brain_phase=human_brain_phase,
            dna_signal=j_flux,
        )

        biophoton_signal, hologram_density = dna_oscillator.emit_biophotons(
            j_flux=float(stabilized_dna_flux),
            brain_modulation_frequency=active_fundamental,
        )

        phantom_coherence = dna_oscillator.stabilize_phantom(
            modulated_signal=biophoton_signal,
            current_system_coherence=quantum_coherence,
        )

        molecular_cluster.apply_biophoton_forcing(
            biophoton_signal=biophoton_signal,
            phantom_coherence=phantom_coherence,
        )

        molecular_coherence = molecular_cluster.synchronize_molecular_bonds(
            dt=0.01,
        )

        print(
            " -> [RESULT] "
            f"Quantum mass: {quantum_core.M:.2f} | "
            f"DNA hologram density: {hologram_density:.4f} | "
            f"Molecular coherence: {molecular_coherence:.4f}"
        )
