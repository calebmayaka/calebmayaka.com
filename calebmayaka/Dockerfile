# Production image for calebmayaka.com (built by deploy/vps/bin/deploy.sh on the VPS).
# Data lives outside the image: PostgreSQL in the shared "postgres" container, plus mounted folders
#   /app/media         CMS uploads
#   /app/staticfiles   collected static files (served directly by Caddy)
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# uid 1001 matches the "caleb" user on the VPS, so the mounted folders stay writable.
RUN useradd -u 1001 -m app && mkdir -p /app/media /app/staticfiles && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput --verbosity 0 && exec gunicorn calebmayaka.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile - --error-logfile -"]
