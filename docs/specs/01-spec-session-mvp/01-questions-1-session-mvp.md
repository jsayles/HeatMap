# 01 Questions Round 1 - Session MVP

Please answer each question below (select one or more options, or add your own notes). Feel free to add additional context under any question.

**Current direction (not questions, but open to change as we learn):**

- **Stack:** Python 3.15 with uv, Django 6.1. A quick install test on 2026-10-21 showed pywebview 6.2.1 and Django 6.1.2 both install and import on Python 3.15.
- **App shell:** Leaning toward a native window using pywebview, so it feels like an application rather than a browser tab. The app would start its own local Django server and shut it down on quit. If this doesn't feel right in use, a fully native shell (such as Qt) is still an option.
- **Live updates:** Leaning toward Server-Sent Events for the live graph, plus ordinary POST requests for button presses. Django Channels stays an option if real-time traffic ever needs to go both ways.
- **Locality:** Everything runs on the laptop.
- **Firmware:** Lives in `firmware/` in this repo.
- **Privacy:** Participant data is never committed to git.

## 1. Scope split

Should the real hardware path (CircuitPython firmware + BLE + USB serial) be part of this spec, or its own follow-up spec?

- [ ] (A) One spec, four demoable units: catalog → simulated recording + live graph → press-and-hold tagging → real Philometer
- [X] (B) Two specs: this one ends with the simulator; spec 02 covers firmware + BLE/serial
- [ ] (C) Other (describe)

**Recommended answer(s):** (A)

**Why these are recommended:**

- The whole point of the milestone is to sit with a wired-up person and tag readings; ending without real hardware leaves the MVP undemoable in the way that matters.
- The simulator-first ordering already de-risks the UI; hardware is the last unit, so if it bogs down it can be split out then. (B) is the safer choice if you expect firmware/BLE debugging to take a while.

## 2. Who decides the LED color?

Your notes say firmware does two jobs: show the color and send the GSR value. Where is the color computed?

