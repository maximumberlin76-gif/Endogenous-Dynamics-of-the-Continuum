# Marnov Retention-Collapse Protocol for EDK

## EN

Numerical protocol for formation, critical loading, delayed unlocking, controlled coupling release, and measurable decay of a retained macroscopic phase attractor in a high-density open dynamic system.

The module operates above the EDK GPU mean-field phase dynamics engine and uses it as the phase-evolution backend.

The protocol manages the staged experiment:

`attractor formation ↓ retained-state verification ↓ normalized external-pressure loading ↓ approach to the critical boundary ↓ accumulation of critical exposure ↓ delayed unlocking of the phase-coupling node ↓ controlled coupling release ↓ decay of the phase attractor ↓ decay of the amplitude regime ↓ measurement of retention-collapse characteristics`

The module is intended for high-density systems of phase domains, including simulations with `131072` or more globally coupled domains when sufficient host or GPU memory is available.

## Repository Location

`module_edk_marnov_retention_collapse_protocol/`

## Module Structure

`module_edk_marnov_retention_collapse_protocol/`

`├── README_EN_RU.md`

`├── marnov_retention_collapse_protocol.py`

`├── marnov_retention_diagnostics.py`

`├── smoke_test.py`

`└── __init__.py`

## Main Class

`EDKMarnovRetentionCollapseProtocol`

## Configuration Class

`MarnovRetentionCollapseConfig`

## Dependency

The protocol depends on:

`module_edk_gpu_mean_field_phase_engine`

Required imported classes:

`EDKGPUMeanFieldPhaseEngine`

`MeanFieldPhaseConfig`

The following mechanisms are provided by the EDK GPU mean-field phase dynamics engine:

- NumPy or CuPy backend selection;
- CUDA device initialization;
- phase-domain initialization;
- amplitude-domain initialization;
- fixed natural-frequency initialization;
- global Kuramoto-Sakaguchi mean-field coupling;
- backend-specific random-number generation;
- field transfer between GPU and host memory.

## Computational Purpose

The module provides a controlled numerical environment for investigating the loss of a previously formed phase attractor after the system enters a critical retention regime.

The protocol distinguishes:

`formation of a retained attractor`

and:

`collapse of a retained attractor`

A collapse experiment becomes valid only after the initial state satisfies the configured retained-state criteria over a consecutive verification interval.

The protocol first forms and verifies the attractor using measured phase and amplitude diagnostic parameters.

## Protocol Scope

The protocol models:

- formation of a globally coupled phase attractor;
- retention of the phase attractor over time;
- loading by normalized external pressure;
- calculation of the diagnostic proxy parameter of endogenous coherence;
- calculation of retention margin;
- classification of retained, critical, and degradation regimes;
- accumulation of critical exposure;
- delayed activation of the coupling-release process;
- tact-by-tact reduction of effective coupling;
- additional growth of phase and frequency mismatch;
- decay of the phase-order parameter;
- decay of the amplitude regime;
- phase-order half-life;
- amplitude-regime half-life;
- attractor unlock time;
- attractor collapse time;
- final-state classification.

## Integration Context

The protocol exports measured phase and amplitude diagnostics for the following integration layers of EDK.

Primary protocol-level diagnostic outputs:

- `R_t_phase_order`;
- `phase_amplitude_order_proxy`;
- `C_proxy_t`;
- `external_pressure_P_ext`;
- `retention_margin`;
- `pressure_excess`;
- `instantaneous_delay_tau`;
- `critical_exposure`;
- `effective_coupling_K`;
- `exchange_activity_proxy`;
- `phase_order_half_life`;
- `amplitude_regime_half_life`;
- `attractor_collapse_duration`.

Downstream EDK integration layers may consume these outputs for interface-tensor, exchange-flow, molecular, biological, or mass-formation modelling.

The protocol therefore preserves the distinction between phase-attractor collapse diagnostics and downstream EDK quantities such as `T_int`, `J_flux`, and `M(t)`.

## Marnov Retention-Collapse Protocol

Within this module, the Marnov Retention-Collapse Protocol is defined as a controlled numerical procedure in which:

1. a phase attractor is formed;
2. the retained state is verified;
3. normalized external pressure approaches or exceeds diagnostic retention capacity;
4. critical exposure accumulates over a finite delay interval;
5. the macroscopic phase-coupling node is unlocked;
6. effective coupling decreases tact by tact;
7. phase and amplitude mismatch are measured;
8. the decay of the retained attractor is quantitatively evaluated.

The result arises from the configured tact-by-tact dynamics of the protocol.

## Phase-Order Parameter

The base GPU mean-field engine computes:

`Z(t) = 1 / N sum_j exp(i theta_j)`

with:

`Z(t) = R(t) exp(i Psi(t))`

where:

- `R(t)` is the global phase-order parameter;
- `Psi(t)` is the global mean phase;
- `theta_j` is the phase of domain `j`;
- `N` is the number of phase domains.

The protocol uses:

`R_t_phase_order`

as an indicator of global phase synchronization.

## Mandatory Semantic Distinctions

The module preserves the following distinctions:

`phase synchronization ≠ phase coherence`

`R(t) ≠ C(t)`

`C_proxy(t) ≠ C(t)`

`phase-amplitude proxy parameter ≠ general endogenous structural coherence`

`exchange_activity_proxy ≠ J_flux`

`controlled coupling release ≠ automatically detected physical bifurcation`

`amplitude-regime decay ≠ decay of manifested mass`

`retained phase attractor ≠ full material form`

These terms are fixed semantic invariants of the module.

## Diagnostic Proxy Parameter of Endogenous Coherence

The protocol uses:

`C_proxy(t)`

`C_proxy(t)` is a bounded diagnostic proxy parameter used for protocol control and dynamic-regime classification.

Possible operational form:

`C_proxy(t) = w_R R(t) + w_PA PA(t) + w_V V_stability(t) + w_A A_stability(t)`

where:

- `R(t)` is the global phase-order parameter;
- `PA(t)` is the phase-amplitude proxy parameter;
- `V_stability(t)` is the normalized contribution of phase-velocity stability;
- `A_stability(t)` is the normalized contribution of amplitude stability;
- `w_R`, `w_PA`, `w_V`, and `w_A` are non-negative weighting coefficients;
- the sum of all weighting coefficients is equal to `1`.

The phase-velocity stability contribution may be represented as:

`V_stability(t) = 1 / (1 + sigma_v(t) / v_ref)`

where:

- `sigma_v(t)` is the dispersion of phase velocities;
- `v_ref` is a positive reference scale.

The amplitude-stability contribution may be represented as:

`A_stability(t) = 1 / (1 + sigma_A(t) / A_ref)`

where:

- `sigma_A(t)` is the dispersion of amplitudes;
- `A_ref` is a positive reference scale.

