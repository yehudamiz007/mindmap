# Zerobus - Real-Time Streaming Message Bus

## What is Zerobus?
Zerobus is Databricks' fully managed, Kafka-compatible message bus built into the Lakehouse. It eliminates the need for a separate Kafka/Confluent cluster while providing native integration with Delta Live Tables and Spark Structured Streaming.

## Key Features
- **Kafka-compatible API** - drop-in replacement, no code changes needed
- **Serverless** - no brokers to manage, auto-scaling
- **UC governed** - topics are Unity Catalog assets with lineage and RBAC
- **Exactly-once semantics** - built-in deduplication
- **Native DLT integration** - use Zerobus topics as DLT sources/sinks directly
- **Low latency** - sub-second end-to-end delivery

## Topics as UC Assets

```sql
-- Create a Zerobus topic (appears as UC asset)
CREATE TOPIC my_catalog.streaming.order_events
  PARTITIONS = 8
  RETENTION_MS = 604800000;  -- 7 days

-- Grant access
GRANT READ ON TOPIC my_catalog.streaming.order_events TO `consumer_group`;
GRANT WRITE ON TOPIC my_catalog.streaming.order_events TO `producer_app`;

-- List topics
SHOW TOPICS IN my_catalog.streaming;
```

## Producing Messages (Kafka API)

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=["<zerobus-endpoint>:9092"],
    security_protocol="SASL_SSL",
    sasl_mechanism="PLAIN",
    sasl_plain_username="token",
    sasl_plain_password="<databricks-pat>",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

producer.send("my_catalog.streaming.order_events", {
    "order_id": 1001,
    "customer_id": 42,
    "event": "shipped",
    "timestamp": "2026-04-26T12:00:00Z"
})
producer.flush()
```

## Consuming from Spark Structured Streaming

```python
# Read from Zerobus (Kafka-compatible)
df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "<zerobus-endpoint>:9092")
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "PLAIN")
    .option("kafka.sasl.jaas.config",
            f'org.apache.kafka.common.security.plain.PlainLoginModule required '
            f'username="token" password="{pat}";')
    .option("subscribe", "my_catalog.streaming.order_events")
    .option("startingOffsets", "latest")
    .load()
)

# Parse JSON payload
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, IntegerType

schema = StructType() \
    .add("order_id", IntegerType()) \
    .add("customer_id", IntegerType()) \
    .add("event", StringType())

parsed = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# Write to Delta Lake
(parsed.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/order_events")
    .toTable("my_catalog.analytics.order_events")
)
```

## Zerobus with Delta Live Tables (Native Integration)

```python
import dlt
from pyspark.sql.functions import from_json, col

# DLT reads directly from Zerobus topic
@dlt.table(comment="Raw order events from Zerobus")
def raw_order_events():
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", spark.conf.get("zerobus.endpoint"))
        .option("subscribe", "my_catalog.streaming.order_events")
        .load()
    )

@dlt.table(comment="Parsed order events")
@dlt.expect("valid_order_id", "order_id IS NOT NULL")
def parsed_order_events():
    schema = "order_id INT, customer_id INT, event STRING, timestamp TIMESTAMP"
    return (
        dlt.read_stream("raw_order_events")
        .select(from_json(col("value").cast("string"), schema).alias("d"))
        .select("d.*")
    )
```

## Writing Back to Zerobus from Spark

```python
# Produce from Spark to Zerobus topic
(result_df.writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "<zerobus-endpoint>:9092")
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "PLAIN")
    .option("kafka.sasl.jaas.config", f'... username="token" password="{pat}";')
    .option("topic", "my_catalog.streaming.enriched_events")
    .option("checkpointLocation", "/checkpoints/enriched_out")
    .start()
)
```

## Monitoring

```sql
-- Consumer lag (via system tables)
SELECT topic, partition, consumer_group, lag
FROM system.zerobus.consumer_lag
WHERE topic = 'my_catalog.streaming.order_events'
ORDER BY lag DESC;

-- Topic throughput
SELECT topic, messages_in_per_sec, bytes_in_per_sec
FROM system.zerobus.topic_metrics
WHERE window_start > NOW() - INTERVAL 1 HOUR;
```

## Best Practices
- Name topics with full UC path: `catalog.schema.topic_name`
- Set `RETENTION_MS` based on consumer SLA, not storage limits (serverless)
- Use DLT for stateful stream processing - handles checkpointing automatically
- Monitor consumer lag via `system.zerobus.consumer_lag`
- Use `startingOffsets = "earliest"` for backfill, `"latest"` for real-time
- Zerobus supports compacted topics for CDC (Change Data Capture) use cases
