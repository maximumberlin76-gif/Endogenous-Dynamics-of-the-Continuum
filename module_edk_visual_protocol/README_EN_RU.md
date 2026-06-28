# Marnov Protocol U_6D / C^3 Engineering Visualizer

## EN — Engineering Visualization of Tact-by-Tact Phase Locking and Local Interface Transition

The `MarnovCubicPotentialVisualizer` module implements an engineering visual simulator of:

- tact-by-tact phase-mismatch dynamics;
- the trajectory of a three-plane phase-state space;
- the tensor-product multiplet operator `U_6D`;
- the normalized phase-lock amplitude;
- the local representation of `C^3`;
- the local transition between `C^3` and the cubic-dissipation level `P_cubic`;
- the independent system-level relation between `C(t)` and `P(t)`.

The module combines temporal phase dynamics with spatial analysis of an interface barrier.

The module preserves the mandatory distinctions:

C(t) ≠ C^3

P(t) ≠ P_cubic

R(n) ≠ C(t)

The local equality:

C^3 = P_cubic

is a local cubic-transition boundary.

It is not the system-level EDS / EDC boundary.

The system-level relation is determined independently through:

C(t) > P(t) — Endogenous Dynamic Stability

C(t) = P(t) — Endogenous Dynamic Criticality

C(t) < P(t) — degradation drift

## EN — Module File

`module_edk_visual_protocol/marnov_cubic_potential_visualizer.py`

## EN — README File

`module_edk_visual_protocol/README_EN_RU.md`

## EN — Dependencies

The module requires:

- `numpy>=1.26.0`
- `matplotlib>=3.8.0`

## EN — Installation

`pip install numpy matplotlib`

## EN — Launch

`python module_edk_visual_protocol/marnov_cubic_potential_visualizer.py`

## EN — Main Operational Architecture

The module contains two separate operational relations.

Local multiplet and interface relation:

three orthogonal two-dimensional phase planes  
→ pair-lock operators `L_k`  
→ tensor-product operator `U_6D`  
→ normalized phase-lock amplitude  
→ local representation of `C^3`  
→ comparison with `P_cubic`  
→ local `C^3`-dominance domain  
→ local transition boundary `C^3 = P_cubic`  
→ local cubic-dissipation-dominance domain

Independent system-level relation:

C(t) and P(t)  
→ C(t) > P(t): Endogenous Dynamic Stability  
→ C(t) = P(t): Endogenous Dynamic Criticality  
→ C(t) < P(t): degradation drift

The local relation between `C^3` and `P_cubic` must not be used as a replacement for the system-level relation between `C(t)` and `P(t)`.

## EN — Pair-Lock Operator

Each two-dimensional phase plane is represented by one complex pair-lock operator with dimension `2 × 2`.

The local phase angle is:

`phase_angle = kappa · sin(delta_phi)`

The two counter-directed channels use opposite phase directions:

`phase_operator = [[exp(+i · phase_angle), 0], [0, exp(-i · phase_angle)]]`

The micro-asymmetry operator is:

`asymmetry_operator = [[cos(epsilon), sin(epsilon)], [-sin(epsilon), cos(epsilon)]]`

The complete pair-lock operator is:

`L_k = sqrt(R) · phase_operator · asymmetry_operator`

Where:

- `R` is the local phase-support coefficient;
- `kappa` is the local nonlinear phase-lock strength;
- `epsilon` is the micro-asymmetry angle;
- `delta_phi` is the phase difference between counter-directed channels.

The coefficient `R` is a local phase-support parameter.

It is not the general endogenous structural coherence `C(t)`.

The multiplier `sqrt(R)` changes the amplitude of the pair-lock operator and not only its complex phase.

## EN — Multiplet Operator U_6D

Three orthogonal pair-lock operators are contracted through the Kronecker product:

`U_6D = L_1 ⊗ L_2 ⊗ L_3`

Each `L_k` is a `2 × 2` matrix.

The resulting multiplet operator is:

`U_6D = complex matrix 8 × 8`

The name `U_6D` describes a multiplet assembled from three orthogonal two-dimensional phase planes.

The current numerical implementation does not use six independent spatial coordinates.

