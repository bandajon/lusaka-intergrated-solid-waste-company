# Google Earth Engine Setup Guide

This guide explains how to configure Google Earth Engine for the Lusaka Zoning Tool.

## Overview

The zoning tool uses Google Earth Engine to analyze satellite imagery for:
- Land use classification
- Population estimation
- Environmental monitoring
- Climate-based waste collection planning

## Setup Methods

### Method 1: Default Authentication (Development)

For development and testing, you can use the default Earth Engine authentication:

1. Install the Earth Engine CLI:
   ```bash
   pip install earthengine-api
   ```

2. Authenticate your account:
   ```bash
   earthengine authenticate
   ```
   This will open a browser window where you can log in with your Google account.

3. The tool will automatically use this authentication when no service account is configured.

### Method 2: Service Account (Production - Recommended)

For production environments, use a service account:

1. The service account credentials are already configured in `config/agripredict-82e4a-6631d28b0e09.json`

2. The configuration automatically uses these credentials when available.

3. Service Account Details:
   - Email: `agripredict-earth-engine@agripredict-82e4a.iam.gserviceaccount.com`
   - Project: `agripredict-82e4a`

## Testing the Configuration

Run the test script to verify your setup:

```bash
python test_earth_engine.py
```

Or run the example usage script:

```bash
python example_earth_engine_usage.py
```

## Troubleshooting

### Error: "Earth Engine not initialized"

1. For development: Run `earthengine authenticate`
2. For production: Ensure the service account JSON file exists at the configured path

### Error: "Permission denied"

1. Check that your Google account has Earth Engine access
2. For service accounts, verify the account has the necessary permissions in the GCP project

### Error: "Module 'ee' not found"

Install the Earth Engine API:
```bash
pip install earthengine-api
```

## Using Earth Engine in the Application

The Earth Engine functionality is integrated into the zone analysis features:

1. **Zone Analysis**: When viewing a zone, Earth Engine data is automatically fetched
2. **Land Use**: Satellite imagery is used to classify land use patterns
3. **Population**: WorldPop data provides population estimates
4. **Climate**: ERA5 data helps optimize collection schedules

## Environment Variables (Optional)

You can override the default configuration using environment variables:

```bash
export GEE_SERVICE_ACCOUNT="your-service-account@project.iam.gserviceaccount.com"
export GEE_KEY_FILE="/path/to/your/credentials.json"
```

## Resources

- [Earth Engine Python API Documentation](https://developers.google.com/earth-engine/guides/python_install)
- [Service Account Setup Guide](https://developers.google.com/earth-engine/guides/service_account)
- [Earth Engine Dataset Catalog](https://developers.google.com/earth-engine/datasets)