#!/usr/bin/env python3
"""Генератор HTML-отчёта покрытия требований тест-кейсами."""

from datetime import datetime
from pathlib import Path


class CoverageReportGenerator:
    """Генерирует HTML-отчёт с матрицей трассировки requirement -> testcases."""

    TEMPLATE_FILE = Path(__file__).resolve().parent.parent / "templates" / "coverage_report.html.tpl"

    TECHNIQUE_NAMES = {
        "equivalence": "Equivalence",
        "bva": "Boundary Value",
        "decision_table": "Decision Table",
        "state_transition": "State Transition",
        "error_guessing": "Error Guessing",
    }

    def __init__(self, template_path: Path | None = None):
        self.template_path = template_path or self.TEMPLATE_FILE

    def _load_template(self) -> str:
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        return self.template_path.read_text(encoding="utf-8")

    @staticmethod
    def _build_matrix_rows(matrix: dict) -> str:
        rows = ""
        for i, req_id in enumerate(sorted(matrix.keys())):
            info = matrix[req_id]
            row_class = "" if info.get("testcase_count", 0) > 0 else 'class="uncovered"'

            testcases = info.get("testcases", [])
            if testcases:
                tc_chips = "".join(f'<span class="tc-chip">{tc}</span>' for tc in testcases)
                tc_list = f'<div class="tc-list">{tc_chips}</div>'
            else:
                tc_list = (
                    '<span class="tc-chip" '
                    'style="background:rgba(255,56,96,0.1);color:var(--neon-red);'
                    'border-color:rgba(255,56,96,0.2)">NONE</span>'
                )

            def chk(ok: bool) -> str:
                if ok:
                    return '<span class="chk chk-ok">&#10003;</span>'
                return '<span class="chk chk-miss">&mdash;</span>'

            rows += f"""
                <tr {row_class} style="animation-delay:{0.05 * (i + 1):.2f}s">
                    <td><span class="req-id">{req_id}</span></td>
                    <td>{info.get('title', '')}</td>
                    <td>{tc_list}</td>
                    <td style="text-align:center">{chk(info.get('has_positive', False))}</td>
                    <td style="text-align:center">{chk(info.get('has_negative', False))}</td>
                    <td style="text-align:center">{chk(info.get('has_boundary', False))}</td>
                </tr>"""
        return rows

    def _build_technique_html(self, result: dict) -> str:
        tech_dist = result.get("technique_distribution", {})
        if not tech_dist:
            return ""

        max_count = max(tech_dist.values()) if tech_dist else 1
        bar_items = ""
        for i, (tech, count) in enumerate(sorted(tech_dist.items())):
            pct = int((count / max_count) * 100)
            name = self.TECHNIQUE_NAMES.get(tech, tech)
            bar_items += f"""
                <div class="tech-bar-row">
                    <div class="tech-bar-label">{name}</div>
                    <div class="tech-bar-track">
                        <div class="tech-bar-fill b-{i}" style="width:{pct}%">{count}</div>
                    </div>
                </div>"""

        return f"""
    <div class="card" style="animation-delay:0.25s">
        <h2><span class="icon">&#9672;</span> ISTQB Techniques</h2>
        <div class="tech-bars">{bar_items}</div>
    </div>"""

    @staticmethod
    def _build_recommendations_html(result: dict) -> str:
        recs = result.get("recommendations", [])
        if not recs:
            return ""

        rec_items = "".join(f"<li>{r}</li>" for r in recs)
        return f"""
    <div class="card rec-card" style="animation-delay:0.45s">
        <h2><span class="icon">&#9888;</span> Recommendations</h2>
        <ul>{rec_items}</ul>
    </div>"""

    def generate(self, result: dict, output_path: Path) -> str:
        template = self._load_template()
        matrix = result.get("matrix", {})

        coverage_pct = result.get("coverage_percent", 0)
        uncovered_count = result.get("total_requirements", 0) - result.get("covered_requirements", 0)
        gauge_offset = 502 - (502 * coverage_pct / 100)

        if coverage_pct >= 95:
            gauge_color = "c-pass"
            cov_class = "v-pass"
        elif coverage_pct >= 80:
            gauge_color = "c-warn"
            cov_class = "v-warn"
        else:
            gauge_color = "c-fail"
            cov_class = "v-fail"

        html = template.format(
            report_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            threshold=95,
            status_class="pass" if result.get("pass", False) else "fail",
            status_icon="&#10004;" if result.get("pass", False) else "&#10006;",
            status_text="ALL REQUIREMENTS COVERED" if result.get("pass", False) else "COVERAGE INSUFFICIENT",
            coverage_pct=coverage_pct,
            coverage_class=cov_class,
            gauge_offset=f"{gauge_offset:.1f}",
            gauge_color_class=gauge_color,
            total_req=result.get("total_requirements", 0),
            covered_req=result.get("covered_requirements", 0),
            uncovered_count=uncovered_count,
            total_tc=result.get("total_testcases", 0),
            technique_html=self._build_technique_html(result),
            matrix_rows=self._build_matrix_rows(matrix),
            recommendations_html=self._build_recommendations_html(result),
        )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding="utf-8")
        return str(output_file)