`C_proxy(t)` remains a numerical diagnostic parameter of the protocol layer.

## Normalized External Pressure

The protocol uses the normalized external-pressure parameter:

`P_ext(t)`

`P_ext(t)` is expressed in the same bounded diagnostic scale as `C_proxy(t)`.

Recommended range:

`0 ≤ P_ext(t) ≤ 1`

Values outside the configured range are rejected or explicitly normalized before use.

## Retention Margin

Retention margin:

`retention_margin(t) = C_proxy(t) - P_ext(t)`

The protocol classifies three dynamic regimes using the configurable tolerance `epsilon_EDC`.

### Retained Regime

`retention_margin(t) > epsilon_EDC`

Interpretation:

`C_proxy(t) > P_ext(t)`

The diagnostic capacity of the retained phase regime exceeds normalized external pressure.

### EDC Critical Regime

`absolute(retention_margin(t)) ≤ epsilon_EDC`

Interpretation:

`C_proxy(t) is approximately equal to P_ext(t)`

The system is near the diagnostic retention boundary.

### Degradation Regime

`retention_margin(t) < -epsilon_EDC`

Interpretation:

`C_proxy(t) < P_ext(t)`

Normalized external pressure exceeds diagnostic retention capacity.

After entering the degradation regime, the protocol calculates and accumulates critical exposure before unlock activation.

## Attractor-Formation Stage

The protocol begins with the formation stage under configured baseline parameters:

`initial coupling constant K_initial`

`baseline external forcing F_hold`

`baseline forcing phase Psi_hold`

`baseline normalized pressure P_hold`

`configured phase lag alpha`

`fixed natural frequencies`

`configured phase and amplitude noise`

At each tact, the protocol records:

`R(t)`

`Psi(t)`

`phase-amplitude proxy parameter`

`mean phase velocity`

`phase-velocity dispersion`

`mean amplitude`

`amplitude dispersion`

`coupling-energy proxy`

`C_proxy(t)`

`P_ext(t)`

`retention margin`

The attractor is declared formed only after all configured formation criteria hold over a consecutive confirmation interval.

## Attractor-Formation Criteria

Possible formation criteria:

`R(t) ≥ R_form_min`

`phase_amplitude_order_proxy ≥ PA_form_min`

`phase_velocity_dispersion ≤ V_disp_form_max`

`amplitude_dispersion ≤ A_disp_form_max`

`retention_margin > epsilon_EDC`

The criteria must be preserved for:

`formation_confirmation_tacts`

consecutive tacts.

After confirmation, the protocol may enter:

`RETAINED_ATTRACTOR`

## Retained-State Verification

After formation, the protocol may maintain an additional verification interval:

`retained_verification_tacts`

This interval confirms that the attractor is a retained dynamic state rather than a transient synchronization spike.

During verification, the protocol measures preservation of:

- global phase order;
- phase-amplitude coordination;
- low phase-velocity dispersion;
- bounded amplitude dispersion;
- positive retention margin;
- stable coupling-energy proxy.

Baseline values of the retained state are stored for comparison with the collapse stage.

## Critical-Loading Stage

After the retained attractor is verified, the protocol changes external loading according to the configured pressure profile.

Supported pressure profiles may include:

`step`

`linear_ramp`

`smooth_ramp`

`externally supplied sequence`

The pressure profile is explicit and reproducible.

Examples:

`P_ext(t) = P_hold before loading starts`

`P_ext(t) = P_collapse after the step transition`

or:

`P_ext(t + dt) = minimum(P_collapse, P_ext(t) + pressure_ramp_rate dt)`

The protocol records the first tact on which:

`retention_margin(t) ≤ epsilon_EDC`

and the first tact on which:

`retention_margin(t) < -epsilon_EDC`

## Pressure Excess

Pressure excess:

`pressure_excess(t) = maximum(P_ext(t) - C_proxy(t), 0)`

When:

`pressure_excess(t) = 0`

the critical-exposure accumulator remains unchanged.

When:

`pressure_excess(t) > 0`

the system accumulates critical exposure according to the retardation law.

## Retardation Law

The protocol represents the configured inverse-cube-root delay relation through:

`v(t) = mu pressure_excess(t)`

and:

`tau_delay(t) = tau_0 / (v(t) + epsilon_v)^(1/3)`

where:

- `mu` is the coefficient converting pressure excess into collapse velocity;
- `tau_0` is the base delay scale;
- `epsilon_v` is a small positive numerical regularizer;
- `tau_delay(t)` is the instantaneous diagnostic delay scale.

Equivalent form:

`tau_delay(t) is proportional to v(t)^(-1/3)`

This relation is a configurable modelling assumption of the numerical protocol.

## Critical-Exposure Accumulator

Critical exposure accumulates as:

`critical_exposure(t + dt) = critical_exposure(t) + dt / tau_delay(t)`

when:

`pressure_excess(t) > 0`

The phase-coupling node unlocks under the condition:

`critical_exposure ≥ critical_exposure_threshold`

Before this condition is reached, the system remains in:

`CRITICAL_EXPOSURE`

This mechanism makes `tau_delay` an operational parameter controlling the activation moment.

## Recovery Before Unlocking

If retention margin becomes positive again before:

`critical_exposure ≥ critical_exposure_threshold`

the protocol may use one of two configurable modes:

`persistent exposure`

`decaying exposure`

In `persistent exposure` mode, accumulated exposure is retained.

In `decaying exposure` mode:

`critical_exposure(t + dt) = maximum(0, critical_exposure(t) - exposure_recovery_rate dt)`

The selected mode is recorded in the configuration and protocol logs.

## Phase-Node Unlocking

When:

`critical_exposure ≥ critical_exposure_threshold`

the protocol records:

`unlock_tact`

`unlock_time`

`R_unlock`

`phase_amplitude_order_unlock`

`amplitude_mean_unlock`

`amplitude_dispersion_unlock`

`C_proxy_unlock`

`P_ext_unlock`

`retention_margin_unlock`

`tau_delay_unlock`

After that, the protocol enters:

`PHASE_NODE_UNLOCKED`

A configurable coupling-release law controls the subsequent evolution of effective coupling.

## Effective Coupling Release

Effective coupling after unlocking may evolve as:

`K_eff(t + dt) = K_floor + (K_eff(t) - K_floor) exp(-dt / tau_K)`

where:

- `K_floor` is the minimum retained coupling level;
- `tau_K` is the coupling-release time scale.

An explicit instantaneous release mode may also be supported:

`K_eff = K_floor`

and is recorded in configuration as:

`instantaneous coupling quench`

## Growth of Phase Mismatch

After unlocking, the protocol may increase phase mismatch through configurable channels.

Possible channels:

`phase_noise_strength`

`natural-frequency-dispersion multiplier`

`external-forcing removal`

