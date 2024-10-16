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
    - [First install of the certificates](#first-install-of-the-certificates)
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
- [Nessus Processes](#nessus-processes)
  - [1. Nessus Plugin Converter Process](#1-nessus-plugin-converter-process)
    - [Overview](#overview-1)
    - [Prerequisites](#prerequisites)
    - [Usage](#usage)
  - [2. Nessus Signature Upload Process](#2-nessus-signature-upload-process)
    - [Overview](#overview-2)
    - [Prerequisites](#prerequisites-1)
    - [Import Command](#import-command)
    - [Usage](#usage-1)
  - [3. Nessus Scan Parser Process (convert from .nessus to .json)](#3-nessus-scan-parser-process-convert-from-nessus-to-json)
    - [Overview](#overview-3)
    - [Prerequisites](#prerequisites-2)
    - [Usage](#usage-2)

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
### First install of the certificates

1. First disable the https portion of the nginx config
2. Run this script in the Docker hosting server
   ```
   docker compose run --rm certbot certonly --manual --preferred-challenges=dns   --email itops@securitygroupcr.com --agree-tos --no-eff-email   -d *.securitygroupcr.com
   ```
3. You will receive a DNS TXT entry, similar to the one below, configure it on the DNS provider
   ```
   Before continuing, verify the TXT record has been deployed. Depending on the DNS provider, this may take some time, from a few seconds to multiple minutes. You can check if it has finished deploying with aid of online tools, such as the Google
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   Press Enter to Continue
   ```
4. Back to the Docker host, Wait for about 5 to 10 minutes and then hit enter
5. You can enable the https section of your nginx
Ref: [Deploying a Django Application with Docker, Nginx, and Certbot](https://medium.com/@akshatgadodia/deploying-a-django-application-with-docker-nginx-and-certbot-eaf576463f19)

### Certificate Renewal Script
Create `/root/scgportal/renew_cert.sh`:
```bash
#!/bin/bash
cd /root/scgportal
docker compose run --rm certbot renew --webroot --webroot-path=/var/www/certbot
docker compose exec nginx nginx -s reload
```

Make it executable:
```bash
chmod +x /root/scgportal/renew_cert.sh
```

### Cron Job for Certificate Renewal
Add to crontab (`crontab -e`):
```
0 0 1,15 * * /root/scgportal/renew_cert.sh >> /var/log/certbot_renewal.log 2>&1
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
docker compose logs backend
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


# Nessus Processes

## 1. Nessus Plugin Converter Process

### Overview

### Prerequisites
- Have access to Nessus Server

### Usage
1. Log in to Nessus server and in terminal type this command to extract the `plugins.xml`. Ref [How to export a list of all plugins available in a Nessus scanner](https://community.tenable.com/s/article/How-to-export-a-list-of-all-plugins-available-in-a-Nessus-scanner?language=en_US)
   ```
   sudo /opt/nessus/sbin/nessuscli dump --plugins
   ```
2. Extract the plugin ids from it and save them into `plugin_ids.txt`
   ```
   grep script_id  plugins.xml | sed -E 's/(<script_id>|<\/script_id>)//g' >> plugin_ids.txt
   ```
3. Extract the plugin details to save them into `list_plugins.json` file
   ```
   (echo "["; first=true; for i in $(cat plugin_ids.txt); do if [ "$first" = true ]; then first=false; else echo ","; fi; curl -H "X-ApiKeys: accessKey=<ACCESS_KEY_STRING>; secretKey=<SECRET_KEY_STRING>" -s -k https://<NESSUS_IP>:8834/plugins/plugin/$i | jq .; done; echo "]") > list_plugins.json
   ```
4. Run the `nessus_plugin_converter.py` script to create the signature JSON file `output.json`, make sure the `list_plugins.json` and the `nessus_plugin_converter.py` are in the same folder
   ```
   python nessus_plugin_converter.py
   ```

## 2. Nessus Signature Upload Process

### Overview
This process imports a large JSON file containing the latest signatures from Nessus into the Django application's database. This only has to be ran when there are updates to the Nessus Signature Datbase

### Prerequisites
- Django application with a `signatures` app installed
- Large JSON file with Output data (e.g., `output.json`)

### Import Command
Located in `signatures/management/commands/upload_signatures.py`.

### Usage
1. Upload the cr_padron file to the Docker Host
   ```
   scp -i ~/.ssh/scgportal.key output.json root@165.22.185.21:/root/scgportal/
   ```
2. Copy the output.json to the docker container
   ```
   docker cp output.json scgportal-backend-1:/app/output.json
   ```
3. Ensure the JSON file is in the Django project's root directory.
   ```
   docker exec -it scgportal-backend-1 ls -l /app/output.json
   ```
4. Run the command:
   ```
   docker exec -it scgportal-backend-1 python manage.py upload_signatures  --settings=core.settings.development output.json Nessus --settings=core.settings.production
   ```

## 3. Nessus Scan Parser Process (convert from .nessus to .json)

### Overview
This process converts the scan report from `.nessus` to JSON format, to make it readable by the application, this happens every time we run a scan for a customer.

### Prerequisites
- `.nessus` file with report data (e.g., `10_30_1_0_24_4lu5pv.nessus`)
- `nessus_scan_parser.py` script in the same directory as the `.nessus` file

### Usage
1. Run the script
   ```
   python nessus_scan_parser.py 10_30_1_0_24_4lu5pv.nessus
   ```
2. Grab the resulting file and upload it to the customer in the application's GUI