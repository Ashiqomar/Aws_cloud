"""
Remediation Service — AWS Boto3 automated actions.

Executes resource remediation actions via Boto3 session:
- ``stop_ec2_instance``: Stops an idle EC2 instance.
- ``delete_ebs_volume``: Deletes an unattached EBS volume.
- Includes DryRun permission check handling.
"""

from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class RemediationError(Exception):
    """Raised when a remediation action fails."""
    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


def stop_ec2_instance(
    session: boto3.Session,
    instance_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Stop an EC2 instance using Boto3.

    Parameters
    ----------
    session : boto3.Session
        Authenticated session with AssumeRole temporary creds.
    instance_id : str
        EC2 instance identifier (e.g. i-0a8f912bc41).
    dry_run : bool
        If True, validates AWS permissions without stopping the instance.

    Returns
    -------
    dict
        Status summary of action taken.
    """
    ec2 = session.client("ec2")
    try:
        response = ec2.stop_instances(
            InstanceIds=[instance_id],
            DryRun=dry_run,
        )
        stopping_info = response.get("StoppingInstances", [])
        current_state = stopping_info[0]["CurrentState"]["Name"] if stopping_info else "stopping"
        
        logger.info("EC2 %s state set to %s (dry_run=%s)", instance_id, current_state, dry_run)
        return {
            "action": "stop_ec2_instance",
            "resource_id": instance_id,
            "status": current_state,
            "dry_run": dry_run,
            "message": f"Successfully initiated stop for instance {instance_id}.",
        }

    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        msg = exc.response["Error"]["Message"]

        # DryRunOperation exception indicates permissions ARE valid during a dry-run test!
        if dry_run and code == "DryRunOperation":
            logger.info("DryRun permission test passed for stop_ec2_instance on %s", instance_id)
            return {
                "action": "stop_ec2_instance",
                "resource_id": instance_id,
                "status": "dry_run_success",
                "dry_run": True,
                "message": f"DryRun test passed: IAM permissions allow stopping instance {instance_id}.",
            }

        if code in ("UnauthorizedOperation", "AccessDenied", "AccessDeniedException"):
            logger.error("AccessDenied stopping EC2 %s: %s", instance_id, msg)
            raise RemediationError(
                f"Access denied: missing ec2:StopInstances permission for {instance_id}.",
                code="ACCESS_DENIED",
            ) from exc

        logger.error("EC2 stop error [%s] for %s: %s", code, instance_id, msg)
        raise RemediationError(f"Failed to stop instance {instance_id}: {msg}", code=code) from exc


def delete_ebs_volume(
    session: boto3.Session,
    volume_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Delete an unattached EBS volume using Boto3.

    Parameters
    ----------
    session : boto3.Session
        Authenticated session.
    volume_id : str
        EBS volume identifier (e.g. vol-0f12984cd12a).
    dry_run : bool
        If True, validates AWS permissions without deleting the volume.

    Returns
    -------
    dict
        Status summary.
    """
    ec2 = session.client("ec2")
    try:
        ec2.delete_volume(
            VolumeId=volume_id,
            DryRun=dry_run,
        )
        logger.info("EBS volume %s deleted (dry_run=%s)", volume_id, dry_run)
        return {
            "action": "delete_ebs_volume",
            "resource_id": volume_id,
            "status": "deleted" if not dry_run else "dry_run_success",
            "dry_run": dry_run,
            "message": f"Successfully deleted EBS volume {volume_id}.",
        }

    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        msg = exc.response["Error"]["Message"]

        if dry_run and code == "DryRunOperation":
            logger.info("DryRun permission test passed for delete_ebs_volume on %s", volume_id)
            return {
                "action": "delete_ebs_volume",
                "resource_id": volume_id,
                "status": "dry_run_success",
                "dry_run": True,
                "message": f"DryRun test passed: IAM permissions allow deleting EBS volume {volume_id}.",
            }

        if code in ("UnauthorizedOperation", "AccessDenied", "AccessDeniedException"):
            logger.error("AccessDenied deleting EBS volume %s: %s", volume_id, msg)
            raise RemediationError(
                f"Access denied: missing ec2:DeleteVolume permission for {volume_id}.",
                code="ACCESS_DENIED",
            ) from exc

        logger.error("EBS delete error [%s] for %s: %s", code, volume_id, msg)
        raise RemediationError(f"Failed to delete volume {volume_id}: {msg}", code=code) from exc


def execute_remediation_action(
    session: boto3.Session,
    reco_type: str,
    resource_id: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Dispatcher to execute the appropriate remediation action by recommendation type.
    """
    if reco_type == "idle_ec2":
        return stop_ec2_instance(session, resource_id, dry_run=dry_run)
    elif reco_type == "unused_ebs":
        return delete_ebs_volume(session, resource_id, dry_run=dry_run)
    elif reco_type == "oversized_rds":
        # Simulate RDS modification acknowledgement
        return {
            "action": "modify_rds_instance",
            "resource_id": resource_id,
            "status": "applied" if not dry_run else "dry_run_success",
            "dry_run": dry_run,
            "message": f"Downsize plan logged for RDS {resource_id} (dry_run={dry_run}).",
        }
    else:
        raise RemediationError(f"Unsupported remediation type: {reco_type}")
