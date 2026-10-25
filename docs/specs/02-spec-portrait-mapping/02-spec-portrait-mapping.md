# 02-spec-portrait-mapping.md

## Introduction/Overview

Personal Heat Map overlays a subject's emotional readings on a photo of their body. Before any readings can be mapped, each subject's portrait has to become a **map**: the body cut out from its background, its outline traced, and the whole thing aligned to a standard grid so every body lands in the same place at the same scale. This spec builds that mapping framework: import a photo, remove the background, trace the outline, align it using the bridge of the nose and the shoulders, and store everything in PostGIS. There is no heat map yet, and body areas come in a later spec.

The goal is a trustworthy, spatially queryable store of subject portraits. It is the foundation that later body areas ("show me the torso across everyone"), the cursor-and-zoom session and the heat map all build on.

## Goals

- Import a subject's portrait into the app, with the photo's location data removed and its rotation applied, stored only in the private `recordings/` folder.
- Choose the background-removal method with the best body boundary through a side-by-side comparison on real photos, then use that one method.
- Store each portrait's body outline and key points in PostGIS, in both original-photo and standard-grid coordinates.
- Align every portrait so the nose bridge sits at a fixed grid point and shoulder width sets a fixed scale. When alignment isn't possible, keep the portrait and say why.
- Record what each photo shows (coverage), in a form that later links to body areas and the reciprocal catalog.

## User Stories

- **As the artist**, I want to import a subject's photo into the app and know it is stored privately with its location data removed, so that I can keep my promise that their photo is safe with me.
- **As the artist**, I want the body cut out cleanly from its background, so that the eventual heat map follows the true edge of the body, including hair and the gaps between arms and torso.
- **As the artist**, I want to compare background-removal methods side by side on real photos, so that I choose the best boundary from evidence rather than a guess.
- **As the artist**, I want every portrait aligned to the same grid at the same scale, so that later I can ask spatial questions across everyone, like "show me the torso".
- **As the artist**, I want to record whether the chest, sex and buttocks are exposed, covered or not in the photo, so that the reciprocal catalog can later show people only what they've shared.
- **As the artist**, I want a portrait that can't be aligned to be kept and flagged rather than rejected, so that I never have to ask a subject for a new photo just because their head was turned.

## Demoable Units of Work

### Unit 1: PostGIS database, subjects and portrait import

**Purpose:** Move the app onto PostgreSQL + PostGIS, add subjects and portraits, and let the artist import a photo privately and safely.

**Functional Requirements:**

- The system shall use PostgreSQL with PostGIS as its only Django database (GeoDjango), connecting to the local Postgres.app server. SQLite is no longer used.
- The system shall store a **Subject** (display name, optional notes), separate from Django's `User`, with optional intake details:
  - **Gender**, asked as "Which best describes your gender?": Woman / Man / Non-binary / In my own words (free text) / Prefer not to say. There is no "Other" option.
  - **Pronouns** (free text).
  - **Year of birth.** It must make the subject at least 18 this year. Files on disk shall identify a subject only by ID (for example `subject_24`).
- The system shall store a **Portrait** belonging to one subject, with a view type (only "front" in this MVP; the model allows other views later) and an import time.
- The user shall be able to create and edit subjects (standard Django admin), and import a portrait for a subject from a screen inside the app window.
- The system shall accept JPEG, PNG and HEIC photos (HEIC is the iPhone default).
- On import, the system shall apply the photo's stored rotation, remove all **location** data (GPS) from the image metadata, and keep the other camera metadata (camera model, exposure, date).
- The system shall save the stored copy under Django's media folder, set to the git-ignored `recordings/` folder, at a path that contains only IDs (for example `recordings/subject_24/portrait_7/original.jpg`). The uploaded original is not kept anywhere else in the app.
- The system shall record **coverage** for each portrait as three exposure areas: chest, sex (stored internally as `genitals`) and buttocks. Each area is one of *exposed*, *covered* or *not in photo*.
- The system shall work out an overall level from the coverage:
  - **nude** if at least one area is exposed and none are covered.
  - **partly clothed** if at least one is exposed and at least one is covered.
  - **clothed** if none are exposed.
- In the MVP, the artist sets coverage at import.

**Proof Artifacts:**

