# 01-spec-session-mvp.md

> **Status (2026-10-25): closed after task 1.0 (app shell).** Superseded by a new direction: portrait first, then a cursor-and-zoom session over the photo (see the "Interface Option 2" note). The remaining units were not built. See the task file for details.

## Introduction/Overview

Personal Heat Map is an art project. A participant wears a galvanic skin response (GSR) sensor while the facilitator talks them through their body, part by part. The readings become a heat map over a photo of the participant. This spec covers the first slice of the desktop session app: run a session against a **simulated** Philometer, record the raw GSR stream, watch it live, and tag stretches of the timeline with the body part being discussed.

The goal is a session app that feels like a real application and records every reading safely. Each tagged segment should be tied to a body part, so later milestones (the real hardware, the heat map overlay, consent) have trustworthy data to build on.

## Goals

- Launch the app as a native desktop window (not a browser tab) that manages its own local server.
- Record a full session's raw GSR stream to a crash-safe file with no dropped samples, without assuming a fixed sample rate.
- Show a live, responsive graph of the stream, with a provisional range and a color for the current reading.
- Let the facilitator tag timeline segments with one body part at a time, using click to start and click to stop.
- Define the color mapping once, in a small pure-Python library that the app uses now and the CircuitPython firmware can use in spec 02.

## User Stories

- **As the facilitator**, I want to open the session app like any other Mac app, so that it feels like a tool and not a webpage while I'm sitting with someone.
- **As the facilitator**, I want to start a session for a participant and see their readings stream live, so that I can point at a dip and say "every time I mention X, it dips."
- **As the facilitator**, I want to click a body part to mark that we're talking about it, and click again to stop, so that only the meaningful stretches feed the heat map. I shouldn't have to hold a button down through a long answer.
- **As the facilitator**, I want a calibration phase marked at the start of each session, so that I can find the participant's baseline and range before the walkthrough. Later I can tell the warm-up chat apart from the walkthrough.
- **As the facilitator**, I want every raw reading kept even if the app crashes, so that no session is lost and I can re-run any color algorithm later.
- **As the artist**, I want the color map defined in one place, so that the light on the participant's hand (spec 02) and the colors on screen always agree.

## Demoable Units of Work

### Unit 1: App shell, participants and the body-part list

**Purpose:** Establish the project, the native app window, and the core records (participants, body parts, sessions) so the facilitator can open the app and manage the basics.

**Functional Requirements:**

- The system shall be a uv-managed Python 3.15 project using Django 6.1, runnable with a single command (for example `uv run heatmap`).
- The system shall open its user interface in a native desktop window (current direction: pywebview), with no browser address bar or tabs.
- The system shall start its local web server when the window opens, and stop the server and any background workers when the window closes.
- The system shall bind the server to `127.0.0.1` only, on a free port chosen at launch.
- The system shall reject requests that do not come from the app's own window. Current direction: a secret generated at each launch, which the window presents and other local programs do not have.
- The system shall store a Participant profile in the database (for example a display name and optional notes), separate from Django's `User` model. `User` is reserved for whoever logs into the app (the facilitator).
- Session files at rest shall identify the participant only by ID, for example `participant_24`. Only the app links that ID back to the profile in the database.
- The system shall store a single, ordered, flat list of body parts, each with a name and display order. It shall be seeded with a draft head-to-toe list (see Open Questions), which the facilitator can edit.
- The system shall store a Session linked to one Participant, with start time, end time and current phase.
- The user shall be able to create and edit participants and body parts from within the app window.
- The system shall create a new timestamped folder inside `recordings/` (at the repository root, listed in `.gitignore`) for every session, for example `recordings/2026-10-21_19-42-05/`. That folder holds the session's raw data files and exports.
- The system shall keep participants, body parts, sessions, phases and segments in Django's standard database setup (`db.sqlite3`, already in `.gitignore`). Raw samples are never stored in the database.

