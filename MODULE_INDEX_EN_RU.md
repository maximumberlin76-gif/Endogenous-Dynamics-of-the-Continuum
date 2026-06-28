# MODULE INDEX EN/RU

# Endogenous Dynamics of the Continuum (EDK)

## Repository Module Index

This file provides the module-level navigation map for the repository Endogenous-Dynamics-of-the-Continuum.

It does not replace the individual module README files.

It defines the repository as a unified computational and theorem-algorithmic architecture of the open nonlinear dissipative dynamic Continuum, where each module occupies a controlled layer in the EDK cascade.

The repository must be read as a linked system:

phase layers → Φ → phase coherence → C(t) → T_int → M(t) → J_flux → biological / molecular modulation

and in the reverse chain:

loss of C(t) → degradation of T_int → demanifestation of M(t) → growth of J_flux → return into background modes of the Continuum

## 1. Core Repository Layer

### 1.1. framework_core.py

Role:

Quantum-phase core of the model.

Main purpose:

Models the transition from phase coherence of multiplet layers toward interface retention, manifested mass anchoring and exchange-flow formation.

Main entities:

ContinuumSimulation

calculate_phi_operator

update_state

run_marnov_demolition

Primary EDK meaning:

The module belongs to the base computational layer that connects phase coherence, Φ, C(t), T_int, M(t) and J_flux.

Controlled distinctions:

R(t) is not identical to C(t).

Phase synchronization is not identical to phase coherence.

J is not automatically identical to J_flux.

### 1.2. continuum_core_engine.py

Role:

Early system cascade orchestrator.

Main purpose:

Links solar, planetary, quantum-phase, biological and molecular layers into a single recursive tact-by-tact cascade.

Main entities:

ContinuumCoreEngine

execute_cascade_step

trigger_marnov_collapse_cascade

Primary EDK meaning:

This file represents the early system-level orchestration layer before the newer hierarchical orchestrator was introduced.

Controlled distinctions:

Cascade execution is not a replacement for C(t).

Cascade state is not a replacement for T_int.

Module coordination is not identical to full hierarchical EDK orchestration.

### 1.3. THEORY_TENSOR_MATRIX.md

Role:

Tensor-coupling theory layer.

Main purpose:

Defines the dynamic interface tensor T_int and its decomposition into isotropic and deviatoric components.

Core expressions:

T_int = [ σ_xx  τ_xy  τ_xz ] [ τ_yx  σ_yy  τ_yz ] [ τ_zx  τ_zy  σ_zz ]

T_int = T_iso + T_dev = C(t) · I + τ_dev

Primary EDK meaning:

T_int is the interface tensor of manifestation, coupling and retention of form.

Controlled distinctions:

T_int is not identical to M(t).

R(θ) is not identical to C(t).

The tensor matrix is not a substitute for the full EDK cascade.

### 1.4. phase_coupling_protocol/

Role:

Universal meta-protocol layer.

Main file:

phase_coupling_protocol/universal_meta_protocol_EN_RU.md

Main purpose:

Provides the repository-level protocol of phase coupling for heterogeneous systems.

Primary EDK meaning:

This module fixes the meta-protocol chain of phase coupling, endogenous structural coherence, T_int retention, M(t) anchoring, J_flux exchange and reverse demanifestation.

Controlled distinctions:

J is not identical to J_flux.

C_proxy(t) is not identical to C(t).

Phase-amplitude proxy is not full endogenous structural coherence.

The meta-protocol is not a completed experimentally confirmed physical theory.

## 2. Phase Dynamics Layer

### 2.1. module_edk_gpu_mean_field_phase_engine/

Role:

GPU / CPU mean-field phase dynamics engine.

Main files:

module_edk_gpu_mean_field_phase_engine/README_EN_RU.md

module_edk_gpu_mean_field_phase_engine/edk_gpu_mean_field_phase_engine.py

module_edk_gpu_mean_field_phase_engine/benchmark_gpu_phase_engine.py

module_edk_gpu_mean_field_phase_engine/test_gpu_mean_field_phase_engine.py

module_edk_gpu_mean_field_phase_engine/smoke_test.py

module_edk_gpu_mean_field_phase_engine/__init__.py

Main entities:

MeanFieldPhaseConfig

EDKGPUMeanFieldPhaseEngine

EDKGPUMeanFieldLogger

Primary computational function:

Implements exact Kuramoto-Sakaguchi mean-field phase coupling with O(N) computational complexity and without allocation of an N × N phase-difference matrix.

Primary EDK meaning:

This module calculates global phase-order diagnostics, phase-amplitude proxy quantities and amplitude-regime dynamics. It provides a high-density computational layer for global phase dynamics.

Main outputs:

R_t_phase_order

global_mean_phase

phase_amplitude_order_proxy

mean_phase_velocity

phase_velocity_dispersion

mean_amplitude

amplitude_dispersion

coupling_energy_proxy

gpu_mean_field_tact_*.json

