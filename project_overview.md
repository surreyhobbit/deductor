# Project Overview

This document contains combined README files from all GitHub repositories in the home directory.

---

# deductor

# Pocket Money Tracker

A lightweight self-hosted web app for tracking monthly pocket money.
Built with Flask + SQLite, runs in Docker, designed for Raspberry Pi.

---

## Quick Start

### 1. Configure children

Edit `app/db.py` and update the `CHILDREN` list near the top:

```python
CHILDREN = [
    {"id": 1, "name": "Chrissy",  "allowance_chf": 160},
    {"id": 2, "name": "Nick", "allowance_chf": 115},
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

---

# sleep

# Sleep Journal

A simple web app for tracking nightly sleep — designed to help flip a sleep rhythm from nocturnal back to normal.

## Running

```bash
docker compose up
```

Then open [http://localhost:8888](http://localhost:8888).

---

## Reading the sleep window chart

The **Sleep window — when you slept** chart on the Journal tab is the core tool for tracking rhythm progress.

### What it shows

Each bar spans from the time you went to bed (bottom of the bar) to the time you woke up (top). The x-axis is the date; the y-axis is the time of day.

```
14:00 ──────────────────────────────────────  ← 2 PM next day
      
10:00 ──────────────────────  ████  ████ ████
08:00 ──────────── ████ ████  ████  ████ ████
      
00:00 ════════════════════════════════════════  ← MIDNIGHT
      
22:00  ████ ████  ████ ████                 
20:00 ──────────────────────────────────────  ← 8 PM
         Mon  Tue  Wed  Thu  Fri  Sat  Sun
```

### The midnight line

The bright white grid line at **00:00** is midnight. Any bar that straddles this line means sleep crossed midnight — the person went to bed before midnight and woke up after, which is the goal.

A bar sitting entirely *above* midnight means bedtime was after midnight (nocturnal pattern). A bar sitting entirely *below* it means bedtime was in the evening (normal pattern). Progress shows as bars gradually shifting downward over time.

### What "getting better" looks like

| Pattern | What you see |
|---|---|
| Nocturnal (e.g. bed 03:00, wake 12:00) | Tall bar floating high above midnight |
| Transitioning | Bars creeping down toward and then across the midnight line |
| Normal rhythm (e.g. bed 22:30, wake 07:00) | Bar crossing midnight, roughly centred on it |

The goal is a band that straddles the midnight line and stays roughly in the same place night after night — consistent timing plus adequate duration.

### Hover for exact times

Hovering over any bar shows the exact bed and wake time, e.g. `Bed 23:00 → Wake 07:30`.

### Duration

The *height* of each bar is the total time asleep. A taller bar is more sleep. Aim for bars of consistent height (roughly 8–9 hours) as the band drifts downward.

---

## Logging a night

Go to the **Today** tab and fill in:

- **Date** — which night you're logging; defaults to today but can be changed (useful when logging after midnight)
- **Bed time** — when you got into bed
- **Minutes to fall asleep** — roughly how long it took
- **Wake time** — when you woke up
- **Out of bed time** — optional, if different from wake time
- **Quality** — 1–10 slider
- **Notes** — anything worth remembering

One entry per date; submitting again updates the existing entry for that date. Changing the date in the form immediately reloads any existing data for that date (or clears the form if there is none).

---

## DB maintenance

Navigate to [/admin](http://localhost:8888/admin) to view all entries and delete any incorrect ones. This page is not linked from the main navigation.

---

# trading

# 🚀 Crypto Portfolio Tracker

A comprehensive, self-hosted cryptocurrency portfolio tracking application built with Streamlit. Track your crypto holdings across multiple exchanges and wallets with automated data collection, real-time price updates, and beautiful visualizations.

## 📊 Features

### 🔄 **Multi-Exchange Support**
- **Binance** - Spot, futures, margin, and funding balances
- **Pionex** - Complete portfolio tracking
- **Lightning Network** - On-chain and channel balances

### 📈 **Real-Time Portfolio Tracking**
- Live price updates from CoinGecko API
- Historical portfolio value tracking
- Interactive charts and visualizations
- Portfolio composition analysis
- Performance metrics and trends

### 🤖 **Automated Data Collection**
- Daily automated balance updates
- Configurable collection frequency
- Manual refresh capability
- Startup data collection

### 🎨 **Beautiful Dashboard**
- Clean, responsive Streamlit interface
- Interactive pie charts and bar charts
- Historical performance graphs
- Asset breakdown by source
- Date-based portfolio snapshots

### 🐳 **Easy Deployment**
- Dockerized for simple deployment
- Runs 24/7 on Raspberry Pi
- Automated setup scripts
- Health monitoring and logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Exchanges     │    │   Portfolio      │    │   Dashboard     │
│                 │    │   Tracker        │    │                 │
│ • Binance API   │───▶│                  │───▶│ • Streamlit UI  │
│ • Pionex API    │    │ • Data Collection│    │ • Real-time     │
│ • Lightning LND │    │ • Price Updates  │    │   Charts        │
└─────────────────┘    │ • SQLite Storage │    │ • History View  │
                       └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   CoinGecko API  │
                       │   Price Data     │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi (3B+ or newer) or any Linux system
- Docker and Docker Compose
- API credentials for your exchanges
- Lightning Network node (optional)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/crypto-portfolio-tracker.git
cd crypto-portfolio-tracker
```

