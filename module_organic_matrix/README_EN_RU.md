# Marnov Organic Matrix Generator

## Three-Dimensional Recursive Growth of an Organic Matrix in an Asymmetric C3 Retention Field

The `MarnovOrganicMatrixGenerator` module implements a conceptual numerical model of recursive tact-by-tact growth of a three-dimensional organic-density matrix.

The model begins with a central initiation point and an asymmetric toroidal cubic-retention field `C3`.

The organic-density field develops through the interaction of:

- a central initiation point;
- an asymmetric toroidal retention field;
- nonlinear spatial diffusion;
- density-limited local growth;
- nonlinear saturation;
- recursive phase-shifted branching;
- an organic manifestation layer.

The module is a numerical experimental model. It does not simulate a complete living organism and does not by itself prove a physical theory of life.

## File

`module_organic_matrix/marnov_organic_matrix_generator.py`

## Dependencies

- `numpy>=1.26.0`
- `matplotlib>=3.8.0`

## Installation

Run from the repository root:

    pip install -r requirements.txt

## Launch

    python module_organic_matrix/marnov_organic_matrix_generator.py

## Core Operational Chain

    central initiation point
    → asymmetric toroidal C3 field
    → nonlinear spatial diffusion
    → retained local growth
    → nonlinear saturation
    → recursive phase-shifted branching
    → bio_density
    → organic_appearance_index

## 1. Central Initiation Point

The initial state contains one active central cell:

    bio_density[center, center, center] = 1

This cell functions as:

- an ancestor cell;
- an initial local wave focus;
- a trigger of spatial density propagation;
- a local anchor of the developing organic matrix.

The resulting structure is not generated exclusively by the central cell.

The distributed `C3` field also creates spatial regions of retention and local density growth around the toroidal core.

## 2. Asymmetric Toroidal C3 Field

The method `generate_asymmetric_c3_field()` generates the three-dimensional toroidal retention field.

The radial distance in the horizontal plane is:

    radial_distance =
    sqrt(x_offset^2 + y_offset^2)

The distance from each spatial point to the toroidal core line is:

    toroidal_distance =
    sqrt(
        (radial_distance - torus_radius)^2
        + z_offset^2
    )

The Gaussian toroidal envelope is:

    toroidal_envelope =
    exp(
        -toroidal_distance^2
        / (2 · torus_width^2)
    )

The persistent angular and vertical asymmetry is:

    asymmetry_factor =
    1
    + epsilon
    · sin(
        3 · theta
        + 0.1 · z_offset
    )

The resulting field is:

    C3 =
    asymmetry_factor
    · toroidal_envelope

The parameter `epsilon` breaks the ideal rotational symmetry of the torus and creates unequal retention intensity across angular and vertical regions.

The default value is:

    epsilon = 0.236068

Within this module, the value is used as a numerical coefficient of persistent micro-asymmetry associated with the golden-ratio remainder.

Its use does not by itself establish a universal biological constant.

## 3. Dimensional Scope

The module calculates a scalar field on a three-dimensional grid:

    grid_size × grid_size × grid_size

The implemented numerical domain is therefore three-dimensional.

The name `C3` identifies the cubic-retention field used by the model.

The current code does not directly implement:

- six independent spatial or phase coordinates;
- a six-dimensional state array;
- a six-dimensional tensor;
- an explicit projection from a six-dimensional phase space into three-dimensional observation space.

A strict `6D` implementation would require these additional mathematical structures.

## 4. Recursive Tact-by-Tact Growth

The method `grow_organic_matrix()` executes a sequence of discrete growth tacts.

Each tact calculates:

1. the spatial Laplacian of `bio_density`;
2. the current recursive branching modulation;
3. the remaining local density capacity;
4. the retained `C3`-driven growth;
5. nonlinear saturation;
6. the updated organic-density field.

Each subsequent tact inherits the density distribution produced by the preceding tact.

The recursive operational chain is:

    previous bio_density
    → current C3 retention
    → current phase-shifted branching field
    → diffusion and local growth
    → nonlinear saturation
    → updated bio_density
    → next tact

## 5. Three-Dimensional Discrete Laplacian

The spatial Laplacian is calculated by central finite differences along all three axes:

    laplacian =
    sum over x, y, z
    (
        field(position + dx)
        + field(position - dx)
        - 2 · field(position)
    )
    / dx^2

The implementation uses `numpy.roll`, producing periodic boundary conditions.

