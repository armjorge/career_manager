from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from psycopg2.extras import RealDictCursor

from backend.app.auth import get_current_user_id
from backend.app.database import db_cursor, schema
from backend.app.schemas import (
    AttachmentDownloadOut,
    AttachmentOut,
    AttachmentTypeLiteral,
    CoverLetterOut,
    CoverLetterRow,
    CoverLetterUpdate,
    DownloadUrlOut,
    FileTemplateOut,
    FileTemplateUpdate,
    GenerateDocumentOut,
    GenerateDocumentRequest,
    GenerationLogOut,
    GenerationOptionOut,
    ResumeDetailsOut,
    ResumeDetailsRow,
    ResumeDetailsUpdate,
)
from backend.app.services.document_generation import (
    format_date_issued,
    populate_document,
    propose_output_filename,
    unique_output_filename,
)
from backend.app.services.s3_storage import (
    attachment_object_key,
    generated_object_key,
    get_document_storage,
    md5_hex,
    template_object_key,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _ensure_application_owned(cur: RealDictCursor, user_id: UUID, application_id: int) -> None:
    cur.execute(
        f"SELECT 1 FROM {schema()}.fact_application WHERE user_id = %s AND application_id = %s",
        (str(user_id), application_id),
    )
    if cur.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Application not found", "code": "NOT_FOUND"},
        )


def _ensure_file_owned(cur: RealDictCursor, user_id: UUID, file_id: int | None) -> None:
    if file_id is None:
        return
    cur.execute(
        f"""
        SELECT 1 FROM {schema()}.dim_file
        WHERE user_id = %s AND file_id = %s AND active_status = TRUE
        """,
        (str(user_id), file_id),
    )
    if cur.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Template not found or inactive", "code": "NOT_FOUND"},
        )


def _ensure_lang_owned(cur: RealDictCursor, user_id: UUID, lang_id: int | None) -> None:
    if lang_id is None:
        return
    cur.execute(
        f"SELECT 1 FROM {schema()}.dim_language WHERE user_id = %s AND lang_id = %s",
        (str(user_id), lang_id),
    )
    if cur.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Language not found for this user", "code": "NOT_FOUND"},
        )


def _infer_file_type(file_name: str) -> str:
    return "cover letter" if "cover" in file_name.lower() else "cv"


