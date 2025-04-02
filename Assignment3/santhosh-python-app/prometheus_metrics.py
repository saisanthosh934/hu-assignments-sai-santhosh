from prometheus_client import Counter, Histogram, Gauge

# Existing metrics
page_views = Counter(
    'page_views_total',
    'Total number of page views',
    ['page']
)

health_checks = Counter(
    'health_checks_total',
    'Total number of health checks'
)

metrics_requests = Counter(
    'metrics_requests_total',
    'Total number of metrics requests'
)

# New metrics
database_queries = Counter(
    'database_queries_total',
    'Total number of database queries',
    ['query_type']
)

external_api_calls = Counter(
    'external_api_calls_total',
    'Total number of external API calls',
    ['api_name', 'status']
)

response_sizes = Histogram(
    'response_size_bytes',
    'Size of HTTP responses',
    ['endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_name']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_name']
)

# Business specific metrics
orders_processed = Counter(
    'orders_processed_total',
    'Total number of orders processed',
    ['status']
)

revenue_generated = Counter(
    'revenue_generated_total',
    'Total revenue generated',
    ['currency']
)

active_users = Gauge(
    'active_users_count',
    'Current number of active users'
)
