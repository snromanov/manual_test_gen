from pathlib import Path

import yaml

from utils.parse_requirements import load_config_and_requirements, parse_requirements_md


def test_parse_requirements_md_parses_headers_and_multiline(tmp_path: Path):
    md = tmp_path / "requirements.md"
    md.write_text(
        "## REQ_001 [Front] Login form\n"
        "- Field is visible\n"
        "- Password accepts masked input\n"
        "  with continuation line\n"
        "\n"
        "## REQ_002 [Back] Auth API\n"
        "- Returns 200 for valid credentials\n",
        encoding="utf-8",
    )

    result = parse_requirements_md(str(md))

    assert len(result) == 2
    assert result[0]["id"] == "REQ_001"
    assert result[0]["tag"] == "Front"
    assert result[0]["title"] == "Login form"
    assert result[0]["criteria"][1] == "Password accepts masked input with continuation line"
    assert result[1]["id"] == "REQ_002"


def test_load_config_and_requirements_reads_md_from_config(tmp_path: Path):
    md = tmp_path / "requirements.md"
    md.write_text(
        "## REQ_010 [Front] Dashboard\n"
        "- Loads widgets\n",
        encoding="utf-8",
    )
    config = tmp_path / "requirements.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "project": "Demo",
                "module": "UI",
                "requirements_file": str(md),
                "global_preconditions": ["User is authenticated"],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    ctx = load_config_and_requirements(str(config))

    assert ctx["project_name"] == "Demo"
    assert ctx["module_name"] == "UI"
    assert len(ctx["requirements"]) == 1
    assert ctx["requirements"][0]["id"] == "REQ_010"