The numerical grid is therefore treated as spatially closed across opposing boundaries. Density leaving one boundary can mathematically re-enter through the opposite boundary.

## 6. Numerical Stability

The explicit three-dimensional diffusion scheme must satisfy:

    diffusion_coefficient · dt / dx^2 ≤ 1 / 6

The time step is calculated automatically:

    dt =
    cfl_safety
    · dx^2
    / (6 · diffusion_coefficient)

This prevents artificial numerical instability under the original parameter combination:

    dt = 0.1
    diffusion_coefficient = 0.15
    dx = 0.05

Clipping the density into the interval from `0` to `1` is not used as a substitute for numerical stability.

The diffusion step is stabilized before clipping is applied.

## 7. Organic-Matrix Evolution Equation

The density evolution is calculated as:

    growth_rate =
    diffusion_coefficient · laplacian
    + retained_growth
    - nonlinear_saturation

The retained local growth is:

    retained_growth =
    growth_strength
    · C3
    · branching_modulation
    · available_capacity

The available local capacity is:

    available_capacity =
    1 - bio_density

The nonlinear saturation term is:

    nonlinear_saturation =
    saturation_strength
    · bio_density^2

The density update is:

    bio_density(t + dt) =
    bio_density(t)
    + dt · growth_rate

After each tact:

    0 ≤ bio_density ≤ 1

## 8. Nonlinear Saturation

The factor `1 - bio_density` reduces local growth as the corresponding spatial region approaches complete density saturation.

The term `bio_density^2` additionally suppresses excessive local density accumulation.

The organic matrix emerges from competition between:

- spatial diffusion;
- local retention;
- density growth;
- spatial filling;
- nonlinear saturation;
- boundary formation.

Nonlinear saturation is implemented as a separate load-bearing term of the evolution equation.

## 9. Recursive Phase-Shifted Branching

The branching field is:

    branching_modulation =
    1
    + branching_strength
    · sin(
        3 · theta
        + 0.17 · z_offset
        + step · golden_phase_increment
    )

The phase increment is:

    golden_phase_increment =
    pi · (3 - sqrt(5))

The phase changes at every tact.

The same angular growth configuration is therefore not reproduced identically in consecutive cycles.

The causal chain is:

    previous density configuration
    → tact-dependent angular phase shift
    → new local retention distribution
    → inherited density modified by the new distribution
    → next density configuration

This mechanism implements recursive morphological variation while preserving the qualitative characteristics inherited from previous growth tacts.

## 10. Organic Manifestation Layer

The module calculates the parameter:

    organic_appearance_index

The index combines:

- mean biological density;
- active-volume fraction;
- spatial density contrast;
- density retention inside the `C3` field.

The mean density is:

    mean_bio_density =
    mean(bio_density)

The active-density fraction is:

    active_density_fraction =
    fraction of cells where bio_density > 0.05

The branching contrast is:

    branching_contrast =
    standard_deviation(bio_density)

The toroidal retention value is:

    toroidal_retention =
    sum(bio_density · C3)
    / sum(C3)

The organic manifestation index is:

    organic_appearance_index =
    mean_bio_density
    · (1 + active_density_fraction)
    · (1 + branching_contrast)
    · (1 + toroidal_retention)

## 11. Manifestation Regimes

The module reports one of three operational regimes.

### STABLE ORGANIC MATRIX MANIFESTATION

The organic-density matrix has reached a comparatively strong retained manifestation state according to the current numerical thresholds.

### PARTIAL ORGANIC MATRIX MANIFESTATION

The organic-density field is spatially distributed but has not reached the stable manifestation threshold.

### WEAK OR EMERGING ORGANIC MATRIX MANIFESTATION

The organic-density field remains weak, localized, or at an early stage of development.

These values are internal diagnostic thresholds of the simulation. They are not experimentally established biological constants.

## 12. Visual Output

The method `visualize_organic_slice()` displays two central slices of the three-dimensional density matrix.

### XY Slice

The horizontal `XY` slice can display:

- a toroidally distributed density region;
- threefold angular asymmetry;
- wave-like density folds;
- regions of stronger and weaker local growth;
- diffusion-smoothed boundaries.

The ideal circular symmetry is broken by `epsilon` and by the recursive tact-dependent phase shift.

### XZ Slice

The vertical `XZ` slice can display:

- density distribution around the toroidal core;
- vertically shifted asymmetry;
- elongated regions of increased density;
- nonuniform folds and branch-like structures.