gpu_mean_field_step_*.json

gpu_mean_field_field_*.npz

Execution:

python module_edk_gpu_mean_field_phase_engine/edk_gpu_mean_field_phase_engine.py --backend cpu

Benchmark:

python module_edk_gpu_mean_field_phase_engine/benchmark_gpu_phase_engine.py

Smoke test:

python module_edk_gpu_mean_field_phase_engine/smoke_test.py

Unit tests:

python -m unittest module_edk_gpu_mean_field_phase_engine/test_gpu_mean_field_phase_engine.py

Controlled distinctions:

R(t) is not identical to C(t).

Mean-field phase order is not full endogenous structural coherence.

Phase synchronization is not phase coherence.

Phase-amplitude proxy is not full C(t).

Amplitude proxy is not manifested mass M(t).

exchange_activity_proxy is not J_flux.

GPU acceleration does not change model meaning.

O(N) mean-field scaling does not allocate an N × N phase-difference matrix.

Fixed natural frequencies are not tact-by-tact stochastic phase noise.

## 3. Delay and Local Coupling Layer

### 3.1. module_edk_spatiotemporal_phase_delay/

Role:

Spatiotemporal phase-delay engine.

Main files:

module_edk_spatiotemporal_phase_delay/README_EN_RU.md

module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py

module_edk_spatiotemporal_phase_delay/edk_delay_diagnostics.py

module_edk_spatiotemporal_phase_delay/test_spatiotemporal_phase_delay.py

module_edk_spatiotemporal_phase_delay/smoke_test.py

module_edk_spatiotemporal_phase_delay/__init__.py

Main entities:

PhaseDelayConfig

EDKSpatiotemporalPhaseDelayEngine

EDKDelayLogger

Primary computational function:

Models metric propagation delay between spatially distributed phase domains.

Core expression:

tau_ij = distance_ij / c

d theta_i / dt = omega_i + K sum_j w_ij sin(theta_j(t - tau_ij) - theta_i(t) - alpha) + F_i(t)

Primary EDK meaning:

This module introduces local retarded phase coupling, delayed phase reconstruction and spatial neighbor topology.

Main outputs:

delay_tact_*.json

delay_step_*.json

delay_field_*.npz

delay diagnostics figures

Execution:

python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend cpu

Diagnostics:

python module_edk_spatiotemporal_phase_delay/edk_delay_diagnostics.py

Smoke test:

python module_edk_spatiotemporal_phase_delay/smoke_test.py

Unit tests:

python -m unittest module_edk_spatiotemporal_phase_delay/test_spatiotemporal_phase_delay.py

Controlled distinctions:

Instantaneous mean-field coupling is not metrically delayed local coupling.

Delayed local phase order is not full phase coherence.

Propagation delay is not automatically stabilizing influence.

Delay-field diagnostics are not J_flux.

Retarded phase states are not downstream EDK interface, mass or exchange-flow quantities.

## 4. Vortex Phase-Field Layer

### 4.1. module_edk_vortex_phase_field/

Role:

Vortex phase-field diagnostic engine.

Main files:

module_edk_vortex_phase_field/README_EN_RU.md

module_edk_vortex_phase_field/edk_vortex_phase_field.py

module_edk_vortex_phase_field/edk_vortex_diagnostics.py

module_edk_vortex_phase_field/test_vortex_phase_field.py

module_edk_vortex_phase_field/smoke_test.py

Main entities:

EDKVortexPhaseFieldEngine

EDKVortexLogger

Primary computational function:

Models local spatial phase-field structure, directed current, discrete vortex diagnostics and asymmetric vortex contributions.

Primary EDK meaning:

This module tests how spatial twisting and vortex asymmetry contribute to phase-field diagnostics without replacing full EDK quantities.

Main outputs:

vortex_step_*.json

vortex_field_*.npz

positive_vortex_support

negative_vortex_penalty

interface_retention_proxy

continuum_appearance_index

Execution:

python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend cpu

Diagnostics:

python module_edk_vortex_phase_field/edk_vortex_diagnostics.py

Smoke test:

python module_edk_vortex_phase_field/smoke_test.py

Unit tests:

python -m unittest module_edk_vortex_phase_field/test_vortex_phase_field.py

Controlled distinctions:

Local vortex moment is not strict rot J.

Positive vortex contribution is not automatic stabilization.

C_proxy(t) is not C(t).

interface_retention_proxy is not T_int.

M_proxy(t) is not M(t).

Vortex diagnostics are not the full field J_flux.

## 5. Retention-Collapse Layer

### 5.1. module_edk_marnov_retention_collapse_protocol/

Role:

Marnov retention-collapse protocol.

Main files:

module_edk_marnov_retention_collapse_protocol/README_EN_RU.md

module_edk_marnov_retention_collapse_protocol/marnov_retention_collapse_protocol.py

module_edk_marnov_retention_collapse_protocol/marnov_retention_diagnostics.py

