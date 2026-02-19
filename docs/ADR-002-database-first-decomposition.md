# ADR-002: Adopt Strangler Fig with Database-First Decomposition

**Title:** Decompose the monolith using database-first separation followed by critical service extraction via Strangler Fig pattern

**Status:** Proposed

## Context

Our modular monolith has separate schemas per module (orders, catalog, payments, users) on PostgreSQL, deployed cloud-native. The database is already straining at 2M MAU and will not survive 10M MAU across 5 markets. Our $2M budget eliminates any possibility of a full rewrite or parallel platform build. Traditional microservices-first decomposition is too expensive and risky for a platform generating $50M revenue. However, our existing module boundaries and separate schemas provide a significant head start — the logical separation already exists in the database layer. We need a decomposition strategy that simultaneously addresses the database scaling bottleneck, enables GDPR data residency, and stays within budget.

## Decision

Lead with database separation, not service extraction:

**Step 1 — Database-First Split:** Promote existing PostgreSQL schemas to independent database instances. Each schema (users, payments, catalog, orders) gets its own connection endpoint. Use a database proxy layer (PgBouncer) so the monolith application layer connects through a proxy that routes to the correct database instance transparently. Zero application code changes for the initial split.

**Step 2 — Regional Placement:** Once schemas are on independent instances, place them in the appropriate region per [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) (Hybrid Regional-Domain Data Architecture). Users and payments schemas go to EU-regional instances for GDPR compliance. Catalog replicates globally.

**Step 3 — Critical Service Extraction:** Only after the database is separated, extract the 2-3 services that genuinely need independent deployment: payments (PCI compliance, independent scaling), user/auth (regional data sovereignty), and catalog pricing (multi-currency, market-specific pricing). Use Strangler Fig pattern — API gateway routes requests to either monolith or new service.

**Step 4 — Remaining modules stay in the monolith** until revenue or operational pressure justifies extraction. The monolith continues to run, now backed by distributed databases, which is a stable and proven architecture pattern.

**De-risking approach:** Schema-level feature flags allow routing individual schemas to regional instances one at a time. Shadow replication testing validates correctness before committing — replicate to new instances and compare query results against both before switching traffic.

## Consequences

### Positive

- Fastest path to international market launch — don't need microservices to go multi-region
- Solves GDPR data residency at the database layer with minimal application changes
- Addresses the immediate database scaling bottleneck (the current pain point)
- Budget-friendly — database separation is dramatically cheaper than full service decomposition
- Existing separate schemas make this a routing exercise, not a restructuring project
- Creates natural extraction points — once a schema is independent, promoting to service is just changing a connection string
- Each market launch funds the next decomposition step

### Negative

- Cross-schema queries break when schemas live on different hosts — reporting, admin dashboards, analytics jobs that JOIN across schemas will fail
- Distributed transactions lost between schemas on different databases — order creation touching orders + payments schemas needs saga pattern or eventual consistency
- Connection management complexity increases — monolith goes from one connection pool to multiple per-region pools
- Hidden coupling risk — shared enums, lookup tables, sequences, or stored procedures referencing multiple schemas may surface unexpectedly
- Operational complexity — monitoring, backup, disaster recovery multiplied across instances and regions
- Team may lack distributed database operations experience

### Mitigations

- Materialized views replace cross-schema JOINs — pre-compute joined data, reports read from views
- Audit schema independence before migration — rank schemas by cross-schema dependencies, split most independent first
- Rollback plan for each schema migration — route back to primary within minutes if issues arise
- Enabling team (Multi-Region Infrastructure) owns this decomposition and establishes patterns

## Related ADRs

- [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) — Data architecture that determines regional placement
- [ADR-010](ADR-010-region-aware-data-abstraction-layer.md) — Abstraction layer that makes routing transparent
- [ADR-007](ADR-007-managed-services-by-default.md) — Managed PostgreSQL for database instances
