from pathlib import Path

import yaml

from utils.render_prompt import parse_req_ids, render_prompt


def test_parse_req_ids_accepts_spaces_and_commas():
    req_ids = parse_req_ids(["REQ_001,REQ_002", " req_003 ", "REQ_002"])
    assert req_ids == ["REQ_001", "REQ_002", "REQ_003"]


def test_render_prompt_filters_requirements_by_ids(tmp_path: Path):
    md = tmp_path / "requirements.md"
    md.write_text(
        "## REQ_001 [Front] Calendar view\n"
        "- Opens correctly\n\n"
        "## REQ_002 [Back] Event create\n"
        "- Saves event\n",
        encoding="utf-8",
    )
    config = tmp_path / "requirements.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "project": "Demo",
                "module": "Calendar",
                "test_level": "system",
                "language": "ru",
                "tags_prefix": "module:calendar",
                "requirements_file": str(md),
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    template = tmp_path / "template.jinja2"
    template.write_text(
        "IDs: {{ selected_requirement_ids | join(', ') }}\n"
        "{% for req in requirements %}{{ req.id }}: {{ req.title }}\n{% endfor %}",
        encoding="utf-8",
    )

    rendered = render_prompt(
        config_path=str(config),
        template_path=str(template),
        req_ids=["REQ_002"],
        offset=0,
        limit=None,
    )

    assert "IDs: REQ_002" in rendered
    assert "REQ_002: Event create" in rendered
    assert "REQ_001: Calendar view" not in rendered