- Test: model tests pass for Subject, Portrait and coverage, including all overall-level rules (for example, chest and sex exposed with buttocks not in the photo → nude). Demonstrates the data model.
- Test: importing a test photo that carries GPS and camera metadata produces a stored copy with no GPS data, the camera model still present, the rotation applied, and an ID-only path under the media folder. Demonstrates safe import.
- CLI: `psql` shows the PostGIS extension enabled in the app database, and the Django migrations applied. Demonstrates the database move.
- Screenshot: the import screen in the app window, using an openly licensed or non-sensitive test photo. Demonstrates the in-app import flow.

### Unit 2: Background-removal comparison and body outline

**Purpose:** Choose the background-removal method with the best boundary from evidence, then use it to produce each portrait's cutout and outline polygon in PostGIS.

**Functional Requirements:**

- The system shall provide a comparison tool that runs each candidate method on a folder of test photos:
  - Apple Vision person segmentation (highest quality setting).
  - Apple Vision foreground mask.
  - MediaPipe image segmenter.

  For each photo it shall save each method's mask, drawn as an outline over the photo, side by side, plus the run time.
- The comparison tool shall write its output only to a private, git-ignored location, because the test photos include real subjects.
- The artist shall pick the winning method. The pick shall be recorded in a short written decision (method, date, why, a summary of the photos it was tested on) committed to the repo, with no images of real subjects.
- The system shall use one setting to name the background-removal method in use, defaulting to the winner. Each method shall sit behind one simple interface, so adding a method later (for example rembg, once it runs on Python 3.15) only means adding one implementation.
- On import, the system shall run the chosen method and save the cutout (the body with a transparent background) and the mask in the portrait's folder.
- The system shall trace the mask's outer boundary as a polygon:
  - Keep only the largest body region, dropping stray specks.
  - Smooth away pixel-level jaggedness without visibly cutting into the body.
  - Store the polygon in PostGIS on the portrait, in original-photo pixel coordinates.
- If no person or no usable outline is found, the system shall reject the import with a clear reason and keep nothing.

**Proof Artifacts:**

- Document: the committed background-removal decision record names the chosen method and the evidence behind it. Demonstrates an evidence-based choice.
- Screenshot: a comparison sheet for an openly licensed test photo, with all three methods side by side. Demonstrates the comparison tool. Sheets made from real subjects stay private.
- Test: on a committed test image with a known simple shape, the traced polygon is valid, closed, has the expected area within a small tolerance, and comes from the largest region only. Demonstrates outline tracing.
- Test: an image with no person is rejected with a reason, and no files or database rows are left behind. Demonstrates the rejection path.
- CLI: a `psql` query shows a portrait's outline as a valid PostGIS polygon (for example `ST_IsValid` and `ST_NPoints`). Demonstrates storage in PostGIS.

### Unit 3: Landmarks, alignment to the standard grid and the portrait view

**Purpose:** Align each portrait to the standard grid using the nose bridge and shoulders, store both coordinate versions, and show the result in the app.

**Functional Requirements:**

- The system shall detect key points on each portrait: the nose bridge (between the eyes), the left and right eye, and the left and right shoulder, plus any other body points the detector provides (for example elbows, hips, knees, ankles).
- The system shall store each key point in PostGIS as a named point, in both original-photo and grid coordinates.
- The system shall compute an alignment (shift, uniform scale, rotation) that puts:
  - The nose bridge at a fixed grid point.
  - The two shoulders a fixed distance apart (shoulder width sets the scale).
  - The shoulder line horizontal (sets the rotation).
- The system shall store the alignment numbers on the portrait, so either coordinate version can be recomputed from the other.
- The system shall store the outline polygon in grid coordinates as well, and save an aligned image (the cutout placed on the grid) in the portrait's folder.
- The system shall handle upper-body-only photos the same way, since alignment needs only the nose bridge and shoulders.
- If the nose bridge or either shoulder can't be found, but the outline is fine, the system shall keep the portrait with its outline, mark it **not aligned**, and record the reason (for example "face not found"). Aligning these by hand comes in a later version.
- The user shall be able to open a portrait in the app and see:
  - The photo with its outline and key points drawn on it.
  - The aligned cutout on the grid, with the fixed nose-bridge point and shoulder-width marks shown.
  - The coverage and the overall level.
  - The alignment status and reason.
- The user shall be able to see all aligned outlines of all subjects overlaid on the grid in one view, as a first look at cross-subject mapping.

**Proof Artifacts:**

- Test: alignment math tests pass on synthetic key points:
  - After alignment, the nose bridge is within 0.5 grid units of the fixed point.
  - The shoulder distance is within 0.5% of the fixed width.
  - The shoulder line is within 0.5° of horizontal.
  - Converting grid → original → grid returns the starting points within 0.5 units.

  Demonstrates correct alignment and that the stored numbers are reversible.
