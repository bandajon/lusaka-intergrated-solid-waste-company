# Lusaka Integrated Solid Waste Management Company (LISWMC)

A monorepo containing all applications and services for the Lusaka Integrated Solid Waste Management Company.

## Repository Structure

```
├── packages/
│   ├── analytics/          # Analytics Dashboard & Data Processing
│   ├── zoning/            # Zoning Management System  
│   └── shared/            # Shared utilities and components
├── docs/                  # Documentation
├── scripts/              # Build and deployment scripts
└── tools/                # Development tools and configs
```

## Packages

### 📊 Analytics (`packages/analytics/`)
Web-based analytics dashboard for waste management data visualization and reporting.

**Features:**
- Real-time waste collection analytics
- Vehicle performance tracking
- Location-based waste collection insights
- Company billing and fee management
- Data export and reporting

**Tech Stack:** Python, Dash, Plotly, PostgreSQL

[📖 Analytics Documentation](./packages/analytics/README.md)

### 🗺️ Zoning (`packages/zoning/`)
Zoning management system for waste collection routes and area management.

**Features:**
- Collection route planning
- Area zoning management
- Vehicle assignment optimization

**Tech Stack:** [To be determined]

[📖 Zoning Documentation](./packages/zoning/README.md)

### 🔧 Shared (`packages/shared/`)
Common utilities, database connections, and authentication used across packages.

**Components:**
- Database connection utilities
- Authentication and authorization
- Common data models
- Shared business logic

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (if using frontend packages)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd lusaka-intergrated-solid-waste-management-company
```

2. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run specific package**
```bash
# Analytics Dashboard
cd packages/analytics
pip install -r requirements.txt
python db_dashboard.py

# Zoning System
cd packages/zoning
# [Setup instructions to be added]
```

### Development

Each package is independent and can be developed, tested, and deployed separately:

```bash
# Work on analytics
cd packages/analytics
pip install -r requirements.txt
python -m pytest tests/

# Work on zoning  
cd packages/zoning
# [Setup commands to be added]
```

### Database Migrations

Shared database migrations are located in `packages/shared/database/migrations/`:

```bash
python scripts/run_migrations.py
```

## Documentation

- [Architecture Overview](./docs/ARCHITECTURE.md)
- [Technical Overview](./docs/TECHNICAL%20OVERVIEW.md)
- [Work Plan](./docs/WORK-PLAN.md)
- [Deployment Guide](./docs/deployment.md)

## Contributing

1. Each package maintains its own dependencies and configurations
2. Shared components go in `packages/shared/`
3. Documentation goes in `docs/`
4. Scripts for automation go in `scripts/`

## License

[License information] 