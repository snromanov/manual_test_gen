# Manual Test Generator

> LLM-powered генератор ручных тест-кейсов по стандартам ISTQB с экспортом в Allure TestOps

Проект позволяет описать требования в простом Markdown, сгенерировать исчерпывающий набор ручных тест-кейсов с помощью LLM, проверить покрытие >= 95% и экспортировать результат в CSV для импорта в Allure TestOps.

## Ключевые возможности

- **Markdown-вход** — требования пишутся в естественном формате, как в задачах
- **ISTQB-техники** — equivalence partitioning, boundary value analysis, decision tables, state transitions, error guessing
- **Покрытие >= 95%** — автоматическая проверка с матрицей трассировки
- **Allure TestOps CSV** — экспорт с `[step N]`/`[expected N]` синтаксисом сценариев
- **HTML-отчёт** — интерактивный dark-theme дашборд с gauge, анимациями и трассировкой
- **Инкрементальная генерация** — батчи по 3-5 тест-кейсов с чекпоинтами

## Быстрый старт

```bash
# 1. Установка
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Проверка окружения
PYTHONPATH=. python3 utils/check_env.py

# 3. Запуск генерации через LLM CLI агент
LLM_CLI "read agent_rules.md and follow the instructions"
```

Или вручную по шагам — см. раздел [Рабочий поток](#рабочий-поток).

## Структура проекта

```
├── agent_rules.md                      # Инструкции для LLM-агента
├── requirements.txt                    # pinned: PyYAML, Jinja2, pytest
├── requirements_input/
│   ├── requirements.yaml               # Конфиг: проект, модуль, предусловия
│   └── requirements.md                 # Требования в Markdown
├── prompts/
│   └── generate_testcases.jinja2       # Промпт-шаблон с ISTQB-техниками
├── utils/
│   ├── parse_requirements.py           # Парсер Markdown → структура
│   ├── render_prompt.py                # Рендер промпта из Jinja2 + контекста
│   ├── write_testcases_incremental.py  # Инкрементальная сборка YAML
│   ├── validate_coverage.py            # Валидация покрытия >= 95%
│   ├── export_allure_csv.py            # YAML → Allure TestOps CSV
│   ├── report_generator.py             # HTML-отчёт с дашбордом
│   ├── checkpoint_manager.py           # Состояние агента
│   ├── check_env.py                    # Проверка окружения
│   └── logger_config.py               # Логирование
├── output/                             # Генерируемые артефакты
│   ├── testcases_output.yaml
│   └── testcases_allure.csv
└── reports/
    └── coverage_report.html
```

## Формат требований

Файл `requirements_input/requirements.md` — требования в том виде, как их пишут в задачах:

```markdown
## REQ_001 [Front] Отображение календаря

- Есть возможность посмотреть все созданные события в календаре
  в статусах "черновик" и "запланировано"
- Календарь расположен в разделе в домиках над администрированием
- В календаре есть цветовая индикация событий по сообществам
- Текущая дата подсвечивается красным цветом

## REQ_002 [Back] Валидация данных события

- Сервер валидирует все обязательные поля
- При невалидных данных возвращается HTTP 400 с описанием ошибок
- Название: минимум 3 символа, максимум 200 символов
```

**Правила:**
- `## REQ_NNN` — заголовок с ID (обязательно)
- `[Front]`, `[Back]` — тег слоя (опционально, попадает в теги тест-кейсов)
- Буллеты `- ...` — критерии приёмки

Метаданные (проект, модуль, предусловия) задаются в `requirements_input/requirements.yaml`:

```yaml
project: "Demo Project"
module: "Календарь событий"
test_level: "system"
language: "ru"
tags_prefix: "module:calendar"
requirements_file: "requirements_input/requirements.md"

global_preconditions:
  - "Приложение развёрнуто и доступно"
  - "Пользователь авторизован с ролью администратора"
```

## Формат тест-кейсов (YAML)

LLM генерирует тест-кейсы в промежуточном YAML-формате:

```yaml
testcases:
  - id: "TC_001"
    title: "Отображение событий в календаре"
    description: "Проверка что отображаются события в статусах черновик и запланировано"
    requirement_ids:
      - "REQ_001"
    priority: "high"
    type: "positive"              # positive | negative | boundary
    preconditions: |
      1. Пользователь авторизован
      2. В системе есть события в разных статусах
    steps:
      - step: 1
        action: "Перейти в раздел Календарь"
        expected: "Отображается календарь с событиями"
      - step: 2
        action: "Проверить наличие событий в статусе 'черновик'"
        expected: "События со статусом 'черновик' отображаются"
    tags: "module:calendar,front,positive,equivalence"
    notes: ""
```

**Типы ID:** `TC_001` (позитивные), `TC_NEG_001` (негативные), `TC_BVA_001` (граничные)

## Allure TestOps CSV

Экспортируемый CSV содержит колонки, совместимые с импортом в Allure TestOps:

| Колонка           | Описание                                    |
| ----------------- | ------------------------------------------- |
| `allure_id`       | ID тест-кейса (TC_001)                      |
| `Name`            | Название                                    |
| `Description`     | Описание                                    |
| `Precondition`    | Предусловия                                 |
| `Scenario`        | Шаги в формате `[step N]`/`[expected N]`    |
| `Expected result` | Ожидаемый результат последнего шага          |
| `Tags`            | Теги через запятую                          |

Пример ячейки `Scenario`:
```
[step 1] Перейти в раздел Календарь
[expected 1] Отображается календарь с событиями
[step 2] Проверить цветовую индикацию
[expected 2] Цвета соответствуют настройкам сообществ
```

## Рабочий поток

### Автоматический (через LLM-агент)

```bash
LLM CLI agent "read agent_rules.md and follow the instructions"
```

Агент сам пройдёт все шаги: парсинг требований, генерация, валидация, экспорт.

### Ручной (пошагово)

```bash
# 1. Парсинг требований
PYTHONPATH=. python3 utils/parse_requirements.py

# 2. Рендер промпта для конкретного батча требований
PYTHONPATH=. python3 utils/render_prompt.py --req-ids REQ_001 REQ_002 --output prompt_batch_1.txt

# 3. Инициализация буфера
python3 utils/write_testcases_incremental.py --init --project "My Project"

# 4. Добавление тест-кейсов порциями
python3 utils/write_testcases_incremental.py --append part_1.yaml part_2.yaml --sync

# 5. Финализация
python3 utils/write_testcases_incremental.py --finalize --sync

# 6. Валидация покрытия
PYTHONPATH=. python3 utils/validate_coverage.py          # консоль
PYTHONPATH=. python3 utils/validate_coverage.py --html    # + HTML-отчёт
PYTHONPATH=. python3 utils/validate_coverage.py --json    # JSON

# 7. Экспорт в Allure CSV
PYTHONPATH=. python3 utils/export_allure_csv.py
```

## ISTQB-техники

Генератор применяет 5 техник тест-дизайна из ISTQB Foundation Level:

| Техника                  | Применение                                     | Тег                |
| ------------------------ | ---------------------------------------------- | ------------------ |
| Equivalence Partitioning | Классы эквивалентности для каждого параметра    | `equivalence`      |
| Boundary Value Analysis  | Границы: min, max, min-1, max+1                | `bva`              |
| Decision Table           | Комбинации условий и правил                    | `decision_table`   |
| State Transition         | Переходы между статусами                       | `state_transition` |
| Error Guessing           | Пустой ввод, XSS, спецсимволы, SQL-инъекции    | `error_guessing`   |

## Требования к окружению

- Python 3.10+
- Зависимости: `PyYAML`, `Jinja2` (см. pinned версии в `requirements.txt`)
- Для автоматической генерации: LLM CLI агент (например, Qwen, Claude и др.)

## Тесты

```bash
pytest -q
```

## Безопасность

- Не добавляйте секреты, токены и персональные данные в требования и тест-кейсы
- Для тестов используйте обезличенные/синтетические данные
- Перед публикацией проверяйте содержимое `output/` и `reports/`
- Runtime-файлы (`agent_state.json`, логи, output) исключены из git через `.gitignore`
