python manage.py collectstatic --noinput
python manage.py migrate --noinput
python -m uvicorn WebGIS.asgi:application --host 0.0.0.0 --port 8000 --workers 3