module_edk_marnov_retention_collapse_protocol/test_marnov_retention_collapse_protocol.py

Main entities:

MarnovRetentionCollapseConfig

EDKMarnovRetentionCollapseProtocol

EDKMarnovProtocolLogger

Primary computational function:

Models phase-attractor formation, retained-regime verification, critical loading, delayed phase-node unlocking, coupling release and phase-attractor decay.

Primary EDK meaning:

This module defines a controlled numerical protocol for testing retention and collapse under external parasitic pressure.

Core condition:

P_ext >> C(t)

Collapse chain:

P_ext >> C(t) → degradation of T_int → demanifestation of M(t) → growth of J_flux → return into background modes of the Continuum

Delay scaling:

t_delay ~ v^(-1/3)

v = mu · P_ext

Main outputs:

marnov_step_*.json

marnov_field_*.npz

marnov_protocol_summary.json

phase-order half-life

amplitude-regime half-life

critical exposure

retention margin

Diagnostics:

python module_edk_marnov_retention_collapse_protocol/marnov_retention_diagnostics.py

Unit tests:

python -m unittest module_edk_marnov_retention_collapse_protocol/test_marnov_retention_collapse_protocol.py

Controlled distinctions:

Retained phase attractor is not full material form.

C_proxy(t) is not C(t).

Amplitude-regime decay is not manifested mass decay.

exchange_activity_proxy is not J_flux.

Phase synchronization is not phase coherence.

Protocol dynamics must not manually force diagnostic quantities toward a predetermined result.

## 6. Hierarchical Orchestration Layer

### 6.1. module_edk_hierarchical_orchestrator/

Role:

Hierarchical EDK orchestrator.

Main files:

module_edk_hierarchical_orchestrator/README_EN_RU.md

module_edk_hierarchical_orchestrator/edk_hierarchical_orchestrator.py

module_edk_hierarchical_orchestrator/hierarchical_diagnostics.py

module_edk_hierarchical_orchestrator/test_hierarchical_orchestrator.py

module_edk_hierarchical_orchestrator/smoke_test.py

module_edk_hierarchical_orchestrator/__init__.py

Main entities:

EDKHierarchicalOrchestrator

EDKHierarchicalState

EDKModuleRegistry

EDKForwardCascadePacket

EDKFeedbackPacket

PhiOperator

EDKHierarchicalLogger

Primary computational function:

Coordinates multiple EDK modules into a unified tact-by-tact hierarchical execution chain.

Primary EDK meaning:

This module preserves T_int continuity, J_flux continuity, recursive Φ update, inherited tact state and field provenance across module stages.

Main outputs:

hierarchical_step_*.json

hierarchical_field_*.npz

hierarchical diagnostics reports

Execution:

python module_edk_hierarchical_orchestrator/edk_hierarchical_orchestrator.py

Diagnostics:

python module_edk_hierarchical_orchestrator/hierarchical_diagnostics.py

Smoke test:

python module_edk_hierarchical_orchestrator/smoke_test.py

Unit tests:

python -m unittest module_edk_hierarchical_orchestrator/test_hierarchical_orchestrator.py

Controlled distinctions:

C(t) is not C_proxy(t).

C(t) is not C3.

T_int is not M(t).

J_flux is not J_vector.

Scalar exchange proxy is not J_flux.

Hierarchical orchestration is not a replacement of original EDK quantities.

Module registry is not the physical model itself.

## 7. Macro, Planetary, Biological and Molecular Layers

### 7.1. module_solar_synthesis/

Role:

Macroscopic solar synthesis layer.

Main file:

module_solar_synthesis/solar_synthesis_resonator.py

Main entity:

SolarSynthesisResonator

Primary computational function:

Models the Sun as a macroscopic phase node retained in a synthesis phase.

Primary EDK meaning:

The amplitude layer of plasma may remain chaotic, while the phase layer may retain a high level of endogenous coherence.

Execution:

python module_solar_synthesis/solar_synthesis_resonator.py

Controlled distinctions:

Chaotic amplitude layer is not automatic loss of phase coherence.

Solar synthesis layer is not the whole EDK cascade.

Macro-light flux is not automatically J_flux.

### 7.2. module_planetary_resonance/

Role:

Planetary resonance layer.

Main file:

module_planetary_resonance/schumann_planetary_resonator.py

Main entity:

SchumannPlanetaryResonator

Primary computational function:

Calculates planetary forcing and models Schumann modes as a global planetary tact field.

Primary EDK meaning:

Planetary resonance modulates biological phase alignment, DNA-biophoton dynamics and molecular phase chemistry.

Execution:

python module_planetary_resonance/schumann_planetary_resonator.py

Controlled distinctions:

Planetary forcing is not full C(t).

Schumann-mode modulation is not direct proof of biological phase coherence.

Planetary tact field is not the whole Continuum.

### 7.3. module_wave_genetics/

Role:

Biological wave layer.

Main file:

module_wave_genetics/wave_genetics_dna_oscillator.py

