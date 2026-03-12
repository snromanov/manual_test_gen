from pathlib import Path

import yaml

from utils.write_testcases_incremental import TestcaseWriter


def _write_yaml(path: Path, data):
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _make_testcase(tc_id: str, req_id: str):
    return {
        "id": tc_id,
        "title": f"Test {tc_id}",
        "description": "desc",
        "requirement_ids": [req_id],
        "priority": "high",
        "type": "positive",
        "preconditions": "none",
        "steps": [{"step": 1, "action": "Do", "expected": "Done"}],
        "tags": "module:demo,positive,equivalence",
        "notes": "",
    }


def test_append_rejects_invalid_testcase_structure(tmp_path: Path):
    writer = TestcaseWriter(workspace_root=tmp_path)
    assert writer.init("Demo")

    invalid_part = tmp_path / "part_invalid.yaml"
    _write_yaml(
        invalid_part,
        {"testcases": [{"id": "TC_001", "title": "Broken testcase", "type": "positive"}]},
    )

    assert writer.append_from_file(str(invalid_part)) is False

    buffer_data = yaml.safe_load((tmp_path / "testcases_buffer.yaml").read_text(encoding="utf-8"))
    assert buffer_data["testcases"] == []


def test_append_deduplicates_by_id(tmp_path: Path):
    writer = TestcaseWriter(workspace_root=tmp_path)
    assert writer.init("Demo")

    part_1 = tmp_path / "part_1.yaml"
    _write_yaml(part_1, {"testcases": [_make_testcase("TC_001", "REQ_001"), _make_testcase("TC_002", "REQ_001")]})
    assert writer.append_from_file(str(part_1)) is True

    part_2 = tmp_path / "part_2.yaml"
    _write_yaml(part_2, {"testcases": [_make_testcase("TC_002", "REQ_002"), _make_testcase("TC_003", "REQ_002")]})
    assert writer.append_from_file(str(part_2)) is True

    buffer_data = yaml.safe_load((tmp_path / "testcases_buffer.yaml").read_text(encoding="utf-8"))
    ids = [tc["id"] for tc in buffer_data["testcases"]]
    assert ids == ["TC_001", "TC_002", "TC_003"]
