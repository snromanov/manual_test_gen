#!/usr/bin/env python3
import argparse
import sys
import subprocess
import yaml
from pathlib import Path
from typing import Any

from utils.logger_config import get_logger

logger = get_logger(__name__)


class TestcaseWriter:
    """Инкрементальная запись тест-кейсов порциями"""
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
        """Инициализация буферного файла"""
        data = {
            'project': project_name,
            'testcases': []
        }

        with open(self.buffer_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info(f"Создан буферный файл: {self.BUFFER_FILE}")
        logger.info(f"  Проект: {project_name}")
        return True

    @staticmethod
    def _is_non_empty_string(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    def _validate_step(self, step: Any, step_idx: int, tc_id: str) -> list[str]:
        errors = []
        prefix = f"{tc_id}: шаг #{step_idx}"
        if not isinstance(step, dict):
            return [f"{prefix} должен быть объектом"]

        step_num = step.get("step")
        action = step.get("action")
        expected = step.get("expected")

        if not isinstance(step_num, int) or step_num <= 0:
            errors.append(f"{prefix} содержит некорректное поле 'step' (ожидается целое число > 0)")
        if not self._is_non_empty_string(action):
            errors.append(f"{prefix} содержит пустое поле 'action'")
        if not self._is_non_empty_string(expected):
            errors.append(f"{prefix} содержит пустое поле 'expected'")

        return errors

    def _validate_testcase(self, testcase: Any, index: int) -> list[str]:
        if not isinstance(testcase, dict):
            return [f"Элемент testcases[{index}] должен быть объектом"]

        errors = []
        tc_id = testcase.get("id", f"testcases[{index}]")

        for field in self.REQUIRED_FIELDS:
            if field not in testcase:
                errors.append(f"{tc_id}: отсутствует обязательное поле '{field}'")

        if not self._is_non_empty_string(testcase.get("id")):
            errors.append(f"testcases[{index}]: поле 'id' должно быть непустой строкой")

        if not self._is_non_empty_string(testcase.get("title")):
            errors.append(f"{tc_id}: поле 'title' должно быть непустой строкой")

        req_ids = testcase.get("requirement_ids")
        if not isinstance(req_ids, list) or not req_ids:
            errors.append(f"{tc_id}: поле 'requirement_ids' должно быть непустым списком")
        else:
            for i, req_id in enumerate(req_ids):
                if not self._is_non_empty_string(req_id):
                    errors.append(f"{tc_id}: requirement_ids[{i}] должен быть непустой строкой")

        steps = testcase.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{tc_id}: поле 'steps' должно быть непустым списком")
        else:
            for i, step in enumerate(steps, start=1):
                errors.extend(self._validate_step(step, i, str(tc_id)))

        tc_type = testcase.get("type")
        if not self._is_non_empty_string(tc_type):
            errors.append(f"{tc_id}: поле 'type' должно быть непустой строкой")

        return errors

    @staticmethod
    def _extract_testcases(new_data: Any, tc_file: str):
        if isinstance(new_data, list):
            return new_data
        if isinstance(new_data, dict) and "testcases" in new_data:
            return new_data["testcases"]
        logger.error(
            f"Некорректная структура файла: {tc_file}. "
            "Ожидается список или dict с ключом 'testcases'."
        )
        return None

    def append_from_file(self, tc_file):
        """Добавление тест-кейсов из YAML файла в буфер"""
        tc_path = Path(tc_file)

        if not tc_path.exists():
            logger.error(f"Файл не найден: {tc_file}")
            return False

        try:
            with open(tc_path, 'r', encoding='utf-8') as f:
                new_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Некорректный YAML в {tc_file}: {e}")
            return False

        new_testcases = self._extract_testcases(new_data, tc_file)
        if new_testcases is None:
            return False

        if not isinstance(new_testcases, list):
            logger.error(f"Поле 'testcases' в {tc_file} должно быть списком.")
            return False

        if not new_testcases:
            logger.warning(f"Файл не содержит тест-кейсов: {tc_file}")
            return True

        validation_errors = []
        for i, testcase in enumerate(new_testcases):
            validation_errors.extend(self._validate_testcase(testcase, i))

        if validation_errors:
            logger.error(f"Валидация testcases из {tc_file} завершилась ошибками:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return False

        if self.buffer_path.exists():
            with open(self.buffer_path, 'r', encoding='utf-8') as f:
                buffer_data = yaml.safe_load(f)
        else:
            logger.error("Буферный файл не найден. Запустите с --init")
            return False

        if not isinstance(buffer_data, dict):
            logger.error(f"Буферный файл {self.BUFFER_FILE} повреждён: ожидался объект YAML")
            return False
        if not isinstance(buffer_data.get("testcases"), list):
            logger.error(f"Буферный файл {self.BUFFER_FILE} повреждён: поле 'testcases' должно быть списком")
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
            logger.warning(f"Пропущены дублирующиеся id: {dup_list}")

        if not unique_new:
            logger.warning("Новые тест-кейсы не добавлены: все записи оказались дубликатами")
            return True

        buffer_data['testcases'].extend(unique_new)

        with open(self.buffer_path, 'w', encoding='utf-8') as f:
            yaml.dump(buffer_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        total = len(buffer_data['testcases'])
        added = len(unique_new)
        logger.info(f"Буфер обновлён: добавлено {added} (всего: {total})")

        if self.sync_checkpoint:
            self._sync_with_checkpoint(total)

        return True

    def _sync_with_checkpoint(self, count):
        """Синхронизация с checkpoint_manager"""
        try:
            cmd = [sys.executable, str(self.workspace / "utils" / "checkpoint_manager.py"), "--set-count", str(count)]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Чекпоинт синхронизирован: {count} тест-кейсов")
        except Exception as e:
            logger.warning(f"Не удалось синхронизировать чекпоинт: {e}")

    def finalize(self):
        """Финализация: перенос буфера в итоговый файл"""
        if not self.buffer_path.exists():
            logger.error(f"Буферный файл не найден: {self.BUFFER_FILE}")
            return False

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.output_path.exists():
            self.output_path.unlink()

        self.buffer_path.rename(self.output_path)

        logger.info(f"Создан итоговый файл: {self.OUTPUT_FILE}")

        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        tc_count = len(data.get('testcases', []))
        logger.info(f"  Проект: {data.get('project', 'N/A')}")
        logger.info(f"  Всего тест-кейсов: {tc_count}")

        if self.sync_checkpoint:
            self._sync_with_checkpoint(tc_count)

        return True

    def status(self):
        """Показать текущий статус"""
        if self.buffer_path.exists():
            with open(self.buffer_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"Буферный файл: {self.BUFFER_FILE}")
            logger.info(f"   Проект: {data.get('project', 'N/A')}")
            logger.info(f"   Тест-кейсов: {len(data.get('testcases', []))}")
        else:
            logger.info("Буферный файл не создан")

        if self.output_path.exists():
            with open(self.output_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"Итоговый файл: {self.OUTPUT_FILE}")
            logger.info(f"   Проект: {data.get('project', 'N/A')}")
            logger.info(f"   Тест-кейсов: {len(data.get('testcases', []))}")
        else:
            logger.info("Итоговый файл не создан")

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Инкрементальная запись тест-кейсов'
    )

    parser.add_argument('--init', action='store_true', help='Инициализация буфера')
    parser.add_argument('--project', type=str, help='Имя проекта (для --init)')
    parser.add_argument('--append', nargs='+', metavar='FILE', help='Добавить тест-кейсы из файла(ов)')
    parser.add_argument('--finalize', action='store_true', help='Финализация в output/testcases_output.yaml')
    parser.add_argument('--status', action='store_true', help='Показать текущий статус')
    parser.add_argument('--sync', action='store_true', help='Синхронизировать с checkpoint_manager')
    parser.add_argument('--workspace', type=str, help='Путь к корню проекта')

    args = parser.parse_args()

    if not any([args.init, args.append, args.finalize, args.status]):
        parser.print_help()
        sys.exit(1)

    if args.init and not args.project:
        print("--init требует --project", file=sys.stderr)
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
