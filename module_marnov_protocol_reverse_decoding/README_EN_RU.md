# Marnov Protocol Reverse Decoding Module

## EN — README for the Marnov Protocol Reverse Decoding Module

Module directory:

`module_marnov_protocol_reverse_decoding`

Python file:

`marnov_reverse_decoder.py`

README file:

`README_EN_RU.md`

Main class:

`MarnovMultidimensionalCoder`

## EN — Module Purpose

The `MarnovMultidimensionalCoder` module implements deterministic phase encoding and reverse decoding of byte sequences through a sparse three-dimensional complex grid.

The module provides:

- deterministic collision-free 3D address generation;
- byte-to-phase mapping;
- sparse complex payload construction;
- nonlinear phase-lock transformation;
- reverse decoding through comparison with 256 valid byte-phase candidates;
- byte reconstruction;
- optional UTF-8 text reconstruction;
- verification of complete encode-decode cycles.

The module operates as the reverse-decoding support layer of the Marnov Protocol.

The current numerical implementation uses a three-dimensional complex grid as the operational address container.

The 7D and 6D names are retained as protocol-layer terminology where the implementation maps them to the current sparse-grid and locked-payload operations.

## EN — Operational Chain

The implemented computational chain is:

UTF-8 string or byte sequence  
→ deterministic collision-free 3D address table  
→ byte-to-phase mapping  
→ sparse complex payload `Q_grid`  
→ nonlinear phase-lock transformation  
→ locked complex payload  
→ discrete comparison with 256 valid phase candidates  
→ reconstructed byte sequence  
→ optional UTF-8 decoding

The byte layer is the control layer.

The text layer is an optional UTF-8 interpretation of the reconstructed byte sequence.

## EN — Operational Naming

`Q_grid`

Sparse three-dimensional complex grid containing byte-phase values.

`locked_payload`

Phase-transformed complex payload produced from `Q_grid`.

`kappa`

Nonlinear phase-lock stiffness parameter.

`original_byte_length`

External decoding metadata required for exact byte reconstruction.

`C3_payload`

Backward-compatible legacy name for `locked_payload`.

`encode_bytes_to_7d()`

Backward-compatible alias for `encode_bytes_to_grid()`.

`encode_string_to_7d()`

Backward-compatible alias for `encode_text_to_grid()`.

`generate_6d_torus_payload()`

Backward-compatible alias for `generate_locked_payload()`.

`decode_7d_to_bytes()`

Backward-compatible alias for `decode_locked_payload_to_bytes()`.

`decode_7d_to_string()`

Backward-compatible alias for `decode_locked_payload_to_text()`.

## EN — Data Representation

The source data can be:

- a byte sequence;
- a UTF-8 string converted into bytes.

Each byte is mapped into one complex value at one deterministic coordinate of the 3D grid.

The encoded payload is a sparse complex grid.

The recommended operational name is:

`Q_grid`

The conceptual name `Q(n)` can be used as a protocol-layer label.

## EN — Address Table

The module builds a deterministic collision-free address table.

The primary address path follows a ring-like trajectory inside the 3D grid.

If two byte positions map to the same coordinate, deterministic linear probing assigns the next free voxel.

The address table is determined by:

- the grid size;
- the source byte length;
- the byte position index.

The grid capacity is:

`capacity = grid_size^3`

The source byte length is bounded by the grid capacity.

For grid size `32`:

`capacity = 32768`

## EN — Byte-to-Phase Mapping

Each byte value is mapped to a distinct phase bin.

The mapping is:

`phase = byte_value / 256 · 2 · pi`

The division by `256` separates all byte values in the valid byte interval.

The valid byte range is:

`0 ≤ byte_value ≤ 255`

The phase value is embedded into the complex unit circle:

`complex_value = exp(i · phase)`

## EN — Sparse Complex Payload Q_grid

The encoded grid has the shape:

`grid_size × grid_size × grid_size`

Only the coordinates assigned by the deterministic address table are filled with byte-phase values.

All other grid positions remain zero.

The grid is sparse by construction.

## EN — Nonlinear Phase-Lock Transformation

The nonlinear phase-lock transformation is:

`phase_locked = phase + kappa · sin(phase)`

Where:

- `phase` is extracted from the encoded complex value;
- `kappa` is the nonlinear phase-lock stiffness parameter.

The locked value is constructed as:

