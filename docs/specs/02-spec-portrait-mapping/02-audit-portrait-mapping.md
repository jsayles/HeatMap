# 02-audit-portrait-mapping.md

## Executive Summary

- Overall Status: PASS
- Required Gate Failures: 0
- Flagged Risks: 2

## Gateboard

| Gate | Status | Why it failed (<=10 words) | Exact fix target |
| --- | --- | --- | --- |
| Requirement-to-test traceability | PASS | | |
| Proof artifact verifiability | PASS | | |
| Repository standards consistency | PASS | | |
| Open question resolution | PASS | | |
| Regression-risk blind spots | FLAG | Real-model tests skip silently when fixtures are missing | `## Tasks > 3.0, 5.0` |
| Non-goal leakage | PASS | | |

### Gate notes

- **Traceability:** every functional requirement in spec Units 1–3 maps to a named pytest file in tasks 1.0–6.0. Visual-only requirements (the screens) also have screenshots. The one non-code requirement, the artist's choice of method, is covered by the decision record `docs/decisions/0001-background-removal.md`.
- **Standards:** `README.md` (out of date: participants, SQLite) conflicts with spec 02. The precedence decision is that spec 02 wins and task 1.7 updates the README.
- **Open questions:** all four spec Open Questions have explicit assumptions in the task Notes: grid settings, store all key points, backups as a README note, and fixtures.

## Standards Evidence Table (Required)

| Source File | Read | Standards Extracted | Conflicts |
| --- | --- | --- | --- |
| `README.md` | yes | `uv run heatmap` / `pytest` / `ruff`; private data never committed; specs in `docs/specs/` | Participant/SQLite wording; resolved by task 1.7 |
| `pyproject.toml` | yes | Python 3.15; pytest-django `heatmap.settings`; ruff line length 100, single quotes, import sorting | none |
| `.gitignore` | yes | `/recordings`, `db.sqlite3` ignored | none |
| Git history | yes | Conventional commits (`feat:`, `chore:`), on `main` | none |
| `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `.github/`, `.pre-commit-config.yaml` | not found | | |

## Findings

### FLAG Findings

1. **Real-model tests skip when fixtures are absent.**
   - Risk: before task 3.1, the tests that run the real Apple Vision / MediaPipe models skip, so a broken model path could pass unnoticed.
   - Suggested remediation: once the fixtures are committed in 3.1, make those tests fail rather than skip when the fixture folder is missing. Fixtures will then always be in the repo.
2. **Screenshot proofs depend on Jacob** (tasks 2.0, 3.0, 6.0), because the agent's terminal lacks Screen Recording permission.
   - Risk: proof files are incomplete until Jacob captures them, which can block parent-task completion.
   - Suggested remediation: accept this as is (it's noted in the task Notes), or grant the terminal Screen Recording permission so the agent can capture the app window itself.

## User-Approved Remediation Plan

- Pending approval (FLAG items only; no REQUIRED failures)

## Re-Audit Delta (Run 2, 2026-10-25)

- **Change:** at Jacob's request, everything is simplified into one `body_map` app (Subject, Portrait, Keypoint). Flat `segmentation.py` and `landmarks.py` modules replace the registries. Landmarks are implemented only for the framework that wins 3.0. Fakes in tests use `monkeypatch`. No SHA checks in `fetch_models`.
- **Changed gate statuses:** none. Every functional requirement still maps to the same test files, and all REQUIRED gates still PASS.
- **New findings:** none.
