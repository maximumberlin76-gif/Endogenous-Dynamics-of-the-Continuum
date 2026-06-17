import numpy as np


class EDKProtocolSimulation:
    def __init__(
        self,
        grid_size=32,
        dt=0.01,
        dx=0.1,
        c=1.0,
        chi=0.5,
        gamma=0.1,
        beta=0.05,
    ):
        """
        Initialization of the parameters of the through Continuum of the EDK Protocol.
        The 3D coordinate grid acts as a projection screen for higher-dimensional layers.
        """
        self.grid_size = grid_size
        self.dt = dt
        self.dx = dx
        self.c = c          # Speed of manifestation / wave propagation
        self.chi = chi      # Coupling coefficient between the window geometry and div(C^3)
        self.gamma = gamma  # Resistance coefficient of the non-resonant modes of the Continuum
        self.beta = beta    # Damping coefficient of the 1D impulse by the phase lock

        # Initialization of fields on the 3D discrete manifestation screen (i, j, k)
        self.shape = (grid_size, grid_size, grid_size)

        # 5D resonance window Omega(t) at the steps t, t-1, t+1, finite-difference FDTD scheme
        self.Omega_prev = np.zeros(self.shape)
        self.Omega_curr = np.zeros(self.shape)
        self.Omega_next = np.zeros(self.shape)

        # 3D background non-resonant modes of the Continuum (rho_cont)
        self.rho_cont = np.random.normal(
            1.0,
            0.05,
            self.shape,
        )  # White-noise distribution of the medium

        # 1D / 2D linear flow of exchange and impulse transfer (vector field J = [Jx, Jy, Jz])
        self.J = np.zeros((3, *self.shape))

        # State holders for monitoring
        self.C3_field = np.zeros(self.shape)
        self.mass_field = np.zeros(self.shape)

    def step_7d_recursive_inheritance(self, Q_n, D_n, R_n, A_n, E_medium, P_t):
        """
        STAGE 1: Initiation in 7D space (multiplet invariant).
        Formula: Psi_7D = Phi(Q(n), D(n), A(n))
        Architectonics: Phi = M_inher * [I + alpha * D_n * E_medium]^-1 * A_attr(R_n, P_t)
        """
        # Simulate the work of the matrix of pure inheritance M_inher and the dissipative inverse filter.
        # The inverse filter cleans the Super-Code: [1 / (1 + alpha * D_n * E_medium)]
        alpha = 0.1
        immune_filter = 1.0 / (1.0 + alpha * np.mean(D_n) * np.mean(E_medium))

        # Attractor topology tensor A_attr, modulated by synchronization R_n and pressure P_t
        # At the output, we obtain the complex matrix of the Super-Code wave function
        Psi_7D = (Q_n * A_n * immune_filter) * np.exp(
            1j * (R_n - np.mean(P_t))
        )

        return Psi_7D

    def step_6d_phase_lock(self, Psi_7D):
        """
        STAGE 2: Phase fixation in 6D space (toroidal field of reference frequencies).
        Formula: Psi_coh = U_hat_6D * Psi_7D
        Formula of cubic saturation: C^3 = Tr(|Psi_coh|^2)
        """
        # Microstructure of the phase lock:
        # U_6D = product exp(i * kappa * sin(Delta_phi)) * H_asym

        # Calculate the phase of the Super-Code
        phase_7D = np.angle(Psi_7D)

        # Model counter phase shifts Delta_phi and the sinusoidal returning lock
        kappa = 2.5  # Lock stiffness
        delta_phi = np.sin(phase_7D * 2.0)

        # Introduction of eccentricity and amplitude asymmetry (H_asym)
        epsilon = 0.15  # Asymmetry parameter excluding degeneration of the torus
        H_asym_factor = np.abs(Psi_7D) * (1.0 + epsilon * np.sin(phase_7D))

        # Resulting phase-coherent configuration of the fields
        Psi_coh = H_asym_factor * np.exp(1j * (phase_7D + kappa * delta_phi))

        # Generation of cubic nonlinear retention of volume C^3 through Tr of the density matrix
        # In spatial projection, this is the three-dimensional density of coherence "donuts"
        C3 = np.power(np.abs(Psi_coh), 3)

        # Distribute C3 across the volume of our grid, simulating spatial toroidal geometry
        # Create a toroidal distribution in the center of the computational domain
        x, y, z = np.indices(self.shape)
        cx, cy, cz = (
            self.grid_size // 2,
            self.grid_size // 2,
            self.grid_size // 2,
        )

        r_tor = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        d_tor = np.sqrt((r_tor - self.grid_size // 4) ** 2 + (z - cz) ** 2)

        # Modulate the base torus by the magnitude of the obtained cubic coherence
        C3_spatial = C3 * np.exp(
            -(d_tor ** 2) / (2.0 * (self.grid_size // 8) ** 2)
        )

        self.C3_field = C3_spatial

        return C3_spatial

    def step_5d_4d_3d_cascade(self, C3, P_t, P_intent_vector):
        """
        STAGE 3: Trajectory filtration in 5D (EDC criticality: C(t) -> P(t))
        STAGE 4: Topological Monolith in 4D (EDS stability: C(t) > P(t))
        STAGE 5: Volumetric Manifestation mc^2 in 3D
        """
        # --- STAGE 3: EDC criticality and calculation of the geometry of the Omega(t) window ---

        # Calculate the average coherence of the system for EDC evaluation
        C_t = np.mean(C3)

        # Scan nodes for the EDC condition (convergence of coherence and pressure of the medium)
        # Window equation:
        # nabla^2 Omega - (1 / c^2) partial^2 Omega / partial t^2 = chi * div(C^3)

        # Numerical calculation of div(C^3) by central differences
        grad_C3_x, grad_C3_y, grad_C3_z = np.gradient(C3, self.dx)
        div_C3 = grad_C3_x + grad_C3_y + grad_C3_z

        # Operator intention vector P (brain-continuum interface) produces drift v = mu * P
        # The drift direction locally "tilts" the Laplacian of the Omega window
        mu = 0.2
        v_drift = mu * P_intent_vector
        drift_term = v_drift * (grad_C3_x + grad_C3_y + grad_C3_z)

        # Discrete Laplacian for the current state of Omega
        grad_Om_x, grad_Om_y, grad_Om_z = np.gradient(self.Omega_curr, self.dx)

        laplacian_Omega = (
            np.gradient(grad_Om_x, self.dx)[0]
            + np.gradient(grad_Om_y, self.dx)[1]
            + np.gradient(grad_Om_z, self.dx)[2]
        )

        # FDTD wave-equation scheme: calculation of the next time step of the Omega_next window
        source_term = self.chi * div_C3 - drift_term

        self.Omega_next = (
            2.0 * self.Omega_curr
            - self.Omega_prev
            + (self.c * self.dt) ** 2 * laplacian_Omega
            - (self.c ** 2 * self.dt ** 2) * source_term
        )

        # Shift of the time layers
        self.Omega_prev = np.copy(self.Omega_curr)
        self.Omega_curr = np.copy(self.Omega_next)

        # --- STAGE 4: Check of the EDS condition (C(t) > P(t)) and fixation of the Monolith ---

        # Omega(t) passes only those zones where internal coherence has suppressed the medium
        eds_mask = (C3 > P_t) & (self.Omega_curr > 0.1)

        # --- STAGE 5: Manifestation of mass mc^2 in 3D ---

        # Local freeze-frame of quasi-rest conserves mass from the gradient of rho_cont and C^3
        grad_rho_x, grad_rho_y, grad_rho_z = np.gradient(self.rho_cont, self.dx)

        grad_rho_magnitude = np.sqrt(
            grad_rho_x ** 2
            + grad_rho_y ** 2
            + grad_rho_z ** 2
        )

        # Mass manifests strictly inside the stable EDS retention contour
        self.mass_field = np.zeros(self.shape)

        self.mass_field[eds_mask] = (
            grad_rho_magnitude[eds_mask] * C3[eds_mask]
        ) / (self.c ** 2)

        return eds_mask

    def step_1d_2d_flux_dynamics(self, eds_mask, C3):
        """
        STAGE 6: Reduction to 2D / 1D and dynamics of the exchange flow.
        Formula: partial J / partial t + (J * nabla)J = - gamma * nabla rho_cont - beta * C^3 * J
        """
        # Numerical calculation of the gradient of the non-resonant modes of the Continuum
        # academic "dark matter"
        grad_rho = np.array(np.gradient(self.rho_cont, self.dx))

        # Calculation of the convective term (J * nabla)J for each component of the vector J
        conv_J = np.zeros_like(self.J)

        for d in range(3):  # Along the axes x, y, z
            grad_J_x, grad_J_y, grad_J_z = np.gradient(self.J[d], self.dx)

            conv_J[d] = (
                self.J[0] * grad_J_x
                + self.J[1] * grad_J_y
                + self.J[2] * grad_J_z
            )

        # Update of the 1D impulse of the exchange flow J at step dt
        for d in range(3):
            # Right side: pressure of the non-resonant noise of the Continuum
            # and damping by the cubic phase lock
            rhs = -self.gamma * grad_rho[d] - self.beta * C3 * self.J[d]

            # Differential step: J_new = J_old + dt * (-(J * nabla)J + RHS)
            self.J[d] += self.dt * (-conv_J[d] + rhs)

        # Model the 2D manifestation interface (boundary of the EDS mask) through the synchronization indicator R(t)
        # Fix tangential flows at the boundaries between media
        R_t = np.mean(self.J[0][eds_mask]) if np.any(eds_mask) else 0.0

        return R_t

    def execute_full_cycle(self, Q_n, D_n, R_n, A_n, E_medium, P_t, P_intent):
        """
        Full tact-by-tact launch of the through cascade of the EDK Protocol strictly from top to bottom.
        """
        # 7D Higher Synthesis
        Psi_7D = self.step_7d_recursive_inheritance(
            Q_n,
            D_n,
            R_n,
            A_n,
            E_medium,
            P_t,
        )

        # 6D Coherent toroidal folding
        C3 = self.step_6d_phase_lock(Psi_7D)

        # 5D / 4D / 3D Filtration, EDC Criticality, EDS Stability and Manifestation of mass
        eds_mask = self.step_5d_4d_3d_cascade(C3, P_t, P_intent)

        # 2D / 1D Reduction of volume into the flat slice of perception and calculation of the exchange-flow vector
        R_t = self.step_1d_2d_flux_dynamics(eds_mask, C3)

        # Calculate the integral mass manifested in this tact
        total_manifested_mass = np.sum(self.mass_field) * (self.dx ** 3)

        return total_manifested_mass, R_t


# ==============================================================================
# PRACTICAL TESTING EXAMPLE OF THE PROTOCOL EMULATOR
# ==============================================================================

if __name__ == "__main__":
    # Initialize the computational Continuum
    sim = EDKProtocolSimulation(grid_size=16, dt=0.01, dx=0.1)

    # Set the initial parameters of the 7D Super-Code
    Q_initial = 1.0        # Initial qualitative invariants
    D_initial = [0.02]     # Dissipative inheritance of the previous tact
    R_initial = 0.95       # Initial phase synchronization
    A_initial = 1.2        # Amplitude coefficient of the attractor
    E_medium = 0.4         # Background of manifested energy of the medium
    P_t = 0.5              # Destabilizing pressure of the external medium
    P_intent_vector = 0.8  # Focusing of the operator intention (coherent ensemble)

    print("--- START OF THE THROUGH SIMULATION OF THE EDK PROTOCOL ---")

    # Simulate 5 tacts of recursive evolution of the system
    for taqt in range(1, 6):
        mass, R_sync = sim.execute_full_cycle(
            Q_initial,
            D_initial,
            R_initial,
            A_initial,
            E_medium,
            P_t,
            P_intent_vector,
        )

        print(
            f"Tact #{taqt}: "
            f"Manifested mass mc^2 = {mass:.6f} | "
            f"2D synchronization indicator R(t) = {R_sync:.6f}"
        )

        # Recursive feedback of the EDK Protocol:
        # Qualities of the next tact Q(n+1) and synchronization are recalculated
        # based on the results of the current slice
        Q_initial = Q_initial * 0.99 + R_sync * 0.01
        R_initial = R_initial * 0.95 + (1.0 if mass > 0 else 0.0) * 0.05
        D_initial = [np.mean(sim.J ** 2)]  # Accumulated dissipative trace from the exchange flow 1D
