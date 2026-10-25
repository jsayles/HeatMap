# 01-tasks-session-mvp.md

Spec: [01-spec-session-mvp.md](01-spec-session-mvp.md)

> **Status (2026-10-25): closed after task 1.0.** The project changed direction: the photo comes first, and the button-driven session gives way to a cursor-and-zoom interface over the portrait. Task 1.0 (the app shell) is built and carries forward. Tasks 2.0–5.0 are superseded and were not built; the parts that still apply will be planned again in later specs, starting with spec 02 (portrait mapping).

## Relevant Files

| File | Why It Is Relevant |
| --- | --- |
| `pyproject.toml` | uv project: Python 3.15, Django 6.1, pywebview, uvicorn; `heatmap` script entry point; pytest and ruff config. |
| `.python-version` | Pins Python 3.15 for uv. |
| `uv.lock` | Committed lockfile. |
| `README.md` | How to run, test, lint and create the facilitator login. |
| `.gitignore` | Already ignores `/recordings` and `db.sqlite3`. Add nothing unless something new needs ignoring. |
| `manage.py` | Standard Django entry point. |
| `heatmap/settings.py` | Standard Django settings, plus `RECORDINGS_DIR`, `LAUNCH_TOKEN`, `MIN_SEGMENT_SECONDS`, `HEATCOLOR_INVERT` and simulator rate. |
| `heatmap/urls.py` | Root URLs: launch, admin, `recording` app. |
| `heatmap/asgi.py` | ASGI application served by uvicorn. |
| `heatmap/app.py` | `main()`: picks a free port, generates the launch secret, runs migrations, starts uvicorn in a thread, opens the pywebview window, and shuts everything down on close. |
| `heatmap/server.py` | Small helpers for the free port and the uvicorn server on `127.0.0.1` (start/stop), kept separate so they can be tested without a window. |
| `heatmap/launch.py` | Launch-secret middleware and the `/launch/` view that sets the cookie. |
| `heatcolor/__init__.py` | Shared CircuitPython-compatible color library: reading + range → RGB, ironbow palette, invert option. |
| `catalog/models.py` | `BodyPart` (name, order). |
| `catalog/admin.py` | Body-part admin with editable order. |
| `catalog/migrations/0002_seed_body_parts.py` | Data migration with the draft head-to-toe list. |
| `recording/models.py` | `Participant`, `Session`, `PhaseChange`, `Segment`. |
| `recording/admin.py` | Participant and session admin. |
| `recording/storage.py` | Creates timestamped session folders under `recordings/`; paths for `meta.json`, `samples.csv` and exports. |
| `recording/devices.py` | `DeviceReader` interface and `SimulatedPhilometer`. |
| `recording/recorder.py` | Background recorder thread (stamp → append → flush), `RecorderManager`, and a `python -m recording.recorder` command-line entry for standalone runs. |
| `recording/phases.py` | Phase transition rules (Calibrating → Walkthrough → Ended). |
| `recording/tagging.py` | Click-to-toggle segment logic, short-segment discard, close on phase change or end. |
| `recording/summary.py` | Per-body-part summary from `samples.csv` + segments. |
| `recording/export.py` | Writes `phases.csv` and `segments.csv` into the session folder. |
| `recording/stream.py` | Async SSE view that follows `samples.csv` and emits value, range and color. |
| `recording/views.py` | Home, start session, session screen, phase POST, toggle POST, segments JSON, review, export. |
| `recording/urls.py` | `recording` app URLs. |
| `recording/templates/recording/base.html` | Shared layout for app screens. |
| `recording/templates/recording/home.html` | Participants, start-session form, list of past sessions. |
| `recording/templates/recording/session.html` | Live session screen. |
| `recording/templates/recording/review.html` | Finished-session review screen. |
| `recording/static/recording/session.js` | EventSource, live uPlot graph, range, virtual light, phase buttons, body-part toggles, bands. |
| `recording/static/recording/review.js` | Full-session graph with phase markers and bands. |
| `recording/static/recording/app.css` | Quiet app styling, large touch-friendly buttons. |
| `recording/static/recording/vendor/uplot/` | uPlot JS and CSS (pinned version), kept in the repo for offline use. |
| `tests/conftest.py` | Fixtures: temporary `RECORDINGS_DIR`, launch-token client, participant, session, fixture CSV. |
| `tests/test_access.py` | Launch-secret rejection and acceptance. |
| `tests/test_server.py` | Free port, binding only to `127.0.0.1`, and server stop. |
| `tests/test_models.py` | Models, ordering, seed list, `User` separation. |
| `tests/test_admin.py` | Admin pages for participants and body parts load and save. |
| `tests/test_session_folder.py` | Timestamped folders; files carry only `participant_<id>`. |
| `tests/test_heatcolor.py` | Color mapping and the import-allowlist check. |
| `tests/test_recorder.py` | Sample rates, no dropped samples, timestamps, independence from the stream. |
| `tests/test_crash_safety.py` | SIGKILL of the recorder subprocess; checks the file holds data to within 1 s of the kill. |
| `tests/test_phases.py` | Phase rules and timestamps. |
| `tests/test_stream.py` | SSE order, range, colors, partial lines, two consumers at once. |
| `tests/test_tagging.py` | Toggle rules. |
| `tests/test_summary_export.py` | Summary values and export files. |
| `tests/test_review.py` | Review view loads with phases, segments and summary. |
| `docs/specs/01-spec-session-mvp/01-proofs/` | Proof artifacts (simulated data only). |

