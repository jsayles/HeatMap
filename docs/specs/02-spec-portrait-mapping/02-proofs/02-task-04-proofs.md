# Task 04 Proofs - Cutout and body outline stored in PostGIS

## Task Summary

Importing a portrait now runs the chosen background-removal method (`vision_person`) and saves three files: the cleaned photo, the mask and a cutout (the photo with the background transparent). It also traces the body's outer edge into a polygon stored in PostGIS, in original-photo pixels. A photo with no usable person is rejected with a clear reason before anything is saved, and a failure partway through removes whatever was written.

## What This Task Proves

- Outline tracing keeps only the largest body region, drops stray specks, thresholds the mask at 0.5, and produces a valid closed polygon whose area is within 2% of the true shape.
- A successful import stores `original`, `mask.png`, `cutout.png`, the outline and the method name.
- A photo with no person, or a person too small to map, is rejected with a reason shown on the form, leaving no files, folders or database rows.
- A failure while saving cleans up after itself.
- A real import of Demo Image 02 with Apple Vision produces a valid outline in PostGIS.

## Evidence Summary

- `psql` shows the Demo Image 02 outline: valid, 300 points, about 23% of the photo.
- 8 task-specific tests pass; the full suite has 56. Lint and format are clean.

## Artifact: Real import, outline in PostGIS

**What it proves:** the whole pipeline works with the real method: clean, remove background, trace, store.

**Command:** `import_portrait()` from a Django shell for a subject "Demo 02", using `tests/fixtures/images/02-commons-female-anatomical.jpg` (CC0), then:

~~~bash
psql -h localhost -d heatmap -c "select id, segmentation_method, ST_IsValid(outline_px) as valid, ST_NPoints(outline_px) as points, ST_SRID(outline_px) as srid, round(ST_Area(outline_px)) as area_px from body_map_portrait where outline_px is not null;"
~~~

**Result summary:** the import took 0.64 s. The outline is a valid 300-point polygon covering 388,780 px² of the 1067 × 1600 photo (about 23%), which is plausible for a standing body.

~~~text
imported portrait 3 for subject_3 in 0.64 s with vision_person
files: ['cutout.png', 'mask.png', 'original.jpg']

 id | segmentation_method | valid | points | srid | area_px
----+---------------------+-------+--------+------+---------
  3 | vision_person       | t     |    300 | 3857 |  388780
~~~

## Artifact: Outline and pipeline tests

**Command:** `uv run pytest -v tests/test_outline.py tests/test_import_pipeline.py`

**Result summary:** 8 passed. The pipeline tests use a predictable fake segmenter, so the results don't depend on the model.

~~~text
tests/test_import_pipeline.py::test_import_stores_cutout_mask_and_outline PASSED
tests/test_import_pipeline.py::test_photo_with_no_person_is_rejected_and_leaves_nothing PASSED
tests/test_import_pipeline.py::test_failure_while_saving_removes_the_folder PASSED
tests/test_import_pipeline.py::test_import_view_shows_no_person_reason PASSED
tests/test_outline.py::test_outline_is_a_valid_closed_polygon_of_the_body PASSED
tests/test_outline.py::test_soft_mask_is_thresholded_at_one_half PASSED
tests/test_outline.py::test_empty_mask_is_rejected PASSED
tests/test_outline.py::test_tiny_body_is_rejected PASSED
============================== 8 passed in 0.59s ===============================
~~~

Full suite: `56 passed`. `ruff check` and `ruff format --check` are clean, and there are no pending migrations.

## Deviation from the plan: SRID

The plan said to store geometry with `srid=0`. GeoDjango can't do that: GEOS reports SRID 0 as "none", so Django wraps every insert in `ST_Transform(..., 0)`, which PostGIS rejects. Geometry is instead labeled with `IMAGE_SRID = 3857` (in `body_map/models.py`), a flat (planar) SRID it is never transformed out of. The values are still image pixels (and, from task 5.0, grid units). The spec and task list are updated to match.

## Reviewer Conclusion

Each imported portrait now has a cutout, a mask and a valid body outline in PostGIS. Photos that can't be mapped are refused cleanly. This is the geometry that alignment (task 5.0) and the views (task 6.0) build on.