### 2. Quick Setup

```bash
chmod +x quick_start.sh
./quick_start.sh
```

### 3. Configure API Keys

Edit the `.env` file with your credentials:

```bash
nano .env
```

```env
# Exchange API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret
PIONEX_API_KEY=your_pionex_api_key
PIONEX_API_SECRET=your_pionex_secret

# Lightning Network (optional)
LND_GRPC_HOST=localhost:10009
LND_TLS_CERT_PATH=/app/certs/tls.cert
LND_MACAROON_PATH=/app/certs/readonly.macaroon
```

### 4. Start the Application

```bash
docker-compose up -d
```

### 5. Access Dashboard

Open your browser and navigate to:
- **Local**: http://localhost:8501
- **Network**: http://[your-ip]:8501

## 📁 Project Structure

```
crypto_portfolio_tracker/
├── 📊 ui/
│   └── dashboard.py              # Streamlit dashboard
├── 🔌 src/
│   └── data_collector.py         # Data collection logic
├── 💾 data/
│   ├── binance_account.py        # Binance API integration
│   ├── pionex_account.py         # Pionex API integration
│   ├── lightning_account.py      # Lightning Network integration
│   └── lightning/                # Lightning gRPC files
├── 🗄️ db/
│   └── database_init.py          # Database initialization
├── 🐳 docker/
│   ├── supervisord.conf          # Process management
│   └── crontab                   # Scheduled tasks
├── 📜 templates/
│   ├── history.html              # FastAPI templates
│   └── summary.html
├── 🧪 test/
│   └── test_lightning_connection.py
├── 📋 certs/                     # Lightning certificates
├── 📝 logs/                      # Application logs
├── ⚙️ config.py                  # Configuration management
├── 🗃️ portfolio.db               # SQLite database
├── 🐳 Dockerfile                 # Container definition
├── 🐳 docker-compose.yml         # Service orchestration
├── 📦 requirements.txt           # Python dependencies
├── 🔧 quick_start.sh             # Quick setup script
├── 🛠️ setup_raspberry_pi.sh      # Raspberry Pi setup
└── 📖 DEPLOYMENT_GUIDE.md        # Detailed instructions
```

## 🔧 Configuration

### Environment Variables

The application supports extensive configuration through environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Binance API key | Yes |
| `BINANCE_API_SECRET` | Binance API secret | Yes |
| `PIONEX_API_KEY` | Pionex API key | Yes |
| `PIONEX_API_SECRET` | Pionex API secret | Yes |
| `LND_GRPC_HOST` | Lightning node gRPC host | Optional |
| `LND_TLS_CERT_PATH` | Lightning TLS certificate path | Optional |
| `LND_MACAROON_PATH` | Lightning macaroon path | Optional |
| `BTC_WALLETS` | Bitcoin wallet addresses (comma-separated) | Optional |
| `ETH_WALLETS` | Ethereum wallet addresses (comma-separated) | Optional |

### Collection Frequency

Modify `docker/crontab` to change data collection frequency:

```bash
# Daily at 6 AM UTC (default)
0 6 * * * cd /app && python -m src.data_collector

# Every 4 hours
0 */4 * * * cd /app && python -m src.data_collector

# Hourly (be careful with API limits)
0 * * * * cd /app && python -m src.data_collector
```

## 📊 Dashboard Features

### Portfolio Overview
- Total portfolio value with 7-day change
- Asset allocation pie charts
- Balance breakdown by exchange
- Real-time price updates

### Historical Analysis
- Portfolio value over time
- Asset performance tracking
- Date-based snapshots
- Composition changes

### Data Management
- Manual refresh capability
- Export functionality
- Source filtering
- Date range selection

## 🛠️ Development

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/crypto-portfolio-tracker.git
cd crypto-portfolio-tracker

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python db/database_init.py

# Run dashboard
streamlit run ui/dashboard.py

# Run data collection
python -m src.data_collector
```

### Adding New Exchanges

1. Create new account class in `data/` directory
2. Implement `get_balances()` method
3. Update `src/data_collector.py` to include new exchange
4. Add API credentials to `.env` file

### Database Schema

```sql
CREATE TABLE portfolio_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    asset TEXT NOT NULL,
    balance REAL NOT NULL,
    fiat_value REAL NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 🐳 Docker Deployment

### Services

The application runs three main services via Supervisor:

1. **Streamlit Dashboard** - Web interface (port 8501)
2. **Cron Daemon** - Scheduled data collection
3. **Startup Collector** - Initial data collection

### Volumes

- `./portfolio.db:/app/portfolio.db` - Database persistence
- `./certs:/app/certs:ro` - Lightning certificates (read-only)
- `./logs:/app/logs` - Application logs

### Health Monitoring

The container includes health checks and logging:

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f crypto-tracker

# View data collection logs
docker-compose exec crypto-tracker tail -f /app/logs/cron_collection.log
```

## 🔐 Security

### API Security
- API keys stored as environment variables
- Read-only API permissions recommended
- No API keys stored in code or containers

### Lightning Security
- Certificates mounted read-only
- Uses readonly macaroon
- TLS encryption for gRPC communication

### Network Security
- Dashboard runs on localhost by default
- Use reverse proxy for external access
- Consider VPN for remote access

## 📈 Monitoring

### Logs

All application logs are stored in the `logs/` directory:

- `streamlit.log` - Dashboard application logs
- `cron_collection.log` - Data collection logs
- `startup_collection.log` - Initial collection logs
- `health.log` - System health checks

### Commands

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Manual data collection
docker-compose exec crypto-tracker python -m src.data_collector

# Access database
docker-compose exec crypto-tracker sqlite3 portfolio.db
```

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify API credentials in `.env`
   - Check API permissions (read-only access needed)
   - Validate internet connectivity

2. **Lightning Connection Issues**
   - Ensure certificates are in `certs/` directory
   - Verify LND is running and accessible
   - Check certificate paths in `.env`

3. **Dashboard Not Accessible**
   - Verify container is running: `docker-compose ps`
   - Check port 8501 is open: `sudo ufw allow 8501`
   - Review logs: `docker-compose logs crypto-tracker`

4. **Data Collection Failures**
   - Check cron service: `docker-compose exec crypto-tracker service cron status`
   - Review collection logs: `tail -f logs/cron_collection.log`
   - Test manual collection: `python -m src.data_collector`

## 📋 Requirements

### System Requirements
- 1GB+ RAM
- 2GB+ disk space
- Linux-based OS (Raspberry Pi OS, Ubuntu, etc.)
- Docker 20.10+
- Docker Compose 2.0+

### API Requirements
- Binance API key with read permissions
- Pionex API key with read permissions
- Lightning Network node (optional)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Web framework
- [CoinGecko](https://coingecko.com/) - Price data API
- [Plotly](https://plotly.com/) - Interactive charts
- [Docker](https://docker.com/) - Containerization

## 📞 Support

- 📖 Check the [Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed instructions
- 🐛 Report issues on [GitHub Issues](https://github.com/yourusername/crypto-portfolio-tracker/issues)
- 💬 Join discussions on [GitHub Discussions](https://github.com/yourusername/crypto-portfolio-tracker/discussions)

---

**⚠️ Disclaimer**: This software is for educational and personal use only. Always verify balances independently and use at your own risk. Not financial advice.
