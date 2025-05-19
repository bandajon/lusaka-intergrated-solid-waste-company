# Running the Lusaka Waste Management Zone Planning Tool

## Prerequisites
- Google Earth Engine account (if you don't have one, sign up at https://code.earthengine.google.com/)
- Basic familiarity with Google Earth Engine Code Editor

## Steps to Run the Application

### 1. Login to Google Earth Engine
- Go to https://code.earthengine.google.com/
- Sign in with your Google account

### 2. Create a New Repository (Optional)
- Click on the "Assets" tab in the left panel
- Click "NEW" → "Repository" 
- Name it "lusaka-waste-management" (or your preferred name)

### 3. Upload the Files
- In the Code Editor, click the "Scripts" tab in the left panel
- Right-click on your username or repository and select "New File"
- Name the file "index.js" and copy the contents from the index.js file in this project
- Click "Save"
- Repeat this process for all the module files, creating the following structure:
  - index.js
  - modules/config.js
  - modules/map.js
  - modules/ui.js
  - modules/drawing.js
  - modules/analysis.js
  - modules/export.js

### 4. Run the Application
- Open the "index.js" file in the Code Editor
- Click the "Run" button in the top right of the code editor
- The application should load in the map view

### 5. Application Loading Issues
- If the application doesn't load properly, check the "Console" tab at the bottom of the screen for errors
- Verify that all module paths are correct (they should match your folder structure)
- Ensure all files were uploaded with the correct content

## Alternative: Using a Single File

If you prefer to avoid creating multiple files, you can combine all code into a single file:

1. Create a new script file (e.g., "lusaka_waste_management_app.js")
2. Copy all the code from all files, replacing module imports with the actual code
3. Remove the `require('./modules/xxx')` statements and combine all the code
4. Run this single file

## Using the Application

1. After the application loads, you'll see a map of Lusaka on the left and control panel on the right
2. Navigate to your area of interest using the district selector
3. Use the "Draw Zone" tab to create waste management zones
4. Use the "Analysis" tab to analyze the zones you've created
5. Use "Edit Zones" to modify existing zones
6. Use "Export" to export your data

## Saving Your Work

- Google Earth Engine automatically saves your scripts in your account
- To save the data you create within the app (zones, analysis, etc.), use the Export functionality
- Exported data will be available in your Google Drive

## Troubleshooting

- If you encounter "User memory limit exceeded" errors, try working with smaller areas
- If the map fails to load, check your internet connection and refresh the page
- If certain datasets fail to load, they may be temporarily unavailable; try again later