#!/usr/bin/env python3
import argparse
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


class TestcaseWriter:
    """Инкрементальная запись тест-кейсов порциями"""

    BUFFER_FILE = "testcases_buffer.yaml"
    OUTPUT_FILE = "output/testcases_output.yaml"

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

    def append_from_file(self, tc_file):
        """Добавление тест-кейсов из YAML файла в буфер"""
        tc_path = Path(tc_file)

        if not tc_path.exists():
            logger.error(f"Файл не найден: {tc_file}")
            return False

        with open(tc_path, 'r', encoding='utf-8') as f:
            new_data = yaml.safe_load(f)

        if isinstance(new_data, list):
            new_testcases = new_data
        elif isinstance(new_data, dict) and 'testcases' in new_data:
            new_testcases = new_data['testcases']
        else:
            logger.error(f"Некорректная структура файла: {tc_file}. Ожидается список или dict с ключом 'testcases'.")
            return False

        if not isinstance(new_testcases, list):
            logger.error(f"Поле 'testcases' в {tc_file} должно быть списком.")
            return False

        if not new_testcases:
            logger.warning(f"Файл не содержит тест-кейсов: {tc_file}")
            return True

        if self.buffer_path.exists():
            with open(self.buffer_path, 'r', encoding='utf-8') as f:
                buffer_data = yaml.safe_load(f)
        else:
            logger.error("Буферный файл не найден. Запустите с --init")
            return False

        buffer_data['testcases'].extend(new_testcases)

        with open(self.buffer_path, 'w', encoding='utf-8') as f:
            yaml.dump(buffer_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        total = len(buffer_data['testcases'])
        added = len(new_testcases)
        logger.info(f"Буфер обновлён: добавлено {added} (всего: {total})")

        if self.sync_checkpoint:
            self._sync_with_checkpoint(total)

        return True

    def _sync_with_checkpoint(self, count):
        """Синхронизация с checkpoint_manager"""
        import subprocess
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
