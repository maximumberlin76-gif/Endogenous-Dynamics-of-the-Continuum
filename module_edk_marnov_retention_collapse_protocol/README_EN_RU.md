# EDK Marnov Retention-Collapse Protocol

Numerical protocol for the formation, critical loading, delayed unlocking, and measurable collapse of a retained macroscopic phase attractor in a high-density open dynamic system.

The module operates above the EDK GPU Mean-Field Phase Engine and does not duplicate its phase-evolution backend.

The protocol controls a staged experiment:

    attractor formation
    ↓
    retained-state verification
    ↓
    normalized external-pressure loading
    ↓
    approach to the critical boundary
    ↓
    accumulation of critical exposure
    ↓
    delayed unlocking of the phase-coupling node
    ↓
    controlled coupling quench
    ↓
    phase-attractor decay
    ↓
    amplitude-regime decay
    ↓
    measurement of collapse characteristics

The module is designed for high-density phase-domain systems, including simulations containing 131072 or more globally coupled domains when sufficient host or GPU memory is available.

## Repository Location

    module_edk_marnov_retention_collapse_protocol/

## Module Structure

    module_edk_marnov_retention_collapse_protocol/
    ├── README_EN_RU.md
    ├── marnov_retention_collapse_protocol.py
    ├── marnov_retention_diagnostics.py
    ├── smoke_test.py
    └── __init__.py

## Main Class

    EDKMarnovRetentionCollapseProtocol

## Configuration Class

    MarnovRetentionCollapseConfig

## Dependency

The protocol depends on:

    module_edk_gpu_mean_field_phase_engine

Required imported classes:

    EDKGPUMeanFieldPhaseEngine
    MeanFieldPhaseConfig

The protocol does not independently implement:

- NumPy or CuPy backend selection;
- CUDA device initialization;
- phase-domain initialization;
- amplitude-domain initialization;
- fixed natural frequencies;
- global mean-field Kuramoto–Sakaguchi coupling;
- backend-specific random-number generation;
- GPU-to-host field transfer.

These mechanisms remain under the control of the EDK GPU Mean-Field Phase Engine.

## Computational Purpose

The module provides a controlled numerical environment for studying the loss of a previously formed phase attractor after a system enters a critical retention regime.

The protocol must distinguish between:

    formation of a retained attractor

and:

    collapse of a retained attractor

A collapse experiment is invalid unless the initial state has first satisfied the configured retained-state criteria over a consecutive verification interval.

The module therefore does not begin with an automatically declared stable macroscopic phase node.

It first forms and verifies the attractor using measured phase and amplitude diagnostics.

## Scope of the Protocol

The protocol models:

- formation of a globally coupled phase attractor;
- retention of the phase attractor over time;
- normalized external-pressure loading;
- calculation of a diagnostic endogenous-coherence proxy;
- calculation of the retention margin;
- classification of retained, critical, and degradation regimes;
- accumulation of critical exposure;
- delayed activation of the coupling-quench process;
- tact-by-tact reduction of effective coupling;
- optional growth of phase and frequency disorder;
- decay of the phase-order parameter;
- decay of the amplitude regime;
- phase-order half-life;
- amplitude-regime half-life;
- attractor unlocking time;
- attractor collapse time;
- final-state classification.

The protocol does not independently calculate:

- complete general endogenous structural coherence C(t);
- manifested mass M(t);
- retained interface tensor T_int;
- full spatial exchange-flow field J_flux;
- molecular or biological reconstruction;
- complete plasma magnetohydrodynamics;
- physical dematerialization or materialization.

## System Class

The protocol applies to the numerical representation of an open nonlinear dissipative dynamic system.

The operational model includes:

- nonlinear phase coupling;
- amplitude relaxation;
- environmental loading;
- dissipative decay;
- externally controlled parameter changes;
- evaluation of dynamic state over time;
- inheritance of the phase and amplitude configuration from the preceding tact.

The protocol does not assume an isolated system.

External pressure, external phase forcing, and configurable noise channels may influence the phase-domain dynamics.

## Marnov Retention-Collapse Protocol

Within this module, the Marnov Retention-Collapse Protocol is defined as a controlled numerical procedure in which:

1. a phase attractor is formed;
2. the retained state is verified;
3. normalized external pressure approaches or exceeds the diagnostic retention capacity;
4. critical exposure accumulates over a finite delay interval;
5. the macroscopic phase-coupling node is unlocked;
6. effective coupling is reduced tact by tact;
7. phase and amplitude disorder are measured;
8. the decay of the retained attractor is quantified.

The protocol does not define collapse by manually assigning a final value to R(t), the amplitude state, or any downstream EDK parameter.

The result must emerge from the configured tact-by-tact dynamics.

## Phase-Order Parameter

The underlying GPU mean-field engine calculates:

    Z(t) = 1 / N sum_j exp(i theta_j)

with:

    Z(t) = R(t) exp(i Psi(t))

where:

- R(t) is the global phase-order parameter;
- Psi(t) is the global mean phase;
- theta_j is the phase of domain j;
- N is the number of phase domains.

The protocol uses:

    R_t_phase_order

as an indicator of global phase synchronization.

It does not rename R(t) as general endogenous structural coherence C(t).

## Required Semantic Distinctions

The module preserves the following distinctions:

    phase synchronization ≠ phase coherence

    R(t) ≠ C(t)

    C_proxy(t) ≠ C(t)

    phase-amplitude order proxy ≠ general endogenous structural coherence

    exchange-activity proxy ≠ J_flux

    controlled coupling quench ≠ automatically detected physical bifurcation

    amplitude decay ≠ manifested-mass decay

    retained phase attractor ≠ complete material form

These terms must not be used interchangeably.

## Diagnostic Endogenous-Coherence Proxy

Because the GPU mean-field engine does not calculate the complete EDK parameter C(t), the protocol uses:

    C_proxy(t)

C_proxy(t) is a bounded diagnostic proxy used only for protocol control and regime classification.

A possible operational form is:

    C_proxy(t)
    =
    w_R R(t)
    + w_PA PA(t)
    + w_V V_stability(t)
    + w_A A_stability(t)

where:

- R(t) is the global phase-order parameter;
- PA(t) is the phase-amplitude order proxy;
- V_stability(t) is the normalized phase-velocity stability contribution;
- A_stability(t) is the normalized amplitude-stability contribution;
- w_R, w_PA, w_V, and w_A are non-negative weights;
- the sum of all weights equals 1.

The phase-velocity stability contribution may be represented as:

    V_stability(t)
    =
    1 / (1 + sigma_v(t) / v_ref)

where:

- sigma_v(t) is the phase-velocity dispersion;
- v_ref is a positive reference scale.

The amplitude-stability contribution may be represented as:

    A_stability(t)
    =
    1 / (1 + sigma_A(t) / A_ref)

where:

- sigma_A(t) is the amplitude dispersion;
- A_ref is a positive reference scale.

C_proxy(t) remains a protocol-level numerical diagnostic.

It must not be presented as the complete calculation of C(t).

## Normalized External Pressure

The protocol uses a normalized external-pressure parameter:

    P_ext(t)

P_ext(t) must be expressed on the same bounded diagnostic scale as C_proxy(t).

Recommended range:

    0 ≤ P_ext(t) ≤ 1

