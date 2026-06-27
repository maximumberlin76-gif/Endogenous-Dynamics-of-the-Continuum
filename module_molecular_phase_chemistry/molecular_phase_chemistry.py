from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from module_framework_core.framework_core import ContinuumSimulation
from module_wave_genetics.wave_genetics_dna_oscillator import (
    WaveGeneticsDNAOscillator,
)


__all__ = [
    "MolecularPhaseChemistry",
    "run_demo",
]


class MolecularPhaseChemistry:
    """
    Conceptual module for molecular phase chemistry.

    The module represents molecular bonding not as a purely mechanical
    interaction between static particles, but as topological phase closure
    of nonlinear oscillator groups inside a liquid medium.

    Within the open nonlinear dissipative dynamic Continuum, chemical bonds
    are modeled as retained phase relations between atomic or molecular
    resonators.

    Controlled distinctions preserved by this module:
    - J_flux belongs to the upstream Continuum / framework layer.
    - biophoton_signal is received from the wave-genetic layer.
    - binding_matrix is a local molecular phase-bonding matrix.
    - molecular_coherence is a reduced molecular phase-coherence indicator.
    - medium_memory_tensor is a local memory-bearing substrate tensor.
    - chemical_appearance_index is a local chemical manifestation index.
    - none of these local parameters replaces the complete theoretical C(t).
    """

    STABLE_CHEMICAL_PHASE_MANIFESTATION = "STABLE CHEMICAL PHASE MANIFESTATION"
    PARTIAL_CHEMICAL_PHASE_MANIFESTATION = "PARTIAL CHEMICAL PHASE MANIFESTATION"
    WEAK_CHEMICAL_PHASE_MANIFESTATION = (
        "WEAK OR UNSTABLE CHEMICAL PHASE MANIFESTATION"
    )

    def __init__(
        self,
        num_resonators: int = 32,
        medium_viscosity: float = 0.1,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the molecular phase-chemistry cluster.

        Parameters
        ----------
        num_resonators:
            Number of atomic or molecular oscillators in the cluster.
        medium_viscosity:
            Viscosity of the liquid medium.
        seed:
            Optional random seed for reproducible experiments.
        """
        self.num_resonators = self._validate_positive_integer(
            "num_resonators",
            num_resonators,
        )

        self.eta = self._validate_non_negative_finite(
            "medium_viscosity",
            medium_viscosity,
        )

        self.rng = np.random.default_rng(seed)

        self.atomic_frequencies = self.rng.uniform(
            20.0,
            50.0,
            self.num_resonators,
        )

        self.molecular_phases = self.rng.uniform(
            0.0,
            2.0 * np.pi,
            self.num_resonators,
        )

        self.binding_matrix = np.zeros(
            (self.num_resonators, self.num_resonators),
            dtype=np.float64,
        )

        self.medium_memory_tensor = np.zeros(
            (self.num_resonators, self.num_resonators),
            dtype=np.float64,
        )

        self.chemical_appearance_index = 0.0
        self.last_molecular_coherence = 0.0
        self.last_active_bond_density = 0.0
        self.last_medium_memory_strength = 0.0
        self.last_viscosity_penalty = 1.0 / (1.0 + self.eta)
        self.last_phantom_coherence = 0.0
        self.last_biophoton_signal_energy = 0.0

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

        if array.ndim != 1:
            raise ValueError(f"{name} must be a one-dimensional array.")

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} must contain only finite values.")

        return array

    def apply_biophoton_forcing(
        self,
        biophoton_signal: np.ndarray,
        phantom_coherence: float,
    ) -> None:
        """
        Apply modeled biophoton or phantom-field forcing to the liquid medium.

        Parameters
        ----------
        biophoton_signal:
            Modeled biophoton signal generated by the DNA oscillator layer.
        phantom_coherence:
            Retained phantom-field coherence received from the wave-genetic layer.
        """
        biophoton_signal = self._validate_signal(
            biophoton_signal,
            "biophoton_signal",
        )

        phantom_coherence = self._validate_non_negative_finite(
            "phantom_coherence",
            phantom_coherence,
        )

        phantom_coherence = float(
            np.clip(
                phantom_coherence,
                0.0,
                1.0,
            )
        )

        self.last_phantom_coherence = phantom_coherence

        if biophoton_signal.size == 0:
            self.last_biophoton_signal_energy = 0.0
            self._validate_state()
            return

        self.last_biophoton_signal_energy = float(
            np.mean(
                np.square(biophoton_signal),
            )
        )

        if biophoton_signal.size == 1:
            forcing_pattern = np.full(
                self.num_resonators,
                float(biophoton_signal[0]),
                dtype=np.float64,
            )
        else:
            forcing_pattern = np.interp(
                np.linspace(
                    0.0,
                    1.0,
                    self.num_resonators,
                    dtype=np.float64,
                ),
                np.linspace(
                    0.0,
                    1.0,
                    biophoton_signal.size,
                    dtype=np.float64,
                ),
                biophoton_signal,
            )

        forcing_amplitude = forcing_pattern * phantom_coherence

        self.medium_memory_tensor += (
            np.outer(
                forcing_amplitude,
                forcing_amplitude,
            )
            * 0.1
        )

        self.medium_memory_tensor = np.clip(
            self.medium_memory_tensor,
            -2.0,
            2.0,
        )

        self._validate_state()

    def synchronize_molecular_bonds(
        self,
        dt: float = 0.01,
    ) -> float:
        """
        Execute one tact of molecular phase-closure dynamics.

        Parameters
        ----------
        dt:
            Discrete time step for phase evolution.

        Returns
        -------
        float:
            Reduced molecular phase-coherence indicator of the cluster.
        """
        dt = self._validate_positive_finite("dt", dt)

        phase_difference = (
            self.molecular_phases[None, :]
            - self.molecular_phases[:, None]
        )

        baseline_coupling = np.ones(
            (self.num_resonators, self.num_resonators),
            dtype=np.float64,
        )

        total_coupling = (
            baseline_coupling + self.medium_memory_tensor
        ) / (1.0 + self.eta)

        np.fill_diagonal(total_coupling, 0.0)

        phase_acceleration = np.sum(
            total_coupling * np.sin(phase_difference),
            axis=1,
        )

        self.molecular_phases = (
            self.molecular_phases
            + (self.atomic_frequencies + phase_acceleration) * dt
        ) % (2.0 * np.pi)

        updated_phase_difference = (
            self.molecular_phases[:, None]
            - self.molecular_phases[None, :]
        )

        self.binding_matrix = np.cos(updated_phase_difference)
        np.fill_diagonal(self.binding_matrix, 0.0)

        molecular_coherence = float(
            abs(
                np.mean(
                    np.exp(1j * self.molecular_phases),
                )
            )
        )

        self._update_chemical_appearance(
            molecular_coherence=molecular_coherence,
        )

        self._validate_state()

        return molecular_coherence

    def _update_chemical_appearance(
        self,
        molecular_coherence: float,
    ) -> None:
        """
        Update the chemical appearance index.

        The chemical appearance index describes how strongly the molecular
        phase-bonding structure is manifested as a retained chemical regime.
        """
        molecular_coherence = self._validate_non_negative_finite(
            "molecular_coherence",
            molecular_coherence,
        )

        molecular_coherence = float(
            np.clip(
                molecular_coherence,
                0.0,
                1.0,
            )
        )

        positive_bonds = self.binding_matrix > 0.85

        active_bond_density = float(
            np.sum(positive_bonds)
            / max(
                1,
                self.num_resonators * (self.num_resonators - 1),
            )
        )

        medium_memory_strength = float(
            np.mean(
                np.abs(self.medium_memory_tensor),
            )
        )

        viscosity_penalty = 1.0 / (1.0 + self.eta)

        self.last_molecular_coherence = molecular_coherence
        self.last_active_bond_density = active_bond_density
        self.last_medium_memory_strength = medium_memory_strength
        self.last_viscosity_penalty = float(viscosity_penalty)

        self.chemical_appearance_index = float(
            molecular_coherence
            * (1.0 + active_bond_density)
            * (1.0 + medium_memory_strength)
            * viscosity_penalty
        )

    def calculate_chemical_appearance(self) -> dict[str, float | str]:
        """
        Calculate the current appearance state of the molecular cluster.

        Returns
        -------
        dict[str, float | str]:
            Chemical appearance index, bonding regime, active bond density,
            medium-memory strength, viscosity penalty, molecular coherence,
            phantom coherence, and biophoton signal energy.
        """
        positive_bonds = self.binding_matrix > 0.85

        active_bond_density = float(
            np.sum(positive_bonds)
            / max(
                1,
                self.num_resonators * (self.num_resonators - 1),
            )
        )

        medium_memory_strength = float(
            np.mean(
                np.abs(self.medium_memory_tensor),
            )
        )

        viscosity_penalty = 1.0 / (1.0 + self.eta)

        if self.chemical_appearance_index >= 1.2:
            bonding_regime = self.STABLE_CHEMICAL_PHASE_MANIFESTATION
        elif self.chemical_appearance_index >= 0.6:
            bonding_regime = self.PARTIAL_CHEMICAL_PHASE_MANIFESTATION
        else:
            bonding_regime = self.WEAK_CHEMICAL_PHASE_MANIFESTATION

        return {
            "chemical_appearance_index": float(self.chemical_appearance_index),
            "bonding_regime": bonding_regime,
            "active_bond_density": active_bond_density,
            "medium_memory_strength": medium_memory_strength,
            "viscosity_penalty": float(viscosity_penalty),
            "molecular_coherence": float(self.last_molecular_coherence),
            "phantom_coherence": float(self.last_phantom_coherence),
            "biophoton_signal_energy": float(self.last_biophoton_signal_energy),
        }

    def demanifest_chemical_bonds(self) -> None:
        """
        Dissolve chemical phase bonds through phase opening.
        """
        print(
            "[MOLECULAR] Molecular phase-bonding structure is being released. "
            "The cluster transitions into uncoupled phase modes."
        )

        self.binding_matrix = np.zeros(
            (self.num_resonators, self.num_resonators),
            dtype=np.float64,
        )

        self.medium_memory_tensor *= 0.0
        self.chemical_appearance_index = 0.0
        self.last_molecular_coherence = 0.0
        self.last_active_bond_density = 0.0
        self.last_medium_memory_strength = 0.0

        self._validate_state()

    def _validate_state(self) -> None:
        expected_vector_shape = (self.num_resonators,)
        expected_matrix_shape = (
            self.num_resonators,
            self.num_resonators,
        )

        if self.atomic_frequencies.shape != expected_vector_shape:
            raise RuntimeError("atomic_frequencies has invalid shape.")

        if self.molecular_phases.shape != expected_vector_shape:
            raise RuntimeError("molecular_phases has invalid shape.")

        if self.binding_matrix.shape != expected_matrix_shape:
            raise RuntimeError("binding_matrix has invalid shape.")

        if self.medium_memory_tensor.shape != expected_matrix_shape:
            raise RuntimeError("medium_memory_tensor has invalid shape.")

        arrays = {
            "atomic_frequencies": self.atomic_frequencies,
            "molecular_phases": self.molecular_phases,
            "binding_matrix": self.binding_matrix,
            "medium_memory_tensor": self.medium_memory_tensor,
        }

        for name, array in arrays.items():
            if not np.all(np.isfinite(array)):
                raise FloatingPointError(f"{name} contains non-finite values.")

        scalar_fields = {
            "chemical_appearance_index": self.chemical_appearance_index,
            "last_molecular_coherence": self.last_molecular_coherence,
            "last_active_bond_density": self.last_active_bond_density,
            "last_medium_memory_strength": self.last_medium_memory_strength,
            "last_viscosity_penalty": self.last_viscosity_penalty,
            "last_phantom_coherence": self.last_phantom_coherence,
            "last_biophoton_signal_energy": self.last_biophoton_signal_energy,
        }

        for name, value in scalar_fields.items():
            if not np.isfinite(float(value)):
                raise FloatingPointError(f"{name} is non-finite.")

        if self.chemical_appearance_index < 0.0:
            raise RuntimeError("chemical_appearance_index must be non-negative.")

        if self.last_molecular_coherence < 0.0:
            raise RuntimeError("last_molecular_coherence must be non-negative.")

        if self.last_phantom_coherence < 0.0:
            raise RuntimeError("last_phantom_coherence must be non-negative.")


def run_demo() -> None:
    macro_continuum = ContinuumSimulation(
        num_layers=4,
        dt=0.01,
        seed=42,
    )

    dna_oscillator = WaveGeneticsDNAOscillator(
        sequence_length=32,
        base_frequency=320.0,
        seed=76,
    )

    molecular_cluster = MolecularPhaseChemistry(
        num_resonators=32,
        medium_viscosity=0.1,
        seed=144,
    )

    print("=== MOLECULAR PHASE CHEMISTRY WITH APPEARANCE LAYER ===")

    R_t = macro_continuum.update_state(
        coupling_strength=12.0,
        external_pressure=0.0,
    )

    continuum_state = macro_continuum.calculate_continuum_appearance()

    current_system_coherence = float(
        continuum_state["endogenous_structural_coherence"]
    )

    upstream_j_flux = float(
        continuum_state["j_flux"]
    )

    biophoton_signal, hologram_density = dna_oscillator.emit_biophotons(
        j_flux=upstream_j_flux,
        brain_modulation_frequency=7.83,
    )

    phantom_coherence = dna_oscillator.stabilize_phantom(
        modulated_signal=biophoton_signal,
        current_system_coherence=current_system_coherence,
    )

    molecular_cluster.apply_biophoton_forcing(
        biophoton_signal=biophoton_signal,
        phantom_coherence=phantom_coherence,
    )

    print(
        "Upstream state | "
        f"R(t): {R_t:.4f} | "
        f"C(t) proxy: {current_system_coherence:.4f} | "
        f"J_flux: {upstream_j_flux:.4f} | "
        f"Hologram density: {hologram_density:.4f} | "
        f"Phantom coherence: {phantom_coherence:.4f}"
    )

    print(
        "\n[SIMULATION] Starting molecular phase alignment "
        "inside the liquid medium..."
    )

    for tact_index in range(1, 5):
        molecular_coherence = molecular_cluster.synchronize_molecular_bonds(
            dt=0.02,
        )

        appearance_state = molecular_cluster.calculate_chemical_appearance()

        print(
            f"Tact {tact_index:02d} | "
            f"Molecular coherence: {molecular_coherence:.4f} | "
            f"Chemical appearance index: "
            f"{appearance_state['chemical_appearance_index']:.4f}"
        )

        print(
            "       -> Bonding regime: "
            f"{appearance_state['bonding_regime']}"
        )

        print(
            "       -> Active bond density: "
            f"{appearance_state['active_bond_density']:.4f} | "
            "Medium memory strength: "
            f"{appearance_state['medium_memory_strength']:.4f}"
        )

    print(
        "\n[INFO] Molecular phase-chemistry simulation completed. "
        f"Hologram density: {hologram_density:.4f} | "
        f"Phantom coherence: {phantom_coherence:.4f}"
    )


if __name__ == "__main__":
    run_demo()
