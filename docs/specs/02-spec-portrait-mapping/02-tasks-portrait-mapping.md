# 02-tasks-portrait-mapping.md

Spec: [02-spec-portrait-mapping.md](02-spec-portrait-mapping.md)

## Relevant Files

| File | Why It Is Relevant |
| --- | --- |
| `pyproject.toml` / `uv.lock` | New dependencies: psycopg, pillow, pillow-heif, opencv-python-headless, mediapipe, pyobjc-framework-Vision. |
| `heatmap/settings.py` | PostGIS database, GDAL/GEOS library paths, `django.contrib.gis`, the `body_map` app, `MEDIA_ROOT`/`MEDIA_URL`, `FILE_UPLOAD_TEMP_DIR`, `SEGMENTATION_METHOD`, grid settings. |
| `heatmap/urls.py` | Media file serving; includes `body_map` URLs (replaces the placeholder home). |
| `.gitignore` | Ignore `body_map/ml_models/` (downloaded MediaPipe model files). |
| `README.md` | Update for subjects, PostGIS setup, `fetch_models`, `compare_segmentation`. |
| `body_map/models.py` | `Subject`, `Portrait` (files, coverage, outlines, alignment) and `Keypoint`. |
| `body_map/admin.py` | Subject editing; read-only portraits and key points. |
| `body_map/imaging.py` | Load JPEG/PNG/HEIC, apply rotation, remove location data, save the cleaned copy. |
| `body_map/segmentation.py` | The three background-removal methods as plain functions (image in, float mask 0–1 out) in a `METHODS` dict; `SEGMENTATION_METHOD` picks one. |
| `body_map/outline.py` | Mask → largest region → smoothed, valid polygon. |
| `body_map/landmarks.py` | Key-point detection using the framework that won 3.0 (one implementation only). |
| `body_map/alignment.py` | Similarity transform from the nose bridge and shoulders; point and geometry conversion; aligned-image rendering. |
| `body_map/pipeline.py` | `import_portrait()`: clean → segment → outline → landmarks → align or flag, all-or-nothing. |
| `body_map/forms.py` | Import form (subject, file, three coverage areas). |
| `body_map/views.py`, `body_map/urls.py` | Home, import, portrait view, overlay view. |
| `body_map/svg.py` | Turns stored geometry into SVG for the views (outlines and points drawn server-side). |
| `body_map/templates/body_map/*.html` | `base.html`, `home.html`, `import.html`, `portrait_detail.html`, `overlay.html`. |
| `body_map/static/body_map/app.css` | Calm, plain styling. |
| `body_map/management/commands/fetch_models.py` | Downloads the MediaPipe model files into the git-ignored models folder. |
| `body_map/management/commands/compare_segmentation.py` | The side-by-side comparison tool. |
| `docs/decisions/0001-background-removal.md` | The background-removal decision record. |
| `tests/fixtures/images/` + `ATTRIBUTION.md` | Openly licensed test photos and their credits and licenses. |
| `tests/images.py` | Helpers that build synthetic test images (shapes, EXIF with GPS/XMP, a rotation flag, HEIC). |
| `tests/test_subjects.py` | Subject model and admin. |
| `tests/test_import.py` | Import cleaning (rotation, GPS/XMP removal, camera details kept, ID paths, HEIC, no stray temp files). |
| `tests/test_coverage.py` | Coverage rules, required at import. |
| `tests/test_segmentation.py` | Each method returns a valid mask. |
| `tests/test_compare_command.py` | The comparison tool writes sheets only to the private folder. |
| `tests/test_outline.py` | Outline tracing. |
| `tests/test_import_pipeline.py` | Pipeline storage and the rejection path (with a fake segmenter). |
| `tests/test_alignment.py` | Alignment math. |
| `tests/test_landmarks_pipeline.py` | Key-point storage, grid outline, aligned image, not-aligned path (with a fake detector). |
| `tests/test_views.py` | Import / portrait / overlay pages. |
| `docs/specs/02-spec-portrait-mapping/02-proofs/` | Proof files (no images of private subjects). |

### Notes