Values outside the configured range must be rejected or explicitly normalized before use.

The protocol must not compare an unrestricted physical pressure value directly with a dimensionless coherence proxy.

## Retention Margin

The retention margin is:

    retention_margin(t)
    =
    C_proxy(t) - P_ext(t)

The protocol classifies three dynamic regimes using a configurable tolerance epsilon_EDC.

### Retained Regime

    retention_margin(t) > epsilon_EDC

Interpretation:

    C_proxy(t) > P_ext(t)

The diagnostic capacity of the retained phase regime exceeds the normalized external pressure.

### Critical EDC Regime

    absolute(retention_margin(t)) ≤ epsilon_EDC

Interpretation:

    C_proxy(t) approximately equals P_ext(t)

The system is located near the diagnostic retention boundary.

### Degradation Regime

    retention_margin(t) < -epsilon_EDC

Interpretation:

    C_proxy(t) < P_ext(t)

The normalized external pressure exceeds the diagnostic retention capacity.

Entering the degradation regime does not immediately force the final collapse state.

The protocol first calculates and accumulates critical exposure.

## Attractor-Formation Stage

The protocol begins with a formation stage using the configured baseline parameters:

    initial coupling strength K_initial
    baseline external forcing F_hold
    baseline forcing phase Psi_hold
    baseline normalized pressure P_hold
    configured phase lag alpha
    fixed natural frequencies
    configured phase and amplitude noise

At every tact, the protocol records:

    R(t)
    Psi(t)
    phase-amplitude order proxy
    mean phase velocity
    phase-velocity dispersion
    mean amplitude
    amplitude dispersion
    coupling-energy proxy
    C_proxy(t)
    P_ext(t)
    retention margin

The attractor is not declared formed after a single threshold crossing.

It must satisfy all configured formation criteria for a consecutive verification interval.

## Attractor-Formation Criteria

Possible formation criteria include:

    R(t) ≥ R_form_min

    phase_amplitude_order_proxy ≥ PA_form_min

    phase_velocity_dispersion ≤ V_disp_form_max

    amplitude_dispersion ≤ A_disp_form_max

    retention_margin > epsilon_EDC

The criteria must remain satisfied for:

    formation_confirmation_tacts

consecutive tacts.

Only then may the protocol enter:

    RETAINED_ATTRACTOR

## Retained-State Verification

After formation, the protocol may maintain an additional verification interval:

    retained_verification_tacts

This interval confirms that the attractor is not a temporary synchronization spike.

The verification stage measures whether the system preserves:

- global phase order;
- phase-amplitude alignment;
- low phase-velocity dispersion;
- bounded amplitude dispersion;
- a positive retention margin;
- a stable coupling-energy proxy.

The baseline retained-state values are stored for later comparison with the collapse stage.

## Critical Loading Stage

After the retained attractor is verified, the protocol changes the external loading according to a configured pressure schedule.

Supported pressure schedules may include:

    step
    linear_ramp
    smooth_ramp
    externally supplied sequence

The pressure schedule must be explicit and reproducible.

Examples:

    P_ext(t) = P_hold before loading

    P_ext(t) = P_collapse after a step transition

or:

    P_ext(t + dt)
    =
    minimum(
        P_collapse,
        P_ext(t) + pressure_ramp_rate dt
    )

The protocol records the first tact at which:

    retention_margin(t) ≤ epsilon_EDC

and the first tact at which:

    retention_margin(t) < -epsilon_EDC

## Pressure Excess

The pressure excess is:

    pressure_excess(t)
    =
    maximum(
        P_ext(t) - C_proxy(t),
        0
    )

When:

    pressure_excess(t) = 0

the critical-exposure accumulator does not increase.

When:

    pressure_excess(t) > 0

the system accumulates critical exposure according to the retardation law.

## Retardation Law

The protocol represents the configured inverse-cubic-root delay relation through:

    v(t)
    =
    mu pressure_excess(t)

and:

    tau_delay(t)
    =
    tau_0
    /
    (v(t) + epsilon_v)^(1/3)

where:

- mu is the pressure-to-collapse-velocity coefficient;
- tau_0 is the base delay scale;
- epsilon_v is a small positive numerical regularizer;
- tau_delay(t) is the instantaneous diagnostic delay scale.

Equivalent notation:

    tau_delay(t) proportional to v(t)^(-1/3)

The module treats this relation as a configurable model assumption for the numerical protocol.

It is not presented by the module itself as a universally established physical law.

## Critical-Exposure Accumulator

The protocol does not unlock the phase node immediately after one threshold crossing.

Critical exposure accumulates as:

    critical_exposure(t + dt)
    =
    critical_exposure(t)
    + dt / tau_delay(t)

when:

    pressure_excess(t) > 0

The phase-coupling node is unlocked when:

    critical_exposure ≥ 1

Before this condition is reached, the system remains in:

    CRITICAL_EXPOSURE

This mechanism makes tau_delay operationally affect the trigger time.

## Recovery Before Unlocking

If the retention margin becomes positive again before:

    critical_exposure ≥ 1

the protocol may use one of two configured modes:

    persistent exposure
    decaying exposure

In persistent mode, accumulated exposure remains unchanged.

In decaying mode:

    critical_exposure(t + dt)
    =
    maximum(
        0,
        critical_exposure(t)
        - exposure_recovery_rate dt
    )

The selected mode must be recorded in the protocol configuration and logs.

## Phase-Node Unlocking

When:

    critical_exposure ≥ 1

the protocol records:

    unlock_tact
    unlock_time
    R_unlock
    phase_amplitude_order_unlock
    amplitude_mean_unlock
    amplitude_dispersion_unlock
    C_proxy_unlock
    P_ext_unlock
    retention_margin_unlock
    tau_delay_unlock

The protocol then enters:

    PHASE_NODE_UNLOCKED

The effective coupling is not necessarily changed discontinuously to a hard-coded value.

A configurable coupling-quench law is used.

## Effective Coupling Quench

The effective coupling after unlocking may evolve as:

    K_eff(t + dt)
    =
    K_floor
    + (
        K_eff(t) - K_floor
      )
      exp(-dt / tau_K)

where:

- K_floor is the minimum retained coupling;
- tau_K is the coupling-quench time scale.

An explicit instantaneous-quench mode may also be supported:

    K_eff = K_floor

but it must be identified in the configuration as:

    instantaneous coupling quench

The protocol must not describe an externally imposed change of K as an automatically discovered internal bifurcation.

## Growth of Phase Disorder

After unlocking, the protocol may increase phase disorder through configurable channels.

Possible channels:

    phase_noise_strength
    natural-frequency-dispersion multiplier
    external-forcing removal
    forcing-phase displacement
    Sakaguchi phase-lag modification

A possible natural-frequency-dispersion control is:

    omega_effective_i
    =
    omega_mean
    + frequency_dispersion_multiplier
      (
        omega_i - omega_mean
      )

The original natural-frequency array remains unchanged.

The protocol applies a temporary effective transformation rather than regenerating natural frequencies at every tact.

## External Forcing

External forcing is independent of the internal mean phase.

The forcing term remains:

    F_ext sin(Psi_ext - theta_i)

where:

- F_ext is the external forcing density;
- Psi_ext is the external forcing phase.