### Notes

- **Proof paths:** `01-proofs/...` below means `docs/specs/01-spec-session-mvp/01-proofs/...`. Each parent task also gets one summary file there, `01-task-NN-proofs.md`, that embeds or links its artifacts. Proof artifacts come from **simulated sessions only**, and use made-up participant names like "Test Participant".
- **Commands:** run tests with `uv run pytest [path]`; lint and format with `uv run ruff check .` and `uv run ruff format .`.
- **Test data:** tests must never write to the real `recordings/` folder. Point `RECORDINGS_DIR` at `tmp_path` in `tests/conftest.py`.
- **Keep Django standard:** generate the project and apps with `django-admin startproject` and `startapp`, keep `SECRET_KEY` in `settings.py`, use the default `db.sqlite3`, and use Django admin for editing.
- **Python 3.15:** before adding any new dependency, check it installs on 3.15 (`uv add <pkg>`).
- **Shared timebase:** all session times are seconds since the session started (`t = time.time() - session.start_epoch`). The recorder and the POST views use the same function, `recording.storage.session_time(session)`.
- **Assumptions for the spec's Open Questions** (each can be changed later):
  1. Seed list = the draft list in the spec. It's editable in admin.
  2. The raw file is CSV with a header: `t,value`.
  3. The palette is ironbow by default.
  4. Color direction is `HEATCOLOR_INVERT = True` (a low reading shows as hot), as a setting.
  5. The simulator defaults to 20 Hz. Nothing assumes a fixed rate.
- **Naming:** the Django app is `recording`, not `sessions`, to avoid clashing with `django.contrib.sessions`. The data folder is `recordings/`.

## Tasks

### [x] 1.0 Project scaffold and native app shell

uv-managed Python 3.15 / Django 6.1 project that launches as a native pywebview window, runs its own ASGI server on `127.0.0.1` on a free port, rejects requests without the per-launch secret, and shuts everything down when the window closes. (Spec Unit 1: shell, server, access check.)

#### 1.0 Proof Artifact(s)

