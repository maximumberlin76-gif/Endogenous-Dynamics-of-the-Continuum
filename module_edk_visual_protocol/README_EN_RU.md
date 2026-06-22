# Marnov U_6D / C3 Engineering Visual Simulator

## Engineering Visualization of Tact-by-Tact Phase Retention and Interface Bifurcation

The `MarnovCubicPotentialVisualizer` module implements an engineering visual simulator for:

- tact-by-tact phase-mismatch dynamics;
- three-plane phase-space trajectories;
- the tensor-product multiplet operator `U_6D`;
- the normalized phase-lock amplitude;
- the cubic retention potential `C3`;
- the EDS retention criterion at an interface-density barrier.

The module combines temporal phase dynamics with spatial analysis of a transition through an interface barrier.

## Module File

`module_edk_visual_protocol/marnov_cubic_potential_visualizer.py`

## Dependencies

- `numpy>=1.26.0`
- `matplotlib>=3.8.0`

## Installation

    pip install -r requirements.txt

## Launch

    python module_edk_visual_protocol/marnov_cubic_potential_visualizer.py

## Core Operational Chain

    three orthogonal 2D phase planes
    → pair-lock operators L_k
    → tensor-product operator U_6D
    → normalized phase-lock amplitude
    → cubic retention potential C3
    → comparison with environmental dissipation P
    → retention domain C3 > P
    → bifurcation boundary C3 = P
    → breakdown domain C3 <= P

## Pair-Lock Operator

Each two-dimensional phase plane is represented by one complex `2 × 2` pair-lock operator.

The local phase angle is:

    phase_angle =
    kappa · sin(delta_phi)

The two counter-directed channels use opposite phase directions:

    phase_operator =
    [
        exp(+i · phase_angle)    0
        0                        exp(-i · phase_angle)
    ]

The micro-asymmetry operator is:

    asymmetry_operator =
    [
         cos(epsilon)    sin(epsilon)
        -sin(epsilon)    cos(epsilon)
    ]

The complete pair-lock operator is:

    L_k =
    sqrt(R)
    · phase_operator
    · asymmetry_operator

Where:

- `R` is the local coherence-support parameter;
- `kappa` is the local phase-lock strength;
- `epsilon` is the micro-asymmetry angle;
- `delta_phi` is the phase difference between counter-directed channels.

## Multiplet Operator U_6D

Three orthogonal pair-lock operators are contracted through the Kronecker product:

    U_6D =
    L_1 ⊗ L_2 ⊗ L_3

Each `L_k` is a `2 × 2` matrix.

The resulting multiplet operator is therefore:

    U_6D = complex 8 × 8 matrix

The name `U_6D` describes a multiplet assembled from three orthogonal two-dimensional phase planes.

The current numerical implementation does not use six independent spatial coordinates.

## Normalized Phase-Lock Amplitude

The phase-lock amplitude is calculated as:

    lock_amplitude =
    abs(Tr(U_6D))
    / dimension(U_6D)

For the current operator:

    lock_amplitude =
    abs(Tr(U_6D))
    / 8

Normalization allows the retained phase-lock amplitude to be compared across different simulation tacts and interface positions.

## Cubic Retention Potential C3

The cubic retention potential is:

    C3 =
    psi_amplitude^2
    · lock_amplitude^3

The cubic exponent makes `C3` more sensitive to reductions in the retained phase-lock amplitude.

The operational chain is:

    decrease of lock_amplitude
    → stronger relative decrease of C3
    → approach to the EDS critical boundary

## Environmental Dissipation P

The environmental dissipation level is:

    P =
    dissipation_coefficient
    · psi_amplitude^3

The EDS conditions are:

    C3 > P
    → retained dynamic contour

    C3 = P
    → bifurcation boundary

    C3 <= P
    → breakdown of the retained contour

## Tact-by-Tact Phase Dynamics

The temporal simulation begins from three phase differences:

    current_phi =
    [
         0.8,
        -0.7,
         0.5
    ]

The nonlinear restoring increment is:

    restoring_increment =
    -gamma
    · sin(current_phi)
    · dt

The external dissipative-noise increment is:

    noise_increment =
    noise_strength
    · sqrt(dt)
    · normal_random_vector

The phase state is updated as:

    current_phi(t + dt) =
    current_phi(t)
    + restoring_increment
    + noise_increment

Each subsequent tact inherits the phase state produced by the preceding tact.