The protocol may reduce F_ext after unlocking, but must not silently replace Psi_ext with the current global mean phase Psi(t).

## Amplitude-Regime Decay

The protocol may apply an additional post-unlock amplitude-decay contribution.

A numerically stable exponential form is:

    A_i(t + dt)
    =
    A_floor
    + (
        A_i(t) - A_floor
      )
      exp(-lambda_A(t) dt)

where:

    lambda_A(t)
    =
    amplitude_decay_scale
    /
    maximum(
        tau_delay(t),
        tau_min
    )

and:

- A_floor is the configured minimum amplitude;
- tau_min prevents numerical divergence;
- amplitude_decay_scale controls the additional collapse-stage damping.

This contribution is applied separately from the baseline amplitude-relaxation law of the GPU mean-field engine.

The module does not identify amplitude decay with physical mass dematerialization.

## No Direct M(t) Assignment

The protocol must not use operations such as:

    M(t) = constant C_proxy(t)

or:

    M(t + dt) = decay_factor M(t)

The module does not calculate M(t).

Any downstream relationship between attractor collapse, T_int, J_flux, and M(t) belongs to a separate EDK integration layer.

## No Direct T_int Assignment

The protocol does not define:

    T_int = identity matrix C_proxy(t)

The module records phase and amplitude collapse diagnostics only.

T_int must be calculated by a dedicated retained-interface or integration module.

## J_flux Boundary

The protocol does not calculate the complete spatial exchange-flow field J_flux.

A scalar diagnostic may be named:

    exchange_activity_proxy

A possible bounded diagnostic form may combine:

    mean amplitude
    R(t)
    phase-amplitude order proxy
    phase-velocity stability

This scalar must not be renamed J_flux.

The complete J_flux field requires:

- spatial direction;
- local exchange topology;
- temporal evolution;
- divergence;
- curl;
- coupling with the retained interface;
- coupling with the background modes of the Continuum.

## Protocol States

The protocol state machine may contain:

    INITIALIZED

    FORMING_ATTRACTOR

    RETAINED_ATTRACTOR

    CRITICAL_APPROACH

    CRITICAL_EXPOSURE

    PHASE_NODE_UNLOCKED

    COLLAPSE_ACTIVE

    DEGRADED_PHASE_REGIME

    COLLAPSE_COMPLETED

    COLLAPSE_NOT_REACHED

State transitions must be determined by explicit criteria and logged at the corresponding tact.

## Collapse Criteria

The collapse stage must be evaluated through measured dynamics.

Possible phase-collapse criteria:

    R(t) ≤ R_collapse_threshold

or:

    R(t) ≤ phase_order_fraction
           R_unlock

Possible phase-amplitude criteria:

    phase_amplitude_order_proxy
    ≤ PA_collapse_threshold

Possible dispersion criteria:

    phase_velocity_dispersion
    ≥ V_disp_collapse_threshold

Possible combined criterion:

    phase collapse criterion
    and
    phase-amplitude collapse criterion
    and
    minimum post-unlock duration

The selected criterion must be explicit in the configuration.

## Phase-Order Half-Life

The phase-order half-life is measured relative to the unlock state.

Define:

    R_half_target
    =
    0.5 R_unlock

The phase-order half-life is:

    t_R_half
    =
    first time after unlocking
    when
    R(t) ≤ R_half_target

If this condition is not reached during the configured observation interval, the result is:

    not reached

It must not be replaced by an artificial value.

## Amplitude-Regime Half-Life

Define the amplitude distance from the configured floor:

    D_A(t)
    =
    mean_amplitude(t) - A_floor

At unlocking:

    D_A_unlock
    =
    mean_amplitude_unlock - A_floor

The amplitude half-life target is:

    D_A_half
    =
    0.5 D_A_unlock

The amplitude-regime half-life is the first post-unlock time at which:

    D_A(t) ≤ D_A_half

If the target is not reached, the result remains:

    not reached

## Attractor Collapse Time

The attractor collapse time is measured from:

    unlock_time

to the first tact satisfying the configured collapse criterion.

The protocol stores:

    collapse_tact
    collapse_time
    collapse_duration_after_unlock

The protocol must also store cases where the attractor persists throughout the complete observation interval.

## Maximum Observation Interval

The protocol uses:

    maximum_post_unlock_tacts

or:

    maximum_post_unlock_time

to prevent an unbounded simulation.

If no collapse criterion is reached within this interval, the final state is:

    COLLAPSE_NOT_REACHED

This is a valid result.

The protocol must not force the system into the collapse state merely to complete the test.

## Core Configuration

The protocol configuration is expected to include:

    formation_maximum_tacts
    formation_confirmation_tacts
    retained_verification_tacts

    R_form_min
    phase_amplitude_form_min
    phase_velocity_dispersion_form_max
    amplitude_dispersion_form_max

    coherence_weight_R
    coherence_weight_phase_amplitude
    coherence_weight_phase_velocity
    coherence_weight_amplitude

    phase_velocity_reference
    amplitude_dispersion_reference

    retained_boundary_tolerance

    pressure_schedule
    pressure_hold
    pressure_collapse
    pressure_ramp_rate

    delay_base_tau_0
    pressure_velocity_coefficient_mu
    delay_regularization_epsilon
    minimum_delay_tau

    critical_exposure_threshold
    exposure_recovery_mode
    exposure_recovery_rate

    coupling_quench_mode
    coupling_floor
    coupling_quench_tau

    post_unlock_phase_noise_multiplier
    post_unlock_frequency_dispersion_multiplier
    post_unlock_amplitude_decay_scale

    phase_order_collapse_threshold
    phase_order_collapse_fraction
    phase_amplitude_collapse_threshold
    phase_velocity_dispersion_collapse_threshold

    maximum_post_unlock_tacts

    log_every
    field_every

## Underlying Engine Configuration

The underlying mean-field engine retains its own configuration:

    num_domains
    coupling_strength_k
    sakaguchi_phase_lag_alpha
    natural_frequency_mean
    natural_frequency_std
    external_forcing_phase
    phase_noise_strength
    amplitude_growth_rate
    amplitude_saturation_rate
    amplitude_noise_strength
    amplitude_minimum
    amplitude_maximum
    seed
    dtype
    backend
    device_id

The protocol must not silently overwrite the immutable engine configuration.

Dynamic protocol parameters such as K_eff are stored separately.

## Core Scalar Diagnostics

The protocol records:

    tact_index
    simulation_time
    protocol_state

    R_t_phase_order
    global_mean_phase
    phase_amplitude_order_proxy

    mean_phase_velocity
    phase_velocity_dispersion

    mean_amplitude
    amplitude_dispersion
    minimum_amplitude
    maximum_amplitude

    coupling_energy_proxy

    C_proxy_t
    external_pressure_P_ext
    retention_margin
    pressure_excess

    instantaneous_delay_tau
    critical_exposure

    initial_coupling_K
    effective_coupling_K
    coupling_floor_K

    effective_phase_noise_strength
    effective_frequency_dispersion_multiplier
    effective_amplitude_decay_rate

    attractor_formed
    attractor_verified
    phase_node_unlocked
    collapse_detected

    formation_tact
    unlock_tact
    collapse_tact

    phase_order_half_life
    amplitude_regime_half_life
    attractor_collapse_duration

