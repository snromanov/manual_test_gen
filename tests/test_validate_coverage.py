from pathlib import Path

import yaml

from utils.validate_coverage import validate_coverage


def _write_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_validate_coverage_counts_coverage_and_orphans(tmp_path: Path):
    requirements_md = tmp_path / "requirements.md"
    requirements_md.write_text(
        "## REQ_001 [Front] Req one\n"
        "- criterion\n\n"
        "## REQ_002 [Back] Req two\n"
        "- criterion\n",
        encoding="utf-8",
    )
    requirements_cfg = tmp_path / "requirements.yaml"
    _write_yaml(
        requirements_cfg,
        {
            "project": "Demo",
            "module": "Calendar",
            "requirements_file": str(requirements_md),
        },
    )

    testcases = tmp_path / "testcases.yaml"
    _write_yaml(
        testcases,
        {
            "project": "Demo",
            "testcases": [
                {
                    "id": "TC_001",
                    "title": "Valid",
                    "requirement_ids": ["REQ_001"],
                    "type": "positive",
                    "tags": "equivalence",
                    "steps": [{"step": 1, "action": "a", "expected": "b"}],
                },
                {
                    "id": "TC_002",
                    "title": "Orphan",
                    "requirement_ids": ["REQ_999"],
                    "type": "negative",
                    "tags": "error_guessing",
                    "steps": [{"step": 1, "action": "a", "expected": "b"}],
                },
            ],
        },
    )

    result = validate_coverage(req_path=str(requirements_cfg), tc_path=str(testcases))

    assert result["total_requirements"] == 2
    assert result["covered_requirements"] == 1
    assert result["coverage_percent"] == 50.0
    assert "REQ_002" in result["uncovered_requirements"]
    assert any("REQ_999" in item for item in result["orphan_testcases"])
