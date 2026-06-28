# EDK Spatiotemporal Phase Delay

## EN

## Purpose

This module introduces metric spatiotemporal propagation delay of phase signals into the numerical EDK architecture.

The module implements a spatially distributed Kuramoto-Sakaguchi system with propagation retardation. The phase state of a neighboring domain `j` is read by domain `i` through a reconstructed preceding state corresponding to the metric propagation delay:

`tau_ij = distance_ij / c`

The module preserves the following controlled distinctions:

`instantaneous phase coupling ≠ metric retarded phase coupling`

`phase synchronization ≠ phase coherence`

`R(t) ≠ full C(t)`

`propagation delay ≠ automatically stabilizing influence`

The module calculates retarded phase interaction as an independent base layer that can be used by the vortex phase-field module and other EDK modules.

## Folder Structure

`module_edk_spatiotemporal_phase_delay/`

`├── README_EN_RU.md`

`├── edk_spatiotemporal_phase_delay.py`

`├── edk_delay_diagnostics.py`

`├── smoke_test.py`

`└── __init__.py`

Generated simulation data:

`edk_delay_snapshots/`

Recommended `.gitignore` entries:

`edk_delay_snapshots/`

`edk_delay_diagnostics.png`

`__pycache__/`

## External Dependencies

Required:

`Python >= 3.10`

`numpy >= 1.26.0`

`matplotlib >= 3.8.0`

Optional GPU backend:

`CuPy compatible with the installed CUDA environment`

The CuPy package is selected according to the active CUDA version.

Example for CUDA 12:

`pip install cupy-cuda12x`

The installed CuPy package must match the local CUDA environment.

## Spatial Geometry of Domains

Each phase domain receives a fixed three-dimensional coordinate:

`x_i = (x_i, y_i, z_i)`

Spatial displacement between domain `i` and neighboring domain `j`:

`delta_x_ij = x_j - x_i`

Metric distance:

`d_ij = |delta_x_ij|`

Propagation delay:

`tau_ij = d_ij / c`

where:

- `d_ij` is the metric distance between two spatial domains;
- `c` is the model parameter of phase-signal propagation through the simulated medium;
- `tau_ij` is the individual propagation delay of the connection `i ← j`.

The parameter `c` is a model parameter and is not automatically identified with the speed of light in vacuum.

## Spatial Neighbor Graph

Each domain interacts with a controlled number `k` of spatial neighbors.

The numerical structure therefore uses:

`N × k`

instead of a full pairwise structure:

`N × N`

The main memory scaling is reduced from:

`O(N²)`

approximately to:

`O(N k)`

This allows the module to operate with large domain ensembles without allocating full pairwise tensors.

The nearest-neighbor graph is built in blocks, so the complete pairwise-distance tensor is not retained in memory.

## Spatial Coupling Weights

The spatial coupling weight may be defined by a normalized radial kernel:

`raw_w_ij = exp(-d_ij² / 2 sigma²)`

Normalized weight:

`w_ij = raw_w_ij / sum_j raw_w_ij`

For each domain:

`sum_j w_ij = 1`

This keeps the effective coupling scale controlled when the selected number of neighbors changes.

## Retarded Kuramoto-Sakaguchi Equation

Retarded phase difference:

`delta_theta_ij(t) = theta_j(t - tau_ij) - theta_i(t) - alpha`

Phase evolution:

`d theta_i / dt = omega_i + K sum_j w_ij sin(delta_theta_ij(t)) + F_i(t)`

where:

- `theta_i(t)` is the current phase of domain `i`;
- `theta_j(t - tau_ij)` is the retarded phase of neighboring domain `j`;
- `omega_i` is the fixed natural frequency of domain `i`;
- `K` is the coupling strength;
- `w_ij` is the normalized spatial coupling weight;
- `alpha` is the Sakaguchi phase-lag parameter;
- `F_i(t)` is the external-forcing term.

Natural frequencies are initialized once and remain fixed during the full simulation.

## External Phase Forcing

External forcing may be represented as:

`F_i(t) = A_F sin(theta_F(t) - theta_i(t))`

