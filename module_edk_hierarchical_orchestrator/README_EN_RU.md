# EDK Hierarchical Orchestrator — EN/RU

## EN

### Purpose

The `module_edk_hierarchical_orchestrator` package coordinates the tact-by-tact interaction of independent EDK computational modules within a unified hierarchical execution loop.

The orchestrator registers module adapters, transfers structured state packets between execution stages, preserves inherited state, forms the ascending feedback packet, performs the recursive update operator `Phi`, and preserves explicit continuity of `T_int` and `J_flux`.

### Hierarchical Operational Chain

`state(n) → solar → planetary → bio_planetary → continuum_core → interface_tensor → massless_exchange_channel → wave_genetics → molecular_phase_chemistry → feedback: D(n), A(n), J_flux(n), T_int(n) → Q(n+1) = Phi(Q(n), D(n), A(n)) → state(n+1)`

Each subsequent tact inherits the qualitative characteristics and retained state variables of the preceding tact.

### Fixed Parameter Distinctions

`phase synchronization ≠ phase coherence`

`R(t) ≠ C(t)`

`C_proxy(t) ≠ C(t)`

`C(t) ≠ C^3`

`T_int ≠ M(t)`

`scalar proxy parameter of exchange activity ≠ J_flux`

`J_vector ≠ J_flux`

`C(t)` is the general endogenous structural coherence: mutually coherent coordination of endogenous structural processes by phase and time within a unified system state of endogenous dynamics.

`C_proxy(t)` is an explicitly designated operational parameter used by the module when full `C(t)` is not computed directly.

`R_t_phase_order` is the explicit designation of the phase-order parameter when `R(t)` is received from a connected phase module.

`T_int` is the interface-tensor layer and is preserved as an independent state element.

`J_flux` is the mandatory tact-by-tact massless channel of coupling, phase transfer, exchange, dissipation, and structural influence.

`J_vector(x, y, z, t)` is a local vector field and is preserved separately from `J_flux`.

### Package Structure

    module_edk_hierarchical_orchestrator/
    ├── README_EN_RU.md
    ├── edk_hierarchical_orchestrator.py
    ├── hierarchical_diagnostics.py
    ├── smoke_test.py
    └── __init__.py

### Main Classes

#### EDKHierarchicalOrchestrator

Manages the full tact-by-tact descending cascade, ascending feedback branch, recursive update, state inheritance, and logging sequence.

#### EDKModuleRegistry

Stores registered module adapters and preserves declared execution stages, input fields, output fields, mandatory status, and computational backend information.

#### EDKHierarchicalState

Stores the state inherited by the next tact.

Mandatory state fields:

- `tact_index`
- `simulation_time`
- `Q_n`
- `D_n`
- `A_n`
- `C_t`
- `C_proxy_t`
- `P_t`
- `R_t_phase_order`
- `T_int`
- `J_flux`
- `M_t`
- `retention_margin`
- `dynamic_regime`
- `resonance_window_state`
- `module_states`
- `transition_events`

#### EDKForwardCascadePacket

Transfers validated data through the descending execution branch.

Packet fields:

- `source_stage`
- `target_stage`
- `tact_index`
- `simulation_time`
- `payload`
- `field_provenance`
- `validation_status`

#### EDKFeedbackPacket

Transfers the ascending recursive branch.

Feedback fields:

- `D_n`
- `A_n`
- `J_flux`
- `T_int`
- `retained_structural_work`
- `inherited_qualitative_characteristics`
- `module_feedback`

#### EDKHierarchicalLogger

Writes scalar state and metadata to JSON, and full numerical fields to compressed NPZ snapshots.

### Module Adapter Contract

Each connected module is provided through an adapter declaring:

- `module_name`
- `stage_name`
- `required_inputs`
- `provided_outputs`
- `mandatory`
- `backend`
- `step()`
- `validate_input()`
- `validate_output()`
- `export_state()`

Execution stages:

