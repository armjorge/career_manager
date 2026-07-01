from contextlib import contextmanager
from typing import Iterator

import psycopg2
from fastapi import HTTPException, status
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from backend.app.config import get_settings

_pool: SimpleConnectionPool | None = None


def reset_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def _get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        try:
            _pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=settings.db_postgresql,
                cursor_factory=RealDictCursor,
            )
        except OperationalError as exc:
            reset_pool()
            raise _db_unavailable(exc) from exc
    return _pool


def _db_unavailable(exc: Exception) -> HTTPException:
    message = str(exc).lower()
    if "password authentication failed" in message:
        detail = (
            "Database password rejected. Copy a fresh connection string from "
            "Neon Console and update DB_POSTGRESQL in the project root .env file."
        )
    else:
        detail = "Database connection failed. Verify DB_POSTGRESQL in the project root .env file."

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"message": detail, "code": "DB_UNAVAILABLE"},
    )


def check_db_connection() -> None:
    with db_cursor():
        return


@contextmanager
def db_cursor() -> Iterator[RealDictCursor]:
    try:
        pool = _get_pool()
    except HTTPException:
        raise
    except OperationalError as exc:
        reset_pool()
        raise _db_unavailable(exc) from exc

    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except OperationalError as exc:
        conn.rollback()
        reset_pool()
        raise _db_unavailable(exc) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def schema() -> str:
    return get_settings().db_schema
