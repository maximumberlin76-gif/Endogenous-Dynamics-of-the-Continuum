# EDK GPU Mean-Field Phase Engine

High-density GPU-accelerated global phase-dynamics engine for the EDK computational architecture.

The module implements exact mean-field Kuramoto–Sakaguchi coupling with linear computational complexity relative to the number of phase domains.

The engine is intended for simulations containing tens of thousands, hundreds of thousands, or potentially millions of globally coupled phase domains without constructing an N × N phase-difference matrix.

## Repository Location

    module_edk_gpu_mean_field_phase_engine/

## Module Structure

    module_edk_gpu_mean_field_phase_engine/
    ├── README_EN_RU.md
    ├── edk_gpu_mean_field_phase_engine.py
    ├── benchmark_gpu_phase_engine.py
    ├── smoke_test.py
    └── __init__.py

## Main Class

    EDKGPUMeanFieldPhaseEngine

## Computational Purpose

The module provides a high-density computational layer for global mean-field phase dynamics.

Its primary responsibilities are:

- initialization of phase-domain states;
- initialization of fixed natural frequencies;
- initialization and evolution of domain amplitudes;
- calculation of the global complex phase-order parameter;
- extraction of R(t) and Psi(t);
- exact O(N) mean-field coupling;
- optional external phase forcing;
- optional stochastic phase perturbation;
- stochastic amplitude relaxation;
- GPU execution through CuPy;
- automatic NumPy fallback when a compatible CUDA environment is unavailable;
- compact scalar diagnostics;
- controlled export of full field snapshots.

The module does not independently calculate manifested mass M(t), retained interface T_int, general endogenous structural coherence C(t), or the full exchange-flow field J_flux.

Those quantities belong to downstream EDK layers that combine phase dynamics with spatial topology, amplitude structure, retained-interface dynamics, environmental pressure, vortex exchange, and recursive inheritance.

## Mathematical Core

For N globally coupled phase domains, the complex phase-order parameter is:

    Z(t) = 1 / N sum_j exp(i theta_j)

with:

    Z(t) = R(t) exp(i Psi(t))

where:

- R(t) is the global phase-order parameter;
- Psi(t) is the global mean phase;
- theta_j is the phase of domain j.

The exact Kuramoto mean-field identity is:

    K / N sum_j sin(theta_j - theta_i)
    =
    K R(t) sin(Psi(t) - theta_i)

For Kuramoto–Sakaguchi coupling with phase lag alpha:

    K / N sum_j sin(theta_j - theta_i - alpha)
    =
    K R(t) sin(Psi(t) - theta_i - alpha)

The phase evolution law used by the engine is:

    d theta_i / dt
    =
    omega_i
    + K R(t) sin(Psi(t) - theta_i - alpha)
    + F_ext sin(Psi_ext - theta_i)
    + phase_noise_i

where:

- omega_i is the fixed natural frequency of domain i;
- K is the global coupling strength;
- alpha is the Sakaguchi phase lag;
- F_ext is the external forcing density;
- Psi_ext is the external forcing phase;
- phase_noise_i is an optional stochastic phase perturbation.

The exact mean-field transformation removes the need to construct the full N × N pairwise phase-difference matrix.

## Computational Complexity

The original pairwise implementation requires:

    memory complexity: O(N²)
    computational complexity: O(N²)

The mean-field implementation requires:

    memory complexity: O(N)
    computational complexity: O(N)

For N = 100000, the module stores vectors of length N instead of matrices containing ten billion pairwise elements.

This is the central scaling mechanism of the module.

## Phase and Amplitude Distinction

The module explicitly distinguishes:

    R(t) ≠ C(t)

R(t) measures global phase synchronization.

R(t) does not represent full phase coherence because it does not independently verify amplitude consistency.

R(t) also does not represent general endogenous structural coherence C(t), which belongs to the complete EDK system state.

The module may calculate a separate phase-amplitude diagnostic proxy, but that proxy must not be identified with C(t) without additional structural and environmental variables.

## Natural Frequencies

Natural frequencies are generated once during engine initialization and remain fixed during the simulation unless an explicit reconfiguration operation is requested.

They are stored as:

    natural_frequencies

