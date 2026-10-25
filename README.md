# Personal Heat Map

Desktop app for the Personal Heat Map art project. It turns a subject's portrait into a body map (background removed, outline traced, aligned to a standard grid and stored in PostGIS) that later sessions and heat maps build on.

## Set up

The app uses PostgreSQL with PostGIS from [Postgres.app](https://postgresapp.com/), which also provides the GDAL and GEOS libraries GeoDjango needs. With Postgres.app running and its `bin` folder on your `PATH`, create the database once:

```bash
createdb -h localhost heatmap
psql -h localhost -d heatmap -c "create extension if not exists postgis;"
uv run manage.py migrate
```

Download the MediaPipe model files (into the git-ignored `body_map/ml_models/`):

```bash
uv run manage.py fetch_models
```

## Run

```bash
uv run heatmap
```

Opens the app in its own window. The app starts a local server on `127.0.0.1` and stops it when the window closes.

The first time, create a login for the admin screens (subjects):

```bash
uv run manage.py createsuperuser
```

## Develop

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
```

To compare the background-removal methods on a folder of photos (sheets go to `recordings/comparisons/`, never anywhere else):

```bash
uv run manage.py compare_segmentation path/to/photos
```

Specs and task lists live in [docs/specs/](docs/specs/).

## Demo Images

Two of the test photos are the Demo Images, the ones to use when showing the app:

- `tests/fixtures/images/01-commons-male-anatomical.jpg` — [source](https://commons.wikimedia.org/wiki/File:Anterior_view_of_human_male,_retouched.jpg)
- `tests/fixtures/images/02-commons-female-anatomical.jpg` — [source](https://commons.wikimedia.org/wiki/File:Anterior_view_of_human_female.jpg)

Both are CC0, so they can be used for anything without credit. A courtesy credit is "Mikael Häggström / City Studios Stockholm, CC0, via Wikimedia Commons". The copies in the repo are downscaled; full-size originals are on the source pages. CC0 covers the photos, not the models' likeness, so don't present the models as endorsing the project.

Credits for all test photos are in [tests/fixtures/images/ATTRIBUTION.md](tests/fixtures/images/ATTRIBUTION.md).

## Private data

Subjects' photos and everything made from them (cutouts, masks, aligned images, comparison sheets) live in `recordings/`, which is in `.gitignore` and must never be committed. Subject records live in the `heatmap` Postgres database, whose data folder is outside the repo (in Postgres.app's Application Support folder).

Backups such as Time Machine or cloud sync will copy both `recordings/` and the Postgres data folder. Decide whether that's acceptable before importing real subjects' photos.
