#!/usr/bin/env python3
"""
Parser for requirements written in Markdown.

Format:
  ## REQ_001 [Front] Requirement title
  - criterion 1
  - criterion 2

  ## REQ_002 [Back] Another requirement
  - criterion 1

The ID is matched by the REQ_NNN pattern at the start of a level 2 heading.
A bracketed tag such as [Front] or [Back] is optional and is parsed as `tag`.
The rest of the heading is the title.
Bullet points (- ...) under the heading become acceptance_criteria.
"""
import re
import sys
import yaml
from pathlib import Path

from utils.logger_config import get_logger

logger = get_logger(__name__)

# Heading pattern: ## REQ_001 [Front] Title
HEADER_PATTERN = re.compile(
    r'^##\s+'
    r'(REQ_\d+)'              # ID (required)
    r'(?:\s+\[([^\]]+)\])?'   # [Tag] (optional)
    r'\s+(.*)',                # Title (rest of the line)
    re.IGNORECASE
)


def parse_requirements_md(md_path: str) -> list:
    """Parse a Markdown requirements file and return a list of dicts."""
    path = Path(md_path)
    if not path.exists():
        logger.error(f"File not found: {md_path}")
        return []

    text = path.read_text(encoding='utf-8')
    lines = text.split('\n')

    requirements = []
    current_req = None

    for line in lines:
        stripped = line.strip()

        # Check for a ## heading
        match = HEADER_PATTERN.match(stripped)
        if match:
            # Store the previous requirement
            if current_req:
                requirements.append(current_req)

            req_id = match.group(1).upper()
            tag = match.group(2) or ""
            title = match.group(3).strip()

            current_req = {
                'id': req_id,
                'tag': tag,
                'title': title,
                'criteria': [],
                'raw_text': ''
            }
            continue

        # Bullet point
        if current_req is not None:
            if stripped.startswith('- '):
                criterion = stripped[2:].strip()
                current_req['criteria'].append(criterion)
                current_req['raw_text'] += stripped + '\n'
            elif stripped and not stripped.startswith('#'):
                # Continuation of the previous bullet across lines
                if current_req['criteria']:
                    current_req['criteria'][-1] += ' ' + stripped
                current_req['raw_text'] += stripped + '\n'

    # The last requirement
    if current_req:
        requirements.append(current_req)

    logger.info(f"Parsed {len(requirements)} requirement(s) from {md_path}")
    return requirements


def load_config_and_requirements(config_path: str = "requirements_input/requirements.yaml") -> dict:
    """Load the YAML config and parse the Markdown requirements into one context dict."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    md_path = config.get('requirements_file', 'requirements_input/requirements.md')
    requirements = parse_requirements_md(md_path)

    return {
        'project_name': config.get('project', 'Unknown'),
        'version': config.get('version', '1.0'),
        'module_name': config.get('module', 'Unknown'),
        'test_level': config.get('test_level', 'system'),
        'language': config.get('language', 'en'),
        'tags_prefix': config.get('tags_prefix', ''),
        'global_preconditions': config.get('global_preconditions', []),
        'requirements': requirements,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Markdown requirements parser")
    parser.add_argument("--config", type=str, default="requirements_input/requirements.yaml")
    parser.add_argument("--md", type=str, help="Parse an MD file directly, without the config")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.md:
        reqs = parse_requirements_md(args.md)
        if args.json:
            import json
            print(json.dumps(reqs, indent=2, ensure_ascii=False))
        else:
            for r in reqs:
                print(f"\n{r['id']} [{r['tag']}] {r['title']}")
                for c in r['criteria']:
                    print(f"  - {c}")
    else:
        ctx = load_config_and_requirements(args.config)
        if args.json:
            import json
            print(json.dumps(ctx, indent=2, ensure_ascii=False))
        else:
            print(f"Project: {ctx['project_name']}")
            print(f"Module: {ctx['module_name']}")
            print(f"Requirements: {len(ctx['requirements'])}")
            for r in ctx['requirements']:
                print(f"  {r['id']} [{r['tag']}] {r['title']} ({len(r['criteria'])} criteria)")