- Screenshot: `01-proofs/1.0-app-window.png` shows the app's home screen in its own window with no address bar or tabs. Demonstrates the native app shell.
- CLI: `uv run heatmap` opens the window. After it closes, `lsof -iTCP -sTCP:LISTEN -P | grep -i python` prints nothing, saved as `01-proofs/1.0-shutdown.txt`. Demonstrates clean start and shutdown.
- Test: `uv run pytest tests/test_access.py` passes: a request without the launch secret gets 403, and one with it gets 200. Demonstrates the local access check.
- Test: `uv run pytest tests/test_server.py` passes: the chosen port is free, the server binds only to `127.0.0.1`, and after `stop()` the port is no longer listening. Demonstrates binding and shutdown without a window.
- CLI: `uv run ruff check .` reports no errors. Demonstrates the lint setup.

#### 1.0 Tasks

- [x] 1.1 Run `uv init` for an application project named `heatmap` with `requires-python = ">=3.15"` and `.python-version` set to `3.15`. Add dependencies with `uv add "django>=6.1,<6.2" pywebview uvicorn` and dev dependencies with `uv add --dev pytest pytest-django ruff`. Commit `uv.lock`.
- [x] 1.2 Run `uv run django-admin startproject heatmap .`. In `heatmap/settings.py`, set `ALLOWED_HOSTS = ["127.0.0.1"]` and `RECORDINGS_DIR = BASE_DIR / "recordings"`, and add placeholder settings `LAUNCH_TOKEN` (from the env var `HEATMAP_LAUNCH_TOKEN`), `MIN_SEGMENT_SECONDS = 1.0`, `HEATCOLOR_INVERT = True` and `SIMULATOR_RATE_HZ = 20`.
- [x] 1.3 Write `heatmap/server.py` with:
  - `find_free_port()`, which binds a socket to `127.0.0.1:0` and returns the port.
  - A `LocalServer` class that wraps `uvicorn.Server`, with host fixed to `127.0.0.1` and app `heatmap.asgi:application`. `start()` runs it in a daemon thread and waits until it is started; `stop()` sets `should_exit` and joins the thread.
- [x] 1.4 Write `heatmap/launch.py` with:
  - Middleware that allows `/launch/` and static files, and rejects every other request with 403 unless the `heatmap_launch` cookie matches `settings.LAUNCH_TOKEN`.
  - A `/launch/?token=...` view that checks the token, sets the cookie (HttpOnly, SameSite=Strict) and redirects to the home page.

  Register the middleware and the URL.
- [x] 1.5 Write `heatmap/app.py` `main()`:
  1. Generate a token with `secrets.token_urlsafe()` and set the env var.
  2. Run `django.setup()` and then `call_command("migrate")`.
  3. Pick a port and start `LocalServer`.
  4. Open `webview.create_window("Personal Heat Map", f"http://127.0.0.1:{port}/launch/?token=...")` and call `webview.start()`.
  5. In a `finally` block, call the shutdown hooks (a simple list that task 3.5 adds the recorder to) and `server.stop()`.

  Add `[project.scripts] heatmap = "heatmap.app:main"`.
- [x] 1.6 Add a minimal home page so the window shows something. Create a placeholder template and view, to be replaced in 2.0/4.0.
- [x] 1.7 Configure pytest and ruff in `pyproject.toml`: `DJANGO_SETTINGS_MODULE = "heatmap.settings"`, `testpaths = ["tests"]`, and ruff target `py315` with default rules plus import sorting. Write `tests/conftest.py` with a client fixture that has the launch cookie.
- [x] 1.8 Write `tests/test_access.py` (403 without the cookie, 200 with it, 403 for a wrong token on `/launch/`) and `tests/test_server.py` (free port, host is `127.0.0.1`, and the port has stopped listening after `stop()`).
- [x] 1.9 Write `README.md` covering what the app is (one line), `uv run heatmap`, `uv run manage.py createsuperuser` (the facilitator login for admin), `uv run pytest` and `uv run ruff check .`, and a note that `recordings/` and `db.sqlite3` hold private data and are never committed.
- [x] 1.10 Run `uv run heatmap` by hand and capture `01-proofs/01-task-01-app-window.png`. Close the window, then record the `lsof` output in `01-proofs/01-task-01-proofs.md`.

