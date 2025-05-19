# Deploying as a Standalone Web Application

Google Earth Engine allows you to deploy applications as standalone web apps that anyone can access (with or without a GEE account). Here's how to deploy the Lusaka Waste Management Zone Planning Tool as a standalone application:

## Prerequisites

- Google Earth Engine account with Developer access
- All application files uploaded to your GEE Code Editor

## Deployment Steps

### 1. Prepare the App for Deployment

First, ensure that your app is working properly in the Code Editor. Make any necessary adjustments to improve the user experience in a standalone environment.

### 2. Create a New Deployment

1. In the Code Editor, with your `index.js` file open, click on the "Apps" button in the top-right corner
2. Select "NEW APP" from the dropdown menu
3. This will open the "Deploy an Earth Engine App" dialog

### 3. Configure Your App

In the deployment dialog:

1. **Name & Description**:
   - Enter a name for your app (e.g., "Lusaka Waste Management Zone Planner")
   - Provide a description of your application
   - Optionally add relevant tags

2. **URLs & Access**:
   - Choose a URL path for your app (e.g., "lusaka-waste-management")
   - The full URL will be: `https://[YOUR_USERNAME].users.earthengine.app/view/lusaka-waste-management`

3. **Access Options**:
   - Choose who can access your app:
     - **Private**: Only you
     - **Unlisted**: Anyone with the link
     - **Public**: Anyone, and it may be listed in public directories

4. **Earth Engine Access**:
   - Choose how the app will authenticate with Earth Engine:
     - **Default service account**: Recommended for public apps
     - **User-specific credentials**: Each user authenticates with their own GEE account (requires them to have a GEE account)

### 4. Deploy the App

1. Click "DEPLOY" to create your app
2. The deployment process may take a few minutes
3. Once completed, you'll receive a URL where your app is hosted

### 5. Share Your App

- Share the URL with your team or users
- If you chose "User-specific credentials," users will need to sign in with their Google Earth Engine account
- If you chose "Default service account," anyone can use the app without authentication

## Making Updates to Your App

After deployment, if you need to make changes:

1. Make your changes in the Code Editor
2. Save your changes
3. Go to the "Apps" menu again
4. Find your app in the list and click "UPDATE"
5. Your changes will be deployed to the live app

## Important Considerations

### Resource Limitations

- Standalone apps use Google's computation resources, which have limitations
- If your app performs heavy computations, consider:
  - Adding loading indicators
  - Optimizing your code
  - Processing smaller areas at a time

### Authentication Requirements

- If using the "Default service account," be aware of quota limitations
- For applications requiring higher quotas, consider using "User-specific credentials" but note that users will need Google Earth Engine accounts

### User Interface

- Standalone apps should have clear instructions for users
- Consider adding more help text and tooltips than would be necessary in the Code Editor

### Ongoing Maintenance

- Monitor your app's usage through the Google Cloud Console
- Be prepared to update the app as Earth Engine APIs evolve

## Alternative: Embedding in Your Own Website

If you want more control over the user experience, you can also embed your Earth Engine app in your own website:

1. Deploy as above
2. Use an iframe to embed the app in your site:
   ```html
   <iframe 
     src="https://[YOUR_USERNAME].users.earthengine.app/view/lusaka-waste-management" 
     style="width:100%; height:800px; border:none;"
   ></iframe>
   ```

This allows you to provide additional context, help pages, or integrate the app with your organization's existing web presence.