Main entity:

WaveGeneticsDNAOscillator

Primary computational function:

Transforms J_flux into modulated biophoton signal and residual phantom trace within the numerical model.

Primary EDK meaning:

DNA is represented as a polarized biophoton laser-interferometric structure inside the model.

Execution:

python module_wave_genetics/wave_genetics_dna_oscillator.py

Controlled distinctions:

Biophoton modulation is not the full J_flux.

Phantom trace is not full material form.

Biological phase alignment is not full endogenous structural coherence.

### 7.4. module_molecular_chemistry/

Role:

Molecular phase-chemistry layer.

Main file:

module_molecular_chemistry/molecular_phase_chemistry.py

Main entity:

MolecularPhaseChemistry

Primary computational function:

Models chemical bonds as stable phase relations between atomic or molecular oscillators.

Primary EDK meaning:

Chemical bonding is treated as a phase relation supported by medium memory, biophoton forcing and sufficient molecular coherence.

Execution:

python module_molecular_chemistry/molecular_phase_chemistry.py

Controlled distinctions:

Molecular coherence is not full C(t).

Chemical bond demanifestation is not automatically full M(t) demanifestation.

Biophoton forcing is not J_flux itself.

## 8. Execution Map

Recommended basic execution order:

1. Run unit tests for the computational modules.

2. Run smoke tests for each active module.

3. Run diagnostics only after valid snapshots are produced.

4. Run the hierarchical orchestrator after individual modules pass their smoke tests.

Core commands:

python -m unittest module_edk_gpu_mean_field_phase_engine/test_gpu_mean_field_phase_engine.py

python module_edk_gpu_mean_field_phase_engine/smoke_test.py

python -m unittest module_edk_spatiotemporal_phase_delay/test_spatiotemporal_phase_delay.py

python module_edk_spatiotemporal_phase_delay/smoke_test.py

python -m unittest module_edk_vortex_phase_field/test_vortex_phase_field.py

python module_edk_vortex_phase_field/smoke_test.py

python -m unittest module_edk_marnov_retention_collapse_protocol/test_marnov_retention_collapse_protocol.py

python -m unittest module_edk_hierarchical_orchestrator/test_hierarchical_orchestrator.py

python module_edk_hierarchical_orchestrator/smoke_test.py

## 9. Repository-Level Controlled Distinctions

The following distinctions must be preserved across all modules and documentation:

R(t) ≠ C(t)

C_proxy(t) ≠ C(t)

C(t) ≠ C3

T_int ≠ M(t)

J ≠ J_flux

J_vector ≠ J_flux

macro_light_flux ≠ J_flux

exchange_activity_proxy ≠ J_flux

scalar exchange proxy ≠ J_flux

phase synchronization ≠ phase coherence

phase-amplitude proxy ≠ full endogenous structural coherence

amplitude proxy ≠ manifested mass M(t)

amplitude-regime decay ≠ manifested mass decay

dynamic retention ≠ frozen state

propagation delay ≠ automatic stabilizing influence

vortex contribution ≠ automatic stabilization

local vortex moment ≠ strict rot J

delayed local phase order ≠ full phase coherence

delay field ≠ J_flux

retarded phase states ≠ downstream EDK interface, mass and exchange-flow quantities

GPU acceleration ≠ change of model meaning

O(N) mean-field scaling ≠ allocation of an N × N phase-difference matrix

## 10. Research Status

This repository is a conceptual-numerical and theorem-algorithmic research framework.

It is intended for:

numerical testing of EDK invariants;

modeling recursive tact-by-tact dynamics;

testing computational boundaries between R(t), C(t), T_int, M(t), J_flux and proxy parameters;

formalizing phase coherence, dynamic retention, retention-collapse and hierarchical inheritance;

preparing further EDK / EDC theorem formalization.

It must not be interpreted as a completed experimentally confirmed physical theory.

It is a working modular research architecture of the open nonlinear dissipative dynamic Continuum.

---

# ИНДЕКС МОДУЛЕЙ EN/RU

# Эндогенная Динамика Континуума (EDK)

## Индекс модулей репозитория

Данный файл задаёт навигационную карту модульного уровня для репозитория Endogenous-Dynamics-of-the-Continuum.

Он не заменяет отдельные README файлов модулей.

Он определяет репозиторий как единую вычислительную и теоремно-алгоритмическую архитектуру открытого нелинейного диссипативного динамического Континуума, где каждый модуль занимает контролируемый слой в каскаде EDK.

Репозиторий должен читаться как связанная система:

фазовые слои → Φ → фазовая когерентность → C(t) → T_int → M(t) → J_flux → биологическая / молекулярная модуляция

и в обратной цепочке:

потеря C(t) → деградация T_int → деманифестация M(t) → рост J_flux → возврат в фоновые моды Континуума

## 1. Базовый слой репозитория

### 1.1. framework_core.py

Роль:

Квантово-фазовое ядро модели.

