# Databricks Clusters Reference

## Cluster Types

| Type | Use Case | Cost |
|------|----------|------|
| All-purpose | Interactive notebooks, development, ad-hoc | Higher (runs until terminated) |
| Job cluster | Automated workflows, pipelines | Lower (terminates after job) |
| SQL Warehouse | SQL analytics, dashboards, Genie | Per-query billing |
| DLT cluster | Delta Live Tables (auto-managed) | Managed by DLT |

## Cluster Config

### Key Fields

```json
{
  "cluster_name": "my-cluster",
  "spark_version": "15.4.x-scala2.12",
  "node_type_id": "i3.xlarge",
  "driver_node_type_id": "i3.xlarge",
  "num_workers": 4,
  "autoscale": {
    "min_workers": 2,
    "max_workers": 10
  },
  "autotermination_minutes": 30,
  "runtime_engine": "PHOTON",
  "data_security_mode": "SINGLE_USER",
  "single_user_name": "user@company.com",
  "spark_conf": {
    "spark.sql.shuffle.partitions": "400",
    "spark.databricks.io.cache.enabled": "true"
  },
  "spark_env_vars": {
    "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
  },
  "custom_tags": {
    "team": "data-eng",
    "project": "etl"
  },
  "init_scripts": [
    { "workspace": { "destination": "/Repos/main/init/setup.sh" } },
    { "volumes": { "destination": "/Volumes/my_catalog/scripts/init.sh" } }
  ],
  "libraries": [
    { "pypi": { "package": "pandas==2.0.0" } },
    { "maven": { "coordinates": "com.databricks:spark-csv_2.12:1.5.0" } }
  ]
}
```

### Data Security Modes

| Mode | Unity Catalog | Multi-user | Notes |
|------|--------------|------------|-------|
| `SINGLE_USER` | Full support | No | Recommended for UC |
| `USER_ISOLATION` | Full support | Yes (shared) | Each user isolated |
| `NONE` | Not supported | - | Legacy only |

### Runtime Engine

- **PHOTON** - Vectorized C++ engine, 2-10x faster for SQL/ETL, included with Premium
- **STANDARD** - Default Spark JVM engine

## Cluster Policies

Policies enforce configuration constraints and simplify cluster creation:

```python
from databricks.sdk import WorkspaceClient
import json

w = WorkspaceClient()

policy = w.cluster_policies.create(
    name="Data Engineering Policy",
    definition=json.dumps({
        "spark_version": {
            "type": "allowlist",
            "values": ["15.4.x-scala2.12", "14.3.x-scala2.12"]
        },
        "node_type_id": {
            "type": "allowlist",
            "values": ["i3.xlarge", "i3.2xlarge"]
        },
        "autotermination_minutes": {
            "type": "range",
            "minValue": 10,
            "maxValue": 120,
            "defaultValue": 30
        },
        "custom_tags.team": {
            "type": "fixed",
            "value": "data-engineering"
        }
    })
)
```

## Instance Pools

Pre-warmed instances to reduce cluster startup time:

```python
pool = w.instance_pools.create(
    instance_pool_name="fast-start-pool",
    node_type_id="i3.xlarge",
    min_idle_instances=2,
    max_capacity=50,
    idle_instance_autotermination_minutes=30,
    preloaded_spark_versions=["15.4.x-scala2.12"],
    aws_attributes={  # or azure_attributes / gcp_attributes
        "availability": "ON_DEMAND"
    }
)

# Use pool in cluster config
cluster_config = {
    "instance_pool_id": pool.instance_pool_id,
    "driver_instance_pool_id": pool.instance_pool_id,
    ...
}
```

## Cluster Management via SDK

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import CreateCluster, AutoScale

w = WorkspaceClient()

# Create cluster
cluster = w.clusters.create(
    cluster_name="dev-cluster",
    spark_version="15.4.x-scala2.12",
    node_type_id="i3.xlarge",
    autoscale=AutoScale(min_workers=2, max_workers=8),
    autotermination_minutes=60
)

# Wait until running
w.clusters.wait_get_cluster_running(cluster_id=cluster.cluster_id)

# Start / stop / restart
w.clusters.start(cluster_id=cluster.cluster_id)
w.clusters.terminate(cluster_id=cluster.cluster_id)
w.clusters.restart(cluster_id=cluster.cluster_id)
w.clusters.delete(cluster_id=cluster.cluster_id)

# List clusters
for c in w.clusters.list():
    print(c.cluster_name, c.state)

# Get cluster info
info = w.clusters.get(cluster_id="0101-abc123")
print(info.state, info.num_workers)
```

## Libraries

```python
# Install library on running cluster
w.libraries.install(
    cluster_id="0101-abc123",
    libraries=[
        {"pypi": {"package": "scikit-learn==1.3.0"}},
        {"pypi": {"package": "great-expectations"}},
        {"whl": {"path": "/Volumes/my_catalog/libs/my_lib-1.0.0-py3-none-any.whl"}},
    ]
)

# List installed libraries
statuses = w.libraries.cluster_status(cluster_id="0101-abc123")
for lib in statuses.library_statuses:
    print(lib.library, lib.status)

# Uninstall
w.libraries.uninstall(cluster_id="0101-abc123", libraries=[...])
```

## Cluster Events & Logs

```python
# Get cluster events
events = w.clusters.events(cluster_id="0101-abc123")
for event in events:
    print(event.timestamp, event.type, event.details)

# Driver logs location (configure in cluster)
# spark_conf: spark.databricks.cluster.profile = serverless
# Log delivery: S3/ADLS path in cluster config
```

## SQL Warehouses

```python
from databricks.sdk.service.sql import CreateWarehouseRequestWarehouseType

warehouse = w.warehouses.create(
    name="analytics-warehouse",
    cluster_size="Medium",          # 2X-Small to 4X-Large
    warehouse_type=CreateWarehouseRequestWarehouseType.PRO,  # or SERVERLESS, CLASSIC
    auto_stop_mins=10,
    min_num_clusters=1,
    max_num_clusters=5,
    enable_photon=True,
    enable_serverless_compute=True
)

# Start / stop
w.warehouses.start(id=warehouse.id)
w.warehouses.stop(id=warehouse.id)
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Cluster stuck in PENDING | Check instance availability, try different AZ |
| OOM errors | Increase driver/worker size, reduce shuffle partitions |
| Slow startup | Use instance pools with pre-warmed nodes |
| Library conflicts | Use isolated cluster or specify exact versions |
| UC access denied | Check `data_security_mode` = `SINGLE_USER` or `USER_ISOLATION` |
