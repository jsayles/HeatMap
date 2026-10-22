# Personal Heat Map

Desktop session app for the Personal Heat Map art project: record a participant's galvanic skin response while talking through their body part by part, tag each stretch with the body part being discussed, and build a heat map from it.

## Run

```bash
uv run heatmap
```

Opens the app in its own window. The app starts a local server on `127.0.0.1` and stops it when the window closes.

The first time, create a login for the admin screens (participants, body parts):

```bash
uv run manage.py createsuperuser
```

## Develop

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run ruff format .   # format
```

Specs and task lists live in [docs/specs/](docs/specs/).

## Private data

`recordings/` (raw session files) and `db.sqlite3` (participants and sessions) hold private participant data. Both are in `.gitignore` and must never be committed.