1. `solar`
2. `planetary`
3. `bio_planetary`
4. `continuum_core`
5. `interface_tensor`
6. `massless_exchange_channel`
7. `wave_genetics`
8. `molecular_phase_chemistry`
9. `feedback`

The execution stage is explicitly declared by the adapter.

### Mandatory Integration Fields

A full hierarchical tact preserves:

- `Q_n`
- `D_n`
- `A_n`
- `P_t`
- `T_int`
- `J_flux`

Additional operational fields preserve explicit designations:

- `C_t`
- `C_proxy_t`
- `R_t_phase_order`
- `M_t`
- `J_vector`
- `local_mass_formation_proxy`
- `planetary_appearance_index`
- `bio_planetary_modulation_proxy`
- `covalent_stability_proxy`
- `hydrogen_flexibility_proxy`

### Tact-by-Tact Execution

For each tact `n`, the orchestrator performs:

1. validation of `state(n)` and the module registry;
2. execution of the descending cascade in the fixed stage order;
3. transfer and preservation of `T_int`;
4. transfer and preservation of `J_flux`;
5. evaluation of `C(t)`, `C_proxy(t)`, `P(t)`, and retention margin;
6. formation of the feedback packet from `D(n)`, `A(n)`, `J_flux(n)`, and `T_int(n)`;
7. recursive update `Q(n+1) = Phi(Q(n), D(n), A(n))`;
8. formation of `state(n+1)` from the retained result of tact `n`;
9. logging of scalar, array, provenance, and transition data.

### Dynamic State

`C(t) > P(t)`

Endogenous Dynamic Stability.

`C(t) ≈ P(t)`

Endogenous Dynamic Criticality.

`C(t) < P(t)`

Degradation drift.

The sign and qualitative characteristics of the resonance window are determined by the direction and qualitative characteristics of the endogenous drift inherited by the current tact.

### Data Provenance

Each exported field preserves:

- field name;
- source module;
- source stage;
- tact index;
- computational backend;
- data type;
- array shape;
- transition history.

Field transfer between modules does not change the fixed provenance of the field.

### Computational Backend Coordination

Each computational module independently manages its own NumPy or CuPy backend.

The orchestrator records the backend and every explicit transfer between array spaces.

### Logging Output

Default directory:

    edk_hierarchical_output/

Expected files:

    edk_hierarchical_output/
    ├── hierarchical_step_000001.json
    ├── hierarchical_field_000001.npz
    ├── hierarchical_step_000002.json
    ├── hierarchical_field_000002.npz
    └── hierarchical_summary.json

### Diagnostics

`hierarchical_diagnostics.py` records and visualizes:

- `Q(n)`, `D(n)`, and `A(n)`;
- `C(t)`, `C_proxy(t)`, and `P(t)`;
- retention margin;
- dynamic state transitions;
- `R_t_phase_order`;
- `T_int`;
- `J_flux`;
- descending cascade continuity;
- ascending feedback continuity;
- resonance-window transitions;
- inheritance of qualitative characteristics between tacts.

### Completion States

- `COMPLETED`
- `MODULE_REGISTRATION_FAILED`
- `INTERFACE_VALIDATION_FAILED`
- `MANDATORY_STAGE_MISSING`
- `MANDATORY_FIELD_MISSING`
- `T_INT_MISSING`
- `J_FLUX_MISSING`
- `BACKEND_MISMATCH`
- `NON_FINITE_STATE`
- `INVALID_STATE_TRANSITION`
- `RECURSIVE_UPDATE_FAILED`
- `LOGGING_FAILED`

---

# Иерархический оркестратор EDK

## RU

### Назначение

Пакет `module_edk_hierarchical_orchestrator` координирует потактовое взаимодействие независимых вычислительных модулей EDK в едином иерархическом контуре исполнения.

