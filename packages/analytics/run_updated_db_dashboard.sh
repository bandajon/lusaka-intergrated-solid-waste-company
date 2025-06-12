#!/bin/bash
# Run the updated database-connected analytics dashboard

# First, kill any existing process using port 5007
lsof -i :5007 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null

echo "Starting Updated Database Analytics Dashboard with auto-polling every 5 minutes..."
echo "Dashboard will be available at: http://localhost:5007/"

# Set environment variable to ignore React warnings in development mode
export PYTHONWARNINGS="ignore::DeprecationWarning"

# Run the dashboard
python db_dashboard.py