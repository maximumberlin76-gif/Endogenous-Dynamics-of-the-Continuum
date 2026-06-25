import numpy as np

from module_framework_core.framework_core import ContinuumSimulation


class WaveGeneticsDNAOscillator:
    """
    Conceptual module for DNA-based wave-genetic phase modulation.

    The module represents DNA not as a static symbolic storage medium,
    but as a polarized biophoton laser-interferometric structure.

    Within the open nonlinear dissipative dynamic Continuum, the DNA phase
    matrix modulates the dissipative flow channel J_flux and generates
    a biophoton interference signal. Under sufficient system coherence,
    this signal can leave a residual phantom-field imprint in the local
    Continuum domain.

    The module also includes a genetic appearance layer:
    a numerical indicator of how strongly DNA biophoton modulation is
    manifested as a retained wave-genetic phase regime.
    """

    def __init__(
        self,
        sequence_length: int = 64,
        base_frequency: float = 320.0,
        seed: int | None = None,
    ):
        """
        Initialize the DNA biophoton oscillator.

        Parameters
        ----------
        sequence_length:
            Length of the quantized DNA phase vector.
        base_frequency:
            Base emission frequency of the biophoton oscillator
            in arbitrary simulation units.
        seed:
            Optional random seed for reproducible experiments.
        """
        if sequence_length <= 0:
            raise ValueError("sequence_length must be positive.")
        if base_frequency <= 0:
            raise ValueError("base_frequency must be positive.")

        self.length = sequence_length
        self.base_frequency = base_frequency
        self.rng = np.random.default_rng(seed)

        # DNA phase matrix:
        # each sequence position is represented as a phase displacement.
        self.dna_phase_matrix = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            sequence_length,
        )

        # Simplified polarization state of the emitted biophoton field.
        self.polarization = np.array(
            [1.0 + 0.0j, 0.0 + 1.0j],
            dtype=np.complex128,
        ) / np.sqrt(2.0)

        # Residual phantom-field variables.
        self.phantom_coherence = 0.0
        self.phantom_field_matrix = np.zeros(
            sequence_length,
            dtype=np.float64,
        )

        # Latest generated signal parameters.
        self.last_hologram_density = 0.0
        self.last_signal_energy = 0.0
        self.last_pump_energy = 0.0

        # Genetic appearance layer:
        # numerical indicator of retained DNA-biophoton manifestation.
        self.genetic_appearance_index = 0.0

    def emit_biophotons(
        self,
        j_flux: float,
        brain_modulation_frequency: float = 0.0,
    ) -> tuple[np.ndarray, float]:
        """
        Generate a biophoton modulation signal from the dissipative flow J_flux.

        Parameters
        ----------
        j_flux:
            Intensity of the dissipative flow channel.
        brain_modulation_frequency:
            External biological modulation frequency in arbitrary units.

        Returns
        -------
        tuple[np.ndarray, float]:
            Modulated biophoton signal and hologram density parameter.
        """
        if j_flux <= 0.0:
            self.last_pump_energy = 0.0
            self.last_signal_energy = 0.0
            self.last_hologram_density = 0.0
            self._update_genetic_appearance(
                current_system_coherence=0.0,
            )

            return np.zeros(self.length, dtype=np.float64), 0.0

        # The dissipative flow channel pumps the biological oscillator.
        pump_energy = np.log1p(j_flux)
        self.last_pump_energy = float(pump_energy)

        # Phase axis for one complete structural cycle.
        phase_axis = np.linspace(
            0.0,
            2.0 * np.pi,
            self.length,
        )

        # DNA phase geometry and biological modulation jointly define
        # the biophoton wave pattern.
        biophoton_wave = np.sin(
            self.base_frequency * phase_axis
            + self.dna_phase_matrix
            + brain_modulation_frequency
        )

        # The outgoing signal is scaled by the available pump energy.
        modulated_signal = biophoton_wave * pump_energy

        # Compact hologram-density measure:
        # order parameter of the resulting interference pattern.
        hologram_density = np.abs(
            np.mean(np.exp(1j * modulated_signal))
        )

        self.last_hologram_density = float(hologram_density)
        self.last_signal_energy = float(
            np.mean(np.square(modulated_signal))
        )

        return modulated_signal, float(hologram_density)

    def stabilize_phantom(
        self,
        modulated_signal: np.ndarray,
        current_system_coherence: float,
    ) -> float:
        """
        Stabilize a residual phantom-field imprint in the local Continuum domain.

        Parameters
        ----------
        modulated_signal:
            Current DNA-modulated biophoton signal.
        current_system_coherence:
            Current coherence of the surrounding system.

        Returns
        -------
        float:
            Updated phantom coherence.
        """
        if modulated_signal.shape[0] != self.length:
            raise ValueError(
                "modulated_signal length must match sequence_length."
            )

        if current_system_coherence < 0:
            raise ValueError(
                "current_system_coherence must be non-negative."
            )

        if current_system_coherence > 0.5:
            # Coherent conditions allow the local domain to accumulate
            # the structural trace of the signal.
            self.phantom_field_matrix = (
                0.95 * self.phantom_field_matrix
                + 0.05 * modulated_signal
            )

            self.phantom_coherence = float(
                np.clip(
                    self.phantom_coherence
                    + 0.1 * current_system_coherence,
                    0.0,
                    1.0,
                )
            )
        else:
            # Without sufficient coherence, the residual field decays slowly.
            self.phantom_coherence *= 0.99

        self._update_genetic_appearance(
            current_system_coherence=current_system_coherence,
        )

        return float(self.phantom_coherence)

    def _update_genetic_appearance(
        self,
        current_system_coherence: float,
    ) -> None:
        """
        Update the genetic appearance index.

        The genetic appearance index describes how strongly DNA biophoton
        modulation is manifested as a retained wave-genetic phase regime.

        It combines:
        - current coherence of the surrounding system,
        - hologram density of the emitted biophoton signal,
        - signal energy of DNA modulation,
        - phantom coherence of the residual field,
        - pump energy received through J_flux.
        """
        coherence_factor = max(float(current_system_coherence), 0.0)

        hologram_factor = self.last_hologram_density

        signal_energy_factor = np.log1p(
            max(self.last_signal_energy, 0.0)
        )

        pump_factor = np.log1p(
            max(self.last_pump_energy, 0.0)
        )

        phantom_factor = self.phantom_coherence

        self.genetic_appearance_index = float(
            coherence_factor
            * (1.0 + hologram_factor)
            * (1.0 + signal_energy_factor)
            * (1.0 + pump_factor)
            * (1.0 + phantom_factor)
        )

    def calculate_genetic_appearance(self) -> dict[str, float | str]:
        """
        Calculate the current appearance state of the DNA biophoton oscillator.

        Returns
        -------
        dict[str, float | str]:
            Genetic appearance index, genetic manifestation regime,
            hologram density, signal energy, phantom coherence, and pump energy.
        """
        if self.genetic_appearance_index >= 6.0:
            genetic_regime = "STABLE WAVE-GENETIC MANIFESTATION"
        elif self.genetic_appearance_index >= 3.0:
            genetic_regime = "PARTIAL WAVE-GENETIC MANIFESTATION"
        else:
            genetic_regime = "WEAK OR UNSTABLE WAVE-GENETIC MANIFESTATION"

        return {
            "genetic_appearance_index": float(
                self.genetic_appearance_index
            ),
            "genetic_regime": genetic_regime,
            "hologram_density": float(self.last_hologram_density),
            "signal_energy": float(self.last_signal_energy),
            "phantom_coherence": float(self.phantom_coherence),
            "pump_energy": float(self.last_pump_energy),
        }

    def read_phantom_without_dna(self) -> np.ndarray:
        """
        Read the residual field after removal of the physical DNA source.

        Returns
        -------
        np.ndarray:
            Reconstructed residual phantom signal.
        """
        print(
            "[OSCILLOGRAPH] Physical DNA source removed. "
            "Scanning the local Continuum domain..."
        )

        if self.phantom_coherence > 0.05:
            print(
                "[WARNING] Residual phantom field detected. "
                f"Phantom coherence: {self.phantom_coherence:.4f}"
            )

            reconstructed_signal = (
                self.phantom_field_matrix * self.phantom_coherence
            )

            return reconstructed_signal

        print(
            "[INFO] No stable residual phantom field detected. "
            "The local domain returned to the non-resonant baseline state."
        )

        return np.zeros(self.length, dtype=np.float64)


