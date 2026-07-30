# Generalized Ramp-Scaling Lemma for a Linear Critical Ramp

## EN — Scope

Consider the generalized critical normal form

`dC/dt = v_eff t C - g C^n`

with

`v_eff > 0`, `g > 0`, `n > 1`.

The lemma applies to the class in which the control parameter crosses the critical point through the linear ramp term `v_eff t C`. The symbol `~` denotes scaling up to a dimensionless factor fixed by the reduced trajectory, the initial condition, and the selected dimensionless critical or delay criterion.

## EN — Lemma

For every `n > 1` in this linear-ramp class, the characteristic critical-time and delay-time scales are

`t_critical ~ v_eff^(-1/2)`

`t_delay ~ v_eff^(-1/2)`.

The corresponding characteristic amplitude scale is

`C_critical ~ g^(-1/(n-1)) v_eff^(1/(2(n-1)))`.

Therefore, the temporal exponent `-1/2` is independent of the saturation order `n`, while the amplitude exponent depends on `n`.

## EN — Scaling Proof

Introduce the scaling ansatz

`t = v_eff^(-alpha) tau`

`C = g^(-1/(n-1)) v_eff^beta y`.

The three terms of the normal form scale as

`dC/dt ~ g^(-1/(n-1)) v_eff^(beta + alpha) dy/dtau`,

`v_eff t C ~ g^(-1/(n-1)) v_eff^(1 - alpha + beta) tau y`,

`g C^n ~ g^(-1/(n-1)) v_eff^(n beta) y^n`.

A non-degenerate reduced equation requires the exponent balance

`beta + alpha = 1 - alpha + beta = n beta`.

The equality of the derivative and ramp exponents gives

`alpha = 1/2`.

The equality of the derivative and saturation exponents then gives

`beta + 1/2 = n beta`,

hence

`beta = 1/(2(n-1))`.

With these values,

`t = v_eff^(-1/2) tau`

and

`C = g^(-1/(n-1)) v_eff^(1/(2(n-1))) y`.

After division by the common prefactor, the normal form becomes

`dy/dtau = tau y - y^n`.

The reduced equation contains neither `v_eff` nor `g`. Consequently, any critical or delay event defined by a fixed dimensionless condition in the reduced dynamics occurs at a dimensionless value `tau = O(1)`, which gives

`t_critical ~ v_eff^(-1/2)`

and

`t_delay ~ v_eff^(-1/2)`.

The amplitude at the same reduced event obeys

`C_critical ~ g^(-1/(n-1)) v_eff^(1/(2(n-1)))`.

## EN — Cubic Three-Dimensional Specialization

For `n = 3`,

`dC/dt = v_eff t C - g C^3`,

and the amplitude scale becomes

`C_critical ~ g^(-1/2) v_eff^(1/4)`.

The temporal scales remain

`t_critical ~ v_eff^(-1/2)`

`t_delay ~ v_eff^(-1/2)`.

The exponent `-1/3` does not follow from cubic saturation. Cubic saturation changes the amplitude exponent to `1/4`; it does not change the temporal exponent from `-1/2`.

## EN — Geometric Closure

Let a `d`-dimensional coherent volume be represented by directional coherence amplitudes:

`V_coh,d ∝ C_1 C_2 ... C_d`.

Under isotropic reduction,

`C_1 ~ C_2 ~ ... ~ C_d ~ C`,

so

`V_coh,d ∝ C^d`.

The identification

`n = d`

is a geometric dimensional closure connecting the saturation order to the modeled coherent-volume product. It is a model closure. Spatial dimensionality alone does not prove a unique dynamical normal form without this identification and the associated dynamical assumptions.

For `d = 3`, the closure gives `n = 3` and supports a cubic saturation term.

## EN — Symmetry Closure

If `C` is a signed amplitude and the local amplitude dynamics are invariant under

`C -> -C`,

