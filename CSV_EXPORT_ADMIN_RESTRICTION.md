# CSV Export Admin Restriction Implementation

## Overview
CSV export functionality in the LISWMC Dashboard is now restricted to users with admin role only. This ensures data security and prevents unauthorized data downloads.

## Implementation Details

### 1. Role-Based Access Control
- **Admin users** (`role='admin'`): Full CSV export access
- **Non-admin users** (`role='viewer'`, `role='user'`): No CSV export access

### 2. UI Changes
The data table tab now checks user role and conditionally displays:

#### For Admin Users:
- Data table with built-in CSV export button (top-right of table)
- "Export Full Data to CSV" button below the table
- Both export methods work normally

#### For Non-Admin Users:
- Data table WITHOUT built-in CSV export functionality
- Disabled "CSV Export (Admin Only)" button below the table
- Clicking the disabled button shows access denied message

### 3. Backend Protection
The CSV export callback (`export_data`) now:
1. Checks user role from session data
2. Returns access denied message for non-admin users
3. Only processes export requests from admin users

### 4. Access Denied Message
Non-admin users attempting to export see:
```
Access Denied: CSV export is restricted to administrators only.
Please contact your system administrator for data export requests.
```

## Test Credentials

### Admin User (Has CSV Export Access)
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** `admin`

### Viewer User (No CSV Export Access)
- **Username:** `viewer`
- **Password:** `viewer123`
- **Role:** `viewer`

## Testing the Implementation

1. **Login as admin user:**
   - Navigate to Data Table tab
   - Verify CSV export button is active and functional
   - Verify data table has built-in export functionality
   - Test full data export

2. **Login as viewer user:**
   - Navigate to Data Table tab
   - Verify CSV export button shows as disabled with "(Admin Only)" text
   - Verify data table does NOT have built-in export functionality
   - Test clicking disabled export button shows access denied message

## Security Features

- **Session-based validation:** User role checked from authenticated session
- **Double protection:** Both UI restrictions and backend validation
- **Clear messaging:** Users understand why export is restricted
- **Graceful degradation:** Non-admin users can still view all data, just can't export

## Files Modified

1. **`analytics/db_dashboard.py`:**
   - Modified `update_data_table_tab()` to accept user data input
   - Added role checking logic for conditional UI elements
   - Modified data table configuration to conditionally enable export
   - Updated `export_data()` callback to validate admin role
   - Added access denied messaging for unauthorized attempts

## Compliance & Security Notes

- Maintains audit trail through existing authentication system
- Prevents unauthorized data extraction
- Allows administrators to control data access centrally
- Users can still view and filter data normally 