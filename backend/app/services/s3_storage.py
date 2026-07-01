from __future__ import annotations

import hashlib
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from backend.app.config import get_settings

AttachmentTypeLiteral = str  # 'job_description' | 'resume_submitted' | 'cover_letter_submitted'


def user_templates_prefix(user_id: UUID) -> str:
    return f"{user_id}/Templates"


def user_generated_prefix(user_id: UUID) -> str:
    return f"{user_id}/Generated_files"


def user_attachments_prefix(user_id: UUID, application_id: int) -> str:
    return f"{user_id}/Attachments/{application_id}"


def template_object_key(user_id: UUID, file_name: str) -> str:
    return f"{user_templates_prefix(user_id)}/{file_name}"


def generated_object_key(user_id: UUID, file_name: str) -> str:
    return f"{user_generated_prefix(user_id)}/{file_name}"


def attachment_object_key(user_id: UUID, application_id: int, attachment_type: AttachmentTypeLiteral) -> str:
    return f"{user_attachments_prefix(user_id, application_id)}/{attachment_type}.pdf"


def md5_hex(content: bytes) -> str:
    hasher = hashlib.md5()
    hasher.update(content)
    return hasher.hexdigest()


class DocumentStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.documents_s3_bucket
        # boto3 reads AWS_REGION from the Lambda runtime environment automatically
        self.client = boto3.client("s3")

    def upload_template(self, user_id: UUID, file_name: str, content: bytes) -> str:
        key = template_object_key(user_id, file_name)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        return key

    def upload_generated(self, user_id: UUID, file_name: str, content: bytes) -> str:
        key = generated_object_key(user_id, file_name)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        return key

    def upload_attachment(
        self,
        user_id: UUID,
        application_id: int,
        attachment_type: AttachmentTypeLiteral,
        content: bytes,
    ) -> str:
        key = attachment_object_key(user_id, application_id, attachment_type)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType="application/pdf",
        )
        return key

    def delete_attachment(
        self,
        user_id: UUID,
        application_id: int,
        attachment_type: AttachmentTypeLiteral,
    ) -> None:
        key = attachment_object_key(user_id, application_id, attachment_type)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError:
            pass

    def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete_template(self, user_id: UUID, file_name: str) -> None:
        key = template_object_key(user_id, file_name)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError:
            pass

    def list_generated_names(self, user_id: UUID) -> set[str]:
        prefix = f"{user_generated_prefix(user_id)}/"
        names: set[str] = set()
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".docx"):
                    names.add(key.rsplit("/", 1)[-1])
        return names

    def presigned_download_url(self, key: str, file_name: str, expires_in: int = 300) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ResponseContentDisposition": f'attachment; filename="{file_name}"',
            },
            ExpiresIn=expires_in,
        )


_storage: DocumentStorage | None = None


def get_document_storage() -> DocumentStorage:
    global _storage
    if _storage is None:
        _storage = DocumentStorage()
    return _storage