`locked_value = magnitude^3 · exp(i · phase_locked)`

The resulting payload is:

`locked_payload`

The transformation preserves deterministic reversibility through candidate matching when the same `kappa` and the same address table are used.

## EN — Locked Payload

The locked payload is the phase-transformed data container generated from the sparse complex payload.

Operational name:

`locked_payload`

Legacy compatible name:

`C3_payload`

The payload stores transformed complex values at the same deterministic address positions used by `Q_grid`.

The payload can be decoded when the decoder receives:

- the locked payload;
- the original byte length;
- the same grid size;
- the same nonlinear phase-lock stiffness parameter `kappa`.

## EN — Reverse Decoding

Reverse decoding performs discrete byte-candidate matching.

For each encoded address:

1. The locked complex value is read.
2. All 256 possible byte phases are generated.
3. Each candidate phase is transformed through the same phase-lock function.
4. The candidate closest to the received locked complex value is selected.
5. The selected candidate index is returned as the decoded byte.

The reverse operation is:

locked complex value  
→ nearest valid byte-phase candidate  
→ reconstructed byte

The decoded bytes are assembled in the original byte order.

## EN — Original Byte Length

The decoder uses:

`original_byte_length`

This value defines how many encoded addresses must be read during reconstruction.

The current payload workflow receives this value as external metadata.

A container-level implementation can store this metadata together with the payload.

Recommended future container fields:

- grid size;
- byte length;
- kappa identifier;
- checksum;
- version field;
- integrity data.

The current module implements the deterministic encoding and decoding core.

## EN — UTF-8 Text Layer

Text encoding is performed by converting a string into UTF-8 bytes.

The byte layer remains primary.

The text layer is reconstructed after byte decoding.

If reconstructed bytes do not form valid UTF-8 text, the text decoder returns a structured decoding status.

The byte decoder remains the control mechanism for exact payload recovery.

## EN — Security Layer Boundary

The current implementation defines the deterministic phase-coding core.

Protected transmission and storage are handled by an external security container.

The external security layer can provide:

- confidentiality;
- authentication;
- integrity verification;
- nonce handling;
- replay protection;
- cryptographic key derivation.

The parameter `kappa` controls the nonlinear phase-lock transformation.

For protected storage or transmission, the deterministic phase-coding core is combined with an external cryptographic container.

## EN — Verification Logic

The module verifies complete deterministic cycles:

source text  
→ UTF-8 byte sequence  
→ sparse 3D phase encoding  
→ nonlinear phase-lock transformation  
→ reverse candidate matching  
→ reconstructed byte sequence  
→ reconstructed text  
→ comparison with the original text

The module also verifies arbitrary byte payloads, including the full byte range:

`0..255`

Verification passes when the reconstructed bytes match the original byte sequence exactly.

## EN — Main State Parameters

`grid_size`

Side length of the cubic 3D address grid.

`shape`

Grid shape:

`grid_size × grid_size × grid_size`

`capacity`

Maximum number of bytes addressable by the current grid:

`grid_size^3`

`kappa`

Nonlinear phase-lock stiffness parameter.

## EN — Main Methods

### `encode_bytes_to_grid()`

Encodes a byte sequence into a sparse 3D complex grid.

### `encode_text_to_grid()`

Encodes a UTF-8 string into a sparse 3D complex grid.

### `generate_locked_payload()`

Applies the nonlinear phase-lock transformation to the sparse complex grid.

### `decode_locked_payload_to_bytes()`

Reconstructs the original byte sequence through 256-candidate phase matching.

### `decode_locked_payload_to_text()`

Reconstructs UTF-8 text from the decoded bytes and returns decoding status.

### `verify_text_cycle()`

Verifies a complete text encode-decode cycle.

### `verify_bytes_cycle()`

Verifies a complete arbitrary byte encode-decode cycle.

## EN — Backward-Compatible Method Aliases

The module keeps repository-compatible aliases for earlier method names.

`encode_bytes_to_7d()`

Alias of `encode_bytes_to_grid()`.

`encode_string_to_7d()`

Alias of `encode_text_to_grid()`.

`generate_6d_torus_payload()`

Alias of `generate_locked_payload()`.

`decode_7d_to_bytes()`

Alias of `decode_locked_payload_to_bytes()`.

`decode_7d_to_string()`

Alias of `decode_locked_payload_to_text()`.

