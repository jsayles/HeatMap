# Task 01 Proofs - App on PostGIS, with subjects

## Task Summary

The app's database moved from SQLite to PostgreSQL + PostGIS (GeoDjango) on the local Postgres.app, using the GDAL and GEOS libraries Postgres.app bundles. A single `body_map` app now holds the `Subject` model: the person being mapped, separate from Django's `User`, and identified on disk only by `subject_<id>`. Subjects can be edited in the admin. The README covers the new setup.

## What This Task Proves

- The `heatmap` database has PostGIS 3.6.2 enabled, and every migration is applied.
- GeoDjango loads GDAL and GEOS from Postgres.app; no separate GDAL install is needed.
- `Subject` has no link to `User`, its file ID contains only its database ID, and the admin can list, add and edit subjects.
- All of spec 01's tests still pass, now running on the PostGIS test database.

## Evidence Summary

- `postgis_full_version()` reports PostGIS 3.6.2 with GEOS 3.14.1.
- `showmigrations` shows every migration applied, including `body_map.0001_initial`, and `makemigrations --check` finds no pending changes.
- The full suite passes: 15 tests, 4 of them new.
- `ruff check` and `ruff format --check` are clean.

## Artifact: PostGIS enabled in the app database

**What it proves:** the app's database is PostgreSQL with PostGIS.

**Why it matters:** outlines and key points are stored as PostGIS geometry from task 4.0 onward.

**Command:** `psql -h localhost -d heatmap -c "select postgis_full_version();"`

**Result summary:** PostGIS 3.6.2 on PostgreSQL 18, with GEOS 3.14.1 and PROJ 9.7.1.

~~~text
POSTGIS="3.6.2 08d9b9f" [EXTENSION] PGSQL="180" GEOS="3.14.1-CAPI-1.20.5" PROJ="9.7.1 NETWORK_ENABLED=OFF ...
~~~

## Artifact: GDAL and GEOS load from Postgres.app

**What it proves:** GeoDjango works with the libraries bundled in Postgres.app (`GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` in `heatmap/settings.py`).

**Why it matters:** the Django docs say to install GDAL separately for Postgres.app. That turned out to be unnecessary, which keeps setup to one app.

**Command:** `uv run manage.py shell -c "from django.contrib.gis.gdal import gdal_version; ..."`

**Result summary:** both libraries load.

~~~text
GDAL 3.8.5 GEOS 3.14.1-CAPI-1.20.5
~~~

## Artifact: Migrations applied

**Command:** `uv run manage.py showmigrations`, then `uv run manage.py makemigrations --check --dry-run`

**Result summary:** every migration is applied (`[X]`), including `body_map.0001_initial`, and there are no pending model changes.

~~~text
body_map
 [X] 0001_initial
contenttypes
 [X] 0001_initial
 [X] 0002_remove_content_type_name
sessions
 [X] 0001_initial
...            (admin and auth migrations, all [X])

$ uv run manage.py makemigrations --check --dry-run
No changes detected
~~~

## Artifact: Full test suite on PostGIS

**What it proves:**
- The Subject rules hold: no `User` relation, ID-only file name, and admin list, add and edit.
- The database move didn't break spec 01's launch-secret and server tests.

**Command:** `uv run pytest -v`

**Result summary:** 15 passed. pytest-django created the `test_heatmap` database with PostGIS automatically.

~~~text
tests/test_subjects.py::test_subject_has_no_relation_to_user PASSED
tests/test_subjects.py::test_file_id_uses_only_the_id PASSED
tests/test_subjects.py::test_admin_lists_subjects PASSED
tests/test_subjects.py::test_admin_adds_and_edits_subject PASSED
tests/test_access.py::test_request_without_launch_secret_is_rejected PASSED
tests/test_access.py::test_request_with_wrong_secret_is_rejected PASSED
tests/test_access.py::test_request_with_launch_secret_is_accepted PASSED
tests/test_access.py::test_launch_with_wrong_token_is_rejected PASSED
tests/test_access.py::test_launch_sets_cookie_and_unlocks_app PASSED
tests/test_access.py::test_empty_server_token_rejects_everything PASSED
tests/test_access.py::test_admin_also_requires_launch_secret[/admin/] PASSED
tests/test_access.py::test_admin_also_requires_launch_secret[/admin/login/] PASSED
tests/test_server.py::test_find_free_port_returns_unused_port PASSED
tests/test_server.py::test_server_binds_to_loopback_only PASSED
tests/test_server.py::test_server_starts_and_stops PASSED
============================== 15 passed in 1.13s ==============================
~~~

## Artifact: Lint and format

**Command:** `uv run ruff check . && uv run ruff format --check .`

**Result summary:** clean.

~~~text
All checks passed!
31 files already formatted
~~~

## Reviewer Conclusion

The app now runs on PostGIS, with the Subject model in place, and the existing behavior is intact. This is the foundation for storing portraits and their geometry in the following tasks.
