# LISWMC Analytics Dashboard 🚀

Secure, authenticated analytics dashboard for Lusaka Integrated Solid Waste Management Company.

## 🔐 Authentication Features

- **Secure Login**: All dashboard content protected behind authentication
- **Role-Based Access**: Admin, User, and Viewer roles
- **Session Management**: 8-hour session timeout with auto-refresh
- **Account Security**: Login attempt limits and account lockouts
- **Password Protection**: bcrypt password hashing

## 🚀 Quick Start

### Option 1: Simple Startup (Recommended)
```bash
python start_dashboard.py
```

### Option 2: Direct Launch
```bash
python analytics/db_dashboard.py
```

## 🔑 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Viewer | `viewer` | `viewer123` |

> ⚠️ **Important**: Change these passwords after first login!

## 🌐 Access

Once running, open your browser to:
- **Local**: http://localhost:5007
- **Network**: http://0.0.0.0:5007

## 📊 Dashboard Features

### 🔐 Login Page
- Professional login interface
- Feature overview and instructions
- Error handling for failed logins
- Session persistence across refreshes

### 📈 Analytics (Business Hours: 8AM-5PM Zambia Time)
- **Overview Tab**: KPIs, trends, and heatmaps
- **Data Analysis**: Detailed charts and metrics
- **Location Insights**: Geographic analysis
- **Data Table**: Exportable data with filtering

### 🎛️ User Interface
- User info displayed in header
- Logout button in top-right corner
- Auto-refresh every 5 minutes
- Responsive design with Tailwind CSS

## 🔧 Database Setup

The dashboard requires a PostgreSQL database with the `liswmc_users` table.

### Run Migrations (if needed)
```bash
python run_migrations.py
```

### Database Tables
- `liswmc_users`: User authentication and management
- `company`: Company information
- `vehicle`: Vehicle tracking data  
- `weigh_event`: Waste collection events

## 🛡️ Security Features

- **Password Hashing**: bcrypt with salt
- **Session Tokens**: Secure session management
- **Account Lockout**: 5 failed attempts = 30-minute lockout
- **SQL Injection Protection**: Parameterized queries
- **Session Timeout**: 8-hour automatic logout

## 📁 Project Structure

```
analytics/
├── auth.py                 # Authentication system
├── database_connection.py  # Database connectivity
├── db_dashboard.py        # Main dashboard application
└── ...

migrations/
├── 001_create_users_table.sql
└── 001_rollback_users_table.sql

start_dashboard.py         # Simple startup script
run_migrations.py         # Database migration runner
```

## 🔧 Configuration

### Environment Variables (Optional)
```bash
export DB_HOST="your-database-host"
export DB_NAME="your-database-name"  
export DB_USER="your-database-user"
export DB_PASSWORD="your-database-password"
export DB_PORT="5432"
export DEBUG="True"
export PORT="5007"
```

### Default Configuration
- **Database**: AWS RDS PostgreSQL
- **Port**: 5007
- **Debug Mode**: Enabled
- **Auto-refresh**: 5 minutes
- **Session Timeout**: 8 hours

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project root directory
   cd /path/to/lusaka-intergrated-solid-waste-management-company
   ```

2. **Database Connection**
   ```bash
   # Check database connectivity
   python -c "from analytics.database_connection import get_db_connection; print('✅' if get_db_connection() else '❌')"
   ```

3. **Authentication Issues**
   ```bash
   # Reset admin password if needed
   python -c "from analytics.auth import AuthManager; AuthManager().change_password('admin_user_id', 'old_pass', 'new_pass')"
   ```

### Contact Support
For technical issues, contact the development team with:
- Error messages (full traceback)
- Browser console logs
- Database connection status

---

**© 2025 Lusaka Integrated Solid Waste Management Company** 