The designation `U_6D` therefore identifies the model layer and the construction of the multiplet operator, not a six-coordinate spatial grid.

## EN — Normalized Phase-Lock Amplitude

The normalized phase-lock amplitude is calculated as:

`lock_amplitude = abs(Tr(U_6D)) / dimension(U_6D)`

For the current operator:

`lock_amplitude = abs(Tr(U_6D)) / 8`

Normalization makes it possible to compare the phase-lock amplitude:

- between different simulation tacts;
- between different interface coordinates;
- between different local phase-support values.

The normalized lock amplitude is an indicator of the current multiplet phase-lock state.

It is not the general endogenous structural coherence `C(t)`.

## EN — Local Representation of C^3

`C^3` is defined within the EDK architecture as cubic nonlinear saturation, compression, and delay of the phase-coherent configuration.

The current visualizer represents the cubic amplitude component of `C^3` through:

`C^3 = (psi_amplitude · lock_amplitude)^3`

The cubic relation increases the sensitivity of the local `C^3` profile to a reduction in the normalized phase-lock amplitude.

The local operational chain is:

reduction of `lock_amplitude`  
→ stronger relative reduction of `C^3`  
→ approach to the local `C^3 / P_cubic` transition boundary

The current visualizer does not implement a separate temporal delay kernel for `C^3`.

It visualizes the cubic nonlinear amplitude component used by the local interface model.

`C^3` is not the general endogenous structural coherence:

C(t) ≠ C^3

## EN — Local Cubic-Dissipation Level P_cubic

The local cubic-dissipation level is calculated as:

`P_cubic = dissipation_coefficient · psi_amplitude^3`

`P_cubic` is a local comparison level used by the interface visualization.

It is not the system-level destabilizing pressure `P(t)`:

P(t) ≠ P_cubic

The local relations are:

C^3 > P_cubic  
→ local C^3 dominance

C^3 = P_cubic  
→ local cubic-transition boundary

C^3 < P_cubic  
→ local cubic-dissipation dominance

These relations describe the local interface profile only.

They do not independently determine Endogenous Dynamic Stability or Endogenous Dynamic Criticality.

## EN — Independent System-Level EDS / EDC Relation

The module receives the independent parameters:

- `C_t` — general endogenous structural coherence `C(t)`;
- `P_t` — destabilizing pressure `P(t)`.

The system-level regime is classified through:

C(t) > P(t)  
→ Endogenous Dynamic Stability

C(t) = P(t)  
→ Endogenous Dynamic Criticality

C(t) < P(t)  
→ degradation drift

The method `classify_system_regime()` performs this classification independently from the local `C^3` profile.

The system-level relation must not be derived from:

- the normalized trace of `U_6D`;
- the phase-support coefficient `R`;
- the local `C^3` profile;
- the local cubic-dissipation level `P_cubic`.

## EN — Tact-by-Tact Phase Dynamics

The temporal simulation begins with three phase differences:

`current_phi = [0.8, -0.7, 0.5]`

The nonlinear restoring increment is:

`restoring_increment = -gamma · sin(current_phi) · dt`

The external dissipative-noise increment is:

`noise_increment = noise_strength · sqrt(dt) · normal_random_vector`

The phase state is updated as:

`current_phi(t + dt) = current_phi(t) + restoring_increment + noise_increment`

Each subsequent tact inherits the phase state formed by the preceding tact.

This is the recursive inheritance of the preceding phase state within the temporal numerical process.

The expected result is not an ideally static zero state.

The expected result is a fluctuating dynamically retained region near the phase attractor.

The stochastic increment is scaled by `sqrt(dt)` so that changing the tact duration does not incorrectly rescale the noise process.

## EN — Interface Barrier

The spatial phase-support profile is:

`R(X) = R_base - barrier_depth · exp(-((X - barrier_center) / barrier_width)^2)`

Outside the barrier:

`R(X) ≈ R_base`

Inside the barrier:

`R(X)` decreases

After the barrier:

`R(X)` recovers

The profile is constrained to the interval:

`0 ≤ R(X) ≤ 1`

The local phase-lock strength is:

`kappa_local = alpha_lock · R(X)`

For each spatial coordinate, the module recalculates:

