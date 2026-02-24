# Workshop 01: ETL System Architecture

```mermaid
graph LR
    subgraph Data_Source ["Source"]
        CSV[fa:fa-file-csv "Candidates CSV"]
    end

    subgraph ETL_Process ["ETL Pipeline"]
        Raw["fa:fa-database Raw Dataset"]
        EDA["fa:fa-chart-line EDA"]
        Transform["fa:fa-gears Transform"]
    end

    subgraph Storage ["Storage"]
        DW["fa:fa-server Data Warehouse"]
    end

    subgraph Visualization ["Output"]
        Dashboard["fa:fa-gauge Dashboard"]
    end

    CSV --> Raw
    Raw --> EDA
    Raw --> Transform
    Transform --> DW
    DW --> Dashboard

    style Data_Source fill:#f9f,stroke:#333,stroke-width:2px
    style ETL_Process fill:#bbf,stroke:#333,stroke-width:2px
    style Storage fill:#bfb,stroke:#333,stroke-width:2px
    style Visualization fill:#fbb,stroke:#333,stroke-width:2px
```