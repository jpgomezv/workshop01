import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Ensure parent directory is on the path so sibling packages resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logs.logger import get_logger
from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data

logger = get_logger(__name__)

# Path to the raw source file relative to the project root
RAW_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'candidates.csv')


def get_engine():
    """
    Build a SQLAlchemy Engine from environment variables.
    Expects .env (or the shell environment) to define:
        DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    """
    load_dotenv()

    host     = os.getenv("DB_HOST", "localhost")
    port     = os.getenv("DB_PORT", "5432")
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    db_name  = os.getenv("DB_NAME")

    if not all([user, password, db_name]):
        logger.error("Missing database credentials. Check your .env file.")
        raise EnvironmentError("DB_USER, DB_PASSWORD, and DB_NAME must be set in the environment.")

    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
    logger.debug("Connecting to PostgreSQL at %s:%s/%s", host, port, db_name)

    return create_engine(connection_string)


def main():
    """
    ETL Pipeline Orchestrator.

    Sequentially executes:
        1. Extract  - read raw CSV
        2. Transform - cleanse, apply rules, build Star Schema tables
        3. Load      - insert tables into PostgreSQL Data Warehouse
    """
    logger.info("--- ETL Pipeline started ---")

    try:
        # Step 1: Extract
        logger.info("[1/3] Extract")
        df_raw = extract_data(RAW_FILE_PATH)

        # Step 2: Transform
        logger.info("[2/3] Transform")
        data = transform_data(df_raw)

        # Step 3: Load
        logger.info("[3/3] Load")
        engine = get_engine()
        load_data(data, engine)

        logger.info("--- ETL Pipeline completed successfully ---")

    except Exception:
        logger.exception("--- ETL Pipeline failed ---")
        sys.exit(1)


if __name__ == "__main__":
    main()
