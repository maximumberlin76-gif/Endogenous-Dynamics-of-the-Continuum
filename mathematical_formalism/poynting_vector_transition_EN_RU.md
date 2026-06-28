# Poynting-Vector Transition Formalism

## From U_6D / C^3 Internal Retention to Directed 1D Energy Flux

## English Version

## 1. Scope

This formalism describes the transition from an internally retained multiplet phase-lock state to a directed axial energy-flux state.

The operational chain is:

    three orthogonal phase planes
    → pair-lock operators L_k
    → multiplet operator U_6D
    → normalized lock amplitude A_lock
    → cubic retention potential C^3
    → controlled phase opening
    → directed axial flux S_1D

Within this formalism:

- `U_6D` describes the coupled multiplet phase-lock operator;
- `A_lock` describes the normalized retained phase-lock amplitude;
- `C^3` describes the cubic retention potential;
- `P` describes environmental dissipation;
- `g_open` describes the controlled opening of the retained contour;
- `S_1D` describes the directed axial output-flux density.

`C^3` must not be confused with the general endogenous structural coherence `C(t)`.

## 2. Pair-Lock Operator

For each orthogonal phase plane `k`:

    theta_k =
    kappa_k · sin(delta_phi_k)

The counter-directed phase operator is:

    D_k =
    diag(
        exp(+i · theta_k),
        exp(-i · theta_k)
    )

The controlled asymmetry operator is:

    H_epsilon =
    [
         cos(epsilon)    sin(epsilon)
        -sin(epsilon)    cos(epsilon)
    ]

The complete pair-lock operator is:

    L_k =
    sqrt(R_k)
    · D_k
    · H_epsilon

Where:

- `delta_phi_k` is the phase difference in plane `k`;
- `kappa_k` is the local phase-lock strength;
- `R_k` is the local coherence-support parameter;
- `epsilon` is the controlled asymmetry or eccentricity parameter.

## 3. Multiplet Operator U_6D

The three pair-lock operators are contracted through the Kronecker product:

    U_6D =
    L_1 ⊗ L_2 ⊗ L_3

Since every `L_k` is a `2 × 2` matrix:

    U_6D =
    complex 8 × 8 operator

The normalized phase-lock amplitude is:

    A_lock =
    abs(Tr(U_6D))
    / 8

The retained phase-lock domain corresponds to comparatively high `A_lock`.

## 4. Cubic Retention Potential C^3

The cubic retention potential is defined as:

    C^3 =
    abs(Psi)^2
    · A_lock^3

Where:

- `Psi` is the amplitude of the retained state;
- `A_lock^3` represents cubic nonlinear saturation of the retained multiplet lock.

The EDS comparison is:

    C^3 > P
    → retained dynamic domain

    C^3 = P
    → critical boundary

    C^3 < P
    → breakdown tendency

The condition `C^3 > P` does not require the output flux to be zero. A controlled output can occur while the retained domain remains above the critical boundary.

## 5. Physical Poynting Vector

In standard electromagnetic theory, the Poynting vector is:

    S_EM =
    E × H

Its axial component is:

    S_axis =
    (E × H) · n_axis

Where:

- `E` is the electric-field vector;
- `H` is the magnetic-field vector;
- `n_axis` is the selected output-axis unit vector.

Therefore, a calculated quantity may be called a physical Poynting flux only when the corresponding `E` and `H` fields are explicitly defined.

## 6. Reduced EDK Output-Flux Model

When explicit electromagnetic fields are not yet calculated, the transition from retained `C^3` to directed output is represented by a reduced output-flux proxy.

The normalized phase-opening gradient is:

    G_phi =
    sqrt(
        sin(delta_phi_1)^2
        + sin(delta_phi_2)^2
        + sin(delta_phi_3)^2
    )
    / sqrt(3)

Therefore:

    0 <= G_phi <= 1

The controlled opening function is:

    g_open =
    clip(
        beta_phi · G_phi
        + beta_epsilon · abs(epsilon - epsilon_0),
        0,
        1
    )

Where:

- `epsilon_0` is the retained equilibrium eccentricity;
- `beta_phi` controls sensitivity to phase mismatch;
- `beta_epsilon` controls sensitivity to eccentricity displacement.

The directed axial output-flux density is:

    S_1D =
    eta_release
    · C^3
    · g_open

The corresponding directed vector is:

    S_model =
    S_1D
    · n_axis

This is a reduced EDK output-flux model.

It becomes equivalent to the axial electromagnetic Poynting flux only when:

    S_1D =
    (E × H) · n_axis

## 7. Internal Circulation and Axial Release

The total flux can be decomposed into an internally circulating toroidal component and an externally directed axial component:

    S_total =
    S_toroidal · e_theta
    + S_1D · n_axis

Where:

- `S_toroidal` describes circulation inside the retained topology;
- `e_theta` is the local toroidal-direction unit vector;
- `S_1D` describes directed axial release;
- `n_axis` is the axial-output unit vector.

In the closed retained state:

    g_open ≈ 0

Therefore:

    S_1D ≈ 0

