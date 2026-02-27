### **Model Design Details**

![System Architecture](./star_schema.png) 

*   **Fact Table Grain:** The grain is **one row per candidate application**. This represents the most atomic level of data provided in the source system, allowing for maximum analytical flexibility.
*   **Surrogate Keys (SK):** In compliance with Data Warehousing best practices, all Primary Keys in this model are **Surrogate Keys** (integers generated during the ETL process). This decouples the Data Warehouse from source-system natural keys (like Email), ensuring referential integrity even if source data changes.
*   **Dimensional Strategy:** 
    *   **dim_jobs:** Technology and Seniority are combined into a single "Job Profile" dimension to simplify queries and improve performance when filtering by candidate expertise.
    *   **dim_times:** The application date is deconstructed into a dedicated dimension to support time-series KPIs (Yearly, Quarterly, and Monthly trends).
*   **Measures:** The Fact table stores quantitative scores and the result of the **"Hired" business logic**, enabling direct aggregation for KPI reporting.

---

### **Schema Definition**

**Fact Table: `fact_applications`**
*   `application_id` **(PK)**: Unique surrogate key for each application.
*   `candidate_id` **(FK)**: Reference to Candidate dimension.
*   `date_id` **(FK)**: Reference to Time dimension.
*   `job_id` **(FK)**: Reference to Job dimension (Tech + Seniority).
*   `location_id` **(FK)**: Reference to Location dimension.
*   `score_code_challenge`: Integer score (0-10).
*   `score_technical_interview`: Integer score (0-10).
*   `is_hired`: Boolean/Integer flag (1 if both scores $\ge$ 7, else 0).

**Dimension: `dim_candidates`**
*   `candidate_id` **(PK)**: Surrogate key.
*   `first_name`: Candidate's first name.
*   `last_name`: Candidate's last name.
*   `email`: Candidate's email address.

**Dimension: `dim_jobs`**
*   `job_id` **(PK)**: Surrogate key.
*   `technology`: The technical stack (e.g., Data Engineer).
*   `seniority`: The experience level (e.g., Senior).

**Dimension: `dim_locations`**
*   `location_id` **(PK)**: Surrogate key.
*   `country`: Name of the candidate's country.

**Dimension: `dim_times`**
*   `date_id` **(PK)**: Surrogate key.
*   `full_date`: Original date in `YYYY-MM-DD` format.
*   `year`: Extraction of the year.
*   `month`: Extraction of the month.
*   `day`: Extraction of the day.
*   `quarter`: Extraction of the quarter (1-4).