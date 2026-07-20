#!/usr/bin/env python3
"""Incremental, validated collection of generated test cases into a YAML buffer."""
import argparse
import sys
import subprocess
import yaml
from pathlib import Path
from typing import Any

from utils.logger_config import get_logger

logger = get_logger(__name__)


class TestcaseWriter:
    """Collects test cases batch by batch into a buffer, then promotes it to the output file."""
    __test__ = False

    BUFFER_FILE = "testcases_buffer.yaml"
    OUTPUT_FILE = "output/testcases_output.yaml"
    REQUIRED_FIELDS = ("id", "title", "requirement_ids", "steps", "type")

    def __init__(self, workspace_root=None, sync_checkpoint=False):
        if workspace_root:
            self.workspace = Path(workspace_root)
        else:
            self.workspace = Path(__file__).parent.parent

        self.buffer_path = self.workspace / self.BUFFER_FILE
        self.output_path = self.workspace / self.OUTPUT_FILE
        self.sync_checkpoint = sync_checkpoint

    def init(self, project_name):
        """Create the buffer file."""
        data = {
            'project': project_name,
            'testcases': []
        }

        with open(self.buffer_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info(f"Buffer file created: {self.BUFFER_FILE}")
        logger.info(f"  Project: {project_name}")
        return True

    @staticmethod
    def _is_non_empty_string(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def _validate_step(self, step: Any, step_idx: int, tc_id: str) -> list[str]:
        errors = []
        prefix = f"{tc_id}: step #{step_idx}"
        if not isinstance(step, dict):
            return [f"{prefix} must be an object"]

        step_num = step.get("step")
        action = step.get("action")
        expected = step.get("expected")

        if not isinstance(step_num, int) or step_num <= 0:
            errors.append(f"{prefix} has an invalid 'step' field (expected an integer > 0)")
        if not self._is_non_empty_string(action):
            errors.append(f"{prefix} has an empty 'action' field")
        if not self._is_non_empty_string(expected):
            errors.append(f"{prefix} has an empty 'expected' field")

        return errors

    def _validate_testcase(self, testcase: Any, index: int) -> list[str]:
        if not isinstance(testcase, dict):
            return [f"Element testcases[{index}] must be an object"]

        errors = []
        tc_id = testcase.get("id", f"testcases[{index}]")

        for field in self.REQUIRED_FIELDS:
            if field not in testcase:
                errors.append(f"{tc_id}: required field '{field}' is missing")

        if not self._is_non_empty_string(testcase.get("id")):
            errors.append(f"testcases[{index}]: field 'id' must be a non empty string")

        if not self._is_non_empty_string(testcase.get("title")):
            errors.append(f"{tc_id}: field 'title' must be a non empty string")

        req_ids = testcase.get("requirement_ids")
        if not isinstance(req_ids, list) or not req_ids:
            errors.append(f"{tc_id}: field 'requirement_ids' must be a non empty list")
        else:
            for i, req_id in enumerate(req_ids):
                if not self._is_non_empty_string(req_id):
                    errors.append(f"{tc_id}: requirement_ids[{i}] must be a non empty string")

        steps = testcase.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{tc_id}: field 'steps' must be a non empty list")
        else:
            for i, step in enumerate(steps, start=1):
                errors.extend(self._validate_step(step, i, str(tc_id)))

        tc_type = testcase.get("type")
        if not self._is_non_empty_string(tc_type):
            errors.append(f"{tc_id}: field 'type' must be a non empty string")

        return errors

    @staticmethod
    def _extract_testcases(new_data: Any, tc_file: str):
        if isinstance(new_data, list):
            return new_data
        if isinstance(new_data, dict) and "testcases" in new_data:
            return new_data["testcases"]
        logger.error(
            f"Malformed file structure: {tc_file}. "
            "Expected a list, or a dict with a 'testcases' key."
        )
        return None

    def append_from_file(self, tc_file):
        """Append test cases from a YAML file to the buffer."""
        tc_path = Path(tc_file)

        if not tc_path.exists():
            logger.error(f"File not found: {tc_file}")
            return False

        try:
            with open(tc_path, 'r', encoding='utf-8') as f:
                new_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {tc_file}: {e}")
            return False

        new_testcases = self._extract_testcases(new_data, tc_file)
        if new_testcases is None:
            return False

        if not isinstance(new_testcases, list):
            logger.error(f"Field 'testcases' in {tc_file} must be a list.")
            return False

        if not new_testcases:
            logger.warning(f"File contains no test cases: {tc_file}")
            return True

        validation_errors = []
        for i, testcase in enumerate(new_testcases):
            validation_errors.extend(self._validate_testcase(testcase, i))

        if validation_errors:
            logger.error(f"Validation of test cases from {tc_file} failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return False

        if self.buffer_path.exists():
            with open(self.buffer_path, 'r', encoding='utf-8') as f:
                buffer_data = yaml.safe_load(f)
        else:
            logger.error("Buffer file not found. Run with --init first")
            return False

        if not isinstance(buffer_data, dict):
            logger.error(f"Buffer file {self.BUFFER_FILE} is corrupt: expected a YAML object")
            return False
        if not isinstance(buffer_data.get("testcases"), list):
            logger.error(f"Buffer file {self.BUFFER_FILE} is corrupt: field 'testcases' must be a list")
            return False

        existing_ids = {
            tc.get("id").strip()
            for tc in buffer_data["testcases"]
            if isinstance(tc, dict) and self._is_non_empty_string(tc.get("id"))
        }
        seen_new = set()
        unique_new = []
        skipped_duplicates = []
        for tc in new_testcases:
            tc_id = tc["id"].strip()
            if tc_id in existing_ids or tc_id in seen_new:
                skipped_duplicates.append(tc_id)
                continue
            seen_new.add(tc_id)
            unique_new.append(tc)

        if skipped_duplicates:
            dup_list = ", ".join(sorted(set(skipped_duplicates)))
            logger.warning(f"Skipped duplicate ids: {dup_list}")

        if not unique_new:
            logger.warning("No test cases added: every entry was a duplicate")
            return True

        buffer_data['testcases'].extend(unique_new)

        with open(self.buffer_path, 'w', encoding='utf-8') as f:
            yaml.dump(buffer_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        total = len(buffer_data['testcases'])
        added = len(unique_new)
        logger.info(f"Buffer updated: {added} added (total: {total})")

        if self.sync_checkpoint:
            self._sync_with_checkpoint(total)

        return True

    def _sync_with_checkpoint(self, count):
        """Push the current test case count into the checkpoint file."""
        try:
            cmd = [sys.executable, str(self.workspace / "utils" / "checkpoint_manager.py"), "--set-count", str(count)]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Checkpoint synced: {count} test case(s)")
        except Exception as e:
            logger.warning(f"Could not sync the checkpoint: {e}")

    def finalize(self):
        """Promote the buffer to the output file."""
        if not self.buffer_path.exists():
            logger.error(f"Buffer file not found: {self.BUFFER_FILE}")
            return False

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.output_path.exists():
            self.output_path.unlink()

        self.buffer_path.rename(self.output_path)

        logger.info(f"Output file created: {self.OUTPUT_FILE}")

        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        tc_count = len(data.get('testcases', []))
        logger.info(f"  Project: {data.get('project', 'N/A')}")
        logger.info(f"  Test cases in total: {tc_count}")

        if self.sync_checkpoint:
            self._sync_with_checkpoint(tc_count)

        return True

    def status(self):
        """Report the current state of the buffer and the output file."""
        if self.buffer_path.exists():
            with open(self.buffer_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"Buffer file: {self.BUFFER_FILE}")
            logger.info(f"   Project: {data.get('project', 'N/A')}")
            logger.info(f"   Test cases: {len(data.get('testcases', []))}")
        else:
            logger.info("No buffer file yet")

        if self.output_path.exists():
            with open(self.output_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"Output file: {self.OUTPUT_FILE}")
            logger.info(f"   Project: {data.get('project', 'N/A')}")
            logger.info(f"   Test cases: {len(data.get('testcases', []))}")
        else:
            logger.info("No output file yet")

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Incremental writer for generated test cases'
    )

    parser.add_argument('--init', action='store_true', help='Create the buffer file')
    parser.add_argument('--project', type=str, help='Project name (used with --init)')
    parser.add_argument('--append', nargs='+', metavar='FILE', help='Append test cases from one or more files')
    parser.add_argument('--finalize', action='store_true', help='Promote the buffer to output/testcases_output.yaml')
    parser.add_argument('--status', action='store_true', help='Show the current state')
    parser.add_argument('--sync', action='store_true', help='Sync the count with checkpoint_manager')
    parser.add_argument('--workspace', type=str, help='Path to the project root')

    args = parser.parse_args()

    if not any([args.init, args.append, args.finalize, args.status]):
        parser.print_help()
        sys.exit(1)

    if args.init and not args.project:
        print("--init requires --project", file=sys.stderr)
        sys.exit(1)

    writer = TestcaseWriter(workspace_root=args.workspace, sync_checkpoint=args.sync)

    success = True

    if args.init:
        success = writer.init(args.project) and success

    if args.append:
        for tc_file in args.append:
            success = writer.append_from_file(tc_file) and success

    if args.finalize:
        success = writer.finalize() and success

    if args.status:
        success = writer.status() and success

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