and the dominant flux remains internally circulating:

    S_total ≈
    S_toroidal · e_theta

After a controlled phase displacement:

    G_phi increases
    → g_open increases
    → S_1D increases

As the nonlinear phase-lock dynamics restore the phase differences:

    G_phi decreases
    → g_open decreases
    → S_1D decreases

## 8. Retained-Energy Balance

The retained energy balance is:

    dE_ret / dt =
    P_in
    - P_diss
    - A_out · S_1D

Where:

- `E_ret` is the retained internal energy;
- `P_in` is input power;
- `P_diss` is internal dissipative loss;
- `A_out` is the effective output area;
- `S_1D` is the axial output-flux density.

A directed output therefore reduces the retained energy unless it is compensated by input power or positive structural work.

## 9. Operational Regimes

### Closed Retention

    C^3 > P
    g_open ≈ 0
    S_1D ≈ 0

The phase-lock domain is retained and the dominant flux circulates internally.

### Controlled Directed Release

    C^3 > P
    0 < g_open < 1
    S_1D > 0

The retained contour remains dynamically supported while part of the accumulated potential is released along the selected axis.

### Critical Boundary

    C^3 = P

The retained domain reaches its critical boundary.

Further output or external pressure can initiate a phase transition toward breakdown.

### Breakdown

    C^3 < P

Environmental dissipation exceeds the cubic retention potential.

The retained phase-lock contour loses its capacity to preserve the previous qualitative characteristics.

## 10. Core Invariant

    directed axial output =
    controlled conversion of part of the retained cubic potential C^3
    into an axial flux through a phase-opening function,
    while the retained domain remains dynamically sustainable
    only as long as C^3 remains above environmental dissipation P

The complete operational chain is:

    U_6D phase lock
    → A_lock
    → C^3
    → controlled phase displacement
    → G_phi
    → g_open
    → S_1D
    → restoration or breakdown of the retained contour

## 11. Position in the EDK Architecture

    pair-lock operators L_k
    → U_6D
    → A_lock
    → C^3
    → phase-opening control
    → directed output-flux density S_1D
    → J_flux / energy redistribution layer
    → restoration, continued release, or breakdown

---

# Формализм перехода вектора Пойнтинга

## От внутреннего удержания U_6D / C^3 к направленному одномерному потоку энергии

## Русская версия

## 1. Область формализма

Данный формализм описывает переход от внутренне удерживаемого мультиплетного состояния фазового замка к направленному осевому потоку энергии.

Операционная цепочка:

    три ортогональные фазовые плоскости
    → операторы парного замка L_k
    → мультиплетный оператор U_6D
    → нормированная амплитуда замка A_lock
    → кубический потенциал удержания C^3
    → управляемое открытие фазового контура
    → направленный осевой поток S_1D

Внутри данного формализма:

- `U_6D` описывает сопряжённый мультиплетный оператор фазового замка;
- `A_lock` описывает нормированную удерживаемую амплитуду фазового замка;
- `C^3` описывает кубический потенциал удержания;
- `P` описывает диссипацию среды;
- `g_open` описывает управляемое открытие удерживаемого контура;
- `S_1D` описывает плотность направленного осевого выходного потока.

`C^3` нельзя смешивать с общей эндогенной структурной когерентностью `C(t)`.

## 2. Оператор парного замка

Для каждой ортогональной фазовой плоскости `k`:

    theta_k =
    kappa_k · sin(delta_phi_k)

Оператор встречных фазовых направлений:

    D_k =
    diag(
        exp(+i · theta_k),
        exp(-i · theta_k)
    )

Оператор управляемой асимметрии:

    H_epsilon =
    [
         cos(epsilon)    sin(epsilon)
        -sin(epsilon)    cos(epsilon)
    ]

Полный оператор парного замка:

    L_k =
    sqrt(R_k)
    · D_k
    · H_epsilon

Где:

- `delta_phi_k` — разность фаз в плоскости `k`;
- `kappa_k` — локальная сила фазового замка;
- `R_k` — локальный параметр поддержки когерентности;
- `epsilon` — параметр управляемой асимметрии или эксцентриситета.

## 3. Мультиплетный оператор U_6D

Три оператора парного замка сворачиваются через произведение Кронекера:

    U_6D =
    L_1 ⊗ L_2 ⊗ L_3

Поскольку каждый `L_k` является матрицей `2 × 2`:

    U_6D =
    комплексный оператор 8 × 8

Нормированная амплитуда фазового замка:

    A_lock =
    abs(Tr(U_6D))
    / 8

Удерживаемая фазовая область соответствует сравнительно высокому значению `A_lock`.

## 4. Кубический потенциал удержания C^3

Кубический потенциал удержания определяется как:

    C^3 =
    abs(Psi)^2
    · A_lock^3

Где:

- `Psi` — амплитуда удерживаемого состояния;
- `A_lock^3` — кубическое нелинейное насыщение удерживаемого мультиплетного замка.

Сравнение EDS:

    C^3 > P
    → удерживаемая динамическая область

    C^3 = P
    → критическая граница

    C^3 < P
    → тенденция к срыву

