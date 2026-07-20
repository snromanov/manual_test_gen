English | [Русский](README.ru.md) | [中文](README.zh.md)

# Manual Test Generator

A toolkit for producing manual test cases from written requirements using an LLM, checking that the result covers the requirements, and exporting it to a CSV that Allure TestOps can import.

The Python code in this repository does the deterministic work: parsing requirements, building the prompt, validating the generated YAML, measuring coverage, and writing the CSV. The test case text itself comes from an LLM. There is no API client here. You drive generation with whatever LLM CLI agent you already use, and `agent_rules.md` tells that agent which scripts to call and in what order.

## Key features

- Requirements are written as plain Markdown headings with bullet points. No schema to learn.
- The prompt template asks for five ISTQB Foundation Level design techniques and tags each case with the technique used.
- Coverage validation builds a requirement to test case traceability matrix and fails the build below 95 percent.
- Export produces the `[step N]` / `[expected N]` scenario syntax that Allure TestOps expects.
- A standalone HTML coverage report with a gauge, per technique distribution, and the full matrix.
- Incremental writing. Test cases arrive in small batches, get validated and deduplicated on the way into a buffer, and only become the output file when you finalize.
- A checkpoint file records progress so a long generation run can resume after the agent restarts.

## Quick start

```bash
# 1. Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Check the environment (also creates output/ and reports/)
PYTHONPATH=. python3 utils/check_env.py

# 3. Describe your requirements
#    edit requirements_input/requirements.md and requirements_input/requirements.yaml

# 4. Hand the workflow to your LLM CLI agent
<your-llm-cli> "read agent_rules.md and follow the instructions"
```

