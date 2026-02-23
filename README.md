graph LR
  A[(Raw CSV)] --> B[Extract: Python]
  B --> C[Transform: Pandas/uv]
  C --> D[(Data Warehouse: SQLite)]
  D --> E[Dashboard: PowerBI]