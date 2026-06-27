# EDK Vortex Phase Field Module — EN/RU

## EN

### Purpose

This module introduces rotational components into the phase-continuum model of EDK.

The module forms a non-parallel tangential component of the phase current, constructs a nodal exchange-flow field, and evaluates the local three-dimensional curl of this field through weighted least-squares reconstruction over a spatial neighborhood graph.

The module preserves the following controlled distinctions:

`phase synchronization ≠ phase coherence`

`R(t) ≠ C(t)`

`C_proxy(t) ≠ full C(t)`

`local vortex moment ≠ strict rot J`

`positive vortex contribution ≠ automatically stabilizing vortex contribution`

The implemented quantity `curl_J` is a discrete local approximation:

`rot J = curl J`

The numerical quantity `C_proxy_t` is explicitly designated as a model proxy parameter.

It is not declared to be the complete general endogenous structural coherence `C(t)`.

### Folder Structure

    module_edk_vortex_phase_field/
    ├── README_EN_RU.md
    ├── edk_vortex_phase_field.py
    ├── edk_vortex_diagnostics.py
    ├── smoke_test.py
    └── __init__.py

Generated simulation data:

    edk_vortex_snapshots/

Recommended `.gitignore` entries:

    edk_vortex_snapshots/
    edk_vortex_diagnostics.png
    __pycache__/

### External Dependencies

Required:

    Python >= 3.10
    numpy >= 1.26.0
    matplotlib >= 3.8.0

Optional GPU backend:

    CuPy compatible with the installed CUDA version

The repository should not pin the abstract `cupy` package without coordination with the installed CUDA environment.

Example:

    pip install cupy-cuda12x

The corresponding CuPy package must be selected for the active CUDA version.

### Mathematical Structure

For domain `i` and neighboring domain `j`:

`delta_theta_ij = theta_j(t - tau_ij) - theta_i(t) - alpha`

Unit direction vector:

`e_ij = (x_j - x_i) / |x_j - x_i|`

Local axis field:

`a_i = normalize(global_axis + radial_mix · radial_direction_i)`

Tangential direction:

`t_ij = normalize(a_i × e_ij)`

Weighted pair current:

`J_ij = w_ij · sin(delta_theta_ij) · (e_ij + xi · t_ij)`

Nodal exchange-flow field:

`J_i = sum_j J_ij`

This construction removes the zero identity that appears for parallel vectors:

`e_ij × [sin(delta_theta_ij) · e_ij] = 0`

Therefore, the radial component of the phase current and the tangential component of the phase current are calculated separately.

### Discrete Curl Reconstruction

For each node, the local gradient of the current field is reconstructed from current differences between neighboring nodes.

Let:

`X_i = [x_j - x_i]`

`Delta_J_i = [J_j - J_i]`

Weighted least-squares gradient:

`B_i = (X_i^T · W_i · X_i + lambda · I)^-1 · X_i^T · W_i · Delta_J_i`

The discrete curl is calculated as:

`curl_J_x = partial_y J_z - partial_z J_y`

`curl_J_y = partial_z J_x - partial_x J_z`

`curl_J_z = partial_x J_y - partial_y J_x`

Signed local vortex component:

`omega_i = curl_J_i · a_i`

This signed projection makes it possible to distinguish vortex contributions aligned with the local axis from vortex contributions directed against it.

### Retarded Kuramoto–Sakaguchi Evolution

Phase evolution:

`d_theta_i / dt = omega_i_natural + K · sum_j w_ij · sin(delta_theta_ij) + kappa_vortex · tanh(signed_vorticity_i / vorticity_scale) + external_forcing_i`

Natural frequencies are initialized once and remain constant during the simulation.

Propagation delay:

`tau_ij = |x_j - x_i| / c`

Delay indices are precomputed and stored in the simulation structure.

Retarded phase states are read from a ring buffer of phase history.

### Amplitude Evolution

Amplitudes change through a bounded Stuart–Landau-type proxy equation:

`d_A_i / dt = mu · A_i · (1 - A_i^2) + k_A · (mean_neighbor_amplitude_i - A_i) - eta_A · P_ext · A_i`

