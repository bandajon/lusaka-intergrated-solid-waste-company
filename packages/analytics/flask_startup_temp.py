
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import and create the Flask app
from packages.analytics.flask_app import create_app
from datetime import datetime

app = create_app()

# Create uploads directory if it doesn't exist
uploads_dir = Path(__file__).resolve().parent / 'uploads'
uploads_dir.mkdir(exist_ok=True)

# Add jinja2 global variables
@app.context_processor
def inject_globals():
    return dict(now=datetime.now())

if __name__ == '__main__':
    from config import AnalyticsConfig
    app.run(debug=True, host=AnalyticsConfig.FLASK_HOST, port=AnalyticsConfig.FLASK_PORT)