@router.get("/resumes", response_model=list[ResumeDetailsRow])
def list_resume_details(user_id: UUID = Depends(get_current_user_id)) -> list[ResumeDetailsRow]:
    s = schema()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                dc.company_name,
                fa.job_name,
                dl.language,
                fa.status,
                djc.category_name,
                drd.ed1, drd.ed2, drd.ed3,
                drd.ex1, drd.ex2, drd.ex3,
                drd.skills, drd.interests,
                dimf.file_name,
                fa.application_id,
                drd.file_id,
                fa.created_at
            FROM {s}.fact_application fa
            JOIN {s}.dim_tracker dt
                ON dt.application_id = fa.application_id AND dt.user_id = fa.user_id
            JOIN {s}.dim_company dc
                ON dc.company_id = fa.company_id AND dc.user_id = fa.user_id
            LEFT JOIN {s}.dim_language dl
                ON dl.lang_id = fa.lang_id AND dl.user_id = fa.user_id
            LEFT JOIN {s}.dim_job_category djc
                ON djc.job_cat_id = fa.job_cat_id AND djc.user_id = fa.user_id
            JOIN {s}.dim_resume_details drd
                ON drd.application_id = fa.application_id AND drd.user_id = fa.user_id
            LEFT JOIN {s}.dim_file dimf
                ON dimf.file_id = drd.file_id AND dimf.user_id = fa.user_id
            WHERE fa.user_id = %s
            ORDER BY fa.created_at DESC
            """,
            (str(user_id),),
        )
        return [ResumeDetailsRow.model_validate(row) for row in cur.fetchall()]


@router.get("/resumes/{application_id}", response_model=ResumeDetailsOut)
def get_resume_details(
    application_id: int,
    user_id: UUID = Depends(get_current_user_id),
) -> ResumeDetailsOut:
    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)
        cur.execute(
            f"""
            SELECT application_id, ed1, ed2, ed3, ex1, ex2, ex3, skills, interests, file_id
            FROM {schema()}.dim_resume_details
            WHERE user_id = %s AND application_id = %s
            """,
            (str(user_id), application_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Resume details not found", "code": "NOT_FOUND"},
            )
        return ResumeDetailsOut.model_validate(row)


@router.patch("/resumes/{application_id}", response_model=ResumeDetailsOut)
def update_resume_details(
    application_id: int,
    payload: ResumeDetailsUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> ResumeDetailsOut:
    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)
        _ensure_file_owned(cur, user_id, payload.file_id)

        cur.execute(
            f"""
            UPDATE {schema()}.dim_resume_details
            SET ed1 = %s, ed2 = %s, ed3 = %s,
                ex1 = %s, ex2 = %s, ex3 = %s,
                skills = %s, interests = %s, file_id = %s
            WHERE user_id = %s AND application_id = %s
            RETURNING application_id, ed1, ed2, ed3, ex1, ex2, ex3, skills, interests, file_id
            """,
            (
                _optional_text(payload.ed1),
                _optional_text(payload.ed2),
                _optional_text(payload.ed3),
                _optional_text(payload.ex1),
                _optional_text(payload.ex2),
                _optional_text(payload.ex3),
                _optional_text(payload.skills),
                _optional_text(payload.interests),
                payload.file_id,
                str(user_id),
                application_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Resume details not found", "code": "NOT_FOUND"},
            )
        return ResumeDetailsOut.model_validate(row)


@router.get("/cover-letters", response_model=list[CoverLetterRow])
def list_cover_letters(user_id: UUID = Depends(get_current_user_id)) -> list[CoverLetterRow]:
    s = schema()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                dc.company_name,
                fa.job_name,
                dl.language,
                fa.status,
                djc.category_name,
                dcletter.header,
                dcletter.body,
                dcletter.close,
                dimf.file_name,
                fa.application_id,
                dcletter.file_id,
                fa.created_at
            FROM {s}.fact_application fa
            JOIN {s}.dim_tracker dt
                ON dt.application_id = fa.application_id AND dt.user_id = fa.user_id
            JOIN {s}.dim_company dc
                ON dc.company_id = fa.company_id AND dc.user_id = fa.user_id
            LEFT JOIN {s}.dim_language dl
                ON dl.lang_id = fa.lang_id AND dl.user_id = fa.user_id
            LEFT JOIN {s}.dim_job_category djc
                ON djc.job_cat_id = fa.job_cat_id AND djc.user_id = fa.user_id
            JOIN {s}.dim_cover_letter dcletter
                ON dcletter.application_id = fa.application_id AND dcletter.user_id = fa.user_id
            LEFT JOIN {s}.dim_file dimf
                ON dimf.file_id = dcletter.file_id AND dimf.user_id = fa.user_id
            WHERE fa.user_id = %s
            ORDER BY fa.created_at DESC
            """,
            (str(user_id),),
        )
        return [CoverLetterRow.model_validate(row) for row in cur.fetchall()]


