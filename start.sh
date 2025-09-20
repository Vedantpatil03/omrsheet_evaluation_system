#!/bin/bash
# Run database initialization
python -c "from app import init_db; init_db()"

# Start the Gunicorn server
gunicorn --bind 0.0.0.0:$PORT app:app