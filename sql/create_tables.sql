-- Schema: ETL Workshop 1 - Star Schema
-- All tables follow the Dimensional Model defined in diagrams/README.md
-- Run this script once to create the Data Warehouse schema in PostgreSQL.

-- Drop tables in reverse dependency order to allow clean re-runs
DROP TABLE IF EXISTS fact_applications;
DROP TABLE IF EXISTS dim_candidates;
DROP TABLE IF EXISTS dim_jobs;
DROP TABLE IF EXISTS dim_locations;
DROP TABLE IF EXISTS dim_times;


-- Dimension: Candidates
CREATE TABLE dim_candidates (
    candidate_id        SERIAL PRIMARY KEY,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255) NOT NULL
);


-- Dimension: Job Profiles (Technology + Seniority)
CREATE TABLE dim_jobs (
    job_id              SERIAL PRIMARY KEY,
    technology          VARCHAR(150) NOT NULL,
    seniority           VARCHAR(50) NOT NULL,
    UNIQUE (technology, seniority)
);


-- Dimension: Locations (Country)
CREATE TABLE dim_locations (
    location_id         SERIAL PRIMARY KEY,
    country             VARCHAR(150) NOT NULL UNIQUE
);


-- Dimension: Time (Derived from Application Date)
CREATE TABLE dim_times (
    date_id             SERIAL PRIMARY KEY,
    full_date           DATE NOT NULL UNIQUE,
    year                SMALLINT NOT NULL,
    month               SMALLINT NOT NULL,
    day                 SMALLINT NOT NULL,
    quarter             SMALLINT NOT NULL
);


-- Fact Table: Applications
-- Grain: One row per candidate application.
CREATE TABLE fact_applications (
    application_id              SERIAL PRIMARY KEY,
    candidate_id                INT NOT NULL REFERENCES dim_candidates(candidate_id),
    date_id                     INT NOT NULL REFERENCES dim_times(date_id),
    job_id                      INT NOT NULL REFERENCES dim_jobs(job_id),
    location_id                 INT NOT NULL REFERENCES dim_locations(location_id),
    yoe                         SMALLINT NOT NULL,
    score_code_challenge        SMALLINT NOT NULL,
    score_technical_interview   SMALLINT NOT NULL,
    is_hired                    SMALLINT NOT NULL DEFAULT 0
);
