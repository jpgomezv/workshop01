import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logs.logger import get_logger

logger = get_logger(__name__)


def _cleanse(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to snake_case, enforce types, drop duplicates.
    Returns a cleansed copy of the raw DataFrame.
    """
    logger.debug("Cleansing: renaming columns and enforcing types.")

    df = df.copy()

    # Standardize column names
    df.columns = [
        'first_name', 'last_name', 'email', 'application_date', 'country',
        'yoe', 'seniority', 'technology', 'score_code_challenge',
        'score_technical_interview',
    ]

    # Enforce numeric types
    df['yoe'] = pd.to_numeric(df['yoe'], errors='coerce').astype('Int64')
    df['score_code_challenge'] = pd.to_numeric(df['score_code_challenge'], errors='coerce').astype('Int64')
    df['score_technical_interview'] = pd.to_numeric(df['score_technical_interview'], errors='coerce').astype('Int64')

    # Enforce datetime
    df['application_date'] = pd.to_datetime(df['application_date'], errors='coerce')

    # Drop rows that violate core constraints
    initial_count = len(df)
    df = df.drop_duplicates()
    df = df.dropna(subset=['email', 'application_date', 'yoe', 'score_code_challenge', 'score_technical_interview'])
    df = df[(df['yoe'] >= 0) & (df['yoe'] <= 50)]
    df = df[(df['score_code_challenge'] >= 0) & (df['score_code_challenge'] <= 10)]
    df = df[(df['score_technical_interview'] >= 0) & (df['score_technical_interview'] <= 10)]

    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning("Cleansing removed %d invalid record(s).", dropped)
    else:
        logger.info("Cleansing passed: no invalid records found.")

    return df


def _apply_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Inject the 'is_hired' flag: 1 when both scores >= 7, otherwise 0.
    """
    logger.debug("Applying business rule: is_hired = (score_code_challenge >= 7 AND score_technical_interview >= 7).")

    df = df.copy()
    df['is_hired'] = np.where(
        (df['score_code_challenge'] >= 7) & (df['score_technical_interview'] >= 7),
        1, 0
    )

    hired_count = df['is_hired'].sum()
    logger.info("Business rule applied. Hired candidates: %d (%.2f%%).", hired_count, (hired_count / len(df)) * 100)

    return df


def _build_dim_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique candidates and assign surrogate keys."""
    dim = (
        df[['first_name', 'last_name', 'email']]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.insert(0, 'candidate_id', dim.index + 1)
    logger.debug("dim_candidates built: %d unique records.", len(dim))
    return dim


def _build_dim_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique technology + seniority combinations and assign surrogate keys."""
    dim = (
        df[['technology', 'seniority']]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.insert(0, 'job_id', dim.index + 1)
    logger.debug("dim_jobs built: %d unique records.", len(dim))
    return dim


def _build_dim_locations(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique countries and assign surrogate keys."""
    dim = (
        df[['country']]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim.insert(0, 'location_id', dim.index + 1)
    logger.debug("dim_locations built: %d unique records.", len(dim))
    return dim


def _build_dim_times(df: pd.DataFrame) -> pd.DataFrame:
    """Decompose unique application dates into time attributes and assign surrogate keys."""
    dim = (
        df[['application_date']]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    dim['full_date'] = dim['application_date'].dt.date
    dim['year']      = dim['application_date'].dt.year.astype('Int64')
    dim['month']     = dim['application_date'].dt.month.astype('Int64')
    dim['day']       = dim['application_date'].dt.day.astype('Int64')
    dim['quarter']   = dim['application_date'].dt.quarter.astype('Int64')
    dim = dim.drop(columns=['application_date'])
    dim.insert(0, 'date_id', dim.index + 1)
    logger.debug("dim_times built: %d unique records.", len(dim))
    return dim


def _build_fact_applications(
    df: pd.DataFrame,
    dim_candidates: pd.DataFrame,
    dim_jobs: pd.DataFrame,
    dim_locations: pd.DataFrame,
    dim_times: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join dimension surrogate keys back onto the main DataFrame to produce
    the fact_applications table.
    """
    logger.debug("Building fact_applications by mapping surrogate keys.")

    df = df.copy()
    df['full_date'] = df['application_date'].dt.date

    # Map surrogate keys
    df = df.merge(dim_candidates[['candidate_id', 'first_name', 'last_name', 'email']], on=['first_name', 'last_name', 'email'], how='left')
    df = df.merge(dim_jobs[['job_id', 'technology', 'seniority']], on=['technology', 'seniority'], how='left')
    df = df.merge(dim_locations[['location_id', 'country']], on='country', how='left')
    df = df.merge(dim_times[['date_id', 'full_date']], on='full_date', how='left')

    fact = df[[
        'candidate_id', 'date_id', 'job_id', 'location_id',
        'yoe', 'score_code_challenge', 'score_technical_interview', 'is_hired',
    ]].reset_index(drop=True)

    fact.insert(0, 'application_id', fact.index + 1)

    # Ensure integer types for FK columns (nullable int -> regular int after merge)
    int_cols = ['candidate_id', 'date_id', 'job_id', 'location_id',
                'yoe', 'score_code_challenge', 'score_technical_interview', 'is_hired']
    for col in int_cols:
        fact[col] = fact[col].astype(int)

    logger.info("fact_applications built: %d rows.", len(fact))
    return fact


def transform_data(df_raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Transform: Cleanse, apply business rules, and decompose the raw DataFrame
    into Star Schema dimension + fact tables.

    Args:
        df_raw: Raw DataFrame from extract_data().

    Returns:
        A dictionary with keys:
          'dim_candidates', 'dim_jobs', 'dim_locations', 'dim_times',
          'fact_applications'
    """
    logger.info("Starting transformation.")

    df = _cleanse(df_raw)
    df = _apply_business_rules(df)

    dim_candidates = _build_dim_candidates(df)
    dim_jobs       = _build_dim_jobs(df)
    dim_locations  = _build_dim_locations(df)
    dim_times      = _build_dim_times(df)
    fact           = _build_fact_applications(df, dim_candidates, dim_jobs, dim_locations, dim_times)

    logger.info("Transformation complete.")

    return {
        'dim_candidates':   dim_candidates,
        'dim_jobs':         dim_jobs,
        'dim_locations':    dim_locations,
        'dim_times':        dim_times,
        'fact_applications': fact,
    }