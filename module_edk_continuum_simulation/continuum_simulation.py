from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from module_framework_core.framework_core import ContinuumSimulation


__all__ = ["ContinuumSimulation"]


if __name__ == "__main__":
    system = ContinuumSimulation(
        num_layers=8,
        dt=0.01,
        seed=42,
    )

    print("=== CONTINUUM CORE WITH APPEARANCE LAYER ===")

    for tick in range(5):
        coherence = system.update_state(
            coupling_strength=15.0,
            external_pressure=0.1,
        )

        appearance_state = system.calculate_continuum_appearance()

        print(
            f"Step {tick} | "
            f"Layer phase coherence: {coherence:.4f} | "
            f"Manifested mass: {system.M:.4f} | "
            f"J flux: {system.J_flux:.4f}"
        )

        print(
            "       -> Continuum appearance index: "
            f"{appearance_state['continuum_appearance_index']:.4f}"
        )

        print(
            "       -> Manifestation regime: "
            f"{appearance_state['manifestation_regime']}"
        )

    print("\n=== CRITICAL CONTINUUM OVERLOAD ===")

    system.update_state(
        coupling_strength=2.0,
        external_pressure=50.0,
    )

    system.run_marnov_demolition(
        external_pressure=50.0,
    )