This allows the module to distinguish the phase-only order parameter from the proxy parameter of phase-amplitude coherence.

### Operational Metrics

#### R_t_phase_order

Kuramoto phase-order parameter:

`R(t) = |mean(exp(i · theta))|`

It measures only phase synchronization.

It is not identified with the full endogenous structural coherence `C(t)`.

#### phase_amplitude_coherence

Normalized global phase-amplitude order:

`|mean(A · exp(i · theta))| / mean(A)`

#### local_phase_coherence

Weighted mean local phase order over the spatial neighborhood graph.

#### amplitude_retention

Bounded proxy parameter of amplitude uniformity.

#### C_proxy_t

Geometric combination of:

- phase-amplitude coherence;
- local phase coherence;
- amplitude retention.

This quantity remains a model proxy parameter.

It must not be identified with the full `C(t)` of EDK.

#### mean_vorticity_abs

Mean magnitude of the computed local discrete curl field.

#### vortex_alignment

Mean bounded signed alignment between `curl J` and the local axis field.

#### positive_vortex_support

Positive signed contribution of the computed vortex field into the proxy parameter of the retained interface.

#### negative_vortex_penalty

Negative signed contribution of the computed vortex field into interface degradation or destabilization.

#### interface_retention_proxy

Bounded proxy parameter that includes:

- `C_proxy(t)`;
- external pressure;
- positive vortex support;
- negative vortex penalty.

Therefore, vortex twisting is not considered automatically stabilizing.

#### M_proxy_t

Model proxy parameter of the manifested mass anchor, derived from the retained-interface proxy parameter.

#### continuum_appearance_index

Dimensionless diagnostic index.

It is an algorithmic observable parameter of this numerical implementation, not an independently established physical law.

### Computational Architecture

The original full tensor structure `N × N × 3` is replaced by a local spatial neighborhood graph.

The implementation uses arrays:

`N × k`

and:

`N × k × 3`

where `k` is the number of spatial neighbors.

This reduces the main memory scaling of the simulation from:

`O(N^2)`

approximately to:

`O(N k)`

The primary nearest-neighbor search is computed in blocks so that the full pairwise distance tensor does not have to be retained in memory.

### CPU and GPU Modes

Automatic backend selection:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py

Forced CPU:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend cpu

Forced GPU:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend gpu

Example GPU run:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend gpu --domains 4096 --neighbors 24 --steps 100 --dt 0.005 --forcing 8.0 --pressure 0.1 --field-every 10

Short CPU check:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend cpu --domains 256 --neighbors 16 --steps 10 --field-every 5

### Diagnostics

The engine writes compact JSON metric snapshots:

    vortex_step_000001.json

Optional computed-field snapshots are written as compressed NumPy archives:

    vortex_field_000010.npz

A computed-field snapshot contains:

    coords_3d
    phases
    amplitudes
    node_exchange_current
    curl_J
    signed_vorticity
    local_axes

Diagnostic panel generation:

    python module_edk_vortex_phase_field/edk_vortex_diagnostics.py --snapshot-dir edk_vortex_snapshots --output edk_vortex_diagnostics.png --no-show

The diagnostic panel contains:

- dynamics of the Continuum appearance index;
- dynamics of the mean discrete curl;
- dynamics of the Kuramoto phase-order parameter `R(t)`;
- computed three-dimensional vector field `curl_J`.

The three-dimensional panel visualizes the field computed during the simulation.

It does not generate a synthetic toroidal substitute.

### Operational Chain

`spatial domains → retarded phase differences → radial phase current → tangential phase current → nodal exchange-flow field → discrete rot J → signed vortex component → vortex phase feedback → R(t) → C_proxy(t) → retained-interface proxy parameter → M_proxy(t) → positive or negative change of the appearance index`

### Position in the EDK Architecture

The module introduces a rotational phase-field layer between spatial phase interaction and the calculation of retained-interface conditions.

Its operational position:

`spatial phase interaction → retarded phase coupling → radial phase-current component → tangential phase-current component → discrete rot J → signed vortex feedback → phase synchronization R(t) → phase-amplitude coherence proxy parameter → C_proxy(t) → retained-interface proxy parameter → M_proxy(t) → diagnostic appearance index`