`R(X) → L_k(X) → U_6D(X) → lock_amplitude(X) → C^3(X)`

The local `C^3` profile is then compared with the independent local cubic-dissipation profile:

`P_cubic(X)`

In the current implementation, `P_cubic(X)` is spatially constant unless the model is extended with a variable dissipation profile.

## EN — Local Transition Coordinates

The module determines coordinates where:

`C^3(X) - P_cubic(X) = 0`

The transition-point detector retains:

- exact equality samples;
- sign-changing intervals between neighboring samples.

For a sign-changing interval, the transition coordinate is estimated through linear interpolation.

The resulting coordinates represent the local numerical boundary:

`C^3 = P_cubic`

They are local cubic-transition coordinates.

They must not be identified as the system-level EDC boundary:

`C(t) = P(t)`

The previous field name `bifurcation_points` is retained only as a backward-compatible alias.

The operational field name is:

`cubic_transition_points`

## EN — Engineering Visualizations

The module generates four engineering graphs.

### EN — 1. Tact-by-Tact Phase-Mismatch Dynamics

The graph displays:

- `delta_phi_1(t)`;
- `delta_phi_2(t)`;
- `delta_phi_3(t)`.

It shows the interaction between:

- nonlinear restoring dynamics;
- external dissipative phase noise;
- recursive inheritance of the preceding phase state.

### EN — 2. Three-Plane Phase-State-Space Trajectory

The graph displays the trajectory:

`delta_phi_1, delta_phi_2, delta_phi_3`

It shows:

- the initial state;
- the intermediate trajectory;
- the final state.

This is the phase-state space of the numerical system.

It is not a space of ordinary physical coordinates.

### EN — 3. U_6D Lock Amplitude and C^3

The graph displays:

`normalized abs(Tr(U_6D))`

and:

`C^3`

The normalized trace represents the current multiplet phase-lock amplitude.

The `C^3` curve represents the local cubic nonlinear amplitude used by the visualizer.

Neither quantity is the general endogenous structural coherence `C(t)`.

### EN — 4. Local C^3 / P_cubic Interface Transition

The graph displays:

`C^3(X)`

and:

`P_cubic(X)`

Local `C^3`-dominance domain:

`C^3 > P_cubic`

Local cubic-dissipation-dominance domain:

`C^3 < P_cubic`

Vertical markers show the approximate local transition coordinates:

`C^3 = P_cubic`

The graphical block separately displays the independent system-level values:

- `C(t)`;
- `P(t)`;
- the classified system regime.

## EN — Correction of the Original Trace Construction

The original construction used one common complex multiplier:

`L_k = exp(i · phase_angle) · H_asym`

A common phase multiplier changes the phase of the trace but does not necessarily change:

`abs(Tr(L_k))`

The same limitation propagates into:

`abs(Tr(U_6D))`

The corrected module uses:

- counter-directed phase directions `exp(+i · phase_angle)` and `exp(-i · phase_angle)`;
- the independent phase-support amplitude `sqrt(R)`.

The absolute trace can therefore respond to:

- phase mismatch;
- local nonlinear coupling strength;
- the phase-support coefficient;
- the depth of the interface barrier.

## EN — Dimensional Interpretation

The current module explicitly implements:

- three phase differences;
- three pair-lock operators `2 × 2`;
- one complex tensor-product operator `8 × 8`;
- one temporal coordinate;
- one spatial interface coordinate;
- one independent system-level pair `C(t)` and `P(t)`.

The designations `2D`, `4D`, `5D`, `6D`, and `7D` identify model layers when the corresponding independent mathematical coordinates are not directly implemented.

The module must not be interpreted as a direct numerical realization of six or seven independent spatial coordinates.

## EN — Main Invariants

Local multiplet invariant:

`tact-by-tact phase-lock retention is represented by a dynamically evolving multiplet state whose normalized phase-lock amplitude forms the local C^3 profile`

Local interface relation:

C^3 > P_cubic  
→ local C^3 dominance

C^3 = P_cubic  
→ local cubic-transition boundary

C^3 < P_cubic  
→ local cubic-dissipation dominance

System-level relation:

C(t) > P(t)  
→ Endogenous Dynamic Stability

