"""
AWS data ingestion — Cost Explorer, EC2, EBS & RDS metrics.

Public functions:
- ``fetch_monthly_costs``   — daily cost breakdown by service
- ``fetch_ec2_utilization`` — running EC2 instances + 14-day avg CPU
- ``fetch_ebs_volumes``     — all EBS volumes with attachment state
- ``fetch_rds_utilization`` — RDS instances + CPU & connection metrics
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# ── Retry config for throttled AWS calls ─────────────────────────
MAX_RETRIES = 5
BACKOFF_BASE = 1.0  # seconds


def _is_throttle(exc: ClientError) -> bool:
    """Return True if the error is a throttling / rate-limit response."""
    code = exc.response["Error"]["Code"]
    return code in (
        "Throttling",
        "ThrottlingException",
        "RequestLimitExceeded",
        "TooManyRequestsException",
        "LimitExceededException",
    )


def _retry_on_throttle(func, *args, **kwargs) -> Any:
    """Call *func* with exponential backoff on throttle errors."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except ClientError as exc:
            if _is_throttle(exc) and attempt < MAX_RETRIES:
                wait = BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "Throttled (%s) — retry %d/%d in %.1fs",
                    exc.response["Error"]["Code"],
                    attempt,
                    MAX_RETRIES,
                    wait,
                )
                time.sleep(wait)
            else:
                raise


# ═══════════════════════════════════════════════════════════════════
#  COST EXPLORER
# ═══════════════════════════════════════════════════════════════════

def fetch_monthly_costs(
    session: boto3.Session,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    """
    Retrieve daily cost data grouped by AWS service.

    Parameters
    ----------
    session : boto3.Session
        Session with temporary AssumeRole credentials.
    start_date : str
        Inclusive start in ``YYYY-MM-DD`` format.
    end_date : str
        Exclusive end in ``YYYY-MM-DD`` format.

    Returns
    -------
    list[dict]
        Each dict has keys: ``date``, ``service``, ``amount``, ``currency``.
    """
    ce = session.client("ce")
    results: list[dict[str, Any]] = []
    next_token: str | None = None

    try:
        while True:
            params: dict[str, Any] = {
                "TimePeriod": {"Start": start_date, "End": end_date},
                "Granularity": "DAILY",
                "Metrics": ["UnblendedCost"],
                "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
            }
            if next_token:
                params["NextPageToken"] = next_token

            response = _retry_on_throttle(ce.get_cost_and_usage, **params)

            for result_by_time in response.get("ResultsByTime", []):
                period_start = result_by_time["TimePeriod"]["Start"]
                for group in result_by_time.get("Groups", []):
                    service_name = group["Keys"][0]
                    cost_info = group["Metrics"]["UnblendedCost"]
                    results.append({
                        "date": period_start,
                        "service": service_name,
                        "amount": float(cost_info["Amount"]),
                        "currency": cost_info.get("Unit", "USD"),
                    })

            next_token = response.get("NextPageToken")
            if not next_token:
                break

        logger.info(
            "Fetched %d cost records from %s to %s",
            len(results), start_date, end_date,
        )
        return results

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        logger.error("Cost Explorer error [%s]: %s", error_code, error_msg)

        if error_code == "AccessDeniedException":
            raise PermissionError(
                "Cost Explorer access denied — ensure ce:GetCostAndUsage "
                "is allowed in the IAM policy."
            ) from exc

        raise RuntimeError(
            f"Cost Explorer API error ({error_code}): {error_msg}"
        ) from exc


# ═══════════════════════════════════════════════════════════════════
#  EC2 UTILIZATION  (EC2 + CloudWatch)
# ═══════════════════════════════════════════════════════════════════

def fetch_ec2_utilization(
    session: boto3.Session,
    lookback_days: int = 14,
) -> list[dict[str, Any]]:
    """
    List running EC2 instances and their average CPU over the past
    *lookback_days*.

    Parameters
    ----------
    session : boto3.Session
        Session with temporary AssumeRole credentials.
    lookback_days : int
        Number of past days to average CPU utilization over.

    Returns
    -------
    list[dict]
        Each dict: ``instance_id``, ``instance_type``, ``state``,
        ``region``, ``avg_cpu_percent``.
    """
    ec2 = session.client("ec2")
    cw = session.client("cloudwatch")
    region = session.region_name
    results: list[dict[str, Any]] = []

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=lookback_days)

    try:
        # ── Paginate through EC2 instances ───────────────────────
        paginator = ec2.get_paginator("describe_instances")
        page_iterator = paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}],
        )

        instances: list[dict[str, Any]] = []
        for page in page_iterator:
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instances.append({
                        "instance_id": inst["InstanceId"],
                        "instance_type": inst["InstanceType"],
                        "state": inst["State"]["Name"],
                    })

        logger.info("Found %d running EC2 instances in %s", len(instances), region)

        # ── Fetch avg CPU per instance ───────────────────────────
        for inst in instances:
            avg_cpu = _get_avg_cpu(
                cw,
                inst["instance_id"],
                start_time,
                now,
            )
            results.append({
                "instance_id": inst["instance_id"],
                "instance_type": inst["instance_type"],
                "state": inst["state"],
                "region": region,
                "avg_cpu_percent": avg_cpu,
            })

        return results

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        logger.error("EC2/CloudWatch error [%s]: %s", error_code, error_msg)

        if error_code in ("UnauthorizedOperation", "AccessDeniedException"):
            raise PermissionError(
                "EC2 or CloudWatch access denied — check IAM permissions "
                "for ec2:DescribeInstances and cloudwatch:GetMetricStatistics."
            ) from exc

        raise RuntimeError(
            f"EC2/CloudWatch API error ({error_code}): {error_msg}"
        ) from exc