## Full Field Snapshots

Optional field snapshots may include:

    phases
    amplitudes
    natural_frequencies
    effective_natural_frequencies
    phase_velocity
    amplitude_velocity
    phase_noise_increment
    amplitude_noise_increment

Full field snapshots must not be exported at every tact by default.

## Logging Strategy

Recommended logging:

    JSON
    → protocol state, scalar metrics, configuration, transition events

    NPZ
    → phase, amplitude, frequency, and velocity arrays

Compact metrics are written according to:

    log_every

Full field snapshots are written according to:

    field_every

Transition events should be written immediately when the protocol enters:

    RETAINED_ATTRACTOR
    CRITICAL_EXPOSURE
    PHASE_NODE_UNLOCKED
    COLLAPSE_ACTIVE
    COLLAPSE_COMPLETED
    COLLAPSE_NOT_REACHED

## Atomic Writing

JSON and NPZ outputs must be written atomically:

    temporary file
    ↓
    flush
    ↓
    fsync
    ↓
    os.replace
    ↓
    final file

This reduces the risk of incomplete protocol snapshots after interruption.

## Diagnostic Module

The file:

    marnov_retention_diagnostics.py

must generate diagnostic visualizations from the calculated protocol data.

Recommended plots:

1. R(t), phase-amplitude order proxy, and C_proxy(t);
2. normalized external pressure and retention margin;
3. critical exposure and instantaneous tau_delay;
4. initial and effective coupling K;
5. phase-velocity and amplitude dispersions;
6. mean amplitude and amplitude half-life target;
7. protocol-state transitions;
8. phase-order half-life and collapse-time markers.

The diagnostics must display the actual calculated trajectory.

They must not reconstruct a predetermined collapse curve.

## GPU Scaling

The protocol inherits O(N) global mean-field scaling from:

    EDKGPUMeanFieldPhaseEngine

The protocol must not construct:

    N × N phase-difference matrices

For:

    N = 131072

a single dense pairwise matrix would contain:

    17179869184 elements

Approximate memory for one matrix:

    float32 → 64 GiB
    float64 → 128 GiB

These values do not include additional sine arrays, temporary arrays, reductions, or memory-pool overhead.

The mean-field engine avoids this allocation.

## Backend Selection

Backend modes are inherited from the GPU mean-field engine:

    auto
    gpu
    cpu

The protocol does not implement a second independent CuPy detection mechanism.

A compatible CUDA device is verified by the underlying engine.

The protocol may run on CPU for small validation cases.

Large-scale runs should be attempted only after memory and performance benchmarking.

## Reproducibility

The protocol records:

- engine seed;
- engine configuration;
- protocol configuration;
- backend name;
- device ID;
- dtype;
- pressure schedule;
- forcing schedule;
- state-transition tacts;
- final diagnostic values.

Fixed natural frequencies must remain unchanged throughout the complete protocol.

Any effective post-unlock frequency transformation must be derived from the fixed base array.

## Failure Conditions

The protocol must report explicit failure conditions.

Examples:

    ATTRACTOR_NOT_FORMED

    ATTRACTOR_NOT_VERIFIED

    INVALID_PRESSURE_SCALE

    CRITICAL_BOUNDARY_NOT_REACHED

    UNLOCK_NOT_TRIGGERED

    COLLAPSE_NOT_REACHED

    NUMERICAL_INSTABILITY

    NON_FINITE_STATE

A failed or incomplete collapse experiment must not be reported as successful collapse.

## Basic Execution

CPU validation:

    python marnov_retention_collapse_protocol.py --backend cpu

Automatic backend selection:

    python marnov_retention_collapse_protocol.py --backend auto

Explicit GPU execution:

    python marnov_retention_collapse_protocol.py --backend gpu --device-id 0

Large-domain GPU run:

    python marnov_retention_collapse_protocol.py --backend gpu --num-domains 131072

Diagnostics:

    python marnov_retention_diagnostics.py --snapshot-dir edk_marnov_snapshots

Smoke test:

    python smoke_test.py

## Smoke-Test Requirements

The smoke test must verify:

- successful CPU initialization;
- correct import of the GPU mean-field engine;
- absence of duplicated backend initialization;
- deterministic initialization with a fixed seed;
- fixed natural frequencies;
- valid formation-stage execution;
- retained-attractor verification;
- bounded C_proxy(t);
- bounded normalized external pressure;
- correct retention-margin calculation;
- correct EDS, EDC, and degradation classification;
- finite tau_delay;
- correct critical-exposure accumulation;
- no immediate unlocking before the exposure threshold;
- correct unlock event after the threshold;
- monotonic coupling reduction after unlocking when exponential quench is selected;
- valid phase wrapping;
- finite phase and amplitude arrays;
- non-negative dispersions;
- phase-order half-life calculation;
- amplitude-regime half-life calculation;
- valid COLLAPSE_NOT_REACHED result when thresholds are not crossed;
- compact JSON export;
- NPZ field export;
- atomic file replacement;
- successful diagnostic generation from test snapshots.

## Research Status

This module is a numerical research component of the EDK computational architecture.

It provides a controlled protocol for studying:

    formation
    retention
    critical loading
    delayed unlocking
    coupling quench
    phase-attractor decay
    amplitude-regime decay

The module does not by itself establish a universal physical collapse law.

The inverse-cubic-root retardation relation is implemented as a configurable model assumption whose consequences can be numerically tested against alternative delay laws.

## License

The module inherits the license of the parent EDK repository.

---

# EDK ПРОТОКОЛ МАРНОВА ДЛЯ СРЫВА УДЕРЖАНИЯ

Численный протокол формирования, критического нагружения, задержанной разблокировки и измеряемого распада удерживаемого макроскопического фазового аттрактора в высокоплотной открытой динамической системе.

Модуль работает над EDK GPU-движком среднеполевой фазовой динамики и не дублирует его бэкенд эволюции фаз.

Протокол управляет поэтапным экспериментом:

    формирование аттрактора
    ↓
    проверка удерживаемого состояния
    ↓
    нагружение нормированным внешним давлением
    ↓
    приближение к критической границе
    ↓
    накопление критического воздействия
    ↓
    задержанная разблокировка узла фазового сопряжения
    ↓
    управляемое снятие сопряжения
    ↓
    распад фазового аттрактора
    ↓
    распад амплитудного режима
    ↓
    измерение характеристик срыва

Модуль предназначен для высокоплотных систем фазовых доменов, включая симуляции с 131072 и более глобально сопряжёнными доменами при наличии достаточного объёма памяти хоста или GPU.

## Расположение в репозитории

    module_edk_marnov_retention_collapse_protocol/

## Структура модуля

    module_edk_marnov_retention_collapse_protocol/
    ├── README_EN_RU.md
    ├── marnov_retention_collapse_protocol.py
    ├── marnov_retention_diagnostics.py
    ├── smoke_test.py
    └── __init__.py

## Основной класс

    EDKMarnovRetentionCollapseProtocol

## Класс конфигурации

    MarnovRetentionCollapseConfig

## Зависимость

Протокол зависит от:

    module_edk_gpu_mean_field_phase_engine

Необходимые импортируемые классы:

    EDKGPUMeanFieldPhaseEngine
    MeanFieldPhaseConfig