C(t) = P(t)  
→ Endogenous Dynamic Criticality

C(t) < P(t)  
→ degradation drift

Mandatory distinctions:

C(t) ≠ C^3

P(t) ≠ P_cubic

R(n) ≠ C(t)

The local interface relation and the system-level relation are not interchangeable.

## EN — Main Class

`MarnovCubicPotentialVisualizer`

## EN — Main Methods

- `set_system_state()` — sets the independent system-level parameters `C(t)` and `P(t)`.
- `classify_system_regime()` — classifies the independent system-level EDS / EDC relation.
- `build_pair_lock()` — forms one complex pair-lock operator `2 × 2`.
- `calculate_u_6d()` — contracts three pair-lock operators into one multiplet operator `8 × 8`.
- `calculate_lock_amplitude()` — calculates the normalized absolute trace.
- `calculate_cubic_potential()` — calculates the local representation of `C^3`.
- `calculate_cubic_dissipation_level()` — calculates the local cubic-dissipation level `P_cubic`.
- `simulate_temporal_dynamics()` — simulates tact-by-tact phase dynamics.
- `calculate_interface_profile()` — calculates the local interface profile.
- `visualize_engineering_data()` — generates four engineering graphs.
- `run_visual_simulation()` — executes the complete simulation and visualization.

---

# Инженерный визуальный симулятор U_6D / C^3 Протокола Марнова

## RU — Инженерная визуализация потактового фазового удержания и локального интерфейсного перехода

Модуль `MarnovCubicPotentialVisualizer` реализует инженерный визуальный симулятор:

- потактовой динамики фазового рассогласования;
- траектории трёхплоскостного фазового пространства состояний;
- тензорно-произведённого мультиплетного оператора `U_6D`;
- нормированной амплитуды фазового замка;
- локального представления `C^3`;
- локального перехода между `C^3` и уровнем кубической диссипации `P_cubic`;
- самостоятельного общесистемного соотношения между `C(t)` и `P(t)`.

Модуль объединяет временную фазовую динамику и пространственный анализ перехода через интерфейсный барьер.

Модуль сохраняет обязательные различия:

C(t) ≠ C^3

P(t) ≠ P_cubic

R(n) ≠ C(t)

Локальное равенство:

C^3 = P_cubic

является локальной границей кубического перехода.

Оно не является общесистемной границей EDS / EDC.

Общесистемное соотношение определяется самостоятельно:

C(t) > P(t) — эндогенная динамическая устойчивость

C(t) = P(t) — эндогенная динамическая критичность

C(t) < P(t) — дрейф деградации

## RU — Файл модуля

`module_edk_visual_protocol/marnov_cubic_potential_visualizer.py`

## RU — Файл README

`module_edk_visual_protocol/README_EN_RU.md`

## RU — Зависимости

Модулю требуются:

- `numpy>=1.26.0`
- `matplotlib>=3.8.0`

## RU — Установка

`pip install numpy matplotlib`

## RU — Запуск

`python module_edk_visual_protocol/marnov_cubic_potential_visualizer.py`

## RU — Основная операционная архитектура

Модуль содержит два отдельных операционных соотношения.

Локальная мультиплетная и интерфейсная цепочка:

три ортогональные двумерные фазовые плоскости  
→ операторы парного замка `L_k`  
→ тензорно-произведённый оператор `U_6D`  
→ нормированная амплитуда фазового замка  
→ локальное представление `C^3`  
→ сравнение с `P_cubic`  
→ локальная область доминирования `C^3`  
→ локальная граница перехода `C^3 = P_cubic`  
→ локальная область доминирования кубической диссипации

Самостоятельное общесистемное соотношение:

C(t) и P(t)  
→ C(t) > P(t): эндогенная динамическая устойчивость  
→ C(t) = P(t): эндогенная динамическая критичность  
→ C(t) < P(t): дрейф деградации

Локальное соотношение между `C^3` и `P_cubic` не должно использоваться как замена общесистемного соотношения между `C(t)` и `P(t)`.

## RU — Оператор парного замка

Каждая двумерная фазовая плоскость представлена одним комплексным оператором парного замка размерностью `2 × 2`.

Локальный фазовый угол:

`phase_angle = kappa · sin(delta_phi)`

Два встречных канала используют противоположные фазовые направления:

`phase_operator = [[exp(+i · phase_angle), 0], [0, exp(-i · phase_angle)]]`

Оператор микроасимметрии:

`asymmetry_operator = [[cos(epsilon), sin(epsilon)], [-sin(epsilon), cos(epsilon)]]`

Полный оператор парного замка:

`L_k = sqrt(R) · phase_operator · asymmetry_operator`

Где:

- `R` — локальный коэффициент фазовой поддержки;
- `kappa` — локальная сила нелинейного фазового замка;
- `epsilon` — угол микроасимметрии;
- `delta_phi` — разность фаз встречных каналов.

Коэффициент `R` является локальным параметром фазовой поддержки.

Он не является общей эндогенной структурной когерентностью `C(t)`.

Множитель `sqrt(R)` изменяет амплитуду оператора парного замка, а не только его комплексную фазу.

## RU — Мультиплетный оператор U_6D

Три ортогональных оператора парного замка сворачиваются через произведение Кронекера:

`U_6D = L_1 ⊗ L_2 ⊗ L_3`

Каждый `L_k` является матрицей `2 × 2`.

Результирующий мультиплетный оператор:

`U_6D = комплексная матрица 8 × 8`

Название `U_6D` описывает мультиплет, собранный из трёх ортогональных двумерных фазовых плоскостей.

Текущая численная реализация не использует шесть независимых пространственных координат.

Поэтому обозначение `U_6D` определяет модельный слой и конструкцию мультиплетного оператора, а не шестикоординатную пространственную сетку.

## RU — Нормированная амплитуда фазового замка

Нормированная амплитуда фазового замка рассчитывается как:

`lock_amplitude = abs(Tr(U_6D)) / dimension(U_6D)`

Для текущего оператора:

`lock_amplitude = abs(Tr(U_6D)) / 8`

Нормирование позволяет сравнивать амплитуду фазового замка:

- между различными тактами симуляции;
- между различными координатами интерфейса;
- между различными локальными значениями фазовой поддержки.

Нормированная амплитуда замка является индикатором текущего мультиплетного фазового состояния.

Она не является общей эндогенной структурной когерентностью `C(t)`.

## RU — Локальное представление C^3

`C^3` определяется в архитектуре EDK как кубическое нелинейное насыщение, сжатие и задержка фазово-когерентной конфигурации.

Текущий визуализатор представляет кубическую амплитудную составляющую `C^3` через:

`C^3 = (psi_amplitude · lock_amplitude)^3`

Кубическое соотношение повышает чувствительность локального профиля `C^3` к снижению нормированной амплитуды фазового замка.

Локальная операционная цепочка:

снижение `lock_amplitude`  
→ более сильное относительное снижение `C^3`  
→ приближение к локальной границе перехода `C^3 / P_cubic`

Текущий визуализатор не реализует отдельное временное ядро задержки `C^3`.

Он визуализирует кубическую нелинейную амплитудную составляющую, используемую локальной интерфейсной моделью.

`C^3` не является общей эндогенной структурной когерентностью:

C(t) ≠ C^3

## RU — Локальный уровень кубической диссипации P_cubic

Локальный уровень кубической диссипации рассчитывается как:

`P_cubic = dissipation_coefficient · psi_amplitude^3`

`P_cubic` является локальным уровнем сравнения, используемым интерфейсной визуализацией.

Он не является общесистемным дестабилизующим давлением `P(t)`:

P(t) ≠ P_cubic

Локальные соотношения:

C^3 > P_cubic  
→ локальное доминирование C^3

C^3 = P_cubic  
→ локальная граница кубического перехода

C^3 < P_cubic  
→ локальное доминирование кубической диссипации

Эти соотношения описывают только локальный интерфейсный профиль.

Они не определяют самостоятельно эндогенную динамическую устойчивость или эндогенную динамическую критичность.

## RU — Самостоятельное общесистемное соотношение EDS / EDC

Модуль принимает самостоятельные параметры:

- `C_t` — общая эндогенная структурная когерентность `C(t)`;
- `P_t` — дестабилизующее давление `P(t)`.