`forcing-phase displacement`

`Sakaguchi phase-lag modification`

Possible control of natural-frequency dispersion:

`omega_effective_i = omega_mean + frequency_dispersion_multiplier (omega_i - omega_mean)`

The original natural-frequency array remains fixed.

The protocol applies a temporary effective transformation derived from the fixed base array.

## External Forcing

External forcing is independent of the internal mean phase.

The forcing contribution is preserved as:

`F_ext sin(Psi_ext - theta_i)`

where:

- `F_ext` is the external-forcing density;
- `Psi_ext` is the external-forcing phase.

The protocol may reduce `F_ext` after unlocking while preserving the configured external-forcing phase relation.

## Amplitude-Regime Decay

The protocol may apply an additional post-unlock contribution to amplitude-regime decay.

Numerically stable exponential form:

`A_i(t + dt) = A_floor + (A_i(t) - A_floor) exp(-lambda_A(t) dt)`

where:

`lambda_A(t) = amplitude_decay_scale / maximum(tau_delay(t), tau_min)`

and:

- `A_floor` is the configured minimum amplitude;
- `tau_min` prevents numerical divergence;
- `amplitude_decay_scale` controls additional damping during the collapse stage.

This contribution is applied separately from the base amplitude-relaxation law of the GPU mean-field engine.

## Downstream EDK Quantities

The protocol records phase and amplitude diagnostics of retention collapse.

Downstream EDK integration layers may calculate or reconstruct:

- manifested mass `M(t)`;
- retained-interface tensor `T_int`;
- full spatial exchange-flow field `J_flux`;
- molecular reconstruction;
- biological reconstruction;
- plasma magnetohydrodynamic regimes;
- materialization or dematerialization interpretations.

The protocol-level scalar exchange diagnostic is named:

`exchange_activity_proxy`

A possible bounded diagnostic form may combine:

`mean amplitude`

`R(t)`

`phase-amplitude proxy parameter`

`phase-velocity stability`

The full `J_flux` integration field requires:

- spatial direction;
- local exchange topology;
- temporal evolution;
- divergence;
- curl;
- coupling with the retained interface;
- coupling with background modes of the Continuum.

## Protocol States

The protocol state machine may contain:

`INITIALIZED`

`FORMING_ATTRACTOR`

`RETAINED_ATTRACTOR`

`CRITICAL_APPROACH`

`CRITICAL_EXPOSURE`

`PHASE_NODE_UNLOCKED`

`COLLAPSE_ACTIVE`

`DEGRADED_PHASE_REGIME`

`COLLAPSE_COMPLETED`

`COLLAPSE_NOT_REACHED`

State transitions are determined by explicit criteria and recorded at the corresponding tact.

## Collapse Criteria

The collapse stage is evaluated using measured dynamics.

Possible phase-collapse criteria:

`R(t) ≤ R_collapse_threshold`

or:

`R(t) ≤ phase_order_fraction R_unlock`

Possible phase-amplitude criteria:

`phase_amplitude_order_proxy ≤ PA_collapse_threshold`

Possible dispersion criteria:

`phase_velocity_dispersion ≥ V_disp_collapse_threshold`

Possible combined criterion:

`phase-collapse criterion and phase-amplitude collapse criterion and minimum duration after unlocking`

The selected criterion is explicitly specified in the configuration.

## Phase-Order Half-Life

Phase-order half-life is measured relative to the unlock state.

Definition:

`R_half_target = 0.5 R_unlock`

Phase-order half-life:

`t_R_half = first moment after unlocking when R(t) ≤ R_half_target`

If the condition remains unreached during the configured observation interval, the result is preserved as:

`not reached`

## Amplitude-Regime Half-Life

The distance of the mean amplitude from the configured lower level is defined as:

`D_A(t) = mean_amplitude(t) - A_floor`

At unlocking:

`D_A_unlock = mean_amplitude_unlock - A_floor`

Half-decay target:

`D_A_half = 0.5 D_A_unlock`

Amplitude-regime half-life is the first moment after unlocking when:

`D_A(t) ≤ D_A_half`

If the target remains unreached, the result is preserved as:

`not reached`

## Attractor Collapse Time

Attractor collapse time is measured from:

`unlock_time`

to the first tact satisfying the configured collapse criterion.

The protocol preserves:

`collapse_tact`

`collapse_time`

`collapse_duration_after_unlock`

The protocol also preserves cases where the attractor remains retained over the full observation interval.

## Maximum Observation Interval

The protocol uses:

`maximum_post_unlock_tacts`

or:

`maximum_post_unlock_time`

to bound the simulation.

If no collapse criterion is reached during this interval, the terminal state is:

`COLLAPSE_NOT_REACHED`

This is a valid terminal result of the experiment.

## Main Configuration

Protocol configuration includes:

`formation_maximum_tacts`

`formation_confirmation_tacts`

`retained_verification_tacts`

`R_form_min`

`phase_amplitude_form_min`

`phase_velocity_dispersion_form_max`

`amplitude_dispersion_form_max`

`coherence_weight_R`

`coherence_weight_phase_amplitude`

`coherence_weight_phase_velocity`

`coherence_weight_amplitude`

`phase_velocity_reference`

`amplitude_dispersion_reference`

`retained_boundary_tolerance`

`pressure_schedule`

`pressure_hold`

`pressure_collapse`

`pressure_ramp_rate`

`delay_base_tau_0`

`pressure_velocity_coefficient_mu`

`delay_regularization_epsilon`

`minimum_delay_tau`

`critical_exposure_threshold`

`exposure_recovery_mode`

`exposure_recovery_rate`

`coupling_quench_mode`

`coupling_floor`

`coupling_quench_tau`

`post_unlock_phase_noise_multiplier`

`post_unlock_frequency_dispersion_multiplier`

`post_unlock_amplitude_decay_scale`

`phase_order_collapse_threshold`

`phase_order_collapse_fraction`

`phase_amplitude_collapse_threshold`

`phase_velocity_dispersion_collapse_threshold`

`maximum_post_unlock_tacts`

`log_every`

`field_every`

## Base Engine Configuration

The base mean-field engine preserves its own configuration:

`num_domains`

`coupling_strength_k`

`sakaguchi_phase_lag_alpha`

`natural_frequency_mean`

`natural_frequency_std`

`external_forcing_phase`

`phase_noise_strength`

`amplitude_growth_rate`

`amplitude_saturation_rate`

`amplitude_noise_strength`

`amplitude_minimum`

`amplitude_maximum`

`seed`

`dtype`

`backend`

`device_id`

Dynamic protocol parameters, for example `K_eff`, are stored separately.

## Main Scalar Diagnostic Parameters

The protocol records:

`tact_index`

`simulation_time`

`protocol_state`

`R_t_phase_order`

`global_mean_phase`

