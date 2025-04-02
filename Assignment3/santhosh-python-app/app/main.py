from flask import Flask, render_template, Response, jsonify, request
import prometheus_metrics
import logging
import os
import time
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Histogram, Counter, Gauge

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure data directory exists
DATA_DIR = '/app/data'
os.makedirs(DATA_DIR, exist_ok=True)

# Enhanced Metrics Configuration
REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application request latency',
    ['method', 'endpoint', 'http_status']
)

REQUEST_COUNT = Counter(
    'app_request_count_total',
    'Application request count',
    ['method', 'endpoint', 'http_status']
)

ERROR_COUNT = Counter(
    'app_error_count_total',
    'Application error count',
    ['method', 'endpoint', 'http_status']
)

IN_PROGRESS_REQUESTS = Gauge(
    'app_in_progress_requests',
    'Number of requests currently in progress',
    ['method', 'endpoint']
)

APP_VERSION = Gauge(
    'app_version',
    'Application version info',
    ['version', 'build']
)

# Simulate application version info
APP_VERSION.labels(version='1.0.0', build='42').set(1)


def get_visit_count():
    count_file = os.path.join(DATA_DIR, 'visit_count.txt')
    try:
        with open(count_file, 'r') as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0


def increment_visit_count():
    count = get_visit_count() + 1
    count_file = os.path.join(DATA_DIR, 'visit_count.txt')
    with open(count_file, 'w') as f:
        f.write(str(count))
    return count


@app.before_request
def before_request():
    request.start_time = time.time()
    IN_PROGRESS_REQUESTS.labels(
        method=request.method,
        endpoint=request.endpoint
    ).inc()


@app.after_request
def after_request(response):
    # Calculate request time
    resp_time = time.time() - request.start_time

    # Record metrics
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.endpoint,
        http_status=response.status_code
    ).observe(resp_time)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint,
        http_status=response.status_code
    ).inc()

    if response.status_code >= 400:
        ERROR_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint,
            http_status=response.status_code
        ).inc()

    # Decrement in-progress requests
    IN_PROGRESS_REQUESTS.labels(
        method=request.method,
        endpoint=request.endpoint
    ).dec()

    return response


@app.route('/')
def home():
    visit_count = increment_visit_count()
    logger.info(f"Home page accessed - Total visits: {visit_count}")
    prometheus_metrics.page_views.labels(page='home').inc()
    return render_template('index.html', visit_count=visit_count)


@app.route('/health')
def health():
    logger.info("Health check endpoint accessed")
    prometheus_metrics.health_checks.inc()
    return {
        'status': 'healthy',
        'visit_count': get_visit_count(),
        'version': '1.0.0'
    }, 200


@app.route('/api/data')
def get_data():
    # Simulate API endpoint with potential errors
    if 'fail' in request.args:
        ERROR_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint,
            http_status=500
        ).inc()
        return jsonify({'error': 'simulated failure'}), 500

    # Simulate processing time
    time.sleep(0.1 * float(request.args.get('delay', 1)))
    return jsonify({'data': 'sample response'})


@app.route('/metrics')
def metrics():
    prometheus_metrics.metrics_requests.inc()
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


@app.errorhandler(404)
def page_not_found(e):
    ERROR_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint,
        http_status=404
    ).inc()
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    ERROR_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint,
        http_status=500
    ).inc()
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
