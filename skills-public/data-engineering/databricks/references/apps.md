# Databricks Apps Reference

## What are Databricks Apps?

Databricks Apps lets you build and deploy web applications directly on the Databricks platform - no separate hosting needed. Apps run inside the workspace, have native access to Unity Catalog, SQL Warehouses, and cluster compute, and support OAuth/SSO out of the box.

**Supported frameworks:** Streamlit, Gradio, Dash, Flask, FastAPI, Shiny (R), and any Python web server.

## Project Structure

```
my-app/
├── app.py           # Entry point
├── app.yaml         # App configuration (required)
├── requirements.txt # Python dependencies
└── assets/          # Static files (optional)
```

### app.yaml

```yaml
command: ["python", "app.py"]

# For Streamlit
# command: ["streamlit", "run", "app.py", "--server.port", "8080"]

# For Gradio
# command: ["python", "app.py"]

# Environment variables (non-secret)
env:
  - name: APP_ENV
    value: production
  - name: WAREHOUSE_ID
    value: abc123def456

# Secret references from Databricks secret scopes
  - name: API_KEY
    valueFrom:
      secretScope: my-scope
      secretKey: api-key
```

## Streamlit App Example

```python
# app.py
import streamlit as st
from databricks import sql
from databricks.sdk import WorkspaceClient
import os

# SDK auto-authenticates inside Databricks Apps
w = WorkspaceClient()

st.title("Sales Dashboard")

@st.cache_data(ttl=300)
def get_revenue_data():
    with sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=f"/sql/1.0/warehouses/{os.environ['WAREHOUSE_ID']}",
        credentials_provider=lambda: {"token": w.config.token}
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT date_trunc('day', order_date) as day,
                       SUM(amount) as revenue
                FROM my_catalog.sales.orders
                WHERE order_date >= current_date - 30
                GROUP BY 1 ORDER BY 1
            """)
            return cursor.fetchall_arrow().to_pandas()

df = get_revenue_data()
st.line_chart(df.set_index("day")["revenue"])
st.dataframe(df)
```

## FastAPI App Example

```python
# app.py
from fastapi import FastAPI
from databricks.sdk import WorkspaceClient
import uvicorn, os

app = FastAPI()
w = WorkspaceClient()

@app.get("/api/tables")
def list_tables(catalog: str = "my_catalog", schema: str = "sales"):
    tables = w.tables.list(catalog_name=catalog, schema_name=schema)
    return [{"name": t.name, "type": t.table_type} for t in tables]

@app.get("/api/query")
def run_query(q: str):
    result = w.statement_execution.execute_statement(
        warehouse_id=os.environ["WAREHOUSE_ID"],
        statement=q,
        wait_timeout="30s"
    )
    return result.result.data_array

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Deploying Apps

### Via Databricks UI

1. Go to **Databricks > Apps** (sidebar)
2. Click **Create App**
3. Choose template or upload files
4. Configure compute and environment
5. Click **Deploy**

### Via CLI

```bash
# Install CLI
pip install databricks-cli

# Deploy app
databricks apps deploy my-app --source-code-path ./my-app

# List apps
databricks apps list

# Get app status
databricks apps get my-app

# Delete app
databricks apps delete my-app
```

### Via SDK

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import App, AppDeployment

w = WorkspaceClient()

# Create app
app = w.apps.create(
    name="my-sales-dashboard",
    description="Sales analytics dashboard"
)

# Deploy
deployment = w.apps.deploy(
    app_name="my-sales-dashboard",
    app_deployment=AppDeployment(
        source_code_path="/Repos/main/apps/sales-dashboard"
    )
)

# Wait for deployment
w.apps.wait_get_app_active(app_name="my-sales-dashboard")
print(w.apps.get("my-sales-dashboard").url)
```

### Via Databricks Asset Bundles (DAB)

```yaml
# databricks.yml
resources:
  apps:
    sales_dashboard:
      name: "sales-dashboard"
      description: "Sales analytics app"
      source_code_path: ./apps/sales-dashboard
      config:
        command: ["streamlit", "run", "app.py", "--server.port", "8080"]
        env:
          - name: WAREHOUSE_ID
            value: ${var.warehouse_id}
```

```bash
databricks bundle deploy -t prod
databricks bundle run sales_dashboard -t prod
```

## Authentication & Permissions

Apps use the **app's service principal** for Databricks access (not the deploying user).

```python
# Inside an app - auto-authenticated
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()  # No token needed - uses app identity

# Check current user/principal
me = w.current_user.me()
print(me.display_name)
```

```sql
-- Grant app service principal access to data
GRANT SELECT ON TABLE my_catalog.sales.orders
TO `my-sales-dashboard`;  -- app name = service principal name

GRANT USE CATALOG ON CATALOG my_catalog
TO `my-sales-dashboard`;
```

## Accessing Databricks Resources from App

```python
import os
from databricks.sdk import WorkspaceClient
from databricks import sql

w = WorkspaceClient()

# Run SQL query via Statement Execution API
result = w.statement_execution.execute_statement(
    warehouse_id=os.environ["WAREHOUSE_ID"],
    statement="SELECT * FROM my_catalog.sales.orders LIMIT 100",
    wait_timeout="30s"
)
rows = result.result.data_array

# Read Delta table via DBFS/Volumes
import pandas as pd
df = pd.read_parquet("/Volumes/my_catalog/my_schema/exports/report.parquet")

# Trigger a job
run = w.jobs.run_now(job_id=12345)
```

## Compute Options

| Option | Description | Best For |
|--------|-------------|----------|
| Serverless | Auto-managed, pay-per-use | Most apps |
| Classic | Dedicated VM | Heavy compute needs |

Apps with serverless compute scale to zero automatically.

## Tips

- Apps run as their own **service principal** - grant it UC permissions explicitly
- Use `DATABRICKS_HOST` and `DATABRICKS_TOKEN` env vars (auto-injected in apps)
- Store secrets in **Databricks Secret Scopes**, reference via `app.yaml`
- Use `@st.cache_data` (Streamlit) to avoid re-querying on every interaction
- Apps share the workspace URL: `https://<workspace>.azuredatabricks.net/apps/<app-name>`
- For Gradio: set `server_name="0.0.0.0"` and `server_port=8080`
- Apps support **custom domains** via workspace settings
