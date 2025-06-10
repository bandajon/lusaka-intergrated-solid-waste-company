#!/usr/bin/env python3
"""
Production entry point for the LISWMC Analytics Dashboard
"""

import os
from db_dashboard import app

# Configure for production - expose server for WSGI
server = app.server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug
    )