Общесистемный режим классифицируется через:

C(t) > P(t)  
→ эндогенная динамическая устойчивость

C(t) = P(t)  
→ эндогенная динамическая критичность

C(t) < P(t)  
→ дрейф деградации

Метод `classify_system_regime()` выполняет эту классификацию независимо от локального профиля `C^3`.

Общесистемное соотношение нельзя выводить непосредственно из:

- нормированного следа `U_6D`;
- коэффициента фазовой поддержки `R`;
- локального профиля `C^3`;
- локального уровня кубической диссипации `P_cubic`.

## RU — Потактовая фазовая динамика

Временная симуляция начинается с трёх разностей фаз:

`current_phi = [0.8, -0.7, 0.5]`

Нелинейное возвращающее приращение:

`restoring_increment = -gamma · sin(current_phi) · dt`

Приращение внешнего диссипативного фазового шума:

`noise_increment = noise_strength · sqrt(dt) · normal_random_vector`

Обновление фазового состояния:

`current_phi(t + dt) = current_phi(t) + restoring_increment + noise_increment`

Каждый последующий такт наследует фазовое состояние, сформированное предшествующим тактом.

Это представляет рекурсивное наследование предшествующего фазового состояния внутри временного численного процесса.

Ожидаемый результат не является идеально статичным нулевым состоянием.

Ожидаемый результат — флуктуирующая динамически удерживаемая область вблизи фазового аттрактора.

Стохастическое приращение масштабируется через `sqrt(dt)`, чтобы изменение длительности такта не приводило к некорректному масштабированию шумового процесса.

## RU — Интерфейсный барьер

Пространственный профиль фазовой поддержки:

`R(X) = R_base - barrier_depth · exp(-((X - barrier_center) / barrier_width)^2)`

Вне барьера:

`R(X) ≈ R_base`

Внутри барьера:

`R(X)` снижается

После барьера:

`R(X)` восстанавливается

Профиль ограничивается интервалом:

`0 ≤ R(X) ≤ 1`

Локальная сила фазового замка:

`kappa_local = alpha_lock · R(X)`

Для каждой пространственной координаты модуль заново рассчитывает:

`R(X) → L_k(X) → U_6D(X) → lock_amplitude(X) → C^3(X)`

После этого локальный профиль `C^3` сравнивается с самостоятельным локальным профилем кубической диссипации:

`P_cubic(X)`

В текущей реализации `P_cubic(X)` является пространственно постоянным, если модель не расширена переменным профилем диссипации.

## RU — Координаты локального перехода

Модуль определяет координаты, в которых:

`C^3(X) - P_cubic(X) = 0`

Механизм определения точек перехода сохраняет:

- отсчёты с точным равенством;
- интервалы со сменой знака между соседними отсчётами.

Для интервала со сменой знака координата перехода оценивается линейной интерполяцией.

Полученные координаты представляют локальную численную границу:

`C^3 = P_cubic`

Они являются координатами локального кубического перехода.

Их нельзя отождествлять с общесистемной границей EDC:

`C(t) = P(t)`

Предыдущее имя поля `bifurcation_points` сохранено только как обратно совместимый псевдоним.

Операционное имя поля:

`cubic_transition_points`

## RU — Инженерные визуализации

Модуль формирует четыре инженерных графика.

### RU — 1. Потактовая динамика фазового рассогласования

Отображаются:

- `delta_phi_1(t)`;
- `delta_phi_2(t)`;
- `delta_phi_3(t)`.

График показывает взаимодействие:

- нелинейной возвращающей динамики;
- внешнего диссипативного фазового шума;
- рекурсивного наследования предшествующего фазового состояния.

### RU — 2. Траектория трёхплоскостного фазового пространства состояний

Отображается траектория:

`delta_phi_1, delta_phi_2, delta_phi_3`

График показывает:

- начальное состояние;
- промежуточную траекторию;
- конечное состояние.

Это фазовое пространство состояний численной системы.

Оно не является пространством обычных физических координат.

### RU — 3. Амплитуда замка U_6D и C^3

Отображаются:

`normalized abs(Tr(U_6D))`

и:

`C^3`

Нормированный след представляет текущую амплитуду мультиплетного фазового замка.

