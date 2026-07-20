#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from utils.logger_config import get_logger

logger = get_logger(__name__)


def check_env():
    required_dirs = ["requirements_input", "prompts", "utils"]
    runtime_dirs = ["output", "reports"]
    required_files = [
        "requirements_input/requirements.yaml",
        "prompts/generate_testcases.jinja2",
        "templates/coverage_report.html.tpl",
        "utils/render_prompt.py",
        "utils/checkpoint_manager.py",
        "utils/validate_coverage.py",
        "utils/export_allure_csv.py",
        "utils/parse_requirements.py",
    ]

    missing = []

    for d in required_dirs:
        if not os.path.isdir(d):
            missing.append(f"Directory {d}/ not found")

    for d in runtime_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

    for f in required_files:
        if not os.path.isfile(f):
            missing.append(f"File {f} not found")

    # Check the Markdown requirements file referenced by the config
    config_path = Path("requirements_input/requirements.yaml")
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            md_file = config.get('requirements_file')
            if md_file and not os.path.isfile(md_file):
                missing.append(f"Requirements file {md_file} not found (referenced from requirements.yaml)")
        except Exception:
            pass

    if missing:
        logger.error("The environment is not ready:")
        for m in missing:
            logger.info(f"  - {m}")
        return False

    logger.info("Environment checked, every required component is in place.")
    return True


if __name__ == "__main__":
    if not check_env():
        sys.exit(1)
    sys.exit(0)
