-- load_tables.sql
-- Verification queries to confirm the Data Warehouse was populated correctly.
-- Run these after executing the ETL pipeline (python src/main.py).

-- Row counts for each table
SELECT 'dim_candidates'   AS table_name, COUNT(*) AS row_count FROM dim_candidates
UNION ALL
SELECT 'dim_jobs',                        COUNT(*) FROM dim_jobs
UNION ALL
SELECT 'dim_locations',                   COUNT(*) FROM dim_locations
UNION ALL
SELECT 'dim_times',                       COUNT(*) FROM dim_times
UNION ALL
SELECT 'fact_applications',               COUNT(*) FROM fact_applications;


-- KPI preview: Hired candidates by Technology
SELECT
    j.technology,
    SUM(f.is_hired) AS total_hired,
    COUNT(*)        AS total_applicants
FROM fact_applications f
JOIN dim_jobs j ON f.job_id = j.job_id
GROUP BY j.technology
ORDER BY total_hired DESC;


-- KPI preview: Hires by Year
SELECT
    t.year,
    SUM(f.is_hired) AS total_hired
FROM fact_applications f
JOIN dim_times t ON f.date_id = t.date_id
GROUP BY t.year
ORDER BY t.year;


-- KPI preview: Hires by Seniority
SELECT
    j.seniority,
    SUM(f.is_hired) AS total_hired
FROM fact_applications f
JOIN dim_jobs j ON f.job_id = j.job_id
GROUP BY j.seniority
ORDER BY total_hired DESC;


-- KPI preview: Hires by Country (focus countries)
SELECT
    l.country,
    t.year,
    SUM(f.is_hired) AS total_hired
FROM fact_applications f
JOIN dim_locations l ON f.location_id = l.location_id
JOIN dim_times     t ON f.date_id     = t.date_id
WHERE l.country IN ('United States of America', 'Brazil', 'Colombia', 'Ecuador')
GROUP BY l.country, t.year
ORDER BY l.country, t.year;
