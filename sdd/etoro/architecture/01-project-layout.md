# Standard Project Layout - eToro Data Engineering

## Databricks / PySpark Project

```
etoro-<domain>-pipeline/
├── src/
│   └── etoro_<domain>/
│       ├── __init__.py
│       ├── config.py               ← Pydantic settings from env
│       ├── models/                 ← Pydantic/dataclass models
│       ├── services/               ← Business logic
│       ├── repositories/           ← Delta/API data access
│       ├── transformations/        ← Pure DataFrame → DataFrame functions
│       │   ├── __init__.py
│       │   ├── bronze.py           ← Raw ingestion transforms
│       │   ├── silver.py           ← Cleaning & enrichment
│       │   └── gold.py             ← Aggregations & business metrics
│       ├── jobs/                   ← Entry points (one per job)
│       │   ├── ingest_positions.py
│       │   ├── build_silver.py
│       │   └── build_gold.py
│       └── utils/
│           ├── spark_utils.py
│           ├── date_utils.py
│           └── schema_utils.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── transformations/
│   └── integration/
├── notebooks/                      ← Databricks exploration only (not production)
│   └── exploratory/
├── sql/                            ← DDL and one-time migration scripts
│   ├── create_tables.sql
│   └── migrations/
├── .databricks/
│   └── bundle.yml                  ← Databricks Asset Bundle config
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── README.md
```

## Job Entry Point Pattern

```python
# src/etoro_trading/jobs/ingest_positions.py
"""Entry point for position ingestion job.

Reads from eToro API bronze layer and writes to silver.trading.positions.

Usage:
    databricks bundle run ingest_positions
    python -m etoro_trading.jobs.ingest_positions
"""
import logging
from pyspark.sql import SparkSession
from etoro_trading.config import Settings
from etoro_trading.repositories import PositionRepository
from etoro_trading.transformations.silver import clean_positions
from etoro_trading.utils.spark_utils import get_spark

logger = logging.getLogger(__name__)


def run(spark: SparkSession, settings: Settings) -> None:
    """Main job logic."""
    logger.info("Starting position ingestion", extra={"job": "ingest_positions"})

    repo = PositionRepository(spark)
    raw_df = repo.read_bronze()
    clean_df = clean_positions(raw_df)
    repo.write_silver(clean_df)

    logger.info("Ingestion complete", extra={"records": clean_df.count()})


if __name__ == "__main__":
    spark = get_spark("etoro-ingest-positions")
    settings = Settings()
    run(spark, settings)
```

## Databricks Asset Bundle (bundle.yml)

```yaml
bundle:
  name: etoro-trading-pipeline

targets:
  dev:
    mode: development
    workspace:
      host: https://adb-xxx.azuredatabricks.net
    variables:
      catalog: dev
  prod:
    mode: production
    workspace:
      host: https://adb-xxx.azuredatabricks.net
    variables:
      catalog: prod

resources:
  jobs:
    ingest_positions:
      name: "eToro - Ingest Positions"
      tasks:
        - task_key: ingest
          python_wheel_task:
            package_name: etoro_trading
            entry_point: etoro_trading.jobs.ingest_positions
          job_cluster_key: main
      job_clusters:
        - job_cluster_key: main
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: Standard_D4s_v3
            num_workers: 2
```

## pyproject.toml Template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "etoro-trading-pipeline"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "structlog>=24.0",
    "delta-spark>=3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.0",
    "black>=24.0",
    "isort>=5.0",
    "flake8>=7.0",
    "mypy>=1.0",
]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]
```
