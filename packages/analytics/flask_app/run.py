from flask_app import create_app
from datetime import datetime
import os

app = create_app()

# Create uploads directory if it doesn't exist
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

# Add jinja2 global variables
@app.context_processor
def inject_globals():
    return dict(now=datetime.now())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