@router.get("/cover-letters/{application_id}", response_model=CoverLetterOut)
def get_cover_letter(
    application_id: int,
    user_id: UUID = Depends(get_current_user_id),
) -> CoverLetterOut:
    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)
        cur.execute(
            f"""
            SELECT application_id, header, body, close, file_id
            FROM {schema()}.dim_cover_letter
            WHERE user_id = %s AND application_id = %s
            """,
            (str(user_id), application_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Cover letter not found", "code": "NOT_FOUND"},
            )
        return CoverLetterOut.model_validate(row)


@router.patch("/cover-letters/{application_id}", response_model=CoverLetterOut)
def update_cover_letter(
    application_id: int,
    payload: CoverLetterUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> CoverLetterOut:
    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)
        _ensure_file_owned(cur, user_id, payload.file_id)

        cur.execute(
            f"""
            UPDATE {schema()}.dim_cover_letter
            SET header = %s, body = %s, close = %s, file_id = %s
            WHERE user_id = %s AND application_id = %s
            RETURNING application_id, header, body, close, file_id
            """,
            (
                _optional_text(payload.header),
                _optional_text(payload.body),
                _optional_text(payload.close),
                payload.file_id,
                str(user_id),
                application_id,
            ),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Cover letter not found", "code": "NOT_FOUND"},
            )
        return CoverLetterOut.model_validate(row)


@router.get("/templates", response_model=list[FileTemplateOut])
def list_templates(user_id: UUID = Depends(get_current_user_id)) -> list[FileTemplateOut]:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                f.file_id, f.file_name, f.file_hash, f.file_type,
                f.lang_id, l.language, f.active_status, f.created_at
            FROM {schema()}.dim_file f
            LEFT JOIN {schema()}.dim_language l
                ON l.lang_id = f.lang_id AND l.user_id = f.user_id
            WHERE f.user_id = %s AND f.active_status = TRUE
            ORDER BY f.file_name ASC
            """,
            (str(user_id),),
        )
        return [FileTemplateOut.model_validate(row) for row in cur.fetchall()]


@router.post("/templates/upload", response_model=FileTemplateOut, status_code=status.HTTP_201_CREATED)
async def upload_template(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
) -> FileTemplateOut:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Only .docx templates are supported", "code": "INVALID_FILE"},
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Uploaded file is empty", "code": "INVALID_FILE"},
        )

    file_name = file.filename.rsplit("/", 1)[-1]
    if file_name.startswith("~"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid template file name", "code": "INVALID_FILE"},
        )

    file_hash = md5_hex(content)
    file_type = _infer_file_type(file_name)
    storage = get_document_storage()

    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT file_id, file_name, active_status
            FROM {schema()}.dim_file
            WHERE user_id = %s AND file_hash = %s
            """,
            (str(user_id), file_hash),
        )
        existing = cur.fetchone()

        storage.upload_template(user_id, file_name, content)

        if existing:
            cur.execute(
                f"""
                UPDATE {schema()}.dim_file
                SET file_name = %s, file_type = %s, active_status = TRUE
                WHERE user_id = %s AND file_id = %s
                RETURNING file_id, file_name, file_hash, file_type, lang_id, active_status, created_at
                """,
                (file_name, file_type, str(user_id), existing["file_id"]),
            )
        else:
            cur.execute(
                f"""
                INSERT INTO {schema()}.dim_file
                    (user_id, file_name, file_hash, file_type, active_status)
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING file_id, file_name, file_hash, file_type, lang_id, active_status, created_at
                """,
                (str(user_id), file_name, file_hash, file_type),
            )

        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail={"message": "Failed to save template"})
        return FileTemplateOut.model_validate({**row, "language": None})


