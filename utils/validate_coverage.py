#!/usr/bin/env python3
"""
Validates that test cases cover the requirements.
Checks that >= 95% of requirements carry at least one test case.
Builds a traceability matrix and an HTML report.
"""
import json
import sys
import yaml
from pathlib import Path
from collections import defaultdict

from utils.logger_config import get_logger
from utils.parse_requirements import load_config_and_requirements

logger = get_logger(__name__)

REQUIREMENTS_FILE = "requirements_input/requirements.yaml"
TESTCASES_FILE = "output/testcases_output.yaml"
COVERAGE_THRESHOLD = 95.0

ISTQB_TECHNIQUES = ["bva", "equivalence", "decision_table", "state_transition", "error_guessing"]


def load_testcases(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_requirements_from_config(config_path: str) -> dict:
    """Load requirements through the config, which points at the Markdown file."""
    ctx = load_config_and_requirements(config_path)
    return {r['id']: r for r in ctx['requirements']}


def validate_coverage(req_path: str = REQUIREMENTS_FILE, tc_path: str = TESTCASES_FILE) -> dict:
    requirements = load_requirements_from_config(req_path)
    tc_data = load_testcases(tc_path)
    testcases = tc_data.get('testcases', [])

    # Traceability matrix: requirement_id -> list of TC info
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
                orphan_testcases.append(f"{tc_id} -> {req_id} (does not exist)")
            else:
                coverage_matrix[req_id].append({
                    'tc_id': tc_id,
                    'type': tc_type,
                    'tags': tc_tags
                })

    # Coverage
    covered = set(coverage_matrix.keys())
    uncovered = all_req_ids - covered
    total = len(all_req_ids)
    covered_count = len(covered)
    coverage_pct = (covered_count / total * 100) if total > 0 else 0.0

    # Detailed matrix
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

    # ISTQB technique distribution, read off the tags
    technique_dist = defaultdict(int)
    for tc in testcases:
        tags = tc.get('tags', '')
        for tech in ISTQB_TECHNIQUES:
            if tech in tags:
                technique_dist[tech] += 1

    # Recommendations
    recommendations = []
    if coverage_pct < COVERAGE_THRESHOLD:
        recommendations.append(
            f"CRITICAL: coverage {coverage_pct:.1f}% is below the {COVERAGE_THRESHOLD}% threshold. "
            f"Uncovered requirements: {', '.join(sorted(uncovered))}"
        )

    reqs_without_negative = [
        req_id for req_id, info in matrix.items()
        if info['testcase_count'] > 0 and not info['has_negative']
    ]
    if reqs_without_negative:
        recommendations.append(
            f"No negative test cases for: {', '.join(reqs_without_negative)}"
        )

    missing_techniques = [t for t in ISTQB_TECHNIQUES if technique_dist.get(t, 0) == 0]
    if missing_techniques:
        recommendations.append(
            f"ISTQB techniques never applied: {', '.join(missing_techniques)}"
        )

    if orphan_testcases:
        recommendations.append(
            f"Test cases with no valid requirement reference: {', '.join(orphan_testcases)}"
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
    """Print the coverage report to the console."""
    status = "PASS" if result['pass'] else "FAIL"
    print(f"\n{'='*60}")
    print(f"  REQUIREMENTS COVERAGE REPORT: {status}")
    print(f"{'='*60}")
    print(f"  Coverage: {result['coverage_percent']}% (threshold: {COVERAGE_THRESHOLD}%)")
    print(f"  Requirements: {result['covered_requirements']}/{result['total_requirements']}")
    print(f"  Test cases: {result['total_testcases']}")
    print(f"{'='*60}")

    print("\n  TRACEABILITY MATRIX:")
    print(f"  {'REQ ID':<12} {'Title':<40} {'TC':<5} {'+':<3} {'-':<3} {'BVA':<3}")
    print(f"  {'-'*12} {'-'*40} {'-'*5} {'-'*3} {'-'*3} {'-'*3}")

    for req_id in sorted(result['matrix'].keys()):
        info = result['matrix'][req_id]
        title = info['title'][:38] + '..' if len(info['title']) > 40 else info['title']
        pos = 'V' if info['has_positive'] else '-'
        neg = 'V' if info['has_negative'] else '-'
        bva = 'V' if info['has_boundary'] else '-'
        print(f"  {req_id:<12} {title:<40} {info['testcase_count']:<5} {pos:<3} {neg:<3} {bva:<3}")

    if result['uncovered_requirements']:
        print(f"\n  UNCOVERED REQUIREMENTS: {', '.join(result['uncovered_requirements'])}")

    if result['technique_distribution']:
        print(f"\n  ISTQB TECHNIQUES:")
        for tech, count in sorted(result['technique_distribution'].items()):
            print(f"    {tech}: {count} test case(s)")

    if result['recommendations']:
        print(f"\n  RECOMMENDATIONS:")
        for rec in result['recommendations']:
            print(f"    - {rec}")

    print()


def generate_html_report(result: dict):
    """Render the HTML coverage report through report_generator."""
    from utils.report_generator import CoverageReportGenerator

    generator = CoverageReportGenerator()
    output_path = Path("reports/coverage_report.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generator.generate(result, output_path)
    logger.info(f"HTML report: {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate requirements coverage")
    parser.add_argument("--requirements", type=str, default=REQUIREMENTS_FILE)
    parser.add_argument("--testcases", type=str, default=TESTCASES_FILE)
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    parser.add_argument("--html", action="store_true", help="Generate the HTML report")

    args = parser.parse_args()

    result = validate_coverage(args.requirements, args.testcases)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_report(result)

    if args.html:
        generate_html_report(result)

    sys.exit(0 if result['pass'] else 1)