Основное назначение:

Моделирует переход от фазовой когерентности мультиплетных слоёв к удержанию интерфейса, манифестации массового якоря и формированию потока обмена.

Основные сущности:

ContinuumSimulation

calculate_phi_operator

update_state

run_marnov_demolition

Основной смысл в EDK:

Модуль относится к базовому вычислительному слою, который связывает фазовую когерентность, Φ, C(t), T_int, M(t) и J_flux.

Контролируемые различия:

R(t) не тождественен C(t).

Фазовая синхронизация не тождественна фазовой когерентности.

J не автоматически тождественен J_flux.

### 1.2. continuum_core_engine.py

Роль:

Ранний системный каскадный оркестратор.

Основное назначение:

Связывает солнечный, планетарный, квантово-фазовый, биологический и молекулярный слои в единый рекурсивный потактовый каскад.

Основные сущности:

ContinuumCoreEngine

execute_cascade_step

trigger_marnov_collapse_cascade

Основной смысл в EDK:

Файл представляет ранний системный уровень оркестрации до введения нового иерархического оркестратора.

Контролируемые различия:

Каскадное выполнение не является заменой C(t).

Каскадное состояние не является заменой T_int.

Координация модулей не тождественна полной иерархической оркестрации EDK.

### 1.3. THEORY_TENSOR_MATRIX.md

Роль:

Теоретический слой тензорного сопряжения.

Основное назначение:

Определяет динамический интерфейсный тензор T_int и его разложение на изотропный и девиаторный компоненты.

Базовые выражения:

T_int = [ σ_xx  τ_xy  τ_xz ] [ τ_yx  σ_yy  τ_yz ] [ τ_zx  τ_zy  σ_zz ]

T_int = T_iso + T_dev = C(t) · I + τ_dev

Основной смысл в EDK:

T_int является интерфейсным тензором манифестации, сопряжения и удержания формы.

Контролируемые различия:

T_int не тождественен M(t).

R(θ) не тождественен C(t).

Тензорная матрица не заменяет полный каскад EDK.

### 1.4. phase_coupling_protocol/

Роль:

Универсальный метапротокольный слой.

Основной файл:

phase_coupling_protocol/universal_meta_protocol_EN_RU.md

Основное назначение:

Задаёт протокол репозиторного уровня для фазового сопряжения разнородных систем.

Основной смысл в EDK:

Модуль фиксирует метапротокольную цепочку фазового сопряжения, эндогенной структурной когерентности, удержания T_int, якорения M(t), обмена J_flux и обратной деманифестации.

Контролируемые различия:

J не тождественен J_flux.

C_proxy(t) не тождественен C(t).

Фазово-амплитудный прокси-параметр не является полной эндогенной структурной когерентностью.

Метапротокол не является завершённой экспериментально подтверждённой физической теорией.

## 2. Слой фазовой динамики

### 2.1. module_edk_gpu_mean_field_phase_engine/

Роль:

GPU / CPU среднеполевой движок фазовой динамики.

Основные файлы:

module_edk_gpu_mean_field_phase_engine/README_EN_RU.md

module_edk_gpu_mean_field_phase_engine/edk_gpu_mean_field_phase_engine.py

module_edk_gpu_mean_field_phase_engine/benchmark_gpu_phase_engine.py

module_edk_gpu_mean_field_phase_engine/test_gpu_mean_field_phase_engine.py

module_edk_gpu_mean_field_phase_engine/smoke_test.py

module_edk_gpu_mean_field_phase_engine/__init__.py

Основные сущности:

MeanFieldPhaseConfig

EDKGPUMeanFieldPhaseEngine

EDKGPUMeanFieldLogger

Основная вычислительная функция:

Реализует точное среднеполевое фазовое сопряжение Курамото — Сакагучи с вычислительной сложностью O(N) и без выделения матрицы фазовых разностей N × N.

Основной смысл в EDK:

Модуль вычисляет глобальные диагностические параметры фазового порядка, фазово-амплитудные прокси-величины и динамику амплитудного режима. Он предоставляет высокоплотный вычислительный слой глобальной фазовой динамики.

Основные выходы:

R_t_phase_order

global_mean_phase

phase_amplitude_order_proxy

mean_phase_velocity

phase_velocity_dispersion

mean_amplitude

amplitude_dispersion

coupling_energy_proxy

gpu_mean_field_tact_*.json

gpu_mean_field_step_*.json

gpu_mean_field_field_*.npz

Запуск:

python module_edk_gpu_mean_field_phase_engine/edk_gpu_mean_field_phase_engine.py --backend cpu

Benchmark:

python module_edk_gpu_mean_field_phase_engine/benchmark_gpu_phase_engine.py

Smoke test:

python module_edk_gpu_mean_field_phase_engine/smoke_test.py

Unit tests:

python -m unittest module_edk_gpu_mean_field_phase_engine/test_gpu_mean_field_phase_engine.py

Контролируемые различия:

R(t) не тождественен C(t).