Random values must not be regenerated as natural frequencies on every tact.

Optional tact-by-tact stochastic forcing is represented separately through a dedicated phase-noise parameter.

## Amplitude Dynamics

Amplitude evolution is treated as a stochastic nonlinear relaxation model.

A minimal operational form is:

    dA_i
    =
    amplitude_relaxation(A_i) dt
    + amplitude_noise_strength dW_i

The default relaxation term may be represented as:

    amplitude_relaxation(A_i)
    =
    amplitude_growth_rate A_i
    - amplitude_saturation_rate A_i³

The amplitude equation is a numerical nonlinear relaxation model.

It must not be described as a complete Navier–Stokes plasma model because it does not independently contain spatial fluid velocity, convective transport, pressure gradients, viscosity, or magnetohydrodynamic field equations.

## GPU Backend

The preferred backend is CuPy with a compatible NVIDIA CUDA environment.

Backend selection modes:

    auto
    gpu
    cpu

In automatic mode, the engine:

1. attempts to import CuPy;
2. checks whether at least one CUDA device is available;
3. selects the configured device_id;
4. initializes GPU arrays and a backend-specific random-number generator;
5. falls back to NumPy when GPU initialization is unavailable.

A successful CuPy import alone is not treated as proof that a usable CUDA device exists.

## Device Selection

The GPU device is selected through:

    device_id

The engine must not hard-code device 0 without allowing configuration.

Example configuration:

    device_id = 0

## Numerical Precision

Supported floating-point modes may include:

    float32
    float64

The selected dtype controls:

- phase arrays;
- amplitude arrays;
- natural-frequency arrays;
- temporary backend arrays;
- exported field snapshots.

Complex order-parameter calculations use the corresponding backend-compatible complex precision.

## Random-Number Generation

The module uses a local random-number generator associated with the active backend.

The module must not modify the global NumPy or CuPy random state.

The same seed is used to support repeatable initialization within the limits of backend-specific floating-point execution.

## Operational Chain

    fixed natural frequencies
    ↓
    phase-domain initialization
    ↓
    amplitude-domain initialization
    ↓
    calculation of Z(t)
    ↓
    extraction of R(t) and Psi(t)
    ↓
    exact O(N) mean-field coupling
    ↓
    external phase forcing
    ↓
    optional stochastic phase perturbation
    ↓
    tact-by-tact phase update
    ↓
    nonlinear amplitude relaxation
    ↓
    recalculation of phase and amplitude diagnostics
    ↓
    compact metric export
    ↓
    controlled field-snapshot export
    ↓
    transfer to downstream EDK modules

## Core Configuration

The engine configuration is expected to include:

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

## Core State Arrays

The engine retains:

    phases
    amplitudes
    natural_frequencies
    phase_velocity

Optional diagnostic arrays may include:

    phase_noise
    amplitude_velocity
    phase_alignment
    amplitude_alignment

## Core Scalar Diagnostics

The engine calculates compact scalar metrics such as:

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
    external_forcing_density
    active_domains
    backend_name
    device_id
    simulation_time
    tact_index

## Coupling-Energy Proxy

A bounded mean-field coupling diagnostic may be calculated as:

    coupling_energy_proxy
    =
    mean cos(Psi(t) - theta_i - alpha)

This value is a diagnostic proxy of global phase alignment.

It is not identified with the full physical energy of the plasma system.

## External Forcing

External forcing is represented separately from endogenous global coupling.

The forcing contribution is:

    F_ext sin(Psi_ext - theta_i)

where:

- F_ext controls forcing density;
- Psi_ext controls forcing phase.

Removal of forcing does not automatically imply instantaneous destruction of the phase attractor.

The subsequent evolution depends on:

- current R(t);
- current amplitude structure;
- coupling strength K;
- natural-frequency dispersion;
- phase lag alpha;
- phase noise;
- amplitude noise;
- inherited phase-domain configuration.

## Interruption Experiment

A forcing-interruption experiment must compare the system before and after a controlled parameter change.

The experiment may alter:

    coupling_strength_k
    external_forcing_density
    external_forcing_phase
    phase_noise_strength
    amplitude_noise_strength