`phase_amplitude_order_proxy`

`mean_phase_velocity`

`phase_velocity_dispersion`

`mean_amplitude`

`amplitude_dispersion`

`minimum_amplitude`

`maximum_amplitude`

`coupling_energy_proxy`

`C_proxy_t`

`external_pressure_P_ext`

`retention_margin`

`pressure_excess`

`instantaneous_delay_tau`

`critical_exposure`

`initial_coupling_K`

`effective_coupling_K`

`coupling_floor_K`

`effective_phase_noise_strength`

`effective_frequency_dispersion_multiplier`

`effective_amplitude_decay_rate`

`attractor_formed`

`attractor_verified`

`phase_node_unlocked`

`collapse_detected`

`formation_tact`

`unlock_tact`

`collapse_tact`

`phase_order_half_life`

`amplitude_regime_half_life`

`attractor_collapse_duration`

## Full Field Snapshots

Additional field snapshots may include:

`phases`

`amplitudes`

`natural_frequencies`

`effective_natural_frequencies`

`phase_velocity`

`amplitude_velocity`

`phase_noise_increment`

`amplitude_noise_increment`

Full field snapshots are exported according to configured snapshot cadence.

## Logging Strategy

Recommended logging:

`JSON → protocol state, scalar metrics, configuration, transition events`

`NPZ → arrays of phases, amplitudes, frequencies, and velocities`

Compact metrics are written according to:

`log_every`

Full field snapshots are written according to:

`field_every`

Transition events are written immediately when the protocol enters:

`RETAINED_ATTRACTOR`

`CRITICAL_EXPOSURE`

`PHASE_NODE_UNLOCKED`

`COLLAPSE_ACTIVE`

`COLLAPSE_COMPLETED`

`COLLAPSE_NOT_REACHED`

## Atomic Writing

JSON and NPZ output files are written atomically:

`temporary file ↓ flush ↓ fsync ↓ os.replace ↓ final file`

This reduces the risk of incomplete protocol snapshots after interruption.

## Diagnostic Module

File:

`marnov_retention_diagnostics.py`

The diagnostic module forms visualizations from calculated protocol data.

Recommended plots:

1. `R(t)`, phase-amplitude proxy parameter, and `C_proxy(t)`;
2. normalized external pressure and retention margin;
3. critical exposure and instantaneous `tau_delay`;
4. initial and effective coupling `K`;
5. phase-velocity and amplitude dispersions;
6. mean amplitude and half-decay target;
7. protocol-state transitions;
8. phase-order half-life and collapse-time markers.

Diagnostics display the calculated trajectory of the protocol.

## GPU Scaling

The protocol inherits global mean-field `O(N)` scaling from:

`EDKGPUMeanFieldPhaseEngine`

For:

`N = 131072`

one dense pairwise matrix would contain:

`17179869184 elements`

Approximate memory volume of one matrix:

`float32 → 64 GiB`

`float64 → 128 GiB`

These values exclude additional sine arrays, temporary arrays, reductions, and memory-pool overhead.

The mean-field engine preserves scalable execution by using global order parameters.

## Backend Selection

Backend modes are inherited from the GPU mean-field engine:

`auto`

`gpu`

`cpu`

A compatible CUDA device is checked by the base engine.

The protocol may run on CPU for small verification cases.

Large-scale runs should be performed after memory and performance measurement.

## Reproducibility

The protocol preserves:

- engine seed;
- engine configuration;
- protocol configuration;
- backend name;
- device identifier;
- dtype;
- pressure profile;
- forcing profile;
- protocol-state transition tacts;
- final diagnostic values.

Fixed natural frequencies remain unchanged throughout the protocol.

Any effective post-unlock frequency transformation is derived from the fixed base array.

## Failure States

The protocol reports explicit failure states.

Examples:

`ATTRACTOR_NOT_FORMED`

`ATTRACTOR_NOT_VERIFIED`

`INVALID_PRESSURE_SCALE`

`CRITICAL_BOUNDARY_NOT_REACHED`

`UNLOCK_NOT_TRIGGERED`

`COLLAPSE_NOT_REACHED`

`NUMERICAL_INSTABILITY`

`NON_FINITE_STATE`

An incomplete collapse experiment is preserved as an explicit diagnostic outcome.

## Basic Run

CPU verification run:

`python marnov_retention_collapse_protocol.py --backend cpu`

Automatic backend selection:

`python marnov_retention_collapse_protocol.py --backend auto`

Explicit GPU run:

`python marnov_retention_collapse_protocol.py --backend gpu --device-id 0`

Large-scale GPU run:

`python marnov_retention_collapse_protocol.py --backend gpu --num-domains 131072`

Diagnostics:

`python marnov_retention_diagnostics.py --snapshot-dir edk_marnov_snapshots`

Smoke test:

`python smoke_test.py`

## Smoke-Test Requirements

The smoke test verifies:

- successful CPU initialization;
- correct import of the GPU mean-field engine;
- backend selection through the base engine;
- reproducible initialization with fixed seed;
- invariance of natural frequencies;
- correct execution of the formation stage;
- verification of the retained attractor;
- bounded `C_proxy(t)`;
- bounded normalized external pressure;
- correct retention-margin calculation;
- correct classification of EDS, EDC, and degradation regimes;
- finite `tau_delay`;
- correct accumulation of critical exposure;
- delayed unlocking before threshold completion;
- correct unlock event after threshold completion;
- monotonic coupling decrease after unlock under exponential release;
- correct phase wrapping;
- finite phase and amplitude arrays;
- non-negative dispersions;
- phase-order half-life calculation;
- amplitude-regime half-life calculation;
- correct `COLLAPSE_NOT_REACHED` result when thresholds remain unreached;
- compact JSON export;
- NPZ field export;
- atomic file replacement;
- successful diagnostics from test snapshots.

## Research Status

This module is a numerical research component of the EDK computational architecture.

It provides a controlled protocol for investigating:

`retention formation`

`critical loading`

`delayed unlocking`

`coupling release`

`phase-attractor decay`

`amplitude-regime decay`

The inverse-cube-root retardation relation is implemented as a configurable modelling assumption whose consequences can be numerically compared with alternative delay laws.

## License

The module inherits the license of the parent EDK repository.

---

# Протокол Марнова для срыва удержания в EDK

## RU

Численный протокол формирования, критического нагружения, задержанной разблокировки, управляемого снятия сопряжения и измеряемого распада удерживаемого макроскопического фазового аттрактора в высокоплотной открытой динамической системе.

Модуль работает над EDK GPU-движком среднеполевой фазовой динамики и использует его как бэкенд фазовой эволюции.

Протокол управляет поэтапным экспериментом:

