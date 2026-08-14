"""
SQLAlchemy declarative base.

All ORM models inherit from ``Base`` defined here.  Keeping the base in its
own module avoids circular imports between models and the session factory.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide declarative base for SQLAlchemy models."""
    pass