The experiment records:

    R(t)
    global mean phase
    phase-amplitude order proxy
    mean phase velocity
    phase-velocity dispersion
    amplitude dispersion
    coupling-energy proxy
    attractor decay time
    phase-order half-life

The result must be derived from the tact-by-tact dynamics.

No diagnostic value is manually forced toward a predetermined outcome.

## Relationship to Other EDK Modules

### EDK GPU Mean-Field Phase Engine

Provides:

    global high-density phase dynamics
    exact O(N) mean-field coupling
    GPU-accelerated vector evolution

### EDK Spatiotemporal Phase-Delay Module

Provides:

    spatial neighbor topology
    propagation delay tau_ij
    delayed phase reconstruction
    local retarded coupling

Its typical complexity is:

    O(N k)

where k is the number of neighbors per domain.

### EDK Vortex Phase-Field Module

Provides:

    spatial exchange-flow topology
    directional current
    discrete curl
    vortex diagnostics
    local spatial phase-field structure

Its typical complexity is:

    O(N k)

The three modules represent different computational layers and must not be treated as interchangeable.

## J_flux Boundary

The GPU mean-field module does not independently reconstruct the full J_flux field.

A scalar phase-activity or exchange-activity diagnostic may be exported, but it must not be renamed J_flux.

The full J_flux field requires spatial direction, exchange topology, temporal evolution, and coupling with the retained interface and background modes of the Continuum.

## C(t) Boundary

The module does not identify R(t) with C(t).

General endogenous structural coherence C(t) must be calculated by a higher EDK integration layer using the required structural variables.

Possible inputs include:

    global phase order
    local phase order
    amplitude consistency
    phase-velocity dispersion
    retained-interface state
    spatial exchange-flow state
    environmental pressure
    dissipation
    recursive inheritance

## M(t) and T_int Boundary

The engine does not instantaneously generate manifested mass M(t) from a phase-order threshold.

The engine does not replace T_int with a scaled identity matrix.

M(t) and T_int belong to downstream dynamic-retention layers and must be calculated through explicit tact-by-tact laws.

## Logging Strategy

Compact scalar metrics are written at a configurable interval:

    log_every

Full field snapshots are written less frequently:

    field_every

Recommended format:

    JSON
    → scalar metrics and metadata

    NPZ
    → phase, amplitude, natural-frequency, and phase-velocity arrays

Full phase and amplitude vectors must not be converted to JSON lists at every tact.

## Atomic File Writing

Metric snapshots should be written atomically:

    temporary file
    ↓
    flush
    ↓
    fsync
    ↓
    os.replace
    ↓
    final file

This reduces the risk of incomplete snapshots after an interrupted process.

## Benchmarking

CUDA execution is asynchronous relative to the host process.

GPU timing must therefore use:

    CUDA events

or:

    cupyx.profiler.benchmark

A plain host-side timer without synchronization does not measure the complete GPU execution time.

Benchmark results must distinguish:

    kernel execution time
    host-to-device transfer time
    device-to-host transfer time
    metric serialization time
    full snapshot export time

## Memory Monitoring

The benchmark module may report:

    active device
    total device memory
    used device memory
    free device memory
    CuPy memory-pool usage
    NumPy host-memory estimate
    bytes per domain
    estimated maximum domain count

The benchmark must not claim unlimited or seamless scaling without checking available memory and the selected dtype.

## Installation

Base CPU dependency:

    numpy

Optional GPU dependency depends on the installed CUDA generation.

Examples may include:

    cupy-cuda12x
    cupy-cuda13x

The GPU package should not be placed as an unconditional dependency in the common repository requirements file.

GPU installation instructions must be documented separately according to the target CUDA environment.

## Basic Execution

CPU fallback:

    python edk_gpu_mean_field_phase_engine.py --backend cpu

Automatic backend selection:

    python edk_gpu_mean_field_phase_engine.py --backend auto

Explicit GPU execution:

    python edk_gpu_mean_field_phase_engine.py --backend gpu --device-id 0

Benchmark:

    python benchmark_gpu_phase_engine.py

Smoke test:

    python smoke_test.py

## Smoke-Test Requirements

The smoke test must verify:

