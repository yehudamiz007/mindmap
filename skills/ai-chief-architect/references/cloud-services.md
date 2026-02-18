# Cloud Service Selection Guide

## Compute

| Need | AWS | GCP | Azure |
|------|-----|-----|-------|
| Containers (managed K8s) | EKS | GKE | AKS |
| Serverless functions | Lambda | Cloud Functions | Azure Functions |
| Serverless containers | Fargate / App Runner | Cloud Run | Container Apps |
| VMs | EC2 | Compute Engine | Virtual Machines |

**Selection criteria:** Team K8s expertise, cold start tolerance, cost model (per-request vs reserved), vendor lock-in tolerance.

## Databases

| Type | AWS | GCP | Azure | OSS Alternative |
|------|-----|-----|-------|----------------|
| Relational | RDS/Aurora | Cloud SQL/AlloyDB | Azure SQL | PostgreSQL, MySQL |
| Document | DynamoDB | Firestore | Cosmos DB | MongoDB |
| Graph | Neptune | — | Cosmos (Gremlin) | Neo4j |
| Time-series | Timestream | — | ADX | InfluxDB, TimescaleDB |
| Vector | — | — | — | Pinecone, Weaviate, pgvector |
| Cache | ElastiCache | Memorystore | Azure Cache | Redis, Valkey |

**Selection criteria:** Query patterns, consistency needs, scale requirements, cost at volume, operational burden.

## Messaging & Streaming

| Need | AWS | GCP | Azure | OSS |
|------|-----|-----|-------|-----|
| Queue | SQS | Pub/Sub | Service Bus | RabbitMQ |
| Stream | Kinesis / MSK | Pub/Sub | Event Hubs | Kafka |
| Event bus | EventBridge | Eventarc | Event Grid | — |

## Storage

| Need | AWS | GCP | Azure |
|------|-----|-----|-------|
| Object | S3 | Cloud Storage | Blob Storage |
| File | EFS | Filestore | Azure Files |
| Block | EBS | Persistent Disk | Managed Disks |

## Networking

| Need | AWS | GCP | Azure |
|------|-----|-----|-------|
| CDN | CloudFront | Cloud CDN | Azure CDN / Front Door |
| API Gateway | API Gateway | Apigee / API Gateway | API Management |
| Service mesh | App Mesh | Anthos SM | — (use Istio/Linkerd) |
| DNS | Route 53 | Cloud DNS | Azure DNS |

## Decision Framework

1. **Start with requirements**, not services
2. **Prefer managed** over self-hosted unless cost or control demands otherwise
3. **Evaluate lock-in** — how hard is it to migrate away?
4. **Check regional availability** for compliance needs
5. **Model costs** at current AND projected scale
6. **Consider team expertise** — the best tool your team can't operate isn't the best tool