## EN — Dependencies

The module requires:

`numpy>=1.26.0`

## EN — Python Version

Python 3.10 or later.

## EN — Installation

`pip install numpy`

## EN — Run Command

From the repository root:

`python module_marnov_protocol_reverse_decoding/marnov_reverse_decoder.py`

## EN — Expected Output

The demonstration prints:

- text verification cycles;
- decoded text results;
- byte verification for the complete `0..255` byte range;
- final verification status.

A successful run confirms deterministic encode-decode consistency.

## EN — Module Structure

`module_marnov_protocol_reverse_decoding/README_EN_RU.md`

`module_marnov_protocol_reverse_decoding/marnov_reverse_decoder.py`

## EN — Status

Module status:

working deterministic phase-coding prototype.

Layer:

Marnov Protocol reverse-decoding support layer.

Function:

deterministic byte-to-phase encoding, nonlinear phase-lock transformation, and reverse byte reconstruction through discrete candidate matching.

---

# Модуль обратного декодирования Протокола Марнова

## RU — README к модулю обратного декодирования Протокола Марнова

Папка модуля:

`module_marnov_protocol_reverse_decoding`

Python-файл:

`marnov_reverse_decoder.py`

README-файл:

`README_EN_RU.md`

Основной класс:

`MarnovMultidimensionalCoder`

## RU — Назначение модуля

Модуль `MarnovMultidimensionalCoder` реализует детерминированное фазовое кодирование и обратное декодирование байтовых последовательностей через разреженную трёхмерную комплексную сетку.

Модуль обеспечивает:

- детерминированную генерацию трёхмерных адресов без коллизий;
- отображение байта в фазу;
- построение разреженной комплексной полезной нагрузки;
- нелинейное фазово-замковое преобразование;
- обратное декодирование через сопоставление с 256 допустимыми фазовыми кандидатами;
- восстановление байтов;
- опциональное восстановление текста UTF-8;
- проверку полного цикла кодирования-декодирования.

Модуль работает как вспомогательный слой обратного декодирования Протокола Марнова.

Текущая численная реализация использует трёхмерную комплексную сетку как операционный адресный контейнер.

Обозначения 7D и 6D сохраняются как терминология протокольных слоёв там, где реализация отображает их на текущие операции разреженной сетки и фазово-запертой полезной нагрузки.

## RU — Операционная цепочка

Реализованная вычислительная цепочка:

строка UTF-8 или байтовая последовательность  
→ детерминированная таблица трёхмерных адресов без коллизий  
→ отображение байта в фазу  
→ разреженная комплексная полезная нагрузка `Q_grid`  
→ нелинейное фазово-замковое преобразование  
→ фазово-запертая комплексная полезная нагрузка  
→ дискретное сопоставление с 256 допустимыми фазовыми кандидатами  
→ восстановленная байтовая последовательность  
→ опциональное декодирование UTF-8

Байтовый слой является контрольным слоем.

Текстовый слой является опциональной UTF-8-интерпретацией восстановленной байтовой последовательности.

## RU — Операционные имена

`Q_grid`

Разреженная трёхмерная комплексная сетка, содержащая байтово-фазовые значения.

`locked_payload`

Фазово-преобразованная комплексная полезная нагрузка, полученная из `Q_grid`.

`kappa`

Параметр жёсткости нелинейного фазового замка.

`original_byte_length`

Внешние метаданные декодирования, необходимые для точного восстановления байтов.

`C3_payload`

Обратно совместимое прежнее имя для `locked_payload`.

`encode_bytes_to_7d()`

Обратно совместимый псевдоним `encode_bytes_to_grid()`.

`encode_string_to_7d()`

Обратно совместимый псевдоним `encode_text_to_grid()`.

`generate_6d_torus_payload()`

Обратно совместимый псевдоним `generate_locked_payload()`.

`decode_7d_to_bytes()`

Обратно совместимый псевдоним `decode_locked_payload_to_bytes()`.

`decode_7d_to_string()`

Обратно совместимый псевдоним `decode_locked_payload_to_text()`.

## RU — Представление данных

Исходными данными могут быть:

- байтовая последовательность;
- строка UTF-8, преобразованная в байты.

Каждый байт отображается в одно комплексное значение по одной детерминированной координате трёхмерной сетки.

Закодированная полезная нагрузка является разреженной комплексной сеткой.

