# 01-audit-session-mvp.md

## Executive Summary

- Overall Status: PASS
- Required Gate Failures: 0
- Flagged Risks: 2

## Gateboard

| Gate | Status | Why it failed (<=10 words) | Exact fix target |
| --- | --- | --- | --- |
| Requirement-to-test traceability | PASS | | |
| Proof artifact verifiability | PASS | | |
| Repository standards consistency | PASS (low confidence) | | |
| Open question resolution | PASS | | |
| Regression-risk blind spots | FLAG | Native window and shutdown are verified by hand only | `## Tasks > 1.0` |
| Non-goal leakage | FLAG | Startup recovery (5.8) isn't explicit in spec | `## Tasks > 5.0 > 5.8` |

### Gate notes

- **Traceability:** every functional requirement in spec Units 1–3 maps to a pytest file in the tasks.
  - Five purely visual requirements are covered by named screenshots or screen recordings rather than automated tests:
    - The window has no browser chrome.
    - The graph scrolls.
    - The virtual light changes color.
    - The buttons are large and the active one is highlighted.
    - The bands are drawn.
  - The logic behind each one does have an automated test (`test_server`, `test_stream`, `test_tagging`).
- **Open questions:** all five spec Open Questions have explicit default assumptions in the task Notes. They cover the seed list, CSV `t,value`, the ironbow palette, `HEATCOLOR_INVERT = True`, and 20 Hz with no fixed-rate assumption.
- **Standards:** the repo has no guideline files yet. `.gitignore` is the only source, and the spec's Repository Standards section is the fallback. Task 1.9 creates `README.md` as the first standards document.

## Standards Evidence Table (Required)

| Source File | Read | Standards Extracted | Conflicts |
| --- | --- | --- | --- |
| `AGENTS.md` (root and parents) | not found | | |
| `README.md` | not found (created in task 1.9) | | |
| `CONTRIBUTING.md` | not found | | |
| `CLAUDE.md` | not found | | |
| `.github/` (PR template, CI) | not found | | |
| `.pre-commit-config.yaml` / `pyproject.toml` | not found (`pyproject.toml` created in task 1.1) | | |
| `.gitignore` | yes | `/recordings` and `db.sqlite3` ignored; uv/Python template | none |

## Findings

### FLAG Findings

1. **The native window and shutdown are checked by hand only, and pywebview hasn't opened a window on Python 3.15 yet.**
   - Risk: if pywebview misbehaves on 3.15, everything built on the shell is affected.
   - Suggested remediation: run the manual step 1.10 as a smoke test right after 1.5, before 1.6–1.9. `test_server.py` already covers server start/stop without a window.
2. **Startup recovery (5.8) goes beyond the spec's explicit requirements.**
   - Risk: a small amount of scope the spec didn't ask for.
   - Justification: it supports the spec's crash-safety user story. Without it, a crash leaves a session stuck "in progress" in the database.
   - Suggested remediation: keep it, or drop 5.8 and `tests/test_startup_recovery.py` if you'd rather keep this milestone minimal.

## User-Approved Remediation Plan

- Completed:
  - Flag 1: the window smoke test runs right after 1.5.
  - Flag 2: startup recovery is dropped (5.8 and its test removed).
  - Proof files move to `01-proofs/`, matching the SDD-3 convention.
