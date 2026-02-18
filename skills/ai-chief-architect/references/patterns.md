# Architecture Patterns Catalog

## Structural Patterns

### Monolithic
- **When:** Small team, early-stage product, simple domain
- **Trade-offs:** Simple deployment, but scaling and team autonomy limited
- **Evolution:** Modular monolith → strangler fig → microservices

### Microservices
- **When:** Multiple teams, independent deployability needed, complex domain
- **Trade-offs:** Team autonomy and scalability, but operational complexity high
- **Prerequisites:** CI/CD maturity, observability, service mesh or API gateway

### Modular Monolith
- **When:** Want clean boundaries without distributed systems overhead
- **Trade-offs:** Best of both worlds early on, but requires discipline on module boundaries

## Communication Patterns

### Synchronous (Request/Response)
- REST, gRPC, GraphQL
- Simple mental model, but creates temporal coupling
- Use for: queries, commands needing immediate response

### Asynchronous (Event-Driven)
- Message queues (SQS, RabbitMQ), event streams (Kafka, EventBridge)
- Decoupled, resilient, but harder to debug and reason about
- Use for: notifications, data sync, long-running processes

### Saga Pattern
- Orchestration: central coordinator manages steps
- Choreography: services react to events independently
- Use for: distributed transactions across service boundaries

## Data Patterns

### CQRS (Command Query Responsibility Segregation)
- Separate read/write models for different optimization
- Use when: read and write workloads have very different characteristics

### Event Sourcing
- Store events, not state; derive current state by replaying
- Use when: audit trail critical, temporal queries needed, undo/replay required

### Database per Service
- Each service owns its data store
- Enforces loose coupling but complicates cross-service queries

## Resilience Patterns

### Circuit Breaker
- Prevent cascading failures by failing fast when downstream is unhealthy
- States: closed → open → half-open

### Bulkhead
- Isolate resources so one failing component doesn't exhaust shared resources

### Retry with Backoff
- Exponential backoff + jitter for transient failures
- Always set max retries and timeouts

### Timeout
- Every external call must have a timeout; no exceptions

## Deployment Patterns

### Blue-Green
- Two identical environments; switch traffic atomically
- Simple rollback, but double infrastructure cost

### Canary
- Route small percentage of traffic to new version
- Gradual rollout with automated rollback on error budget breach

### Feature Flags
- Decouple deployment from release
- Enable trunk-based development and progressive delivery