The module does not replace:

- the complete mathematical formalism of EDK;
- the general endogenous structural coherence `C(t)`;
- the dynamic interface tensor `T_int`;
- the through exchange-flow channel `J_flux`;
- the complete recursive inheritance operator `Phi`.

It provides a numerical rotational phase-field layer that can later be connected with these elements through a controlled integration interface.

### Interpretation Boundaries

This module is a numerical model.

It does not independently establish that:

- the calculated field is the complete physical field of vortex twisting of the Continuum;
- `C_proxy(t)` is identical to the full endogenous structural coherence `C(t)`;
- the appearance index is a directly measurable physical observable;
- any vortex contribution stabilizes the retained form;
- metric or mass proxy parameters are a complete solution of relativistic field equations;
- discrete curl reconstruction replaces direct experimental measurement.

The module is intended for:

- testing internal mathematical consistency;
- numerical experiments with perturbations;
- comparison of radial and rotational phase coupling;
- stress testing near `C_proxy(t) ≈ P(t)`;
- analysis of positive and negative signed vortex contributions;
- formation of reproducible computed-field snapshots;
- comparison of CPU and GPU execution;
- preparation for subsequent integration with `T_int` and `J_flux`.

---

# Модуль EDK Vortex Phase Field — EN/RU

## RU

### Назначение

Данный модуль вводит роторные компоненты в фазово-континуумную модель EDK.

Модуль формирует непараллельную тангенциальную компоненту фазового тока, строит узловое поле потока обмена и оценивает локальный трёхмерный ротор этого поля посредством взвешенной реконструкции методом наименьших квадратов по пространственному графу соседства.

Модуль сохраняет следующие контролируемые различия:

`фазовая синхронизация ≠ фазовая когерентность`

`R(t) ≠ C(t)`

`C_proxy(t) ≠ полное C(t)`

`локальный вихревой момент ≠ строгий rot J`

`положительный вихревой вклад ≠ автоматически стабилизирующий вихревой вклад`

Реализованная величина `curl_J` является дискретным локальным приближением:

`rot J = curl J`

Численная величина `C_proxy_t` прямо обозначена как модельный прокси-параметр.

Она не объявляется полной общей эндогенной структурной когерентностью `C(t)`.

### Структура папки

    module_edk_vortex_phase_field/
    ├── README_EN_RU.md
    ├── edk_vortex_phase_field.py
    ├── edk_vortex_diagnostics.py
    ├── smoke_test.py
    └── __init__.py

Генерируемые данные симуляции:

    edk_vortex_snapshots/

Рекомендуемые записи `.gitignore`:

    edk_vortex_snapshots/
    edk_vortex_diagnostics.png
    __pycache__/

### Внешние зависимости

Обязательные:

    Python >= 3.10
    numpy >= 1.26.0
    matplotlib >= 3.8.0

Необязательный GPU-бэкенд:

    CuPy, совместимый с установленной версией CUDA

В репозитории не следует фиксировать абстрактный пакет `cupy` без его согласования с установленной средой CUDA.

Пример:

    pip install cupy-cuda12x

Необходимо использовать соответствующий пакет CuPy для активной версии CUDA.

### Математическая структура

Для домена `i` и соседнего домена `j`:

`delta_theta_ij = theta_j(t - tau_ij) - theta_i(t) - alpha`

Единичный вектор направления:

`e_ij = (x_j - x_i) / |x_j - x_i|`

Локальное поле осей:

`a_i = normalize(global_axis + radial_mix · radial_direction_i)`

Тангенциальное направление:

`t_ij = normalize(a_i × e_ij)`

Взвешенный парный ток:

`J_ij = w_ij · sin(delta_theta_ij) · (e_ij + xi · t_ij)`

Узловое поле потока обмена:

`J_i = sum_j J_ij`

Данная конструкция устраняет нулевое тождество, возникающее для параллельных векторов:

`e_ij × [sin(delta_theta_ij) · e_ij] = 0`

Поэтому радиальная компонента фазового тока и тангенциальная компонента фазового тока рассчитываются раздельно.