### [-] 2.0 Participants, body parts and sessions (superseded)

Django models and in-window editing (standard Django admin) for Participant (separate from `User`), a flat ordered BodyPart list seeded with the draft head-to-toe list, and Session linked to a Participant. Starting a session creates a timestamped folder in `recordings/`, whose files identify the participant only as `participant_<id>`. (Spec Unit 1: data model, seeding, data layout.)

#### 2.0 Proof Artifact(s)

- Test: `uv run pytest tests/test_models.py` passes, covering:
  - Participant creation, with no foreign key or relation to `User`.
  - BodyPart ordering.
  - Session's link to Participant.
  - The seeded list matching the draft list, in head-to-toe order.

  Demonstrates the data model.
- Test: `uv run pytest tests/test_admin.py` passes: a logged-in facilitator can open, add and edit participants and body parts. Demonstrates in-app editing.
- Test: `uv run pytest tests/test_session_folder.py` passes:
  - Creating a session creates `recordings/<YYYY-MM-DD_HH-MM-SS>/` with a `meta.json`.
  - That file contains `participant_<id>` and not the participant's display name.
  - Two sessions in the same second get distinct folders.

  Demonstrates the data layout and the identity split.
- Screenshot: `01-proofs/2.0-body-parts.png` shows the seeded body-part list in order in the admin, inside the app window. Demonstrates seeding and editing.

#### 2.0 Tasks

- [ ] 2.1 Run `uv run manage.py startapp catalog`. Add `BodyPart(name: CharField unique, order: PositiveIntegerField)` with `Meta.ordering = ["order"]`. Register it in admin with `list_display = ("name", "order")` and `list_editable = ("order",)`.
- [ ] 2.2 Add the data migration `catalog/migrations/0002_seed_body_parts.py` that inserts the draft list in order: Head, Face, Neck, Shoulders, Arms, Hands, Chest, Breasts, Ribs, Belly, Back, Hips, Butt, Sex, Thighs, Knees, Lower legs, Feet. Order values go in steps of 10, so parts can be inserted later.
- [ ] 2.3 Run `uv run manage.py startapp recording`. Add `Participant(display_name, notes blank, created_at)` with a `file_id` property returning `f"participant_{self.pk}"`, and with no relation to `User`. Add `Session(participant FK, started_at, start_epoch: FloatField, ended_at null, phase: choices calibrating/walkthrough/ended, folder: CharField)`. Register both in admin.
- [ ] 2.4 Write `recording/storage.py` with:
  - `create_session_folder(session)`: creates `settings.RECORDINGS_DIR / started_at.strftime("%Y-%m-%d_%H-%M-%S")`, adding `-2`, `-3` and so on if the folder exists. It writes `meta.json` holding `{"participant": file_id, "started_at": iso, "session_id": pk}` and saves the folder name on the session.
  - `session_time(session)` and the path helpers `samples_path`, `phases_csv_path` and `segments_csv_path`.
- [ ] 2.5 Link "Participants" and "Body parts" (admin pages) from the home page, so they open inside the app window.
- [ ] 2.6 Write `tests/test_models.py`, `tests/test_admin.py` (using `admin_client`) and `tests/test_session_folder.py`, with `RECORDINGS_DIR` set to `tmp_path`.
- [ ] 2.7 Capture `01-proofs/2.0-body-parts.png` from the running app.

### [-] 3.0 Shared color library, simulator and recording worker (superseded)

A CircuitPython-compatible `heatcolor` package, a simulated Philometer behind a device-reader interface, and a background recorder that stamps samples on receipt and appends them to the session's raw file. The recorder runs independently of web requests. (Spec Unit 2: color library, simulator, worker, raw file.)

#### 3.0 Proof Artifact(s)

