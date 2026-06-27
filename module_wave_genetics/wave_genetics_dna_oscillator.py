from __future__ import annotations

from typing import Any

import numpy as np

from module_framework_core.framework_core import ContinuumSimulation


class WaveGeneticsDNAOscillator:
    """
    Conceptual module for DNA-based wave-genetic phase modulation.

    The module models DNA as a biological phase-modulating structure inside
    an open nonlinear dissipative dynamic Continuum.

    Controlled distinctions preserved by this module:
    - J_flux is the through massless exchange-flow channel received from
      the upstream Continuum / framework layer.
    - biophoton_signal is the modeled biological wave output of this layer.
    - hologram_density is a compact numerical order parameter of the
      modeled DNA-biophoton field.
    - phantom_coherence is the retained remanent field-trace coherence.
    - current_system_coherence is a local coherence input and is not
      automatically identical to the full theoretical C(t).
    """

    STABLE_WAVE_GENETIC_MANIFESTATION = "STABLE WAVE-GENETIC MANIFESTATION"
    PARTIAL_WAVE_GENETIC_MANIFESTATION = "PARTIAL WAVE-GENETIC MANIFESTATION"
    WEAK_WAVE_GENETIC_MANIFESTATION = "WEAK OR UNSTABLE WAVE-GENETIC MANIFESTATION"

    def __init__(
        self,
        sequence_length: int = 64,
        base_frequency: float = 320.0,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the DNA biophoton oscillator.

        Parameters
        ----------
        sequence_length:
            Length of the quantized DNA phase vector.
        base_frequency:
            Base modeled emission frequency of the biophoton oscillator.
        seed:
            Optional random seed for reproducible experiments.
        """
        self.length = self._validate_positive_integer(
            "sequence_length",
            sequence_length,
        )
        self.base_frequency = self._validate_positive_finite(
            "base_frequency",
            base_frequency,
        )

        self.rng = np.random.default_rng(seed)

        self.dna_phase_matrix = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            self.length,
        )

        self.polarization = np.array(
            [1.0 + 0.0j, 0.0 + 1.0j],
            dtype=np.complex128,
        ) / np.sqrt(2.0)

        self.phantom_coherence = 0.0
        self.phantom_field_matrix = np.zeros(
            self.length,
            dtype=np.float64,
        )

        self.last_hologram_density = 0.0
        self.last_signal_energy = 0.0
        self.last_pump_energy = 0.0
        self.last_j_flux = 0.0
        self.last_system_coherence = 0.0

        self.genetic_appearance_index = 0.0

        self._validate_state()

    @staticmethod
    def _validate_finite_scalar(name: str, value: Any) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _validate_positive_finite(cls, name: str, value: Any) -> float:
        scalar = cls._validate_finite_scalar(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    @classmethod
    def _validate_non_negative_finite(cls, name: str, value: Any) -> float:
        scalar = cls._validate_finite_scalar(name, value)

        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")

        return scalar

    @staticmethod
    def _validate_positive_integer(name: str, value: Any) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a positive integer.")

        try:
            integer = int(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a positive integer.") from exc

        if integer != value:
            raise ValueError(f"{name} must be a positive integer.")

        if integer <= 0:
            raise ValueError(f"{name} must be positive.")

        return integer

    def _validate_signal(self, signal: Any, name: str) -> np.ndarray:
        array = np.asarray(signal, dtype=np.float64)

        if array.shape != (self.length,):
            raise ValueError(f"{name} must have shape ({self.length},).")

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must contain only finite values.")

        return array

    def emit_biophotons(
        self,
        j_flux: float,
        brain_modulation_frequency: float = 0.0,
    ) -> tuple[np.ndarray, float]:
        """
        Generate a modeled DNA-biophoton modulation signal from J_flux.

        Operational chain:

        J_flux -> pump_energy -> DNA phase matrix -> biological phase modulation
        -> biophoton_signal -> modulated_signal -> hologram_density

        Parameters
        ----------
        j_flux:
            Through massless exchange-flow input from the upstream EDK layer.
        brain_modulation_frequency:
            External biological phase-modulation frequency.

        Returns
        -------
        tuple[np.ndarray, float]:
            Modulated biophoton model signal and hologram-density parameter.
        """
        j_flux = self._validate_non_negative_finite("j_flux", j_flux)
        brain_modulation_frequency = self._validate_finite_scalar(
            "brain_modulation_frequency",
            brain_modulation_frequency,
        )

        self.last_j_flux = j_flux

        if j_flux <= 0.0:
            self.last_pump_energy = 0.0
            self.last_signal_energy = 0.0
            self.last_hologram_density = 0.0
            self._update_genetic_appearance(current_system_coherence=0.0)

            return np.zeros(self.length, dtype=np.float64), 0.0

        pump_energy = np.log1p(j_flux)
        self.last_pump_energy = float(pump_energy)

        phase_axis = np.linspace(
            0.0,
            2.0 * np.pi,
            self.length,
            endpoint=False,
            dtype=np.float64,
        )

        biophoton_signal = np.sin(
            self.base_frequency * phase_axis
            + self.dna_phase_matrix
            + brain_modulation_frequency
        )

        modulated_signal = biophoton_signal * pump_energy

        hologram_density = abs(
            np.mean(
                np.exp(1j * modulated_signal),
            )
        )

        self.last_hologram_density = float(hologram_density)
        self.last_signal_energy = float(
            np.mean(
                np.square(modulated_signal),
            )
        )

        self._validate_state()

        return modulated_signal.astype(np.float64, copy=True), float(hologram_density)

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
            Current DNA-modulated biophoton model signal.
        current_system_coherence:
            Local system-coherence input received from the upstream layer.

        Returns
        -------
        float:
            Updated phantom coherence.
        """
        modulated_signal = self._validate_signal(
            modulated_signal,
            "modulated_signal",
        )

        current_system_coherence = self._validate_non_negative_finite(
            "current_system_coherence",
            current_system_coherence,
        )

        current_system_coherence = float(
            np.clip(
                current_system_coherence,
                0.0,
                1.0,
            )
        )

        self.last_system_coherence = current_system_coherence

        if current_system_coherence > 0.5:
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
            self.phantom_coherence = float(
                np.clip(
                    self.phantom_coherence * 0.99,
                    0.0,
                    1.0,
                )
            )

        self._update_genetic_appearance(
            current_system_coherence=current_system_coherence,
        )

        self._validate_state()

        return float(self.phantom_coherence)

    def _update_genetic_appearance(
        self,
        current_system_coherence: float,
    ) -> None:
        """
        Update the genetic appearance index.

        The genetic appearance index describes how strongly DNA-biophoton
        modulation is manifested as a retained wave-genetic phase regime.
        """
        coherence_factor = self._validate_non_negative_finite(
            "current_system_coherence",
            current_system_coherence,
        )

        coherence_factor = float(
            np.clip(
                coherence_factor,
                0.0,
                1.0,
            )
        )

        hologram_factor = max(
            float(self.last_hologram_density),
            0.0,
        )

        signal_energy_factor = np.log1p(
            max(
                float(self.last_signal_energy),
                0.0,
            )
        )

        pump_factor = np.log1p(
            max(
                float(self.last_pump_energy),
                0.0,
            )
        )

        phantom_factor = max(
            float(self.phantom_coherence),
            0.0,
        )

        self.genetic_appearance_index = float(
            coherence_factor
            * (1.0 + hologram_factor)
            * (1.0 + signal_energy_factor)
            * (1.0 + pump_factor)
            * (1.0 + phantom_factor)
        )

    def calculate_genetic_appearance(self) -> dict[str, float | str]:
        """
        Calculate the current appearance state of the DNA-biophoton oscillator.
        """
        if self.genetic_appearance_index >= 6.0:
            genetic_regime = self.STABLE_WAVE_GENETIC_MANIFESTATION
        elif self.genetic_appearance_index >= 3.0:
            genetic_regime = self.PARTIAL_WAVE_GENETIC_MANIFESTATION
        else:
            genetic_regime = self.WEAK_WAVE_GENETIC_MANIFESTATION

        return {
            "genetic_appearance_index": float(self.genetic_appearance_index),
            "genetic_regime": genetic_regime,
            "hologram_density": float(self.last_hologram_density),
            "signal_energy": float(self.last_signal_energy),
            "phantom_coherence": float(self.phantom_coherence),
            "pump_energy": float(self.last_pump_energy),
            "j_flux": float(self.last_j_flux),
            "current_system_coherence": float(self.last_system_coherence),
        }

    def read_phantom_without_dna(self) -> np.ndarray:
        """
        Read the residual field after removal of the physical DNA-source input.

        Returns
        -------
        np.ndarray:
            Reconstructed residual phantom signal.
        """
        print(
            "[OSCILLOGRAPH] Physical DNA-source input removed. "
            "Scanning the local Continuum domain..."
        )

        if self.phantom_coherence > 0.05:
            print(
                "[WARNING] Residual phantom field detected. "
                f"Phantom coherence: {self.phantom_coherence:.4f}"
            )

            reconstructed_signal = self.phantom_field_matrix * self.phantom_coherence

            return reconstructed_signal.astype(np.float64, copy=True)

        print(
            "[INFO] No stable residual phantom field detected. "
            "The local domain returned to the non-resonant baseline state."
        )

        return np.zeros(self.length, dtype=np.float64)

    def _validate_state(self) -> None:
        if self.dna_phase_matrix.shape != (self.length,):
            raise RuntimeError("dna_phase_matrix has invalid shape.")

        if not np.all(np.isfinite(self.dna_phase_matrix)):
            raise FloatingPointError("dna_phase_matrix contains non-finite values.")

        if self.phantom_field_matrix.shape != (self.length,):
            raise RuntimeError("phantom_field_matrix has invalid shape.")

        if not np.all(np.isfinite(self.phantom_field_matrix)):
            raise FloatingPointError("phantom_field_matrix contains non-finite values.")

        scalar_fields = {
            "phantom_coherence": self.phantom_coherence,
            "last_hologram_density": self.last_hologram_density,
            "last_signal_energy": self.last_signal_energy,
            "last_pump_energy": self.last_pump_energy,
            "last_j_flux": self.last_j_flux,
            "last_system_coherence": self.last_system_coherence,
            "genetic_appearance_index": self.genetic_appearance_index,
        }

        for name, value in scalar_fields.items():
            if not np.isfinite(float(value)):
                raise FloatingPointError(f"{name} is non-finite.")

        if self.phantom_coherence < 0.0:
            raise RuntimeError("phantom_coherence must be non-negative.")

        if self.genetic_appearance_index < 0.0:
            raise RuntimeError("genetic_appearance_index must be non-negative.")


def run_demo() -> None:
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

    for tact_index in range(1, 4):
        R_t = continuum.update_state(
            coupling_strength=20.0,
            external_pressure=0.05,
        )

        continuum_state = continuum.calculate_continuum_appearance()

        current_system_coherence = float(
            continuum_state["endogenous_structural_coherence"]
        )

        upstream_j_flux = float(
            continuum_state["j_flux"]
        )

        signal, hologram_density = dna_oscillator.emit_biophotons(
            j_flux=upstream_j_flux,
            brain_modulation_frequency=40.0,
        )

        phantom_coherence = dna_oscillator.stabilize_phantom(
            modulated_signal=signal,
            current_system_coherence=current_system_coherence,
        )

        genetic_state = dna_oscillator.calculate_genetic_appearance()

        print(
            f"Tact {tact_index:02d} | "
            f"R(t): {R_t:.4f} | "
            f"C(t) proxy: {current_system_coherence:.4f} | "
            f"J_flux: {upstream_j_flux:.4f} | "
            f"Hologram density: {hologram_density:.4f} | "
            f"Phantom coherence: {phantom_coherence:.4f}"
        )

        print(
            "       -> Genetic appearance index: "
            f"{genetic_state['genetic_appearance_index']:.4f}"
        )

        print(
            "       -> Genetic regime: "
            f"{genetic_state['genetic_regime']}"
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
    residual_energy = float(
        np.sum(
            np.square(phantom_signal),
        )
    )

    print(
        "[RESULT] Residual structural field strength: "
        f"{residual_energy:.6f}"
    )


if __name__ == "__main__":
    run_demo()
