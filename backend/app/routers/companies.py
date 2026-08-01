from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.database import db_cursor, schema
from app.schemas import (
    CompanyCreate,
    CompanyOut,
    CompanyTypeCreate,
    CompanyTypeOut,
    LanguageCreate,
    LanguageOut,
)

router = APIRouter(tags=["companies"])


@router.get("/company-types", response_model=list[CompanyTypeOut])
def list_company_types(user_id: UUID = Depends(get_current_user_id)) -> list[CompanyTypeOut]:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT ctype_id, type_name, created_at
            FROM {schema()}.dim_ctype
            WHERE user_id = %s
            ORDER BY type_name
            """,
            (str(user_id),),
        )
        return [CompanyTypeOut.model_validate(row) for row in cur.fetchall()]


@router.post("/company-types", response_model=CompanyTypeOut, status_code=status.HTTP_201_CREATED)
def create_company_type(
    payload: CompanyTypeCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> CompanyTypeOut:
    name = payload.type_name.strip()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT ctype_id, type_name, created_at
            FROM {schema()}.dim_ctype
            WHERE user_id = %s AND lower(type_name) = lower(%s)
            """,
            (str(user_id), name),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": f"'{name}' already exists.", "code": "DUPLICATE"},
            )

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_ctype (user_id, type_name)
            VALUES (%s, %s)
            RETURNING ctype_id, type_name, created_at
            """,
            (str(user_id), name),
        )
        return CompanyTypeOut.model_validate(cur.fetchone())


@router.get("/languages", response_model=list[LanguageOut])
def list_languages(user_id: UUID = Depends(get_current_user_id)) -> list[LanguageOut]:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT lang_id, language, created_at
            FROM {schema()}.dim_language
            WHERE user_id = %s
            ORDER BY language
            """,
            (str(user_id),),
        )
        return [LanguageOut.model_validate(row) for row in cur.fetchall()]


@router.post("/languages", response_model=LanguageOut, status_code=status.HTTP_201_CREATED)
def create_language(
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
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": f"'{name}' already exists.", "code": "DUPLICATE"},
            )

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_language (user_id, language)
            VALUES (%s, %s)
            RETURNING lang_id, language, created_at
            """,
            (str(user_id), name),
        )
        return LanguageOut.model_validate(cur.fetchone())


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(user_id: UUID = Depends(get_current_user_id)) -> list[CompanyOut]:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                c.company_id,
                c.company_name,
                c.ctype_id,
                t.type_name AS industry,
                c.created_at
            FROM {schema()}.dim_company c
            LEFT JOIN {schema()}.dim_ctype t
                ON t.ctype_id = c.ctype_id AND t.user_id = c.user_id
            WHERE c.user_id = %s
            ORDER BY c.company_name
            """,
            (str(user_id),),
        )
        return [CompanyOut.model_validate(row) for row in cur.fetchall()]


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    user_id: UUID = Depends(get_current_user_id),
) -> CompanyOut:
    name = payload.company_name.strip()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT 1 FROM {schema()}.dim_ctype
            WHERE user_id = %s AND ctype_id = %s
            """,
            (str(user_id), payload.ctype_id),
        )
        if cur.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Company type not found for this user", "code": "NOT_FOUND"},
            )

        cur.execute(
            f"""
            SELECT company_id FROM {schema()}.dim_company
            WHERE user_id = %s AND lower(company_name) = lower(%s)
            """,
            (str(user_id), name),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": f"'{name}' already exists.", "code": "DUPLICATE"},
            )

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_company (user_id, company_name, ctype_id)
            VALUES (%s, %s, %s)
            RETURNING company_id, company_name, ctype_id, created_at
            """,
            (str(user_id), name, payload.ctype_id),
        )
        row = cur.fetchone()

        cur.execute(
            f"SELECT type_name FROM {schema()}.dim_ctype WHERE user_id = %s AND ctype_id = %s",
            (str(user_id), payload.ctype_id),
        )
        type_row = cur.fetchone()
        row["industry"] = type_row["type_name"] if type_row else None
        return CompanyOut.model_validate(row)