### Дискретная реконструкция ротора

Для каждого узла локальный градиент поля тока реконструируется по разностям токов соседних узлов.

Пусть:

`X_i = [x_j - x_i]`

`Delta_J_i = [J_j - J_i]`

Взвешенный градиент метода наименьших квадратов:

`B_i = (X_i^T · W_i · X_i + lambda · I)^-1 · X_i^T · W_i · Delta_J_i`

Дискретный ротор вычисляется как:

`curl_J_x = partial_y J_z - partial_z J_y`

`curl_J_y = partial_z J_x - partial_x J_z`

`curl_J_z = partial_x J_y - partial_y J_x`

Знаковая локальная вихревая компонента:

`omega_i = curl_J_i · a_i`

Данная знаковая проекция позволяет различать вихревые вклады, согласованные с локальной осью, и вихревые вклады, направленные против неё.

### Ретардированная эволюция Курамото — Сакагучи

Эволюция фаз:

`d_theta_i / dt = omega_i_natural + K · sum_j w_ij · sin(delta_theta_ij) + kappa_vortex · tanh(signed_vorticity_i / vorticity_scale) + external_forcing_i`

Собственные частоты инициализируются один раз и остаются постоянными в течение симуляции.

Задержка распространения:

`tau_ij = |x_j - x_i| / c`

Индексы задержек предварительно вычисляются и сохраняются в структуре симуляции.

Ретардированные состояния фаз считываются из кольцевого буфера истории.

### Эволюция амплитуд

Амплитуды изменяются посредством ограниченного прокси-уравнения типа Стюарта — Ландау:

`d_A_i / dt = mu · A_i · (1 - A_i^2) + k_A · (mean_neighbor_amplitude_i - A_i) - eta_A · P_ext · A_i`

Это позволяет модулю различать параметр порядка только фаз и прокси-параметр фазово-амплитудной когерентности.

### Операционные метрики

#### R_t_phase_order

Параметр фазового порядка Курамото:

`R(t) = |mean(exp(i · theta))|`

Он измеряет только фазовую синхронизацию.

Он не отождествляется с полной эндогенной структурной когерентностью `C(t)`.

#### phase_amplitude_coherence

Нормированный глобальный фазово-амплитудный порядок:

`|mean(A · exp(i · theta))| / mean(A)`

#### local_phase_coherence

Взвешенный средний локальный фазовый порядок по пространственному графу соседства.

#### amplitude_retention

Ограниченный прокси-параметр равномерности амплитуд.

#### C_proxy_t

Геометрическая комбинация:

- фазово-амплитудной когерентности;
- локальной фазовой когерентности;
- удержания амплитуд.

Данная величина остаётся модельным прокси-параметром.

Она не должна отождествляться с полным `C(t)` EDK.

#### mean_vorticity_abs

Средний модуль вычисленного локального дискретного поля ротора.

#### vortex_alignment

Средняя ограниченная знаковая согласованность между `curl J` и локальным полем осей.

#### positive_vortex_support

Положительный знаковый вклад вычисленного вихревого поля в прокси-параметр удерживаемого интерфейса.

#### negative_vortex_penalty

Отрицательный знаковый вклад вычисленного вихревого поля в деградацию или дестабилизацию интерфейса.

#### interface_retention_proxy

Ограниченный прокси-параметр, включающий:

- `C_proxy(t)`;
- внешнее давление;
- положительную вихревую поддержку;
- отрицательный вихревой штраф.

Поэтому вихревое закручивание не считается автоматически стабилизирующим.

#### M_proxy_t

Модельный прокси-параметр проявленного массового якоря, выведенный из прокси-параметра удерживаемого интерфейса.

#### continuum_appearance_index

Безразмерный диагностический индекс.

Он является алгоритмическим наблюдаемым параметром данной численной реализации, а не независимо установленным физическим законом.

### Вычислительная архитектура

Исходная полная тензорная структура `N × N × 3` заменена локальным пространственным графом соседства.

Реализация использует массивы:

`N × k`

и:

`N × k × 3`

где `k` является числом пространственных соседей.

Это уменьшает основное масштабирование памяти симуляции с:

`O(N^2)`