Кривая `C^3` представляет локальную кубическую нелинейную амплитуду, используемую визуализатором.

Ни одна из этих величин не является общей эндогенной структурной когерентностью `C(t)`.

### RU — 4. Локальный интерфейсный переход C^3 / P_cubic

Отображаются:

`C^3(X)`

и:

`P_cubic(X)`

Локальная область доминирования `C^3`:

`C^3 > P_cubic`

Локальная область доминирования кубической диссипации:

`C^3 < P_cubic`

Вертикальные маркеры показывают приближённые координаты локального перехода:

`C^3 = P_cubic`

В графическом блоке отдельно отображаются самостоятельные общесистемные значения:

- `C(t)`;
- `P(t)`;
- классифицированный общесистемный режим.

## RU — Исправление исходной конструкции следа

Исходная конструкция использовала один общий комплексный множитель:

`L_k = exp(i · phase_angle) · H_asym`

Общий фазовый множитель изменяет фазу следа, но не обязательно изменяет:

`abs(Tr(L_k))`

Та же проблема переходит в:

`abs(Tr(U_6D))`

Исправленный модуль использует:

- встречные фазовые направления `exp(+i · phase_angle)` и `exp(-i · phase_angle)`;
- самостоятельную амплитуду фазовой поддержки `sqrt(R)`.

Теперь абсолютный след может реагировать на:

- фазовое рассогласование;
- локальную силу нелинейного сопряжения;
- коэффициент фазовой поддержки;
- глубину интерфейсного барьера.

## RU — Размерностная интерпретация

Текущий модуль явно реализует:

- три разности фаз;
- три оператора парного замка `2 × 2`;
- один комплексный тензорно-произведённый оператор `8 × 8`;
- одну временную координату;
- одну пространственную координату интерфейса;
- одну самостоятельную общесистемную пару `C(t)` и `P(t)`.

Обозначения `2D`, `4D`, `5D`, `6D` и `7D` определяют модельные слои, если соответствующие независимые математические координаты не реализованы непосредственно.

Модуль нельзя интерпретировать как прямую численную реализацию шести или семи независимых пространственных координат.

## RU — Основные инварианты

Локальный мультиплетный инвариант:

`потактовое удержание фазового замка представлено динамически изменяющимся мультиплетным состоянием, нормированная амплитуда фазового замка которого формирует локальный профиль C^3`

Локальное интерфейсное соотношение:

C^3 > P_cubic  
→ локальное доминирование C^3

C^3 = P_cubic  
→ локальная граница кубического перехода

C^3 < P_cubic  
→ локальное доминирование кубической диссипации

Общесистемное соотношение:

C(t) > P(t)  
→ эндогенная динамическая устойчивость

C(t) = P(t)  
→ эндогенная динамическая критичность

C(t) < P(t)  
→ дрейф деградации

Обязательные различия:

C(t) ≠ C^3

P(t) ≠ P_cubic

R(n) ≠ C(t)

Локальное интерфейсное соотношение и общесистемное соотношение не являются взаимозаменяемыми.

## RU — Основной класс

`MarnovCubicPotentialVisualizer`

## RU — Основные методы

- `set_system_state()` — задаёт самостоятельные общесистемные параметры `C(t)` и `P(t)`.
- `classify_system_regime()` — классифицирует самостоятельное общесистемное соотношение EDS / EDC.
- `build_pair_lock()` — формирует один комплексный оператор парного замка `2 × 2`.
- `calculate_u_6d()` — сворачивает три оператора парного замка в один мультиплетный оператор `8 × 8`.
- `calculate_lock_amplitude()` — рассчитывает нормированный абсолютный след.
- `calculate_cubic_potential()` — рассчитывает локальное представление `C^3`.
- `calculate_cubic_dissipation_level()` — рассчитывает локальный уровень кубической диссипации `P_cubic`.
- `simulate_temporal_dynamics()` — моделирует потактовую фазовую динамику.
- `calculate_interface_profile()` — рассчитывает локальный интерфейсный профиль.
- `visualize_engineering_data()` — формирует четыре инженерных графика.
- `run_visual_simulation()` — запускает полную симуляцию и визуализацию.