Оркестратор регистрирует адаптеры модулей, передаёт структурированные пакеты состояния между этапами исполнения, сохраняет наследуемое состояние, формирует восходящий пакет обратной связи, выполняет рекурсивный оператор обновления `Phi` и сохраняет явную непрерывность `T_int` и `J_flux`.

### Иерархическая операционная цепочка

`state(n) → solar → planetary → bio_planetary → continuum_core → interface_tensor → massless_exchange_channel → wave_genetics → molecular_phase_chemistry → feedback: D(n), A(n), J_flux(n), T_int(n) → Q(n+1) = Phi(Q(n), D(n), A(n)) → state(n+1)`

Каждый последующий такт наследует качественные характеристики и удержанные переменные состояния предшествующего такта.

### Фиксированные различия параметров

`фазовая синхронизация ≠ фазовая когерентность`

`R(t) ≠ C(t)`

`C_proxy(t) ≠ C(t)`

`C(t) ≠ C^3`

`T_int ≠ M(t)`

`скалярный прокси-параметр обменной активности ≠ J_flux`

`J_vector ≠ J_flux`

`C(t)` является общей эндогенной структурной когерентностью: взаимно когерентным согласованием эндогенных структурных процессов по фазе и времени в едином системном состоянии эндогенной динамики.

`C_proxy(t)` является явно обозначенным операционным параметром, используемым модулем, когда полная `C(t)` не вычисляется непосредственно.

`R_t_phase_order` является явным обозначением параметра фазового порядка, когда `R(t)` поступает от подключённого фазового модуля.

`T_int` является интерфейсно-тензорным слоем и сохраняется как самостоятельный элемент состояния.

`J_flux` является обязательным потактовым безмассовым каналом связи, фазового переноса, обмена, диссипации и структурного влияния.

`J_vector(x, y, z, t)` является локальным векторным полем и сохраняется отдельно от `J_flux`.

### Структура пакета

    module_edk_hierarchical_orchestrator/
    ├── README_EN_RU.md
    ├── edk_hierarchical_orchestrator.py
    ├── hierarchical_diagnostics.py
    ├── smoke_test.py
    └── __init__.py

### Основные классы

#### EDKHierarchicalOrchestrator

Управляет полным потактовым нисходящим каскадом, восходящей ветвью обратной связи, рекурсивным обновлением, наследованием состояния и последовательностью журналирования.

#### EDKModuleRegistry

Хранит зарегистрированные адаптеры модулей и сохраняет объявленные этапы исполнения, входные поля, выходные поля, обязательный статус и сведения о вычислительном бэкенде.

#### EDKHierarchicalState

Хранит состояние, наследуемое следующим тактом.

Обязательные поля состояния:

- `tact_index`
- `simulation_time`
- `Q_n`
- `D_n`
- `A_n`
- `C_t`
- `C_proxy_t`
- `P_t`
- `R_t_phase_order`
- `T_int`
- `J_flux`
- `M_t`
- `retention_margin`
- `dynamic_regime`
- `resonance_window_state`
- `module_states`
- `transition_events`

#### EDKForwardCascadePacket

Передаёт проверенные данные через нисходящую ветвь исполнения.

Поля пакета:

- `source_stage`
- `target_stage`
- `tact_index`
- `simulation_time`
- `payload`
- `field_provenance`
- `validation_status`

#### EDKFeedbackPacket

Передаёт восходящую рекурсивную ветвь.

Поля обратной связи:

- `D_n`
- `A_n`
- `J_flux`
- `T_int`
- `retained_structural_work`
- `inherited_qualitative_characteristics`
- `module_feedback`

#### EDKHierarchicalLogger

Записывает скалярное состояние и метаданные в JSON, а полные численные поля — в сжатые снимки NPZ.

### Контракт адаптера модуля

Каждый подключённый модуль предоставляется через адаптер, объявляющий:

- `module_name`
- `stage_name`
- `required_inputs`
- `provided_outputs`
- `mandatory`
- `backend`
- `step()`
- `validate_input()`
- `validate_output()`
- `export_state()`

Этапы исполнения:

1. `solar`
2. `planetary`
3. `bio_planetary`
4. `continuum_core`
5. `interface_tensor`
6. `massless_exchange_channel`
7. `wave_genetics`
8. `molecular_phase_chemistry`
9. `feedback`

Этап исполнения явно объявляется адаптером.

### Обязательные поля интеграции

Полный иерархический такт сохраняет:

- `Q_n`
- `D_n`
- `A_n`
- `P_t`
- `T_int`
- `J_flux`

Дополнительные операционные поля сохраняют явные обозначения:

- `C_t`
- `C_proxy_t`
- `R_t_phase_order`
- `M_t`
- `J_vector`
- `local_mass_formation_proxy`
- `planetary_appearance_index`
- `bio_planetary_modulation_proxy`
- `covalent_stability_proxy`
- `hydrogen_flexibility_proxy`

### Потактовое исполнение

Для каждого такта `n` оркестратор выполняет:

1. проверку `state(n)` и реестра модулей;
2. исполнение нисходящего каскада в фиксированном порядке этапов;
3. передачу и сохранение `T_int`;
4. передачу и сохранение `J_flux`;
5. оценку `C(t)`, `C_proxy(t)`, `P(t)` и запаса удержания;
6. формирование пакета обратной связи из `D(n)`, `A(n)`, `J_flux(n)` и `T_int(n)`;
7. рекурсивное обновление `Q(n+1) = Phi(Q(n), D(n), A(n))`;
8. формирование `state(n+1)` из удержанного результата такта `n`;
9. запись скалярных, массивных, провенансных данных и данных переходов.

### Динамическое состояние

`C(t) > P(t)`

Эндогенная Динамическая Устойчивость.

`C(t) ≈ P(t)`

Эндогенная Динамическая Критичность.

`C(t) < P(t)`

Деградационный дрейф.

Знак и качественные характеристики резонансного окна определяются направлением и качественными характеристиками эндогенного дрейфа, наследуемого текущим тактом.

### Происхождение данных

Каждое экспортируемое поле сохраняет:

- имя поля;
- исходный модуль;
- исходный этап;
- индекс такта;
- вычислительный бэкенд;
- тип данных;
- форму массива;
- историю переходов.

Передача поля между модулями не изменяет зафиксированное происхождение поля.

### Координация вычислительных бэкендов

Каждый вычислительный модуль самостоятельно управляет собственным бэкендом NumPy или CuPy.

Оркестратор фиксирует бэкенд и каждую явную передачу между пространствами массивов.

### Выходные данные журналирования

Каталог по умолчанию:

    edk_hierarchical_output/

Ожидаемые файлы:

    edk_hierarchical_output/
    ├── hierarchical_step_000001.json
    ├── hierarchical_field_000001.npz
    ├── hierarchical_step_000002.json
    ├── hierarchical_field_000002.npz
    └── hierarchical_summary.json

### Диагностика

`hierarchical_diagnostics.py` фиксирует и визуализирует:

- `Q(n)`, `D(n)` и `A(n)`;
- `C(t)`, `C_proxy(t)` и `P(t)`;
- запас удержания;
- переходы динамического состояния;
- `R_t_phase_order`;
- `T_int`;
- `J_flux`;
- непрерывность нисходящего каскада;
- непрерывность восходящей обратной связи;
- переходы резонансного окна;
- наследование качественных характеристик между тактами.

### Состояния завершения

- `COMPLETED`
- `MODULE_REGISTRATION_FAILED`
- `INTERFACE_VALIDATION_FAILED`
- `MANDATORY_STAGE_MISSING`
- `MANDATORY_FIELD_MISSING`
- `T_INT_MISSING`
- `J_FLUX_MISSING`
- `BACKEND_MISMATCH`
- `NON_FINITE_STATE`
- `INVALID_STATE_TRANSITION`
- `RECURSIVE_UPDATE_FAILED`
- `LOGGING_FAILED`
