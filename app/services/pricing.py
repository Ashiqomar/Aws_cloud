"""
Reference pricing for AWS resources.

This module provides approximate on-demand monthly costs for common
instance types and volume types.  These are ballpark US-East-1 prices
used to estimate savings — for production accuracy, integrate the
AWS Pricing API.

All prices are in USD/month (730 hrs for compute).
"""

# ═══════════════════════════════════════════════════════════════════
#  EC2 ON-DEMAND MONTHLY PRICES  (us-east-1, Linux)
# ═══════════════════════════════════════════════════════════════════
EC2_MONTHLY_PRICES: dict[str, float] = {
    # General Purpose
    "t2.nano":      3.36,
    "t2.micro":     6.72,
    "t2.small":    13.44,
    "t2.medium":   26.78,
    "t2.large":    53.58,
    "t2.xlarge":  107.16,
    "t2.2xlarge": 214.30,
    "t3.nano":      3.07,
    "t3.micro":     6.13,
    "t3.small":    12.26,
    "t3.medium":   24.53,
    "t3.large":    49.06,
    "t3.xlarge":   98.11,
    "t3.2xlarge": 196.22,
    "m5.large":    55.48,
    "m5.xlarge":  110.96,
    "m5.2xlarge": 221.92,
    "m5.4xlarge": 443.84,
    "m6i.large":   55.48,
    "m6i.xlarge": 110.96,
    "m6i.2xlarge":221.92,
    # Compute Optimized
    "c5.large":    49.28,
    "c5.xlarge":   98.55,
    "c5.2xlarge": 197.10,
    "c5.4xlarge": 394.20,
    "c6i.large":   49.28,
    "c6i.xlarge":  98.55,
    # Memory Optimized
    "r5.large":    72.56,
    "r5.xlarge":  145.12,
    "r5.2xlarge": 290.24,
    "r6i.large":   72.56,
    "r6i.xlarge": 145.12,
}

# ── Downsize mapping: current → smaller alternative ──────────────
EC2_DOWNSIZE_MAP: dict[str, str] = {
    "t2.2xlarge":  "t2.xlarge",
    "t2.xlarge":   "t2.large",
    "t2.large":    "t2.medium",
    "t2.medium":   "t2.small",
    "t2.small":    "t2.micro",
    "t3.2xlarge":  "t3.xlarge",
    "t3.xlarge":   "t3.large",
    "t3.large":    "t3.medium",
    "t3.medium":   "t3.small",
    "t3.small":    "t3.micro",
    "m5.4xlarge":  "m5.2xlarge",
    "m5.2xlarge":  "m5.xlarge",
    "m5.xlarge":   "m5.large",
    "m6i.2xlarge": "m6i.xlarge",
    "m6i.xlarge":  "m6i.large",
    "c5.4xlarge":  "c5.2xlarge",
    "c5.2xlarge":  "c5.xlarge",
    "c5.xlarge":   "c5.large",
    "c6i.xlarge":  "c6i.large",
    "r5.2xlarge":  "r5.xlarge",
    "r5.xlarge":   "r5.large",
    "r6i.xlarge":  "r6i.large",
}


# ═══════════════════════════════════════════════════════════════════
#  EBS VOLUME MONTHLY PRICES  (per GB/month, us-east-1)
# ═══════════════════════════════════════════════════════════════════
EBS_MONTHLY_PER_GB: dict[str, float] = {
    "gp2":       0.10,
    "gp3":       0.08,
    "io1":       0.125,
    "io2":       0.125,
    "st1":       0.045,
    "sc1":       0.015,
    "standard":  0.05,   # magnetic
}


# ═══════════════════════════════════════════════════════════════════
#  RDS ON-DEMAND MONTHLY PRICES  (us-east-1, Single-AZ, MySQL)
# ═══════════════════════════════════════════════════════════════════
RDS_MONTHLY_PRICES: dict[str, float] = {
    "db.t3.micro":   10.66,
    "db.t3.small":   23.36,
    "db.t3.medium":  47.45,
    "db.t3.large":   94.90,
    "db.m5.large":  125.56,
    "db.m5.xlarge": 251.12,
    "db.m5.2xlarge":502.24,
    "db.r5.large":  163.52,
    "db.r5.xlarge": 327.04,
    "db.r5.2xlarge":654.08,
}

RDS_DOWNSIZE_MAP: dict[str, str] = {
    "db.t3.large":   "db.t3.medium",
    "db.t3.medium":  "db.t3.small",
    "db.t3.small":   "db.t3.micro",
    "db.m5.2xlarge": "db.m5.xlarge",
    "db.m5.xlarge":  "db.m5.large",
    "db.r5.2xlarge": "db.r5.xlarge",
    "db.r5.xlarge":  "db.r5.large",
}


# ═══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def ec2_monthly_cost(instance_type: str) -> float | None:
    """Return the monthly cost for an EC2 type, or None if unknown."""
    return EC2_MONTHLY_PRICES.get(instance_type)


def ec2_downsize_savings(instance_type: str) -> tuple[str | None, float]:
    """
    Return (smaller_type, monthly_savings) if a downsize path exists.
    Returns (None, 0.0) otherwise.
    """
    smaller = EC2_DOWNSIZE_MAP.get(instance_type)
    if smaller is None:
        return None, 0.0
    current_cost = EC2_MONTHLY_PRICES.get(instance_type, 0)
    smaller_cost = EC2_MONTHLY_PRICES.get(smaller, 0)
    return smaller, round(current_cost - smaller_cost, 2)


def ebs_monthly_cost(volume_type: str, size_gb: int) -> float:
    """Return the estimated monthly cost for an EBS volume."""
    per_gb = EBS_MONTHLY_PER_GB.get(volume_type, 0.10)  # fallback to gp2
    return round(per_gb * size_gb, 2)


def rds_monthly_cost(instance_class: str) -> float | None:
    """Return the monthly cost for an RDS class, or None if unknown."""
    return RDS_MONTHLY_PRICES.get(instance_class)


def rds_downsize_savings(instance_class: str) -> tuple[str | None, float]:
    """
    Return (smaller_class, monthly_savings) if a downsize path exists.
    Returns (None, 0.0) otherwise.
    """
    smaller = RDS_DOWNSIZE_MAP.get(instance_class)
    if smaller is None:
        return None, 0.0
    current_cost = RDS_MONTHLY_PRICES.get(instance_class, 0)
    smaller_cost = RDS_MONTHLY_PRICES.get(smaller, 0)
    return smaller, round(current_cost - smaller_cost, 2)
