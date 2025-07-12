# LISWMC Service Architecture

## Overview

The LISWMC platform consists of multiple integrated services that work together to provide a comprehensive waste management solution with a unified login experience and role-based access control.

## Services and Ports

### 1. **Unified Portal** (Port 5005)
- **Description**: Single sign-on entry point for all services
- **Features**:
  - Unified authentication with role-based access
  - Dashboard showing only accessible services based on user role
  - User management (role-dependent)
  - **Integrated QR code generation and email service**
- **Access**: http://localhost:5005

### 2. **Analytics Dashboard** (Port 5007)
- **Description**: Real-time waste collection analytics
- **Features**:
  - Interactive data visualizations
  - Vehicle performance tracking
  - Location-based insights
  - Fee calculation and reporting
- **Access**: http://localhost:5007
- **Required Role**: Viewer or higher

### 3. **Data Management App** (Port 5002)
- **Description**: File upload and data processing utilities
- **Features**:
  - CSV/Excel file upload
  - Data cleaning and validation
  - Company unification tool (Analyst+)
  - License plate cleaning
  - Database import/export (Analyst+)
- **Access**: http://localhost:5002
- **Required Role**: Viewer or higher

### 4. **Zoning Service** (Port 5001)
- **Description**: Geographic zone management and GIS analytics
- **Features**:
  - Zone creation and editing (Analyst+)
  - Population and demographics analysis
  - Waste collection optimization
  - Google Earth Engine integration
- **Access**: http://localhost:5001
- **Required Role**: Viewer or higher

## Role-Based Access Control (RBAC)

### Available Roles

1. **Administrator** (`admin`)
   - Full system access
   - User management capabilities
   - All service permissions
   - System configuration

2. **Manager** (`manager`)
   - Manage data, analytics, and zones
   - View user accounts
   - Cannot create/modify users
   - Full access to operational features

3. **Data Analyst** (`analyst`)
   - Analyze data and create reports
   - Create and edit zones
   - Export data and reports
   - Company unification tools

4. **Operator** (`operator`)
   - Basic data operations
   - Upload and clean data
   - Generate QR codes
   - View-only for analytics

5. **Viewer** (`viewer`)
   - Read-only access to all services
   - View analytics and reports
   - No data modification capabilities

### Permission Matrix

| Service/Feature | Viewer | Operator | Analyst | Manager | Admin |
|----------------|---------|----------|---------|---------|--------|
| **Portal Access** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Analytics Dashboard** | View | View/Export | View/Export | View/Export/Admin | Full |
| **Data Management** | View | Upload/Clean | Full | Full | Full |
| **Company Unification** | View | View | Full | Full | Full |
| **QR Code Generation** | - | ✓ | ✓ | ✓ | ✓ |
| **Zoning Service** | View | View | Create/Edit | Full | Full |
| **User Management** | - | - | - | View | Full |

## Authentication Flow (SSO)

### Unified Login Experience

1. **Single Entry Point**: Users log in once through the Portal (port 5005)
2. **Role Detection**: System identifies user role and permissions
3. **Dynamic Dashboard**: Portal shows only services the user can access
4. **Automatic SSO**: Clicking any service automatically logs the user in

### How SSO Works

1. **Login Process**:
   ```
   User → Portal Login → Authentication → Session Token → Role Permissions
   ```

2. **Service Access**:
   ```
   Portal → Generate Analytics Token → Append to Service URL → Auto-login
   ```

3. **Session Management**:
   - Sessions last 8 hours
   - Shared across all services
   - Single logout from Portal ends all sessions

### Technical Implementation

- **Shared Session Token**: Generated on login, passed via URL parameters
- **Session Bridge**: Validates tokens across services
- **Permission Checks**: Each service validates user permissions
- **Automatic Redirects**: Unauthorized access redirects to Portal

## Starting the Services

### Option 1: Start Everything (Recommended)
```bash
# From project root
python start_platform.py --all

# Or from analytics directory
python start_analytics.py --all
```

### Option 2: Start Individual Services
```bash
# Portal only (includes QR service)
python start_analytics.py --portal

# Analytics Dashboard only
python start_analytics.py --dashboard

# Data Management only
python start_analytics.py --flask

# Zoning Service only
python start_analytics.py --zoning
```

## Security Features

1. **Password Security**:
   - Bcrypt hashing (v4.3.0)
   - Minimum 6 characters
   - Account lockout after 5 failed attempts

2. **Session Security**:
   - 8-hour timeout
   - Secure session tokens
   - CSRF protection

3. **Permission Enforcement**:
   - Role-based access at service level
   - Feature-level permission checks
   - API endpoint protection

## Database Schema

### Users Table (`liswmc_users`)
```sql
- user_id (UUID, Primary Key)
- username (Unique)
- password_hash
- full_name
- email
- role (admin/manager/analyst/operator/viewer)
- is_active
- created_at
- updated_at
- last_login
- login_attempts
- locked_until
```

## Configuration

### Environment Variables (.env)
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=liswmc_prod
DB_USER=your_user
DB_PASSWORD=your_password

# Optional: Custom ports
PORTAL_PORT=5005
DASH_PORT=5007
FLASK_PORT=5002
```

### MCP Configuration (.cursor/mcp.json)
For Cursor integration, add the same environment variables to the `env` section.

## Best Practices

1. **User Management**:
   - Assign minimum required role
   - Regular permission audits
   - Remove inactive users

2. **Security**:
   - Strong passwords
   - Regular password changes
   - Monitor failed login attempts

3. **Service Usage**:
   - Always access through Portal
   - Don't bookmark individual services
   - Log out when finished

## Troubleshooting

### Common Issues

1. **"Access Denied" Error**:
   - Check user role permissions
   - Ensure logged in through Portal
   - Contact administrator for access

2. **Service Not Loading**:
   - Verify service is running
   - Check port availability
   - Ensure database connection

3. **Login Issues**:
   - Check account status
   - Verify password
   - Check for account lockout

### Support

For technical support or access requests, contact your system administrator. 