Протокол не реализует самостоятельно:

- выбор бэкенда NumPy или CuPy;
- инициализацию устройства CUDA;
- инициализацию фазовых доменов;
- инициализацию амплитудных доменов;
- фиксированные естественные частоты;
- глобальное среднеполевое сопряжение Курамото — Сакагучи;
- специализированную генерацию случайных чисел для активного бэкенда;
- передачу полей с GPU на хост.

Эти механизмы остаются под управлением EDK GPU-движка среднеполевой фазовой динамики.

## Вычислительное назначение

Модуль предоставляет управляемую численную среду для исследования потери ранее сформированного фазового аттрактора после входа системы в критический режим удержания.

Протокол должен различать:

    формирование удерживаемого аттрактора

и:

    срыв удерживаемого аттрактора

Эксперимент срыва недействителен, если исходное состояние сначала не выполнило настроенные критерии удерживаемого состояния на последовательном интервале проверки.

Поэтому модуль не начинает работу с автоматически объявленного устойчивого макроскопического фазового узла.

Сначала он формирует и проверяет аттрактор по измеряемым фазовым и амплитудным диагностическим параметрам.

## Область протокола

Протокол моделирует:

- формирование глобально сопряжённого фазового аттрактора;
- удержание фазового аттрактора во времени;
- нагружение нормированным внешним давлением;
- расчёт диагностического прокси-параметра эндогенной когерентности;
- расчёт запаса удержания;
- классификацию удерживаемого, критического и деградационного режимов;
- накопление критического воздействия;
- задержанную активацию процесса снятия сопряжения;
- потактовое уменьшение эффективного сопряжения;
- дополнительный рост фазового и частотного рассогласования;
- распад параметра фазового порядка;
- распад амплитудного режима;
- период полураспада фазового порядка;
- период полураспада амплитудного режима;
- время разблокировки аттрактора;
- время распада аттрактора;
- классификацию конечного состояния.

Протокол не вычисляет самостоятельно:

- полную общую эндогенную структурную когерентность C(t);
- проявленную массу M(t);
- тензор удерживаемого интерфейса T_int;
- полное пространственное поле сквозного потока обмена J_flux;
- молекулярную или биологическую реконструкцию;
- полную магнитогидродинамику плазмы;
- физическую дематериализацию или материализацию.

## Протокол Марнова для срыва удержания

В пределах этого модуля Протокол Марнова для срыва удержания определяется как управляемая численная процедура, в которой:

1. формируется фазовый аттрактор;
2. проверяется удерживаемое состояние;
3. нормированное внешнее давление приближается к диагностической способности удержания или превышает её;
4. критическое воздействие накапливается в течение конечного интервала задержки;
5. макроскопический узел фазового сопряжения разблокируется;
6. эффективное сопряжение уменьшается потактово;
7. измеряются фазовое и амплитудное рассогласование;
8. количественно оценивается распад удерживаемого аттрактора.

Протокол не определяет срыв посредством ручного присваивания конечного значения R(t), амплитудного состояния или любого последующего параметра EDK.

Результат должен возникать из настроенной потактовой динамики.

## Параметр фазового порядка

Базовый GPU-среднеполевой движок вычисляет:

    Z(t) = 1 / N sum_j exp(i theta_j)

при этом:

    Z(t) = R(t) exp(i Psi(t))

где:

- R(t) — глобальный параметр фазового порядка;
- Psi(t) — глобальная средняя фаза;
- theta_j — фаза домена j;
- N — число фазовых доменов.

Протокол использует:

    R_t_phase_order

как индикатор глобальной фазовой синхронизации.

Он не переименовывает R(t) в общую эндогенную структурную когерентность C(t).

## Обязательные семантические различия

Модуль сохраняет следующие различия:

    фазовая синхронизация ≠ фазовая когерентность

    R(t) ≠ C(t)

    C_proxy(t) ≠ C(t)

    фазово-амплитудный прокси-параметр ≠ общая эндогенная структурная когерентность

    прокси-параметр активности обмена ≠ J_flux

    управляемое снятие сопряжения ≠ автоматически обнаруженная физическая бифуркация

    распад амплитудного режима ≠ распад проявленной массы

    удерживаемый фазовый аттрактор ≠ полная материальная форма

Эти термины не должны использоваться как взаимозаменяемые.

## Диагностический прокси-параметр эндогенной когерентности

Поскольку GPU-среднеполевой движок не вычисляет полный параметр EDK C(t), протокол использует:

    C_proxy(t)

C_proxy(t) является ограниченным диагностическим прокси-параметром, используемым только для управления протоколом и классификации режимов.

Возможная операционная форма:

    C_proxy(t)
    =
    w_R R(t)
    + w_PA PA(t)
    + w_V V_stability(t)
    + w_A A_stability(t)

где:

- R(t) — глобальный параметр фазового порядка;
- PA(t) — фазово-амплитудный прокси-параметр;
- V_stability(t) — нормированный вклад устойчивости фазовых скоростей;
- A_stability(t) — нормированный вклад устойчивости амплитуд;
- w_R, w_PA, w_V и w_A — неотрицательные весовые коэффициенты;
- сумма всех весовых коэффициентов равна 1.

Вклад устойчивости фазовых скоростей может быть представлен как:

    V_stability(t)
    =
    1 / (1 + sigma_v(t) / v_ref)

где:

- sigma_v(t) — дисперсия фазовых скоростей;
- v_ref — положительный опорный масштаб.

Вклад устойчивости амплитуд может быть представлен как:

    A_stability(t)
    =
    1 / (1 + sigma_A(t) / A_ref)

где:

- sigma_A(t) — дисперсия амплитуд;
- A_ref — положительный опорный масштаб.

C_proxy(t) остаётся численным диагностическим параметром уровня протокола.

Он не должен представляться как полный расчёт C(t).

## Нормированное внешнее давление

Протокол использует нормированный параметр внешнего давления:

    P_ext(t)

P_ext(t) должен быть выражен в той же ограниченной диагностической шкале, что и C_proxy(t).

Рекомендуемый диапазон:

    0 ≤ P_ext(t) ≤ 1

Значения за пределами настроенного диапазона должны отклоняться или явно нормироваться до использования.

Протокол не должен напрямую сравнивать неограниченное физическое значение давления с безразмерным прокси-параметром когерентности.

## Запас удержания

Запас удержания:

    retention_margin(t)
    =
    C_proxy(t) - P_ext(t)

Протокол классифицирует три динамических режима с использованием настраиваемого допуска epsilon_EDC.

### Удерживаемый режим

    retention_margin(t) > epsilon_EDC

Интерпретация:

    C_proxy(t) > P_ext(t)

Диагностическая способность удерживаемого фазового режима превышает нормированное внешнее давление.

### Критический режим EDC

    absolute(retention_margin(t)) ≤ epsilon_EDC

Интерпретация:

    C_proxy(t) приблизительно равно P_ext(t)

Система находится вблизи диагностической границы удержания.

### Деградационный режим

    retention_margin(t) < -epsilon_EDC

Интерпретация:

    C_proxy(t) < P_ext(t)

Нормированное внешнее давление превышает диагностическую способность удержания.

Вход в деградационный режим не принуждает систему немедленно перейти в конечное состояние срыва.