if __name__ == "__main__":
    continuum = ContinuumSimulation(
        num_layers=8,
        dt=0.01,
        seed=42,
    )

    dna_oscillator = WaveGeneticsDNAOscillator(
        sequence_length=64,
        base_frequency=320.0,
        seed=76,
    )

    print("=== WAVE-GENETIC DNA OSCILLATOR WITH APPEARANCE LAYER ===")

    for tick in range(3):
        system_coherence = continuum.update_state(
            coupling_strength=20.0,
            external_pressure=0.05,
        )

        j_flux = continuum.M * system_coherence

        signal, hologram_density = dna_oscillator.emit_biophotons(
            j_flux=j_flux,
            brain_modulation_frequency=40.0,
        )

        phantom_coherence = dna_oscillator.stabilize_phantom(
            modulated_signal=signal,
            current_system_coherence=system_coherence,
        )

        appearance_state = dna_oscillator.calculate_genetic_appearance()

        print(
            f"Tick {tick} | "
            f"System coherence: {system_coherence:.4f} | "
            f"J flux: {j_flux:.4f} | "
            f"Hologram density: {hologram_density:.4f} | "
            f"Phantom coherence: {phantom_coherence:.4f}"
        )

        print(
            f"       -> Genetic appearance index: "
            f"{appearance_state['genetic_appearance_index']:.4f}"
        )

        print(
            f"       -> Genetic regime: "
            f"{appearance_state['genetic_regime']}"
        )

    print("\n=== STAGE 2: Marnov Protocol collapse of the core interface ===")

    continuum.update_state(
        coupling_strength=1.0,
        external_pressure=100.0,
    )

    continuum.run_marnov_demolition(
        external_pressure=100.0,
    )

    print("\n=== STAGE 3: Residual phantom-field scan ===")

    phantom_signal = dna_oscillator.read_phantom_without_dna()
    residual_energy = float(np.sum(np.square(phantom_signal)))

    print(
        "[RESULT] Residual structural field strength: "
        f"{residual_energy:.6f}"
    )