- successful CPU initialization;
- successful automatic backend selection;
- valid phase wrapping within the configured phase interval;
- fixed natural frequencies across multiple tacts;
- finite phase and amplitude arrays;
- finite scalar diagnostics;
- R(t) within the interval from 0 to 1;
- valid mean phase;
- non-negative dispersions;
- deterministic initialization for a fixed seed;
- O(N) state-array dimensions;
- absence of an N × N phase-difference allocation;
- successful compact JSON export;
- successful NPZ field export;
- graceful GPU fallback when CUDA is unavailable.

When a compatible CUDA environment is present, the smoke test may additionally verify GPU execution and field transfer.

## Research Status

This module is a numerical research component of the EDK computational architecture.

It models global phase-domain dynamics and nonlinear amplitude relaxation.

## License

The module inherits the license of the parent EDK repository.

---

# EDK GPU-ДВИЖОК СРЕДНЕПОЛЕВОЙ ФАЗОВОЙ ДИНАМИКИ

Высокоплотный GPU-ускоренный движок глобальной фазовой динамики для вычислительной архитектуры EDK.

Модуль реализует точное среднеполевое сопряжение Курамото — Сакагучи с линейной вычислительной сложностью относительно числа фазовых доменов.

Движок предназначен для моделирования десятков тысяч, сотен тысяч и потенциально миллионов глобально сопряжённых фазовых доменов без построения матрицы разностей фаз размерности N × N.

## Расположение в репозитории

    module_edk_gpu_mean_field_phase_engine/

## Структура модуля

    module_edk_gpu_mean_field_phase_engine/
    ├── README_EN_RU.md
    ├── edk_gpu_mean_field_phase_engine.py
    ├── benchmark_gpu_phase_engine.py
    ├── smoke_test.py
    └── __init__.py

## Основной класс

    EDKGPUMeanFieldPhaseEngine

## Вычислительное назначение

Модуль предоставляет высокоплотный вычислительный слой глобальной среднеполевой фазовой динамики.

Основные функции модуля:

- инициализация состояний фазовых доменов;
- инициализация фиксированных естественных частот;
- инициализация и эволюция амплитуд доменов;
- вычисление глобального комплексного параметра фазового порядка;
- выделение R(t) и Psi(t);
- точное среднеполевое сопряжение O(N);
- дополнительный внешний фазовый форсинг;
- дополнительное стохастическое фазовое возмущение;
- стохастическая амплитудная релаксация;
- исполнение на GPU через CuPy;
- автоматический переход на NumPy при отсутствии совместимой среды CUDA;
- компактная скалярная диагностика;
- контролируемый экспорт полных снимков полей.

Модуль не вычисляет самостоятельно проявленную массу M(t), удерживаемый интерфейс T_int, общую эндогенную структурную когерентность C(t) или полное поле сквозного потока обмена J_flux.

Эти параметры относятся к последующим слоям EDK, объединяющим фазовую динамику с пространственной топологией, амплитудной структурой, динамикой удерживаемого интерфейса, давлением среды, вихревым обменом и рекурсивным наследованием.

## Математическое ядро

Для N глобально сопряжённых фазовых доменов комплексный параметр фазового порядка определяется как:

    Z(t) = 1 / N sum_j exp(i theta_j)

при этом:

    Z(t) = R(t) exp(i Psi(t))

где:

- R(t) — глобальный параметр фазового порядка;
- Psi(t) — глобальная средняя фаза;
- theta_j — фаза домена j.

Точное среднеполевое тождество Курамото:

    K / N sum_j sin(theta_j - theta_i)
    =
    K R(t) sin(Psi(t) - theta_i)

Для сопряжения Курамото — Сакагучи с фазовым сдвигом alpha:

    K / N sum_j sin(theta_j - theta_i - alpha)
    =
    K R(t) sin(Psi(t) - theta_i - alpha)

Используемый движком закон эволюции фаз:

    d theta_i / dt
    =
    omega_i
    + K R(t) sin(Psi(t) - theta_i - alpha)
    + F_ext sin(Psi_ext - theta_i)
    + phase_noise_i

где:

- omega_i — фиксированная естественная частота домена i;
- K — глобальная константа сопряжения;
- alpha — фазовый сдвиг Сакагучи;
- F_ext — плотность внешнего форсинга;
- Psi_ext — фаза внешнего форсинга;
- phase_noise_i — дополнительное стохастическое фазовое возмущение.