With only fifteen growth tacts, the system remains at an early stage of development.

More pronounced spatial morphology requires a larger number of tacts or a different parameter regime.

## 13. Scope of the Term Fractal

The module produces a recursive asymmetric fractal-like density structure.

Recursive branching alone does not mathematically prove that the resulting field is a fractal.

A strict fractal analysis would require additional measurements, including:

- box-counting dimension;
- correlation dimension;
- scale dependence of occupied cells;
- persistence of the measured dimension across multiple spatial scales;
- comparison between successive growth stages.

The technically accurate description of the current output is:

    recursive asymmetric fractal-like organic matrix

## 14. J_flux Limitation

The conceptual EDK architecture connects structural channels with the massless flow channel `J_flux`.

The current organic-matrix module does not explicitly calculate a vector `J_flux` field.

The visible density channels are currently generated through:

- gradients of `bio_density`;
- asymmetric `C3` retention;
- recursive branching modulation;
- nonlinear diffusion.

An explicit flow layer could later be defined as:

    J_flux =
    -diffusion_coefficient · grad(bio_density)
    + directed_retention_flux(C3)

That extension would allow separate visualization of:

- flow direction;
- flow magnitude;
- divergence;
- accumulation zones;
- dissipation zones;
- density redistribution through the organic matrix.

Until this layer is implemented, the density channels must not be presented as a directly calculated `J_flux` vector field.

## 15. Core Invariant

The organic matrix in this module is not generated by absolute symmetry or unlimited growth.

It is generated by the dynamic balance:

    spatial diffusion
    + asymmetric toroidal C3 retention
    + inherited micro-asymmetry
    + recursive phase-shifted branching
    - nonlinear saturation
    = retained three-dimensional organic-density form

The core invariant is:

    organic matrix =
    a recursively retained asymmetric density structure
    formed through the balance of diffusion,
    C3-driven local growth,
    nonlinear saturation,
    and tact-by-tact phase-shifted branching
    inside the open nonlinear dissipative dynamic Continuum

## 16. Position in the EDK Architecture

    framework_core
    → C(t)
    → T_int
    → M(t)
    → J_flux
    → module_wave_genetics
    → biophoton_signal
    → module_molecular_phase_chemistry
    → molecular phase relations
    → module_organic_matrix
    → bio_density
    → organic_appearance_index

The module occupies the architectural layer between molecular phase chemistry and macroscopic biological morphogenesis.

It translates local phase and molecular conditions into a spatially distributed three-dimensional organic-density matrix.

## 17. Main Class

`MarnovOrganicMatrixGenerator`

## 18. Main Methods

- `generate_asymmetric_c3_field()` — generates the asymmetric toroidal cubic-retention field.
- `grow_organic_matrix()` — executes recursive tact-by-tact evolution of the biological-density matrix.
- `calculate_organic_appearance()` — returns the manifestation index and structural diagnostic parameters.
- `visualize_organic_slice()` — displays central `XY` and `XZ` slices of the generated matrix.

## 19. Example

    from module_organic_matrix.marnov_organic_matrix_generator import (
        MarnovOrganicMatrixGenerator,
    )


    generator = MarnovOrganicMatrixGenerator(
        grid_size=64,
        dx=0.05,
    )

    C3_field = generator.generate_asymmetric_c3_field(
        epsilon=0.236068,
    )

    generator.grow_organic_matrix(
        C3=C3_field,
        steps=15,
    )

    state = generator.calculate_organic_appearance()

    print(state)

    generator.visualize_organic_slice()

---

# Генератор органической матрицы Марнова

## Трёхмерный рекурсивный рост органической матрицы в асимметричном поле удержания C3

Модуль `MarnovOrganicMatrixGenerator` реализует концептуальную численную модель рекурсивного потактового роста трёхмерной матрицы биологической плотности.

Модель начинается с центральной точки инициации и асимметричного тороидального поля кубического удержания `C3`.

Поле органической плотности развивается через взаимодействие:

- центральной точки инициации;
- асимметричного тороидального поля удержания;
- нелинейной пространственной диффузии;
- локального роста с ограниченной вместимостью;
- нелинейного насыщения;
- рекурсивного фазово-смещённого ветвления;
- слоя проявленности органической матрицы.

Модуль является численной экспериментальной моделью. Он не моделирует полный живой организм и сам по себе не доказывает физическую теорию жизни.

## Файл

`module_organic_matrix/marnov_organic_matrix_generator.py`