- [ ] (A) Laptop computes the color (using the session's provisional range) and sends it back to the device; device just displays what it's told
- [ ] (B) Device computes its own color locally from a simple self-adjusting range; laptop only listens
- [ ] (C) Both: device runs a local fallback when not connected, laptop overrides when connected
- [ ] (D) LED color is out of scope for this milestone (firmware only sends readings)
- [*] (E) Other (describe)
  We have a DRY python library that can be used in both the firmware AND the web app to define the colors.  Then one definition, run in 2 contexts.  

**Recommended answer(s):** (C)

**Why these are recommended:**

- (A) keeps one source of truth for the color map, so the LED and the on-screen graph always agree and you can change palettes without reflashing. But the light goes dark or freezes if the link drops.
- (C) gets (A)'s consistency plus a light that still works standalone (battery on the hand, no laptop) — useful for playground demos. Slightly more firmware.
- (D) is the smallest scope, but the light on the hand is the participant-facing half of the experience.

## 3. Calibration phase

Is the calibration period (baseline chat, "hands too sweaty" warning, provisional range) in this milestone?

- [X] (A) Minimal: a "Calibrating" session phase marked on the timeline, and a running min/max range shown; no warnings
- [ ] (B) Full: calibration phase plus baseline-too-high / signal-flat warnings
- [ ] (C) Out of scope; just record
- [ ] (D) Other (describe)

**Recommended answer(s):** (A)

**Why these are recommended:**

- Raw data is always kept, so calibration logic can be refined later. But the live graph and LED need *some* range to scale to, and marking the calibration window now means old sessions can be re-analyzed later.
- (B) needs real GSR data from several people to set thresholds sensibly. Better done after a few real sessions.

## 4. Participant record

What does a session need to know about who is in it?

- [ ] (A) Just a session label/alias you type (e.g. "Neighbor A, test 1"); no participant model yet
- [X] (B) A minimal Participant (alias + optional notes) that sessions link to, so one person can have several sessions
- [ ] (C) Full participant record (contact info, intake details)
- [ ] (D) Other (describe)


**Recommended answer(s):** (B)

**Why these are recommended:**

- Consent, the reciprocal catalog, and repeat sessions all hang off a participant, so creating that link now avoids a migration later.
- An alias only (no real name or contact info) keeps the most sensitive data out of the MVP. (C) adds personal information with no MVP use.

## 5. Raw sample storage

How should the raw GSR stream be stored?

- [ ] (A) SQLite rows (one per sample) in the Django database
- [X] (B) An append-only file per session (CSV or JSON Lines) written by the device worker; the database stores session metadata and tagged segments
- [ ] (C) Both: write to the file first (crash-safe), then import into SQLite when the session ends
- [ ] (D) Other (describe)

**Recommended answer(s):** (B)

**Why these are recommended:**

- An append-only file the worker writes directly is the most crash-resistant option: a browser or Django hiccup can't lose samples, and you can open it in a spreadsheet or notebook.
- At ~10–50 samples per second, (A) works fine too, but couples data capture to the web process. (C) adds an import step with no clear MVP benefit.
- Segments refer to timestamps, so they can always be joined against the file.

## 6. Sample rate

Roughly how often should the device send a reading?

- [ ] (A) 10 Hz
- [ ] (B) 20–25 Hz
- [ ] (C) 50 Hz or more
- [ ] (D) Whatever the original Philometer used: ____
- [X] (E) Other (describe)
Unsure.  We need to play with it to find out.  I imagine we'll go with "as fast as that little circuit can push data over the wire/BLE"

**Recommended answer(s):** (B)

**Why these are recommended:**

- GSR changes over seconds, so 20–25 Hz captures every meaningful feature with headroom, and BLE UART handles it easily.
- 50 Hz+ adds noise and data without adding information; 10 Hz is fine but a bit coarse for pointing at the exact moment of a dip.

## 7. Press-and-hold behavior

How should holds behave at the edges?

- [X] (A) One part at a time: pressing a new part ends any current hold
- [ ] (B) Multiple simultaneous holds allowed (multi-touch: e.g. hold both shoulders together)
- [ ] (C) Also offer a keyboard shortcut / "latch" mode so you're not stuck holding a mouse button for a long answer
- [X] (D) Very short holds (under ~1 s) are discarded as accidental taps
- [X] (E) Other (describe)
Let's go with a click turns the part on... the data is being recorded for that part... then I click again to stop it or click on another part.

**Recommended answer(s):** (A), (D)

**Why these are recommended:**

- (A) keeps every reading tied to exactly one region, which keeps the heat map math simple. The "Combined pass" idea ("think about your breasts") is better served by a broad catalog region than by holding two buttons.
- (D) prevents stray taps from creating empty segments.
- (C) is worth considering if you expect long answers; holding a trackpad for two minutes is tiring. Tell me if you want it.

## 8. Device for the session screen

Where will you run the session screen during a session?

- [X] (A) Laptop only (mouse/trackpad) for now
- [X] (B) Laptop plus touch: the session screen must work on a tablet/phone on the local network
- [ ] (C) Laptop with a touchscreen
- [ ] (D) Other (describe)

**Recommended answer(s):** (A), with touch-friendly button sizes so (B) is easy later
Yes... your recomendation

**Why these are recommended:**

- Serving the app on the local network means thinking about access control for highly sensitive data. Keeping it bound to localhost for the MVP avoids that entirely.
- Large buttons that support both pointer and touch events cost nothing now and keep the tablet path open.

## 9. Body-part buttons layout

How should the body-part buttons be laid out for the MVP?

- [X] (A) Grouped word buttons (Head / Upper body / Arms / ...), left/right side by side
- [ ] (B) Buttons placed on a generic front/back body outline
- [ ] (C) Other (describe)

**Recommended answer(s):** (A)

Let's not make it too complicated.  For the first round lets just do one set of parts rather than left/right.  I'll try to group them and go head to toe and go with a wide section.. head, face, neck, shoulders, chest, breasts, ribs, belly, hips, sex...  This keeps it simple.  

**Why these are recommended:**

- Grouped buttons are quick to build, and it's obvious which part you're pressing. The body outline is appealing, but it overlaps with the later photo-region-marking work and is better designed then.
- Mirror left/right the way you'd face the participant? Add a note if you have a preference.

## 10. Participant-facing window

Your notes say the participant can watch the transcript, the photo and the heat map build live. Should the app plan for a second window for them, separate from your control screen?

- [X] (A) One window for now; design so a second window can be added later
- [ ] (B) Include a simple participant window in this milestone (live graph and current body part only, no controls)
- [ ] (C) Other (describe)

**Recommended answer(s):** (A)

**Why these are recommended:**

- In this milestone there is no photo, heat map or transcript yet, so a participant window would mostly duplicate the graph.
- Planning for it now still matters: keep the live data stream separate from the control screen so a second window can subscribe to it later. (B) is worth choosing if you want to see the graph-on-a-second-screen effect in early test sessions.