@router.patch("/templates/{file_id}", response_model=FileTemplateOut)
def update_template(
    file_id: int,
    payload: FileTemplateUpdate,
    user_id: UUID = Depends(get_current_user_id),
) -> FileTemplateOut:
    with db_cursor() as cur:
        _ensure_lang_owned(cur, user_id, payload.lang_id)

        cur.execute(
            f"""
            UPDATE {schema()}.dim_file
            SET file_type = COALESCE(%s, file_type),
                lang_id = %s
            WHERE user_id = %s AND file_id = %s AND active_status = TRUE
            RETURNING file_id, file_name, file_hash, file_type, lang_id, active_status, created_at
            """,
            (payload.file_type, payload.lang_id, str(user_id), file_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Template not found", "code": "NOT_FOUND"},
            )

        language = None
        if row["lang_id"]:
            cur.execute(
                f'SELECT language FROM {schema()}.dim_language WHERE user_id = %s AND lang_id = %s',
                (str(user_id), row["lang_id"]),
            )
            lang_row = cur.fetchone()
            language = lang_row["language"] if lang_row else None

        return FileTemplateOut.model_validate({**row, "language": language})


@router.delete("/templates/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_template(file_id: int, user_id: UUID = Depends(get_current_user_id)) -> None:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT file_name FROM {schema()}.dim_file
            WHERE user_id = %s AND file_id = %s AND active_status = TRUE
            """,
            (str(user_id), file_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Template not found", "code": "NOT_FOUND"},
            )

        cur.execute(
            f"""
            UPDATE {schema()}.dim_file
            SET active_status = FALSE
            WHERE user_id = %s AND file_id = %s
            """,
            (str(user_id), file_id),
        )

    get_document_storage().delete_template(user_id, row["file_name"])


@router.get("/generation-options", response_model=list[GenerationOptionOut])
def list_generation_options(user_id: UUID = Depends(get_current_user_id)) -> list[GenerationOptionOut]:
    s = schema()
    with db_cursor() as cur:
        cur.execute(
            f"""
            WITH base_query AS (
                SELECT
                    fact_app.application_id,
                    'Resume'::text AS category,
                    dc.company_name,
                    fact_app.job_name,
                    dl.language,
                    fact_app.status,
                    djc.category_name,
                    dimf.file_name,
                    dimf.file_hash,
                    dimf.active_status,
                    dimf.file_type,
                    fact_app.created_at
                FROM {s}.fact_application fact_app
                JOIN {s}.dim_company dc
                    ON dc.company_id = fact_app.company_id AND dc.user_id = fact_app.user_id
                LEFT JOIN {s}.dim_language dl
                    ON dl.lang_id = fact_app.lang_id AND dl.user_id = fact_app.user_id
                LEFT JOIN {s}.dim_job_category djc
                    ON djc.job_cat_id = fact_app.job_cat_id AND djc.user_id = fact_app.user_id
                JOIN {s}.dim_resume_details drd
                    ON drd.application_id = fact_app.application_id AND drd.user_id = fact_app.user_id
                LEFT JOIN {s}.dim_file dimf
                    ON dimf.file_id = drd.file_id AND dimf.user_id = fact_app.user_id

                UNION ALL

                SELECT
                    fact_app.application_id,
                    'Cover Letter'::text AS category,
                    dc.company_name,
                    fact_app.job_name,
                    dl.language,
                    fact_app.status,
                    djc.category_name,
                    dimf.file_name,
                    dimf.file_hash,
                    dimf.active_status,
                    dimf.file_type,
                    fact_app.created_at
                FROM {s}.fact_application fact_app
                JOIN {s}.dim_company dc
                    ON dc.company_id = fact_app.company_id AND dc.user_id = fact_app.user_id
                LEFT JOIN {s}.dim_language dl
                    ON dl.lang_id = fact_app.lang_id AND dl.user_id = fact_app.user_id
                LEFT JOIN {s}.dim_job_category djc
                    ON djc.job_cat_id = fact_app.job_cat_id AND djc.user_id = fact_app.user_id
                JOIN {s}.dim_cover_letter dcletter
                    ON dcletter.application_id = fact_app.application_id AND dcletter.user_id = fact_app.user_id
                LEFT JOIN {s}.dim_file dimf
                    ON dimf.file_id = dcletter.file_id AND dimf.user_id = fact_app.user_id
            )
            SELECT *
            FROM base_query
            WHERE active_status = TRUE
              AND file_hash IS NOT NULL
              AND application_id IN (
                  SELECT application_id FROM {s}.fact_application WHERE user_id = %s
              )
            ORDER BY created_at DESC
            """,
            (str(user_id),),
        )
        return [GenerationOptionOut.model_validate(row) for row in cur.fetchall()]


@router.post("/generate", response_model=GenerateDocumentOut)
def generate_document(
    payload: GenerateDocumentRequest,
    user_id: UUID = Depends(get_current_user_id),
) -> GenerateDocumentOut:
    s = schema()
    table = "dim_resume_details" if payload.category == "Resume" else "dim_cover_letter"
    storage = get_document_storage()
    success = False
    output_file = "output_file.docx"
    download_url: str | None = None
    pdf_id = 0
    file_hash = ""
    template_name = ""
    generation_error: str | None = None

    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                t.*,
                fa.job_name AS job,
                fa.created_at AS date,
                dl.language AS lang,
                dc.company_name,
                djc.category_name,
                dimf.file_name,
                dimf.file_hash
            FROM {s}.{table} t
            JOIN {s}.fact_application fa
                ON fa.application_id = t.application_id AND fa.user_id = t.user_id
            JOIN {s}.dim_company dc
                ON dc.company_id = fa.company_id AND dc.user_id = fa.user_id
            LEFT JOIN {s}.dim_language dl
                ON dl.lang_id = fa.lang_id AND dl.user_id = fa.user_id
            LEFT JOIN {s}.dim_job_category djc
                ON djc.job_cat_id = fa.job_cat_id AND djc.user_id = fa.user_id
            LEFT JOIN {s}.dim_file dimf
                ON dimf.file_id = t.file_id AND dimf.user_id = fa.user_id
            WHERE t.user_id = %s
              AND t.application_id = %s
              AND dimf.active_status = TRUE
            """,
            (str(user_id), payload.application_id),
        )
        details = cur.fetchone()
        if details is None or not details.get("file_name"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Application has no active template linked",
                    "code": "NO_TEMPLATE",
                },
            )

        template_name = details["file_name"]
        file_hash = details["file_hash"]
        row_data = dict(details)

        if payload.category == "Cover Letter":
            row_data["date_issued"] = format_date_issued(details.get("lang"), details.get("date"))

        base_name = propose_output_filename(
            _optional_text(payload.prefix),
            details["company_name"],
            details.get("category_name"),
            payload.category,
        )
        existing_names = storage.list_generated_names(user_id)
        output_file = unique_output_filename(base_name, existing_names)

        try:
            template_bytes = storage.download(template_object_key(user_id, template_name))
            generated_bytes = populate_document(template_bytes, row_data)
            storage.upload_generated(user_id, output_file, generated_bytes)
            download_url = storage.presigned_download_url(
                generated_object_key(user_id, output_file),
                output_file,
            )
            success = True
        except Exception as exc:
            generation_error = str(exc)

        cur.execute(
            f"""
            INSERT INTO {s}.fact_pdf_generator
                (user_id, application_id, file_hash, file_name, output_file, pdf_success, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING pdf_id
            """,
            (
                str(user_id),
                payload.application_id,
                file_hash,
                template_name,
                output_file,
                success,
                datetime.now(),
            ),
        )
        pdf_row = cur.fetchone()
        pdf_id = pdf_row["pdf_id"] if pdf_row else 0

    if generation_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Document generation failed: {generation_error}", "code": "GENERATION_FAILED"},
        )

    return GenerateDocumentOut(
        pdf_id=pdf_id,
        output_file=output_file,
        pdf_success=success,
        download_url=download_url,
    )


