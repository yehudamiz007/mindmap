# Workflows & Delta Live Tables Reference

## Databricks Workflows (Jobs)

### Job Structure

```
Job
├── Task 1: Notebook / Python script / SQL / DLT pipeline / dbt
├── Task 2: depends_on: [Task 1]
└── Task 3: depends_on: [Task 1, Task 2]
```

### Create Job via SDK

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import Task, NotebookTask, JobCluster

w = WorkspaceClient()

job = w.jobs.create(
    name="Daily ETL",
    tasks=[
        Task(
            task_key="ingest",
            notebook_task=NotebookTask(
                notebook_path="/Repos/main/notebooks/ingest",
                base_parameters={"env": "prod"}
            ),
            existing_cluster_id="0101-abc123"
        ),
        Task(
            task_key="transform",
            depends_on=[{"task_key": "ingest"}],
            notebook_task=NotebookTask(
                notebook_path="/Repos/main/notebooks/transform"
            ),
            existing_cluster_id="0101-abc123"
        )
    ],
    schedule={
        "quartz_cron_expression": "0 0 6 * * ?",  # 6am daily
        "timezone_id": "Asia/Jerusalem"
    }
)
```

### Trigger & Monitor Jobs

```python
# Run now
run = w.jobs.run_now(job_id=job.job_id)

# Wait for completion
w.jobs.wait_get_run_job_terminated_or_skipped(run_id=run.run_id)

# Get run status
run_info = w.runs.get(run_id=run.run_id)
print(run_info.state.result_state)

# Repair a failed run (re-run failed tasks only)
w.runs.repair(run_id=run.run_id, rerun_all_failed_tasks=True)
```

### Job Parameters

```python
# In notebook, access job parameters
dbutils.widgets.get("env")  # if passed as base_parameter

# Or via task values (pass between tasks)
dbutils.jobs.taskValues.set(key="row_count", value=df.count())
count = dbutils.jobs.taskValues.get(taskKey="ingest", key="row_count")
```

## Delta Live Tables (DLT)

### Pipeline Types

| Type | Description |
|------|-------------|
| `@dlt.table` | Materialized view (batch or streaming) |
| `@dlt.view` | Logical view (not stored) |
| `@dlt.streaming_table` | Append-only streaming table |

### Basic DLT Pipeline

```python
import dlt
from pyspark.sql.functions import *

# Source (raw ingestion)
@dlt.table(
    name="raw_orders",
    comment="Raw orders from bronze layer",
    table_properties={"quality": "bronze"}
)
def raw_orders():
    return (spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "json")
            .load("/Volumes/my_catalog/raw/orders/"))

# Silver (cleaned)
@dlt.table(
    name="cleaned_orders",
    comment="Validated and cleaned orders",
    table_properties={"quality": "silver"}
)
@dlt.expect("valid_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("positive_amount", "amount > 0")
@dlt.expect_or_fail("valid_customer", "customer_id IS NOT NULL")
def cleaned_orders():
    return (dlt.read_stream("raw_orders")
            .select("order_id", "customer_id", "amount",
                    to_timestamp("created_at").alias("created_at"))
            .filter("status != 'cancelled'"))

# Gold (aggregated)
@dlt.table(
    name="daily_revenue",
    comment="Daily revenue aggregation",
    table_properties={"quality": "gold"}
)
def daily_revenue():
    return (dlt.read("cleaned_orders")
            .groupBy(date_trunc("day", "created_at").alias("date"))
            .agg(sum("amount").alias("revenue"), count("order_id").alias("orders")))
```

### DLT Expectations

| Decorator | On failure |
|-----------|-----------|
| `@dlt.expect("name", "condition")` | Tracks violations in event log, keeps records |
| `@dlt.expect_or_drop("name", "condition")` | Drops violating records |
| `@dlt.expect_or_fail("name", "condition")` | Fails pipeline on violation |
| `@dlt.expect_all({"name": "cond", ...})` | Multiple constraints, warn |
| `@dlt.expect_all_or_drop({...})` | Multiple constraints, drop |

### Change Data Capture (APPLY CHANGES)

```python
dlt.create_streaming_table("orders_silver")

dlt.apply_changes(
    target="orders_silver",
    source="raw_cdc_orders",
    keys=["order_id"],
    sequence_by="updated_at",
    apply_as_deletes=expr("op = 'DELETE'"),
    apply_as_truncates=expr("op = 'TRUNCATE'"),
    column_list=["order_id", "customer_id", "amount", "updated_at"],
    except_column_list=["_rescued_data"]
)
```

### DLT Pipeline Config (databricks.yml)

```yaml
resources:
  pipelines:
    orders_pipeline:
      name: "Orders DLT Pipeline"
      target: my_catalog.dlt_schema
      catalog: my_catalog
      continuous: false  # triggered mode
      channel: "PREVIEW"
      clusters:
        - label: "default"
          autoscale:
            min_workers: 2
            max_workers: 8
      libraries:
        - notebook:
            path: /Repos/main/pipelines/orders
      configuration:
        env: prod
        source_path: /Volumes/my_catalog/raw/orders
```

### DLT Event Log

```sql
-- Query DLT event log
SELECT
  timestamp,
  event_type,
  message,
  details
FROM my_catalog.dlt_schema.event_log
WHERE level = 'ERROR'
ORDER BY timestamp DESC
LIMIT 50;

-- Data quality metrics
SELECT
  timestamp,
  details:flow_name::string as flow,
  details:expectations[0]:name::string as expectation,
  details:expectations[0]:passed_records::int as passed,
  details:expectations[0]:failed_records::int as failed
FROM my_catalog.dlt_schema.event_log
WHERE event_type = 'flow_progress'
  AND details:expectations IS NOT NULL;
```

## Databricks Asset Bundles (DAB)

```yaml
# databricks.yml - project root
bundle:
  name: my_project

targets:
  dev:
    mode: development
    workspace:
      host: https://your-workspace.azuredatabricks.net

  prod:
    mode: production
    workspace:
      host: https://your-prod-workspace.azuredatabricks.net

resources:
  jobs:
    etl_job:
      name: "ETL Pipeline"
      tasks:
        - task_key: "run_notebook"
          notebook_task:
            notebook_path: ./notebooks/etl.py
```

```bash
# Deploy and run
databricks bundle deploy -t dev
databricks bundle run etl_job -t dev
databricks bundle destroy -t dev
```
