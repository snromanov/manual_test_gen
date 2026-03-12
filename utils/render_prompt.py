#!/usr/bin/env python3
"""Render Jinja2 prompt for testcase generation from project requirements context."""
import argparse
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from utils.logger_config import get_logger
from utils.parse_requirements import load_config_and_requirements

logger = get_logger(__name__)


def parse_req_ids(raw_values: list[str] | None) -> list[str]:
    if not raw_values:
        return []

    ids: list[str] = []
    seen = set()
    for raw in raw_values:
        for part in raw.split(','):
            req_id = part.strip().upper()
            if not req_id:
                continue
            if req_id not in seen:
                seen.add(req_id)
                ids.append(req_id)
    return ids


def select_requirements(requirements: list[dict], req_ids: list[str], offset: int, limit: int | None) -> list[dict]:
    if req_ids:
        by_id = {r.get("id", "").upper(): r for r in requirements}
        missing = [req_id for req_id in req_ids if req_id not in by_id]
        if missing:
            raise ValueError(f"Требования не найдены: {', '.join(missing)}")
        selected = [by_id[req_id] for req_id in req_ids]
    else:
        selected = list(requirements)

    if offset < 0:
        raise ValueError("--offset должен быть >= 0")

    selected = selected[offset:]
    if limit is not None:
        if limit <= 0:
            raise ValueError("--limit должен быть > 0")
        selected = selected[:limit]

    return selected


def render_prompt(config_path: str, template_path: str, req_ids: list[str], offset: int, limit: int | None) -> str:
    context = load_config_and_requirements(config_path)
    requirements = context.get("requirements", [])

    if not requirements:
        raise ValueError("Требования не найдены. Проверьте requirements_input/requirements.md")

    selected = select_requirements(requirements, req_ids, offset, limit)
    if not selected:
        raise ValueError("После фильтрации не осталось требований для рендера.")

    template_file = Path(template_path)
    if not template_file.exists():
        raise ValueError(f"Шаблон не найден: {template_path}")

    env = Environment(
        loader=FileSystemLoader(str(template_file.parent)),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )

    template = env.get_template(template_file.name)

    render_context = dict(context)
    render_context["requirements"] = selected
    render_context["selected_requirement_ids"] = [r["id"] for r in selected]
    render_context["batch_size"] = len(selected)

    return template.render(**render_context)


def main() -> int:
    parser = argparse.ArgumentParser(description="Рендер промпта генерации тест-кейсов из Jinja2")
    parser.add_argument("--config", default="requirements_input/requirements.yaml", help="Путь к YAML-конфигу")
    parser.add_argument("--template", default="prompts/generate_testcases.jinja2", help="Путь к Jinja2-шаблону")
    parser.add_argument(
        "--req-ids",
        nargs="+",
        help="Список requirement ID (через пробел или запятую), например: REQ_001 REQ_002",
    )
    parser.add_argument("--offset", type=int, default=0, help="Сдвиг по отфильтрованному списку требований")
    parser.add_argument("--limit", type=int, help="Максимум требований для рендера")
    parser.add_argument("--output", help="Файл для сохранения промпта; по умолчанию stdout")

    args = parser.parse_args()

    try:
        req_ids = parse_req_ids(args.req_ids)
        rendered = render_prompt(args.config, args.template, req_ids, args.offset, args.limit)
    except ValueError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Не удалось отрендерить промпт: {e}")
        return 1

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        logger.info(f"Промпт сохранён: {out_path}")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