@router.get("/generations", response_model=list[GenerationLogOut])
def list_generations(
    limit: int = 50,
    user_id: UUID = Depends(get_current_user_id),
) -> list[GenerationLogOut]:
    safe_limit = max(1, min(limit, 200))
    s = schema()
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                fpg.pdf_id,
                fpg.application_id,
                fpg.file_hash,
                fpg.file_name,
                fpg.output_file,
                fpg.pdf_success,
                fpg.created_at,
                dc.company_name,
                fa.job_name
            FROM {s}.fact_pdf_generator fpg
            LEFT JOIN {s}.fact_application fa
                ON fa.application_id = fpg.application_id AND fa.user_id = fpg.user_id
            LEFT JOIN {s}.dim_company dc
                ON dc.company_id = fa.company_id AND dc.user_id = fpg.user_id
            WHERE fpg.user_id = %s
            ORDER BY fpg.created_at DESC
            LIMIT %s
            """,
            (str(user_id), safe_limit),
        )
        return [GenerationLogOut.model_validate(row) for row in cur.fetchall()]


@router.delete("/generations/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generation(
    pdf_id: int,
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT output_file, pdf_success
            FROM {schema()}.fact_pdf_generator
            WHERE user_id = %s AND pdf_id = %s
            """,
            (str(user_id), pdf_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Generation record not found", "code": "NOT_FOUND"},
            )

        cur.execute(
            f"DELETE FROM {schema()}.fact_pdf_generator WHERE user_id = %s AND pdf_id = %s",
            (str(user_id), pdf_id),
        )

    if row["pdf_success"]:
        storage = get_document_storage()
        try:
            storage.client.delete_object(
                Bucket=storage.bucket,
                Key=generated_object_key(user_id, row["output_file"]),
            )
        except Exception:
            pass


@router.get("/generations/{pdf_id}/download", response_model=DownloadUrlOut)
def download_generation(
    pdf_id: int,
    user_id: UUID = Depends(get_current_user_id),
) -> DownloadUrlOut:
    with db_cursor() as cur:
        cur.execute(
            f"""
            SELECT output_file, pdf_success
            FROM {schema()}.fact_pdf_generator
            WHERE user_id = %s AND pdf_id = %s
            """,
            (str(user_id), pdf_id),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Generation record not found", "code": "NOT_FOUND"},
            )
        if not row["pdf_success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Document generation failed for this record", "code": "NOT_AVAILABLE"},
            )

    storage = get_document_storage()
    output_file = row["output_file"]
    url = storage.presigned_download_url(
        generated_object_key(user_id, output_file),
        output_file,
    )
    return DownloadUrlOut(download_url=url, file_name=output_file)


# ---------------------------------------------------------------------------
# Application Attachments (job description, CV submitted, cover letter submitted)
# ---------------------------------------------------------------------------

_VALID_ATTACHMENT_TYPES: set[str] = {"job_description", "resume_submitted", "cover_letter_submitted"}


def _validate_attachment_type(attachment_type: str) -> AttachmentTypeLiteral:
    if attachment_type not in _VALID_ATTACHMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": f"Invalid attachment type: {attachment_type}", "code": "INVALID_TYPE"},
        )
    return attachment_type  # type: ignore[return-value]


