import pandas as pd
from sqlalchemy import Engine, text

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logs.logger import get_logger

logger = get_logger(__name__)


# Dimensions must be inserted AFTER the fact table is cleared,
# and BEFORE the fact table is inserted.
_INSERT_ORDER = [
    'dim_candidates',
    'dim_jobs',
    'dim_locations',
    'dim_times',
    'fact_applications',
]

_SQL_DIR = os.path.join(os.path.dirname(__file__), '..', 'sql')
_CREATE_TABLES_SQL = os.path.join(_SQL_DIR, 'create_tables.sql')


def _recreate_schema(conn) -> None:
    """
    Always execute sql/create_tables.sql, which starts with DROP ... CASCADE.
    This guarantees that schema changes (column types, constraints, etc.)
    are reflected on every pipeline run without manual database intervention.
    """
    logger.info("Recreating schema from sql/create_tables.sql.")
    with open(_CREATE_TABLES_SQL, 'r', encoding='utf-8') as f:
        ddl = f.read()

    # Execute each statement individually (split on ';', skip blank statements)
    statements = [s.strip() for s in ddl.split(';') if s.strip()]
    for statement in statements:
        conn.execute(text(statement))
    logger.info("Schema ready.")


def _truncate_all(conn) -> None:
    """
    Truncate all Star Schema tables in reverse-dependency order so that
    PostgreSQL FK constraints are not violated. RESTART IDENTITY resets
    sequences so surrogate keys start from 1 on every pipeline run.
    """
    truncate_order = list(reversed(_INSERT_ORDER))
    tables = ', '.join(truncate_order)
    logger.debug("Truncating tables (cascade): %s", tables)
    conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE;"))


def load_data(data: dict[str, pd.DataFrame], engine: Engine) -> None:
    """
    Load: Insert dimension and fact DataFrames into the PostgreSQL Data Warehouse.

    On the first run the schema is created automatically from sql/create_tables.sql.
    On subsequent runs the existing rows are cleared first (TRUNCATE CASCADE) so
    the pipeline is fully idempotent.

    Dimensions are inserted before the Fact table to satisfy FK constraints.

    Args:
        data:   Dictionary returned by transform_data(). Keys are table names,
                values are DataFrames ready for insertion.
        engine: SQLAlchemy Engine connected to the target PostgreSQL database.

    Raises:
        Exception: Propagates any database error after logging it.
    """
    logger.info("Starting data load into PostgreSQL.")

    try:
        with engine.begin() as conn:
            _recreate_schema(conn)

            for table_name in _INSERT_ORDER:
                if table_name not in data:
                    logger.warning("Table '%s' not found in transformation output. Skipping.", table_name)
                    continue

                df = data[table_name]

                df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists='append',   # Schema already exists; just insert rows.
                    index=False,
                    method='multi',
                )
                logger.info("Loaded table '%s': %d rows.", table_name, len(df))

        logger.info("All tables loaded successfully.")

    except Exception as exc:
        logger.exception("Load failed: %s", exc)
        raise