Среднеполевой фазовый порядок не является полной эндогенной структурной когерентностью.

Фазовая синхронизация не является фазовой когерентностью.

Фазово-амплитудный прокси-параметр не является полной C(t).

Амплитудный прокси-параметр не является манифестированной массой M(t).

exchange_activity_proxy не является J_flux.

GPU-ускорение не изменяет смысл модели.

O(N) среднеполевое масштабирование не выделяет матрицу фазовых разностей N × N.

Фиксированные собственные частоты не являются потактовым стохастическим фазовым шумом.

## 3. Слой задержки и локального сопряжения

### 3.1. module_edk_spatiotemporal_phase_delay/

Роль:

Движок пространственно-временной фазовой задержки.

Основные файлы:

module_edk_spatiotemporal_phase_delay/README_EN_RU.md

module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py

module_edk_spatiotemporal_phase_delay/edk_delay_diagnostics.py

module_edk_spatiotemporal_phase_delay/test_spatiotemporal_phase_delay.py

module_edk_spatiotemporal_phase_delay/smoke_test.py

module_edk_spatiotemporal_phase_delay/__init__.py

Основные сущности:

PhaseDelayConfig

EDKSpatiotemporalPhaseDelayEngine

EDKDelayLogger

Основная вычислительная функция:

Моделирует метрическую задержку распространения между пространственно распределёнными фазовыми доменами.

Базовое выражение:

tau_ij = distance_ij / c

d theta_i / dt = omega_i + K sum_j w_ij sin(theta_j(t - tau_ij) - theta_i(t) - alpha) + F_i(t)

Основной смысл в EDK:

Модуль вводит локальное ретардированное фазовое сопряжение, задержанную реконструкцию фаз и пространственную топологию соседства.

Основные выходы:

delay_tact_*.json

delay_step_*.json

delay_field_*.npz

диагностические изображения задержки

Запуск:

python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend cpu

Диагностика:

python module_edk_spatiotemporal_phase_delay/edk_delay_diagnostics.py

Smoke test:

python module_edk_spatiotemporal_phase_delay/smoke_test.py

Unit tests:

python -m unittest module_edk_spatiotemporal_phase_delay/test_spatiotemporal_phase_delay.py

Контролируемые различия:

Мгновенное среднеполевое сопряжение не является метрически задержанным локальным сопряжением.

Задержанный локальный фазовый порядок не является полной фазовой когерентностью.

Задержка распространения не является автоматически стабилизирующим влиянием.

Диагностика поля задержки не является J_flux.

Ретардированные фазовые состояния не являются downstream EDK-величинами интерфейса, массы и потока обмена.

## 4. Слой вихревого фазового поля

### 4.1. module_edk_vortex_phase_field/

Роль:

Диагностический движок вихревого фазового поля.

Основные файлы:

module_edk_vortex_phase_field/README_EN_RU.md

module_edk_vortex_phase_field/edk_vortex_phase_field.py

module_edk_vortex_phase_field/edk_vortex_diagnostics.py

module_edk_vortex_phase_field/test_vortex_phase_field.py

module_edk_vortex_phase_field/smoke_test.py

Основные сущности:

EDKVortexPhaseFieldEngine

EDKVortexLogger

Основная вычислительная функция:

Моделирует локальную пространственную структуру фазового поля, направленный ток, дискретные вихревые диагностические параметры и асимметричные вихревые вклады.

Основной смысл в EDK:

Модуль проверяет, как пространственное скручивание и вихревая асимметрия участвуют в диагностике фазового поля, не заменяя полные величины EDK.

Основные выходы:

vortex_step_*.json

vortex_field_*.npz

positive_vortex_support

negative_vortex_penalty

interface_retention_proxy

continuum_appearance_index

Запуск:

python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend cpu

Диагностика:

python module_edk_vortex_phase_field/edk_vortex_diagnostics.py

Smoke test:

python module_edk_vortex_phase_field/smoke_test.py

Unit tests:

python -m unittest module_edk_vortex_phase_field/test_vortex_phase_field.py

Контролируемые различия:

Локальный вихревой момент не является строгим rot J.

Положительный вихревой вклад не является автоматической стабилизацией.

C_proxy(t) не является C(t).

interface_retention_proxy не является T_int.

M_proxy(t) не является M(t).

Вихревая диагностика не является полным полем J_flux.

## 5. Слой удержания и коллапса

### 5.1. module_edk_marnov_retention_collapse_protocol/

Роль:

Протокол удержания и коллапса Марнова.

Основные файлы:

module_edk_marnov_retention_collapse_protocol/README_EN_RU.md

module_edk_marnov_retention_collapse_protocol/marnov_retention_collapse_protocol.py

module_edk_marnov_retention_collapse_protocol/marnov_retention_diagnostics.py

module_edk_marnov_retention_collapse_protocol/test_marnov_retention_collapse_protocol.py

Основные сущности:

MarnovRetentionCollapseConfig

