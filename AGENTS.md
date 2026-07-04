# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **Shipyard Flask template**: a Flask + Celery app backed by
PostgreSQL, Redis, and LocalStack (emulated S3). Everything runs through Docker
Compose — there is no supported non-Docker "run locally" path. Docker itself is
already installed in the VM snapshot; the notes below cover the non-obvious
caveats for running it here.

### Services (all defined in `docker-compose.yaml`)

| Service | Required | Notes |
| --- | --- | --- |
| `web` | yes | Flask app on `http://localhost:8080`. With `DEV=true` it runs the Flask dev server (auto-reload); otherwise uWSGI. |
| `postgres` | yes | `web`/`worker` block on it at startup. Data lives in the `workspace_postgres` named volume. |
| `redis` | yes | Celery broker + result backend. |
| `worker` | optional | Celery worker + Beat; runs the `do_something` heartbeat every 5s (increments counters by 10). App serves pages without it. |
| `localstack` | optional | Emulated S3 for the `/files` routes only. Pinned to a free Community version (see below). |

### Starting everything (non-obvious startup steps)

- **The Docker daemon is NOT auto-started** (no systemd). Start it once per VM
  session before any docker command, e.g. in a tmux session:
  `sudo dockerd > /tmp/dockerd.log 2>&1 &` then wait a few seconds.
- **Use `sudo` for docker** (`sudo docker ...`, `sudo docker compose ...`). The
  `ubuntu` user is in the `docker` group, but the group is not active in fresh
  non-login shells, so the socket returns "permission denied" without sudo.
- Preserve the `DEV` env var through sudo: `DEV=true sudo -E docker compose ...`.
  Set `DEV=true` for the auto-reloading dev server.
- The `Makefile` calls the v1 `docker-compose` command; only the v2 plugin is
  installed, so a `/usr/local/bin/docker-compose -> docker compose` shim is used.
  `make` targets still won't have docker group access, so prefer the compose
  commands directly (with `sudo -E`) over `make develop`.

Bring-up sequence (mirrors `make develop`):
```
DEV=true sudo -E docker compose up -d postgres
sudo -E docker compose exec -T postgres sh -c 'while ! nc -z postgres 5432; do sleep 0.2; done'
DEV=true sudo -E docker compose run --rm worker poetry run flask db upgrade   # migrations
DEV=true sudo -E docker compose up -d                                          # all services
```

### Hello-world / smoke check

- Counter page (increments a DB-backed counter): `curl http://localhost:8080/`
- **S3 files flow order matters**: `GET /files` creates the `test-bucket` and
  lists it; `GET /files/create` uploads an object but does NOT create the bucket,
  so hit `/files` first or `/files/create` returns 500 (`NoSuchBucket`).

### Migrations & tests

- Migrations: `... docker compose run --rm worker poetry run flask db upgrade`.
  Postgres data persists in the `workspace_postgres` volume; if that volume is
  reset you must re-run migrations.
- Tests: pytest is installed but the template ships **no tests** (`pytest` reports
  "no tests ran"). Run with `... docker compose run --rm worker poetry run pytest`.

### Dependency notes (already handled in the committed `Dockerfile` / compose)

These pins exist because the template targets ancient runtimes (Python 3.8 on
Alpine 3.11) and its original unpinned dependencies no longer resolve today. If
you change `pyproject.toml`, `poetry.lock`, `Dockerfile`, or the compose file,
rebuild with `DEV=true sudo -E docker compose build` (the update script does not
rebuild images).

- Poetry is pinned to `1.1.15` (matches `poetry.lock` lock-version 1.1 and avoids
  modern Poetry's `rapidfuzz` source build on musl).
- `cryptography==2.8` is pre-installed so Poetry's keyring dep doesn't pull the
  latest cryptography (needs Rust / `setuptools>=77`, impossible on py3.8).
- `poetry config virtualenvs.create false` installs into the system interpreter;
  the venv Poetry seeds ships a setuptools too new to build the 2020-era sdists
  (psycopg2 2.8.4, uwsgi 2.0.18, SQLAlchemy-Utils). `/home/app/.local/bin` is
  added to `PATH` so `poetry run flask`/`celery` find their console scripts.
- LocalStack is pinned to `localstack/localstack:3.8.1`; the unpinned/`latest`
  tag now requires a paid `LOCALSTACK_AUTH_TOKEN` and exits (code 55) without one.
