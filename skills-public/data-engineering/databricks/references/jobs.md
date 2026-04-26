# Databricks Jobs Reference

## Job Concepts

```
Job
├── Schedule (cron / file arrival / manual)
├── Parameters (key-value, passed to tasks)
└── Tasks
    ├── Task 1: Notebook / Python / SQL / DLT / dbt / JAR / Spark Submit
    ├── Task 2: depends_on: [Task 1]
    └── Task 3: depends_on: [Task 1]  ← parallel with Task 2
```

## Task Types

| Task Type | Use Case |
|-----------|----------|
| `notebook_task` | Run a Databricks notebook |
| `python_wheel_task` | Run a Python wheel package |
| `spark_python_task` | Run a `.py` script |
| `sql_task` | Run SQL query / dashboard / alert |
| `dbt_task` | Run dbt models |
| `pipeline_task` | Trigger a DLT pipeline |
| `run_job_task` | Trigger another job |
| `condition_task` | Branch logic (if/else) |
| `for_each_task` | Loop over a list of inputs |

## Create Job via SDK

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import (
    Task, NotebookTask, PythonWheelTask, SqlTask,
    JobCluster, ClusterSpec, GitSource, CronSchedule,
    JobEmailNotifications, WebhookNotifications
)

w = WorkspaceClient()

job = w.jobs.create(
    name="Daily ETL Pipeline",

    # Job-level cluster (shared by all tasks)
    job_clusters=[
        JobCluster(
            job_cluster_key="main-cluster",
            new_cluster=ClusterSpec(
                spark_version="15.4.x-scala2.12",
                node_type_id="i3.xlarge",
                num_workers=4,
                data_security_mode="SINGLE_USER"
            )
        )
    ],

    tasks=[
        # Task 1: Ingest
        Task(
            task_key="ingest",
            job_cluster_key="main-cluster",
            notebook_task=NotebookTask(
                notebook_path="/Repos/main/notebooks/01_ingest",
                base_parameters={"env": "prod", "date": "{{job.start_time.iso_date}}"}
            ),
            timeout_seconds=3600,
            max_retries=2,
            retry_on_timeout=True,
        ),

        # Task 2: Transform (depends on ingest)
        Task(
            task_key="transform",
            depends_on=[{"task_key": "ingest"}],
            job_cluster_key="main-cluster",
            notebook_task=NotebookTask(
                notebook_path="/Repos/main/notebooks/02_transform"
            )
        ),

        # Task 3: SQL (depends on transform)
        Task(
            task_key="aggregate",
            depends_on=[{"task_key": "transform"}],
            sql_task=SqlTask(
                query={"query_id": "your-query-id"},
                warehouse_id="abc123def456"
            )
        ),
    ],

    # Schedule: daily at 6am Israel time
    schedule=CronSchedule(
        quartz_cron_expression="0 0 6 * * ?",
        timezone_id="Asia/Jerusalem",
        pause_status="UNPAUSED"
    ),

    # Notifications
    email_notifications=JobEmailNotifications(
        on_failure=["alerts@company.com"],
        on_success=["team@company.com"]
    ),

    # Parameters accessible in all tasks
    parameters=[
        {"name": "env", "default": "prod"},
        {"name": "catalog", "default": "my_catalog"},
    ],

    # Max concurrent runs
    max_concurrent_runs=1,
)

print(f"Created job: {job.job_id}")
```

## Task Values (Pass Data Between Tasks)

```python
# In Task 1 (ingest) - set value
count = df.count()
dbutils.jobs.taskValues.set(key="row_count", value=count)
dbutils.jobs.taskValues.set(key="run_date", value="2024-01-15")

# In Task 2 (transform) - get value
count = dbutils.jobs.taskValues.get(taskKey="ingest", key="row_count", default=0)
run_date = dbutils.jobs.taskValues.get(taskKey="ingest", key="run_date")
```

## Dynamic Parameters (Job System Variables)

```python
# In base_parameters, use these placeholders:
# {{job.id}}                    - Job ID
# {{job.run_id}}                - Run ID
# {{job.start_time.iso_date}}   - YYYY-MM-DD
# {{job.start_time.epoch_ms}}   - Epoch milliseconds
# {{tasks.<task_key>.run_id}}   - Specific task run ID

# Example:
NotebookTask(
    notebook_path="/notebooks/etl",
    base_parameters={
        "date": "{{job.start_time.iso_date}}",
        "run_id": "{{job.run_id}}"
    }
)
```

## Trigger & Monitor Jobs

```python
# Run now (manual trigger)
run = w.jobs.run_now(job_id=12345)

# Run with custom parameters
run = w.jobs.run_now(
    job_id=12345,
    job_parameters={"env": "staging", "date": "2024-01-15"}
)