EDKMarnovRetentionCollapseProtocol

EDKMarnovProtocolLogger

Основная вычислительная функция:

Моделирует формирование фазового аттрактора, проверку удержанного режима, критическую нагрузку, задержанное разблокирование фазовых узлов, высвобождение сопряжения и распад фазового аттрактора.

Основной смысл в EDK:

Модуль задаёт контролируемый численный протокол проверки удержания и коллапса под действием внешнего паразитного давления.

Базовое условие:

P_ext >> C(t)

Цепочка коллапса:

P_ext >> C(t) → деградация T_int → деманифестация M(t) → рост J_flux → возврат в фоновые моды Континуума

Масштабирование задержки:

t_delay ~ v^(-1/3)

v = mu · P_ext

Основные выходы:

marnov_step_*.json

marnov_field_*.npz

marnov_protocol_summary.json

phase-order half-life

amplitude-regime half-life

critical exposure

retention margin

Диагностика:

python module_edk_marnov_retention_collapse_protocol/marnov_retention_diagnostics.py

Unit tests:

python -m unittest module_edk_marnov_retention_collapse_protocol/test_marnov_retention_collapse_protocol.py

Контролируемые различия:

Удержанный фазовый аттрактор не является полной материальной формой.

C_proxy(t) не является C(t).

Распад амплитудного режима не является распадом манифестированной массы.

exchange_activity_proxy не является J_flux.

Фазовая синхронизация не является фазовой когерентностью.

Динамика протокола не должна вручную принуждать диагностические величины к заранее заданному результату.

## 6. Слой иерархической оркестрации

### 6.1. module_edk_hierarchical_orchestrator/

Роль:

Иерархический оркестратор EDK.

Основные файлы:

module_edk_hierarchical_orchestrator/README_EN_RU.md

module_edk_hierarchical_orchestrator/edk_hierarchical_orchestrator.py

module_edk_hierarchical_orchestrator/hierarchical_diagnostics.py

module_edk_hierarchical_orchestrator/test_hierarchical_orchestrator.py

module_edk_hierarchical_orchestrator/smoke_test.py

module_edk_hierarchical_orchestrator/__init__.py

Основные сущности:

EDKHierarchicalOrchestrator

EDKHierarchicalState

EDKModuleRegistry

EDKForwardCascadePacket

EDKFeedbackPacket

PhiOperator

EDKHierarchicalLogger

Основная вычислительная функция:

Координирует несколько модулей EDK в единую потактовую иерархическую цепочку выполнения.

Основной смысл в EDK:

Модуль сохраняет непрерывность T_int, непрерывность J_flux, рекурсивное обновление Φ, наследуемое состояние такта и field provenance между стадиями модулей.

Основные выходы:

hierarchical_step_*.json

hierarchical_field_*.npz

иерархические диагностические отчёты

Запуск:

python module_edk_hierarchical_orchestrator/edk_hierarchical_orchestrator.py

Диагностика:

python module_edk_hierarchical_orchestrator/hierarchical_diagnostics.py

Smoke test:

python module_edk_hierarchical_orchestrator/smoke_test.py

Unit tests:

python -m unittest module_edk_hierarchical_orchestrator/test_hierarchical_orchestrator.py

Контролируемые различия:

C(t) не является C_proxy(t).

C(t) не является C3.

T_int не является M(t).

J_flux не является J_vector.

Скалярный прокси обмена не является J_flux.

Иерархическая оркестрация не является заменой исходных величин EDK.

Реестр модулей не является физической моделью сам по себе.

## 7. Макро-, планетарный, биологический и молекулярный слои

### 7.1. module_solar_synthesis/

Роль:

Макроскопический слой солнечного синтеза.

Основной файл:

module_solar_synthesis/solar_synthesis_resonator.py

Основная сущность:

SolarSynthesisResonator

Основная вычислительная функция:

Моделирует Солнце как макроскопический фазовый узел, удержанный в фазе синтеза.

Основной смысл в EDK:

Амплитудный слой плазмы может оставаться хаотичным, тогда как фазовый слой может удерживать высокий уровень эндогенной когерентности.

Запуск:

python module_solar_synthesis/solar_synthesis_resonator.py

Контролируемые различия:

Хаотичный амплитудный слой не является автоматической потерей фазовой когерентности.

Слой солнечного синтеза не является всем каскадом EDK.

macro_light_flux не является автоматически J_flux.

### 7.2. module_planetary_resonance/

Роль:

Планетарный резонансный слой.

Основной файл:

module_planetary_resonance/schumann_planetary_resonator.py

Основная сущность:

SchumannPlanetaryResonator

Основная вычислительная функция:

Рассчитывает планетарное воздействие и моделирует моды Шумана как глобальное планетарное тактовое поле.

Основной смысл в EDK:

Планетарный резонанс модулирует биологическое фазовое согласование, DNA-биофотонную динамику и молекулярную фазовую химию.

Запуск:

python module_planetary_resonance/schumann_planetary_resonator.py

Контролируемые различия:

Планетарное воздействие не является полной C(t).

Модуляция мод Шумана не является прямым доказательством биологической фазовой когерентности.

Планетарное тактовое поле не является всем Континуумом.

### 7.3. module_wave_genetics/

Роль:

Биологический волновой слой.

Основной файл:

module_wave_genetics/wave_genetics_dna_oscillator.py

Основная сущность:

WaveGeneticsDNAOscillator

Основная вычислительная функция:

Преобразует J_flux в модулированный биофотонный сигнал и остаточный фантомный след внутри численной модели.

Основной смысл в EDK:

DNA представлена как поляризованная биофотонная лазерно-интерферометрическая структура внутри модели.

Запуск:

python module_wave_genetics/wave_genetics_dna_oscillator.py

Контролируемые различия:

Биофотонная модуляция не является полным J_flux.

Фантомный след не является полной материальной формой.

Биологическое фазовое согласование не является полной эндогенной структурной когерентностью.

### 7.4. module_molecular_chemistry/

Роль:

Молекулярный слой фазовой химии.

Основной файл:

module_molecular_chemistry/molecular_phase_chemistry.py

Основная сущность:

MolecularPhaseChemistry

Основная вычислительная функция:

Моделирует химические связи как устойчивые фазовые отношения между атомарными или молекулярными осцилляторами.

Основной смысл в EDK:

Химическая связь рассматривается как фазовое отношение, поддержанное памятью среды, биофотонным forcing и достаточной молекулярной когерентностью.

Запуск:

python module_molecular_chemistry/molecular_phase_chemistry.py

Контролируемые различия:

Молекулярная когерентность не является полной C(t).

Деманифестация химической связи не является автоматически полной деманифестацией M(t).

Биофотонное forcing не является самим J_flux.

## 8. Карта запуска

Рекомендуемый базовый порядок выполнения:

1. Запустить unit tests вычислительных модулей.

2. Запустить smoke tests для каждого активного модуля.

3. Запускать диагностику только после появления валидных snapshots.

4. Запускать иерархический оркестратор после прохождения smoke tests отдельных модулей.

Базовые команды:

python -m unittest module_edk_gpu_mean_field_phase_engine/test_gpu_mean_field_phase_engine.py

python module_edk_gpu_mean_field_phase_engine/smoke_test.py

python -m unittest module_edk_spatiotemporal_phase_delay/test_spatiotemporal_phase_delay.py

python module_edk_spatiotemporal_phase_delay/smoke_test.py

python -m unittest module_edk_vortex_phase_field/test_vortex_phase_field.py

python module_edk_vortex_phase_field/smoke_test.py

python -m unittest module_edk_marnov_retention_collapse_protocol/test_marnov_retention_collapse_protocol.py

python -m unittest module_edk_hierarchical_orchestrator/test_hierarchical_orchestrator.py

python module_edk_hierarchical_orchestrator/smoke_test.py

## 9. Контролируемые различия уровня репозитория

Следующие различия должны сохраняться во всех модулях и документации:

R(t) ≠ C(t)

C_proxy(t) ≠ C(t)

C(t) ≠ C3

T_int ≠ M(t)

J ≠ J_flux

J_vector ≠ J_flux

macro_light_flux ≠ J_flux

exchange_activity_proxy ≠ J_flux

скалярный прокси обмена ≠ J_flux

фазовая синхронизация ≠ фазовая когерентность

фазово-амплитудный прокси-параметр ≠ полная эндогенная структурная когерентность

амплитудный прокси-параметр ≠ манифестированная масса M(t)

распад амплитудного режима ≠ распад манифестированной массы

динамическое удержание ≠ замороженное состояние

задержка распространения ≠ автоматическое стабилизирующее влияние

вихревой вклад ≠ автоматическая стабилизация

локальный вихревой момент ≠ строгий rot J

задержанный локальный фазовый порядок ≠ полная фазовая когерентность

поле задержки ≠ J_flux

ретардированные фазовые состояния ≠ downstream EDK-величины интерфейса, массы и потока обмена

GPU-ускорение ≠ изменение смысла модели

O(N) среднеполевое масштабирование ≠ выделение матрицы фазовых разностей N × N

## 10. Исследовательский статус

Данный репозиторий является концептуально-численным и теоремно-алгоритмическим исследовательским каркасом.

Он предназначен для:

численного тестирования инвариантов EDK;

моделирования рекурсивной потактовой динамики;

проверки вычислительных границ между R(t), C(t), T_int, M(t), J_flux и прокси-параметрами;

формализации фазовой когерентности, динамического удержания, удержания-коллапса и иерархического наследования;

подготовки дальнейшей формализации теорем EDK / EDC.

Он не должен трактоваться как завершённая экспериментально подтверждённая физическая теория.

Он является рабочей модульной исследовательской архитектурой открытого нелинейного диссипативного динамического Континуума.