**Proof Artifacts:**

- Screenshot: the app running in its own window with no browser chrome demonstrates the native-window app shell.
- CLI: `uv run heatmap` launches the app, and closing the window leaves no server process running (checked with `lsof`/`ps`), demonstrating clean start and shutdown.
- Test: a request to the local server without the per-launch secret is rejected, demonstrating the local access check.
- Test: model tests for Participant, BodyPart (ordering) and Session pass, demonstrating the data model.
- Test: starting a session creates a new timestamped folder under `recordings/`, demonstrating the data layout.
- Screenshot: the seeded body-part list shown in order in the app demonstrates seeding and editing.

### Unit 2: Simulated recording, live graph and the shared color library

**Purpose:** Run a full session against a simulated Philometer, so the recording, live view and calibration can be built and tested without hardware.

**Functional Requirements:**

- The system shall provide a simulated Philometer that produces a realistic GSR-like signal (slow drift plus occasional reactions), at a configurable sample rate.
- The system shall read samples in a background worker separate from web request handling. A slow or closed window shall not cause samples to be lost.
- The worker shall stamp each sample on receipt with a session-relative time from the app's clock. Nothing downstream shall assume a fixed sample rate.
- The worker shall append each sample to one append-only file in the session's timestamped folder, flushing regularly, so that a crash loses at most the last second of data.
- The user shall be able to start a session for a participant, which begins in a **Calibrating** phase. The user shall be able to move it to **Walkthrough**, and then **End** the session. Each phase change shall be recorded with its timestamp.
- The system shall stream new samples to the session screen as they arrive (current direction: Server-Sent Events), and the screen shall draw a scrolling live graph.
- The system shall track a provisional range (the running minimum and maximum of the session so far) and show it on screen.
- The system shall provide a small shared color library that maps a reading to a color given a range. It shall use only Python features and modules that are also available in CircuitPython, so the firmware can reuse it unchanged in spec 02.
- The color mapping shall support flipping its direction, so that "low reading = hot" or "high reading = hot" is a setting rather than a code change.
- The session screen shall show a "virtual light" whose color comes from the shared library, based on the current reading and the provisional range.
- The system shall keep the live data stream separate from the control screen, so that a second (participant-facing) window can be added later without reworking it.

**Proof Artifacts:**

- Screen recording or screenshot: a simulated session with the live graph scrolling, the provisional range shown, and the virtual light changing color demonstrates live view and color mapping.
- File: the session's raw data file opened after the session, with one row per sample and timestamps, demonstrates raw recording.
- Test: kill the app mid-session, then confirm the data file holds samples up to within ~1 second of the kill. This demonstrates crash safety.
- Test: the color library's unit tests pass under CPython, and a check confirms it imports only modules on a CircuitPython-compatible allowlist. This demonstrates the shared-library constraint.
- Test: simulated runs at different sample rates (for example 10 Hz and 100 Hz) record correctly with no dropped samples, demonstrating rate independence.

### Unit 3: Body-part tagging and session review

**Purpose:** Let the facilitator mark which body part is being discussed, producing the timeline of tagged segments that the heat map will be built from.

**Functional Requirements:**

- The session screen shall show the body parts as large, touch-friendly buttons, in head-to-toe order.
- The user shall click a body part to start tagging it. Clicking the same part again stops tagging, and clicking a different part stops the current tag and starts the new one.
- At most one body part shall be active at a time, and the active part shall be clearly highlighted.
- The system shall record each segment's start and end time when the click arrives at the server, in the same timebase as the samples.
- The system shall discard segments shorter than a minimum length (default 1 second, configurable) as accidental clicks.
- Ending the session or changing phase shall close any active segment.
- The live graph shall show tagged segments as labeled bands on the timeline as they happen.
- The user shall be able to open a finished session and see its full graph, with its phase markers and tagged segments.
- The system shall compute a per-body-part summary for a finished session (for example the mean reading and the number of segments per part), from the raw file and segments.
- The user shall be able to export a session (raw samples, phases and segments) into its timestamped folder, as files they can open in a spreadsheet or notebook.

