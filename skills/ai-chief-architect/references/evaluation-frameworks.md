# Decision & Evaluation Frameworks

## Architecture Trade-off Analysis Method (ATAM)

Structured approach for evaluating architecture against quality attributes:

1. **Present architecture** — describe the system and its drivers
2. **Identify quality attribute scenarios** — concrete, measurable scenarios
3. **Analyze decisions** — map architectural decisions to scenarios
4. **Identify risks & trade-offs** — where do decisions conflict?

## Weighted Scoring Matrix

For technology/vendor selection:

```
| Criteria          | Weight | Option A | Option B | Option C |
|-------------------|--------|----------|----------|----------|
| Performance       | 0.25   | 8 (2.0)  | 6 (1.5)  | 7 (1.75) |
| Team expertise    | 0.20   | 9 (1.8)  | 5 (1.0)  | 7 (1.4)  |
| Cost              | 0.20   | 6 (1.2)  | 9 (1.8)  | 7 (1.4)  |
| Ecosystem         | 0.15   | 8 (1.2)  | 7 (1.05) | 6 (0.9)  |
| Scalability       | 0.10   | 7 (0.7)  | 8 (0.8)  | 9 (0.9)  |
| Vendor lock-in    | 0.10   | 5 (0.5)  | 9 (0.9)  | 7 (0.7)  |
| TOTAL             |        | 7.4      | 7.05     | 7.05     |
```

Score 1-10 per criteria, multiply by weight, sum for total.

## RFC Process

For team-wide architectural decisions:

```markdown
# RFC-{number}: {Title}
**Author:** {name}  |  **Status:** Draft | Review | Accepted | Rejected
**Reviewers:** {names}  |  **Due:** {date}

## Summary
One paragraph: what and why.

## Motivation
Why is this needed? What problem does it solve?

## Detailed Design
Technical details, diagrams, API changes.

## Alternatives Considered
What else was evaluated and why it was rejected.

## Migration Plan
How do we get from here to there?

## Open Questions
Unresolved issues for discussion.
```

## Cost Analysis Template

```
| Component        | Monthly Cost | Annual Cost | Notes              |
|-----------------|-------------|------------|---------------------|
| Compute          | $X          | $Y         | N instances × type  |
| Database         | $X          | $Y         | Storage + IOPS      |
| Networking       | $X          | $Y         | Data transfer       |
| Observability    | $X          | $Y         | Logs + metrics      |
| Licensing        | $X          | $Y         | Per-seat/usage      |
| TOTAL            | $X          | $Y         |                     |
```

Compare against: current costs, projected growth (6mo, 1yr, 3yr), and reserved/committed pricing.

## Non-Functional Requirements Template

| Attribute | Target | Measurement |
|-----------|--------|-------------|
| Availability | 99.9% (8.76h downtime/yr) | Uptime monitoring |
| Latency (p50) | <100ms | APM |
| Latency (p99) | <500ms | APM |
| Throughput | 10k req/s | Load testing |
| Recovery Time (RTO) | <1h | DR drill |
| Recovery Point (RPO) | <5min | Backup verification |
| Data retention | 7 years | Compliance audit |
