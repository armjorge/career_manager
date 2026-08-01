from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response

from app.auth import get_current_user_id
from app.database import db_cursor, schema
from app.schemas import WebsiteCreate, WebsiteOut

router = APIRouter(prefix="/sites", tags=["sites"])

_SITE_ID_COL_CACHE: dict[str, bool] = {}


def _fact_app_has_site_id(cur) -> bool:  # type: ignore[type-arg]
    """Return True if fact_application.site_id column already exists.

    Cached per schema name so the information_schema query runs at most once
    per Lambda cold start.
    """
    s = schema()
    if s not in _SITE_ID_COL_CACHE:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name   = 'fact_application'
                  AND column_name  = 'site_id'
            )
            """,
            (s,),
        )
        _SITE_ID_COL_CACHE[s] = bool(cur.fetchone()["exists"])
    return _SITE_ID_COL_CACHE[s]


@router.get("", response_model=list[WebsiteOut])
def list_sites(user_id: UUID = Depends(get_current_user_id)) -> list[WebsiteOut]:
    s = schema()
    with db_cursor() as cur:
        if _fact_app_has_site_id(cur):
            cur.execute(
                f"""
                SELECT
                    fwl.site_id,
                    fwl.address,
                    fwl.created_at,
                    fwl.last_modification,
                    COUNT(fa.application_id) AS application_count
                FROM {s}.fact_web_list fwl
                LEFT JOIN {s}.fact_application fa
                    ON fa.site_id = fwl.site_id AND fa.user_id = fwl.user_id
                WHERE fwl.user_id = %s
                GROUP BY fwl.site_id, fwl.address, fwl.created_at, fwl.last_modification
                ORDER BY fwl.created_at DESC
                """,
                (str(user_id),),
            )
        else:
            cur.execute(
                f"""
                SELECT
                    site_id,
                    address,
                    created_at,
                    last_modification,
                    0 AS application_count
                FROM {s}.fact_web_list
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (str(user_id),),
            )
        return [WebsiteOut.model_validate(row) for row in cur.fetchall()]


@router.post("", response_model=WebsiteOut, status_code=status.HTTP_201_CREATED)
def create_site(
    payload: WebsiteCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> WebsiteOut:
    address = payload.address.strip()
    with db_cursor() as cur:
        # uq_fact_web_list_per_user is a unique INDEX (not a named CONSTRAINT),
        # so ON CONFLICT must reference the index expression directly.
        cur.execute(
            f"""
            INSERT INTO {schema()}.fact_web_list (user_id, address)
            VALUES (%s, %s)
            ON CONFLICT (user_id, lower(address)) DO UPDATE
                SET last_modification = CURRENT_TIMESTAMP
            RETURNING site_id, address, created_at, last_modification
            """,
            (str(user_id), address),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail={"message": "Failed to create site"})
        return WebsiteOut.model_validate({**row, "application_count": 0})


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_site(
    site_id: int,
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    with db_cursor() as cur:
        cur.execute(
            f"SELECT 1 FROM {schema()}.fact_web_list WHERE user_id = %s AND site_id = %s",
            (str(user_id), site_id),
        )
        if cur.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Site not found", "code": "NOT_FOUND"},
            )
        cur.execute(
            f"DELETE FROM {schema()}.fact_web_list WHERE user_id = %s AND site_id = %s",
            (str(user_id), site_id),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