**Proof Artifacts:**

- Screen recording: clicking parts on, off and across during a simulated session, with bands appearing on the live graph, demonstrates tagging.
- Test: toggle logic tests (start, stop with the same part, switch to another part, discard short segments, close on end of session) pass, demonstrating the tagging rules.
- Screenshot: the review screen for a finished session, showing phases, labeled segments and the per-part summary, demonstrates review.
- File: the exported session files demonstrate export.

## Non-Goals (Out of Scope)

1. **Real hardware:** the CircuitPython firmware, BLE (bleak), USB serial and the physical LED ring are spec 02. Only the simulator is built here, plus a device interface the real readers will plug into.
2. **Left/right pairs, a parent/child hierarchy and named sets (Broad/Granular) of body parts:** this round uses one flat list. The data model should not make adding them later hard, but none of it is built.
3. **Photos, region marking, the heat map overlay and the printed output.**
4. **Consent and distribution records, the reciprocal catalog/gallery, and the public samples.**
5. **Audio recording and transcripts**, including "strike that."
6. **Calibration warnings** (hands too sweaty, flat signal) and post-session re-scaling of the color range.
7. **A participant-facing second window**, though the design leaves room for it.
8. **Access from a phone or tablet on the local network.** The server is localhost-only for now.
9. **Packaging as a double-clickable `.app` bundle.**

## Design Considerations

- **Application feel:** a native window, no full-page reloads on the session screen, updates in place, keyboard-friendly. The facilitator's attention is on the participant, so the screen should be readable at a glance.
- **Session screen layout:** the live graph across the top; the virtual light and the current phase prominently shown; body-part buttons below in head-to-toe order. Buttons should be large enough for touch, with a clear highlighted state for the active part.
- **Phase controls** (Calibrating → Walkthrough → End) should be visible but hard to hit by accident. Ending a session in particular should need a confirmation.
- **Look:** calm and neutral. The palette for readings follows the thermal-camera feel from the project notes (the specific palette is an open question); the app chrome itself should stay quiet.
- **Admin-style screens** (participants, body parts) can be plain. They don't need to be polished in this milestone, but they should open inside the app window.

## Repository Standards

The repository is new (only a `.gitignore`), so this spec sets the initial conventions:

- uv for the Python version, dependencies and the lockfile (`uv.lock` committed).
- Django project layout with apps by domain (for example `sessions`, `catalog`); the shared color library lives in its own top-level package so the firmware can copy it unchanged.
- pytest with pytest-django for tests; ruff for linting and formatting.
- Front-end libraries are kept in the repo (vendored), not loaded from a CDN, so the app works fully offline.
- Short, imperative commit messages.
- Follow these conventions in later specs unless a spec changes them.

## Technical Considerations

All stack choices below are the **current direction**. They are open to change as we learn, especially the app shell.

