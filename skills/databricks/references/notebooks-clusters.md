# Notebooks & Clusters Reference

## Magic Commands

| Command | Description |
|---------|-------------|
| `%python` | Switch cell to Python |
| `%sql` | Switch cell to SQL |
| `%scala` | Switch cell to Scala |
| `%r` | Switch cell to R |
| `%sh` | Run shell command |
| `%md` | Markdown cell |
| `%run ./other_notebook` | Run another notebook inline |
| `%pip install package` | Install Python package (restart kernel after) |
| `%conda install package` | Install via conda |
| `%fs ls /path` | DBFS file system shortcut |
| `%fs cp /src /dst` | Copy files in DBFS |

## dbutils

```python
# File system
dbutils.fs.ls("/Volumes/my_catalog/my_schema/files/")
dbutils.fs.cp("/source/path", "/dest/path")
dbutils.fs.rm("/path/to/file", recurse=True)
dbutils.fs.mkdirs("/new/path")
dbutils.fs.head("/path/to/file.txt", maxBytes=1024)

# Secrets
secret = dbutils.secrets.get(scope="my-scope", key="api-key")
dbutils.secrets.listScopes()
dbutils.secrets.list("my-scope")

# Widgets (notebook parameters)
dbutils.widgets.text("start_date", "2024-01-01", "Start Date")
dbutils.widgets.dropdown("env", "prod", ["dev", "staging", "prod"])
dbutils.widgets.combobox("table", "orders", ["orders", "customers"])
start = dbutils.widgets.get("start_date")
dbutils.widgets.removeAll()

# Notebook utilities
result = dbutils.notebook.run("./child_notebook", timeout_seconds=300,
                               arguments={"param": "value"})
dbutils.notebook.exit("success")  # Return value from notebook

# Library management
dbutils.library.restartPython()  # After %pip install
```

## Widgets in SQL

```sql
-- Create widget
CREATE WIDGET TEXT catalog DEFAULT 'my_catalog';

-- Use widget
SELECT * FROM IDENTIFIER(:catalog || '.sales.orders')
WHERE created_at > :start_date;
```

## Cluster Configuration

### Cluster Types

| Type | Use Case |
|------|----------|
| All-purpose | Interactive notebooks, development |
| Job cluster | Automated workflows, cost-efficient |
| SQL Warehouse | SQL analytics, dashboards, Genie |

### Key Config Options

```json
{
  "spark_version": "15.4.x-scala2.12",
  "node_type_id": "i3.xlarge",
  "num_workers": 4,
  "autoscale": {
    "min_workers": 2,
    "max_workers": 10
  },
  "spark_conf": {
    "spark.databricks.io.cache.enabled": "true",
    "spark.sql.shuffle.partitions": "200"
  },
  "custom_tags": {
    "team": "data-engineering",
    "project": "etl"
  },
  "data_security_mode": "SINGLE_USER",
  "runtime_engine": "PHOTON"
}
```

### Data Security Modes

| Mode | UC Support | Multi-user |
|------|------------|------------|
| `SINGLE_USER` | Full UC | No |
| `USER_ISOLATION` | Full UC | Yes (shared cluster) |
| `NONE` | Legacy (no UC) | - |

### Instance Pools

```python
# Create pool via SDK
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

pool = w.instance_pools.create(
    instance_pool_name="my-pool",
    node_type_id="i3.xlarge",
    min_idle_instances=2,
    max_capacity=20,
    idle_instance_autotermination_minutes=30
)
```

## Spark Config Tips

```python
# Check current config
spark.conf.get("spark.sql.shuffle.partitions")

# Set config
spark.conf.set("spark.sql.shuffle.partitions", "400")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(50 * 1024 * 1024))  # 50MB

# Useful settings
spark.conf.set("spark.databricks.io.cache.enabled", "true")      # SSD caching
spark.conf.set("spark.sql.adaptive.enabled", "true")              # AQE (default on)
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
```

## Notebook Versioning & Repos

```
# Clone repo
Repos > Add Repo > paste GitHub/GitLab URL

# Common Git workflow from notebook
%sh
git status
git pull origin main
git add .
git commit -m "update notebook"
git push
```

## Display & Visualization

```python
# Display DataFrame (rich table UI)
display(df)

# Display with options
display(df.limit(100))

# Matplotlib
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1,2,3], [4,5,6])
display(fig)  # renders inline

# Plotly
import plotly.express as px
fig = px.bar(df.toPandas(), x="category", y="revenue")
fig.show()
```