def _get_avg_cpu(
    cw_client,
    instance_id: str,
    start_time: datetime,
    end_time: datetime,
) -> float | None:
    """
    Query CloudWatch for the average CPUUtilization of a single instance.

    Returns None if no datapoints are available.
    """
    try:
        response = _retry_on_throttle(
            cw_client.get_metric_statistics,
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 1-day granularity
            Statistics=["Average"],
        )
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return None
        avg = sum(dp["Average"] for dp in datapoints) / len(datapoints)
        return round(avg, 2)

    except ClientError as exc:
        logger.warning(
            "Failed to get CPU for %s: %s",
            instance_id,
            exc.response["Error"]["Message"],
        )
        return None


# ═══════════════════════════════════════════════════════════════════
#  EBS VOLUMES
# ═══════════════════════════════════════════════════════════════════

def fetch_ebs_volumes(
    session: boto3.Session,
) -> list[dict[str, Any]]:
    """
    List all EBS volumes and their attachment state.

    Returns
    -------
    list[dict]
        Each dict: ``volume_id``, ``volume_type``, ``size_gb``,
        ``state``, ``region``, ``attached_instance_id`` (or None).
    """
    ec2 = session.client("ec2")
    region = session.region_name
    results: list[dict[str, Any]] = []

    try:
        paginator = ec2.get_paginator("describe_volumes")
        for page in paginator.paginate():
            for vol in page.get("Volumes", []):
                attachments = vol.get("Attachments", [])
                attached_to = attachments[0]["InstanceId"] if attachments else None

                results.append({
                    "volume_id": vol["VolumeId"],
                    "volume_type": vol.get("VolumeType", "gp2"),
                    "size_gb": vol.get("Size", 0),
                    "state": vol["State"] if attachments else "available",
                    "region": region,
                    "attached_instance_id": attached_to,
                })

        logger.info("Found %d EBS volumes in %s", len(results), region)
        return results

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        logger.error("EBS error [%s]: %s", error_code, error_msg)

        if error_code in ("UnauthorizedOperation", "AccessDeniedException"):
            raise PermissionError(
                "EBS access denied — check ec2:DescribeVolumes permission."
            ) from exc

        raise RuntimeError(
            f"EBS API error ({error_code}): {error_msg}"
        ) from exc


# ═══════════════════════════════════════════════════════════════════
#  RDS UTILIZATION  (RDS + CloudWatch)
# ═══════════════════════════════════════════════════════════════════

def fetch_rds_utilization(
    session: boto3.Session,
    lookback_days: int = 14,
) -> list[dict[str, Any]]:
    """
    List RDS instances with their average CPU and connection count.

    Parameters
    ----------
    session : boto3.Session
        Session with temporary AssumeRole credentials.
    lookback_days : int
        Number of past days to average metrics over.

    Returns
    -------
    list[dict]
        Each dict: ``db_instance_id``, ``instance_class``, ``engine``,
        ``status``, ``region``, ``avg_cpu_percent``, ``avg_connections``.
    """
    rds = session.client("rds")
    cw = session.client("cloudwatch")
    region = session.region_name
    results: list[dict[str, Any]] = []

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=lookback_days)

    try:
        paginator = rds.get_paginator("describe_db_instances")
        instances: list[dict[str, Any]] = []

        for page in paginator.paginate():
            for db_inst in page.get("DBInstances", []):
                instances.append({
                    "db_instance_id": db_inst["DBInstanceIdentifier"],
                    "instance_class": db_inst.get("DBInstanceClass", "unknown"),
                    "engine": db_inst.get("Engine", "unknown"),
                    "status": db_inst.get("DBInstanceStatus", "unknown"),
                })

        logger.info("Found %d RDS instances in %s", len(instances), region)

        for inst in instances:
            avg_cpu = _get_rds_metric(
                cw, inst["db_instance_id"],
                "CPUUtilization", "Average",
                start_time, now,
            )
            avg_conns = _get_rds_metric(
                cw, inst["db_instance_id"],
                "DatabaseConnections", "Average",
                start_time, now,
            )
            results.append({
                **inst,
                "region": region,
                "avg_cpu_percent": avg_cpu,
                "avg_connections": avg_conns,
            })

        return results

    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        error_msg = exc.response["Error"]["Message"]
        logger.error("RDS/CloudWatch error [%s]: %s", error_code, error_msg)

        if error_code in ("AccessDenied", "AccessDeniedException"):
            raise PermissionError(
                "RDS access denied — check rds:DescribeDBInstances and "
                "cloudwatch:GetMetricStatistics permissions."
            ) from exc

        raise RuntimeError(
            f"RDS/CloudWatch API error ({error_code}): {error_msg}"
        ) from exc


def _get_rds_metric(
    cw_client,
    db_instance_id: str,
    metric_name: str,
    statistic: str,
    start_time: datetime,
    end_time: datetime,
) -> float | None:
    """
    Query CloudWatch for a single RDS metric.

    Returns None if no datapoints are available.
    """
    try:
        response = _retry_on_throttle(
            cw_client.get_metric_statistics,
            Namespace="AWS/RDS",
            MetricName=metric_name,
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=[statistic],
        )
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return None
        avg = sum(dp[statistic] for dp in datapoints) / len(datapoints)
        return round(avg, 2)

    except ClientError as exc:
        logger.warning(
            "Failed to get %s for RDS %s: %s",
            metric_name,
            db_instance_id,
            exc.response["Error"]["Message"],
        )
        return None

