[English](README.md) | Русский | [中文](README.zh.md)

# Manual Test Generator

Набор инструментов, который по текстовым требованиям генерирует ручные тест-кейсы с помощью LLM, проверяет полноту покрытия и выгружает результат в CSV для импорта в Allure TestOps.

Python-код в репозитории отвечает за детерминированную часть: разбор требований, сборку промпта, валидацию сгенерированного YAML, подсчёт покрытия и запись CSV. Сам текст тест-кейсов пишет LLM. Клиента к API здесь нет. Генерацией управляет тот LLM CLI агент, которым вы уже пользуетесь, а файл `agent_rules.md` объясняет агенту, какие скрипты и в каком порядке вызывать.

## Ключевые возможности

- Требования пишутся обычным Markdown: заголовки и буллеты. Никакой схемы учить не нужно.
- Шаблон промпта требует применить пять техник тест-дизайна ISTQB Foundation Level и проставить тег использованной техники каждому кейсу.
- Валидация покрытия строит матрицу трассировки требование к тест-кейсам и падает, если покрытие ниже 95 процентов.
- Экспорт формирует синтаксис сценария `[step N]` / `[expected N]`, который ожидает Allure TestOps.
- Автономный HTML-отчёт о покрытии со шкалой, распределением по техникам и полной матрицей.
- Инкрементальная запись. Тест-кейсы приходят небольшими порциями, проходят валидацию и проверку на дубликаты по пути в буфер, и становятся итоговым файлом только при финализации.
- Файл чекпоинта хранит прогресс, поэтому долгий прогон генерации можно продолжить после перезапуска агента.

## Быстрый старт

```bash
# 1. Установка
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Проверка окружения (заодно создаёт output/ и reports/)
PYTHONPATH=. python3 utils/check_env.py

# 3. Опишите требования
#    отредактируйте requirements_input/requirements.md и requirements_input/requirements.yaml

# 4. Передайте работу LLM CLI агенту
<ваш-llm-cli> "read agent_rules.md and follow the instructions"
```