Точное среднеполевое преобразование устраняет необходимость построения полной матрицы попарных разностей фаз N × N.

## Вычислительная сложность

Исходная попарная реализация требует:

    сложность памяти: O(N²)
    вычислительная сложность: O(N²)

Среднеполевая реализация требует:

    сложность памяти: O(N)
    вычислительная сложность: O(N)

При N = 100000 модуль хранит векторы длины N вместо матриц, содержащих десять миллиардов попарных элементов.

Это является центральным механизмом масштабирования модуля.

## Различие фазы и амплитуды

Модуль явно различает:

    R(t) ≠ C(t)

R(t) измеряет глобальную фазовую синхронизацию.

R(t) не является полной фазовой когерентностью, поскольку отдельно не проверяет согласованность амплитуд.

R(t) также не является общей эндогенной структурной когерентностью C(t), которая относится к полному состоянию системы EDK.

Модуль может рассчитывать отдельный диагностический фазово-амплитудный прокси-параметр, но этот прокси-параметр не должен отождествляться с C(t) без дополнительных структурных параметров и параметров среды.

## Естественные частоты

Естественные частоты генерируются один раз при инициализации движка и остаются фиксированными в течение симуляции, если не вызвана явная операция реконфигурации.

Они хранятся как:

    natural_frequencies

Случайные значения не должны заново генерироваться как естественные частоты на каждом такте.

Дополнительное потактовое стохастическое воздействие представляется отдельно через специальный параметр фазового шума.

## Амплитудная динамика

Эволюция амплитуд рассматривается как стохастическая нелинейная релаксационная модель.

Минимальная операционная форма:

    dA_i
    =
    amplitude_relaxation(A_i) dt
    + amplitude_noise_strength dW_i

Стандартный релаксационный член может быть представлен как:

    amplitude_relaxation(A_i)
    =
    amplitude_growth_rate A_i
    - amplitude_saturation_rate A_i³

Амплитудное уравнение является численной нелинейной релаксационной моделью.

Оно не должно описываться как полная плазменная модель Навье — Стокса, поскольку самостоятельно не содержит пространственного поля скорости, конвективного переноса, градиентов давления, вязкости или магнитогидродинамических полевых уравнений.

## GPU-бэкенд

Предпочтительным бэкендом является CuPy в совместимой среде NVIDIA CUDA.

Режимы выбора бэкенда:

    auto
    gpu
    cpu

В автоматическом режиме движок:

1. пытается импортировать CuPy;
2. проверяет наличие как минимум одного доступного устройства CUDA;
3. выбирает настроенный device_id;
4. инициализирует GPU-массивы и специализированный генератор случайных чисел;
5. переходит на NumPy, если GPU-инициализация недоступна.

Успешный импорт CuPy сам по себе не рассматривается как доказательство наличия рабочего устройства CUDA.

## Выбор устройства

Устройство GPU выбирается через:

    device_id

Движок не должен жёстко фиксировать устройство 0 без возможности настройки.

Пример конфигурации:

    device_id = 0

## Численная точность

Поддерживаемые режимы численной точности могут включать:

    float32
    float64

Выбранный dtype определяет:

- массивы фаз;
- массивы амплитуд;
- массивы естественных частот;
- временные массивы бэкенда;
- экспортируемые снимки полей.

Расчёт комплексного параметра порядка использует соответствующую комплексную точность активного бэкенда.

## Генерация случайных чисел

Модуль использует локальный генератор случайных чисел активного бэкенда.

Модуль не должен изменять глобальное случайное состояние NumPy или CuPy.

Один и тот же seed используется для воспроизводимой инициализации в пределах различий исполнения операций с плавающей точкой на разных бэкендах.

## Операционная цепочка

    фиксированные естественные частоты
    ↓
    инициализация фазовых доменов
    ↓
    инициализация амплитудных доменов
    ↓
    вычисление Z(t)
    ↓
    выделение R(t) и Psi(t)
    ↓
    точное среднеполевое сопряжение O(N)
    ↓
    внешний фазовый форсинг
    ↓
    дополнительное стохастическое фазовое возмущение
    ↓
    потактовое обновление фаз
    ↓
    нелинейная амплитудная релаксация
    ↓
    повторный расчёт фазовых и амплитудных диагностических параметров
    ↓
    экспорт компактных метрик
    ↓
    контролируемый экспорт снимков полей
    ↓
    передача состояния в последующие модули EDK

