# eToro SDD - Spec Driven Design
## Python & PySpark Coding Standards

This folder contains the official coding specifications for eToro engineering.
OpenClaw uses these specs when writing any Python or PySpark code for eToro projects.

## Structure

```
sdd/etoro/
├── README.md                    ← This file (entry point)
├── python/
│   ├── 01-style.md              ← Code style, naming, formatting
│   ├── 02-structure.md          ← Project/module structure
│   ├── 03-error-handling.md     ← Error handling patterns
│   ├── 04-logging.md            ← Logging standards
│   ├── 05-testing.md            ← Testing requirements
│   ├── 06-type-hints.md         ← Type annotations
│   └── 07-documentation.md     ← Docstrings & comments
├── pyspark/
│   ├── 01-spark-style.md        ← PySpark coding patterns
│   ├── 02-dataframe-ops.md      ← DataFrame best practices
│   ├── 03-performance.md        ← Optimization & partitioning
│   ├── 04-delta-lake.md         ← Delta Lake / Unity Catalog standards
│   └── 05-testing-spark.md      ← Testing Spark jobs
├── architecture/
│   ├── 01-project-layout.md     ← Standard project folder structure
│   ├── 02-medallion.md          ← Bronze/Silver/Gold layer conventions
│   └── 03-config-secrets.md     ← Config & secrets management
└── templates/
    ├── python_module.py         ← Template: Python module
    ├── pyspark_job.py           ← Template: PySpark job
    └── delta_pipeline.py        ← Template: Delta Lake pipeline
```

## How to Use with OpenClaw

When asking OpenClaw to write Python/PySpark code for eToro, prefix your request with:
> "Use eToro SDD standards"

Or point directly:
> "Follow specs in workspace/sdd/etoro/"

OpenClaw will read the relevant spec files before writing any code.
