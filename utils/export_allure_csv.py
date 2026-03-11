#!/usr/bin/env python3
"""
Экспорт тест-кейсов из YAML в CSV формат Allure TestOps.

Формат Scenario-ячейки в Allure TestOps:
  [step N] Действие
  [expected N] Ожидаемый результат
  Строки разделяются символом \n.
  Вложенные шаги начинаются с \t.
"""
import csv
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

TESTCASES_FILE = "output/testcases_output.yaml"
CSV_OUTPUT_FILE = "output/testcases_allure.csv"

CSV_COLUMNS = [
    "allure_id",
    "Name",
    "Description",
    "Precondition",
    "Scenario",
    "Expected result",
    "Tags",
]


def format_scenario(steps: list) -> str:
    """Конвертация списка шагов в формат Allure TestOps Scenario.

    Формат:
        [step 1] Действие 1
        [expected 1] Ожидаемый результат 1
        [step 2] Действие 2
        [expected 2] Ожидаемый результат 2
    """
    lines = []
    for s in steps:
        step_num = s.get('step', 0)
        action = s.get('action', '')
        expected = s.get('expected', '')
        lines.append(f"[step {step_num}] {action}")
        if expected:
            lines.append(f"[expected {step_num}] {expected}")
    return "\n".join(lines)


def get_final_expected(steps: list) -> str:
    """Получить ожидаемый результат последнего шага (для поля Expected result)."""
    if not steps:
        return ""
    last_step = steps[-1]
    return last_step.get('expected', '')


def export_to_csv(input_path: str = TESTCASES_FILE, output_path: str = CSV_OUTPUT_FILE):
    """Экспорт testcases_output.yaml в CSV для Allure TestOps."""
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Файл не найден: {input_path}")
        return False

    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    testcases = data.get('testcases', [])
    if not testcases:
        logger.error("Нет тест-кейсов для экспорта")
        return False

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for tc in testcases:
            steps = tc.get('steps', [])
            row = {
                "allure_id": tc.get('id', ''),
                "Name": tc.get('title', ''),
                "Description": tc.get('description', ''),
                "Precondition": tc.get('preconditions', '').strip(),
                "Scenario": format_scenario(steps),
                "Expected result": get_final_expected(steps),
                "Tags": tc.get('tags', ''),
            }
            writer.writerow(row)

    logger.info(f"Экспортировано {len(testcases)} тест-кейсов в {output_path}")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Экспорт тест-кейсов в Allure TestOps CSV")
    parser.add_argument("--input", type=str, default=TESTCASES_FILE, help="Входной YAML")
    parser.add_argument("--output", type=str, default=CSV_OUTPUT_FILE, help="Выходной CSV")

    args = parser.parse_args()

    success = export_to_csv(args.input, args.output)
    sys.exit(0 if success else 1)
