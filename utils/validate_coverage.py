#!/usr/bin/env python3
"""
Валидация покрытия требований тест-кейсами.
Проверяет что >= 95% требований покрыты минимум одним тест-кейсом.
Генерирует матрицу трассировки и HTML-отчёт.
"""
import json
import sys
import yaml
from pathlib import Path
from collections import defaultdict

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

REQUIREMENTS_FILE = "requirements_input/requirements.yaml"
TESTCASES_FILE = "output/testcases_output.yaml"
COVERAGE_THRESHOLD = 95.0

ISTQB_TECHNIQUES = ["bva", "equivalence", "decision_table", "state_transition", "error_guessing"]


def load_testcases(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_requirements_from_config(config_path: str) -> dict:
    """Загружает требования: из markdown-файла (если указан) или из YAML напрямую."""
    try:
        from utils.parse_requirements import load_config_and_requirements
    except ImportError:
        try:
            from parse_requirements import load_config_and_requirements
        except ImportError:
            load_config_and_requirements = None

    if load_config_and_requirements:
        ctx = load_config_and_requirements(config_path)
        return {r['id']: r for r in ctx['requirements']}

    # Фолбек: прямой YAML с полем requirements
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return {r['id']: r for r in data.get('requirements', [])}


def validate_coverage(req_path: str = REQUIREMENTS_FILE, tc_path: str = TESTCASES_FILE) -> dict:
    requirements = load_requirements_from_config(req_path)
    tc_data = load_testcases(tc_path)
    testcases = tc_data.get('testcases', [])

    # Матрица трассировки: requirement_id -> list of TC info
    coverage_matrix = defaultdict(list)
    orphan_testcases = []
    all_req_ids = set(requirements.keys())

    for tc in testcases:
        tc_id = tc.get('id', 'UNKNOWN')
        tc_type = tc.get('type', 'unknown')
        tc_tags = tc.get('tags', '')
        req_ids = tc.get('requirement_ids', [])

        if not req_ids:
            orphan_testcases.append(tc_id)
            continue

        for req_id in req_ids:
            if req_id not in all_req_ids:
                orphan_testcases.append(f"{tc_id} -> {req_id} (не существует)")
            else:
                coverage_matrix[req_id].append({
                    'tc_id': tc_id,
                    'type': tc_type,
                    'tags': tc_tags
                })

    # Покрытие
    covered = set(coverage_matrix.keys())
    uncovered = all_req_ids - covered
    total = len(all_req_ids)
    covered_count = len(covered)
    coverage_pct = (covered_count / total * 100) if total > 0 else 0.0

    # Детальная матрица
    matrix = {}
    for req_id, req in requirements.items():
        tcs = coverage_matrix.get(req_id, [])
        tc_ids = [t['tc_id'] for t in tcs]
        tc_types = [t['type'] for t in tcs]

        matrix[req_id] = {
            'title': req.get('title', ''),
            'priority': req.get('priority', ''),
            'testcases': tc_ids,
            'testcase_count': len(tc_ids),
            'has_positive': any(t == 'positive' for t in tc_types),
            'has_negative': any(t == 'negative' for t in tc_types),
            'has_boundary': any(t == 'boundary' for t in tc_types),
        }

    # Распределение ISTQB-техник по тегам
    technique_dist = defaultdict(int)
    for tc in testcases:
        tags = tc.get('tags', '')
        for tech in ISTQB_TECHNIQUES:
            if tech in tags:
                technique_dist[tech] += 1

    # Рекомендации
    recommendations = []
    if coverage_pct < COVERAGE_THRESHOLD:
        recommendations.append(
            f"КРИТИЧНО: Покрытие {coverage_pct:.1f}% ниже порога {COVERAGE_THRESHOLD}%. "
            f"Непокрытые требования: {', '.join(sorted(uncovered))}"
        )

    reqs_without_negative = [
        req_id for req_id, info in matrix.items()
        if info['testcase_count'] > 0 and not info['has_negative']
    ]
    if reqs_without_negative:
        recommendations.append(
            f"Нет негативных тест-кейсов для: {', '.join(reqs_without_negative)}"
        )

    missing_techniques = [t for t in ISTQB_TECHNIQUES if technique_dist.get(t, 0) == 0]
    if missing_techniques:
        recommendations.append(
            f"Не применены ISTQB-техники: {', '.join(missing_techniques)}"
        )

    if orphan_testcases:
        recommendations.append(
            f"Тест-кейсы без валидных ссылок на требования: {', '.join(orphan_testcases)}"
        )

    result = {
        "coverage_percent": round(coverage_pct, 2),
        "pass": coverage_pct >= COVERAGE_THRESHOLD,
        "total_requirements": total,
        "covered_requirements": covered_count,
        "uncovered_requirements": sorted(list(uncovered)),
        "total_testcases": len(testcases),
        "orphan_testcases": orphan_testcases,
        "matrix": matrix,
        "technique_distribution": dict(technique_dist),
        "recommendations": recommendations
    }

    return result


def print_report(result: dict):
    """Вывод отчёта в консоль"""
    status = "PASS" if result['pass'] else "FAIL"
    print(f"\n{'='*60}")
    print(f"  ОТЧЁТ О ПОКРЫТИИ ТРЕБОВАНИЙ — {status}")
    print(f"{'='*60}")
    print(f"  Покрытие: {result['coverage_percent']}% (порог: {COVERAGE_THRESHOLD}%)")
    print(f"  Требований: {result['covered_requirements']}/{result['total_requirements']}")
    print(f"  Тест-кейсов: {result['total_testcases']}")
    print(f"{'='*60}")

    print("\n  МАТРИЦА ТРАССИРОВКИ:")
    print(f"  {'REQ ID':<12} {'Название':<40} {'TC':<5} {'+':<3} {'-':<3} {'BVA':<3}")
    print(f"  {'-'*12} {'-'*40} {'-'*5} {'-'*3} {'-'*3} {'-'*3}")

    for req_id in sorted(result['matrix'].keys()):
        info = result['matrix'][req_id]
        title = info['title'][:38] + '..' if len(info['title']) > 40 else info['title']
        pos = 'V' if info['has_positive'] else '-'
        neg = 'V' if info['has_negative'] else '-'
        bva = 'V' if info['has_boundary'] else '-'
        print(f"  {req_id:<12} {title:<40} {info['testcase_count']:<5} {pos:<3} {neg:<3} {bva:<3}")

    if result['uncovered_requirements']:
        print(f"\n  НЕПОКРЫТЫЕ ТРЕБОВАНИЯ: {', '.join(result['uncovered_requirements'])}")

    if result['technique_distribution']:
        print(f"\n  ISTQB-ТЕХНИКИ:")
        for tech, count in sorted(result['technique_distribution'].items()):
            print(f"    {tech}: {count} тест-кейсов")

    if result['recommendations']:
        print(f"\n  РЕКОМЕНДАЦИИ:")
        for rec in result['recommendations']:
            print(f"    - {rec}")

    print()


def generate_html_report(result: dict):
    """Генерация HTML-отчёта и вызов report_generator"""
    try:
        from utils.report_generator import CoverageReportGenerator
    except ImportError:
        try:
            from report_generator import CoverageReportGenerator
        except ImportError:
            logger.warning("report_generator.py не найден, HTML-отчёт не создан")
            return

    generator = CoverageReportGenerator()
    output_path = Path("reports/coverage_report.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generator.generate(result, output_path)
    logger.info(f"HTML-отчёт: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Валидация покрытия требований")
    parser.add_argument("--requirements", type=str, default=REQUIREMENTS_FILE)
    parser.add_argument("--testcases", type=str, default=TESTCASES_FILE)
    parser.add_argument("--json", action="store_true", help="Вывести результат в JSON")
    parser.add_argument("--html", action="store_true", help="Сгенерировать HTML-отчёт")

    args = parser.parse_args()

    result = validate_coverage(args.requirements, args.testcases)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)

    if args.html:
        generate_html_report(result)

    sys.exit(0 if result['pass'] else 1)