## Зависимости

- `numpy>=1.26.0`
- `matplotlib>=3.8.0`

## Установка

Запуск из корневой папки репозитория:

    pip install -r requirements.txt

## Запуск модуля

    python module_organic_matrix/marnov_organic_matrix_generator.py

## Основная операционная цепочка

    центральная точка инициации
    → асимметричное тороидальное поле C3
    → нелинейная пространственная диффузия
    → локальный удерживаемый рост
    → нелинейное насыщение
    → рекурсивное фазово-смещённое ветвление
    → bio_density
    → organic_appearance_index

## 1. Центральная точка инициации

Начальное состояние содержит одну активную центральную ячейку:

    bio_density[center, center, center] = 1

Она выполняет функцию:

- клетки-предка;
- начального локального волнового фокуса;
- точки запуска пространственного распространения плотности;
- локального якоря формирующейся органической матрицы.

Конечная структура не формируется исключительно центральной ячейкой.

Распределённое поле `C3` также создаёт пространственные области удержания и локального роста плотности вокруг тороидального ядра.

## 2. Асимметричное тороидальное поле C3

Метод `generate_asymmetric_c3_field()` формирует трёхмерное тороидальное поле удержания.

Радиальное расстояние в горизонтальной плоскости:

    radial_distance =
    sqrt(x_offset^2 + y_offset^2)

Расстояние от каждой пространственной точки до линии тороидального ядра:

    toroidal_distance =
    sqrt(
        (radial_distance - torus_radius)^2
        + z_offset^2
    )

Гауссова тороидальная огибающая:

    toroidal_envelope =
    exp(
        -toroidal_distance^2
        / (2 · torus_width^2)
    )

Устойчивая угловая и вертикальная асимметрия:

    asymmetry_factor =
    1
    + epsilon
    · sin(
        3 · theta
        + 0.1 · z_offset
    )

Результирующее поле:

    C3 =
    asymmetry_factor
    · toroidal_envelope

Параметр `epsilon` нарушает идеальную вращательную симметрию тора и создаёт неодинаковую интенсивность удержания в различных угловых и вертикальных областях.

Значение по умолчанию:

    epsilon = 0.236068

Внутри данного модуля это значение используется как численный коэффициент устойчивой микроасимметрии, связанный с остатком золотого отношения.

Само его использование не устанавливает универсальную биологическую константу.

## 3. Размерностная область модели

Модуль рассчитывает скалярное поле на трёхмерной сетке:

    grid_size × grid_size × grid_size

Следовательно, реализованная численная область является трёхмерной.

Название `C3` обозначает используемое моделью поле кубического удержания.

Текущий код напрямую не реализует:

- шесть независимых пространственных или фазовых координат;
- шестимерный массив состояния;
- шестимерный тензор;
- явную проекцию шестимерного фазового пространства в трёхмерное пространство наблюдения.

Строгая реализация `6D` потребовала бы добавления этих математических структур.

## 4. Рекурсивный потактовый рост

Метод `grow_organic_matrix()` выполняет последовательность дискретных тактов роста.

На каждом такте рассчитываются:

1. пространственный Лапласиан `bio_density`;
2. текущая рекурсивная модуляция ветвления;
3. оставшаяся локальная вместимость плотности;
4. удерживаемый рост под действием `C3`;
5. нелинейное насыщение;
6. обновлённое поле органической плотности.

Каждый последующий такт наследует распределение плотности, сформированное предшествующим тактом.

Рекурсивная операционная цепочка:

    предыдущее состояние bio_density
    → текущее удержание C3
    → текущее фазово-смещённое поле ветвления
    → диффузия и локальный рост
    → нелинейное насыщение
    → обновлённое состояние bio_density
    → следующий такт

## 5. Трёхмерный дискретный Лапласиан

Пространственный Лапласиан рассчитывается методом центральных конечных разностей по всем трём осям:

    laplacian =
    сумма по осям x, y, z
    (
        field(position + dx)
        + field(position - dx)
        - 2 · field(position)
    )
    / dx^2

Реализация использует `numpy.roll`, создавая периодические граничные условия.

Численная сетка рассматривается как пространственно замкнутая по противоположным границам. Плотность, выходящая через одну границу, математически может вернуться через противоположную.

## 6. Численная устойчивость

Явная трёхмерная диффузионная схема должна удовлетворять условию:

    diffusion_coefficient · dt / dx^2 ≤ 1 / 6

