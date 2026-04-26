# Lakebase - Operational Database on the Lakehouse

## What is Lakebase?
Lakebase is Databricks' managed operational database that brings OLTP workloads (low-latency reads/writes) directly into the Lakehouse. It provides a Postgres-compatible SQL interface while storing data governed by Unity Catalog.

## Key Characteristics
- **Postgres-compatible** - connect with any Postgres client (psycopg2, JDBC, DBeaver, etc.)
- **UC governed** - same permissions, lineage, and tags as Delta Lake tables
- **Low-latency** - row-level upserts without full Parquet file rewrites
- **Serverless** - no cluster to manage, auto-scaling
- **Unified** - query Lakebase tables alongside Delta tables in the same SQL context

## When to Use Lakebase vs Delta Lake

| Use Case | Use Lakebase | Use Delta Lake |
|---|---|---|
| App backend (CRUD) | ✅ | ❌ |
| Low-latency lookups (<10ms) | ✅ | ❌ |
| Large analytical queries | ❌ | ✅ |
| Streaming ingestion | ❌ | ✅ |
| Data warehouse | ❌ | ✅ |
| Feature store (online) | ✅ | ❌ |

## Creating a Lakebase Instance

```sql
-- Via SQL (in Databricks SQL Editor)
CREATE DATABASE lakebase_instance
  CATALOG = 'my_catalog'
  SCHEMA = 'operational'
  TYPE = LAKEBASE;
```

## Working with Lakebase Tables

```sql
-- Create table (Postgres DDL syntax)
CREATE TABLE orders (
  order_id    SERIAL PRIMARY KEY,
  customer_id INT NOT NULL,
  status      TEXT DEFAULT 'pending',
  amount      DECIMAL(10,2),
  created_at  TIMESTAMP DEFAULT NOW(),
  updated_at  TIMESTAMP DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- Upsert (ON CONFLICT)
INSERT INTO orders (order_id, customer_id, status, amount)
VALUES (1001, 42, 'shipped', 99.99)
ON CONFLICT (order_id)
DO UPDATE SET
  status = EXCLUDED.status,
  updated_at = NOW();

-- Standard CRUD
UPDATE orders SET status = 'delivered' WHERE order_id = 1001;
DELETE FROM orders WHERE status = 'cancelled' AND created_at < NOW() - INTERVAL '30 days';
```

## Connecting from Python

```python
import psycopg2

conn = psycopg2.connect(
    host="<lakebase-endpoint>.databricks.com",
    port=5432,
    database="my_catalog.operational",
    user="token",
    password="<databricks-pat>"
)

cur = conn.cursor()
cur.execute("SELECT * FROM orders WHERE customer_id = %s", (42,))
rows = cur.fetchall()
conn.close()
```

## Querying Lakebase from Spark (Federated Query)

```python
# Read Lakebase table in Spark via JDBC
df = spark.read.jdbc(
    url="jdbc:postgresql://<lakebase-endpoint>:5432/my_catalog.operational",
    table="orders",
    properties={"user": "token", "password": dbutils.secrets.get("scope", "pat")}
)

# Join with Delta Lake table
delta_customers = spark.read.table("my_catalog.analytics.dim_customers")
result = df.join(delta_customers, "customer_id")
```

## Unity Catalog Governance

```sql
-- Lakebase tables appear in UC like any other table
SHOW TABLES IN my_catalog.operational;

-- Grant access
GRANT SELECT ON TABLE my_catalog.operational.orders TO `analyst@company.com`;
GRANT INSERT, UPDATE ON TABLE my_catalog.operational.orders TO `app_service_principal`;

-- Lineage tracked automatically in UC
DESCRIBE EXTENDED my_catalog.operational.orders;
```

## Best Practices
- Use Lakebase for application state, feature serving, and real-time lookups
- Use Delta Lake for analytics, reporting, and ML training data
- Always define primary keys - required for upsert semantics
- Use connection pooling (PgBouncer or similar) for high-throughput apps
- Monitor with UC system tables: `system.lakebase.query_history`