- Test: `uv run pytest tests/test_heatcolor.py` passes, covering:
  - Value at the low end, the high end and the midpoint.
  - Values clamped outside the range.
  - Inverted direction.
  - A zero-width range returning the midpoint color with no error.
  - `to_hex` output.
  - An AST check that `heatcolor` imports nothing outside the allowlist `{"math"}`.

  Demonstrates the color mapping and the CircuitPython constraint.
- Test: `uv run pytest tests/test_recorder.py` passes:
  - Two-second simulated runs at 10 Hz and 100 Hz write exactly as many rows as the simulator generated.
  - Timestamps increase strictly.
  - Recording proceeds with no stream consumer attached.
  - A seeded 60-second simulated signal (generated without sleeping) drifts (min ≠ max) and contains at least one reaction dip.

  Demonstrates the simulator's realistic signal, rate independence, no dropped samples and independence from the window.
- Test: `uv run pytest tests/test_crash_safety.py` passes: a `python -m recording.recorder` subprocess is killed with SIGKILL after ~3 s, and the file's last `t` is within 1 s of the elapsed time at the kill. Demonstrates crash safety.
- File: `01-proofs/3.0-sample-raw.csv` holds the first 50 rows of a simulated run. Demonstrates the raw file format.

#### 3.0 Tasks

- [ ] 3.1 Write `heatcolor/__init__.py` using only plain functions, tuples and `math` (no `dataclasses`, `typing` or `enum`), with:
  - `IRONBOW`: a list of RGB stops from black through purple, red and orange to yellow/white.
  - `normalize(value, lo, hi, invert=False)`, returning 0..1 clamped, and 0.5 when `hi == lo`.
  - `color_for(value, lo, hi, invert=False, palette=IRONBOW)`, returning `(r, g, b)` by linear interpolation between stops.
  - `to_hex(rgb)`.
- [ ] 3.2 Write `tests/test_heatcolor.py`, including the AST import-allowlist test that parses every `.py` file in `heatcolor/`.
- [ ] 3.3 Write `recording/devices.py`:
  - A `DeviceReader` base class with `open()`, `read() -> float` (blocks until the next sample) and `close()`.
  - A `SimulatedPhilometer(rate_hz, seed=None)` subclass. It produces a slow random-walk baseline with occasional reactions: a dip that recovers over a few seconds. It paces itself with `time.sleep` relative to a monotonic schedule (pacing can be turned off with `realtime=False` for fast tests) and counts samples in `generated`.
- [ ] 3.4 Write `recording/recorder.py`:
  - A `Recorder(device, path, start_epoch)` thread. It writes the header `t,value`, then loops `read()` → `t = time.time() - start_epoch` → `f.write(f"{t:.4f},{value}\n")` → `f.flush()` until its stop event is set, then closes the device and the file.
  - A `__main__` block with `--out`, `--rate` and `--seconds`, for standalone runs and the crash test.
- [ ] 3.5 Add `RecorderManager` (a module-level singleton) with `start(session)`, `stop(session)` and `stop_all()`. It builds a `SimulatedPhilometer(settings.SIMULATOR_RATE_HZ)` for now. Register `stop_all` as a shutdown hook in `heatmap/app.py`.
- [ ] 3.6 Write `tests/test_recorder.py` and `tests/test_crash_safety.py`. The crash test runs the subprocess with `sys.executable -m recording.recorder`, sends `os.kill(pid, signal.SIGKILL)`, then reads the CSV.
- [ ] 3.7 Run `uv run python -m recording.recorder --out <scratch folder outside the repo>/samples.csv --rate 20 --seconds 5` and copy the header plus the first 50 rows to `01-proofs/3.0-sample-raw.csv`.

### [-] 4.0 Live session screen: phases, graph, range and virtual light (superseded)

A session screen started for a participant. It shows the Calibrating → Walkthrough → End phases, with ending confirmed and each change recorded with its timestamp. Samples stream over SSE into a scrolling uPlot graph, with the running min/max and a virtual light colored by `heatcolor`. The stream is its own endpoint, so a second window could subscribe later. (Spec Unit 2: phases, SSE, live graph, range, virtual light.)