`формирование аттрактора ↓ проверка удерживаемого состояния ↓ нагружение нормированным внешним давлением ↓ приближение к критической границе ↓ накопление критического воздействия ↓ задержанная разблокировка узла фазового сопряжения ↓ управляемое снятие сопряжения ↓ распад фазового аттрактора ↓ распад амплитудного режима ↓ измерение характеристик срыва удержания`

Модуль предназначен для высокоплотных систем фазовых доменов, включая симуляции с `131072` и более глобально сопряжёнными доменами при наличии достаточного объёма памяти хоста или GPU.

## Расположение в репозитории

`module_edk_marnov_retention_collapse_protocol/`

## Структура модуля

`module_edk_marnov_retention_collapse_protocol/`

`├── README_EN_RU.md`

`├── marnov_retention_collapse_protocol.py`

`├── marnov_retention_diagnostics.py`

`├── smoke_test.py`

`└── __init__.py`

## Основной класс

`EDKMarnovRetentionCollapseProtocol`

## Класс конфигурации

`MarnovRetentionCollapseConfig`

## Зависимость

Протокол зависит от:

`module_edk_gpu_mean_field_phase_engine`

Необходимые импортируемые классы:

`EDKGPUMeanFieldPhaseEngine`

`MeanFieldPhaseConfig`

Следующие механизмы предоставляются EDK GPU-движком среднеполевой фазовой динамики:

- выбор бэкенда NumPy или CuPy;
- инициализация устройства CUDA;
- инициализация фазовых доменов;
- инициализация амплитудных доменов;
- инициализация фиксированных естественных частот;
- глобальное среднеполевое сопряжение Курамото — Сакагучи;
- специализированная генерация случайных чисел для активного бэкенда;
- передача полей между GPU и памятью хоста.

## Вычислительное назначение

Модуль предоставляет управляемую численную среду для исследования потери ранее сформированного фазового аттрактора после входа системы в критический режим удержания.

Протокол различает:

`формирование удерживаемого аттрактора`

и:

`срыв удерживаемого аттрактора`

Эксперимент срыва становится действительным только после того, как исходное состояние выполняет настроенные критерии удерживаемого состояния на последовательном интервале проверки.

Сначала протокол формирует и проверяет аттрактор по измеряемым фазовым и амплитудным диагностическим параметрам.

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

## Интеграционный контекст

Протокол экспортирует измеренные фазовые и амплитудные диагностические параметры для последующих интеграционных слоёв EDK.

Основные диагностические выходы уровня протокола:

- `R_t_phase_order`;
- `phase_amplitude_order_proxy`;
- `C_proxy_t`;
- `external_pressure_P_ext`;
- `retention_margin`;
- `pressure_excess`;
- `instantaneous_delay_tau`;
- `critical_exposure`;
- `effective_coupling_K`;
- `exchange_activity_proxy`;
- `phase_order_half_life`;
- `amplitude_regime_half_life`;
- `attractor_collapse_duration`.

Последующие интеграционные слои EDK могут использовать эти выходы для моделирования интерфейсно-тензорного, обменного, молекулярного, биологического или массоформирующего уровня.

Поэтому протокол сохраняет различие между диагностикой срыва фазового аттрактора и последующими величинами EDK, такими как `T_int`, `J_flux` и `M(t)`.

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

Результат возникает из настроенной потактовой динамики протокола.

## Параметр фазового порядка

Базовый GPU-среднеполевой движок вычисляет:

`Z(t) = 1 / N sum_j exp(i theta_j)`

при этом:

`Z(t) = R(t) exp(i Psi(t))`

где:

- `R(t)` — глобальный параметр фазового порядка;
- `Psi(t)` — глобальная средняя фаза;
- `theta_j` — фаза домена `j`;
- `N` — число фазовых доменов.

Протокол использует:

`R_t_phase_order`

как индикатор глобальной фазовой синхронизации.

## Обязательные семантические различия

Модуль сохраняет следующие различия:

`фазовая синхронизация ≠ фазовая когерентность`

`R(t) ≠ C(t)`

`C_proxy(t) ≠ C(t)`

`фазово-амплитудный прокси-параметр ≠ общая эндогенная структурная когерентность`

`exchange_activity_proxy ≠ J_flux`

`управляемое снятие сопряжения ≠ автоматически обнаруженная физическая бифуркация`

`распад амплитудного режима ≠ распад проявленной массы`

`удерживаемый фазовый аттрактор ≠ полная материальная форма`

Эти термины являются фиксированными семантическими инвариантами модуля.

## Диагностический прокси-параметр эндогенной когерентности

Протокол использует:

`C_proxy(t)`

`C_proxy(t)` является ограниченным диагностическим прокси-параметром, используемым для управления протоколом и классификации режимов.

Возможная операционная форма:

`C_proxy(t) = w_R R(t) + w_PA PA(t) + w_V V_stability(t) + w_A A_stability(t)`

где:

- `R(t)` — глобальный параметр фазового порядка;
- `PA(t)` — фазово-амплитудный прокси-параметр;
- `V_stability(t)` — нормированный вклад устойчивости фазовых скоростей;
- `A_stability(t)` — нормированный вклад устойчивости амплитуд;
- `w_R`, `w_PA`, `w_V` и `w_A` — неотрицательные весовые коэффициенты;
- сумма всех весовых коэффициентов равна `1`.

Вклад устойчивости фазовых скоростей может быть представлен как:

`V_stability(t) = 1 / (1 + sigma_v(t) / v_ref)`

где:

- `sigma_v(t)` — дисперсия фазовых скоростей;
- `v_ref` — положительный опорный масштаб.

Вклад устойчивости амплитуд может быть представлен как:

`A_stability(t) = 1 / (1 + sigma_A(t) / A_ref)`

где:

- `sigma_A(t)` — дисперсия амплитуд;
- `A_ref` — положительный опорный масштаб.

`C_proxy(t)` остаётся численным диагностическим параметром уровня протокола.

## Нормированное внешнее давление

Протокол использует нормированный параметр внешнего давления:

`P_ext(t)`

`P_ext(t)` выражается в той же ограниченной диагностической шкале, что и `C_proxy(t)`.

Рекомендуемый диапазон:

`0 ≤ P_ext(t) ≤ 1`

Значения за пределами настроенного диапазона отклоняются или явно нормируются до использования.

## Запас удержания

Запас удержания:

`retention_margin(t) = C_proxy(t) - P_ext(t)`

Протокол классифицирует три динамических режима с использованием настраиваемого допуска `epsilon_EDC`.

### Удерживаемый режим

`retention_margin(t) > epsilon_EDC`

Интерпретация:

`C_proxy(t) > P_ext(t)`

Диагностическая способность удерживаемого фазового режима превышает нормированное внешнее давление.

### Критический режим EDC

`absolute(retention_margin(t)) ≤ epsilon_EDC`

Интерпретация:

`C_proxy(t) приблизительно равно P_ext(t)`

