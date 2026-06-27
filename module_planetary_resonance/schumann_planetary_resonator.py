from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from module_framework_core.framework_core import ContinuumSimulation
from module_molecular_phase_chemistry.molecular_phase_chemistry import (
    MolecularPhaseChemistry,
)
from module_solar_synthesis.solar_synthesis_resonator import (
    SolarSynthesisResonator,
)
from module_wave_genetics.wave_genetics_dna_oscillator import (
    WaveGeneticsDNAOscillator,
)


__all__ = [
    "SchumannPlanetaryResonator",
    "run_demo",
]


class SchumannPlanetaryResonator:
    """
    Conceptual planetary Schumann-resonance module.

    The module represents the Earth-ionosphere cavity as a macro-scale
    planetary phase catalyst.

    The Schumann resonance modes are modeled as observable frequency regimes
    of the planetary timing domain.

    Controlled distinctions preserved by this module:
    - planetary resonance is not C(t);
    - planetary_appearance_index is not C(t);
    - planetary_forcing_value is not J_flux;
    - environmental phase modulation is not J_flux;
    - r_geo is a reduced bio-planetary phase synchronization indicator;
    - planetary coupling is not T_int;
    - phase synchronization is not identical to phase coherence.
    """

    STABLE_PLANETARY_TIMING_MANIFESTATION = (
        "STABLE PLANETARY TIMING MANIFESTATION"
    )
    PARTIAL_PLANETARY_TIMING_MANIFESTATION = (
        "PARTIAL PLANETARY TIMING MANIFESTATION"
    )
    WEAK_PLANETARY_TIMING_MANIFESTATION = (
        "WEAK OR DISTORTED PLANETARY TIMING MANIFESTATION"
    )

    def __init__(
        self,
        schumann_modes: np.ndarray | None = None,
        initial_ionosphere_distortion: float = 0.05,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the planetary Schumann resonator.

        Parameters
        ----------
        schumann_modes:
            Modeled eigenmodes of the Earth-ionosphere cavity in Hz.
        initial_ionosphere_distortion:
            Initial distortion index of the ionospheric layer.
        seed:
            Optional random seed for reproducible experiments.
        """
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

        self._validate_schumann_modes(self.schumann_modes)

        self.ionosphere_distortion = self._validate_non_negative_finite(
            "initial_ionosphere_distortion",
            initial_ionosphere_distortion,
        )

        self.ionosphere_distortion = float(
            np.clip(
                self.ionosphere_distortion,
                0.0,
                0.5,
            )
        )

        self.planetary_phase = 0.0
        self.active_fundamental = float(self.schumann_modes[0])
        self.planetary_forcing_value = 0.0
        self.planetary_appearance_index = 0.0

        self.last_solar_flux = 0.0
        self.last_frequency_stability = 1.0
        self.last_forcing_strength = 0.0
        self.last_solar_drive = 0.0
        self.last_distortion_penalty = 1.0
        self.last_r_geo = 0.0

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
    def _validate_schumann_modes(schumann_modes: np.ndarray) -> None:
        if schumann_modes.ndim != 1:
            raise ValueError("schumann_modes must be a one-dimensional array.")

        if schumann_modes.size == 0:
            raise ValueError("schumann_modes must not be empty.")

        if not np.all(np.isfinite(schumann_modes)):
            raise ValueError("schumann_modes must contain only finite values.")

        if np.any(schumann_modes <= 0.0):
            raise ValueError("all schumann_modes must be positive.")

    @staticmethod
    def _validate_signal(signal: np.ndarray | float, name: str) -> np.ndarray:
        array = np.asarray(signal, dtype=np.float64)

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must contain only finite values.")

        return array

    def calculate_planetary_forcing(
        self,
        solar_flux: float,
        dt: float = 0.01,
    ) -> tuple[float, float]:
        """
        Calculate the local planetary timing-forcing value.

        Operational chain:

        solar_flux -> ionosphere_distortion -> active_fundamental
        -> planetary_phase -> planetary_forcing_value
        -> planetary_appearance_index

        Parameters
        ----------
        solar_flux:
            Macro-level solar forcing input.
        dt:
            Discrete simulation time step.

        Returns
        -------
        tuple[float, float]:
            Planetary timing-forcing value and active fundamental frequency.
        """
        solar_flux = self._validate_non_negative_finite(
            "solar_flux",
            solar_flux,
        )

        dt = self._validate_positive_finite(
            "dt",
            dt,
        )

        self.last_solar_flux = solar_flux

        fundamental_frequency = float(self.schumann_modes[0])

        self.planetary_phase = (
            self.planetary_phase
            + fundamental_frequency * 2.0 * np.pi * dt
        ) % (2.0 * np.pi)

        self.ionosphere_distortion = float(
            np.clip(
                np.sin(solar_flux * 0.01) * 0.1,
                0.0,
                0.5,
            )
        )

        self.active_fundamental = fundamental_frequency + float(
            self.rng.normal(
                loc=0.0,
                scale=self.ionosphere_distortion,
            )
        )

        self.active_fundamental = max(
            self.active_fundamental,
            1.0e-12,
        )

        time_factor = np.sin(self.planetary_phase)

        self.planetary_forcing_value = float(
            np.sin(
                self.active_fundamental * time_factor,
            )
        )

        self._update_planetary_appearance(
            solar_flux=solar_flux,
        )

        self._validate_state()

        return (
            float(self.planetary_forcing_value),
            float(self.active_fundamental),
        )

    def harmonize_brain_and_dna(
        self,
        brain_phase: float,
        dna_signal: np.ndarray | float,
    ) -> tuple[float, np.ndarray | float]:
        """
        Estimate bio-planetary phase synchronization and stabilize DNA signal.

        Parameters
        ----------
        brain_phase:
            Current phase of the biological phase modulator.
        dna_signal:
            DNA-biophoton model signal or scalar exchange-flow input.

        Returns
        -------
        tuple[float, np.ndarray | float]:
            r_geo and stabilized signal.

        Notes
        -----
        r_geo is a reduced phase synchronization indicator.

        r_geo is not C(t).

        The stabilized signal is not J_flux unless the scalar input itself
        is an upstream J_flux value received from the framework layer.
        """
        brain_phase = self._validate_finite_scalar(
            "brain_phase",
            brain_phase,
        )

        signal_array = self._validate_signal(
            dna_signal,
            "dna_signal",
        )

        phase_delta = self.planetary_phase - brain_phase

        r_geo = float(
            np.cos(phase_delta),
        )

        self.last_r_geo = r_geo

        stabilization_factor = 1.0 + max(
            0.0,
            r_geo,
        )

        stabilized_signal = signal_array * stabilization_factor

        self._validate_state()

        if stabilized_signal.ndim == 0:
            return r_geo, float(stabilized_signal)

        return r_geo, stabilized_signal.astype(np.float64, copy=True)

    def _update_planetary_appearance(
        self,
        solar_flux: float,
    ) -> None:
        """
        Update the planetary appearance index.

        The planetary appearance index is a local diagnostic of planetary
        timing manifestation.

        It does not replace C(t).
        """
        solar_flux = self._validate_non_negative_finite(
            "solar_flux",
            solar_flux,
        )

        fundamental_frequency = float(self.schumann_modes[0])

        frequency_stability = 1.0 / (
            1.0 + abs(self.active_fundamental - fundamental_frequency)
        )

        forcing_strength = abs(self.planetary_forcing_value)

        solar_drive = np.log1p(solar_flux)

        distortion_penalty = 1.0 / (
            1.0 + self.ionosphere_distortion
        )

        self.last_frequency_stability = float(frequency_stability)
        self.last_forcing_strength = float(forcing_strength)
        self.last_solar_drive = float(solar_drive)
        self.last_distortion_penalty = float(distortion_penalty)

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
            ionospheric distortion, planetary forcing value, solar flux,
            and bio-planetary phase synchronization indicator.
        """
        if self.planetary_appearance_index >= 6.0:
            timing_regime = self.STABLE_PLANETARY_TIMING_MANIFESTATION
        elif self.planetary_appearance_index >= 3.0:
            timing_regime = self.PARTIAL_PLANETARY_TIMING_MANIFESTATION
        else:
            timing_regime = self.WEAK_PLANETARY_TIMING_MANIFESTATION

        return {
            "planetary_appearance_index": float(
                self.planetary_appearance_index
            ),
            "timing_regime": timing_regime,
            "active_fundamental": float(self.active_fundamental),
            "ionosphere_distortion": float(self.ionosphere_distortion),
            "planetary_forcing_value": float(self.planetary_forcing_value),
            "solar_flux": float(self.last_solar_flux),
            "frequency_stability": float(self.last_frequency_stability),
            "forcing_strength": float(self.last_forcing_strength),
            "solar_drive": float(self.last_solar_drive),
            "distortion_penalty": float(self.last_distortion_penalty),
            "r_geo": float(self.last_r_geo),
        }

    def _validate_state(self) -> None:
        self._validate_schumann_modes(self.schumann_modes)

        scalar_fields = {
            "ionosphere_distortion": self.ionosphere_distortion,
            "planetary_phase": self.planetary_phase,
            "active_fundamental": self.active_fundamental,
            "planetary_forcing_value": self.planetary_forcing_value,
            "planetary_appearance_index": self.planetary_appearance_index,
            "last_solar_flux": self.last_solar_flux,
            "last_frequency_stability": self.last_frequency_stability,
            "last_forcing_strength": self.last_forcing_strength,
            "last_solar_drive": self.last_solar_drive,
            "last_distortion_penalty": self.last_distortion_penalty,
            "last_r_geo": self.last_r_geo,
        }

        for name, value in scalar_fields.items():
            if not np.isfinite(float(value)):
                raise FloatingPointError(f"{name} is non-finite.")

        if self.ionosphere_distortion < 0.0:
            raise RuntimeError("ionosphere_distortion must be non-negative.")

        if self.active_fundamental <= 0.0:
            raise RuntimeError("active_fundamental must be positive.")

        if self.planetary_appearance_index < 0.0:
            raise RuntimeError(
                "planetary_appearance_index must be non-negative."
            )


def run_demo() -> None:
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

    framework_core = ContinuumSimulation(
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
    human_brain_phase = float(
        rng.uniform(
            0.0,
            2.0 * np.pi,
        )
    )

    for tact_index in range(1, 5):
        print(f"\n[SYSTEM TACT {tact_index:02d}]")

        sun.process_micro_interval(
            external_forcing_density=8.0,
            dt=0.005,
        )

        solar_energy_flux = float(
            sun.total_dissipation_flux,
        )

        earth_forcing, active_fundamental = earth.calculate_planetary_forcing(
            solar_flux=solar_energy_flux,
            dt=0.01,
        )

        planetary_state = earth.calculate_planetary_appearance()

        print(
            " -> [EARTH] "
            f"Active Schumann fundamental: {active_fundamental:.3f} Hz | "
            f"planetary forcing: {earth_forcing:.4f}"
        )

        print(
            " -> [EARTH APPEARANCE] "
            f"Index: {planetary_state['planetary_appearance_index']:.4f} | "
            f"regime: {planetary_state['timing_regime']}"
        )

        r_geo, _ = earth.harmonize_brain_and_dna(
            brain_phase=human_brain_phase,
            dna_signal=np.ones(32, dtype=np.float64),
        )

        print(
            " -> [BIOLOGY] "
            f"Bio-planetary phase synchronization r_geo: {r_geo:.4f}"
        )

        effective_external_pressure = max(
            0.1,
            50.0 - solar_energy_flux - (max(r_geo, 0.0) * 20.0),
        )

        R_t = framework_core.update_state(
            coupling_strength=15.0,
            external_pressure=effective_external_pressure / 10.0,
        )

        continuum_state = framework_core.calculate_continuum_appearance()

        current_system_coherence = float(
            continuum_state["endogenous_structural_coherence"]
        )

        upstream_j_flux = float(
            continuum_state["j_flux"]
        )

        manifested_mass_anchor = float(
            continuum_state["manifested_mass"]
        )

        _, stabilized_j_flux_input = earth.harmonize_brain_and_dna(
            brain_phase=human_brain_phase,
            dna_signal=upstream_j_flux,
        )

        biophoton_signal, hologram_density = dna_oscillator.emit_biophotons(
            j_flux=float(stabilized_j_flux_input),
            brain_modulation_frequency=active_fundamental,
        )

        phantom_coherence = dna_oscillator.stabilize_phantom(
            modulated_signal=biophoton_signal,
            current_system_coherence=current_system_coherence,
        )

        molecular_cluster.apply_biophoton_forcing(
            biophoton_signal=biophoton_signal,
            phantom_coherence=phantom_coherence,
        )

        molecular_coherence = molecular_cluster.synchronize_molecular_bonds(
            dt=0.01,
        )

        chemical_state = molecular_cluster.calculate_chemical_appearance()

        print(
            " -> [FRAMEWORK] "
            f"R(t): {R_t:.4f} | "
            f"C(t) proxy: {current_system_coherence:.4f} | "
            f"J_flux: {upstream_j_flux:.4f} | "
            f"M(t): {manifested_mass_anchor:.4f}"
        )

        print(
            " -> [RESULT] "
            f"DNA hologram density: {hologram_density:.4f} | "
            f"Phantom coherence: {phantom_coherence:.4f} | "
            f"Molecular coherence: {molecular_coherence:.4f}"
        )

        print(
            " -> [CHEMISTRY] "
            f"Chemical appearance index: "
            f"{chemical_state['chemical_appearance_index']:.4f} | "
            f"bonding regime: {chemical_state['bonding_regime']}"
        )


if __name__ == "__main__":
    run_demo()
