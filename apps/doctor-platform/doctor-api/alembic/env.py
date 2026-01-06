"""
Alembic Environment Configuration - Doctor API
===============================================

This module configures the Alembic migration environment.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add src to path for model imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import all models to ensure they're registered with Base.metadata
from db.base import Base
from db.doctor_models import *  # noqa
from db.models.clinic import *  # noqa
from db.models.staff import *  # noqa
from db.models.analytics import *  # noqa

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """
    Get database URL from environment variables.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "oncolife_admin")
    password = os.getenv("POSTGRES_PASSWORD", "oncolife_dev_password")
    database = os.getenv("POSTGRES_DOCTOR_DB", "oncolife_doctor")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

