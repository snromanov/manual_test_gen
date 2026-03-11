#!/usr/bin/env python3
"""
Парсер требований из Markdown-файла.

Формат:
  ## REQ_001 [Front] Заголовок требования
  - пункт требования 1
  - пункт требования 2

  ## REQ_002 [Back] Другое требование
  - пункт 1

ID определяется по паттерну REQ_NNN в начале заголовка ## уровня.
Тег в квадратных скобках [Front], [Back] и т.д. — опционален, парсится как `tag`.
Всё остальное в заголовке — title.
Буллет-пойнты (- ...) под заголовком — acceptance_criteria.
"""
import re
import sys
import yaml
from pathlib import Path

try:
    from utils.logger_config import get_logger
except ImportError:
    try:
        from logger_config import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)

logger = get_logger(__name__)

# Паттерн заголовка: ## REQ_001 [Front] Заголовок
HEADER_PATTERN = re.compile(
    r'^##\s+'
    r'(REQ_\d+)'              # ID (обязательный)
    r'(?:\s+\[([^\]]+)\])?'   # [Tag] (опциональный)
    r'\s+(.*)',                # Title (остаток строки)
    re.IGNORECASE
)


def parse_requirements_md(md_path: str) -> list:
    """Парсит markdown-файл с требованиями и возвращает список dict."""
    path = Path(md_path)
    if not path.exists():
        logger.error(f"Файл не найден: {md_path}")
        return []

    text = path.read_text(encoding='utf-8')
    lines = text.split('\n')

    requirements = []
    current_req = None

    for line in lines:
        stripped = line.strip()

        # Проверяем заголовок ##
        match = HEADER_PATTERN.match(stripped)
        if match:
            # Сохраняем предыдущее требование
            if current_req:
                requirements.append(current_req)

            req_id = match.group(1).upper()
            tag = match.group(2) or ""
            title = match.group(3).strip()

            current_req = {
                'id': req_id,
                'tag': tag,
                'title': title,
                'criteria': [],
                'raw_text': ''
            }
            continue

        # Буллет-пойнт
        if current_req is not None:
            if stripped.startswith('- '):
                criterion = stripped[2:].strip()
                current_req['criteria'].append(criterion)
                current_req['raw_text'] += stripped + '\n'
            elif stripped and not stripped.startswith('#'):
                # Продолжение предыдущего буллета (многострочный)
                if current_req['criteria']:
                    current_req['criteria'][-1] += ' ' + stripped
                current_req['raw_text'] += stripped + '\n'

    # Последнее требование
    if current_req:
        requirements.append(current_req)

    logger.info(f"Распарсено {len(requirements)} требований из {md_path}")
    return requirements


def load_config_and_requirements(config_path: str = "requirements_input/requirements.yaml") -> dict:
    """Загружает конфиг YAML + парсит markdown-требования. Возвращает полный контекст."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    md_path = config.get('requirements_file', 'requirements_input/requirements.md')
    requirements = parse_requirements_md(md_path)

    return {
        'project_name': config.get('project', 'Unknown'),
        'version': config.get('version', '1.0'),
        'module_name': config.get('module', 'Unknown'),
        'test_level': config.get('test_level', 'system'),
        'language': config.get('language', 'ru'),
        'tags_prefix': config.get('tags_prefix', ''),
        'global_preconditions': config.get('global_preconditions', []),
        'requirements': requirements,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Парсер markdown-требований")
    parser.add_argument("--config", type=str, default="requirements_input/requirements.yaml")
    parser.add_argument("--md", type=str, help="Напрямую парсить MD файл (без конфига)")
    parser.add_argument("--json", action="store_true", help="Вывод в JSON")

    args = parser.parse_args()

    if args.md:
        reqs = parse_requirements_md(args.md)
        if args.json:
            import json
            print(json.dumps(reqs, indent=2, ensure_ascii=False))
        else:
            for r in reqs:
                print(f"\n{r['id']} [{r['tag']}] {r['title']}")
                for c in r['criteria']:
                    print(f"  - {c}")
    else:
        ctx = load_config_and_requirements(args.config)
        if args.json:
            import json
            print(json.dumps(ctx, indent=2, ensure_ascii=False))
        else:
            print(f"Проект: {ctx['project_name']}")
            print(f"Модуль: {ctx['module_name']}")
            print(f"Требований: {len(ctx['requirements'])}")
            for r in ctx['requirements']:
                print(f"  {r['id']} [{r['tag']}] {r['title']} ({len(r['criteria'])} критериев)")