Сначала протокол рассчитывает и накапливает критическое воздействие.

## Этап формирования аттрактора

Протокол начинается с этапа формирования при настроенных базовых параметрах:

    исходная константа сопряжения K_initial
    базовый внешний форсинг F_hold
    базовая фаза форсинга Psi_hold
    базовое нормированное давление P_hold
    настроенный фазовый сдвиг alpha
    фиксированные естественные частоты
    настроенный фазовый и амплитудный шум

На каждом такте протокол регистрирует:

    R(t)
    Psi(t)
    фазово-амплитудный прокси-параметр
    среднюю фазовую скорость
    дисперсию фазовых скоростей
    среднюю амплитуду
    дисперсию амплитуд
    прокси-параметр энергии сопряжения
    C_proxy(t)
    P_ext(t)
    запас удержания

Аттрактор не объявляется сформированным после однократного пересечения порога.

Он должен выполнять все настроенные критерии формирования на последовательном интервале проверки.

## Критерии формирования аттрактора

Возможные критерии формирования:

    R(t) ≥ R_form_min

    phase_amplitude_order_proxy ≥ PA_form_min

    phase_velocity_dispersion ≤ V_disp_form_max

    amplitude_dispersion ≤ A_disp_form_max

    retention_margin > epsilon_EDC

Критерии должны сохраняться в течение:

    formation_confirmation_tacts

последовательных тактов.

Только после этого протокол может перейти в состояние:

    RETAINED_ATTRACTOR

## Проверка удерживаемого состояния

После формирования протокол может поддерживать дополнительный интервал проверки:

    retained_verification_tacts

Этот интервал подтверждает, что аттрактор не является временным всплеском синхронизации.

На этапе проверки измеряется сохранение системой:

- глобального фазового порядка;
- фазово-амплитудного согласования;
- низкой дисперсии фазовых скоростей;
- ограниченной дисперсии амплитуд;
- положительного запаса удержания;
- устойчивого прокси-параметра энергии сопряжения.

Базовые значения удерживаемого состояния сохраняются для последующего сравнения с этапом срыва.

## Этап критического нагружения

После проверки удерживаемого аттрактора протокол изменяет внешнее нагружение в соответствии с настроенным профилем давления.

Поддерживаемые профили давления могут включать:

    step
    linear_ramp
    smooth_ramp
    externally supplied sequence

Профиль давления должен быть явным и воспроизводимым.

Примеры:

    P_ext(t) = P_hold до начала нагружения

    P_ext(t) = P_collapse после ступенчатого перехода

или:

    P_ext(t + dt)
    =
    minimum(
        P_collapse,
        P_ext(t) + pressure_ramp_rate dt
    )

Протокол регистрирует первый такт, на котором:

    retention_margin(t) ≤ epsilon_EDC

и первый такт, на котором:

    retention_margin(t) < -epsilon_EDC

## Превышение давления

Превышение давления:

    pressure_excess(t)
    =
    maximum(
        P_ext(t) - C_proxy(t),
        0
    )

Когда:

    pressure_excess(t) = 0

аккумулятор критического воздействия не увеличивается.

Когда:

    pressure_excess(t) > 0

система накапливает критическое воздействие в соответствии с ретардационным законом.

## Ретардационный закон

Протокол представляет настроенное соотношение задержки, обратно пропорциональной кубическому корню, через:

    v(t)
    =
    mu pressure_excess(t)

и:

    tau_delay(t)
    =
    tau_0
    /
    (v(t) + epsilon_v)^(1/3)

где:

- mu — коэффициент преобразования превышения давления в скорость срыва;
- tau_0 — базовый масштаб задержки;
- epsilon_v — малый положительный численный регуляризатор;
- tau_delay(t) — мгновенный диагностический масштаб задержки.

Эквивалентная запись:

    tau_delay(t) пропорционально v(t)^(-1/3)

Модуль рассматривает это соотношение как настраиваемое модельное предположение численного протокола.

Сам модуль не представляет его как универсально установленный физический закон.

## Аккумулятор критического воздействия

Протокол не разблокирует фазовый узел немедленно после одного пересечения порога.

Критическое воздействие накапливается как:

    critical_exposure(t + dt)
    =
    critical_exposure(t)
    + dt / tau_delay(t)

когда:

    pressure_excess(t) > 0

Узел фазового сопряжения разблокируется при условии:

    critical_exposure ≥ 1

До достижения этого условия система остаётся в состоянии:

    CRITICAL_EXPOSURE

Этот механизм делает tau_delay операционным параметром, влияющим на момент срабатывания.

## Восстановление до разблокировки

Если запас удержания снова становится положительным до выполнения условия:

    critical_exposure ≥ 1

протокол может использовать один из двух настраиваемых режимов:

    persistent exposure
    decaying exposure

В режиме persistent exposure накопленное воздействие сохраняется неизменным.

В режиме decaying exposure:

    critical_exposure(t + dt)
    =
    maximum(
        0,
        critical_exposure(t)
        - exposure_recovery_rate dt
    )

Выбранный режим должен быть зафиксирован в конфигурации и журналах протокола.

## Разблокировка фазового узла

Когда:

    critical_exposure ≥ 1

протокол регистрирует:

    unlock_tact
    unlock_time
    R_unlock
    phase_amplitude_order_unlock
    amplitude_mean_unlock
    amplitude_dispersion_unlock
    C_proxy_unlock
    P_ext_unlock
    retention_margin_unlock
    tau_delay_unlock

После этого протокол переходит в состояние:

    PHASE_NODE_UNLOCKED

Эффективное сопряжение не обязано изменяться скачком до жёстко заданного значения.

Используется настраиваемый закон снятия сопряжения.

## Снятие эффективного сопряжения

Эффективное сопряжение после разблокировки может изменяться как:

    K_eff(t + dt)
    =
    K_floor
    + (
        K_eff(t) - K_floor
      )
      exp(-dt / tau_K)

где:

- K_floor — минимальный удерживаемый уровень сопряжения;
- tau_K — временной масштаб снятия сопряжения.

Также может поддерживаться явный режим мгновенного снятия:

    K_eff = K_floor

но он должен быть обозначен в конфигурации как:

    instantaneous coupling quench

Протокол не должен описывать внешне заданное изменение K как автоматически обнаруженную внутреннюю бифуркацию.

## Рост фазового рассогласования

После разблокировки протокол может увеличивать фазовое рассогласование через настраиваемые каналы.

Возможные каналы:

    phase_noise_strength
    natural-frequency-dispersion multiplier
    external-forcing removal
    forcing-phase displacement
    Sakaguchi phase-lag modification

Возможное управление дисперсией естественных частот:

    omega_effective_i
    =
    omega_mean
    + frequency_dispersion_multiplier
      (
        omega_i - omega_mean
      )

Исходный массив естественных частот остаётся неизменным.

Протокол применяет временное эффективное преобразование, а не генерирует естественные частоты заново на каждом такте.

## Внешний форсинг

Внешний форсинг независим от внутренней средней фазы.

Вклад форсинга сохраняется как:

    F_ext sin(Psi_ext - theta_i)

где:

- F_ext — плотность внешнего форсинга;
- Psi_ext — фаза внешнего форсинга.

