from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor

from app.auth import get_current_user_id
from app.database import db_cursor, schema
from app.schemas import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    JobCategoryCreate,
    JobCategoryOut,
    LanguageCreate,
    LanguageOut,
    TrackerOut,
    TrackerUpdate,
)

router = APIRouter(tags=["applications"])


def _application_select() -> str:
    s = schema()
    return f"""
        SELECT
            fa.application_id,
            fa.company_id,
            fa.job_name,
            fa.lang_id,
            fa.status,
            fa.job_cat_id,
            fa.site_id,
            fa.created_at,
            c.company_name,
            l.language,
            jc.category_name,
            fwl.address AS site_address
        FROM {s}.fact_application fa
        JOIN {s}.dim_company c
            ON c.company_id = fa.company_id AND c.user_id = fa.user_id
        LEFT JOIN {s}.dim_language l
            ON l.lang_id = fa.lang_id AND l.user_id = fa.user_id
        LEFT JOIN {s}.dim_job_category jc
            ON jc.job_cat_id = fa.job_cat_id AND jc.user_id = fa.user_id
        LEFT JOIN {s}.fact_web_list fwl
            ON fwl.site_id = fa.site_id AND fwl.user_id = fa.user_id
        WHERE fa.user_id = %s
    """


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _tracker_select() -> str:
    s = schema()
    return f"""
        SELECT
            dt.application_id,
            dt.contact_name,
            dt.contact_email,
            dt.position_url,
            fa.job_name,
            c.company_name,
            l.language,
            fa.status,
            jc.category_name,
            fa.created_at
        FROM {s}.dim_tracker dt
        JOIN {s}.fact_application fa
            ON fa.application_id = dt.application_id AND fa.user_id = dt.user_id
        JOIN {s}.dim_company c
            ON c.company_id = fa.company_id AND c.user_id = fa.user_id
        LEFT JOIN {s}.dim_language l
            ON l.lang_id = fa.lang_id AND l.user_id = fa.user_id
        LEFT JOIN {s}.dim_job_category jc
            ON jc.job_cat_id = fa.job_cat_id AND jc.user_id = fa.user_id
        WHERE fa.user_id = %s
    """


def _row_to_tracker(row: dict) -> TrackerOut:
    return TrackerOut.model_validate(row)


def _row_to_application(row: dict) -> ApplicationOut:
    return ApplicationOut.model_validate(row)


def _ensure_company_owned(cur: RealDictCursor, user_id: UUID, company_id: int) -> None:
    cur.execute(
        f"SELECT 1 FROM {schema()}.dim_company WHERE user_id = %s AND company_id = %s",
        (str(user_id), company_id),
    )
    if cur.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Company not found for this user", "code": "NOT_FOUND"},
        )


def _ensure_site_owned(cur: RealDictCursor, user_id: UUID, site_id: int | None) -> None:
    if site_id is None:
        return
    cur.execute(
        f"SELECT 1 FROM {schema()}.fact_web_list WHERE user_id = %s AND site_id = %s",
        (str(user_id), site_id),
    )
    if cur.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Site not found for this user", "code": "NOT_FOUND"},
        )


def _ensure_optional_fk_owned(
    cur: RealDictCursor,
    user_id: UUID,
    table: str,
    id_column: str,
    value: int | None,
    label: str,
) -> None:
    if value is None:
        return
    cur.execute(
        f"SELECT 1 FROM {schema()}.{table} WHERE user_id = %s AND {id_column} = %s",
        (str(user_id), value),
    )
    if cur.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": f"{label} not found for this user", "code": "NOT_FOUND"},
        )


@router.get("/applications", response_model=list[ApplicationOut])
def list_applications(user_id: UUID = Depends(get_current_user_id)) -> list[ApplicationOut]:
    with db_cursor() as cur:
        cur.execute(f"{_application_select()} ORDER BY fa.created_at DESC", (str(user_id),))
        return [_row_to_application(row) for row in cur.fetchall()]


