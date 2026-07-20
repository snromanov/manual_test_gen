from pathlib import Path

from utils.report_generator import CoverageReportGenerator


def _result_with(title: str, tc_id: str, recommendation: str) -> dict:
    return {
        "coverage_percent": 100.0,
        "pass": True,
        "total_requirements": 1,
        "covered_requirements": 1,
        "uncovered_requirements": [],
        "total_testcases": 1,
        "orphan_testcases": [],
        "matrix": {
            "REQ_001": {
                "title": title,
                "priority": "high",
                "testcases": [tc_id],
                "testcase_count": 1,
                "has_positive": True,
                "has_negative": False,
                "has_boundary": False,
            }
        },
        "technique_distribution": {"equivalence": 1},
        "recommendations": [recommendation],
    }


def test_report_escapes_markup_from_requirements_and_model_output(tmp_path: Path):
    result = _result_with(
        title="<script>alert('xss')</script>",
        tc_id="<img src=x onerror=alert(1)>",
        recommendation="No negative test cases for: <b>REQ_001</b>",
    )

    output = tmp_path / "coverage_report.html"
    CoverageReportGenerator().generate(result, output)
    html = output.read_text(encoding="utf-8")

    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "<img src=x onerror" not in html
    assert "&lt;img src=x onerror" in html
    assert "<b>REQ_001</b>" not in html
    assert "&lt;b&gt;REQ_001&lt;/b&gt;" in html


def test_report_keeps_plain_text_readable(tmp_path: Path):
    result = _result_with(
        title="Event calendar display",
        tc_id="TC_001",
        recommendation="No negative test cases for: REQ_001",
    )

    output = tmp_path / "coverage_report.html"
    CoverageReportGenerator().generate(result, output)
    html = output.read_text(encoding="utf-8")

    assert "Event calendar display" in html
    assert "TC_001" in html
    assert "No negative test cases for: REQ_001" in html
