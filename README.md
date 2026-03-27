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

## Manual database access (fixing data errors)

Sometimes you may need to correct a record directly — for example if you changed
an allowance in `db.py` but the running container still has the old value stored.

### Step 1 — Find the container name

```bash
docker ps
```

Look at the **NAMES** column in the output. It will be something like `pocket-money`
or `pocket-money-pocket-money-1`. Use that name in the commands below.

### Step 2 — Open a shell in the container

```bash
docker exec -it <container-name> bash
```

You are now inside the container. The database file is at `/data/pocket.db`.

### Step 3 — Open the SQLite CLI

```bash
sqlite3 /data/pocket.db
```

You will see a `sqlite>` prompt.

### Useful commands

```sql
-- See all tables
.tables

-- Check current month's base amounts and deductions
SELECT c.name, ms.year, ms.month, ms.base_amount,
       (SELECT COALESCE(SUM(amount_chf),0) FROM deductions d
        WHERE d.child_id = ms.child_id AND d.year = ms.year AND d.month = ms.month) AS deducted
FROM monthly_summary ms
JOIN children c ON c.id = ms.child_id
ORDER BY ms.year DESC, ms.month DESC;

-- Fix a wrong base_amount for the current month (replace 25 and child_id as needed)
UPDATE monthly_summary
SET base_amount = 25
WHERE child_id = 1
  AND year  = CAST(strftime('%Y', 'now') AS INTEGER)
  AND month = CAST(strftime('%m', 'now') AS INTEGER);

-- Remove an accidental deduction (replace the id from the deductions table)
DELETE FROM deductions WHERE id = 42;

-- See all deductions for the current month
SELECT * FROM deductions
WHERE year  = CAST(strftime('%Y', 'now') AS INTEGER)
  AND month = CAST(strftime('%m', 'now') AS INTEGER)
ORDER BY deducted_at DESC;
```

### Step 4 — Exit

```sql
.quit
```

Then exit the shell:

```bash
exit
```

Changes are written immediately — reload the browser to confirm.

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