#### 4.0 Proof Artifact(s)

- Screen recording: `01-proofs/4.0-live-session.mov` shows a simulated session going Calibrating → Walkthrough → End (with the confirmation dialog), while the graph scrolls, the range updates and the virtual light changes color. Demonstrates the live view.
- Test: `uv run pytest tests/test_phases.py` passes:
  - A new session starts in Calibrating with a PhaseChange at `t≈0`.
  - Walkthrough and End are recorded in order with increasing `t`.
  - Invalid moves (back to Calibrating, anything after End) return 400.
  - End sets `ended_at` and stops the recorder.

  Demonstrates the phase rules.
- Test: `uv run pytest tests/test_stream.py` passes, using a fixture `samples.csv`:
  - The SSE response emits every row in order, with `min` and `max` matching the running range and `color` equal to `heatcolor.to_hex(color_for(...))`.
  - A half-written last line isn't emitted until it is complete.
  - Two consumers at once receive identical events.
  - The stream ends after the session ends and the file is drained.

  Demonstrates the stream, the range, the shared color source and separation from the control screen.

#### 4.0 Tasks

- [ ] 4.1 Add a `PhaseChange(session FK, phase, t)` model. Write `recording/phases.py` with `start_session(participant)`, which creates the Session (phase calibrating, `start_epoch = time.time()`), the folder, a PhaseChange at `t=0`, and starts the recorder. Also write `change_phase(session, new_phase)`, which allows only calibrating→walkthrough, calibrating→ended and walkthrough→ended, records `session_time`, and on ended sets `ended_at` and stops the recorder.
- [ ] 4.2 Write views and URLs:
  - The home page: the participant list, a "Start session" form (choose a participant), and lists of active and past sessions.
  - A `POST /sessions/start/` endpoint that redirects to the session screen.
  - `POST /sessions/<id>/phase/`, which returns JSON `{phase}` or 400.
  - `GET /sessions/<id>/`, the session screen.
- [ ] 4.3 Write `recording/stream.py`, an async view `GET /sessions/<id>/stream/` that returns a `StreamingHttpResponse` (`text/event-stream`) from an async generator. The generator:
  - Opens `samples.csv`, skips the header, and emits only complete lines (buffering a partial last line).
  - Tracks the running min/max and emits `data: {"t", "v", "min", "max", "color"}` events, with `color` from `heatcolor` using `settings.HEATCOLOR_INVERT`.
  - Polls the file every ~50 ms with `asyncio.sleep`.
  - Ends once the session is ended and no new lines remain. It reads the session state with `sync_to_async`.
- [ ] 4.4 Download a pinned uPlot release (1.6.32: `uPlot.iife.min.js` and `uPlot.min.css`) into `recording/static/recording/vendor/uplot/`, with its LICENSE. Load nothing from a CDN.
- [ ] 4.5 Build `session.html` and `session.js`. The page never reloads; all actions use `fetch` with the CSRF token. It has:
  - An `EventSource` on the stream.
  - A uPlot graph showing the last 120 s and redrawing at most once per animation frame.
  - The range shown as text.
  - A large round virtual light whose background is the latest `color`.
  - The current phase, with Walkthrough and End buttons; End needs `confirm()`.
- [ ] 4.6 Add `app.css`: quiet neutral chrome, a readable-at-a-glance layout (graph top, light and phase prominent, buttons below), and buttons at least 64 px tall.
- [ ] 4.7 Write `tests/test_phases.py` and `tests/test_stream.py`. The stream tests consume the async iterator directly, using `pytest-django`'s async support or `asyncio.run`.
- [ ] 4.8 Record `01-proofs/4.0-live-session.mov` with a test participant.

### [-] 5.0 Body-part tagging, session review and export (superseded)

Large, touch-friendly body-part buttons on the session screen, with click-to-toggle tagging:
- At most one part is active at a time.
- The server stamps start and end times.
- Segments under 1 s are discarded (configurable).
- Any active segment closes on a phase change or end.

