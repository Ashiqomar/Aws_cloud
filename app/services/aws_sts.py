"""
AWS STS AssumeRole service.

Provides a reusable function that exchanges a tenant's IAM Role ARN +
External ID for temporary credentials and returns a ready-to-use
``boto3.Session``.
"""

from __future__ import annotations

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Default session duration (seconds) ───────────────────────────
DEFAULT_SESSION_DURATION = 3600  # 1 hour


class STSError(Exception):
    """Raised when STS AssumeRole fails."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


def assume_role(
    role_arn: str,
    external_id: str,
    session_name: str = "FinOpsPlatformSession",
    duration_seconds: int = DEFAULT_SESSION_DURATION,
    region: Optional[str] = None,
) -> boto3.Session:
    """
    Call STS AssumeRole and return a ``boto3.Session`` with temporary creds.

    Parameters
    ----------
    role_arn : str
        The IAM Role ARN to assume (e.g. ``arn:aws:iam::123456789012:role/X``).
    external_id : str
        The external ID configured in the role's trust policy.
    session_name : str
        An identifier for the assumed-role session (shows up in CloudTrail).
    duration_seconds : int
        How long the temporary credentials remain valid (900 – 3600).
    region : str | None
        Override for the AWS region; defaults to ``settings.AWS_DEFAULT_REGION``.

    Returns
    -------
    boto3.Session
        A session configured with the temporary credentials.

    Raises
    ------
    STSError
        On any STS or permissions failure.
    """
    effective_region = region or settings.AWS_DEFAULT_REGION

    try:
        sts_client = boto3.client("sts", region_name=effective_region)

        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            ExternalId=external_id,
            DurationSeconds=duration_seconds,
        )

        credentials = response["Credentials"]
        logger.info(
            "AssumeRole succeeded for %s (expires %s)",
            role_arn,
            credentials["Expiration"],
        )

        return boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=effective_region,
        )

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]

        if error_code == "AccessDenied":
            logger.error("Access denied assuming role %s: %s", role_arn, error_msg)
            raise STSError(
                f"Access denied: unable to assume role {role_arn}. "
                "Verify the trust policy and external ID.",
                code="ACCESS_DENIED",
            ) from exc

        if error_code == "ExpiredTokenException":
            logger.error("Token expired while assuming role %s", role_arn)
            raise STSError(
                "The security token in the request has expired.",
                code="EXPIRED_TOKEN",
            ) from exc

        if error_code == "MalformedPolicyDocument":
            logger.error("Malformed policy for role %s: %s", role_arn, error_msg)
            raise STSError(
                f"Malformed policy on role {role_arn}.",
                code="MALFORMED_POLICY",
            ) from exc

        if error_code == "RegionDisabledException":
            logger.error("Region disabled: %s", error_msg)
            raise STSError(
                f"Region is disabled: {error_msg}",
                code="REGION_DISABLED",
            ) from exc

        # Throttling
        if error_code in ("Throttling", "ThrottlingException", "RequestLimitExceeded"):
            logger.warning("STS throttled for role %s — retry later", role_arn)
            raise STSError(
                "AWS STS request throttled. Please retry after a short wait.",
                code="THROTTLED",
            ) from exc

        # Catch-all for other ClientErrors
        logger.error("STS ClientError [%s]: %s", error_code, error_msg)
        raise STSError(
            f"STS error ({error_code}): {error_msg}",
            code=error_code,
        ) from exc

    except BotoCoreError as exc:
        logger.error("BotoCoreError during AssumeRole: %s", exc)
        raise STSError(
            f"Low-level AWS SDK error: {exc}",
            code="BOTOCORE_ERROR",
        ) from exc
