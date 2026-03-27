# Pocket Money Tracker

A lightweight self-hosted web app for tracking monthly pocket money.
Built with Flask + SQLite, runs in Docker, designed for Raspberry Pi.

---

## Quick Start

### 1. Configure children

Edit `app/db.py` and update the `CHILDREN` list near the top:

```python
CHILDREN = [
    {"id": 1, "name": "Mia",  "allowance_chf": 20},
    {"id": 2, "name": "Noah", "allowance_chf": 15},
]
```

Names and allowances are updated in the database each time the container starts,
so you can change them at any time by editing this list and restarting.

### 2. Build and run

```bash
# Clone / copy this folder onto your Pi, then:
cd pocket-money

docker compose up --build -d
```

The app will be available at:

```
http://<your-pi-ip-address>:5000
```

Find your Pi's IP with: `hostname -I`

### 3. View logs

```bash
docker compose logs -f
```

### 4. Stop / restart

```bash
docker compose down        # stop (data is preserved in the volume)
docker compose up -d       # start again (no rebuild needed)
docker compose up --build -d  # rebuild after code changes
```

---

## Data persistence

SQLite database is stored in a Docker named volume (`pocket_data`).
It survives container restarts, rebuilds, and `docker compose down`.

To back up the database:

```bash
docker cp pocket-money:/data/pocket.db ./pocket-backup.db
```

To restore:

```bash
docker cp ./pocket-backup.db pocket-money:/data/pocket.db
```

---

## Monthly reset

There is **no cron job or manual reset** needed.
When you first open the app in a new calendar month, a fresh monthly record is
automatically created for each child with their configured allowance.
All previous months remain in the history, accessible at `/history`.

---

## Project structure

```
pocket-money/
├── Dockerfile
├── docker-compose.yml
├── README.md
└── app/
    ├── app.py               # Flask routes
    ├── db.py                # SQLite layer + children config
    ├── entrypoint.sh        # init DB then start Gunicorn
    ├── requirements.txt
    └── templates/
        ├── index.html       # Current month view
        └── history.html     # Full history view
```

---

## Resource usage (Raspberry Pi)

| Metric          | Typical value |
|-----------------|---------------|
| Idle RAM        | ~35–55 MB     |
| Image size      | ~90 MB        |
| Startup time    | ~3 seconds    |
| CPU (idle)      | <1%           |

Tested on Raspberry Pi 4 (arm64) and Pi 3B+ (arm/v7).

---

## Customisation

| Task | Where |
|------|-------|
| Change names / allowances | `app/db.py` → `CHILDREN` |
| Add a third child | Add entry to `CHILDREN` list |
| Change port | `docker-compose.yml` → `ports` |
| Adjust log lines shown | `app/db.py` → `get_summary()` LIMIT clause |
| Style changes | `app/templates/index.html` `<style>` block |