where:

- `A_F` is the external-forcing density;
- `theta_F(t)` is the external-forcing phase.

When the external phase is not supplied, the module may use the current global mean phase as a model reference phase.

## Ring Buffer of Phase History

The required history depth is calculated from the maximum spatial delay:

`history_depth = ceil(maximum_tau / dt) + safety_margin`

The module uses a preallocated ring buffer:

`phase_history[history_index, domain_index]`

This avoids repeated allocation and copying of the complete phase-history field during tact-by-tact simulation.

## Fractional Delay Reconstruction

In the general case:

`tau_ij / dt`

is not an integer.

The module therefore decomposes the delay into:

`q_ij = floor(tau_ij / dt)`

and:

`lambda_ij = tau_ij / dt - q_ij`

The retarded phase is reconstructed between two neighboring history states.

To avoid discontinuities near `-pi` and `pi`, interpolation is performed through the complex phase representation:

`z_0 = exp(i theta_j[n - q_ij])`

`z_1 = exp(i theta_j[n - q_ij - 1])`

`z_delay = (1 - lambda_ij) z_0 + lambda_ij z_1`

`theta_j(t - tau_ij) = arg(z_delay)`

This prevents false interpolation across the phase-wrapping boundary.

## Tact-by-Tact Phase Evolution

At each tact interval, the module performs the following sequence:

`current phase state → retarded-history indices → fractional-delay reconstruction → retarded phase differences → weighted Kuramoto-Sakaguchi interaction → external forcing → phase velocity → phase update → phase wrapping → ring-buffer update → diagnostic metric calculation`

The wrapped phase state remains within:

`-pi <= theta_i < pi`

## Operational Metrics

### R_t_phase_order

Global Kuramoto phase-order parameter:

`R(t) = |mean(exp(i theta_i))|`

`R(t)` measures global phase synchronization.

`R(t)` remains distinct from full endogenous structural coherence `C(t)`.

### global_mean_phase

Global mean phase:

`Psi(t) = arg(mean(exp(i theta_i)))`

### delayed_local_phase_order

For each domain, the local retarded phase order is calculated over its spatial neighbors:

`R_delay_i(t) = |sum_j w_ij exp(i theta_j(t - tau_ij))|`

System-level local retarded phase order:

`R_delay_local(t) = mean_i(R_delay_i(t))`

### mean_phase_velocity

Mean phase velocity:

`mean_phase_velocity = mean_i(d theta_i / dt)`

### phase_velocity_dispersion

Dispersion of phase velocities:

`phase_velocity_dispersion = std_i(d theta_i / dt)`

This metric shows whether the domains retain a common phase-velocity range or transition toward increasing phase divergence.

### mean_delay

Mean metric propagation delay:

`mean_delay = mean_ij(tau_ij)`

### maximum_delay

Maximum retained metric propagation delay:

`maximum_delay = maximum_ij(tau_ij)`

### delay_dispersion

Delay dispersion:

`delay_dispersion = std_ij(tau_ij)`

### delayed_coupling_energy_proxy

A bounded interaction proxy parameter may be calculated as:

`E_delay_proxy = mean_ij(w_ij cos(delta_theta_ij))`

This metric describes the average coordination of retarded coupling links.

It is a numerical diagnostic proxy parameter of the module layer.

## Dynamic Role of Propagation Delay

Propagation delay changes the stability topology of the dynamic system.

Depending on the parameters, delay may support or induce:

- retained phase synchronization;
- retarded phase locking;
- oscillatory synchronization;
- phase clusters;
- phase waves;
- multistability;
- chimera-like states;
- phase-velocity dispersion;
- destabilization;
- transition toward endogenous dynamic criticality.

The influence of delay is evaluated through the full metric profile and the dynamic trajectory of the system.

## CPU and GPU Modes

Automatic backend selection:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py`

Forced CPU:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend cpu`

Forced GPU:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend gpu`

CPU example:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend cpu --domains 512 --neighbors 24 --tacts 100 --dt 0.005 --forcing 2.0`

