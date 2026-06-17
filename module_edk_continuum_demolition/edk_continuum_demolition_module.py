import numpy as np


class EDKContinuumDemolitionSimulation:
    def __init__(self, num_layers=5, dt=0.01):
        """
        Initialization of the open dynamic system of the Continuum.

        num_layers: Number of quantum layers, or fields, of the multiplet.
        """
        self.num_layers = num_layers
        self.dt = dt

        # Initial phases of the layers, chaotic state of the vacuum.
        self.phases = np.random.uniform(0, 2 * np.pi, num_layers)

        # Own frequencies of the layers, internal spectrum of the medium.
        self.omega = np.random.uniform(5.0, 15.0, num_layers)

        # System parameters.
        self.C = 1.0  # Endogenous structural coherence.
        self.M = 0.0  # Manifested mass, invariant anchor.

        # Dynamic interface tensor T_int, 3x3 for 3D manifestation.
        self.T_int = np.eye(3)

    def calculate_phi_operator(self, K):
        """
        Phi operator, Phi, phase-frequency synchronizer of nonlinear oscillators.

        K: Coupling strength, coherence of the medium.
        """
        # Matrix of phase differences between all layers of the multiplet.
        phase_diff = self.phases[:, None] - self.phases

        # Kuramoto equation for nonlinear phase synchronization.
        d_phases = self.omega + (K / self.num_layers) * np.sum(
            np.sin(phase_diff),
            axis=1,
        )

        self.phases = (self.phases + d_phases * self.dt) % (2 * np.pi)

        # Calculation of accumulated coherence, order parameter.
        r = np.abs(np.sum(np.exp(1j * self.phases))) / self.num_layers

        return r

    def update_state(self, K, P_ext):
        """
        Step of system dynamics under the influence of external forcing
        or parasitic pressure.

        P_ext: External parasitic pressure of the medium.
        """
        # 1. Work of the Phi operator.
        r = self.calculate_phi_operator(K)

        # 2. Evolution of endogenous coherence.
        # Coherence grows from synchronization of the layers,
        # but is suppressed by external pressure.
        self.C = r / (1.0 + P_ext)

        # 3. Mass synthesis, resonance window of phase transition.
        if self.C > 0.8:
            # Stabilization threshold of the multiplet.
            self.M = self.C * 10.0

            # Manifestation of mass, invariant anchor fixed.
            self.T_int = np.eye(3) * self.C

            # Interface manifested in 3D.
        else:
            # Disintegration under loss of coherence.
            self.M *= 0.1

        return r

    def run_edk_demolition(self, P_ext, mu=0.5):
        """
        Implementation of the EDK demolition protocol:
        tact-by-tact demolition under P >> C.
        """
        print(
            f"[START] Activation of the EDK demolition protocol. "
            f"External pressure P = {P_ext}"
        )

        step = 0

        while self.C > 1e-5:
            step += 1

            # Calculation of the drift velocity of the tension wave.
            v = mu * P_ext

            # THEOREM 2: Delay Scaling Law.
            t_delay = v ** (-1 / 3)

            # Tact-by-tact fall of endogenous coherence.
            self.C -= (P_ext * t_delay) * self.dt

            if self.C < 0:
                self.C = 0.0

            # Algorithm of demolition of the interface tensor T_int -> 0.
            self.T_int = self.T_int * self.C

            # Calculation of the mass gradient, normal mass shift tends to 0.
            grad_M = self.M * self.C

            # Mass demanifestation, anchor breaks, energy goes into the flow J.
            J_flux = self.M * (1.0 - self.C)

            self.M = grad_M

            print(
                f"Tact {step:02d} | "
                f"t_delay: {t_delay:.5f} | "
                f"C: {self.C:.4f} | "
                f"Mass: {self.M:.4f} | "
                f"Flow J: {J_flux:.4f}"
            )

        # Mathematical closure of the system: return into the Continuum.
        print(
            "[SHUTDOWN] Interface T_int -> 0. "
            "Matter is fully demanifested into the background modes of the Continuum."
        )

        self.T_int = np.zeros((3, 3))
        self.M = 0.0


# ==============================================================================
# TEST RUN OF THE SIMULATION
# ==============================================================================

if __name__ == "__main__":
    # Create a multiplet of quantum layers.
    system = EDKContinuumDemolitionSimulation(num_layers=8)

    print("=== STAGE 1: Formation of multiplet resonance, synthesis of structure ===")

    for tact in range(5):
        # Accumulate coherence, K=15.0;
        # external pressure is minimal, P=0.1.
        coherence = system.update_state(K=15.0, P_ext=0.1)

        print(
            f"Step {tact} | "
            f"Phase coherence of layers: {coherence:.4f} | "
            f"Manifested mass: {system.M:.2f}"
        )

    print()
    print("=== STAGE 2: Activation of critical overstrain of the Continuum ===")

    # External parasitic pressure sharply exceeds internal coherence:
    # P=50.0 >> C.
    system.update_state(K=2.0, P_ext=50.0)

    # Launch of the tact-by-tact EDK demolition process.
    system.run_edk_demolition(P_ext=50.0)