Система находится вблизи диагностической границы удержания.

### Деградационный режим

`retention_margin(t) < -epsilon_EDC`

Интерпретация:

`C_proxy(t) < P_ext(t)`

Нормированное внешнее давление превышает диагностическую способность удержания.

После входа в деградационный режим протокол рассчитывает и накапливает критическое воздействие до активации разблокировки.

## Этап формирования аттрактора

Протокол начинается с этапа формирования при настроенных базовых параметрах:

`исходная константа сопряжения K_initial`

`базовый внешний форсинг F_hold`

`базовая фаза форсинга Psi_hold`

`базовое нормированное давление P_hold`

`настроенный фазовый сдвиг alpha`

`фиксированные естественные частоты`

`настроенный фазовый и амплитудный шум`

На каждом такте протокол регистрирует:

`R(t)`

`Psi(t)`

`фазово-амплитудный прокси-параметр`

`среднюю фазовую скорость`

`дисперсию фазовых скоростей`

`среднюю амплитуду`

`дисперсию амплитуд`

`прокси-параметр энергии сопряжения`

`C_proxy(t)`

`P_ext(t)`

`запас удержания`

Аттрактор объявляется сформированным только после сохранения всех настроенных критериев формирования на последовательном интервале подтверждения.

## Критерии формирования аттрактора

Возможные критерии формирования:

`R(t) ≥ R_form_min`

`phase_amplitude_order_proxy ≥ PA_form_min`

`phase_velocity_dispersion ≤ V_disp_form_max`

`amplitude_dispersion ≤ A_disp_form_max`

`retention_margin > epsilon_EDC`

Критерии должны сохраняться в течение:

`formation_confirmation_tacts`

последовательных тактов.

После подтверждения протокол может перейти в состояние:

`RETAINED_ATTRACTOR`

## Проверка удерживаемого состояния

После формирования протокол может поддерживать дополнительный интервал проверки:

`retained_verification_tacts`

Этот интервал подтверждает, что аттрактор является удерживаемым динамическим состоянием, а не временным всплеском синхронизации.

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

`step`

`linear_ramp`

`smooth_ramp`

`externally supplied sequence`

Профиль давления является явным и воспроизводимым.

Примеры:

`P_ext(t) = P_hold до начала нагружения`

`P_ext(t) = P_collapse после ступенчатого перехода`

или:

`P_ext(t + dt) = minimum(P_collapse, P_ext(t) + pressure_ramp_rate dt)`

Протокол регистрирует первый такт, на котором:

`retention_margin(t) ≤ epsilon_EDC`

и первый такт, на котором:

`retention_margin(t) < -epsilon_EDC`

## Превышение давления

Превышение давления:

`pressure_excess(t) = maximum(P_ext(t) - C_proxy(t), 0)`

Когда:

`pressure_excess(t) = 0`

аккумулятор критического воздействия сохраняет текущее значение.

Когда:

`pressure_excess(t) > 0`

система накапливает критическое воздействие в соответствии с ретардационным законом.

## Ретардационный закон

Протокол представляет настроенное соотношение задержки, обратно пропорциональной кубическому корню, через:

`v(t) = mu pressure_excess(t)`

и:

`tau_delay(t) = tau_0 / (v(t) + epsilon_v)^(1/3)`

где:

- `mu` — коэффициент преобразования превышения давления в скорость срыва;
- `tau_0` — базовый масштаб задержки;
- `epsilon_v` — малый положительный численный регуляризатор;
- `tau_delay(t)` — мгновенный диагностический масштаб задержки.

Эквивалентная запись:

`tau_delay(t) пропорционально v(t)^(-1/3)`

Это соотношение является настраиваемым модельным предположением численного протокола.

## Аккумулятор критического воздействия

Критическое воздействие накапливается как:

`critical_exposure(t + dt) = critical_exposure(t) + dt / tau_delay(t)`

когда:

`pressure_excess(t) > 0`

Узел фазового сопряжения разблокируется при условии:

`critical_exposure ≥ critical_exposure_threshold`

До достижения этого условия система остаётся в состоянии:

`CRITICAL_EXPOSURE`

Этот механизм делает `tau_delay` операционным параметром, влияющим на момент срабатывания.

## Восстановление до разблокировки

Если запас удержания снова становится положительным до выполнения условия:

`critical_exposure ≥ critical_exposure_threshold`

протокол может использовать один из двух настраиваемых режимов:

`persistent exposure`

`decaying exposure`

В режиме `persistent exposure` накопленное воздействие сохраняется.

В режиме `decaying exposure`:

`critical_exposure(t + dt) = maximum(0, critical_exposure(t) - exposure_recovery_rate dt)`

Выбранный режим фиксируется в конфигурации и журналах протокола.

## Разблокировка фазового узла

Когда:

`critical_exposure ≥ critical_exposure_threshold`

протокол регистрирует:

`unlock_tact`

`unlock_time`

`R_unlock`

`phase_amplitude_order_unlock`

`amplitude_mean_unlock`

`amplitude_dispersion_unlock`

`C_proxy_unlock`

`P_ext_unlock`

`retention_margin_unlock`

`tau_delay_unlock`

После этого протокол переходит в состояние:

`PHASE_NODE_UNLOCKED`

Последующая эволюция эффективного сопряжения управляется настраиваемым законом снятия сопряжения.

## Снятие эффективного сопряжения

Эффективное сопряжение после разблокировки может изменяться как:

`K_eff(t + dt) = K_floor + (K_eff(t) - K_floor) exp(-dt / tau_K)`

где:

- `K_floor` — минимальный удерживаемый уровень сопряжения;
- `tau_K` — временной масштаб снятия сопряжения.

Также может поддерживаться явный режим мгновенного снятия:

`K_eff = K_floor`

который фиксируется в конфигурации как:

`instantaneous coupling quench`

## Рост фазового рассогласования

После разблокировки протокол может увеличивать фазовое рассогласование через настраиваемые каналы.

Возможные каналы:

`phase_noise_strength`

`natural-frequency-dispersion multiplier`

`external-forcing removal`

`forcing-phase displacement`

`Sakaguchi phase-lag modification`

Возможное управление дисперсией естественных частот:

`omega_effective_i = omega_mean + frequency_dispersion_multiplier (omega_i - omega_mean)`

Исходный массив естественных частот остаётся фиксированным.

Протокол применяет временное эффективное преобразование, выводимое из фиксированного базового массива.

## Внешний форсинг

Внешний форсинг независим от внутренней средней фазы.

Вклад форсинга сохраняется как:

`F_ext sin(Psi_ext - theta_i)`

где:

- `F_ext` — плотность внешнего форсинга;
- `Psi_ext` — фаза внешнего форсинга.

Протокол может уменьшать `F_ext` после разблокировки с сохранением настроенного отношения внешней фазы форсинга.

