#!/bin/sh
# Initialise the database, then hand off to Gunicorn.
python -c "from db import init_db; init_db()"
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile - \
    app:app
