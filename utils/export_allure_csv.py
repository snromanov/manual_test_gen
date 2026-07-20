#!/usr/bin/env python3
"""
Exports test cases from YAML into the Allure TestOps CSV format.

Shape of the Scenario cell in Allure TestOps:
  [step N] Action
  [expected N] Expected result
  Lines are separated by \n.
  Nested steps start with \t.
"""
import csv
import sys
import yaml
from pathlib import Path

from utils.logger_config import get_logger

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
    """Convert a list of steps into the Allure TestOps Scenario format.

    Shape:
        [step 1] Action 1
        [expected 1] Expected result 1
        [step 2] Action 2
        [expected 2] Expected result 2
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
    """Return the expected result of the last step, used for the Expected result column."""
    if not steps:
        return ""
    last_step = steps[-1]
    return last_step.get('expected', '')


def export_to_csv(input_path: str = TESTCASES_FILE, output_path: str = CSV_OUTPUT_FILE):
    """Export testcases_output.yaml to a CSV for Allure TestOps."""
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"File not found: {input_path}")
        return False

    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    testcases = data.get('testcases', [])
    if not testcases:
        logger.error("No test cases to export")
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

    logger.info(f"Exported {len(testcases)} test case(s) to {output_path}")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export test cases to an Allure TestOps CSV")
    parser.add_argument("--input", type=str, default=TESTCASES_FILE, help="Input YAML file")
    parser.add_argument("--output", type=str, default=CSV_OUTPUT_FILE, help="Output CSV file")

    args = parser.parse_args()

    success = export_to_csv(args.input, args.output)
    sys.exit(0 if success else 1)
