import multiprocessing
import os

# Dynamic worker sizing tuned for ML-heavy workloads.
cores = multiprocessing.cpu_count()
workers_per_core = float(os.getenv("WORKERS_PER_CORE", "1"))
max_default_workers = int(os.getenv("MAX_DEFAULT_WORKERS", "4"))
default_web_concurrency = max(1, min(max_default_workers, int(cores * workers_per_core)))

# Allow override via environment variable
web_concurrency = int(os.getenv("WEB_CONCURRENCY", default_web_concurrency))

# Gunicorn config
workers = web_concurrency
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"

# Performance & Reliability
keepalive = int(os.getenv("GUNICORN_KEEP_ALIVE", 5))
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
max_requests = int(os.getenv("MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", 100))

# Logging
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-" # stdout
errorlog = "-"  # stderr