The expected result is not an ideal static zero state.

The expected result is a fluctuating dynamically retained domain near the phase attractor.

## Interface-Density Barrier

The spatial support profile is:

    R(X) =
    R_base
    - barrier_depth
    · exp(
        -((X - barrier_center) / barrier_width)^2
    )

Outside the barrier:

    R(X) ≈ R_base

Inside the barrier:

    R(X) decreases

After the barrier:

    R(X) recovers

The local phase-lock strength is:

    kappa_local =
    alpha_lock
    · R(X)

For every spatial coordinate, the module recalculates:

    R(X)
    → L_k(X)
    → U_6D(X)
    → lock_amplitude(X)
    → C3(X)

## Bifurcation Coordinates

The module detects locations where:

    C3(X) - P(X)

changes sign.

The crossing coordinate is estimated through linear interpolation between neighboring spatial samples.

The resulting points represent the numerical boundary:

    C3 = P

## Engineering Visualizations

The module generates four graphs.

### 1. Tact-by-Tact Phase-Mismatch Dynamics

Displays:

- `delta_phi_1(t)`;
- `delta_phi_2(t)`;
- `delta_phi_3(t)`.

The graph shows the interaction between nonlinear restoring dynamics and external dissipative noise.

### 2. Three-Plane Phase-Space Trajectory

Displays the trajectory:

    delta_phi_1
    delta_phi_2
    delta_phi_3

The graph marks the initial state, intermediate trajectory, and final state.

This is a state-space graph, not a graph of ordinary physical coordinates.

### 3. U_6D Lock Amplitude and C3 Potential

Displays:

    normalized abs(Tr(U_6D))

and:

    C3

The normalized trace describes the retained multiplet phase-lock amplitude.

The cubic potential describes its nonlinear retention capacity.

### 4. EDS Criterion Across the Interface Barrier

Displays:

    C3(X)
    P(X)

The graph separates:

    retention domain:
    C3 > P

    breakdown domain:
    C3 <= P

Vertical markers show the approximate bifurcation coordinates:

    C3 = P

## Correction of the Original Trace Construction

The original construction used one common complex multiplier:

    L_k =
    exp(i · phase_angle)
    · H_asym

A common phase multiplier changes the phase of the trace but does not necessarily change:

    abs(Tr(L_k))

The same problem propagates into:

    abs(Tr(U_6D))

The corrected module uses:

- opposite phase directions `exp(+i · phase_angle)` and `exp(-i · phase_angle)`;
- a separate support amplitude `sqrt(R)`.

The absolute trace can therefore respond to:

- phase mismatch;
- local coupling strength;
- coherence support;
- interface-barrier depth.

## Dimensional Interpretation

The current module explicitly implements:

- three phase differences;
- three `2 × 2` pair-lock operators;
- one complex `8 × 8` tensor-product operator;
- one temporal coordinate;
- one spatial interface coordinate.

The labels `2D`, `4D`, `5D`, `6D`, and `7D` are model-layer designations unless corresponding independent mathematical coordinates are implemented directly.

## Core Invariant

    phase-lock retention =
    a tact-by-tact dynamically retained multiplet state
    in which the cubic potential generated by coupled phase planes
    remains greater than environmental dissipation
    inside the open nonlinear dissipative dynamic Continuum

Operational condition:

    C3 > P

Critical boundary:

    C3 = P

Breakdown condition:

    C3 <= P

## Main Class

`MarnovCubicPotentialVisualizer`

## Main Methods

- `build_pair_lock()` — builds one complex `2 × 2` pair-lock operator.
- `calculate_u_6d()` — contracts three pair locks into the `8 × 8` multiplet operator.
- `calculate_lock_amplitude()` — calculates the normalized absolute trace.
- `calculate_cubic_potential()` — calculates the cubic retention potential `C3`.
- `simulate_temporal_dynamics()` — simulates tact-by-tact phase dynamics.
- `calculate_interface_profile()` — calculates the interface-retention profile.
- `visualize_engineering_data()` — generates four engineering graphs.
- `run_visual_simulation()` — runs the complete simulation.

---

# Инженерный визуальный симулятор U_6D / C3 Протокола Марнова

## Инженерная визуализация потактового фазового удержания и интерфейсной бифуркации

Модуль `MarnovCubicPotentialVisualizer` реализует инженерный визуальный симулятор:

- потактовой динамики фазового рассогласования;
- траектории трёхплоскостного фазового пространства;
- тензорно-произведённого мультиплетного оператора `U_6D`;
- нормированной амплитуды фазового замка;
- кубического потенциала удержания `C3`;
- критерия EDS при прохождении барьера плотности на границе раздела сред.

Модуль объединяет временную фазовую динамику и пространственный анализ перехода через интерфейсный барьер.

## Файл модуля

`module_edk_visual_protocol/marnov_cubic_potential_visualizer.py`

## Зависимости

- `numpy>=1.26.0`
- `matplotlib>=3.8.0`

## Установка

    pip install -r requirements.txt

## Запуск

    python module_edk_visual_protocol/marnov_cubic_potential_visualizer.py

## Основная операционная цепочка

    три ортогональные двумерные фазовые плоскости
    → операторы парного замка L_k
    → тензорно-произведённый оператор U_6D
    → нормированная амплитуда фазового замка
    → кубический потенциал удержания C3
    → сравнение с диссипацией среды P
    → область удержания C3 > P
    → граница бифуркации C3 = P
    → область срыва C3 <= P

## Оператор парного замка

Каждая двумерная фазовая плоскость представлена одним комплексным оператором парного замка размерностью `2 × 2`.

Локальный фазовый угол:

    phase_angle =
    kappa · sin(delta_phi)

Два встречных канала используют противоположные фазовые направления:

    phase_operator =
    [
        exp(+i · phase_angle)    0
        0                        exp(-i · phase_angle)
    ]

Оператор микроасимметрии:

    asymmetry_operator =
    [
         cos(epsilon)    sin(epsilon)
        -sin(epsilon)    cos(epsilon)
    ]

Полный оператор парного замка:

    L_k =
    sqrt(R)
    · phase_operator
    · asymmetry_operator

Где:

- `R` — локальный параметр поддержки когерентности;
- `kappa` — локальная сила фазового замка;
- `epsilon` — угол микроасимметрии;
- `delta_phi` — разность фаз встречных каналов.

Множитель `sqrt(R)` изменяет амплитуду оператора парного замка, а не только его комплексную фазу.

## Мультиплетный оператор U_6D

Три ортогональных оператора парного замка сворачиваются через произведение Кронекера:

    U_6D =
    L_1 ⊗ L_2 ⊗ L_3

Каждый `L_k` является матрицей `2 × 2`.

Результирующий мультиплетный оператор:

    U_6D = комплексная матрица 8 × 8

Название `U_6D` описывает мультиплет, собранный из трёх ортогональных двумерных фазовых плоскостей.

Текущая численная реализация не использует шесть независимых пространственных координат.

## Нормированная амплитуда фазового замка

Амплитуда фазового замка рассчитывается как:

    lock_amplitude =
    abs(Tr(U_6D))
    / dimension(U_6D)

Для текущего оператора:

    lock_amplitude =
    abs(Tr(U_6D))
    / 8

Нормирование позволяет сравнивать удерживаемую амплитуду фазового замка на различных тактах симуляции и в различных точках интерфейса.

## Кубический потенциал удержания C3

Кубический потенциал удержания:

    C3 =
    psi_amplitude^2
    · lock_amplitude^3

Кубическая степень повышает чувствительность `C3` к снижению удерживаемой амплитуды фазового замка.

Операционная цепочка:

    снижение lock_amplitude
    → более сильное относительное снижение C3
    → приближение к критической границе EDS

## Диссипация среды P

Уровень диссипации среды:

    P =
    dissipation_coefficient
    · psi_amplitude^3

Условия EDS:

    C3 > P
    → динамический контур удерживается

    C3 = P
    → граница бифуркации

    C3 <= P
    → срыв удерживаемого контура

## Потактовая фазовая динамика

Временная симуляция начинается с трёх разностей фаз:

    current_phi =
    [
         0.8,
        -0.7,
         0.5
    ]

Нелинейное возвращающее приращение:

    restoring_increment =
    -gamma
    · sin(current_phi)
    · dt

Приращение внешнего диссипативного шума:

    noise_increment =
    noise_strength
    · sqrt(dt)
    · normal_random_vector

Обновление фазового состояния:

    current_phi(t + dt) =
    current_phi(t)
    + restoring_increment
    + noise_increment

Каждый последующий такт наследует фазовое состояние, сформированное предшествующим тактом.

Ожидаемый результат не является идеальным статичным нулевым состоянием.

