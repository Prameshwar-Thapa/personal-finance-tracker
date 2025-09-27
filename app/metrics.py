from prometheus_client import Counter, Histogram, Gauge, generate_latest
from flask import Response
import time
import functools

# Metrics
REQUEST_COUNT = Counter('flask_http_request_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('flask_http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_USERS = Gauge('finance_active_users_total', 'Number of active users')
TRANSACTION_COUNT = Counter('finance_transactions_total', 'Total transactions', ['type'])

def track_requests(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            response = f(*args, **kwargs)
            status = getattr(response, 'status_code', 200)
            REQUEST_COUNT.labels(method='GET', endpoint=f.__name__, status=status).inc()
            return response
        finally:
            REQUEST_DURATION.labels(method='GET', endpoint=f.__name__).observe(time.time() - start_time)
    return decorated_function

def metrics_endpoint():
    return Response(generate_latest(), mimetype='text/plain')