GPU example:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend gpu --domains 16384 --neighbors 32 --tacts 500 --dt 0.005 --forcing 2.0`

`--steps` may be preserved as a compatibility alias for older scripts, while `--tacts` remains the primary EDK execution term.

## Logging

The module writes compact JSON metric snapshots:

`delay_tact_000001.json`

Optional field snapshots may be written as compressed NumPy archives:

`delay_field_000010.npz`

A field snapshot may contain:

`coords_3d`

`phases`

`natural_frequencies`

`neighbor_indices`

`edge_distances`

`tau_ij`

`delayed_neighbor_phases`

`phase_velocity`

Generated snapshots usually remain outside permanent version control.

## Diagnostics

The diagnostic module reads generated snapshots and visualizes:

- global phase-order parameter `R(t)`;
- local retarded phase order;
- mean phase velocity;
- phase-velocity dispersion;
- mean and maximum spatial delay;
- retarded-coupling energy proxy;
- three-dimensional phase distribution;
- three-dimensional propagation-delay graph.

Example:

`python module_edk_spatiotemporal_phase_delay/edk_delay_diagnostics.py --snapshot-dir edk_delay_snapshots --output edk_delay_diagnostics.png --no-show`

The diagnostic visualization uses the calculated simulation data and the calculated spatial-delay field.

## Operational Chain

`spatial domains → three-dimensional coordinates → spatial neighbor graph → metric distances → propagation delays tau_ij → ring buffer of phase history → fractional-delay reconstruction → retarded phase differences → weighted Kuramoto-Sakaguchi interaction → phase velocity → tact-by-tact phase evolution → R(t) → local retarded phase order → phase-velocity dispersion → transfer into subsequent EDK modules`

## Position in the EDK Architecture

The module forms the base metric-retardation layer of the executable EDK architecture.

Its position:

`framework parameters → three-dimensional spatial geometry → metric propagation delays → retarded phase states → retarded phase coupling → phase-synchronization metrics → vortex phase-field layer → subsequent interface and exchange-flow calculations`

The module may pass retarded phase states into:

`module_edk_vortex_phase_field`

The vortex phase-field module then adds:

`radial phase current → tangential phase current → nodal exchange-flow field → discrete rot J → signed vortex feedback`

## Integration Context

The module provides metric phase-retardation diagnostics and retarded phase states for subsequent EDK layers.

Downstream layers may calculate or integrate:

- full endogenous structural coherence `C(t)`;
- cubic endogenous structural coherence `C^3`;
- resonance window `Omega(t)`;
- retention threshold `Theta_N`;
- dynamic interface tensor `T_int`;
- manifested mass anchor `M(t)`;
- through-channel of exchange flow `J_flux`;
- recursive inheritance operator `Phi`.

The module is intended for:

- testing metric phase retardation;
- comparing instantaneous and retarded coupling;
- studying sensitivity to propagation velocity;
- studying sensitivity to spatial topology;
- identifying phase-locking regions;
- identifying phase-divergence regions;
- studying multistability and oscillatory synchronization;
- forming reproducible phase-delay snapshots;
- preparing retarded phase states for the vortex phase-field module;
- comparing CPU and GPU performance.

---

# EDK Пространственно-временная фазовая задержка

## RU

## Назначение

Данный модуль вводит метрическую пространственно-временную задержку распространения фазового сигнала в численную архитектуру EDK.

Модуль реализует пространственно распределённую систему Курамото — Сакагучи с ретардацией распространения. Фазовое состояние соседнего домена `j` считывается не в текущий момент домена `i`, а реконструируется из предшествующего состояния, соответствующего метрической задержке распространения:

`tau_ij = distance_ij / c`

Модуль сохраняет следующие контролируемые различия:

`мгновенное фазовое сопряжение ≠ метрическое ретардированное фазовое сопряжение`

`фазовая синхронизация ≠ фазовая когерентность`

`R(t) ≠ полное C(t)`

`задержка распространения ≠ автоматически стабилизирующее воздействие`

Модуль рассчитывает ретардированное фазовое взаимодействие как самостоятельный базовый слой, который впоследствии может использоваться вихревым фазово-полевым модулем и другими модулями EDK.

## Структура папки

`module_edk_spatiotemporal_phase_delay/`

`├── README_EN_RU.md`

`├── edk_spatiotemporal_phase_delay.py`

`├── edk_delay_diagnostics.py`

`├── smoke_test.py`

`└── __init__.py`

Генерируемые данные симуляции:

`edk_delay_snapshots/`

Рекомендуемые записи `.gitignore`:

`edk_delay_snapshots/`

`edk_delay_diagnostics.png`

`__pycache__/`

## Внешние зависимости

Обязательные:

`Python >= 3.10`

`numpy >= 1.26.0`

`matplotlib >= 3.8.0`

Необязательный GPU-бэкенд:

`CuPy, совместимый с установленной версией CUDA`

Пакет CuPy выбирается согласно активной версии CUDA.

Пример для CUDA 12:

`pip install cupy-cuda12x`

Установленный пакет CuPy должен соответствовать локальной среде CUDA.

## Пространственная геометрия доменов

Каждый фазовый домен получает фиксированную трёхмерную координату:

`x_i = (x_i, y_i, z_i)`

Пространственное смещение между доменом `i` и соседним доменом `j`:

`delta_x_ij = x_j - x_i`

Метрическое расстояние:

`d_ij = |delta_x_ij|`

Задержка распространения:

`tau_ij = d_ij / c`

где:

- `d_ij` — метрическое расстояние между двумя пространственными доменами;
- `c` — модельный параметр распространения фазового сигнала через симулируемую среду;
- `tau_ij` — индивидуальная задержка распространения связи `i ← j`.

Параметр `c` является параметром модели и автоматически не отождествляется со скоростью света в вакууме.

## Пространственный граф соседства

Каждый домен взаимодействует с контролируемым числом `k` пространственных соседей.

Численная структура поэтому использует:

`N × k`

вместо полной попарной структуры:

`N × N`

Основное масштабирование памяти уменьшается с:

`O(N²)`

примерно до:

`O(N k)`

Это позволяет модулю работать с большими совокупностями доменов без выделения полных попарных тензоров.

Граф ближайших соседей строится блоками, поэтому полный тензор попарных расстояний не удерживается в памяти.

## Пространственные веса сопряжения

Пространственный вес сопряжения может определяться нормированным радиальным ядром:

`raw_w_ij = exp(-d_ij² / 2 sigma²)`

Нормированный вес:

`w_ij = raw_w_ij / sum_j raw_w_ij`

Для каждого домена:

`sum_j w_ij = 1`

Это сохраняет контролируемый масштаб эффективного сопряжения при изменении выбранного числа соседей.

## Ретардированное уравнение Курамото — Сакагучи

Ретардированная разность фаз:

`delta_theta_ij(t) = theta_j(t - tau_ij) - theta_i(t) - alpha`

Эволюция фаз:

`d theta_i / dt = omega_i + K sum_j w_ij sin(delta_theta_ij(t)) + F_i(t)`

где:

- `theta_i(t)` — текущая фаза домена `i`;
- `theta_j(t - tau_ij)` — ретардированная фаза соседнего домена `j`;
- `omega_i` — фиксированная собственная частота домена `i`;
- `K` — сила сопряжения;
- `w_ij` — нормированный пространственный вес сопряжения;
- `alpha` — параметр фазового сдвига Сакагучи;
- `F_i(t)` — член внешнего форсинга.

Собственные частоты инициализируются один раз и остаются постоянными в течение всей симуляции.

## Внешний фазовый форсинг

Внешний форсинг может быть представлен как:

`F_i(t) = A_F sin(theta_F(t) - theta_i(t))`

где:

- `A_F` — плотность внешнего форсинга;
- `theta_F(t)` — фаза внешнего форсинга.

Если внешняя фаза не задана, модуль может использовать текущую глобальную среднюю фазу как модельную опорную фазу.

## Кольцевой буфер истории фаз

Необходимая глубина истории вычисляется из максимальной пространственной задержки:

`history_depth = ceil(maximum_tau / dt) + safety_margin`

Модуль использует предварительно выделенный кольцевой буфер:

`phase_history[history_index, domain_index]`

Это устраняет повторное выделение памяти и копирование полного поля истории фаз во время потактовой симуляции.

## Реконструкция дробной задержки

В общем случае:

`tau_ij / dt`

не является целым числом.

Поэтому модуль разделяет задержку на:

`q_ij = floor(tau_ij / dt)`

и:

`lambda_ij = tau_ij / dt - q_ij`

Ретардированная фаза реконструируется между двумя соседними состояниями истории.

Чтобы избежать разрывов около `-pi` и `pi`, интерполяция выполняется через комплексное представление фазы:

`z_0 = exp(i theta_j[n - q_ij])`

`z_1 = exp(i theta_j[n - q_ij - 1])`

`z_delay = (1 - lambda_ij) z_0 + lambda_ij z_1`

`theta_j(t - tau_ij) = arg(z_delay)`

Это предотвращает ложную интерполяцию через границу свёртки фаз.

## Потактовая эволюция фаз

На каждом потактовом интервале модуль выполняет следующую последовательность:

`текущее состояние фаз → индексы ретардированной истории → реконструкция дробной задержки → ретардированные разности фаз → взвешенное взаимодействие Курамото — Сакагучи → внешний форсинг → фазовая скорость → обновление фаз → свёртка фаз → обновление кольцевого буфера → вычисление диагностических метрик`

Свёрнутое состояние фаз остаётся в диапазоне:

`-pi <= theta_i < pi`

## Операционные метрики

### R_t_phase_order

Глобальный параметр фазового порядка Курамото:

`R(t) = |mean(exp(i theta_i))|`

`R(t)` измеряет глобальную фазовую синхронизацию.

`R(t)` остаётся отличным от полной эндогенной структурной когерентности `C(t)`.

### global_mean_phase

Глобальная средняя фаза:

`Psi(t) = arg(mean(exp(i theta_i)))`

### delayed_local_phase_order

Для каждого домена локальный ретардированный фазовый порядок вычисляется по его пространственным соседям:

`R_delay_i(t) = |sum_j w_ij exp(i theta_j(t - tau_ij))|`

Системный локальный ретардированный фазовый порядок:

`R_delay_local(t) = mean_i(R_delay_i(t))`

### mean_phase_velocity

Средняя фазовая скорость:

`mean_phase_velocity = mean_i(d theta_i / dt)`

### phase_velocity_dispersion

Дисперсия фазовых скоростей:

`phase_velocity_dispersion = std_i(d theta_i / dt)`

Данная метрика показывает, удерживают ли домены общий диапазон фазовых скоростей либо переходят к нарастающему фазовому разносу.

### mean_delay

Средняя метрическая задержка распространения:

`mean_delay = mean_ij(tau_ij)`

### maximum_delay

Максимальная удерживаемая метрическая задержка распространения:

`maximum_delay = maximum_ij(tau_ij)`

### delay_dispersion

Дисперсия задержек:

`delay_dispersion = std_ij(tau_ij)`

### delayed_coupling_energy_proxy

Ограниченный прокси-параметр взаимодействия может вычисляться как:

`E_delay_proxy = mean_ij(w_ij cos(delta_theta_ij))`

Эта метрика описывает среднее согласование ретардированных связей сопряжения.

Она является численным диагностическим прокси-параметром уровня модуля.

## Динамическая роль задержки распространения

Задержка распространения изменяет топологию устойчивости динамической системы.

В зависимости от параметров задержка может поддерживать или индуцировать:

- удерживаемую фазовую синхронизацию;
- ретардированную фазовую фиксацию;
- колебательную синхронизацию;
- фазовые кластеры;
- фазовые волны;
- мультистабильность;
- химероподобные состояния;
- дисперсию фазовых скоростей;
- дестабилизацию;
- переход к эндогенной динамической критичности.

Влияние задержки оценивается по полному профилю метрик и динамической траектории системы.

## Режимы CPU и GPU

Автоматический выбор бэкенда:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py`