then the vector field must be odd in `C`. Even powers, including a quadratic term, are excluded by this symmetry. After the linear term, the leading saturating nonlinearity is

`-g C^3`

provided its coefficient is nonzero. This is a symmetry closure independent of the geometric coherent-volume closure.

In the three-dimensional EDS case, geometric closure and symmetry closure both support `C^3`, but they remain logically distinct arguments.

## EN — Separation of Definitions and Dynamical Closure

A relation such as

`C^3 := (1/N_C) Tr(Psi_coh^dagger Psi_coh)`

defines or normalizes a folded-state intensity on the `C^3` scale. By itself, this identity does not derive the saturation order of the critical normal form. The dynamical cubic term requires the geometric closure, the symmetry closure, or another explicitly stated dynamical closure.

A quadratic term `C^2` is nonlinear. It must not be described as a linear approximation.

The temporal exponent is not determined by spatial dimensionality or by the saturation order. Within this lemma it is fixed by the linear ramp structure `v_eff t C`.

If the ramp term has a different time dependence or a different coupling to `C`, the exponent balance must be derived again; the present lemma does not assign `-1/2` outside the stated linear-ramp class.

## EN — Repository Invariant

Within the EDK documents and executable modules that use the normal form class

`dC/dt = v_eff t C - g C^n`,

the controlled scaling invariant is

`t_critical ~ t_delay ~ v_eff^(-1/2)` for every `n > 1`,

while

`C_critical ~ g^(-1/(n-1)) v_eff^(1/(2(n-1)))`.

Algebraic and computational checks of these relations establish internal mathematical consistency of the implemented scaling. They are not, by themselves, experimental validation of a physical model.

# Обобщённая лемма рампового масштабирования для линейного критического рампа

## RU — Область применимости

Рассмотрим обобщённую критическую нормальную форму

`dC/dt = v_eff t C - g C^n`

при

`v_eff > 0`, `g > 0`, `n > 1`.

Лемма применима к классу, в котором управляющий параметр проходит критическую точку через линейный рамповый член `v_eff t C`. Символ `~` обозначает масштабирование с точностью до безразмерного множителя, определяемого редуцированной траекторией, начальным условием и выбранным безразмерным критерием критического момента или задержки.

## RU — Лемма

Для любого `n > 1` в этом линейно-рамповом классе характерные масштабы критического времени и времени задержки равны

`t_critical ~ v_eff^(-1/2)`

`t_delay ~ v_eff^(-1/2)`.

Соответствующий характерный амплитудный масштаб равен

`C_critical ~ g^(-1/(n-1)) v_eff^(1/(2(n-1)))`.

Следовательно, временной показатель `-1/2` не зависит от порядка насыщения `n`, тогда как амплитудный показатель зависит от `n`.

## RU — Доказательство масштабированием

Введём масштабный анзац

`t = v_eff^(-alpha) tau`

`C = g^(-1/(n-1)) v_eff^beta y`.

Три члена нормальной формы масштабируются как

`dC/dt ~ g^(-1/(n-1)) v_eff^(beta + alpha) dy/dtau`,

`v_eff t C ~ g^(-1/(n-1)) v_eff^(1 - alpha + beta) tau y`,

`g C^n ~ g^(-1/(n-1)) v_eff^(n beta) y^n`.

Невырожденное редуцированное уравнение требует баланса показателей

`beta + alpha = 1 - alpha + beta = n beta`.

Равенство показателей производной и рампового члена даёт

`alpha = 1/2`.

Равенство показателей производной и насыщения затем даёт

`beta + 1/2 = n beta`,

откуда

`beta = 1/(2(n-1))`.

При этих значениях

`t = v_eff^(-1/2) tau`

и

`C = g^(-1/(n-1)) v_eff^(1/(2(n-1))) y`.

После деления на общий множитель нормальная форма принимает вид

`dy/dtau = tau y - y^n`.

