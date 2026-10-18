import logging
import os
import time

import psycopg
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

log = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="devopsPracticum")

REQUESTS = Counter(
    "http_requests_total", "Всего HTTP-запросов", ["method", "path", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Время обработки запроса, секунды",
    ["method", "path"],
)

CREATE_TABLE = (
    "CREATE TABLE IF NOT EXISTS visits (id INT PRIMARY KEY, count BIGINT NOT NULL)"
)
INCREMENT = (
    "INSERT INTO visits (id, count) VALUES (1, 1) "
    "ON CONFLICT (id) DO UPDATE SET count = visits.count + 1 "
    "RETURNING count"
)


def get_conn() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "app"),
        user=os.getenv("DB_USER", "app"),
        password=os.getenv("DB_PASSWORD", ""),
        connect_timeout=3,
    )


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = route.path if route else "unmatched"
        LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, path, str(status)).inc()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
    except psycopg.Error:
        log.exception("База данных недоступна")
        return JSONResponse({"status": "database unavailable"}, status_code=503)
    return {"status": "ready"}


@app.get("/visit")
def visit():
    try:
        with get_conn() as conn:
            conn.execute(CREATE_TABLE)
            row = conn.execute(INCREMENT).fetchone()
    except psycopg.Error:
        log.exception("Не удалось обновить счётчик")
        return JSONResponse({"error": "database unavailable"}, status_code=503)
    return {"visits": row[0]}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