- **Commands:** `uv run pytest [path]`, `uv run ruff check .`, `uv run ruff format .`. Commit on `main` with conventional messages ending in `Related to T<n>.0 in Spec 02`.
- **Keep Django standard:** use `startapp`, the admin, `ImageField`/`FileField` with `MEDIA_ROOT`, and GeoDjango model fields (`PolygonField`, `PointField`) with `srid=IMAGE_SRID`. The y axis runs downward.
- **Two coordinate systems, kept apart:** fields ending `_px` are original-photo pixels; fields ending `_grid` are standard-grid units. Never mix them in one query.
- **One app:** everything for this spec lives in the single `body_map` app (`Subject`, `Portrait`, `Keypoint`, import, views). Keep modules flat; no sub-packages or registries.
- **Deterministic tests:** pipeline and view tests swap the real segmentation and landmark functions for simple fakes with pytest's `monkeypatch`. Tests that run the real Apple Vision or MediaPipe models use the fixtures in `tests/fixtures/images/`, and skip if they're absent.
- **Private data:** tests set `MEDIA_ROOT` and `FILE_UPLOAD_TEMP_DIR` to `tmp_path`. Real subjects' photos, and any comparison sheet or screenshot made from them, never leave `recordings/`.
- **Public repo:** `jsayles/HeatMap` is public. Openly licensed fixtures (nude, partially clothed or clothed) may be committed, with credits in `ATTRIBUTION.md` (Jacob's decision, 2026-10-25). Private subjects' images never are.
- **Screenshots:** the agent's terminal lacks macOS Screen Recording permission, so Jacob takes the in-app screenshots and saves them to the named proof paths.
- **Assumptions for the spec's Open Questions:**
  1. The grid defaults are 1000 × 2000, nose bridge at (500, 200), shoulder width 250. They're settings: `GRID_SIZE`, `GRID_NOSE_BRIDGE`, `GRID_SHOULDER_WIDTH`.
  2. Every key point the detector provides is stored.
  3. Backups: left as is for now; listed in the README as a decision to make before importing real subjects' photos.
  4. Fixtures: the openly licensed images being gathered now, with synthetic images for the pure-logic tests.

## Tasks

### [x] 1.0 PostGIS database and subjects

Switch Django to GeoDjango + PostGIS on the local Postgres.app, add the `Subject` model with admin editing, run the existing spec 01 tests on PostGIS, and update the README for subjects and PostGIS. (Spec Unit 1: database, Subject.)

#### 1.0 Proof Artifact(s)

- CLI: `psql -d heatmap -c "select postgis_full_version();"` reports PostGIS 3.6, and `uv run manage.py showmigrations` shows every migration applied. Demonstrates the database move.
- Test: `uv run pytest` passes in full on the PostGIS test database, including the spec 01 access and server tests and the new `tests/test_subjects.py`:
  - A Subject has no relation to `User`.
  - Its file ID is `subject_<id>`.
  - The admin can list, add and edit subjects.

  Demonstrates the Subject model on PostGIS with nothing broken.

#### 1.0 Tasks

- [x] 1.1 Create the database with `createdb heatmap` (Postgres.app's `bin` on PATH), then `psql -d heatmap -c "create extension if not exists postgis;"`. Record both commands in the README.
- [x] 1.2 Run `uv add "psycopg[binary]"`. In `settings.py`:
  - Set `DATABASES['default']` to `ENGINE: 'django.contrib.gis.db.backends.postgis'`, `NAME: 'heatmap'`, `HOST: 'localhost'`, with no password.
  - Set `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` to `/Applications/Postgres.app/Contents/Versions/latest/lib/libgdal.dylib` and `.../libgeos_c.dylib`.
  - Add `'django.contrib.gis'` to `INSTALLED_APPS`.
- [x] 1.3 Run `uv run manage.py migrate` and `showmigrations`. Confirm `from django.contrib.gis.gdal import gdal_version` works through `uv run manage.py shell -c`.
- [x] 1.4 Run `uv run manage.py startapp body_map` and add it to `INSTALLED_APPS`. In `body_map/models.py` add `Subject(display_name, notes blank, created_at auto)` with a `file_id` property `f'subject_{self.pk}'` and `__str__` returning the display name, with no relation to `User`. Register it in admin with `list_display = ('display_name', 'created_at')`.
- [x] 1.5 Write `tests/test_subjects.py`:
  - The model has no field relating to `User`.
  - `file_id` format.
  - The admin changelist, add and change pages work through the existing `admin_client` fixture (which has the launch cookie).
- [x] 1.6 Run the full suite (`uv run pytest`). The spec 01 tests must pass unchanged on the PostGIS test database; pytest-django creates `test_heatmap` and the PostGIS backend enables the extension.
- [x] 1.7 Update the `README.md` wording: "participant" → "subject", SQLite → PostGIS, and the one-time database setup (1.1). Keep the private-data section, noting the Postgres data folder lives outside the repo.
- [x] 1.8 Write `02-proofs/02-task-01-proofs.md` with the `psql`, `showmigrations` and `pytest` output.

### [x] 2.0 Portrait import with location removal and coverage

An import screen inside the app window for one front portrait per subject:
- Accepts JPEG, PNG and HEIC.
- Applies the photo's rotation and removes location data, keeping camera details.
- Saves the photo under `recordings/subject_<id>/portrait_<id>/` through Django's media handling.
- Records coverage (chest, sex, buttocks: exposed / covered / not in photo), with the overall level worked out from it.

(Spec Unit 1: import, coverage.)

#### 2.0 Proof Artifact(s)

- Test: `uv run pytest tests/test_import.py` passes on a generated test photo that carries GPS, XMP location and a camera model, plus a rotation flag. It checks:
  - The stored copy has no GPS and no XMP location.
  - The camera model is kept.
  - The pixels are upright.
  - The path contains only IDs.
  - A HEIC input imports.
  - No copy of the upload is left in the temp-upload folder.

  Demonstrates safe import.
- Test: `uv run pytest tests/test_coverage.py` passes, covering every overall-level rule: nude / partly clothed / clothed, including "chest and sex exposed, buttocks not in photo → nude", import refusing unset coverage, and a second front portrait for the same subject being refused. Demonstrates the coverage rules and one front photo per subject.
- Screenshot: `02-proofs/02-task-02-import.png` shows the import screen in the app window, taken by Jacob, with no photo selected or with a non-sensitive test image. Demonstrates the in-app flow, including the file picker opening.

#### 2.0 Tasks

- [x] 2.1 **Early check:** add a temporary `<input type="file">` page and confirm by hand that pywebview opens the macOS file picker. If it doesn't, enable it, for example via pywebview's file-dialog support or a `js_api` bridge, before building on it. Record the result in the proofs.
- [x] 2.2 Run `uv add pillow pillow-heif` (both confirmed on Python 3.15). In `settings.py`:
  - Set `MEDIA_ROOT = BASE_DIR / 'recordings'`, `MEDIA_URL = 'media/'`.
  - Set `FILE_UPLOAD_TEMP_DIR = BASE_DIR / 'recordings' / 'tmp'` (created on start), so uploads never touch the system temp folder.

  Serve media in `urls.py` with `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`. It sits behind the launch-secret middleware like every other URL.
- [x] 2.3 Add the **Subject intake** fields: `gender` (choices `woman`, `man`, `non_binary`, `self_described` shown as "In my own words", `prefer_not_to_say`; blank allowed; no "Other"), `gender_self_description` (required only when self-described), `pronouns` and `year_of_birth`. `year_of_birth` is validated as 1900 to this year minus 18. Show them in the Subject admin and test them in `tests/test_subjects.py`. Then, in `body_map/models.py`, add `Portrait` with:
  - `subject` FK, `view` (choices: `front`), `imported_at`.
  - `original` ImageField, using an `upload_to` function in `models.py` that returns `subject_<sid>/portrait_<pid>/original.<ext>`. The portrait row is saved first so the ID exists.
  - Three coverage fields `chest`, `genitals`, `buttocks`, each with choices `exposed` / `covered` / `not_in_photo` and no default.
  - A unique constraint on `(subject, view)`.

  Add a `level` property implementing the rules: nude if at least one area is exposed and none are covered; partly clothed if at least one is exposed and at least one is covered; clothed if none are exposed. Label `genitals` as "Sex" (`verbose_name='sex'`).
- [x] 2.4 Write `body_map/imaging.py` with `clean_image(uploaded_file) -> (bytes, ext)`:
  1. Register the HEIF opener and open the image.
  2. Apply the rotation with `ImageOps.exif_transpose`.
  3. Copy the EXIF, delete the GPS block (tag `0x8825`), and set the orientation to 1.
  4. Drop any XMP and IPTC blocks entirely, since location can live there. Camera details are in EXIF and are kept.
  5. Save JPEG and HEIC inputs as JPEG (quality 95) and PNG as PNG, with the cleaned EXIF.

  Reject anything else with a clear message.
- [x] 2.5 Write `tests/images.py` helpers that build a small JPEG with an EXIF camera model, a GPS block, an XMP packet containing location and a rotation flag of 6. Also build a PNG, and a HEIC through pillow-heif.
- [x] 2.6 Write `body_map/forms.py` (`ImportForm`: subject, file, the three coverage areas as required radio choices with the labels "Chest", "Sex", "Buttocks") and the `import_portrait_view` (GET form; POST runs import and redirects). At this stage, import only cleans and stores the original; 4.0 extends it into the full pipeline. Add `import.html`, `base.html` and `home.html` (subjects with their portrait status, plus an "Import portrait" link) in `body_map`, and point `/` at the new home view, replacing `heatmap/views.py`.
- [x] 2.7 Write `tests/test_import.py` and `tests/test_coverage.py` as described in the proof artifacts. Import through the view with `launched_client` and a logged-in user as needed, then inspect the stored file with Pillow.
- [x] 2.8 Jacob captures `02-proofs/02-task-02-import.png`. Write `02-proofs/02-task-02-proofs.md`.

### [x] 3.0 Background-removal comparison and decision

A comparison command runs Apple Vision person segmentation, Apple Vision foreground mask and MediaPipe image segmenter on a folder of test photos. For each photo it writes a side-by-side sheet (outline over the photo, plus run time) to a private, git-ignored folder. You pick the winner, and the decision is recorded in the repo without images. **Needs your test photos and your judgment.** (Spec Unit 2: comparison, decision.)

#### 3.0 Proof Artifact(s)

- CLI: `uv run manage.py compare_segmentation <folder>` output lists, for each photo, all three methods with their run times, and says where the private sheets were written. Demonstrates the tool runs on real photos.
- Document: `docs/decisions/0001-background-removal.md` names the chosen method, the date, the reasons, and a description of the at least 5 photos it was judged on, with no images of private subjects. Demonstrates an evidence-based choice.
- Screenshot: `02-proofs/02-task-03-comparison.png` shows a comparison sheet for an openly licensed fixture (never a private subject). Demonstrates the side-by-side output.
- Test: `uv run pytest tests/test_segmentation.py` passes:
  - Each method in `METHODS` returns a float mask the same size as the input, with values from 0 to 1, on an openly licensed fixture.

  Demonstrates the common interface.
- Test: `uv run pytest tests/test_compare_command.py` passes: the command, run on a fixture folder, writes one sheet per photo, and only under `MEDIA_ROOT/comparisons/` (the git-ignored `recordings/` in the app). Demonstrates private output.

#### 3.0 Tasks

- [x] 3.1 Add the openly licensed images to `tests/fixtures/images/`. Recheck each license on its source page, and write `ATTRIBUTION.md` with file name, source URL, author, license and attribution text. Remove any image whose license can't be confirmed.
- [x] 3.2 Run `uv add opencv-python-headless mediapipe pyobjc-framework-Vision`. Create `body_map/segmentation.py`. Each method is a plain function `(image: PIL.Image) -> numpy.ndarray` (float32, H×W, 0–1), listed in a `METHODS` dict. `segment(image)` calls `METHODS[settings.SEGMENTATION_METHOD]`.
- [x] 3.3 Add the two Apple Vision methods to `segmentation.py`:
  - `vision_person`: `VNGeneratePersonSegmentationRequest`, quality level accurate.
  - `vision_foreground`: `VNGenerateForegroundInstanceMaskRequest`, all instances merged.

  Each converts the PIL image to a `CGImage`, reads the result pixel buffer into numpy, and resizes it to the input size.
- [x] 3.4 Write the `fetch_models` command. It downloads the pinned MediaPipe `.tflite` files (the selfie multiclass segmenter, plus the pose and face landmarker models in case MediaPipe wins) into `body_map/ml_models/`, which is git-ignored. Then add the `mediapipe` method to `segmentation.py`: the person mask from the multiclass model, as 1 − background.
- [x] 3.5 Write the `compare_segmentation <folder>` command. Output always goes to `MEDIA_ROOT / 'comparisons' / <timestamp>/` (that is, inside the git-ignored `recordings/`); there is no option to write anywhere else. For each image it runs every method, times it, and writes one PNG sheet: the image three times side by side, each with that method's outline drawn on it (mask threshold 0.5) and labeled with the method name and run time. It prints a summary table.
- [x] 3.6 Write `tests/test_segmentation.py` and `tests/test_compare_command.py` (`MEDIA_ROOT` is `tmp_path` in tests; check that the sheets land under `MEDIA_ROOT/comparisons/` and nowhere else).
- [-] 3.7 *(Skipped 2026-10-25: chosen from the 10 fixtures only; recorded as open in the decision record.)* Jacob runs the command on at least 5 private photos (his own and consenting subjects'), plus the fixtures, and picks the winner.
- [x] 3.8 Write `docs/decisions/0001-background-removal.md`: the decision, the date, the candidates, how they were judged (edge quality on hair, arm/torso gaps, skin against background), a description of the photos (counts and conditions only), the run times, the reasons, and the rejected options (rembg: not on Python 3.15). Set `SEGMENTATION_METHOD` to the winner in `settings.py`.
- [x] 3.9 Jacob captures `02-proofs/02-task-03-comparison.png` from a fixture sheet. Write `02-proofs/02-task-03-proofs.md`.

### [x] 4.0 Cutout and outline polygon in PostGIS

Import runs the chosen method behind a single setting, then saves the cutout and mask. It traces the largest body region into a smoothed, valid polygon stored in PostGIS in original-photo coordinates. A photo with no usable outline is rejected with a reason and leaves nothing behind. (Spec Unit 2: pipeline, outline, rejection.)

#### 4.0 Proof Artifact(s)

- Test: `uv run pytest tests/test_outline.py` passes, using a synthetic mask (a known shape plus stray specks). The traced polygon:
  - Is valid and closed.
  - Comes from the largest region only.
  - Has an area within 2% of the known shape.

  Demonstrates outline tracing.
- Test: `uv run pytest tests/test_import_pipeline.py` passes, with the fake segmenter:
  - A successful import stores the cutout, the mask and `outline_px`, and records `segmentation_method`.
  - An image with no person (an empty mask, or one smaller than the minimum area) is rejected with a reason and leaves no files, folders or database rows.

  Demonstrates the pipeline and the rejection path.
- CLI: `psql -d heatmap -c "select id, ST_IsValid(outline_px), ST_NPoints(outline_px) from body_map_portrait;"` shows a valid outline for a portrait imported from an openly licensed fixture. Demonstrates storage in PostGIS.

#### 4.0 Tasks

- [x] 4.1 Add these fields to `Portrait`, with a migration:
  - The `cutout` and `mask` file fields (`cutout.png`, `mask.png`).
  - `outline_px = PolygonField(srid=IMAGE_SRID, null=True)`.
  - `segmentation_method` CharField.
- [x] 4.2 Write `body_map/outline.py`: `trace_outline(mask) -> Polygon`.
  - Threshold at 0.5.
  - `cv2.findContours` with external contours only, keeping the largest by area.
  - Reject the outline if its area is under `MIN_BODY_AREA_FRACTION` of the image (default 0.02).
  - `cv2.approxPolyDP` with epsilon 1.0 px, so it smooths without cutting in.
  - Build a GEOS `Polygon(srid=IMAGE_SRID)`, then `make_valid` if needed, keeping the largest polygon.

  Raise `NoUsableOutline(reason)` on failure.
- [x] 4.3 Write `body_map/pipeline.py`: `import_portrait(subject, uploaded_file, coverage) -> Portrait`.
  1. Clean the image (2.4).
  2. Segment with `segmentation.segment()`.
  3. Save the mask, plus the cutout (original + mask as alpha).
  4. Trace the outline.

  Run it inside `transaction.atomic()`. On any exception, delete the portrait's folder and re-raise, so nothing is left behind. Point the import view at it, and show `NoUsableOutline` reasons on the form.
- [x] 4.4 Add a `fake_segment` fixture in `tests/conftest.py` that monkeypatches `segmentation.segment` to return a mask derived from the synthetic image's colors. Write `tests/test_outline.py` and `tests/test_import_pipeline.py`.
- [x] 4.5 Add an "Importing…" state to `import.html`: disable the button and show a message on submit, since segmentation takes several seconds.
- [x] 4.6 Import one openly licensed fixture through the app with the real winning method. Capture the `psql` output and write `02-proofs/02-task-04-proofs.md`.

### [x] 5.0 Landmarks and alignment to the standard grid

Detect the nose bridge, eyes, shoulders and the other available body points, and store them as named PostGIS points in both coordinate systems. Compute and store the alignment (shift, scale, rotation) from the nose bridge and shoulders, then store the grid outline and the aligned image. Mark a portrait "not aligned", with the reason, when key points are missing. (Spec Unit 3: landmarks, alignment, keep-and-flag.)

#### 5.0 Proof Artifact(s)

- Test: `uv run pytest tests/test_alignment.py` passes on synthetic key points (including a tilted, scaled, shifted body, and a mirrored left/right naming). After alignment:
  - The nose bridge is within 0.5 units of the fixed grid point.
  - The shoulder width is within 0.5% of the fixed width.
  - The shoulder line is within 0.5° of horizontal.
  - Converting grid → original → grid returns the starting points within 0.5 units.
  - Upper-body-only points align.

  Demonstrates the alignment math.
- Test: `uv run pytest tests/test_landmarks_pipeline.py` passes, with the fake detector:
  - An aligned portrait has `Keypoint` rows with `point_px` and `point_grid`, plus `outline_grid`, alignment numbers and `aligned.png`.
  - A portrait with no face found is saved with `alignment_status='not_aligned'`, the reason "face not found", `outline_px` intact, and no grid data.

  Demonstrates storage and the keep-and-flag path.
- Test: on each openly licensed fixture with a visible face, the real `landmarks.detect` finds the nose bridge and both shoulders; the test is skipped if fixtures are absent. Demonstrates real detection.
- CLI: `psql -d heatmap -c "select p.id, ST_AsText(k.point_grid) from body_map_keypoint k join body_map_portrait p on p.id = k.portrait_id where k.name = 'nose_bridge';"` shows `POINT(500 200)`, to within rounding, for aligned portraits. Demonstrates the alignment as stored in PostGIS.

#### 5.0 Tasks

- [x] 5.1 Add these fields to `Portrait`:
  - `outline_grid = PolygonField(srid=IMAGE_SRID, null=True)`.
  - The `aligned` file field (`aligned.png`).
  - `align_scale`, `align_rotation_deg`, `align_tx`, `align_ty` (null floats).
  - `alignment_status` (choices `aligned` / `not_aligned`) and `alignment_reason` (blank).

  Add `Keypoint(portrait FK, name, point_px PointField(srid=IMAGE_SRID), point_grid PointField(srid=IMAGE_SRID, null=True))` with `unique (portrait, name)`.
- [x] 5.2 Add the grid settings `GRID_SIZE = (1000, 2000)`, `GRID_NOSE_BRIDGE = (500, 200)`, and `GRID_SHOULDER_WIDTH = 250`.
- [x] 5.3 Write `body_map/alignment.py`:
  - `compute_alignment(nose, shoulder_a, shoulder_b) -> Alignment(scale, rotation_deg, tx, ty)`. Order the shoulders by image x, so naming doesn't matter. The rotation makes the shoulder vector horizontal, the scale is `GRID_SHOULDER_WIDTH / distance`, and the translation puts the nose at `GRID_NOSE_BRIDGE`.
  - `to_grid(x, y)` and `to_px(x, y)`.
  - `transform_geometry(geom, alignment, direction)`.
  - `render_aligned(cutout_image, alignment) -> RGBA image`, using `cv2.warpAffine` onto the grid canvas.
- [x] 5.4 Write `body_map/landmarks.py` with `detect(image) -> dict[name, (x, y)]`, using **MediaPipe** (decided 2026-10-25 for cross-platform reasons; see the decision record):
  - The pose landmarker (heavy) gives 33 body points, named as MediaPipe names them (`left_shoulder`, `right_knee`, …; left and right are the subject's own). Points with visibility under 0.5 are dropped.
  - The face landmarker gives the nasion, point 168, as `nose_bridge`.

- [x] 5.5 Extend `pipeline.import_portrait`. After the outline, detect key points and save the `Keypoint` rows with `point_px`.
  - If the nose bridge and both shoulders are present: compute the alignment, fill `point_grid` and `outline_grid`, save `aligned.png`, and set the status to aligned.
  - Otherwise: set `not_aligned` with a reason naming what's missing ("face not found", "shoulders not found").

  Never reject the import at this stage.
- [x] 5.6 Add a `fake_landmarks` fixture that monkeypatches `landmarks.detect`. Write `tests/test_alignment.py`, `tests/test_landmarks_pipeline.py`, and the real-detector fixture test.
- [x] 5.7 Re-import a fixture, capture the `psql` output, and write `02-proofs/02-task-05-proofs.md`.

### [ ] 6.0 Portrait view and all-subjects overlay

A portrait view shows the photo with its outline and key points, the aligned cutout on the grid with the nose-bridge and shoulder-width marks, and the coverage, overall level and alignment status. An overlay view draws every aligned outline on the grid, outlines only, with no photos. A spatial query check proves cross-subject questions work. (Spec Unit 3: views, spatial query.)

#### 6.0 Proof Artifact(s)

- Screenshot: `02-proofs/02-task-06-portrait-view.png` shows the portrait view for an openly licensed fixture: outline, key points, aligned cutout, coverage and status. Taken by Jacob. Demonstrates the portrait view.
- Screenshot: `02-proofs/02-task-06-overlay.png` shows the all-subjects overlay of outlines only. Taken by Jacob. Demonstrates cross-subject alignment without exposing any image.
- Test: `uv run pytest tests/test_views.py` passes:
  - The portrait page shows the coverage labels, the level and the status.
  - A not-aligned portrait shows its reason and no aligned panel.
  - The overlay page contains one SVG outline per aligned portrait and no `<img>` element.

  Demonstrates the view requirements.
- CLI: `psql -d heatmap -c "select id from body_map_portrait where ST_Contains(outline_grid, ST_Point(500, 300, 3857));"` returns the aligned fixture portraits. (500, 300) is 100 units below the nose bridge, so it should lie inside every aligned body. Demonstrates spatial questions across subjects.

#### 6.0 Tasks

- [ ] 6.1 Write `body_map/svg.py`: functions that turn a `Polygon` or a set of `Keypoint`s into SVG path and circle elements, in pixel or grid coordinates, for use in templates. No front-end library is needed.
- [ ] 6.2 Write the `portrait_detail` view and template:
  - **Left:** the original with an SVG overlay (outline and key points, with names on hover).
  - **Right:** `aligned.png` with an SVG overlay showing the grid border, a cross at `GRID_NOSE_BRIDGE`, and two ticks marking `GRID_SHOULDER_WIDTH`.
  - **Underneath:** coverage ("Chest", "Sex", "Buttocks"), the overall level, the segmentation method, and the alignment status or reason.
- [ ] 6.3 Write the `overlay` view and template: one SVG at grid size, with every aligned portrait's `outline_grid` as a thin, semi-transparent path, a count, and the nose-bridge cross. No `<img>`.
- [ ] 6.4 Link the portrait and overlay views from the home screen; the import redirects to the new portrait's view. Add `app.css` (calm, plain, panels side by side).
- [ ] 6.5 Write `tests/test_views.py`.
- [ ] 6.6 Import all the openly licensed fixtures. Run the `ST_Contains` query, and have Jacob capture both screenshots. Write `02-proofs/02-task-06-proofs.md`.