Рекомендуемое операционное имя:

`Q_grid`

Концептуальное имя `Q(n)` может использоваться как метка протокольного слоя.

## RU — Таблица адресов

Модуль строит детерминированную таблицу адресов без коллизий.

Первичный адресный путь следует кольцеподобной траектории внутри трёхмерной сетки.

Если две позиции байтов попадают в одну координату, детерминированное линейное пробирование назначает следующий свободный воксель.

Таблица адресов определяется:

- размером сетки;
- длиной исходной байтовой последовательности;
- индексом позиции байта.

Ёмкость сетки:

`capacity = grid_size^3`

Длина исходной байтовой последовательности ограничена ёмкостью сетки.

Для размера сетки `32`:

`capacity = 32768`

## RU — Отображение байта в фазу

Каждое значение байта отображается в отдельный фазовый интервал.

Отображение:

`phase = byte_value / 256 · 2 · pi`

Деление на `256` разделяет все значения байтов в допустимом байтовом интервале.

Допустимый диапазон байта:

`0 ≤ byte_value ≤ 255`

Затем фазовое значение встраивается в комплексную единичную окружность:

`complex_value = exp(i · phase)`

## RU — Разреженная комплексная полезная нагрузка Q_grid

Закодированная сетка имеет форму:

`grid_size × grid_size × grid_size`

Только координаты, назначенные детерминированной таблицей адресов, заполняются байтово-фазовыми значениями.

Все остальные позиции сетки остаются нулевыми.

Сетка является разреженной по конструкции.

## RU — Нелинейное фазово-замковое преобразование

Нелинейное фазово-замковое преобразование:

`phase_locked = phase + kappa · sin(phase)`

Где:

- `phase` — фаза, извлечённая из закодированного комплексного значения;
- `kappa` — параметр жёсткости нелинейного фазового замка.

Фазово-запертое значение строится как:

`locked_value = magnitude^3 · exp(i · phase_locked)`

Результирующая полезная нагрузка:

`locked_payload`

Преобразование сохраняет детерминированную обратимость через сопоставление кандидатов при использовании того же `kappa` и той же адресной таблицы.

## RU — Фазово-запертая полезная нагрузка

Фазово-запертая полезная нагрузка является фазово-преобразованным контейнером данных, созданным из разреженной комплексной полезной нагрузки.

Операционное имя:

`locked_payload`

Обратно совместимое имя:

`C3_payload`

Полезная нагрузка хранит преобразованные комплексные значения в тех же детерминированных адресных позициях, которые используются в `Q_grid`.

Полезная нагрузка декодируется при наличии:

- фазово-запертой полезной нагрузки;
- исходной длины байтовой последовательности;
- того же размера сетки;
- того же параметра жёсткости нелинейного фазового замка `kappa`.

## RU — Обратное декодирование

Обратное декодирование выполняет дискретное сопоставление байтовых кандидатов.

Для каждого закодированного адреса:

1. Считывается фазово-запертое комплексное значение.
2. Генерируются все 256 возможных байтовых фаз.
3. Каждая кандидатная фаза проходит через ту же функцию фазового замка.
4. Выбирается кандидат, ближайший к полученному фазово-запертому комплексному значению.
5. Индекс выбранного кандидата возвращается как декодированный байт.

Обратная операция:

фазово-запертое комплексное значение  
→ ближайший допустимый байтово-фазовый кандидат  
→ восстановленный байт

Декодированные байты собираются в исходном порядке.

## RU — Исходная длина байтовой последовательности

Декодер использует:

`original_byte_length`

Это значение определяет, сколько закодированных адресов нужно считать при восстановлении.

В текущем рабочем процессе полезной нагрузки это значение передаётся как внешние метаданные.

Контейнерная реализация может хранить эти метаданные вместе с полезной нагрузкой.

Рекомендуемые поля будущего контейнера:

- размер сетки;
- длина байтовой последовательности;
- идентификатор `kappa`;
- контрольная сумма;
- поле версии;
- данные целостности.

Текущий модуль реализует детерминированное ядро кодирования и декодирования.

## RU — Текстовый слой UTF-8

Кодирование текста выполняется через преобразование строки в байты UTF-8.

Байтовый слой остаётся первичным.

Текстовый слой восстанавливается после декодирования байтов.