- **Versions:** Python 3.15 and Django 6.1, chosen deliberately even though they are new and Django 6.1 is not an LTS release. A test install on 2026-10-21 confirmed pywebview 6.2.1 and Django 6.1.2 install and import on Python 3.15. Opening a window has not been tested yet. Django is moving to a yearly release cycle from 2028, so expect a yearly upgrade.
- **App shell:** pywebview opens a native WebKit window on macOS. If it feels wrong in use, a fully native Qt shell is the fallback, though it would mean rebuilding the screens.
- **Server:** Server-Sent Events need an async-capable (ASGI) server, such as uvicorn, rather than Django's development `runserver`. The app starts this server itself.
- **Live updates:** SSE for samples (server to window) and ordinary POST requests for clicks and phase changes. Django Channels stays an option if real-time traffic ever needs to go both ways.
- **Device interface:** define one simple device-reader interface ("give me the next sample") that the simulator implements now, and that the BLE and serial readers in spec 02 will implement.
- **Timekeeping:** samples and segment boundaries are both stamped by the app's clock on receipt, so they share one timebase. Clicks arriving over POST introduce a few milliseconds of delay, which is acceptable for conversation-scale tagging.
- **Data layout:** raw samples go to files, one timestamped folder per session under `recordings/`. Each folder holds its raw data file (CSV or JSON Lines; see Open Questions) and any exports. Django's standard `db.sqlite3` holds participants, body parts, sessions, phases, segments and the path to each session's folder. Keep the Django project otherwise standard (settings, database, admin) rather than inventing custom layouts.
- **Graph:** a lightweight charting library suited to streaming data (for example uPlot), vendored in the repo. The graph should keep a fixed window of recent data on screen so it stays fast in long sessions.
- **Shared color library limits:** CircuitPython lacks parts of the standard library (for example `dataclasses`, `typing` at runtime and most of `enum`). The library should stick to plain functions and basic math, and guard any optional import.
- **Compatibility risk:** Python 3.15 is new, so some dependencies may lag. Check each new dependency on 3.15 when adding it.

## Security Considerations

Session data is among the most sensitive data a person can share: their emotional reactions to their own body, tied to an alias. This spec must keep it safe even before photos exist.

- **Never in git:** session files live in `recordings/` and records live in `db.sqlite3`, and both are listed in `.gitignore`. Backups of the repo folder (Time Machine, cloud sync) will include both. Be aware of this before running sessions with real participants.
- **Proof artifacts:** use simulated sessions only. Do not commit screenshots, recordings or files from real participants.
- **Local only:** the server binds to `127.0.0.1` and rejects requests that lack the per-launch secret, so other programs and web pages on the laptop can't read session data.
- **Identity split:** profile details live only in the database. Files in `recordings/` carry only the participant ID (`participant_24`), so a session folder on its own doesn't say who it is.
- **No credentials or API keys** are needed in this milestone. Django's secret key lives in `settings.py` as in a standard Django project. The app is local-only, so this is acceptable for now.
- **No network calls:** the app makes no network calls (no CDNs, analytics or telemetry).

## Success Metrics

1. **No dropped samples:** a 30-minute simulated session at 20 Hz, and a 5-minute one at 100 Hz, each record every generated sample.
2. **Crash safety:** after a forced kill, the raw file holds data to within 1 second of the kill.
3. **Responsive tagging:** clicking a body part highlights it and starts a band on the graph with no noticeable delay (under ~100 ms on the laptop).
4. **Feels like an app:** the facilitator can run a full simulated session (start, calibrate, walk through about 10 parts, end, review) without seeing a browser UI or touching the terminal after launch.
5. **Shared library is portable:** the color library passes its tests on CPython and its import allowlist check, ready for CircuitPython in spec 02.

## Open Questions

1. **Final body-part list:** the draft seed list, head to toe and broad, is: Head, Face, Neck, Shoulders, Arms, Hands, Chest, Breasts, Ribs, Belly, Back, Hips, Butt, Sex, Thighs, Knees, Lower legs, Feet. Jacob to confirm or edit. It is editable in the app either way.
2. **Raw file format:** CSV (opens directly in a spreadsheet) or JSON Lines (easier to extend with new fields)? Default if not decided: CSV with a header row.
3. **Palette:** a thermal "ironbow" palette (black → purple → red → orange → yellow/white) or blue → red? The library should make swapping easy; the default is ironbow, to match the thermal-camera reference.
4. **Color direction:** the notes suggest a low GSR value (sweaty, nervous) reads as hot. Confirm against the Grove GSR module's actual output once the hardware is connected in spec 02. Until then, the direction is a setting.
5. **Sample rate:** to be found by experiment in spec 02 ("as fast as the board can push"). This spec only guarantees nothing assumes a fixed rate.
