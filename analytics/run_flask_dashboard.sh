#!/bin/bash
# Run the updated Flask-integrated analytics dashboard

# First, kill any existing process using port 5000
lsof -i :5000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null

echo "Starting Flask Analytics Dashboard with auto-polling every 5 minutes..."
echo "Dashboard will be available at: http://localhost:5000/dashboards/weigh_events/"

# Set environment variable to ignore React warnings in development mode
export PYTHONWARNINGS="ignore::DeprecationWarning"

# Run the Flask app
cd "$(dirname "$0")"
python flask_app/run.py