Если восстановленные байты формируют некорректный UTF-8 текст, текстовый декодер возвращает структурированный статус декодирования.

Байтовый декодер остаётся контрольным механизмом точного восстановления полезной нагрузки.

## RU — Граница слоя безопасности

Текущая реализация определяет детерминированное ядро фазового кодирования.

Защищённая передача и хранение выполняются внешним контейнером безопасности.

Внешний слой безопасности может обеспечивать:

- конфиденциальность;
- аутентификацию;
- проверку целостности;
- обработку nonce;
- защиту от повторной передачи;
- криптографическое выведение ключей.

Параметр `kappa` управляет нелинейным фазово-замковым преобразованием.

Для защищённого хранения или передачи детерминированное ядро фазового кодирования объединяется с внешним криптографическим контейнером.

## RU — Логика верификации

Модуль проверяет полный детерминированный цикл:

исходный текст  
→ байтовая последовательность UTF-8  
→ разреженное трёхмерное фазовое кодирование  
→ нелинейное фазово-замковое преобразование  
→ обратное сопоставление кандидатов  
→ восстановленная байтовая последовательность  
→ восстановленный текст  
→ сравнение с исходным текстом

Модуль также проверяет произвольные байтовые полезные нагрузки, включая полный диапазон байтов:

`0..255`

Проверка проходит при полном совпадении восстановленных байтов с исходной байтовой последовательностью.

## RU — Основные параметры состояния

`grid_size`

Длина стороны кубической трёхмерной адресной сетки.

`shape`

Форма сетки:

`grid_size × grid_size × grid_size`

`capacity`

Максимальное количество байтов, адресуемое текущей сеткой:

`grid_size^3`

`kappa`

Параметр жёсткости нелинейного фазового замка.

## RU — Основные методы

### `encode_bytes_to_grid()`

Кодирует байтовую последовательность в разреженную трёхмерную комплексную сетку.

### `encode_text_to_grid()`

Кодирует строку UTF-8 в разреженную трёхмерную комплексную сетку.

### `generate_locked_payload()`

Применяет нелинейное фазово-замковое преобразование к разреженной комплексной сетке.

### `decode_locked_payload_to_bytes()`

Восстанавливает исходную байтовую последовательность через сопоставление 256 фазовых кандидатов.

### `decode_locked_payload_to_text()`

Восстанавливает текст UTF-8 из декодированных байтов и возвращает статус декодирования.

### `verify_text_cycle()`

Проверяет полный цикл кодирования-декодирования текста.

### `verify_bytes_cycle()`

Проверяет полный цикл кодирования-декодирования произвольной байтовой последовательности.

## RU — Обратно совместимые псевдонимы методов

Модуль сохраняет совместимые с репозиторием псевдонимы для прежних имён методов.

`encode_bytes_to_7d()`

Псевдоним `encode_bytes_to_grid()`.

`encode_string_to_7d()`

Псевдоним `encode_text_to_grid()`.

`generate_6d_torus_payload()`

Псевдоним `generate_locked_payload()`.

`decode_7d_to_bytes()`

Псевдоним `decode_locked_payload_to_bytes()`.

`decode_7d_to_string()`

Псевдоним `decode_locked_payload_to_text()`.

## RU — Зависимости

Модулю требуется:

`numpy>=1.26.0`

## RU — Версия Python

Python 3.10 или новее.

## RU — Установка

`pip install numpy`

## RU — Команда запуска

Из корня репозитория:

`python module_marnov_protocol_reverse_decoding/marnov_reverse_decoder.py`

## RU — Ожидаемый вывод

Демонстрационный запуск печатает:

- циклы проверки текста;
- результаты декодирования текста;
- проверку байтов для полного диапазона `0..255`;
- итоговый статус проверки.

Успешный запуск подтверждает детерминированную согласованность цикла кодирования-декодирования.

## RU — Структура модуля

`module_marnov_protocol_reverse_decoding/README_EN_RU.md`

`module_marnov_protocol_reverse_decoding/marnov_reverse_decoder.py`

## RU — Статус

Статус модуля:

рабочий детерминированный прототип фазового кодирования.

Слой:

вспомогательный слой обратного декодирования Протокола Марнова.

Функция:

детерминированное кодирование байта в фазу, нелинейное фазово-замковое преобразование и обратное восстановление байтов через дискретное сопоставление кандидатов.