Редуцированное уравнение не содержит ни `v_eff`, ни `g`. Следовательно, любое критическое событие или событие задержки, определённое фиксированным безразмерным условием редуцированной динамики, происходит при безразмерном значении `tau = O(1)`, что даёт

`t_critical ~ v_eff^(-1/2)`

и

`t_delay ~ v_eff^(-1/2)`.

Амплитуда при том же редуцированном событии подчиняется

`C_critical ~ g^(-1/(n-1)) v_eff^(1/(2(n-1)))`.

## RU — Кубическая трёхмерная специализация

Для `n = 3`

`dC/dt = v_eff t C - g C^3`,

а амплитудный масштаб принимает вид

`C_critical ~ g^(-1/2) v_eff^(1/4)`.

Временные масштабы сохраняются:

`t_critical ~ v_eff^(-1/2)`

`t_delay ~ v_eff^(-1/2)`.

Показатель `-1/3` не следует из кубического насыщения. Кубическое насыщение изменяет амплитудный показатель на `1/4`, но не изменяет временной показатель `-1/2`.

## RU — Геометрическое замыкание

Пусть `d`-мерный когерентный объём представлен направленными амплитудами когерентности:

`V_coh,d ∝ C_1 C_2 ... C_d`.

При изотропной редукции

`C_1 ~ C_2 ~ ... ~ C_d ~ C`,

поэтому

`V_coh,d ∝ C^d`.

Отождествление

`n = d`

является геометрическим размерностным замыканием, связывающим порядок насыщения с моделируемым произведением когерентного объёма. Это модельное замыкание. Пространственная размерность сама по себе не доказывает единственную динамическую нормальную форму без данного отождествления и связанных с ним динамических предпосылок.

Для `d = 3` это замыкание даёт `n = 3` и поддерживает кубический член насыщения.

## RU — Симметрийное замыкание

Если `C` является знакопеременной амплитудой, а локальная амплитудная динамика инвариантна относительно

`C -> -C`,

то векторное поле должно быть нечётным по `C`. Чётные степени, включая квадратичный член, запрещены этой симметрией. После линейного члена ведущей насыщающей нелинейностью является

`-g C^3`

при ненулевом коэффициенте этого члена. Это симметрийное замыкание, независимое от геометрического замыкания когерентного объёма.

В трёхмерном EDS-случае геометрическое и симметрийное замыкания оба поддерживают `C^3`, но остаются логически различными аргументами.

## RU — Разделение определений и динамического замыкания

Отношение вида

`C^3 := (1/N_C) Tr(Psi_coh^dagger Psi_coh)`

определяет или нормирует интенсивность свёрнутого состояния в шкале `C^3`. Само по себе это тождество не выводит порядок насыщения критической нормальной формы. Динамический кубический член требует геометрического замыкания, симметрийного замыкания или иного явно сформулированного динамического замыкания.

Квадратичный член `C^2` является нелинейным. Его нельзя описывать как линейное приближение.

Временной показатель не определяется пространственной размерностью или порядком насыщения. В рамках данной леммы он задаётся линейной рамповой структурой `v_eff t C`.

Если рамповый член имеет иную временную зависимость или иное сопряжение с `C`, баланс показателей должен быть выведен заново; настоящая лемма не назначает показатель `-1/2` вне указанного линейно-рампового класса.

## RU — Инвариант репозитория

В документах и исполняемых модулях EDK, использующих класс нормальной формы

`dC/dt = v_eff t C - g C^n`,

контролируемым инвариантом масштабирования является

`t_critical ~ t_delay ~ v_eff^(-1/2)` для любого `n > 1`,

тогда как

`C_critical ~ g^(-1/(n-1)) v_eff^(1/(2(n-1)))`.

Алгебраические и вычислительные проверки этих соотношений устанавливают внутреннюю математическую согласованность реализованного масштабирования. Сами по себе они не являются экспериментальной валидацией физической модели.
