# Port Configuration Change

## 🔄 What Changed

The Flask Data Management app has been moved from **port 5001** to **port 5002** to avoid conflicts with other applications.

## 🌐 New URLs

- **Analytics Dashboard (Dash)**: http://localhost:5007 *(unchanged)*
- **Data Management (Flask)**: http://localhost:5002 *(changed from 5001)*
- **Company Unification Tool**: http://localhost:5002/companies/unify *(updated)*

## 🔧 Configuration

Port settings are now centralized in `config.py`. You can override them with environment variables:

```bash
# Change Flask port (default: 5002)
export FLASK_PORT=5003

# Change Dash port (default: 5007)  
export DASH_PORT=5008

# Start with custom ports
python start_analytics.py --flask
```

## 🚀 How to Start

Use the unified startup script:

```bash
# Start Flask app on port 5002
python start_analytics.py --flask

# Start both services
python start_analytics.py --both

# Check available services
python start_analytics.py
```

## 🔍 Troubleshooting

If you still get "port in use" errors:

1. **Check what's using the port**:
   ```bash
   lsof -i :5002
   ```

2. **Kill the process if needed**:
   ```bash
   pkill -f "python.*flask"
   ```

3. **Use a different port**:
   ```bash
   export FLASK_PORT=5003
   python start_analytics.py --flask
   ```

4. **Check all service URLs**:
   ```bash
   python start_analytics.py  # Shows current configuration
   ```

This change ensures the company unification tool runs without conflicts!