# Instructions for the LLM CLI agent

Work by these rules. No exceptions.

## GENERAL PRINCIPLES
- Honesty: do not invent anything. If you do not know something, say "I don't know".
- Transparency: state what your answer rests on (input, memory, guess).
- Limits: do not fake asynchronous work. Report "done" only when something is actually finished.
- Answers: clear, no padding, broken into stages for anything complex.

## STARTUP (REQUIRED)
On every start or restart:
```bash
PYTHONPATH=. python3 utils/check_env.py && python3 utils/checkpoint_manager.py --get
```
**Branching:**
- `current_step == "init"` then go to **Step 0**.
- `completed_steps` is non empty then **SKIP** those and go to the first unfinished step.
- `current_step == "generating_testcases"` then resume generation, taking `testcases_generated` into account.

---

## STEP 0: PREPARE
```bash
python3 utils/checkpoint_manager.py --update "prepare_context"
```

---

## STEP 1: GATHER CONTEXT
Read these, if you have not already:
1. `requirements_input/requirements.yaml` for project config (module, preconditions, tags)
2. `requirements_input/requirements.md` for the **requirements in Markdown**
3. `prompts/generate_testcases.jinja2` for the prompt template and output format

**REQUIREMENTS FORMAT (Markdown):**
Requirements are written in a .md file in a loose format:
```markdown
## REQ_001 [Front] Requirement title
- Criterion 1
- Criterion 2

## REQ_002 [Back] Another requirement
- Criterion 1
```
The ID comes from the heading (REQ_NNN). The bracketed tag [Front/Back] is optional.

To parse the requirements:
```bash
PYTHONPATH=. python3 utils/parse_requirements.py --json
```

From that output work out:
- How many requirements there are
- The module and the project
- The global preconditions

```bash
python3 utils/checkpoint_manager.py --set-req REQUIREMENT_COUNT "PROJECT_NAME"
```

---

## STEP 2: GENERATE TEST CASES (INCREMENTALLY)
CRITICAL: write test cases in batches of 3 to 5 to avoid timeouts.

### Procedure:
1. **Initialise** (once):
   ```bash
   PYTHONPATH=. python3 utils/write_testcases_incremental.py --init --project "PROJECT_NAME"
   python3 utils/checkpoint_manager.py --update "generating_testcases" --status "in_progress"
   ```

2. **Generation loop (3 to 5 test cases at a time):**
   - Take the prompt from generate_testcases.jinja2, substitute the requirements, generate YAML for one batch.
   - Write it to `part_N.yaml` (part_1.yaml, part_2.yaml, and so on).
   - Append it to the buffer:
     ```bash
     PYTHONPATH=. python3 utils/write_testcases_incremental.py --append part_N.yaml --sync
     ```
   - If you are close to the context limit, tell the user a restart is needed.

3. **Finalise:**
   ```bash
   PYTHONPATH=. python3 utils/write_testcases_incremental.py --finalize --sync
   python3 utils/checkpoint_manager.py --update "testcases_finalized"
   ```

### ISTQB generation rules:
- **Every requirement** must be covered by at least one positive and one negative test case
- Apply the techniques: equivalence partitioning, boundary value analysis, decision tables, state transitions, error guessing
- IDs: TC_001 (positive), TC_NEG_001 (negative), TC_BVA_001 (boundary)
- Steps are concrete actions for a manual tester
- Every step carries an expected result
- Every test case references its requirement_ids

---

## STEP 3: VALIDATE COVERAGE
```bash
PYTHONPATH=. python3 utils/validate_coverage.py
```
- Coverage below 95% means generating more test cases for the uncovered requirements.
- Orphan tests mean the requirement_ids references need fixing.
- Repeat validation until it reaches >= 95%.

```bash
python3 utils/checkpoint_manager.py --update "validated"
```

For the HTML report:
```bash
PYTHONPATH=. python3 utils/validate_coverage.py --html
```

---

## STEP 4: EXPORT TO ALLURE TESTOPS CSV
```bash
PYTHONPATH=. python3 utils/export_allure_csv.py
python3 utils/checkpoint_manager.py --update "exported"
```
Output: `output/testcases_allure.csv`

---

## QUALITY STANDARDS (CRITICAL)
- **Coverage**: >= 95% of requirements, every requirement gets at least one test case
- **ISTQB techniques**: at least 3 of the 5 must be applied
- **Completeness**: positive, negative, and boundary test cases
- **Steps**: concrete, executable by hand, each with an expected result
- **Traceability**: every test case references its requirement_ids
- **Tags**: module, technique, and type (positive/negative/boundary)

## TEST CASE YAML FORMAT (REQUIRED)
```yaml
- id: "TC_001"
  title: "Short summary"
  description: "Detailed description"
  requirement_ids: ["REQ_001"]
  priority: "high"
  type: "positive"
  preconditions: |
    1. Precondition 1
    2. Precondition 2
  steps:
    - step: 1
      action: "Action"
      expected: "Expected result"
  tags: "module:auth,positive,equivalence"
  notes: ""
```

## TECHNICAL RULES
- Use `python3` for every script in utils/.
- Every script in utils/ except `checkpoint_manager.py` needs `PYTHONPATH=.` when run from the repository root.
- CRITICAL: when invoking shell commands, always pass `is_background: false`.
- Do not use `run_shell_command` to pass large YAML payloads. Use `create_file` plus `append`.
- Always report progress (X/Y test cases).
