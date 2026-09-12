import json
from django.conf import settings
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class R2StorageError(Exception):
    """Raised when an R2 storage operation fails."""


class R2Storage:
    """
    Thin storage abstraction over Cloudflare R2.

    The rest of the application should interact with this class
    instead of directly using boto3.
    """

    def __init__(self) -> None:
        self.endpoint = settings.R2_ENDPOINT
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.region = settings.R2_REGION

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )

    def put_json(self, key: str, data: dict[str, Any]) -> None:
        """Write a JSON document to R2."""

        try:
            body = json.dumps(
                data,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType="application/json",
            )

        except (BotoCoreError, ClientError) as exc:
            raise R2StorageError(
                f"Failed to write object '{key}' to R2"
            ) from exc

    def get_json(self, key: str) -> dict[str, Any] | None:
        """Read a JSON document from R2.

        Returns None when the object does not exist.
        """

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )

            body = response["Body"].read()

            return json.loads(body.decode("utf-8"))

        except self.client.exceptions.NoSuchKey:
            return None

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in {"NoSuchKey", "404"}:
                return None

            raise R2StorageError(
                f"Failed to read object '{key}' from R2"
            ) from exc

        except (BotoCoreError, json.JSONDecodeError) as exc:
            raise R2StorageError(
                f"Failed to decode object '{key}' from R2"
            ) from exc

    def delete(self, key: str) -> None:
        """Delete an object from R2."""

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )

        except (BotoCoreError, ClientError) as exc:
            raise R2StorageError(
                f"Failed to delete object '{key}' from R2"
            ) from exc

    def exists(self, key: str) -> bool:
        """Check whether an object exists in R2."""

        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return False

            raise R2StorageError(
                f"Failed to check object '{key}' in R2"
            ) from exc

        except BotoCoreError as exc:
            raise R2StorageError(
                f"Failed to check object '{key}' in R2"
            ) from exc


    def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Write raw bytes to R2."""

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

        except (BotoCoreError, ClientError) as exc:
            raise R2StorageError(
                f"Failed to write object '{key}' to R2"
            ) from exc

    def get_bytes(self, key: str) -> bytes | None:
        """Read raw bytes from R2.

        Returns None when the object does not exist.
        """

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )

            return response["Body"].read()

        except self.client.exceptions.NoSuchKey:
            return None

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in {"NoSuchKey", "404", "NotFound"}:
                return None

            raise R2StorageError(
                f"Failed to read object '{key}' from R2"
            ) from exc

        except BotoCoreError as exc:
            raise R2StorageError(
                f"Failed to read object '{key}' from R2"
            ) from exc
