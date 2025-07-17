# LISWMC Docker Deployment Guide

## Overview
This guide provides complete instructions for deploying the LISWMC (Lusaka Integrated Solid Waste Management Company) platform using Docker containers. All services and databases can be deployed in containers for consistent, scalable deployment.

## Architecture

### Services
- **Unified Portal** (port 5005) - Single sign-on entry point
- **Analytics Dashboard** (port 5007) - Real-time analytics and visualization
- **Data Management** (port 5002) - File upload and data processing
- **Zoning Service** (port 5001) - Geographic zone management
- **PostgreSQL** (port 5432) - Database with PostGIS
- **Redis** (port 6379) - Cache and session storage
- **Nginx** (port 80/443) - Reverse proxy and load balancer

## Quick Start

### 1. Prerequisites
```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER
```

### 2. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd lusaka-intergrated-solid-waste-management-company

# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Environment Variables
Create a `.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_DB=liswmc_db
POSTGRES_USER=liswmc_user
POSTGRES_PASSWORD=your_secure_password_here

# Application Security
SECRET_KEY=your_secret_key_here

# API Keys (optional but recommended)
OPENAI_API_KEY=your_openai_api_key
CLAUDE_API_KEY=your_claude_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Production settings
FLASK_ENV=production
DEBUG=false
```

### 4. Local Development Deployment
```bash
# Start all services for development
docker-compose up -d

# View logs
docker-compose logs -f

# Access services
# Portal: http://localhost:5005
# Analytics: http://localhost:5007
# Zoning: http://localhost:5001
# Data Management: http://localhost:5002
```

### 5. Production Deployment
```bash
# Start production deployment
docker-compose -f docker-compose.prod.yml up -d

# View status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Service Details

### Database (PostgreSQL with PostGIS)
- **Image**: `postgis/postgis:15-3.3`
- **Features**: PostGIS spatial extension, automatic initialization
- **Persistence**: Named volume `postgres_data`
- **Initialization**: Runs `scripts/init-db.sql` on first start

### Application Services
Each service has its own Dockerfile with:
- Health checks for monitoring
- Non-root user for security
- Proper dependency management
- Environment-based configuration

### Reverse Proxy (Nginx)
- **Development**: Basic HTTP proxy with rate limiting
- **Production**: HTTPS with SSL, security headers, optimized caching
- **Load Balancing**: Distributes traffic across service instances

## Management Commands

### Container Operations
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart zoning_service

# View service logs
docker-compose logs -f analytics_dashboard

# Execute commands in container
docker-compose exec postgres psql -U liswmc_user -d liswmc_db

# Scale services (production)
docker-compose -f docker-compose.prod.yml up -d --scale analytics_dashboard=3
```

### Database Management
```bash
# Access database
docker-compose exec postgres psql -U liswmc_user -d liswmc_db

# Run backup
docker-compose exec postgres pg_dump -U liswmc_user liswmc_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U liswmc_user -d liswmc_db < backup.sql

# Check database status
docker-compose exec postgres pg_isready -U liswmc_user
```

### Health Monitoring
```bash
# Check all service health
curl http://localhost:5005/health  # Portal
curl http://localhost:5007/health  # Analytics
curl http://localhost:5001/health  # Zoning
curl http://localhost:5002/health  # Data Management

# Docker health status
docker-compose ps
```

## Volume Management

### Data Persistence
- `postgres_data`: Database files
- `redis_data`: Cache data
- `analytics_uploads`: File uploads for analytics
- `zoning_uploads`: File uploads for zoning
- `nginx_logs`: Web server logs

### Backup Volumes
```bash
# Create backup
docker run --rm -v liswmc_postgres_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Restore backup
docker run --rm -v liswmc_postgres_data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/postgres_backup_20240101_120000.tar.gz -C /data
```

## Security Configuration

### Production Hardening
1. **Environment Variables**: Store secrets in environment files, not in images
2. **Non-root Users**: All containers run as non-root users
3. **Network Isolation**: Services communicate through dedicated Docker network
4. **Resource Limits**: Set memory and CPU limits in production
5. **SSL/TLS**: Configure SSL certificates for HTTPS

### SSL Certificate Setup
```bash
# Create SSL directory
mkdir ssl

# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/liswmc.key \
  -out ssl/liswmc.crt \
  -subj "/C=ZM/ST=Lusaka/L=Lusaka/O=LISWMC/CN=localhost"

# For production, use Let's Encrypt or proper CA certificates
```

## Monitoring and Logging

### Centralized Logging
```bash
# View aggregated logs
docker-compose logs -f --tail=100

# Filter logs by service
docker-compose logs -f analytics_dashboard

# Export logs
docker-compose logs --no-color > platform_logs_$(date +%Y%m%d).log
```

### Resource Monitoring
```bash
# Monitor resource usage
docker stats

# Detailed container information
docker-compose exec analytics_dashboard top
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check container logs
docker-compose logs service_name

# Verify environment variables
docker-compose config

# Check port conflicts
netstat -tulpn | grep :5005
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec postgres pg_isready -U liswmc_user

# Check database logs
docker-compose logs postgres

# Verify database initialization
docker-compose exec postgres psql -U liswmc_user -d liswmc_db -c "\dt"
```

#### File Permission Issues
```bash
# Fix upload directory permissions
sudo chown -R 1000:1000 uploads/
sudo chmod -R 755 uploads/
```

### Performance Optimization

#### Resource Limits (Production)
Add to docker-compose.prod.yml:
```yaml
services:
  analytics_dashboard:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

#### Database Optimization
```sql
-- Connect to database and optimize
VACUUM ANALYZE;
REINDEX DATABASE liswmc_db;
```

## Backup and Recovery

### Automated Backups
```bash
# Create backup script
cat > backup_script.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U liswmc_user liswmc_db | gzip > backups/liswmc_backup_$DATE.sql.gz
find backups/ -name "liswmc_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_script.sh

# Add to crontab for daily backups
echo "0 2 * * * /path/to/backup_script.sh" | crontab -
```

### Disaster Recovery
```bash
# Stop services
docker-compose down

# Restore volumes
docker volume rm liswmc_postgres_data
docker volume create liswmc_postgres_data

# Restore data
docker run --rm -v liswmc_postgres_data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/latest_backup.tar.gz -C /data

# Restart services
docker-compose up -d
```

## Kubernetes Deployment (Advanced)

For Kubernetes deployment, use the provided manifests:
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -l app=liswmc

# Access services
kubectl port-forward svc/liswmc-portal 5005:5005
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy LISWMC
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: |
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
```

## Support and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check logs and resource usage
2. **Monthly**: Update base images and dependencies
3. **Quarterly**: Review security settings and certificates
4. **Database**: Regular VACUUM and ANALYZE operations

### Scaling Guidelines
- **Development**: Single instance of each service
- **Production**: Multiple instances behind load balancer
- **High Availability**: Database clustering and service redundancy

## Default Credentials

**Development Environment:**
- Username: `admin`
- Password: `admin123`

**Change these credentials in production!**

---

For additional support, refer to the individual service documentation in their respective packages or contact the LISWMC development team.