Все скрипты в `utils/`, кроме `checkpoint_manager.py`, импортируют пакет `utils`, поэтому из корня репозитория их нужно запускать с `PYTHONPATH=.`. Если хотите пройти шаги руками, а не отдавать агенту, смотрите раздел [Рабочий поток](#рабочий-поток).

## Структура проекта

```
├── agent_rules.md                      # Пошаговые инструкции для LLM-агента
├── requirements.txt                    # Зафиксированные версии: PyYAML, Jinja2, pytest
├── requirements_input/
│   ├── requirements.yaml               # Проект, модуль, теги, глобальные предусловия
│   └── requirements.md                 # Сами требования
├── prompts/
│   └── generate_testcases.jinja2       # Шаблон промпта с техниками ISTQB
├── templates/
│   └── coverage_report.html.tpl        # Шаблон HTML-отчёта
├── utils/
│   ├── parse_requirements.py           # Markdown в структурированные требования
│   ├── render_prompt.py                # Рендер Jinja2-промпта для батча
│   ├── write_testcases_incremental.py  # Буфер YAML с валидацией и дедупликацией
│   ├── validate_coverage.py            # Проверка покрытия и матрица трассировки
│   ├── export_allure_csv.py            # YAML в CSV для Allure TestOps
│   ├── report_generator.py             # Заполнение шаблона HTML-отчёта
│   ├── checkpoint_manager.py           # Состояние прогресса агента
│   ├── check_env.py                    # Проверка окружения
│   └── logger_config.py                # Логи в консоль и в ротируемый файл
├── tests/                              # Набор тестов на pytest
├── output/                             # Создаётся во время работы
│   ├── testcases_output.yaml
│   └── testcases_allure.csv
└── reports/
    └── coverage_report.html
```

`output/`, `reports/`, лог-файлы, `agent_state.json`, `testcases_buffer.yaml` и `part_*.yaml` перечислены в `.gitignore`.

## Формат требований

В `requirements_input/requirements.md` требования лежат в том виде, в каком их обычно пишут в задаче:

```markdown
## REQ_001 [Front] Event calendar display
- The user opens the calendar section and sees a list or grid of events.
- Each event shows its main attributes: name, date, status.
- The interface behaves correctly when there are no events.

## REQ_002 [Back] Input validation and error handling
- The system rejects malformed data: dates, field lengths, special characters.
- A validation error produces a message the user can act on.
```

Демо-требования в репозитории написаны по-английски, потому что проект рассчитан на международную аудиторию. Писать требования можно на любом языке, парсер работает с юникодом.

Правила разбора, как они реализованы в `utils/parse_requirements.py`:

- `## REQ_NNN` начинает требование. ID обязателен и приводится к верхнему регистру.
- Теги в квадратных скобках, `[Front]`, `[Back]` и подобные, опциональны. Тег передаётся в промпт, и модель просят перенести его в теги тест-кейсов.
- Остаток строки заголовка становится названием требования.
- Буллеты `- ` под заголовком становятся критериями приёмки. Строка с отступом после буллета приклеивается к нему, так что критерий может занимать несколько строк.
- Всё, что идёт до первого заголовка `## REQ_NNN`, игнорируется.

Метаданные проекта лежат в `requirements_input/requirements.yaml`:

```yaml
project: "Demo Project"
version: "1.0"
module: "Event calendar"
test_level: "system"
language: "en"
tags_prefix: "module:calendar"

requirements_file: "requirements_input/requirements.md"

global_preconditions:
  - "The application is deployed and reachable"
  - "The user is signed in with the administrator role"
  - "Communities with colour coding are configured in the admin panel"
```

`language` задаёт язык, на котором промпт просит модель писать тест-кейсы. Поставьте `ru`, и модель будет писать кейсы по-русски, сам инструмент от этого не изменится. `tags_prefix` подставляется в начало каждой строки тегов.

## Формат тест-кейсов (YAML)

LLM пишет тест-кейсы в файлы `part_N.yaml` вот в таком виде, и `write_testcases_incremental.py` проверяет каждый из них перед добавлением в буфер:

```yaml
testcases:
  - id: "TC_001"
    title: "Events are displayed in the calendar"
    description: "Verifies that draft and scheduled events both appear"
    requirement_ids:
      - "REQ_001"
    priority: "high"
    type: "positive"              # positive | negative | boundary
    preconditions: |
      1. The user is signed in
      2. Events exist in several statuses
    steps:
      - step: 1
        action: "Open the Calendar section"
        expected: "The calendar renders with its events"
      - step: 2
        action: "Look for events in draft status"
        expected: "Draft events are visible"
    tags: "module:calendar,front,positive,equivalence"
    notes: ""
```

Обязательные поля: `id`, `title`, `requirement_ids`, `steps`, `type`. `requirement_ids` должен быть непустым списком непустых строк. У каждого шага нужен целый `step` больше нуля и непустые `action` и `expected`. Файл, не прошедший валидацию, отклоняется целиком, ни один кейс из него в буфер не попадёт. Тест-кейсы с уже существующим в буфере `id` пропускаются с предупреждением.

Соглашение об идентификаторах из промпта: `TC_001` для позитивных кейсов, `TC_NEG_001` для негативных, `TC_BVA_001` для граничных.

## CSV для Allure TestOps

`export_allure_csv.py` пишет `output/testcases_allure.csv`, все поля берутся в кавычки:

| Колонка           | Источник                                        |
| ----------------- | ----------------------------------------------- |
| `allure_id`       | `id`                                            |
| `Name`            | `title`                                         |
| `Description`     | `description`                                   |
| `Precondition`    | `preconditions`, обрезанные пробелы             |
| `Scenario`        | Шаги строками `[step N]` / `[expected N]`       |
| `Expected result` | `expected` последнего шага                      |
| `Tags`            | `tags`, через запятую                           |

Ячейка `Scenario` выглядит так, с реальными переводами строк внутри поля в кавычках:

```
[step 1] Open the Calendar section
[expected 1] The calendar renders with its events
[step 2] Check the per community colour coding
[expected 2] Colours match the community settings
```

## Рабочий поток

### Через LLM-агента

```bash
<ваш-llm-cli> "read agent_rules.md and follow the instructions"
```

`agent_rules.md` проводит агента через проверку окружения, сбор контекста, генерацию порциями по три-пять кейсов, валидацию покрытия с повтором до достижения порога и экспорт в CSV. Прогресс пишется в `agent_state.json` после каждого этапа, поэтому агента, у которого кончился контекст, можно перезапустить, и он продолжит с места остановки.

### Вручную

```bash
# 1. Разобрать требования и посмотреть, что распозналось
PYTHONPATH=. python3 utils/parse_requirements.py
PYTHONPATH=. python3 utils/parse_requirements.py --json

# 2. Отрендерить промпт для одного батча требований
PYTHONPATH=. python3 utils/render_prompt.py --req-ids REQ_001 REQ_002 --output prompt_batch_1.txt
PYTHONPATH=. python3 utils/render_prompt.py --offset 0 --limit 3    # либо нарезать список

# 3. Отправить промпт модели, сохранить полученный YAML как part_1.yaml

# 4. Инициализировать буфер
PYTHONPATH=. python3 utils/write_testcases_incremental.py --init --project "My Project"

# 5. Добавлять батчи по мере готовности
PYTHONPATH=. python3 utils/write_testcases_incremental.py --append part_1.yaml part_2.yaml --sync
PYTHONPATH=. python3 utils/write_testcases_incremental.py --status

# 6. Финализировать, буфер переезжает в output/testcases_output.yaml
PYTHONPATH=. python3 utils/write_testcases_incremental.py --finalize --sync

# 7. Проверить покрытие
PYTHONPATH=. python3 utils/validate_coverage.py           # отчёт в консоль
PYTHONPATH=. python3 utils/validate_coverage.py --html    # плюс reports/coverage_report.html
PYTHONPATH=. python3 utils/validate_coverage.py --json    # машиночитаемый вывод

# 8. Экспорт
PYTHONPATH=. python3 utils/export_allure_csv.py
```

Флаг `--sync` у инкрементального писателя обновляет счётчик тест-кейсов в `agent_state.json`. Если чекпоинт не используете, флаг можно не ставить.

`validate_coverage.py` завершается с кодом 1, когда покрытие ниже 95 процентов, так что его удобно использовать как гейт в CI. Кроме процента он сообщает, у каких требований нет негативного тест-кейса, какие техники ISTQB ни разу не применялись, и какие тест-кейсы остались сиротами, то есть без `requirement_ids` или со ссылкой на несуществующее требование.

### HTML-отчёт

Флаг `--html` рендерит `reports/coverage_report.html`, автономную страницу в тёмной теме со шкалой покрытия, счётчиками, столбчатой диаграммой распределения техник, матрицей трассировки с колонками позитивных, негативных и граничных кейсов по каждому требованию, и списком рекомендаций.

![Отчёт о покрытии](docs/report.png)

*Отчёт о покрытии: шкала, распределение техник ISTQB и матрица трассировки требование к тест-кейсам.*

## Техники ISTQB

Шаблон промпта требует применить пять техник тест-дизайна уровня Foundation. `validate_coverage.py` считает, сколько тест-кейсов помечено тегом каждой техники, и предупреждает о тех, которые ни разу не встретились.

| Техника                  | Что требует промпт                                                     | Тег                |
| ------------------------ | ---------------------------------------------------------------------- | ------------------ |
| Equivalence Partitioning | Валидные и невалидные классы по каждому параметру, кейс на класс        | `equivalence`      |
| Boundary Value Analysis  | min, max, min-1, max+1 везде, где в критерии есть число                 | `bva`              |
| Decision Table           | Значимые комбинации, когда в требовании несколько условий               | `decision_table`   |
| State Transition         | Кейс на каждый переход, когда требование описывает статусы              | `state_transition` |
| Error Guessing           | Пустой ввод, спецсимволы, SQL-инъекции, XSS, длинные строки             | `error_guessing`   |

Промпт также требует минимум один позитивный и один негативный кейс на требование и обязательное поле `type` со значением `positive`, `negative` или `boundary`.

## Требования к окружению

- Python 3.10 или новее. В коде используется синтаксис типов `X | None`.
- `PyYAML` и `Jinja2` во время работы, `pytest` для тестов. Версии зафиксированы в `requirements.txt`.
- LLM CLI агент на ваш выбор для генерации. Ничто в этом репозитории не ходит в API модели.
- `PYTHONPATH=.` при запуске скриптов из корня репозитория, кроме `utils/checkpoint_manager.py`, у которого нет импортов пакета.

Логи идут в stdout и в отдельный ротируемый файл на каждый модуль в текущей директории, ограничение 10 МБ и три бэкапа. Лог-файлы игнорируются гитом.

## Тесты

```bash
pytest -q
```

Девять тестов в пяти файлах покрывают разбор Markdown вместе с многострочными критериями, фильтрацию требований в рендерере промпта, подсчёт покрытия и сирот, правила валидации и дедупликации инкрементального писателя, а также экранирование HTML в генераторе отчёта.

## Безопасность

- Не кладите секреты, токены и персональные данные в требования и тест-кейсы. Всё, что попало в `requirements.md`, уходит в модель.
- В шагах используйте синтетические или обезличенные данные.
- Просматривайте `output/` и `reports/` перед тем, как ими делиться. Там лежит то, что модель сгенерировала из ваших требований.
- Генерируемые файлы, логи и состояние агента исключены из гита через `.gitignore`. Всё равно проверяйте `git status` перед коммитом.
- Везде используется `yaml.safe_load`, поэтому YAML от модели не сможет сконструировать произвольные Python-объекты.
- HTML-отчёт экранирует названия требований, ID тест-кейсов и текст рекомендаций перед вставкой в страницу, так что разметка, пришедшая из требований или из ответа модели, отображается как обычный текст.

## Лицензия

MIT. Смотрите [LICENSE](LICENSE).
