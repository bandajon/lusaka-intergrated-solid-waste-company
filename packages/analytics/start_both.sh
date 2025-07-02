#!/bin/bash
# Script to start both the Flask app and Analytics Dashboard together

echo "Starting both Flask app and Analytics Dashboard..."
echo "----------------------------------------------------"
echo "Flask app will be available at: http://127.0.0.1:5002/"
echo "Analytics Dashboard will be available at: http://localhost:5007/"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Start the analytics dashboard in the background
echo "Starting Analytics Dashboard..."
python db_dashboard.py > dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard started with PID: $DASHBOARD_PID"

# Wait a moment to ensure it's running
sleep 2

# Start the Flask app in the foreground
echo "Starting Flask app..."
export FLASK_APP=app.py
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5002

# When the Flask app is stopped, also stop the dashboard
echo "Stopping Analytics Dashboard (PID: $DASHBOARD_PID)..."
kill $DASHBOARD_PID

echo "Both services stopped"