примерно до:

`O(N k)`

Первичный поиск ближайших соседей вычисляется блоками, чтобы не удерживать полный тензор попарных расстояний.

### Режимы CPU и GPU

Автоматический выбор бэкенда:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py

Принудительный CPU:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend cpu

Принудительный GPU:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend gpu

Пример GPU-запуска:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend gpu --domains 4096 --neighbors 24 --steps 100 --dt 0.005 --forcing 8.0 --pressure 0.1 --field-every 10

Короткая проверка на CPU:

    python module_edk_vortex_phase_field/edk_vortex_phase_field.py --backend cpu --domains 256 --neighbors 16 --steps 10 --field-every 5

### Диагностика

Движок записывает компактные JSON-снимки метрик:

    vortex_step_000001.json

Необязательные снимки вычисленного поля записываются как сжатые архивы NumPy:

    vortex_field_000010.npz

Снимок вычисленного поля содержит:

    coords_3d
    phases
    amplitudes
    node_exchange_current
    curl_J
    signed_vorticity
    local_axes

Построение диагностической панели:

    python module_edk_vortex_phase_field/edk_vortex_diagnostics.py --snapshot-dir edk_vortex_snapshots --output edk_vortex_diagnostics.png --no-show

Диагностическая панель содержит:

- динамику индекса проявленности Континуума;
- динамику среднего дискретного ротора;
- динамику параметра фазового порядка Курамото `R(t)`;
- вычисленное трёхмерное векторное поле `curl_J`.

Трёхмерная панель визуализирует поле, вычисленное в ходе симуляции.

Она не генерирует синтетическую тороидальную подмену.

### Операционная цепочка

`пространственные домены → ретардированные фазовые различия → радиальный фазовый ток → тангенциальный фазовый ток → узловое поле потока обмена → дискретный rot J → знаковая вихревая компонента → вихревая фазовая обратная связь → R(t) → C_proxy(t) → прокси-параметр удерживаемого интерфейса → M_proxy(t) → положительное или отрицательное изменение индекса проявленности`

### Место в архитектуре EDK

Модуль вводит роторный фазово-полевой слой между пространственным фазовым взаимодействием и вычислением условий удерживаемого интерфейса.

Его операционное положение:

`пространственное фазовое взаимодействие → ретардированное фазовое сопряжение → радиальная компонента фазового тока → тангенциальная компонента фазового тока → дискретный rot J → знаковая вихревая обратная связь → фазовая синхронизация R(t) → прокси-параметр фазово-амплитудной когерентности → C_proxy(t) → прокси-параметр удерживаемого интерфейса → M_proxy(t) → диагностический индекс проявленности`

Модуль не заменяет:

- полный математический формализм EDK;
- общую эндогенную структурную когерентность `C(t)`;
- динамический тензор интерфейса `T_int`;
- сквозной канал потока обмена `J_flux`;
- полный оператор рекурсивного наследования `Phi`.

Он предоставляет численный роторный фазово-полевой слой, который впоследствии может быть связан с этими элементами через контролируемый интерфейс интеграции.

### Границы интерпретации

Данный модуль является численной моделью.

Он самостоятельно не устанавливает, что:

- рассчитанное поле является полным физическим полем вихревого закручивания Континуума;
- `C_proxy(t)` тождественно полной эндогенной структурной когерентности `C(t)`;
- индекс проявленности является непосредственно измеряемым физическим наблюдаемым параметром;
- любой вихревой вклад стабилизирует удерживаемую форму;
- метрические или массовые прокси-параметры являются полным решением релятивистских полевых уравнений;
- дискретная реконструкция ротора заменяет прямое экспериментальное измерение.

Модуль предназначен для:

- проверки внутренней математической согласованности;
- численных экспериментов с возмущениями;
- сравнения радиального и роторного фазового сопряжения;
- нагрузочного тестирования около `C_proxy(t) ≈ P(t)`;
- анализа положительных и отрицательных знаковых вихревых вкладов;
- формирования воспроизводимых снимков вычисленного поля;
- сравнения исполнения на CPU и GPU;
- подготовки последующей интеграции с `T_int` и `J_flux`.