@router.get("/attachments/{application_id}", response_model=list[AttachmentOut])
def list_attachments(
    application_id: int,
    user_id: UUID = Depends(get_current_user_id),
) -> list[AttachmentOut]:
    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)
        cur.execute(
            f"""
            SELECT
                attachment_id, application_id, attachment_type,
                s3_key, file_name, file_hash, file_size_bytes,
                uploaded_at, load_date::text AS load_date, created_at
            FROM {schema()}.dim_attachment
            WHERE user_id = %s AND application_id = %s
            ORDER BY attachment_type
            """,
            (str(user_id), application_id),
        )
        return [AttachmentOut.model_validate(row) for row in cur.fetchall()]


@router.post(
    "/attachments/{application_id}/{attachment_type}/upload",
    response_model=AttachmentOut,
)
async def upload_attachment(
    application_id: int,
    attachment_type: str,
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id),
) -> AttachmentOut:
    atype = _validate_attachment_type(attachment_type)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Only PDF files are accepted", "code": "INVALID_FILE"},
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Uploaded file is empty", "code": "INVALID_FILE"},
        )

    file_hash = md5_hex(content)
    file_size = len(content)
    original_name = file.filename.rsplit("/", 1)[-1]
    storage = get_document_storage()

    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)

        s3_key = storage.upload_attachment(user_id, application_id, atype, content)

        cur.execute(
            f"""
            INSERT INTO {schema()}.dim_attachment
                (application_id, user_id, attachment_type, s3_key, file_name, file_hash,
                 file_size_bytes, uploaded_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (application_id, attachment_type) DO UPDATE
                SET s3_key          = EXCLUDED.s3_key,
                    file_name       = EXCLUDED.file_name,
                    file_hash       = EXCLUDED.file_hash,
                    file_size_bytes = EXCLUDED.file_size_bytes,
                    uploaded_at     = NOW()
            RETURNING
                attachment_id, application_id, attachment_type,
                s3_key, file_name, file_hash, file_size_bytes,
                uploaded_at, load_date::text AS load_date, created_at
            """,
            (application_id, str(user_id), atype, s3_key, original_name, file_hash, file_size),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail={"message": "Failed to save attachment"})
        return AttachmentOut.model_validate(row)


@router.delete(
    "/attachments/{application_id}/{attachment_type}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachment(
    application_id: int,
    attachment_type: str,
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    atype = _validate_attachment_type(attachment_type)

    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)

        cur.execute(
            f"""
            SELECT s3_key FROM {schema()}.dim_attachment
            WHERE user_id = %s AND application_id = %s AND attachment_type = %s
            """,
            (str(user_id), application_id, atype),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Attachment not found", "code": "NOT_FOUND"},
            )

        cur.execute(
            f"""
            UPDATE {schema()}.dim_attachment
            SET s3_key = NULL, file_name = NULL, file_hash = NULL,
                file_size_bytes = NULL, uploaded_at = NULL
            WHERE user_id = %s AND application_id = %s AND attachment_type = %s
            """,
            (str(user_id), application_id, atype),
        )

    if row["s3_key"]:
        storage = get_document_storage()
        try:
            storage.client.delete_object(Bucket=storage.bucket, Key=row["s3_key"])
        except Exception:
            pass


@router.get(
    "/attachments/{application_id}/{attachment_type}/download",
    response_model=AttachmentDownloadOut,
)
def download_attachment(
    application_id: int,
    attachment_type: str,
    user_id: UUID = Depends(get_current_user_id),
) -> AttachmentDownloadOut:
    atype = _validate_attachment_type(attachment_type)

    with db_cursor() as cur:
        _ensure_application_owned(cur, user_id, application_id)

        cur.execute(
            f"""
            SELECT s3_key, file_name FROM {schema()}.dim_attachment
            WHERE user_id = %s AND application_id = %s AND attachment_type = %s
            """,
            (str(user_id), application_id, atype),
        )
        row = cur.fetchone()

    if row is None or not row["s3_key"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No file uploaded for this attachment", "code": "NOT_FOUND"},
        )

    storage = get_document_storage()
    display_name = row["file_name"] or f"{atype}.pdf"
    url = storage.presigned_download_url(row["s3_key"], display_name)
    return AttachmentDownloadOut(download_url=url, file_name=display_name)