Поэтому временной шаг рассчитывается автоматически:

    dt =
    cfl_safety
    · dx^2
    / (6 · diffusion_coefficient)

Это предотвращает искусственную численную неустойчивость при исходном сочетании параметров:

    dt = 0.1
    diffusion_coefficient = 0.15
    dx = 0.05

Ограничение плотности интервалом от `0` до `1` не используется как замена численной устойчивости.

Диффузионный шаг стабилизируется до применения ограничения значений.

## 7. Уравнение эволюции органической матрицы

Динамика плотности рассчитывается как:

    growth_rate =
    diffusion_coefficient · laplacian
    + retained_growth
    - nonlinear_saturation

Локальный удерживаемый рост:

    retained_growth =
    growth_strength
    · C3
    · branching_modulation
    · available_capacity

Доступная локальная вместимость:

    available_capacity =
    1 - bio_density

Член нелинейного насыщения:

    nonlinear_saturation =
    saturation_strength
    · bio_density^2

Обновление плотности:

    bio_density(t + dt) =
    bio_density(t)
    + dt · growth_rate

После каждого такта:

    0 ≤ bio_density ≤ 1

## 8. Нелинейное насыщение

Множитель `1 - bio_density` снижает локальный рост по мере приближения соответствующей пространственной области к полному насыщению плотности.

Член `bio_density^2` дополнительно подавляет чрезмерное локальное накопление плотности.

Органическая матрица формируется через конкуренцию между:

- пространственной диффузией;
- локальным удержанием;
- ростом плотности;
- пространственным заполнением;
- нелинейным насыщением;
- формированием границ.

Нелинейное насыщение реализовано как самостоятельный несущий элемент уравнения эволюции.

## 9. Рекурсивное фазово-смещённое ветвление

Поле ветвления:

    branching_modulation =
    1
    + branching_strength
    · sin(
        3 · theta
        + 0.17 · z_offset
        + step · golden_phase_increment
    )

Фазовое приращение:

    golden_phase_increment =
    pi · (3 - sqrt(5))

Фаза изменяется на каждом такте.

Поэтому одна и та же угловая конфигурация роста не воспроизводится тождественно в последовательных циклах.

Причинная цепочка:

    предыдущее распределение плотности
    → зависящий от такта угловой фазовый сдвиг
    → новое распределение локального удержания
    → наследуемая плотность изменяется новым распределением
    → следующая конфигурация плотности

Этот механизм реализует рекурсивную изменчивость морфологии при сохранении качественных характеристик, унаследованных от предыдущих тактов роста.

## 10. Слой проявленности органической матрицы

Модуль рассчитывает параметр:

    organic_appearance_index

Индекс объединяет:

- среднюю биологическую плотность;
- долю активного объёма;
- пространственный контраст плотности;
- удержание плотности внутри поля `C3`.

Средняя плотность:

    mean_bio_density =
    mean(bio_density)

Доля активной плотности:

    active_density_fraction =
    доля ячеек, где bio_density > 0.05

Контраст ветвления:

    branching_contrast =
    standard_deviation(bio_density)

Тороидальное удержание:

    toroidal_retention =
    sum(bio_density · C3)
    / sum(C3)

Индекс проявленности органической матрицы:

    organic_appearance_index =
    mean_bio_density
    · (1 + active_density_fraction)
    · (1 + branching_contrast)
    · (1 + toroidal_retention)

## 11. Режимы проявленности

Модуль возвращает один из трёх операционных режимов.

### STABLE ORGANIC MATRIX MANIFESTATION

Матрица органической плотности достигла сравнительно сильного удерживаемого состояния проявленности в соответствии с текущими численными порогами.

### PARTIAL ORGANIC MATRIX MANIFESTATION

Поле органической плотности пространственно распределено, но ещё не достигло порога устойчивой проявленности.

### WEAK OR EMERGING ORGANIC MATRIX MANIFESTATION

Поле органической плотности остаётся слабым, локализованным или находится на раннем этапе формирования.

Эти значения являются внутренними диагностическими порогами симуляции. Они не являются экспериментально установленными биологическими константами.

## 12. Визуальный результат

Метод `visualize_organic_slice()` отображает два центральных среза трёхмерной матрицы плотности.

### Срез XY

Горизонтальный срез `XY` может показывать:

- тороидально распределённую область плотности;
- трёхкратную угловую асимметрию;
- волнообразные складки плотности;
- области усиленного и ослабленного локального роста;
- сглаженные диффузией границы.

