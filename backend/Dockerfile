FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download the AWS RDS CA certificate bundle
RUN mkdir -p /app/certs && \
    python -c "import urllib.request; urllib.request.urlretrieve('https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem', '/app/certs/rds-global-bundle.pem')"

COPY . .

RUN DJANGO_SECRET_KEY=build-only-placeholder \
    DB_ENGINE=sqlite \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]