# Wait for completion
result = w.jobs.wait_get_run_job_terminated_or_skipped(run_id=run.run_id)
print(result.state.result_state)  # SUCCESS, FAILED, CANCELED

# Get run status
run_info = w.runs.get(run_id=run.run_id)
print(run_info.state.life_cycle_state)  # RUNNING, TERMINATED, etc.

# List runs
for run in w.runs.list(job_id=12345, limit=10):
    print(run.run_id, run.state.result_state, run.start_time)

# Cancel run
w.runs.cancel(run_id=run.run_id)
```

## Repair & Retry

```python
# Re-run only failed tasks (preserve successful task results)
w.runs.repair(
    run_id=failed_run_id,
    rerun_all_failed_tasks=True
)

# Re-run specific tasks
w.runs.repair(
    run_id=failed_run_id,
    rerun_tasks=["transform", "aggregate"]
)
```

## For Each Task (Loop)

```python
# Job config - ForEach task
Task(
    task_key="process_regions",
    for_each_task={
        "inputs": '["us-east", "eu-west", "ap-south"]',
        "concurrency": 3,
        "task": {
            "task_key": "process_region",
            "notebook_task": {
                "notebook_path": "/notebooks/process_region",
                "base_parameters": {"region": "{{input}}"}
            }
        }
    }
)
```

## Condition Task (Branching)

```python
# If/else branching
Task(
    task_key="check_data",
    condition_task={
        "left": "{{tasks.ingest.values.row_count}}",
        "op": "GREATER_THAN",
        "right": "0"
    }
),
Task(
    task_key="transform",
    depends_on=[{"task_key": "check_data", "outcome": "true"}],
    ...
),
Task(
    task_key="notify_empty",
    depends_on=[{"task_key": "check_data", "outcome": "false"}],
    ...
)
```

## Job Schedules

```python
# Cron examples
"0 0 6 * * ?"          # Every day at 6:00 AM
"0 0 6 ? * MON-FRI"    # Weekdays at 6:00 AM
"0 0 */2 * * ?"        # Every 2 hours
"0 30 8 1 * ?"         # 1st of every month at 8:30 AM

# File arrival trigger
schedule={
    "file_arrival": {
        "url": "dbfs:/mnt/landing/orders/",
        "min_time_between_triggers_seconds": 3600
    }
}

# Continuous (streaming jobs)
trigger={"continuous": {"pause_status": "UNPAUSED"}}
```

## Job Notifications

```python
# Email + webhook
email_notifications=JobEmailNotifications(
    on_start=["team@company.com"],
    on_success=["team@company.com"],
    on_failure=["alerts@company.com", "oncall@company.com"],
    no_alert_for_skipped_runs=True
),
webhook_notifications={
    "on_failure": [{"id": "slack-webhook-id"}]
}
```

## Databricks Asset Bundles (Jobs as Code)

```yaml
# databricks.yml
resources:
  jobs:
    daily_etl:
      name: "Daily ETL"
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: "Asia/Jerusalem"
      job_clusters:
        - job_cluster_key: main
          new_cluster:
            spark_version: 15.4.x-scala2.12
            node_type_id: i3.xlarge
            num_workers: 4
      tasks:
        - task_key: ingest
          job_cluster_key: main
          notebook_task:
            notebook_path: ./notebooks/01_ingest.py
            base_parameters:
              env: ${var.env}
        - task_key: transform
          depends_on:
            - task_key: ingest
          job_cluster_key: main
          notebook_task:
            notebook_path: ./notebooks/02_transform.py
```

## Common Patterns

```python
# Idempotent job - safe to re-run
# Use MERGE instead of INSERT, track processed dates

# Check if already processed
result = spark.sql(f"""
    SELECT COUNT(*) as cnt
    FROM my_catalog.audit.job_runs
    WHERE run_date = '{run_date}' AND status = 'SUCCESS'
""").collect()[0]["cnt"]

if result > 0:
    dbutils.notebook.exit("Already processed")

# Process...

# Mark complete
spark.sql(f"""
    INSERT INTO my_catalog.audit.job_runs
    VALUES ('{run_date}', 'SUCCESS', current_timestamp())
""")
```

## Monitoring via System Tables

```sql
-- Job run history
SELECT
  job_id,
  run_id,
  result_state,
  start_time,
  end_time,
  datediff(second, start_time, end_time) as duration_secs
FROM system.lakeflow.job_runs
WHERE start_time >= current_date - 7
ORDER BY start_time DESC;

-- Failed jobs
SELECT job_id, run_id, result_state, error_message
FROM system.lakeflow.job_task_runs
WHERE result_state = 'FAILED'
  AND start_time >= current_date - 1;
```