Идеальная круговая симметрия нарушается параметром `epsilon` и рекурсивным фазовым сдвигом, зависящим от текущего такта.

### Срез XZ

Вертикальный срез `XZ` может показывать:

- распределение плотности вокруг тороидального ядра;
- вертикально смещённую асимметрию;
- вытянутые области повышенной плотности;
- неоднородные складки и ветвеподобные структуры.

При пятнадцати тактах роста система остаётся на ранней стадии развития.

Более выраженная пространственная морфология потребует большего количества тактов или другого режима параметров.

## 13. Область применимости термина «фрактальный»

Модуль формирует рекурсивную асимметричную фракталоподобную структуру плотности.

Однако само наличие рекурсивного ветвления математически не доказывает фрактальность полученного поля.

Строгий фрактальный анализ потребует дополнительных измерений:

- box-counting dimension;
- correlation dimension;
- зависимости количества занятых ячеек от масштаба;
- сохранения измеренной размерности на нескольких пространственных масштабах;
- сравнения последовательных стадий роста.

Технически корректное определение текущего результата:

    рекурсивная асимметричная фракталоподобная органическая матрица

## 14. Ограничение слоя J_flux

Концептуальная архитектура EDK связывает формирующиеся структурные каналы со сквозным безмассовым каналом `J_flux`.

Текущий модуль органической матрицы не рассчитывает явное векторное поле `J_flux`.

Наблюдаемые каналы сейчас формируются через:

- градиенты `bio_density`;
- асимметричное удержание `C3`;
- рекурсивную модуляцию ветвления;
- нелинейную диффузию.

Явный слой потока может быть определён в дальнейшем как:

    J_flux =
    -diffusion_coefficient · grad(bio_density)
    + directed_retention_flux(C3)

Такое расширение позволит отдельно визуализировать:

- направление потока;
- модуль потока;
- дивергенцию;
- зоны накопления;
- зоны диссипации;
- перераспределение плотности внутри органической матрицы.

До реализации этого слоя каналы плотности нельзя представлять как непосредственно рассчитанное векторное поле `J_flux`.

## 15. Основной инвариант

Органическая матрица в данном модуле формируется не абсолютной симметрией и не неограниченным ростом.

Она формируется динамическим балансом:

    пространственная диффузия
    + асимметричное тороидальное удержание C3
    + наследуемая микроасимметрия
    + рекурсивное фазово-смещённое ветвление
    - нелинейное насыщение
    = удержанная трёхмерная форма органической плотности

Основной инвариант:

    органическая матрица =
    рекурсивно удерживаемая асимметричная структура плотности,
    формируемая через баланс диффузии,
    локального роста под действием C3,
    нелинейного насыщения
    и потактового фазово-смещённого ветвления
    внутри открытого нелинейного диссипативного динамического Континуума

## 16. Место в архитектуре EDK

    framework_core
    → C(t)
    → T_int
    → M(t)
    → J_flux
    → module_wave_genetics
    → biophoton_signal
    → module_molecular_phase_chemistry
    → молекулярные фазовые связи
    → module_organic_matrix
    → bio_density
    → organic_appearance_index

Модуль занимает архитектурный слой между молекулярной фазовой химией и макроскопическим биологическим морфогенезом.

Он переводит локальные фазовые и молекулярные условия в пространственно распределённую трёхмерную матрицу органической плотности.

## 17. Основной класс

`MarnovOrganicMatrixGenerator`

## 18. Основные методы

- `generate_asymmetric_c3_field()` — формирует асимметричное тороидальное поле кубического удержания.
- `grow_organic_matrix()` — выполняет рекурсивную потактовую эволюцию матрицы биологической плотности.
- `calculate_organic_appearance()` — возвращает индекс проявленности и структурные диагностические параметры.
- `visualize_organic_slice()` — отображает центральные срезы `XY` и `XZ` сформированной матрицы.

## 19. Пример использования

    from module_organic_matrix.marnov_organic_matrix_generator import (
        MarnovOrganicMatrixGenerator,
    )


    generator = MarnovOrganicMatrixGenerator(
        grid_size=64,
        dx=0.05,
    )

    C3_field = generator.generate_asymmetric_c3_field(
        epsilon=0.236068,
    )

    generator.grow_organic_matrix(
        C3=C3_field,
        steps=15,
    )

    state = generator.calculate_organic_appearance()

    print(state)

    generator.visualize_organic_slice()