Условие `C^3 > P` не требует полного отсутствия выходного потока. Управляемый выход может происходить, пока удерживаемая область остаётся выше критической границы.

## 5. Физический вектор Пойнтинга

В стандартной электродинамике вектор Пойнтинга определяется как:

    S_EM =
    E × H

Его осевая компонента:

    S_axis =
    (E × H) · n_axis

Где:

- `E` — вектор электрического поля;
- `H` — вектор магнитного поля;
- `n_axis` — единичный вектор выбранной оси выхода.

Следовательно, рассчитанная величина может называться физическим потоком Пойнтинга только при явном определении соответствующих полей `E` и `H`.

## 6. Редуцированная модель выходного потока EDK

Если электромагнитные поля ещё не рассчитываются явно, переход от удерживаемого `C^3` к направленному выходу представляется редуцированным прокси-параметром выходного потока.

Нормированный градиент фазового открытия:

    G_phi =
    sqrt(
        sin(delta_phi_1)^2
        + sin(delta_phi_2)^2
        + sin(delta_phi_3)^2
    )
    / sqrt(3)

Следовательно:

    0 <= G_phi <= 1

Функция управляемого открытия:

    g_open =
    clip(
        beta_phi · G_phi
        + beta_epsilon · abs(epsilon - epsilon_0),
        0,
        1
    )

Где:

- `epsilon_0` — равновесный эксцентриситет удерживаемого состояния;
- `beta_phi` — чувствительность к фазовому рассогласованию;
- `beta_epsilon` — чувствительность к смещению эксцентриситета.

Плотность направленного осевого выходного потока:

    S_1D =
    eta_release
    · C^3
    · g_open

Соответствующий направленный вектор:

    S_model =
    S_1D
    · n_axis

Это редуцированная модель выходного потока EDK.

Она становится эквивалентной осевому электромагнитному потоку Пойнтинга только при условии:

    S_1D =
    (E × H) · n_axis

## 7. Внутренняя циркуляция и осевой выход

Полный поток может быть разложен на внутренне циркулирующую тороидальную компоненту и внешнюю направленную осевую компоненту:

    S_total =
    S_toroidal · e_theta
    + S_1D · n_axis

Где:

- `S_toroidal` описывает циркуляцию внутри удерживаемой топологии;
- `e_theta` — единичный вектор локального тороидального направления;
- `S_1D` описывает направленный осевой выход;
- `n_axis` — единичный вектор оси выхода.

В закрытом удерживаемом состоянии:

    g_open ≈ 0

Следовательно:

    S_1D ≈ 0

Доминирующий поток остаётся внутренне циркулирующим:

    S_total ≈
    S_toroidal · e_theta

После управляемого фазового смещения:

    G_phi возрастает
    → g_open возрастает
    → S_1D возрастает

По мере того как нелинейная динамика фазового замка восстанавливает разности фаз:

    G_phi снижается
    → g_open снижается
    → S_1D снижается

## 8. Баланс удерживаемой энергии

Баланс удерживаемой энергии:

    dE_ret / dt =
    P_in
    - P_diss
    - A_out · S_1D

Где:

- `E_ret` — внутренняя удерживаемая энергия;
- `P_in` — входная мощность;
- `P_diss` — внутренние диссипативные потери;
- `A_out` — эффективная площадь выхода;
- `S_1D` — плотность осевого выходного потока.

Направленный выход уменьшает удерживаемую энергию, если он не компенсируется входной мощностью или положительной структурной работой.

## 9. Операционные состояния

### Закрытое удержание

    C^3 > P
    g_open ≈ 0
    S_1D ≈ 0

Фазовая область удерживается, а доминирующий поток циркулирует внутри неё.

### Управляемый направленный выход

    C^3 > P
    0 < g_open < 1
    S_1D > 0

Удерживаемый контур остаётся динамически поддерживаемым, при этом часть накопленного потенциала выводится вдоль выбранной оси.

### Критическая граница

    C^3 = P

Удерживаемая область достигает критической границы.

Дальнейший выход или рост внешнего давления может инициировать фазовый переход к срыву.

### Срыв

    C^3 < P

Диссипация среды превышает кубический потенциал удержания.

Удерживаемый фазовый контур теряет способность сохранять предшествующие качественные характеристики.

## 10. Основной инвариант

    направленный осевой выход =
    управляемое преобразование части удерживаемого кубического потенциала C^3
    в осевой поток через функцию фазового открытия,
    при этом удерживаемая область остаётся динамически устойчивой
    только пока C^3 остаётся выше диссипации среды P

Полная операционная цепочка:

    фазовый замок U_6D
    → A_lock
    → C^3
    → управляемое фазовое смещение
    → G_phi
    → g_open
    → S_1D
    → восстановление или срыв удерживаемого контура

## 11. Место в архитектуре EDK

    операторы парного замка L_k
    → U_6D
    → A_lock
    → C^3
    → управление фазовым открытием
    → плотность направленного потока S_1D
    → слой J_flux / перераспределения энергии
    → восстановление, продолжение выхода или срыв
