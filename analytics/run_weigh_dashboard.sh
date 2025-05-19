#!/bin/bash
# Script to run the weigh events dashboard standalone

echo "Starting Weigh Events Dashboard..."
echo "-----------------------------------"
echo "The dashboard will be available at: http://localhost:5003/dashboards/weigh_events/"
echo ""

# Run the dash app directly
python weigh_events_app.py