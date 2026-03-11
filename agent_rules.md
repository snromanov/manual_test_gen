# Инструкции для ИИ-ассистента (LLM CLI агент)

Работай по этим правилам. Без исключений.

## ОБЩИЕ ПРИНЦИПЫ
- Честность: Никакой фантазии. Если чего-то не знаешь — пиши «не знаю».
- Прозрачность: Указывай базу ответа (ввод, память, догадка).
- Ограничения: Не имитируй асинхронность. «Готово» — только по реальному завершению.
- Ответы: Четкие, без воды, поэтапные для сложных задач.

## БЫСТРЫЙ СТАРТ (ОБЯЗАТЕЛЬНО)
При каждом запуске или перезапуске:
```bash
PYTHONPATH=. python3 utils/check_env.py && python3 utils/checkpoint_manager.py --get
```
**Логика переходов:**
- `current_step == "init"` → Переходи к **Шагу 0**.
- Есть `completed_steps` → **ПРОПУСТИ** их и переходи к первому незавершенному.
- `current_step == "generating_testcases"` → Продолжай генерацию с учётом `testcases_generated`.

---

## ШАГ 0: ПОДГОТОВКА
```bash
python3 utils/checkpoint_manager.py --update "prepare_context"
```

---

## ШАГ 1: СБОР КОНТЕКСТА
Прочитай (если ещё не читал):
1. `requirements_input/requirements.yaml` — конфиг проекта (module, preconditions, tags)
2. `requirements_input/requirements.md` — **требования в Markdown-формате**
3. `prompts/generate_testcases.jinja2` — шаблон промпта и формат вывода

**ФОРМАТ ТРЕБОВАНИЙ (Markdown):**
Требования пишутся в файле .md в свободном формате:
```markdown
## REQ_001 [Front] Заголовок требования
- Критерий/пункт 1
- Критерий/пункт 2

## REQ_002 [Back] Другое требование
- Пункт 1
```
ID берётся из заголовка (REQ_NNN), тег в скобках [Front/Back] — опционален.

Для парсинга требований:
```bash
PYTHONPATH=. python3 utils/parse_requirements.py --json
```

Из вывода определи:
- Количество требований
- Модуль и проект
- Глобальные предусловия

```bash
python3 utils/checkpoint_manager.py --set-req КОЛИЧЕСТВО_ТРЕБОВАНИЙ "ИМЯ_ПРОЕКТА"
```

---

## ШАГ 2: ГЕНЕРАЦИЯ ТЕСТ-КЕЙСОВ (ИНКРЕМЕНТАЛЬНО)
КРИТИЧЕСКИ ВАЖНО: Пиши тест-кейсы порциями по 3–5 штук, чтобы избежать таймаутов.

### Алгоритм:
1. **Инициализация** (один раз):
   ```bash
   python3 utils/write_testcases_incremental.py --init --project "ИМЯ_ПРОЕКТА"
   python3 utils/checkpoint_manager.py --update "generating_testcases" --status "in_progress"
   ```

2. **Цикл генерации (по 3-5 тест-кейсов):**
   - Используя промпт из generate_testcases.jinja2, подставь требования и сгенерируй YAML для порции тест-кейсов.
   - Запиши в `part_N.yaml` (например, part_1.yaml, part_2.yaml, ...).
   - Добавь в буфер:
     ```bash
     python3 utils/write_testcases_incremental.py --append part_N.yaml --sync
     ```
   - Если контекст близок к пределу — скажи пользователю "Нужен перезапуск".

3. **Финализация:**
   ```bash
   python3 utils/write_testcases_incremental.py --finalize --sync
   python3 utils/checkpoint_manager.py --update "testcases_finalized"
   ```

### Правила генерации по ISTQB:
- **Каждое требование** должно быть покрыто минимум 1 позитивным и 1 негативным тест-кейсом
- Применяй техники: эквивалентное разбиение, анализ граничных значений, таблицы решений, переходы состояний, предугадывание ошибок
- ID: TC_001 (позитивные), TC_NEG_001 (негативные), TC_BVA_001 (граничные)
- Шаги — конкретные действия для ручного тестировщика
- К каждому шагу — ожидаемый результат
- Каждый тест-кейс ссылается на requirement_ids

---

## ШАГ 3: ВАЛИДАЦИЯ ПОКРЫТИЯ
```bash
python3 utils/validate_coverage.py
```
- Если покрытие < 95% — сгенерируй дополнительные тест-кейсы для непокрытых требований.
- Если есть orphan-тесты — исправь ссылки на requirement_ids.
- Повтори валидацию до достижения >= 95%.

```bash
python3 utils/checkpoint_manager.py --update "validated"
```

Для HTML-отчёта:
```bash
python3 utils/validate_coverage.py --html
```

---

## ШАГ 4: ЭКСПОРТ В CSV ДЛЯ ALLURE TESTOPS
```bash
python3 utils/export_allure_csv.py
python3 utils/checkpoint_manager.py --update "exported"
```
Файл: `output/testcases_allure.csv`

---

## СТАНДАРТЫ КАЧЕСТВА (КРИТИЧЕСКИ ВАЖНО)
- **Покрытие**: >= 95% требований (каждое требование → минимум 1 тест-кейс)
- **ISTQB-техники**: Обязательно применять минимум 3 из 5 техник
- **Полнота**: Позитивные + негативные + граничные тест-кейсы
- **Шаги**: Конкретные, выполнимые вручную, с ожидаемыми результатами
- **Трассировка**: Каждый тест-кейс ссылается на requirement_ids
- **Теги**: module + техника + тип (positive/negative/boundary)

## ФОРМАТ YAML ТЕСТ-КЕЙСА (ОБЯЗАТЕЛЬНО)
```yaml
- id: "TC_001"
  title: "Краткое описание"
  description: "Детальное описание"
  requirement_ids: ["REQ_001"]
  priority: "high"
  type: "positive"
  preconditions: |
    1. Предусловие 1
    2. Предусловие 2
  steps:
    - step: 1
      action: "Действие"
      expected: "Ожидаемый результат"
  tags: "module:auth,positive,equivalence"
  notes: ""
```

## ТЕХНИЧЕСКИЕ ПРАВИЛА
- Используй `python3` для всех скриптов в utils/.
- КРИТИЧЕСКИ ВАЖНО: При вызове shell-команд обязательно передавай `is_background: false`.
- Не используй `run_shell_command` для передачи больших YAML (используй `create_file` + `append`).
- Всегда информируй о прогрессе (X/Y тест-кейсов).