## Распад амплитудного режима

Протокол может применять дополнительный постразблокировочный вклад распада амплитудного режима.

Численно устойчивая экспоненциальная форма:

`A_i(t + dt) = A_floor + (A_i(t) - A_floor) exp(-lambda_A(t) dt)`

где:

`lambda_A(t) = amplitude_decay_scale / maximum(tau_delay(t), tau_min)`

и:

- `A_floor` — настроенная минимальная амплитуда;
- `tau_min` предотвращает численную расходимость;
- `amplitude_decay_scale` управляет дополнительным демпфированием на этапе срыва.

Этот вклад применяется отдельно от базового закона амплитудной релаксации GPU-среднеполевого движка.

## Последующие величины EDK

Протокол регистрирует фазовые и амплитудные диагностические параметры срыва удержания.

Последующие интеграционные слои EDK могут рассчитывать или реконструировать:

- проявленную массу `M(t)`;
- тензор удерживаемого интерфейса `T_int`;
- полное пространственное поле сквозного потока обмена `J_flux`;
- молекулярную реконструкцию;
- биологическую реконструкцию;
- магнитогидродинамические режимы плазмы;
- интерпретации материализации или дематериализации.

Скалярный диагностический параметр уровня протокола называется:

`exchange_activity_proxy`

Возможная ограниченная диагностическая форма может объединять:

`среднюю амплитуду`

`R(t)`

`фазово-амплитудный прокси-параметр`

`устойчивость фазовых скоростей`

Полное интеграционное поле `J_flux` требует:

- пространственного направления;
- локальной топологии обмена;
- временной эволюции;
- дивергенции;
- ротора;
- сопряжения с удерживаемым интерфейсом;
- сопряжения с фоновыми модами Континуума.

## Состояния протокола

Машина состояний протокола может содержать:

`INITIALIZED`

`FORMING_ATTRACTOR`

`RETAINED_ATTRACTOR`

`CRITICAL_APPROACH`

`CRITICAL_EXPOSURE`

`PHASE_NODE_UNLOCKED`

`COLLAPSE_ACTIVE`

`DEGRADED_PHASE_REGIME`

`COLLAPSE_COMPLETED`

`COLLAPSE_NOT_REACHED`

Переходы состояний определяются явными критериями и регистрируются на соответствующем такте.

## Критерии срыва

Этап срыва оценивается по измеряемой динамике.

Возможные критерии фазового срыва:

`R(t) ≤ R_collapse_threshold`

или:

`R(t) ≤ phase_order_fraction R_unlock`

Возможные фазово-амплитудные критерии:

`phase_amplitude_order_proxy ≤ PA_collapse_threshold`

Возможные критерии дисперсии:

`phase_velocity_dispersion ≥ V_disp_collapse_threshold`

Возможный комбинированный критерий:

`критерий фазового срыва и фазово-амплитудный критерий срыва и минимальная длительность после разблокировки`

Выбранный критерий явно указывается в конфигурации.

## Период полураспада фазового порядка

Период полураспада фазового порядка измеряется относительно состояния разблокировки.

Определяется:

`R_half_target = 0.5 R_unlock`

Период полураспада фазового порядка:

`t_R_half = первый момент после разблокировки, когда R(t) ≤ R_half_target`

Если это условие остаётся недостигнутым в течение настроенного интервала наблюдения, результат сохраняется как:

`not reached`

## Период полураспада амплитудного режима

Определяется расстояние средней амплитуды от настроенного нижнего уровня:

`D_A(t) = mean_amplitude(t) - A_floor`

При разблокировке:

`D_A_unlock = mean_amplitude_unlock - A_floor`

Целевое значение половинного распада:

`D_A_half = 0.5 D_A_unlock`

Период полураспада амплитудного режима является первым моментом после разблокировки, когда:

`D_A(t) ≤ D_A_half`

Если целевое значение остаётся недостигнутым, результат сохраняется как:

`not reached`

## Время распада аттрактора

Время распада аттрактора измеряется от:

`unlock_time`

до первого такта, выполняющего настроенный критерий срыва.

Протокол сохраняет:

`collapse_tact`

`collapse_time`

`collapse_duration_after_unlock`

Протокол также сохраняет случаи, когда аттрактор остаётся удержанным в течение полного интервала наблюдения.

## Максимальный интервал наблюдения

Протокол использует:

`maximum_post_unlock_tacts`

или:

`maximum_post_unlock_time`

для ограничения симуляции.

Если ни один критерий срыва не достигнут на этом интервале, конечное состояние:

`COLLAPSE_NOT_REACHED`

Это является допустимым конечным результатом эксперимента.

## Основная конфигурация

Конфигурация протокола включает:

`formation_maximum_tacts`

`formation_confirmation_tacts`

`retained_verification_tacts`

`R_form_min`

`phase_amplitude_form_min`

`phase_velocity_dispersion_form_max`

`amplitude_dispersion_form_max`

`coherence_weight_R`

`coherence_weight_phase_amplitude`

`coherence_weight_phase_velocity`

`coherence_weight_amplitude`

`phase_velocity_reference`

`amplitude_dispersion_reference`

`retained_boundary_tolerance`

`pressure_schedule`

`pressure_hold`

`pressure_collapse`

`pressure_ramp_rate`

`delay_base_tau_0`

`pressure_velocity_coefficient_mu`

`delay_regularization_epsilon`

`minimum_delay_tau`

`critical_exposure_threshold`

`exposure_recovery_mode`

`exposure_recovery_rate`

`coupling_quench_mode`

`coupling_floor`

`coupling_quench_tau`

`post_unlock_phase_noise_multiplier`

`post_unlock_frequency_dispersion_multiplier`

`post_unlock_amplitude_decay_scale`

`phase_order_collapse_threshold`

`phase_order_collapse_fraction`

`phase_amplitude_collapse_threshold`

`phase_velocity_dispersion_collapse_threshold`

`maximum_post_unlock_tacts`

`log_every`

`field_every`

## Конфигурация базового движка

Базовый среднеполевой движок сохраняет собственную конфигурацию:

`num_domains`

`coupling_strength_k`

`sakaguchi_phase_lag_alpha`

`natural_frequency_mean`

`natural_frequency_std`

`external_forcing_phase`

`phase_noise_strength`

`amplitude_growth_rate`

`amplitude_saturation_rate`

`amplitude_noise_strength`

`amplitude_minimum`

`amplitude_maximum`

`seed`

`dtype`

`backend`

`device_id`

Динамические параметры протокола, например `K_eff`, хранятся отдельно.

## Основные скалярные диагностические параметры

Протокол регистрирует:

`tact_index`

`simulation_time`

`protocol_state`

`R_t_phase_order`

`global_mean_phase`

`phase_amplitude_order_proxy`

