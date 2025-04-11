## 🐳 Development and Deployment with Docker

### Local Development Environment Setup

Docker and Docker Compose make it easy to configure complex development environments. This project uses Docker Compose to set up the entire stack, including the web server, Celery worker, PostgreSQL, and Redis.

#### Prerequisites

- Install [Docker](https://docs.docker.com/get-docker/)
- Install [Docker Compose](https://docs.docker.com/compose/install/)

#### Running the Development Environment

```bash
# From the project root directory
docker-compose up -d

# Check logs
docker-compose logs -f

# Check logs for a specific service
docker-compose logs -f web
```

#### Accessing the Development Environment

- Django web server: http://localhost:8000
- Database: PostgreSQL (localhost:5432)
- Redis: localhost:6379

#### Running Management Commands

```bash
# Execute Django management commands
docker-compose exec web python manage.py [command]

# Example: Generate migrations
docker-compose exec web python manage.py makemigrations

# Example: Create a superuser
docker-compose exec web python manage.py createsuperuser
```

### On-premises/Server Deployment

#### Production Environment Setup

1. Setting up production environment variables

```bash
# Create .env file
cp src/.env.example src/.env

# Modify the .env file for the production environment
# Be sure to change the following variables:
# - SECRET_KEY: Set to a long random string for security
# - DEBUG: Set to False
# - ALLOWED_HOSTS: Set to your actual domain name
# - DATABASE_URL: Production database connection information
```

2. Optimize docker-compose.yml (optional)

```bash
# Create a production docker-compose file
cp docker-compose.yml docker-compose.prod.yml

# Edit docker-compose.prod.yml:
# - Optimize volume settings
# - Change environment variable DJANGO_SETTINGS_MODULE to conf.settings.production
# - Adjust the number of workers and threads
```

3. Run deployment

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

#### NGINX Proxy Configuration (Recommended)

In a production environment, it's recommended to use NGINX as a front-end to handle static file serving and SSL termination.

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/your/static/files/;
    }
    
    location /media/ {
        alias /path/to/your/media/files/;
    }
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Container Management

#### Basic Commands

```bash
# Start the entire stack
docker-compose up -d

# Stop the entire stack
docker-compose down

# Restart a specific service
docker-compose restart web

# Check container logs
docker-compose logs -f [service_name]

# Access container shell
docker-compose exec [service_name] bash
```

#### Database Backup and Restore

```bash
# PostgreSQL database backup
docker-compose exec db pg_dump -U postgres postgres > backup.sql

# PostgreSQL database restore
cat backup.sql | docker-compose exec -T db psql -U postgres postgres
```

#### Resource Monitoring

```bash
# Check running containers
docker-compose ps

# Check container resource usage
docker stats
```

### Scaling and Performance Optimization

#### Web Application Scaling

```bash
# Adjust the number of web service instances
docker-compose up -d --scale web=3
```

#### Worker Scaling

```bash
# Adjust the number of Celery worker instances
docker-compose up -d --scale worker=5
```

#### Gunicorn Configuration Optimization

To optimize web service performance, adjust Gunicorn settings in Dockerfile or docker-compose.yml:

```
# Number of workers = (2 * CPU cores) + 1
# Number of threads = 2-4
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conf.wsgi:application", "--workers", "5", "--threads", "2"]
```