## Основная конфигурация

Конфигурация движка должна включать:

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

## Основные массивы состояния

Движок удерживает:

    phases
    amplitudes
    natural_frequencies
    phase_velocity

Дополнительные диагностические массивы могут включать:

    phase_noise
    amplitude_velocity
    phase_alignment
    amplitude_alignment

## Основные скалярные диагностические параметры

Движок рассчитывает компактные скалярные метрики:

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
    external_forcing_density
    active_domains
    backend_name
    device_id
    simulation_time
    tact_index

## Прокси-параметр энергии сопряжения

Ограниченный диагностический параметр среднеполевого сопряжения может рассчитываться как:

    coupling_energy_proxy
    =
    mean cos(Psi(t) - theta_i - alpha)

Эта величина является диагностическим прокси-параметром глобального фазового согласования.

Она не отождествляется с полной физической энергией плазменной системы.

## Внешний форсинг

Внешний форсинг представляется отдельно от эндогенного глобального сопряжения.

Вклад форсинга:

    F_ext sin(Psi_ext - theta_i)

где:

- F_ext определяет плотность форсинга;
- Psi_ext определяет фазу форсинга.

Снятие форсинга не означает автоматического мгновенного разрушения фазового аттрактора.

Последующая эволюция зависит от:

- текущего R(t);
- текущей амплитудной структуры;
- константы сопряжения K;
- дисперсии естественных частот;
- фазового сдвига alpha;
- фазового шума;
- амплитудного шума;
- унаследованной конфигурации фазовых доменов.

## Эксперимент прерывания

Эксперимент прерывания форсинга должен сравнивать систему до и после контролируемого изменения параметров.

Эксперимент может изменять:

    coupling_strength_k
    external_forcing_density
    external_forcing_phase
    phase_noise_strength
    amplitude_noise_strength

В эксперименте регистрируются:

    R(t)
    глобальная средняя фаза
    фазово-амплитудный прокси-параметр
    средняя фазовая скорость
    дисперсия фазовых скоростей
    дисперсия амплитуд
    прокси-параметр энергии сопряжения
    время распада аттрактора
    период полураспада фазового порядка

Результат должен выводиться из потактовой динамики.

Ни одно диагностическое значение не должно вручную принудительно направляться к заранее заданному исходу.

## Связь с другими модулями EDK

### EDK GPU-движок среднеполевой фазовой динамики

Предоставляет:

    глобальную высокоплотную фазовую динамику
    точное среднеполевое сопряжение O(N)
    GPU-ускоренную векторную эволюцию

### Модуль пространственно-временной фазовой задержки EDK

Предоставляет:

    пространственную топологию соседства
    задержку распространения tau_ij
    реконструкцию задержанных фаз
    локальное ретардированное сопряжение

Его типичная вычислительная сложность:

    O(N k)

где k — число соседей одного домена.

### Модуль вихревого фазового поля EDK

Предоставляет:

    пространственную топологию потока обмена
    направленный ток
    дискретный ротор
    вихревую диагностику
    локальную пространственную структуру фазового поля

Его типичная вычислительная сложность:

    O(N k)

Три модуля представляют различные вычислительные слои и не должны рассматриваться как взаимозаменяемые.

## Граница J_flux

GPU-среднеполевой модуль не восстанавливает самостоятельно полное поле J_flux.

Скалярный диагностический параметр фазовой активности или активности обмена может экспортироваться, но он не должен переименовываться в J_flux.

Полное поле J_flux требует пространственного направления, топологии обмена, временной эволюции и сопряжения с удерживаемым интерфейсом и фоновыми модами Континуума.

## Граница C(t)

Модуль не отождествляет R(t) с C(t).

Общая эндогенная структурная когерентность C(t) должна рассчитываться интеграционным слоем EDK с использованием необходимых структурных параметров.

