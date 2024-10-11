# Django Application Deployment Guide

## Table of Contents
- [Django Application Deployment Guide](#django-application-deployment-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Static Files Configuration](#static-files-configuration)
    - [Django Settings](#django-settings)
    - [Docker Compose Configuration](#docker-compose-configuration)
    - [Nginx Configuration](#nginx-configuration)
  - [SSL Certificate Management](#ssl-certificate-management)
    - [Certificate Renewal Script](#certificate-renewal-script)
    - [Cron Job for Certificate Renewal](#cron-job-for-certificate-renewal)
  - [Deployment and Maintenance](#deployment-and-maintenance)
    - [Deploy/Update Application](#deployupdate-application)
    - [Collect Static Files](#collect-static-files)
    - [Reload Nginx](#reload-nginx)
  - [Troubleshooting](#troubleshooting)
    - [Check Static Files](#check-static-files)
    - [View Backend Logs](#view-backend-logs)
    - [View Nginx Logs](#view-nginx-logs)
    - [Debug Steps](#debug-steps)
  - [Notes](#notes)
- [Padron Import Process](#padron-import-process)
  - [Overview](#overview-1)
  - [Prerequisites](#prerequisites)
  - [Model](#model)
  - [Import Command](#import-command)
  - [Usage](#usage)
  - [Process](#process)
  - [Notes](#notes-1)
  - [PadronSearchView](#padronsearchview)
  - [Maintenance](#maintenance)

## Overview
This guide covers the deployment of a Django application using Docker, including static file serving, SSL certificate management, and key maintenance tasks.

## Static Files Configuration

### Django Settings
```python
STATIC_ROOT = '/app/staticfiles'
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    # ... other middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware
]
```

### Docker Compose Configuration
```yaml
services:
  backend:
    # ... other configurations
    volumes:
      - .:/app
      - ./staticfiles:/app/staticfiles
      - /var/certbot/conf:/etc/letsencrypt/:ro
    env_file: .env_prod

  nginx:
    # ... other configurations
    volumes:
      - ./staticfiles:/app/staticfiles
      - ./nginx/conf.d/:/etc/nginx/conf.d/
      - /var/certbot/conf:/etc/letsencrypt:ro

  certbot:
    image: certbot/certbot:latest
    volumes:
      - /var/certbot/conf:/etc/letsencrypt/:rw
      - /var/certbot/www/:/var/www/certbot/:rw
    depends_on:
      - nginx
```

### Nginx Configuration
```nginx
location /static/ {
    alias /app/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
}
```

## SSL Certificate Management

### Certificate Renewal Script
Create `/root/medexp_app/renew_cert.sh`:
```bash
#!/bin/bash
cd /root/medexp_app
docker compose run --rm certbot renew --webroot --webroot-path=/var/www/certbot
docker compose exec nginx nginx -s reload
```

Make it executable:
```bash
chmod +x /root/medexp_app/renew_cert.sh
```

### Cron Job for Certificate Renewal
Add to crontab (`crontab -e`):
```
0 0 1,15 * * /root/medexp_app/renew_cert.sh >> /var/log/certbot_renewal.log 2>&1
```

## Deployment and Maintenance

### Deploy/Update Application
```bash
git pull && docker compose down && docker compose up --build -d
```

### Collect Static Files
```bash
docker compose exec backend python manage.py collectstatic --noinput
```

### Reload Nginx
```bash
docker compose exec nginx nginx -s reload
```

## Troubleshooting

### Check Static Files
Backend container:
```bash
docker compose exec backend ls -l /app/staticfiles
```

Nginx container:
```bash
docker compose exec nginx ls -l /app/staticfiles
```

### View Backend Logs
```bash
docker compose backend nginx
```

### View Nginx Logs
```bash
docker compose logs nginx
```

### Debug Steps
1. Verify static files are collected correctly
2. Ensure Nginx can access static files
3. Check Nginx configuration
4. Inspect browser's Network tab for 404 errors on static files
5. Verify SSL certificate renewal process

## Notes
- Keep Docker Compose file, Nginx configuration, and Django settings consistent
- Regularly backup the database before major updates
- Monitor server resources during high-traffic periods
- Update SSL certificates before expiration (auto-renewal should handle this)

# Padron Import Process

## Overview
This process imports a large JSON file containing Padron (electoral roll) data into the Django application's database. It uses a streaming parser to efficiently handle large files without excessive memory usage.

## Prerequisites
- Django application with a `padron` app installed
- `ijson` library installed (`pip install ijson`)
- Large JSON file with Padron data (e.g., `cr_padron_20240809.json`)

## Model
The `Padron` model in `padron/models.py`:

```python
from django.db import models

class Padron(models.Model):
    id_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    lastname1 = models.CharField(max_length=100)
    lastname2 = models.CharField(max_length=100, blank=True)
    deceased = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['id_number']),
        ]
```

## Import Command
Located in `padron/management/commands/import_padron.py`, this command uses `ijson` to stream-parse the JSON file and bulk insert records into the database.

## Usage
1. Upload the cr_padron file to the Docker Host
   ```
   scp -i ~/.ssh/vgclinic.key cr_padron_XXXXXXXXX.json root@165.22.185.21:/root/medexp_app/
   ```
2. Copy the cr_padron_XXXXXXXXX.json to the docker container
   ```
   docker cp cr_padron_XXXXXXXXX.json medexp_app-backend-1:/app/cr_padron_XXXXXXXXX.json
   ```
3. Ensure the JSON file is in the Django project's root directory.
   ```
   docker exec -it medexp_app-backend-1 ls -l /app/cr_padron_XXXXXXXXX.json
   ```
4. Run the command:
   ```
   docker exec -it medexp_app-backend-1 python manage.py import_padron cr_padron_XXXXXXXXX.json --settings=config.settings.production
   ```

## Process
1. The script opens the JSON file and starts parsing it in chunks.
2. It processes each entry, creating `Padron` objects.
3. Every 5000 entries, it performs a bulk insert into the database.
4. The script provides progress updates every 10000 processed entries.
5. After processing all entries, it reports the total number of records and import duration.

## Notes
- The `deceased` flag is set to `False` for all imported records by default.
- The import uses `ignore_conflicts=True`, skipping entries that conflict with existing records.
- The process is designed to be memory-efficient and can handle large files (400MB+).

## PadronSearchView
This view in `patients/views.py` allows searching the imported Padron data:

```python
class PadronSearchView(View):
    def get(self, request, id_number):
        try:
            padron_entry = Padron.objects.get(id_number=id_number)
            return JsonResponse({
                'found': True,
                'first_name': padron_entry.first_name,
                'lastname1': padron_entry.lastname1,
                'lastname2': padron_entry.lastname2,
            })
        except Padron.DoesNotExist:
            return JsonResponse({
                'found': False,
                'message': 'No se encontró un registro coincidente. Por favor ingrese los datos manualmente.'
            })
```

## Maintenance
- Regularly backup the database before running large imports.
- Monitor server resources during import for any performance issues.
- Consider scheduling regular imports if Padron data is updated frequently.