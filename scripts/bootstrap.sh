#!/bin/bash
set -e  # Exit on error

# 🔧 Configurable values
PG_VER=14
DB_NAME="WebGISdb"
DB_USER="myuser"
DB_PASS="mypassword"
DJANGO_PROJ="WebGIS"
DJANGO_SUPERUSER="admin"
DJANGO_SUPERPASS="adminpass"
DJANGO_SUPEREMAIL="admin@example.com"
PYTHON_VENV=".venv"

echo "Creating .env file..."

cat > .env <<EOF
# Django settings
DEBUG=True
SECRET_KEY=$(openssl rand -hex 32)
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Database settings
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_DB=$DB_NAME
POSTGRES_ENGINE=django.contrib.gis.db.backends.postgis
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Email settings
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
EOF

echo ".env file created."

# Optional: create common folder layout
echo "📁 Creating project structure..."

mkdir -p apps static media logs

echo "Project folders created: apps/, static/, media/, logs/"


echo "🔧 Installing PostgreSQL and PostGIS..."
sudo apt update
sudo apt install -y postgresql-$PG_VER postgresql-$PG_VER-postgis-3

echo "🛠️ Creating PostgreSQL user and database..."
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}'
   ) THEN
      CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}';
   END IF;
END
\$\$;

DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\connect ${DB_NAME}
CREATE EXTENSION IF NOT EXISTS postgis;
EOF
echo "PostgreSQL user and database created."

echo "🔧 Installing Python and pip..."
if [ -z "$VIRTUAL_ENV" ]; then
  echo "🐍 Setting up Python virtual environment..."
  python3 -m venv $PYTHON_VENV
  source $PYTHON_VENV/bin/activate
else
  echo "⚠️ Already in a virtual environment: $VIRTUAL_ENV"
fi

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Applying Django migrations..."
export DJANGO_SETTINGS_MODULE=$DJANGO_PROJ.settings
python manage.py migrate

echo "👤 Creating Django superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER', '$DJANGO_SUPEREMAIL', '$DJANGO_SUPERPASS')
EOF

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ All done! Django project is set up."