Протокол может уменьшать F_ext после разблокировки, но не должен скрыто заменять Psi_ext текущей глобальной средней фазой Psi(t).

## Распад амплитудного режима

Протокол может применять дополнительный постразблокировочный вклад распада амплитудного режима.

Численно устойчивая экспоненциальная форма:

    A_i(t + dt)
    =
    A_floor
    + (
        A_i(t) - A_floor
      )
      exp(-lambda_A(t) dt)

где:

    lambda_A(t)
    =
    amplitude_decay_scale
    /
    maximum(
        tau_delay(t),
        tau_min
    )

и:

- A_floor — настроенная минимальная амплитуда;
- tau_min предотвращает численную расходимость;
- amplitude_decay_scale управляет дополнительным демпфированием на этапе срыва.

Этот вклад применяется отдельно от базового закона амплитудной релаксации GPU-среднеполевого движка.

Модуль не отождествляет распад амплитудного режима с физической дематериализацией массы.

## Отсутствие прямого присваивания M(t)

Протокол не должен использовать операции вида:

    M(t) = constant C_proxy(t)

или:

    M(t + dt) = decay_factor M(t)

Модуль не вычисляет M(t).

Любая последующая связь между распадом аттрактора, T_int, J_flux и M(t) относится к отдельному интеграционному слою EDK.

## Отсутствие прямого присваивания T_int

Протокол не определяет:

    T_int = identity matrix C_proxy(t)

Модуль регистрирует только фазовые и амплитудные диагностические параметры срыва.

T_int должен вычисляться отдельным модулем удерживаемого интерфейса или интеграционным модулем.

## Граница J_flux

Протокол не вычисляет полное пространственное поле сквозного потока обмена J_flux.

Скалярный диагностический параметр может называться:

    exchange_activity_proxy

Возможная ограниченная диагностическая форма может объединять:

    среднюю амплитуду
    R(t)
    фазово-амплитудный прокси-параметр
    устойчивость фазовых скоростей

Этот скаляр не должен переименовываться в J_flux.

Полное поле J_flux требует:

- пространственного направления;
- локальной топологии обмена;
- временной эволюции;
- дивергенции;
- ротора;
- сопряжения с удерживаемым интерфейсом;
- сопряжения с фоновыми модами Континуума.

## Состояния протокола

Машина состояний протокола может содержать:

    INITIALIZED

    FORMING_ATTRACTOR

    RETAINED_ATTRACTOR

    CRITICAL_APPROACH

    CRITICAL_EXPOSURE

    PHASE_NODE_UNLOCKED

    COLLAPSE_ACTIVE

    DEGRADED_PHASE_REGIME

    COLLAPSE_COMPLETED

    COLLAPSE_NOT_REACHED

Переходы состояний должны определяться явными критериями и регистрироваться на соответствующем такте.

## Критерии срыва

Этап срыва должен оцениваться по измеряемой динамике.

Возможные критерии фазового срыва:

    R(t) ≤ R_collapse_threshold

или:

    R(t) ≤ phase_order_fraction
           R_unlock

Возможные фазово-амплитудные критерии:

    phase_amplitude_order_proxy
    ≤ PA_collapse_threshold

Возможные критерии дисперсии:

    phase_velocity_dispersion
    ≥ V_disp_collapse_threshold

Возможный комбинированный критерий:

    критерий фазового срыва
    и
    фазово-амплитудный критерий срыва
    и
    минимальная длительность после разблокировки

Выбранный критерий должен быть явно указан в конфигурации.

## Период полураспада фазового порядка

Период полураспада фазового порядка измеряется относительно состояния разблокировки.

Определяется:

    R_half_target
    =
    0.5 R_unlock

Период полураспада фазового порядка:

    t_R_half
    =
    первый момент после разблокировки,
    когда
    R(t) ≤ R_half_target

Если это условие не достигнуто в течение настроенного интервала наблюдения, результат:

    not reached

Он не должен заменяться искусственным значением.

## Период полураспада амплитудного режима

Определяется расстояние средней амплитуды от настроенного нижнего уровня:

    D_A(t)
    =
    mean_amplitude(t) - A_floor

При разблокировке:

    D_A_unlock
    =
    mean_amplitude_unlock - A_floor

Целевое значение половинного распада:

    D_A_half
    =
    0.5 D_A_unlock

Период полураспада амплитудного режима является первым моментом после разблокировки, когда:

    D_A(t) ≤ D_A_half

Если целевое значение не достигнуто, результат сохраняется как:

    not reached

## Время распада аттрактора

Время распада аттрактора измеряется от:

    unlock_time

до первого такта, выполняющего настроенный критерий срыва.

Протокол сохраняет:

    collapse_tact
    collapse_time
    collapse_duration_after_unlock

Протокол также должен сохранять случаи, когда аттрактор остаётся удержанным в течение полного интервала наблюдения.

## Максимальный интервал наблюдения

Протокол использует:

    maximum_post_unlock_tacts

или:

    maximum_post_unlock_time

для предотвращения неограниченной симуляции.

Если ни один критерий срыва не достигнут на этом интервале, конечное состояние:

    COLLAPSE_NOT_REACHED

Это является допустимым результатом.

Протокол не должен принуждать систему перейти в состояние срыва только для завершения теста.

## Основная конфигурация

Конфигурация протокола должна включать:

    formation_maximum_tacts
    formation_confirmation_tacts
    retained_verification_tacts

    R_form_min
    phase_amplitude_form_min
    phase_velocity_dispersion_form_max
    amplitude_dispersion_form_max

    coherence_weight_R
    coherence_weight_phase_amplitude
    coherence_weight_phase_velocity
    coherence_weight_amplitude

    phase_velocity_reference
    amplitude_dispersion_reference

    retained_boundary_tolerance

    pressure_schedule
    pressure_hold
    pressure_collapse
    pressure_ramp_rate

    delay_base_tau_0
    pressure_velocity_coefficient_mu
    delay_regularization_epsilon
    minimum_delay_tau

    critical_exposure_threshold
    exposure_recovery_mode
    exposure_recovery_rate

    coupling_quench_mode
    coupling_floor
    coupling_quench_tau

    post_unlock_phase_noise_multiplier
    post_unlock_frequency_dispersion_multiplier
    post_unlock_amplitude_decay_scale

    phase_order_collapse_threshold
    phase_order_collapse_fraction
    phase_amplitude_collapse_threshold
    phase_velocity_dispersion_collapse_threshold

    maximum_post_unlock_tacts

    log_every
    field_every

## Конфигурация базового движка

Базовый среднеполевой движок сохраняет собственную конфигурацию:

    num_domains
    coupling_strength_k
    sakaguchi_phase_lag_alpha
    natural_frequency_mean
    natural_frequency_std
    external_forcing_phase
    phase_noise_strength
    amplitude_growth_rate
    amplitude_saturation_rate
    amplitude_noise_strength
    amplitude_minimum
    amplitude_maximum
    seed
    dtype
    backend
    device_id

Протокол не должен скрыто перезаписывать неизменяемую конфигурацию движка.

Динамические параметры протокола, например K_eff, хранятся отдельно.

## Основные скалярные диагностические параметры