Every script under `utils/` except `checkpoint_manager.py` imports from the `utils` package, so it needs `PYTHONPATH=.` when run from the repository root. To run the steps yourself instead of delegating to an agent, see [Workflow](#workflow).

## Project structure

```
├── agent_rules.md                      # Step by step instructions for the LLM agent
├── requirements.txt                    # Pinned: PyYAML, Jinja2, pytest
├── requirements_input/
│   ├── requirements.yaml               # Project, module, tags, global preconditions
│   └── requirements.md                 # The requirements themselves
├── prompts/
│   └── generate_testcases.jinja2       # Prompt template with the ISTQB techniques
├── templates/
│   └── coverage_report.html.tpl        # HTML report template
├── utils/
│   ├── parse_requirements.py           # Markdown to structured requirements
│   ├── render_prompt.py                # Renders the Jinja2 prompt for a batch
│   ├── write_testcases_incremental.py  # Validated, deduplicated YAML buffer
│   ├── validate_coverage.py            # Coverage check and traceability matrix
│   ├── export_allure_csv.py            # YAML to Allure TestOps CSV
│   ├── report_generator.py             # Fills the HTML report template
│   ├── checkpoint_manager.py           # Agent progress state
│   ├── check_env.py                    # Environment check
│   └── logger_config.py                # Console and rotating file logging
├── tests/                              # pytest suite
├── output/                             # Created at runtime
│   ├── testcases_output.yaml
│   └── testcases_allure.csv
└── reports/
    └── coverage_report.html
```

`output/`, `reports/`, log files, `agent_state.json`, `testcases_buffer.yaml`, and `part_*.yaml` are all in `.gitignore`.

## Requirements format

`requirements_input/requirements.md` holds requirements in the shape people usually write them in a ticket:

```markdown
## REQ_001 [Front] Event calendar display
- The user opens the calendar section and sees a list or grid of events.
- Each event shows its main attributes: name, date, status.
- The interface behaves correctly when there are no events.

## REQ_002 [Back] Input validation and error handling
- The system rejects malformed data: dates, field lengths, special characters.
- Validation errors produce a message the user can act on.
```

Parsing rules, as implemented in `utils/parse_requirements.py`:

- `## REQ_NNN` starts a requirement. The ID is required and is uppercased.
- `[Front]`, `[Back]` and similar bracketed tags are optional. The tag is passed to the prompt and the model is asked to carry it into the test case tags.
- The rest of the heading line is the title.
- `- ` bullets under the heading become acceptance criteria. An indented line that follows a bullet is appended to that bullet, so criteria can wrap across lines.
- Anything before the first `## REQ_NNN` heading is ignored.

Project metadata lives in `requirements_input/requirements.yaml`:

```yaml
project: "Demo Project"
version: "1.0"
module: "Event calendar"
test_level: "system"
language: "en"
tags_prefix: "module:calendar"

requirements_file: "requirements_input/requirements.md"

global_preconditions:
  - "The application is deployed and reachable"
  - "The user is signed in with the administrator role"
  - "Communities with colour coding are configured in the admin panel"
```

`language` controls the language the prompt asks the model to write test cases in. Set it to `ru`, `zh`, or anything else and the model writes in that language. The tooling itself is unaffected. `tags_prefix` is prepended to every generated tag string.

## Test case format (YAML)

The LLM writes test cases into `part_N.yaml` files in this shape, and `write_testcases_incremental.py` validates every one before it enters the buffer:

```yaml
testcases:
  - id: "TC_001"
    title: "Events are displayed in the calendar"
    description: "Verifies that draft and scheduled events both appear"
    requirement_ids:
      - "REQ_001"
    priority: "high"
    type: "positive"              # positive | negative | boundary
    preconditions: |
      1. The user is signed in
      2. Events exist in several statuses
    steps:
      - step: 1
        action: "Open the Calendar section"
        expected: "The calendar renders with its events"
      - step: 2
        action: "Look for events in draft status"
        expected: "Draft events are visible"
    tags: "module:calendar,front,positive,equivalence"
    notes: ""
```

Required fields are `id`, `title`, `requirement_ids`, `steps`, and `type`. `requirement_ids` must be a non empty list of non empty strings. Each step needs an integer `step` greater than zero plus non empty `action` and `expected`. A file that fails validation is rejected whole, and nothing from it reaches the buffer. Test cases whose `id` already exists in the buffer are skipped with a warning.

ID convention used by the prompt: `TC_001` for positive cases, `TC_NEG_001` for negative, `TC_BVA_001` for boundary.

## Allure TestOps CSV

`export_allure_csv.py` writes `output/testcases_allure.csv` with all fields quoted:

| Column            | Source                                        |
| ----------------- | --------------------------------------------- |
| `allure_id`       | `id`                                          |
| `Name`            | `title`                                       |
| `Description`     | `description`                                 |
| `Precondition`    | `preconditions`, stripped                     |
| `Scenario`        | Steps as `[step N]` / `[expected N]` lines    |
| `Expected result` | `expected` of the last step                   |
| `Tags`            | `tags`, comma separated                       |

A `Scenario` cell looks like this, with real newlines inside the quoted field:

```
[step 1] Open the Calendar section
[expected 1] The calendar renders with its events
[step 2] Check the per community colour coding
[expected 2] Colours match the community settings
```

## Workflow

### Delegated to an LLM agent

```bash
<your-llm-cli> "read agent_rules.md and follow the instructions"
```

`agent_rules.md` walks the agent through environment check, context gathering, batched generation of three to five cases at a time, coverage validation with a retry loop until the threshold is met, and CSV export. Progress is written to `agent_state.json` after each stage, so an agent that runs out of context can be restarted and will pick up where it stopped.

### Run by hand

```bash
# 1. Parse the requirements and see what was recognised
PYTHONPATH=. python3 utils/parse_requirements.py
PYTHONPATH=. python3 utils/parse_requirements.py --json

# 2. Render the prompt for one batch of requirements
PYTHONPATH=. python3 utils/render_prompt.py --req-ids REQ_001 REQ_002 --output prompt_batch_1.txt
PYTHONPATH=. python3 utils/render_prompt.py --offset 0 --limit 3    # or slice the list

# 3. Send that prompt to your model, save the YAML it returns as part_1.yaml

# 4. Initialise the buffer
PYTHONPATH=. python3 utils/write_testcases_incremental.py --init --project "My Project"

# 5. Append each batch as it comes back
PYTHONPATH=. python3 utils/write_testcases_incremental.py --append part_1.yaml part_2.yaml --sync
PYTHONPATH=. python3 utils/write_testcases_incremental.py --status

# 6. Finalise, which moves the buffer to output/testcases_output.yaml
PYTHONPATH=. python3 utils/write_testcases_incremental.py --finalize --sync

# 7. Validate coverage
PYTHONPATH=. python3 utils/validate_coverage.py           # console report
PYTHONPATH=. python3 utils/validate_coverage.py --html    # plus reports/coverage_report.html
PYTHONPATH=. python3 utils/validate_coverage.py --json    # machine readable

# 8. Export
PYTHONPATH=. python3 utils/export_allure_csv.py
```

`--sync` on the incremental writer updates the test case count in `agent_state.json`. Leave it off if you are not using the checkpoint file.

`validate_coverage.py` exits with code 1 when coverage is under 95 percent, which makes it usable as a CI gate. Alongside the percentage it reports requirements with no negative test case, ISTQB techniques that were never applied, and orphan test cases, meaning ones with no `requirement_ids` or with an ID that does not match any requirement.

### HTML report

`--html` renders `reports/coverage_report.html`, a self contained dark theme page with a coverage gauge, counters, a bar chart of technique distribution, the traceability matrix with positive, negative, and boundary columns per requirement, and the list of recommendations.

![Coverage report](docs/report.png)

*Coverage report: gauge, ISTQB technique distribution, and the requirement to test case traceability matrix.*

## ISTQB techniques

The prompt template asks for five Foundation Level test design techniques. `validate_coverage.py` counts how many test cases carry each technique tag and warns about any technique that never appears.

| Technique                | What the prompt asks for                                          | Tag                |
| ------------------------ | ----------------------------------------------------------------- | ------------------ |
| Equivalence Partitioning | Valid and invalid classes per input parameter, one case per class  | `equivalence`      |
| Boundary Value Analysis  | min, max, min-1, max+1 wherever a criterion names a number         | `bva`              |
| Decision Table           | Significant combinations when a requirement has several conditions | `decision_table`   |
| State Transition         | One case per transition when a requirement describes statuses      | `state_transition` |
| Error Guessing           | Empty input, special characters, SQL injection, XSS, long strings  | `error_guessing`   |

The prompt also asks for at least one positive and one negative case per requirement, and for a `type` of `positive`, `negative`, or `boundary` on every case.

## Environment

- Python 3.10 or newer. The code uses `X | None` type syntax.
- `PyYAML` and `Jinja2` at runtime, `pytest` for the suite. Versions are pinned in `requirements.txt`.
- An LLM CLI agent of your choice for generation. Nothing in this repository talks to a model API.
- `PYTHONPATH=.` when running scripts from the repository root, except `utils/checkpoint_manager.py`, which has no package imports.

Logging goes to stdout and to a rotating file per module in the current directory, capped at 10 MB with three backups. Log files are ignored by git.

## Tests

```bash
pytest -q
```

Nine tests across five files cover Markdown parsing including multi line criteria, requirement filtering in the prompt renderer, the coverage and orphan calculation, the validation and deduplication rules of the incremental writer, and HTML escaping in the report generator.

## Security

- Keep secrets, tokens, and personal data out of requirements and test cases. Everything you put in `requirements.md` is sent to the model.
- Use synthetic or anonymised data in test steps.
- Review `output/` and `reports/` before sharing them. They contain whatever the model produced from your requirements.
- Generated files, logs, and agent state are excluded from git through `.gitignore`. Check `git status` before committing anyway.
- `yaml.safe_load` is used everywhere, so a YAML file from a model cannot construct arbitrary Python objects.
- The HTML report escapes requirement titles, test case IDs, and recommendation text before writing them into the page, so markup arriving from requirements or from model output renders as literal text.

## License

MIT. See [LICENSE](LICENSE).
