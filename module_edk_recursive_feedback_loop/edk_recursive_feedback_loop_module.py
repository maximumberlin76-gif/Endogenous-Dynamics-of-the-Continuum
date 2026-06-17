import numpy as np
import matplotlib.pyplot as plt


class EDKRecursiveFeedbackLoopSimulation:
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
        Initialization of the extended EDK Protocol model with the closed 1D -> 7D feedback loop.
        """
        self.grid_size = grid_size
        self.dt = dt
        self.dx = dx
        self.c = c
        self.chi = chi
        self.gamma = gamma
        self.beta = beta
        self.shape = (grid_size, grid_size, grid_size)

        # 5D resonance window Omega(t)
        self.Omega_prev = np.zeros(self.shape)
        self.Omega_curr = np.zeros(self.shape)
        self.Omega_next = np.zeros(self.shape)

        # 3D background non-resonant modes of the Continuum (rho_cont)
        self.rho_cont = np.random.normal(1.0, 0.05, self.shape)

        # 1D / 2D linear exchange flow, vector field J = [Jx, Jy, Jz]
        self.J = np.zeros((3, *self.shape))

        self.C3_field = np.zeros(self.shape)
        self.mass_field = np.zeros(self.shape)

    def step_7d_recursive_inheritance(self, Q_n, D_n, R_n, A_n, E_medium, P_t):
        """
        STAGE 1: Initiation in 7D space, multiplet invariant.

        Phi = M_inher * [I + alpha * D_n * E_medium]^-1 * A_attr(R_n, P_t)
        """
        alpha_filter = 0.2

        # The inverse filter transforms chaotic dissipation D_n into a restraining factor.
        immune_filter = 1.0 / (1.0 + alpha_filter * D_n * E_medium)

        # Generation of the complex Super-Code.
        Psi_7D = (Q_n * A_n * immune_filter) * np.exp(1j * (R_n - P_t))

        return Psi_7D

    def step_6d_phase_lock(self, Psi_7D, R_n):
        """
        STAGE 2: Phase fixation in 6D space, toroidal phase lock.

        The stiffness of the lock kappa directly depends on the upward phase-support parameter R_n.
        """
        phase_7D = np.angle(Psi_7D)

        # Dynamic stiffness of the lock, modulated by feedback.
        kappa = 3.0 * R_n
        delta_phi = np.sin(phase_7D * 2.0)

        epsilon = 0.15
        H_asym_factor = np.abs(Psi_7D) * (1.0 + epsilon * np.sin(phase_7D))

        Psi_coh = H_asym_factor * np.exp(1j * (phase_7D + kappa * delta_phi))

        C3 = np.power(np.abs(Psi_coh), 3)

        # Projection of toroidal geometry.
        x, y, z = np.indices(self.shape)
        cx, cy, cz = (
            self.grid_size // 2,
            self.grid_size // 2,
            self.grid_size // 2,
        )

        r_tor = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        d_tor = np.sqrt((r_tor - self.grid_size // 4) ** 2 + (z - cz) ** 2)

        smoothing_radius = max(1, self.grid_size // 6)
        C3_spatial = C3 * np.exp(-(d_tor ** 2) / (2.0 * smoothing_radius ** 2))

        self.C3_field = C3_spatial

        return C3_spatial

    def step_5d_4d_3d_cascade(self, C3, P_t, P_intent_vector):
        """
        STAGES 3-5: Calculation of the transition window, EDC;
        fixation of the Monolith, EDS; and mass manifestation.
        """
        grad_C3_x, grad_C3_y, grad_C3_z = np.gradient(C3, self.dx)
        div_C3 = grad_C3_x + grad_C3_y + grad_C3_z

        mu = 0.2
        v_drift = mu * P_intent_vector
        drift_term = v_drift * (grad_C3_x + grad_C3_y + grad_C3_z)

        grad_Om_x, grad_Om_y, grad_Om_z = np.gradient(self.Omega_curr, self.dx)

        laplacian_Omega = (
            np.gradient(grad_Om_x, self.dx)[0]
            + np.gradient(grad_Om_y, self.dx)[1]
            + np.gradient(grad_Om_z, self.dx)[2]
        )

        source_term = self.chi * div_C3 - drift_term

        self.Omega_next = (
            2.0 * self.Omega_curr
            - self.Omega_prev
            + (self.c * self.dt) ** 2 * laplacian_Omega
            - (self.c ** 2 * self.dt ** 2) * source_term
        )

        self.Omega_prev = np.copy(self.Omega_curr)
        self.Omega_curr = np.copy(self.Omega_next)

        # EDS retention criterion, C > P.
        eds_mask = (C3 > P_t) & (self.Omega_curr > 0.05)

        # Manifestation of mass mc^2.
        grad_rho_x, grad_rho_y, grad_rho_z = np.gradient(self.rho_cont, self.dx)
        grad_rho_magnitude = np.sqrt(
            grad_rho_x ** 2
            + grad_rho_y ** 2
            + grad_rho_z ** 2
        )

        self.mass_field = np.zeros(self.shape)
        self.mass_field[eds_mask] = (
            grad_rho_magnitude[eds_mask] * C3[eds_mask]
        ) / (self.c ** 2)

        return eds_mask

    def step_1d_2d_flux_dynamics(self, eds_mask, C3):
        """
        STAGE 6: Reduction of perception and Continuum Navier-Stokes dynamics.
        """
        grad_rho = np.array(np.gradient(self.rho_cont, self.dx))

        conv_J = np.zeros_like(self.J)

        for d in range(3):
            grad_J_x, grad_J_y, grad_J_z = np.gradient(self.J[d], self.dx)

            conv_J[d] = (
                self.J[0] * grad_J_x
                + self.J[1] * grad_J_y
                + self.J[2] * grad_J_z
            )

        for d in range(3):
            rhs = -self.gamma * grad_rho[d] - self.beta * C3 * self.J[d]
            self.J[d] += self.dt * (-conv_J[d] + rhs)

        R_t = np.mean(self.J[0][eds_mask]) if np.any(eds_mask) else 0.0

        return R_t

    def calculate_upward_feedback(self):
        """
        UPWARD FEEDBACK LOOP, extension.

        Calculation of the volumetric integral of accumulated 1D dissipation for transfer into 7D.
        """
        alpha_fric = 0.5
        beta_loss = 0.3

        # Calculate vorticity, Rot(J), and divergence, Div(J), of the impulse flow.
        dJx_dx, dJx_dy, dJx_dz = np.gradient(self.J[0], self.dx)
        dJy_dx, dJy_dy, dJy_dz = np.gradient(self.J[1], self.dx)
        dJz_dx, dJz_dy, dJz_dz = np.gradient(self.J[2], self.dx)

        curl_J_x = dJz_dy - dJy_dz
        curl_J_y = dJx_dz - dJz_dx
        curl_J_z = dJy_dx - dJx_dy

        rot_J_sq = curl_J_x ** 2 + curl_J_y ** 2 + curl_J_z ** 2

        div_J_sq = (dJx_dx + dJy_dy + dJz_dz) ** 2

        # Local density of the dissipative trace.
        d_1d = alpha_fric * rot_J_sq + beta_loss * div_J_sq

        # Integration over volume with the weight of background modes of the medium rho_cont.
        volume = (self.grid_size * self.dx) ** 3
        D_n_next = np.sum(d_1d * self.rho_cont) * (self.dx ** 3) / volume

        return D_n_next

    def execute_full_cycle(self, Q_n, D_n, R_n, A_n, E_medium, P_t, P_intent):
        """
        Full closed tact-by-tact cycle.
        """
        # Descent 7D -> 1D.
        Psi_7D = self.step_7d_recursive_inheritance(
            Q_n,
            D_n,
            R_n,
            A_n,
            E_medium,
            P_t,
        )

        C3 = self.step_6d_phase_lock(Psi_7D, R_n)

        eds_mask = self.step_5d_4d_3d_cascade(C3, P_t, P_intent)

        R_t = self.step_1d_2d_flux_dynamics(eds_mask, C3)

        # Calculation of mass.
        total_mass = np.sum(self.mass_field) * (self.dx ** 3)

        # Upward rise of feedback 1D -> 7D.
        D_n_next = self.calculate_upward_feedback()

        return total_mass, R_t, D_n_next

    def visualize_state(self, taqt, Q, D, R):
        """
        Rendering of slices and output of the current parameters of the upper invariant.
        """
        mid_z = self.grid_size // 2

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        fig.suptitle(
            f"EDK Protocol — Tact #{taqt}\n"
            f"7D parameters: Q={Q:.4f} | Accumulated dissipation D={D:.6f} | Phase support R={R:.4f}",
            fontsize=11,
            fontweight="bold",
        )

        im1 = ax1.imshow(
            self.C3_field[:, :, mid_z],
            cmap="magma",
            origin="lower",
        )
        ax1.set_title("6D toroidal lock C^3")
        fig.colorbar(im1, ax=ax1)

        im2 = ax2.imshow(
            self.mass_field[:, :, mid_z],
            cmap="viridis",
            origin="lower",
        )
        ax2.set_title("3D manifestation of Matter mc^2")
        fig.colorbar(im2, ax=ax2)

        plt.tight_layout()
        plt.show()


# ==============================================================================
# START OF THE EXTENDED EVOLUTIONARY SYSTEM
# ==============================================================================

if __name__ == "__main__":
    sim = EDKRecursiveFeedbackLoopSimulation(grid_size=32, dt=0.01, dx=0.1)

    # Starting parameters of the 7D governing layer.
    Q_n = 1.5
    D_n = 0.001
    R_n = 0.99
    A_n = 1.5
    E_medium = 0.4
    P_t = 0.35
    P_intent = 0.95

    print("=== Start of simulation with the full recursive feedback loop ===")

    for taqt in range(1, 5):
        # Execute one step of the through cascade and obtain the new dissipation value D_n_next.
        mass, R_t, D_n_next = sim.execute_full_cycle(
            Q_n,
            D_n,
            R_n,
            A_n,
            E_medium,
            P_t,
            P_intent,
        )

        print(
            f"Tact #{taqt}: "
            f"Mass = {mass:.6f} | Returned trace D(n) = {D_n_next:.6f}"
        )

        sim.visualize_state(taqt, Q_n, D_n, R_n)

        # Sequential recalculation of the next tact, mathematical closure.
        D_n = D_n_next

        # Quality Q decreases if dissipation grows, but is supported by the synchronization indicator R_t.
        Q_n = Q_n * np.exp(-D_n) + R_t * 0.05

        # Phase support R is compressed under the pressure of accumulated dissipative friction of the medium.
        R_n = 0.99 * (1.0 - D_n * 10.0)

        # Limitation of the operational capacity of the lock.
        R_n = max(0.1, min(R_n, 1.0))