- Test: a portrait whose key points are missing is saved as "not aligned", with its reason and its outline intact. Demonstrates the keep-and-flag path.
- Screenshot: the portrait view for an openly licensed or non-sensitive test photo, showing the outline, key points, aligned cutout and status. Demonstrates the portrait view.
- Screenshot: the all-subjects overlay of outlines only (no photos) on the grid. Demonstrates cross-subject alignment without exposing any image.
- CLI: a `psql` spatial query (for example, which grid outlines contain the point 100 units below the nose bridge) returns the expected portraits. Demonstrates that the data supports spatial questions.

## Non-Goals (Out of Scope)

1. **The heat map**: no readings, colors or overlays of readings.
2. **Sessions, GSR recording, the simulator and hardware.** These are planned for later specs. Spec 01's recording design is the starting point.
3. **Body areas / the parts catalog**: no regions such as "left shoulder" or "torso" yet. The design keeps room for them as PostGIS polygons per portrait.
4. **Scrubbing**: no mask editing, no hand placement or dragging of key points, and no brightness/contrast/sharpening. Not-aligned portraits wait for this.
5. **Back, side or close-up views, and more than one photo per subject.** The model allows them later.
6. **The reciprocal catalog / gallery and consent records.** Coverage is recorded now to feed them later.
7. **Printing, export, and packaging the app.**

## Design Considerations

- **Feel:** screens open inside the native app window and stay calm and plain. This is a working tool for the artist.
- **Import screen:**
  - Choose the subject, pick the photo file, and set the three coverage areas. Each area has exposed / covered / not in photo, and the default is unset, so the artist must choose.
  - Then import. Show progress while background removal runs, then go straight to the portrait view.
- **Portrait view:** two panels side by side, the original photo with outline and key points on the left and the aligned cutout on the grid on the right. Coverage, overall level and alignment status sit underneath. Not-aligned portraits show their reason clearly.
- **Overlay view:** outlines only, as thin lines on the grid, with no photos, so it can be shown to others without revealing anyone's image.
- **Language:** clinical and inclusive. The app shows "Sex" for the area stored as `genitals`.
- **No photos in shared or committed material:** wherever possible, visual proofs use outlines, key points and numbers rather than images of real bodies.

## Repository Standards

From the repository (`README.md`, `pyproject.toml`) and spec 01:

- uv for Python and dependencies, with `uv.lock` committed. Python 3.15, Django 6.1.
- A standard Django layout: `startproject`/`startapp`, `SECRET_KEY` in `settings.py`, the Django admin for editing records, and Django's standard media-file handling.
- pytest with pytest-django (`uv run pytest`); ruff for lint and format (`uv run ruff check .`, single quotes, line length 100).
- Commit directly on `main` with conventional, imperative messages that reference the task and spec.
- Front-end libraries kept in the repo; no CDNs, the app works offline.
- Spec 01's app shell stays as is: the pywebview window, uvicorn on `127.0.0.1`, and the launch-secret middleware.

## Technical Considerations

All choices below are the **current direction** and open to change.

- **Database:**
  - Django's GeoDjango with the PostGIS database backend, on the Postgres.app 18 server already running locally (PostGIS 3.6.2 available).
  - Create a local database (for example `heatmap`) and enable the `postgis` extension; the test database needs it too.
  - Postgres.app includes the GDAL and GEOS libraries. Point Django's `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` at them rather than installing GDAL separately (the Django docs suggest a separate install, but the bundled libraries are present).
  - Postgres.app may show a one-time permission dialog the first time the app connects.
- **Coordinates:**
  - Use plain, non-geographic coordinates, labeled with `IMAGE_SRID = 3857` and never transformed (GeoDjango cannot store SRID 0; see `body_map/models.py`): units are pixels for original-photo geometry and grid units for aligned geometry. Keep them in separate fields per portrait, so the two are never mixed in a query.
  - The y axis runs downward, matching images.
- **Standard grid (default, adjustable):**
  - A 1000 × 2000 unit canvas.
  - The nose bridge fixed at (500, 200).
  - A shoulder width of 250 units.
  - These numbers are named settings, so they can be tuned once real portraits are in.
  - Changing them later means recomputing grid geometry from the stored original geometry and alignment numbers.
