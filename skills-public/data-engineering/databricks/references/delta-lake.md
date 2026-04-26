# Delta Lake Reference

## Core Operations

```sql
-- Read
SELECT * FROM my_catalog.my_schema.orders WHERE amount > 100;

-- Insert
INSERT INTO my_catalog.my_schema.orders VALUES (1, 100, 99.9, current_timestamp());

-- Update
UPDATE my_catalog.my_schema.orders SET amount = 150 WHERE order_id = 1;

-- Delete
DELETE FROM my_catalog.my_schema.orders WHERE order_id = 1;

-- Upsert (MERGE)
MERGE INTO my_catalog.my_schema.orders AS target
USING updates AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

## Python API

```python
from delta.tables import DeltaTable

# Load
dt = DeltaTable.forName(spark, "my_catalog.my_schema.orders")

# Merge
dt.alias("target").merge(
    updates_df.alias("source"),
    "target.order_id = source.order_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Update
dt.update(condition="order_id = 1", set={"amount": "150"})

# Delete
dt.delete("order_id = 1")
```

## Time Travel

```sql
-- Query by version
SELECT * FROM my_catalog.my_schema.orders VERSION AS OF 5;

-- Query by timestamp
SELECT * FROM my_catalog.my_schema.orders TIMESTAMP AS OF '2024-01-15 10:00:00';

-- View history
DESCRIBE HISTORY my_catalog.my_schema.orders;

-- Restore to version
RESTORE TABLE my_catalog.my_schema.orders TO VERSION AS OF 5;
RESTORE TABLE my_catalog.my_schema.orders TO TIMESTAMP AS OF '2024-01-15';
```

## Optimization

```sql
-- Compact small files
OPTIMIZE my_catalog.my_schema.orders;

-- Optimize + Z-ORDER (collocate related data)
OPTIMIZE my_catalog.my_schema.orders
ZORDER BY (customer_id, created_at);

-- Vacuum (remove old files - default 7 day retention)
VACUUM my_catalog.my_schema.orders;
VACUUM my_catalog.my_schema.orders RETAIN 168 HOURS;  -- 7 days

-- Analyze (update stats for query optimizer)
ANALYZE TABLE my_catalog.my_schema.orders COMPUTE STATISTICS;
ANALYZE TABLE my_catalog.my_schema.orders COMPUTE STATISTICS FOR COLUMNS order_id, amount;
```

## Table Properties & Schema

```sql
-- Describe table
DESCRIBE TABLE EXTENDED my_catalog.my_schema.orders;

-- Add column
ALTER TABLE my_catalog.my_schema.orders ADD COLUMN status STRING;

-- Rename column (requires delta.columnMapping.mode = 'name')
ALTER TABLE my_catalog.my_schema.orders RENAME COLUMN old_name TO new_name;

-- Change data type (widening only)
ALTER TABLE my_catalog.my_schema.orders ALTER COLUMN amount TYPE DECIMAL(18,2);

-- Set table properties
ALTER TABLE my_catalog.my_schema.orders
SET TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');

-- Enable Change Data Feed
ALTER TABLE my_catalog.my_schema.orders
SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

## Change Data Feed (CDF)

```python
# Read CDF changes
changes = spark.read.format("delta") \
    .option("readChangeFeed", "true") \
    .option("startingVersion", 5) \
    .table("my_catalog.my_schema.orders")

# _change_type: insert, update_preimage, update_postimage, delete
changes.filter("_change_type = 'insert'").show()
```

## Streaming

```python
# Read stream from Delta
stream = spark.readStream.table("my_catalog.my_schema.raw_orders")

# Write stream to Delta
stream.writeStream \
    .outputMode("append") \
    .option("checkpointLocation", "/Volumes/my_catalog/checkpoints/orders") \
    .toTable("my_catalog.my_schema.orders")

# Trigger options
.trigger(processingTime="1 minute")   # micro-batch
.trigger(availableNow=True)           # process all, then stop
.trigger(once=True)                   # single micro-batch
```

## Liquid Clustering (new alternative to Z-ORDER)

```sql
-- Create with clustering
CREATE TABLE my_catalog.my_schema.orders
CLUSTER BY (customer_id, created_at)
AS SELECT * FROM source_table;

-- Cluster existing table
ALTER TABLE my_catalog.my_schema.orders
CLUSTER BY (customer_id);

-- Optimize with liquid clustering (no ZORDER needed)
OPTIMIZE my_catalog.my_schema.orders;
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Too many small files | Run `OPTIMIZE` regularly |
| Slow queries after MERGE | Run `OPTIMIZE ZORDER BY (join_key)` |
| Disk space growing | Run `VACUUM` (respect retention window) |
| Schema mismatch on write | Add `.option("mergeSchema", "true")` |
| Concurrent write conflicts | Use idempotent writes or retry logic |
