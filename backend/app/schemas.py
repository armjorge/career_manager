from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        serialize_by_alias=True,
    )


class ErrorDetail(ApiModel):
    message: str
    code: str | None = None


class CompanyTypeOut(ApiModel):
    ctype_id: int
    type_name: str
    created_at: datetime


class CompanyTypeCreate(ApiModel):
    type_name: str = Field(min_length=1)


class LanguageOut(ApiModel):
    lang_id: int
    language: str
    created_at: datetime


class LanguageCreate(ApiModel):
    language: str = Field(min_length=1)


class CompanyOut(ApiModel):
    company_id: int
    company_name: str
    ctype_id: int | None
    industry: str | None = None
    created_at: datetime


class CompanyCreate(ApiModel):
    company_name: str = Field(min_length=1)
    ctype_id: int


class JobCategoryOut(ApiModel):
    job_cat_id: int
    category_name: str
    created_at: datetime


class JobCategoryCreate(ApiModel):
    category_name: str = Field(min_length=1)


class ApplicationOut(ApiModel):
    application_id: int
    company_id: int
    job_name: str
    lang_id: int | None
    status: Literal["open", "closed"]
    job_cat_id: int | None
    created_at: datetime
    company_name: str
    language: str | None = None
    category_name: str | None = None


class ApplicationCreate(ApiModel):
    company_id: int
    job_name: str = Field(min_length=1)
    lang_id: int | None = None
    status: Literal["open", "closed"]
    job_cat_id: int | None = None


class ApplicationUpdate(ApplicationCreate):
    application_id: int


class TrackerOut(ApiModel):
    application_id: int
    contact_name: str | None = None
    contact_email: str | None = None
    position_url: str | None = None
    job_name: str
    company_name: str
    language: str | None = None
    status: Literal["open", "closed"]
    category_name: str | None = None
    created_at: datetime


class TrackerUpdate(ApiModel):
    contact_name: str | None = None
    contact_email: str | None = None
    position_url: str | None = None


class AnalyticsMetrics(ApiModel):
    total_applications: int
    ready_resumes: int
    ready_cover_letters: int
    cv_prep_rate: float


class MonthlyActivity(ApiModel):
    year_month: str
    apps: int
    resumes: int
    cover_letters: int


class LabelCount(ApiModel):
    name: str
    count: int


class AnalyticsSummary(ApiModel):
    metrics: AnalyticsMetrics
    monthly_activity: list[MonthlyActivity]
    status_distribution: list[LabelCount]
    language_distribution: list[LabelCount]
    category_distribution: list[LabelCount]
    industry_distribution: list[LabelCount]


FileTypeLiteral = Literal["cv", "cover letter"]
DocumentCategoryLiteral = Literal["Resume", "Cover Letter"]


class ResumeDetailsOut(ApiModel):
    application_id: int
    ed1: str | None = None
    ed2: str | None = None
    ed3: str | None = None
    ex1: str | None = None
    ex2: str | None = None
    ex3: str | None = None
    skills: str | None = None
    interests: str | None = None
    file_id: int | None = None


class ResumeDetailsUpdate(ApiModel):
    ed1: str | None = None
    ed2: str | None = None
    ed3: str | None = None
    ex1: str | None = None
    ex2: str | None = None
    ex3: str | None = None
    skills: str | None = None
    interests: str | None = None
    file_id: int | None = None


class ResumeDetailsRow(ResumeDetailsOut):
    company_name: str
    job_name: str
    language: str | None = None
    status: Literal["open", "closed"]
    category_name: str | None = None
    file_name: str | None = None
    created_at: datetime


class CoverLetterOut(ApiModel):
    application_id: int
    header: str | None = None
    body: str | None = None
    close: str | None = None
    file_id: int | None = None


class CoverLetterUpdate(ApiModel):
    header: str | None = None
    body: str | None = None
    close: str | None = None
    file_id: int | None = None


class CoverLetterRow(CoverLetterOut):
    company_name: str
    job_name: str
    language: str | None = None
    status: Literal["open", "closed"]
    category_name: str | None = None
    file_name: str | None = None
    created_at: datetime


class FileTemplateOut(ApiModel):
    file_id: int
    file_name: str
    file_hash: str
    file_type: FileTypeLiteral
    lang_id: int | None = None
    language: str | None = None
    active_status: bool
    created_at: datetime


class FileTemplateUpdate(ApiModel):
    file_type: FileTypeLiteral | None = None
    lang_id: int | None = None


class GenerationOptionOut(ApiModel):
    application_id: int
    category: DocumentCategoryLiteral
    company_name: str
    job_name: str
    language: str | None = None
    status: Literal["open", "closed"]
    category_name: str | None = None
    file_name: str | None = None
    file_hash: str | None = None
    file_type: FileTypeLiteral | None = None
    created_at: datetime


class GenerateDocumentRequest(ApiModel):
    application_id: int
    category: DocumentCategoryLiteral
    prefix: str | None = None


class GenerateDocumentOut(ApiModel):
    pdf_id: int
    output_file: str
    pdf_success: bool
    download_url: str | None = None


class GenerationLogOut(ApiModel):
    pdf_id: int
    application_id: int
    file_hash: str
    file_name: str | None = None
    output_file: str
    pdf_success: bool
    created_at: datetime


class DownloadUrlOut(ApiModel):
    download_url: str
    file_name: str