- **Alignment:**
  - A similarity transform (shift, uniform scale, rotation) computed from the nose bridge and the two shoulders.
  - The nose bridge is the detector's nasion point if it has one, otherwise the midpoint between the inner eye corners.
  - Prefer getting key points from the same framework as the winning background-removal method, if it provides good ones. Apple Vision has body-pose and face-landmark detection; MediaPipe has pose and face landmarkers.
  - Known trade-off: broad-shouldered bodies come out slightly smaller on the grid. That's acceptable, because body areas will later be defined per portrait rather than relying on perfect grid alignment.
- **Background removal:**
  - Apple Vision via pyobjc runs locally on macOS and works on Python 3.15. MediaPipe also works on 3.15.
  - rembg / BiRefNet are excluded for now because onnxruntime has no Python 3.15 build. They can be added behind the same interface later.
  - Tested 2026-10-25.
- **Outline tracing:** OpenCV contour finding on the mask (largest region only), then light smoothing, then a Shapely/GEOS validity check before saving.
- **Image handling:**
  - Use Pillow for reading and writing, plus a HEIC reader; check it installs on Python 3.15, with macOS's built-in image tools as a fallback.
  - Apply the stored rotation before processing.
  - Remove GPS data from EXIF, and also any location fields in other embedded metadata (for example XMP), since location can appear there too.
- **File upload in the window:** the pywebview window must open a file picker from a standard file input; confirm this early. Processing (segmentation can take seconds) should show progress and not freeze the window.
- **Room for body areas later:** a later spec will add body-area polygons per portrait, plus queries such as "the torso polygon of every portrait" or "outlines containing this grid point". Nothing in this spec should assume a portrait has only one shape.
- **Existing code:** the spec 01 tests currently run on SQLite and will run on the PostGIS test database instead.

## Security Considerations

- **These photos are the most sensitive data in the project** (often nude). They are processed and stored only on this laptop; no network calls, no cloud services. Apple Vision and MediaPipe both run locally.
- **Never in git:** all images (originals, cutouts, masks, aligned images, comparison sheets of real subjects) live under the git-ignored `recordings/` folder or another git-ignored private folder. The database lives in Postgres, outside the repo.
- **Location data removed on import**, so a stored photo can't reveal where it was taken, often the subject's home. Camera details are kept on purpose.
- **ID-only paths and file names:** files and folders never contain a subject's name.
- **Committed proofs and test fixtures:**
  - Use only openly licensed or non-sensitive images, or outlines and numbers.
  - Comparison sheets and screenshots of real subjects are never committed.
  - The decision record describes the test photos without including them.
- **Backups:** `recordings/` (and the Postgres data folder) will be included in Time Machine or cloud-sync backups. Worth deciding before importing real subjects' photos.
- **Local access:** the existing per-launch secret and the server's binding to `127.0.0.1` continue to protect the app from other programs on the laptop.
- **Database login:** Postgres.app uses local passwordless login by default. Keep the database settings free of passwords in committed files.

## Success Metrics

1. **Boundary quality chosen on evidence:** the comparison has been run on at least 5 real portraits (yours and consenting subjects'), and the decision record is committed.
2. **Alignment precision:** in tests, after alignment the nose bridge is within 0.5 grid units of the fixed point, the shoulder width within 0.5%, and the shoulder line within 0.5° of horizontal.
3. **Safe import:** 100% of stored photos have no GPS data, checked by an automated test.
4. **No lost portraits:** every photo with a usable outline is stored (aligned or flagged "not aligned" with a reason); only photos with no usable outline are rejected.
5. **Practical speed:** importing one phone photo (removal, tracing, landmarks, alignment) takes under 30 seconds on this laptop.

## Open Questions

1. **Grid numbers:** the defaults (1000 × 2000 canvas, nose bridge at (500, 200), shoulder width 250) are placeholders, to be tuned after the first real portraits.
2. **Which key points to store:** store everything the chosen detector provides (recommended), or only the nose bridge, eyes and shoulders?
3. **Backups:** should `recordings/` and the Postgres data be excluded from Time Machine or cloud sync before real subjects' photos are imported?
4. **Openly licensed test photos:** if no suitable full-body, anatomical-pose photo can be found, automated tests will use synthetic images (simple drawn shapes) plus your private photos for manual checks.
5. **Points the detectors don't find (Jacob, 2026-10-25):** the heat map will need nipples and sex (and likely the navel), and neither MediaPipe nor Apple Vision provides them; both detect posture joints only. A later spec (body areas / scrubbing) must add them, either by hand placement or by estimation from the detected joints. `Keypoint` stores points by name, so adding `left_nipple`, `right_nipple`, `navel` and `genitals` needs no schema change.