Ожидаемый результат — флуктуирующая динамически удерживаемая область вблизи фазового аттрактора.

## Интерфейсный барьер плотности

Пространственный профиль поддержки:

    R(X) =
    R_base
    - barrier_depth
    · exp(
        -((X - barrier_center) / barrier_width)^2
    )

Вне барьера:

    R(X) ≈ R_base

Внутри барьера:

    R(X) снижается

После барьера:

    R(X) восстанавливается

Локальная сила фазового замка:

    kappa_local =
    alpha_lock
    · R(X)

Для каждой пространственной координаты модуль заново рассчитывает:

    R(X)
    → L_k(X)
    → U_6D(X)
    → lock_amplitude(X)
    → C3(X)

## Координаты бифуркации

Модуль определяет точки, где выражение:

    C3(X) - P(X)

меняет знак.

Координата пересечения оценивается линейной интерполяцией между соседними пространственными отсчётами.

Полученные точки представляют численную границу:

    C3 = P

## Инженерные визуализации

Модуль формирует четыре графика.

### 1. Потактовая динамика фазового рассогласования

Отображаются:

- `delta_phi_1(t)`;
- `delta_phi_2(t)`;
- `delta_phi_3(t)`.

График показывает взаимодействие нелинейной возвращающей динамики и внешнего диссипативного шума.

### 2. Траектория трёхплоскостного фазового пространства

Отображается траектория:

    delta_phi_1
    delta_phi_2
    delta_phi_3

График показывает начальное состояние, промежуточную траекторию и конечное состояние.

Это пространство состояний системы, а не пространство обычных физических координат.

### 3. Амплитуда замка U_6D и потенциал C3

Отображаются:

    normalized abs(Tr(U_6D))

и:

    C3

Нормированный след описывает удерживаемую амплитуду мультиплетного фазового замка.

Кубический потенциал описывает его нелинейную способность удержания.

### 4. Критерий EDS на интерфейсном барьере

Отображаются:

    C3(X)
    P(X)

Область удержания:

    C3 > P

Область срыва:

    C3 <= P

Вертикальные маркеры показывают приближённые координаты бифуркации:

    C3 = P

## Исправление исходной конструкции следа

Исходная конструкция использовала один общий комплексный множитель:

    L_k =
    exp(i · phase_angle)
    · H_asym

Общий фазовый множитель изменяет фазу следа, но не обязательно изменяет:

    abs(Tr(L_k))

Та же проблема переходила в:

    abs(Tr(U_6D))

Исправленный модуль использует:

- встречные фазовые направления `exp(+i · phase_angle)` и `exp(-i · phase_angle)`;
- отдельную амплитуду поддержки `sqrt(R)`.

Теперь абсолютный след реагирует на:

- фазовое рассогласование;
- локальную силу сопряжения;
- поддержку когерентности;
- глубину интерфейсного барьера.

## Размерностная интерпретация

Текущий модуль явно реализует:

- три разности фаз;
- три оператора парного замка `2 × 2`;
- один комплексный тензорно-произведённый оператор `8 × 8`;
- одну временную координату;
- одну пространственную координату интерфейса.

Обозначения `2D`, `4D`, `5D`, `6D` и `7D` являются обозначениями модельных слоёв, если соответствующие независимые математические координаты не реализованы непосредственно.

## Основной инвариант

    удержание фазового замка =
    потактово динамически удерживаемое мультиплетное состояние,
    в котором кубический потенциал сопряжённых фазовых плоскостей
    остаётся выше диссипации среды
    внутри открытого нелинейного диссипативного динамического Континуума

Условие удержания:

    C3 > P

Критическая граница:

    C3 = P

Условие срыва:

    C3 <= P

## Основной класс

`MarnovCubicPotentialVisualizer`

## Основные методы

- `build_pair_lock()` — формирует комплексный оператор парного замка `2 × 2`.
- `calculate_u_6d()` — сворачивает три парных замка в мультиплетный оператор `8 × 8`.
- `calculate_lock_amplitude()` — рассчитывает нормированный абсолютный след.
- `calculate_cubic_potential()` — рассчитывает кубический потенциал `C3`.
- `simulate_temporal_dynamics()` — моделирует потактовую фазовую динамику.
- `calculate_interface_profile()` — рассчитывает профиль прохождения интерфейсного барьера.
- `visualize_engineering_data()` — формирует четыре инженерных графика.
- `run_visual_simulation()` — запускает полную симуляцию.

