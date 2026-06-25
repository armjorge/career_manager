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
