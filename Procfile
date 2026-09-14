web: gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080} --worker-tmp-dir /dev/shm
