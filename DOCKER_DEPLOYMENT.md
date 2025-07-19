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



SOME USEFUL INFOMATION



⏺ Oracle Cloud Always Free Setup for LISWMC Platform

  🚀 Step 1: Create Oracle Cloud Account

  1. Sign Up Process

  # Go to: https://cloud.oracle.com/
  # Click "Start for free"
  # Choose your region (closest to you for better performance)

  Required Information:
  - Email address
  - Phone number (for verification)
  - Credit card (for verification only - won't be charged)
  - Government ID or passport

  Important Notes:
  - Choose "Individual" account type
  - Select region closest to your users (e.g., UK South for Europe/Africa)
  - Credit card is required but you won't be charged for Always Free resources

  2. Account Verification

  - Verify email address
  - Verify phone number with SMS
  - Upload ID document (quick approval)

  🖥️ Step 2: Launch ARM Instance

  1. Navigate to Compute

  # In Oracle Cloud Console:
  # Menu → Compute → Instances
  # Click "Create Instance"

  2. Instance Configuration

  # Name: liswmc-platform
  # Compartment: (root)
  # Availability Domain: (any)
  # Image: Ubuntu 22.04 (select "Change Image")
  # Shape: VM.Standard.A1.Flex (ARM-based)
  # OCPU: 1 (can use up to 4 total across all instances)
  # Memory: 6GB (can use up to 24GB total)
  # Boot Volume: 50GB (can use up to 200GB total)

  3. Networking Setup

  # Virtual Cloud Network: Create new VCN
  # Subnet: Create new public subnet
  # Public IP: Assign public IP
  # SSH Keys: Generate new key pair (download private key)

  4. Security List Configuration

  # After instance creation:
  # Go to: VCN → Security Lists → Default Security List
  # Add Ingress Rules:

  # HTTP Traffic
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 80

  # HTTPS Traffic  
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 443

  # Application Ports
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 5001-5007

  # SSH (already exists)
  Source: 0.0.0.0/0
  Protocol: TCP
  Port: 22

  🔧 Step 3: Connect to Instance

  1. SSH Connection

  # Download the private key from Oracle Cloud
  # Set permissions
  chmod 600 ~/Downloads/ssh-key-private.key

  # Connect to instance
  ssh -i ~/Downloads/ssh-key-private.key ubuntu@YOUR_INSTANCE_IP

  2. Initial Server Setup

  # Update system
  sudo apt update && sudo apt upgrade -y

  # Install essential packages
  sudo apt install -y curl wget git htop nano

  # Install Docker
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker ubuntu
  sudo systemctl enable docker
  sudo systemctl start docker

  # Install Docker Compose
  sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose

  # Verify installation
  docker --version
  docker-compose --version

  📁 Step 4: Deploy LISWMC Platform

  1. Get Your Code

  # Clone your repository
  git clone https://github.com/your-username/lusaka-intergrated-solid-waste-management-company.git
  cd lusaka-intergrated-solid-waste-management-company

  # Or if you don't have it on GitHub yet, create the files manually:

  2. Setup Environment

  # Copy environment template
  cp .env.example .env

  # Edit environment file
  nano .env

  Update .env with these values:
  # Database Configuration
  POSTGRES_DB=liswmc_db
  POSTGRES_USER=liswmc_user
  POSTGRES_PASSWORD=SecurePass123!@#

  # Application Security
  SECRET_KEY=your-super-secret-key-here-minimum-32-chars

  # Environment
  FLASK_ENV=production
  DEBUG=false

  # Database connection
  DB_HOST=postgres
  DB_PORT=5432

  # Redis
  REDIS_URL=redis://redis:6379

  3. Deploy Platform

  # Create required directories
  mkdir -p backups ssl

  # Deploy production environment
  docker-compose -f docker-compose.prod.yml up -d

  # Check deployment status
  docker-compose -f docker-compose.prod.yml ps

  # View logs
  docker-compose -f docker-compose.prod.yml logs -f

  🌐 Step 5: Access Your Platform

  1. Get Your Public IP

  # In Oracle Cloud Console:
  # Go to Compute → Instances → Your Instance
  # Copy the "Public IP Address"

  # Or from command line:
  curl ifconfig.me

  2. Access Services

  # Main Portal (Single Sign-On)
  http://YOUR_IP:80

  # Individual Services
  http://YOUR_IP:5005  # Unified Portal
  http://YOUR_IP:5007  # Analytics Dashboard  
  http://YOUR_IP:5001  # Zoning Service
  http://YOUR_IP:5002  # Data Management

  # Health Checks
  http://YOUR_IP:5005/health
  http://YOUR_IP:5007/health
  http://YOUR_IP:5001/health
  http://YOUR_IP:5002/health

  3. Default Login

  # Username: admin
  # Password: admin123
  # (Change this in production!)

  🔒 Step 6: Security Hardening

  1. Change Default Passwords

  # SSH into your instance
  ssh -i ~/Downloads/ssh-key-private.key ubuntu@YOUR_INSTANCE_IP

  # Access the database
  docker-compose -f docker-compose.prod.yml exec postgres psql -U liswmc_user -d liswmc_db

  # Update admin password (run in PostgreSQL)
  UPDATE shared.users SET password_hash = '$2b$12$NewHashedPasswordHere' WHERE username = 'admin';

  2. Enable Firewall

  # Configure UFW firewall
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow ssh
  sudo ufw allow 80
  sudo ufw allow 443
  sudo ufw allow 5001:5007/tcp
  sudo ufw enable

  3. Setup SSL (Optional)

  # Install Certbot
  sudo apt install -y certbot

  # Get your domain first, then:
  sudo certbot certonly --standalone -d yourdomain.com

  # Update nginx configuration to use SSL

  📊 Step 7: Monitoring and Maintenance

  1. Check System Resources

  # Monitor resource usage
  docker stats

  # Check disk usage
  df -h

  # Monitor logs
  docker-compose -f docker-compose.prod.yml logs -f --tail=50

  2. Setup Automated Backups

  # Create backup script
  cat > /home/ubuntu/backup.sh << 'EOF'
  #!/bin/bash
  cd /home/ubuntu/lusaka-intergrated-solid-waste-management-company
  docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U liswmc_user liswmc_db > backups/backup_$(date +%Y%m%d_%H%M%S).sql
  find backups/ -name "backup_*.sql" -mtime +7 -delete
  EOF

  chmod +x /home/ubuntu/backup.sh

  # Add to crontab for daily backups
  crontab -e
  # Add: 0 2 * * * /home/ubuntu/backup.sh

  🎯 Quick Deployment Script

  Save this as oracle_deploy.sh and run it after SSH connection:

  #!/bin/bash
  echo "🚀 Setting up LISWMC Platform on Oracle Cloud..."

  # Update system
  sudo apt update && sudo apt upgrade -y

  # Install Docker
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker ubuntu

  # Install Docker Compose
  sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose

  # Clone repository (replace with your repo)
  git clone https://github.com/your-username/lusaka-intergrated-solid-waste-management-company.git
  cd lusaka-intergrated-solid-waste-management-company

  # Setup environment
  cp .env.example .env
  sed -i 's/your_secure_password_here/SecurePass123!@#/g' .env
  sed -i 's/your_secret_key_here_minimum_32_characters/SuperSecretKey123456789012345678901234567890/g' .env
  sed -i 's/FLASK_ENV=development/FLASK_ENV=production/g' .env
  sed -i 's/DEBUG=true/DEBUG=false/g' .env

  # Create directories
  mkdir -p backups ssl

  # Deploy
  docker-compose -f docker-compose.prod.yml up -d

  # Wait for services to start
  echo "⏳ Waiting for services to start..."
  sleep 60

  # Show status
  echo "✅ Deployment complete!"
  echo "🌐 Access your platform at: http://$(curl -s ifconfig.me):80"
  echo "👤 Default login: admin / admin123"
  echo "📊 Service status:"
  docker-compose -f docker-compose.prod.yml ps

  🔧 Troubleshooting

  Common Issues:

  # If services don't start:
  docker-compose -f docker-compose.prod.yml logs

  # If can't connect:
  # Check Oracle Cloud Security Lists
  # Verify firewall rules: sudo ufw status

  # If out of memory:
  # Monitor with: docker stats
  # Reduce container limits in docker-compose.prod.yml

  💰 Cost Verification

  Your Oracle Cloud usage will be:
  - VM.Standard.A1.Flex: 1 OCPU, 6GB RAM (within free limits)
  - Block Storage: 50GB boot volume (within free limits)
  - Network: 10TB monthly transfer (within free limits)
  - Total Cost: $0/month forever

  🎉 Final Result

  After completion, you'll have:
  - ✅ Professional LISWMC platform running 24/7
  - ✅ Public IP access to all services
  - ✅ Containerized, scalable deployment
  - ✅ Automated backups and monitoring
  - ✅ Total cost: $0/month

  Would you like me to help you with any specific step, or do you need assistance with domain setup for professional URLs?

> when i try to log into the instance iam getting this response     @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
  @         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
  @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
  Permissions 0644 for 'ssh-key-2025-07-17.key' are too open.
  It is required that your private key files are NOT accessible by others.
  This private key will be ignored.
  Load key "ssh-key-2025-07-17.key": bad permissions
  ubuntu@129.80.196.187: Permission denied (publickey).

⏺ Fix SSH Key Permissions for Oracle Cloud

  The issue is that your SSH private key has incorrect permissions. Here's how to fix it:

  🔧 Quick Fix

  1. Fix Key Permissions

  # Navigate to where your key is downloaded
  cd ~/Downloads

  # Set correct permissions (only you can read/write)
  chmod 600 ssh-key-2025-07-17.key

  # Verify permissions
  ls -la ssh-key-2025-07-17.key
  # Should show: -rw------- (600 permissions)

  2. Connect to Instance

  # Now SSH should work
  ssh -i ssh-key-2025-07-17.key ubuntu@129.80.196.187

  🔐 Understanding SSH Key Permissions

  Why This Happens

  - SSH requires private keys to be readable only by the owner
  - Downloads folder often has open permissions (644)
  - SSH refuses to use keys that others can read (security feature)

  Permission Codes

  # 600 = Owner: read/write, Group: none, Others: none
  # 644 = Owner: read/write, Group: read, Others: read (TOO OPEN)
  # 400 = Owner: read only, Group: none, Others: none (also works)

  🚀 Alternative Connection Methods

  Method 1: Move Key to Secure Location

  # Create SSH directory if it doesn't exist
  mkdir -p ~/.ssh

  # Move key to SSH directory
  mv ~/Downloads/ssh-key-2025-07-17.key ~/.ssh/

  # Set correct permissions
  chmod 600 ~/.ssh/ssh-key-2025-07-17.key

  # Connect
  ssh -i ~/.ssh/ssh-key-2025-07-17.key ubuntu@129.80.196.187

  Method 2: Add to SSH Agent

  # Fix permissions first
  chmod 600 ~/Downloads/ssh-key-2025-07-17.key

  # Add to SSH agent
  ssh-add ~/Downloads/ssh-key-2025-07-17.key

  # Connect without specifying key
  ssh ubuntu@129.80.196.187

  Method 3: Create SSH Config

  # Create SSH config file
  nano ~/.ssh/config

  # Add this configuration:
  Host oracle-liswmc
      HostName 129.80.196.187
      User ubuntu
      IdentityFile ~/.ssh/ssh-key-2025-07-17.key
      StrictHostKeyChecking no

  # Save and set permissions
  chmod 600 ~/.ssh/config

  # Connect using alias
  ssh oracle-liswmc

  🛠️ Complete Setup Commands

  Run these commands in sequence:

  # 1. Fix key permissions
  chmod 600 ~/Downloads/ssh-key-2025-07-17.key

  # 2. Test connection
  ssh -i ~/Downloads/ssh-key-2025-07-17.key ubuntu@129.80.196.187

  # 3. If successful, you should see Ubuntu welcome message

  📋 After Successful Connection

  Once you're connected to your Oracle Cloud instance, run this deployment script:

  # Update system
  sudo apt update && sudo apt upgrade -y

  # Install Docker
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker ubuntu

  # Install Docker Compose
  sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose

  # Logout and login again for docker group to take effect
  exit

  Then reconnect and continue with deployment:

  # Reconnect
  ssh -i ~/Downloads/ssh-key-2025-07-17.key ubuntu@129.80.196.187

  # Verify Docker works
  docker --version
  docker-compose --version

  # Clone your project (you'll need to upload your code first)
  git clone <your-repo-url>
  # Or create the files manually

  🔍 Troubleshooting Other SSH Issues

  If Still Getting Permission Denied

  # Check if key is correct format
  head -1 ~/Downloads/ssh-key-2025-07-17.key
  # Should start with: -----BEGIN OPENSSH PRIVATE KEY-----
  # or: -----BEGIN RSA PRIVATE KEY-----

  # Try verbose connection for debugging
  ssh -vvv -i ~/Downloads/ssh-key-2025-07-17.key ubuntu@129.80.196.187

  If Key Format is Wrong

  # Convert if needed (if you have .ppk file)
  # Install putty-tools
  sudo apt install putty-tools

  # Convert .ppk to OpenSSH format
  puttygen ssh-key-2025-07-17.ppk -O private-openssh -o ssh-key-2025-07-17.key

  🌐 Once Connected Successfully

  Your Oracle Cloud instance IP is: 129.80.196.187

  After deploying the platform, you'll access it at:
  - Main Portal: http://129.80.196.187:80
  - Analytics: http://129.80.196.187:5007
  - Zoning: http://129.80.196.187:5001
  - Data Management: http://129.80.196.187:5002

  Try the permission fix and let me know if you can connect successfully!



    Step 1: Stop All Running Containers

  # Stop all running containers
  docker stop $(docker ps -aq)

  Step 2: Remove All Containers

  # Now remove all containers
  docker rm $(docker ps -aq)

  Alternative: Force Remove (if needed)

  If stopping doesn't work, you can force remove:
  # Force remove all containers (stops and removes in one command)
  docker rm -f $(docker ps -aq)

  Step 3: Clean Up Networks and Volumes

  # Remove networks
  docker network rm liswmc_liswmc_network || true
  docker network rm liswmc_network || true

  # Clean up volumes
  docker volume prune -f
  docker network prune -f

  Step 4: Start Fresh

  # Navigate to project directory
  cd lusaka-intergrated-solid-waste-management-company

  # Start production containers
  docker-compose -f docker-compose.prod.yml up -d

  # Check status
  docker-compose -f docker-compose.prod.yml ps

  # View logs
  docker-compose -f docker-compose.prod.yml logs -f