Принудительный CPU:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend cpu`

Принудительный GPU:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend gpu`

Пример запуска на CPU:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend cpu --domains 512 --neighbors 24 --tacts 100 --dt 0.005 --forcing 2.0`

Пример запуска на GPU:

`python module_edk_spatiotemporal_phase_delay/edk_spatiotemporal_phase_delay.py --backend gpu --domains 16384 --neighbors 32 --tacts 500 --dt 0.005 --forcing 2.0`

`--steps` может сохраняться как compatibility alias для старых скриптов, при этом `--tacts` остаётся основным исполнительным термином EDK.

## Логирование

Модуль записывает компактные JSON-снимки метрик:

`delay_tact_000001.json`

Необязательные снимки полей могут записываться как сжатые архивы NumPy:

`delay_field_000010.npz`

Снимок поля может содержать:

`coords_3d`

`phases`

`natural_frequencies`

`neighbor_indices`

`edge_distances`

`tau_ij`

`delayed_neighbor_phases`

`phase_velocity`

Генерируемые снимки обычно остаются за пределами постоянного контроля версий.

## Диагностика

Диагностический модуль считывает сформированные снимки и визуализирует:

- глобальный параметр фазового порядка `R(t)`;
- локальный ретардированный фазовый порядок;
- среднюю фазовую скорость;
- дисперсию фазовых скоростей;
- среднюю и максимальную пространственную задержку;
- прокси-параметр энергии ретардированного сопряжения;
- трёхмерное распределение фаз;
- трёхмерный граф задержек распространения.

Пример:

`python module_edk_spatiotemporal_phase_delay/edk_delay_diagnostics.py --snapshot-dir edk_delay_snapshots --output edk_delay_diagnostics.png --no-show`

Диагностическая визуализация использует рассчитанные данные симуляции и рассчитанное поле пространственных задержек.

## Операционная цепочка

`пространственные домены → трёхмерные координаты → пространственный граф соседства → метрические расстояния → задержки распространения tau_ij → кольцевой буфер истории фаз → реконструкция дробной задержки → ретардированные разности фаз → взвешенное взаимодействие Курамото — Сакагучи → фазовая скорость → потактовая эволюция фаз → R(t) → локальный ретардированный фазовый порядок → дисперсия фазовых скоростей → передача в последующие модули EDK`

## Место в архитектуре EDK

Модуль формирует базовый метрический ретардационный слой исполняемой архитектуры EDK.

Его положение:

`параметры каркаса → трёхмерная пространственная геометрия → метрические задержки распространения → ретардированные состояния фаз → ретардированное фазовое сопряжение → метрики фазовой синхронизации → вихревой фазово-полевой слой → последующие вычисления интерфейса и потока обмена`

Модуль может передавать ретардированные состояния фаз в:

`module_edk_vortex_phase_field`

Вихревой фазово-полевой модуль затем добавляет:

`радиальный фазовый ток → тангенциальный фазовый ток → узловое поле потока обмена → дискретный rot J → знаковую вихревую обратную связь`

## Интеграционный контекст

Модуль предоставляет метрики метрической фазовой ретардации и ретардированные состояния фаз для последующих слоёв EDK.

Последующие слои могут рассчитывать или интегрировать:

- полную эндогенную структурную когерентность `C(t)`;
- кубическую эндогенную структурную когерентность `C^3`;
- резонансное окно `Omega(t)`;
- порог удержания `Theta_N`;
- динамический тензор интерфейса `T_int`;
- проявленный массовый якорь `M(t)`;
- сквозной канал потока обмена `J_flux`;
- оператор рекурсивного наследования `Phi`.

Модуль предназначен для:

- проверки метрической фазовой ретардации;
- сравнения мгновенного и ретардированного сопряжения;
- исследования чувствительности к скорости распространения;
- исследования чувствительности к пространственной топологии;
- определения областей фазовой фиксации;
- определения областей фазового разноса;
- исследования мультистабильности и колебательной синхронизации;
- формирования воспроизводимых снимков фазовой задержки;
- подготовки ретардированных состояний фаз для вихревого фазово-полевого модуля;
- сравнения производительности CPU и GPU.