Возможные входные параметры:

    глобальный фазовый порядок
    локальный фазовый порядок
    согласованность амплитуд
    дисперсия фазовых скоростей
    состояние удерживаемого интерфейса
    состояние пространственного потока обмена
    давление среды
    диссипация
    рекурсивное наследование

## Граница M(t) и T_int

Движок не порождает мгновенно проявленную массу M(t) на основании одного порога фазового порядка.

Движок не заменяет T_int масштабированной единичной матрицей.

M(t) и T_int относятся к последующим слоям динамического удержания и должны рассчитываться через явные потактовые законы.

## Стратегия логирования

Компактные скалярные метрики записываются через настраиваемый интервал:

    log_every

Полные снимки полей записываются реже:

    field_every

Рекомендуемый формат:

    JSON
    → скалярные метрики и метаданные

    NPZ
    → массивы фаз, амплитуд, естественных частот и фазовых скоростей

Полные векторы фаз и амплитуд не должны преобразовываться в списки JSON на каждом такте.

## Атомарная запись файлов

Снимки метрик должны записываться атомарно:

    временный файл
    ↓
    flush
    ↓
    fsync
    ↓
    os.replace
    ↓
    конечный файл

Это снижает риск появления неполных снимков после прерывания процесса.

## Измерение производительности

Исполнение CUDA асинхронно относительно процесса хоста.

Поэтому для измерения времени GPU необходимо использовать:

    события CUDA

или:

    cupyx.profiler.benchmark

Обычный таймер процесса хоста без синхронизации не измеряет полное время исполнения GPU.

Результаты теста должны отдельно учитывать:

    время исполнения вычислительного ядра
    время передачи данных с хоста на устройство
    время передачи данных с устройства на хост
    время сериализации метрик
    время экспорта полного снимка полей

## Контроль памяти

Модуль измерения производительности может регистрировать:

    активное устройство
    общий объём памяти устройства
    используемую память устройства
    свободную память устройства
    использование пула памяти CuPy
    оценку использования памяти хоста NumPy
    число байтов на один домен
    оценочное максимальное число доменов

Тест производительности не должен заявлять неограниченное или бесшовное масштабирование без проверки доступной памяти и выбранного dtype.

## Установка

Базовая зависимость CPU:

    numpy

Дополнительная GPU-зависимость определяется установленным поколением CUDA.

Возможные примеры:

    cupy-cuda12x
    cupy-cuda13x

GPU-пакет не должен добавляться как безусловная зависимость в общий файл requirements репозитория.

Инструкции установки GPU должны задаваться отдельно в соответствии с целевой средой CUDA.

## Базовый запуск

Запуск с CPU:

    python edk_gpu_mean_field_phase_engine.py --backend cpu

Автоматический выбор бэкенда:

    python edk_gpu_mean_field_phase_engine.py --backend auto

Явный запуск на GPU:

    python edk_gpu_mean_field_phase_engine.py --backend gpu --device-id 0

Тест производительности:

    python benchmark_gpu_phase_engine.py

Дымовой тест:

    python smoke_test.py

## Требования дымового теста

Дымовой тест должен проверять:

- успешную инициализацию CPU;
- успешный автоматический выбор бэкенда;
- корректное сворачивание фаз в настроенный фазовый интервал;
- неизменность естественных частот на протяжении нескольких тактов;
- конечность массивов фаз и амплитуд;
- конечность скалярных диагностических параметров;
- нахождение R(t) в диапазоне от 0 до 1;
- корректность глобальной средней фазы;
- неотрицательность дисперсий;
- воспроизводимость инициализации при фиксированном seed;
- размерности массивов состояния O(N);
- отсутствие выделения матрицы разностей фаз N × N;
- успешный экспорт компактного JSON;
- успешный экспорт полей NPZ;
- корректный переход на CPU при отсутствии CUDA.

При наличии совместимой среды CUDA дымовой тест может дополнительно проверять GPU-исполнение и передачу полей.

## Исследовательский статус

Этот модуль является численным исследовательским компонентом вычислительной архитектуры EDK.

Он моделирует глобальную динамику фазовых доменов и нелинейную амплитудную релаксацию.

## Лицензия

Модуль наследует лицензию родительского репозитория EDK.