Segments appear as labeled bands on the live graph. A review screen shows phases, segments and a per-part summary. Export writes the session's phases and segments into its folder. (Spec Unit 3.)

#### 5.0 Proof Artifact(s)

- Test: `uv run pytest tests/test_tagging.py` passes, covering:
  - Start.
  - Stop by clicking the same part.
  - Switching to another part (the previous segment is closed and the new one opened at the same `t`).
  - Discarding a segment shorter than `MIN_SEGMENT_SECONDS`.
  - Closing on a phase change and on end.
  - At most one open segment at any time.
  - Start and end times taken from `session_time`, not the client.

  Demonstrates the tagging rules.
- Test: `uv run pytest tests/test_summary_export.py` passes. From a fixture session with known samples and segments, it checks the per-part mean, count and total seconds against hand-computed values, and checks that `phases.csv` and `segments.csv` exist in the session folder, parse with `csv`, and contain no participant display name. Demonstrates summary and export.
- Test: `uv run pytest tests/test_review.py` passes: the review page for an ended session returns 200 and contains each tagged part's name and summary row. Demonstrates review.
- Screen recording: `01-proofs/5.0-tagging.mov` shows clicking parts on, off and across in a simulated session, with bands appearing live and the active part highlighted. Demonstrates the tagging UI.
- Screenshot: `01-proofs/5.0-review.png` shows the review screen for a finished simulated session. Demonstrates review.
- File: `01-proofs/5.0-export/` holds `phases.csv` and `segments.csv` from a simulated session. Demonstrates export.

#### 5.0 Tasks

- [ ] 5.1 Add a `Segment(session FK, body_part FK, start_t, end_t null)` model. Write `recording/tagging.py` with:
  - `toggle(session, body_part)`, using `t = session_time(session)`. If the open segment is the same part, it closes it. Otherwise it closes any open segment and opens a new one at the same `t`.
  - `close_active(session, t)`, which deletes the segment if its duration is under `settings.MIN_SEGMENT_SECONDS`.

  Call `close_active` from `change_phase`.
- [ ] 5.2 Add `POST /sessions/<id>/toggle/<part_id>/`, which returns `{active_part_id, segments: [...]}`, and `GET /sessions/<id>/segments/`, which returns the same shape so the screen (or a later second window) can load the current state. Reject toggles when the session is ended (400).
- [ ] 5.3 Add body-part buttons to `session.html`, in head-to-toe order from `BodyPart.objects.all()`. Clicks use pointer events (mouse and touch). The active part gets a clear highlight, and the state comes from the server response.
- [ ] 5.4 Draw the segment bands in `session.js` with a uPlot `hooks.draw` callback: shaded rectangles from `start_t` to `end_t` (or to now if still open), each with its part name. Load the existing segments on page open.
- [ ] 5.5 Write `recording/summary.py`: `summarize(session)` reads `samples.csv` and returns, for each body part, `{name, mean, count_segments, total_seconds, n_samples}`, using the samples whose `t` falls in that part's segments.
- [ ] 5.6 Write `recording/export.py`: `export_session(session)` writes `phases.csv` (`phase,t`) and `segments.csv` (`body_part,start_t,end_t`) into the session folder. `samples.csv` is already there.
- [ ] 5.7 Add the review screen `GET /sessions/<id>/review/` (`review.html` and `review.js`) with the full-session uPlot graph, phase markers as vertical lines, segment bands, the summary table, and an "Export" button (POST) that reports where the files were written. Link ended sessions from the home page.
- [ ] 5.8 Write `tests/test_tagging.py`, `tests/test_summary_export.py` and `tests/test_review.py`.
- [ ] 5.9 Capture `01-proofs/5.0-tagging.mov`, `01-proofs/5.0-review.png` and `01-proofs/5.0-export/` from a simulated session with a test participant.