Протокол регистрирует:

    tact_index
    simulation_time
    protocol_state

    R_t_phase_order
    global_mean_phase
    phase_amplitude_order_proxy

    mean_phase_velocity
    phase_velocity_dispersion

    mean_amplitude
    amplitude_dispersion
    minimum_amplitude
    maximum_amplitude

    coupling_energy_proxy

    C_proxy_t
    external_pressure_P_ext
    retention_margin
    pressure_excess

    instantaneous_delay_tau
    critical_exposure

    initial_coupling_K
    effective_coupling_K
    coupling_floor_K

    effective_phase_noise_strength
    effective_frequency_dispersion_multiplier
    effective_amplitude_decay_rate

    attractor_formed
    attractor_verified
    phase_node_unlocked
    collapse_detected

    formation_tact
    unlock_tact
    collapse_tact

    phase_order_half_life
    amplitude_regime_half_life
    attractor_collapse_duration

## Полные снимки полей

Дополнительные снимки полей могут включать:

    phases
    amplitudes
    natural_frequencies
    effective_natural_frequencies
    phase_velocity
    amplitude_velocity
    phase_noise_increment
    amplitude_noise_increment

Полные снимки полей не должны по умолчанию экспортироваться на каждом такте.

## Стратегия журналирования

Рекомендуемое журналирование:

    JSON
    → состояние протокола, скалярные метрики, конфигурация, события переходов

    NPZ
    → массивы фаз, амплитуд, частот и скоростей

Компактные метрики записываются согласно:

    log_every

Полные снимки полей записываются согласно:

    field_every

События переходов должны записываться немедленно при входе протокола в состояния:

    RETAINED_ATTRACTOR
    CRITICAL_EXPOSURE
    PHASE_NODE_UNLOCKED
    COLLAPSE_ACTIVE
    COLLAPSE_COMPLETED
    COLLAPSE_NOT_REACHED

## Атомарная запись

Выходные файлы JSON и NPZ должны записываться атомарно:

    временный файл
    ↓
    flush
    ↓
    fsync
    ↓
    os.replace
    ↓
    конечный файл

Это снижает риск появления неполных снимков протокола после прерывания.

## Диагностический модуль

Файл:

    marnov_retention_diagnostics.py

должен формировать диагностические визуализации по рассчитанным данным протокола.

Рекомендуемые графики:

1. R(t), фазово-амплитудный прокси-параметр и C_proxy(t);
2. нормированное внешнее давление и запас удержания;
3. критическое воздействие и мгновенный tau_delay;
4. исходное и эффективное сопряжение K;
5. дисперсии фазовых скоростей и амплитуд;
6. средняя амплитуда и целевое значение половинного распада;
7. переходы состояний протокола;
8. маркеры полураспада фазового порядка и времени срыва.

Диагностика должна показывать фактически рассчитанную траекторию.

Она не должна восстанавливать заранее заданную кривую срыва.

## Масштабирование GPU

Протокол наследует глобальное среднеполевое масштабирование O(N) от:

    EDKGPUMeanFieldPhaseEngine

Протокол не должен строить:

    матрицы разностей фаз N × N

Для:

    N = 131072

одна плотная попарная матрица содержала бы:

    17179869184 элементов

Приблизительный объём памяти одной матрицы:

    float32 → 64 GiB
    float64 → 128 GiB

Эти значения не учитывают дополнительные массивы синусов, временные массивы, редукции или накладные расходы пула памяти.

Среднеполевой движок исключает это выделение памяти.

## Выбор бэкенда

Режимы бэкенда наследуются от GPU-среднеполевого движка:

    auto
    gpu
    cpu

Протокол не реализует второй независимый механизм обнаружения CuPy.

Совместимое устройство CUDA проверяется базовым движком.

Протокол может запускаться на CPU для небольших проверочных случаев.

Крупномасштабные запуски должны выполняться только после измерения памяти и производительности.

## Воспроизводимость

Протокол сохраняет:

- seed движка;
- конфигурацию движка;
- конфигурацию протокола;
- название бэкенда;
- идентификатор устройства;
- dtype;
- профиль давления;
- профиль форсинга;
- такты переходов состояний;
- конечные диагностические значения.

Фиксированные естественные частоты должны оставаться неизменными на протяжении всего протокола.

Любое эффективное постразблокировочное преобразование частот должно выводиться из фиксированного базового массива.

## Состояния отказа

Протокол должен явно сообщать состояния отказа.

Примеры:

    ATTRACTOR_NOT_FORMED

    ATTRACTOR_NOT_VERIFIED

    INVALID_PRESSURE_SCALE

    CRITICAL_BOUNDARY_NOT_REACHED

    UNLOCK_NOT_TRIGGERED

    COLLAPSE_NOT_REACHED

    NUMERICAL_INSTABILITY

    NON_FINITE_STATE

Неудачный или незавершённый эксперимент срыва не должен сообщаться как успешно завершённый срыв.

## Базовый запуск

Проверочный запуск на CPU:

    python marnov_retention_collapse_protocol.py --backend cpu

Автоматический выбор бэкенда:

    python marnov_retention_collapse_protocol.py --backend auto

Явный запуск на GPU:

    python marnov_retention_collapse_protocol.py --backend gpu --device-id 0

Крупномасштабный запуск на GPU:

    python marnov_retention_collapse_protocol.py --backend gpu --num-domains 131072

Диагностика:

    python marnov_retention_diagnostics.py --snapshot-dir edk_marnov_snapshots

Дымовой тест:

    python smoke_test.py

## Требования дымового теста

Дымовой тест должен проверять:

- успешную инициализацию CPU;
- корректный импорт GPU-среднеполевого движка;
- отсутствие дублированной инициализации бэкенда;
- воспроизводимую инициализацию при фиксированном seed;
- неизменность естественных частот;
- корректное исполнение этапа формирования;
- проверку удерживаемого аттрактора;
- ограниченность C_proxy(t);
- ограниченность нормированного внешнего давления;
- корректный расчёт запаса удержания;
- корректную классификацию EDS, EDC и деградационного режима;
- конечность tau_delay;
- корректное накопление критического воздействия;
- отсутствие немедленной разблокировки до достижения порога воздействия;
- корректное событие разблокировки после достижения порога;
- монотонное снижение сопряжения после разблокировки при выборе экспоненциального снятия;
- корректное сворачивание фаз;
- конечность массивов фаз и амплитуд;
- неотрицательность дисперсий;
- расчёт периода полураспада фазового порядка;
- расчёт периода полураспада амплитудного режима;
- корректный результат COLLAPSE_NOT_REACHED при недостижении порогов;
- экспорт компактного JSON;
- экспорт полей NPZ;
- атомарную замену файлов;
- успешное формирование диагностики по тестовым снимкам.

## Исследовательский статус

Этот модуль является численным исследовательским компонентом вычислительной архитектуры EDK.

Он предоставляет управляемый протокол для исследования:

    формирования
    удержания
    критического нагружения
    задержанной разблокировки
    снятия сопряжения
    распада фазового аттрактора
    распада амплитудного режима

Сам модуль не устанавливает универсальный физический закон срыва.

Ретардационное соотношение обратного кубического корня реализуется как настраиваемое модельное предположение, последствия которого могут численно сравниваться с альтернативными законами задержки.

## Лицензия

Модуль наследует лицензию родительского репозитория EDK.