`mean_phase_velocity`

`phase_velocity_dispersion`

`mean_amplitude`

`amplitude_dispersion`

`minimum_amplitude`

`maximum_amplitude`

`coupling_energy_proxy`

`C_proxy_t`

`external_pressure_P_ext`

`retention_margin`

`pressure_excess`

`instantaneous_delay_tau`

`critical_exposure`

`initial_coupling_K`

`effective_coupling_K`

`coupling_floor_K`

`effective_phase_noise_strength`

`effective_frequency_dispersion_multiplier`

`effective_amplitude_decay_rate`

`attractor_formed`

`attractor_verified`

`phase_node_unlocked`

`collapse_detected`

`formation_tact`

`unlock_tact`

`collapse_tact`

`phase_order_half_life`

`amplitude_regime_half_life`

`attractor_collapse_duration`

## Полные снимки полей

Дополнительные снимки полей могут включать:

`phases`

`amplitudes`

`natural_frequencies`

`effective_natural_frequencies`

`phase_velocity`

`amplitude_velocity`

`phase_noise_increment`

`amplitude_noise_increment`

Полные снимки полей экспортируются согласно настроенной частоте снимков.

## Стратегия журналирования

Рекомендуемое журналирование:

`JSON → состояние протокола, скалярные метрики, конфигурация, события переходов`

`NPZ → массивы фаз, амплитуд, частот и скоростей`

Компактные метрики записываются согласно:

`log_every`

Полные снимки полей записываются согласно:

`field_every`

События переходов записываются немедленно при входе протокола в состояния:

`RETAINED_ATTRACTOR`

`CRITICAL_EXPOSURE`

`PHASE_NODE_UNLOCKED`

`COLLAPSE_ACTIVE`

`COLLAPSE_COMPLETED`

`COLLAPSE_NOT_REACHED`

## Атомарная запись

Выходные файлы JSON и NPZ записываются атомарно:

`временный файл ↓ flush ↓ fsync ↓ os.replace ↓ конечный файл`

Это снижает риск появления неполных снимков протокола после прерывания.

## Диагностический модуль

Файл:

`marnov_retention_diagnostics.py`

Диагностический модуль формирует визуализации по рассчитанным данным протокола.

Рекомендуемые графики:

1. `R(t)`, фазово-амплитудный прокси-параметр и `C_proxy(t)`;
2. нормированное внешнее давление и запас удержания;
3. критическое воздействие и мгновенный `tau_delay`;
4. исходное и эффективное сопряжение `K`;
5. дисперсии фазовых скоростей и амплитуд;
6. средняя амплитуда и целевое значение половинного распада;
7. переходы состояний протокола;
8. маркеры полураспада фазового порядка и времени срыва.

Диагностика показывает фактически рассчитанную траекторию протокола.

## Масштабирование GPU

Протокол наследует глобальное среднеполевое масштабирование `O(N)` от:

`EDKGPUMeanFieldPhaseEngine`

Для:

`N = 131072`

одна плотная попарная матрица содержала бы:

`17179869184 элементов`

Приблизительный объём памяти одной матрицы:

`float32 → 64 GiB`

`float64 → 128 GiB`

Эти значения не учитывают дополнительные массивы синусов, временные массивы, редукции или накладные расходы пула памяти.

Среднеполевой движок сохраняет масштабируемое исполнение через глобальные параметры порядка.

## Выбор бэкенда

Режимы бэкенда наследуются от GPU-среднеполевого движка:

`auto`

`gpu`

`cpu`

Совместимое устройство CUDA проверяется базовым движком.

Протокол может запускаться на CPU для небольших проверочных случаев.

Крупномасштабные запуски должны выполняться после измерения памяти и производительности.

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

Фиксированные естественные частоты остаются неизменными на протяжении всего протокола.

Любое эффективное постразблокировочное преобразование частот выводится из фиксированного базового массива.

## Состояния отказа

Протокол явно сообщает состояния отказа.

Примеры:

`ATTRACTOR_NOT_FORMED`

`ATTRACTOR_NOT_VERIFIED`

`INVALID_PRESSURE_SCALE`

`CRITICAL_BOUNDARY_NOT_REACHED`

`UNLOCK_NOT_TRIGGERED`

`COLLAPSE_NOT_REACHED`

`NUMERICAL_INSTABILITY`

`NON_FINITE_STATE`

Незавершённый эксперимент срыва сохраняется как явный диагностический результат.

## Базовый запуск

Проверочный запуск на CPU:

`python marnov_retention_collapse_protocol.py --backend cpu`

Автоматический выбор бэкенда:

`python marnov_retention_collapse_protocol.py --backend auto`

Явный запуск на GPU:

`python marnov_retention_collapse_protocol.py --backend gpu --device-id 0`

Крупномасштабный запуск на GPU:

`python marnov_retention_collapse_protocol.py --backend gpu --num-domains 131072`

Диагностика:

`python marnov_retention_diagnostics.py --snapshot-dir edk_marnov_snapshots`

Дымовой тест:

`python smoke_test.py`

## Требования дымового теста

Дымовой тест проверяет:

- успешную инициализацию CPU;
- корректный импорт GPU-среднеполевого движка;
- выбор бэкенда через базовый движок;
- воспроизводимую инициализацию при фиксированном seed;
- неизменность естественных частот;
- корректное исполнение этапа формирования;
- проверку удерживаемого аттрактора;
- ограниченность `C_proxy(t)`;
- ограниченность нормированного внешнего давления;
- корректный расчёт запаса удержания;
- корректную классификацию EDS, EDC и деградационного режима;
- конечность `tau_delay`;
- корректное накопление критического воздействия;
- задержанную разблокировку до выполнения порога;
- корректное событие разблокировки после выполнения порога;
- монотонное снижение сопряжения после разблокировки при выборе экспоненциального снятия;
- корректное сворачивание фаз;
- конечность массивов фаз и амплитуд;
- неотрицательность дисперсий;
- расчёт периода полураспада фазового порядка;
- расчёт периода полураспада амплитудного режима;
- корректный результат `COLLAPSE_NOT_REACHED` при недостижении порогов;
- экспорт компактного JSON;
- экспорт полей NPZ;
- атомарную замену файлов;
- успешное формирование диагностики по тестовым снимкам.

## Исследовательский статус

Этот модуль является численным исследовательским компонентом вычислительной архитектуры EDK.

Он предоставляет управляемый протокол для исследования:

`формирования удержания`

`критического нагружения`

`задержанной разблокировки`

`снятия сопряжения`

`распада фазового аттрактора`

`распада амплитудного режима`

Ретардационное соотношение обратного кубического корня реализуется как настраиваемое модельное предположение, последствия которого могут численно сравниваться с альтернативными законами задержки.

## Лицензия

Модуль наследует лицензию родительского репозитория EDK.