@router.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> ApplicationOut:
    with db_cursor() as cur:
        _ensure_company_owned(cur, user_id, payload.company_id)
        _ensure_optional_fk_owned(cur, user_id, "dim_language", "lang_id", payload.lang_id, "Language")
        _ensure_optional_fk_owned(
            cur, user_id, "dim_job_category", "job_cat_id", payload.job_cat_id, "Job category"
        )
        _ensure_site_owned(cur, user_id, payload.site_id)

        cur.execute(
            f"""
            INSERT INTO {schema()}.fact_application
                (user_id, company_id, job_name, lang_id, status, job_cat_id, site_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING application_id
            """,
            (
                str(user_id),
                payload.company_id,
                payload.job_name.strip(),
                payload.lang_id,
                payload.status,
                payload.job_cat_id,
                payload.site_id,
            ),
        )
        application_id = cur.fetchone()["application_id"]

        cur.execute(
            f"{_application_select()} AND fa.application_id = %s",
            (str(user_id), application_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail={"message": "Failed to load created application"})
        return _row_to_application(row)


@router.put("/applications/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> ApplicationOut:
    if payload.application_id != application_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Application id mismatch", "code": "INVALID_ID"},
        )

    with db_cursor() as cur:
        cur.execute(
            f"SELECT 1 FROM {schema()}.fact_application WHERE user_id = %s AND application_id = %s",
            (str(user_id), application_id),
        )
        if cur.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Application not found", "code": "NOT_FOUND"},
            )

        _ensure_company_owned(cur, user_id, payload.company_id)
        _ensure_optional_fk_owned(cur, user_id, "dim_language", "lang_id", payload.lang_id, "Language")
        _ensure_optional_fk_owned(
            cur, user_id, "dim_job_category", "job_cat_id", payload.job_cat_id, "Job category"
        )
        _ensure_site_owned(cur, user_id, payload.site_id)

        cur.execute(
            f"""
            UPDATE {schema()}.fact_application
            SET company_id = %s,
                job_name = %s,
                lang_id = %s,
                status = %s,
                job_cat_id = %s,
                site_id = %s
            WHERE user_id = %s AND application_id = %s
            """,
            (
                payload.company_id,
                payload.job_name.strip(),
                payload.lang_id,
                payload.status,
                payload.job_cat_id,
                payload.site_id,
                str(user_id),
                application_id,
            ),
        )

        cur.execute(
            f"{_application_select()} AND fa.application_id = %s",
            (str(user_id), application_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail={"message": "Failed to load updated application"})
        return _row_to_application(row)


@router.get("/job-categories", response_model=list[JobCategoryOut])
def list_job_categories(user_id: UUID = Depends(get_current_user_id)) -> list[JobCategoryOut]:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT job_cat_id, category_name, created_at
            FROM {schema()}.dim_job_category
            WHERE user_id = %s
            ORDER BY category_name
            """,
            (str(user_id),),
        )
        return [JobCategoryOut.model_validate(row) for row in cur.fetchall()]


@router.post("/job-categories", response_model=JobCategoryOut, status_code=status.HTTP_201_CREATED)
def create_job_category(
    payload: JobCategoryCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> JobCategoryOut:
    name = payload.category_name.strip()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT job_cat_id, category_name, created_at
            FROM {schema()}.dim_job_category
            WHERE user_id = %s AND lower(category_name) = lower(%s)
            """,
            (str(user_id), name),
        )
        existing = cur.fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": f"'{name}' already exists.", "code": "DUPLICATE"},
            )

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_job_category (user_id, category_name)
            VALUES (%s, %s)
            RETURNING job_cat_id, category_name, created_at
            """,
            (str(user_id), name),
        )
        return JobCategoryOut.model_validate(cur.fetchone())


@router.post("/job-categories/resolve", response_model=JobCategoryOut)
def resolve_job_category(
    payload: JobCategoryCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> JobCategoryOut:
    name = payload.category_name.strip()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT job_cat_id, category_name, created_at
            FROM {schema()}.dim_job_category
            WHERE user_id = %s AND lower(category_name) = lower(%s)
            """,
            (str(user_id), name),
        )
        existing = cur.fetchone()
        if existing:
            return JobCategoryOut.model_validate(existing)

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_job_category (user_id, category_name)
            VALUES (%s, %s)
            RETURNING job_cat_id, category_name, created_at
            """,
            (str(user_id), name),
        )
        return JobCategoryOut.model_validate(cur.fetchone())


@router.post("/languages/resolve", response_model=LanguageOut)
def resolve_language(
    payload: LanguageCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> LanguageOut:
    name = payload.language.strip()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT lang_id, language, created_at
            FROM {schema()}.dim_language
            WHERE user_id = %s AND lower(language) = lower(%s)
            """,
            (str(user_id), name),
        )
        existing = cur.fetchone()
        if existing:
            return LanguageOut.model_validate(existing)

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_language (user_id, language)
            VALUES (%s, %s)
            RETURNING lang_id, language, created_at
            """,
            (str(user_id), name),
        )
        return LanguageOut.model_validate(cur.fetchone())


@router.get("/trackers", response_model=list[TrackerOut])
def list_trackers(user_id: UUID = Depends(get_current_user_id)) -> list[TrackerOut]:
    with db_cursor() as cur:
        cur.execute(f"{_tracker_select()} ORDER BY fa.created_at DESC", (str(user_id),))
        return [_row_to_tracker(row) for row in cur.fetchall()]


@router.put("/trackers/{application_id}", response_model=TrackerOut)
def update_tracker(
    application_id: int,
    payload: TrackerUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> TrackerOut:
    with db_cursor() as cur:
        cur.execute(
            f"""
            UPDATE {schema()}.dim_tracker
            SET contact_name = %s,
                contact_email = %s,
                position_url = %s
            WHERE user_id = %s AND application_id = %s
            """,
            (
                _optional_text(payload.contact_name),
                _optional_text(payload.contact_email),
                _optional_text(payload.position_url),
                str(user_id),
                application_id,
            ),
        )
        if cur.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Tracking record not found", "code": "NOT_FOUND"},
            )

        cur.execute(
            f"{_tracker_select()} AND dt.application_id = %s",
            (str(user_id), application_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "Failed to load updated tracking record"},
            )
        return _row_to_tracker(row)
