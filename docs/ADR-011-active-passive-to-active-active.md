# ADR-011: Phase Multi-Region Infrastructure from Active-Passive to Active-Active

**Title:** Launch market 1 with Active-Passive multi-region infrastructure and upgrade to Active-Active when Phase 2 revenue justifies the cost

**Status:** Proposed

## Context

Our target is 5 international markets across EU + US. Multi-region infrastructure is required for both performance (low latency for local users) and compliance (data residency). Active-Active (both regions handle reads and writes independently) provides the lowest latency and highest availability but is the most expensive and operationally complex option. Active-Passive (primary region handles writes, secondary serves reads) is simpler and cheaper but adds write latency for remote users. Our $2M budget cannot afford Active-Active from Day 1 alongside all other expansion costs. However, our Hybrid Regional-Domain data architecture ([ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md)) means most writes are already region-local (EU users write to EU data, US users write to US data), which dramatically reduces Active-Active complexity when we're ready.

## Decision

Phase the infrastructure evolution:

**Phase 1 — Active-Passive (Market 1 launch):**

- Primary region: home region (all writes)
- EU region: read replicas for EU users (catalog, product browsing)
- EU-regional primary for PII schemas only (users, payments) per [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md)
- Write latency for EU users on non-PII data (orders) acceptable for Phase 1 volume

**Phase 2 — Active-Active (triggered by revenue milestone and market demand):**

- Both EU and US regions handle reads AND writes independently
- Hybrid Regional-Domain model ensures most writes are already region-local — EU user data writes to EU, US to US
- Only globally-shared data (catalog updates, CMS changes) needs cross-region conflict resolution
- Catalog/CMS changes are infrequent — eventual consistency acceptable ([ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) mitigations apply)
- Data abstraction layer ([ADR-010](ADR-010-region-aware-data-abstraction-layer.md)) handles the routing upgrade transparently — applications don't change

**Upgrade trigger:** Market revenue milestone (defined in [ADR-001](ADR-001-phased-market-entry-strategy.md) readiness scorecard) AND measured write latency exceeding acceptable thresholds for EU users.

**Next.js edge functions** handle personalization, i18n, and request routing from Phase 1 — these provide low-latency user experience even in Active-Passive mode.

## Consequences

### Positive

- Phase 1 cost is incremental — one additional region with read replicas, not full Active-Active infrastructure
- Hybrid Regional-Domain data model makes Active-Active upgrade a configuration change via the abstraction layer
- Only globally-shared data needs conflict resolution — dramatically simpler than "true" Active-Active for all data
- Revenue-gated upgrade means the business case is proven before the investment
- Next.js edge functions provide good UX even in Active-Passive mode
- Buy the option for Active-Active without paying upfront

### Negative

- Phase 1 EU users experience write latency for non-PII operations (orders, cart updates)
- Active-Passive has a single point of write failure — primary region outage affects all writes
- Upgrade to Active-Active still requires engineering effort for conflict resolution strategy
- Global catalog eventual consistency means brief windows of stale data across regions
- Maintaining two operational modes (AP and AA) during transition adds complexity

### Mitigations

- Next.js optimistic UI updates mask write latency for EU users
- Phase 1 volume (single market) is manageable on Active-Passive — write volume is low initially
- Conflict resolution only needed for catalog/CMS — well-understood problem with mature solutions (last-write-wins, vector clocks)
- Design for Active-Active from Day 1 in the data abstraction layer — just don't activate it until Phase 2

## Related ADRs

- [ADR-001](ADR-001-phased-market-entry-strategy.md) — Revenue milestones trigger infrastructure upgrade
- [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) — Data model that simplifies Active-Active
- [ADR-007](ADR-007-managed-services-by-default.md) — Managed cloud infrastructure for multi-region
- [ADR-010](ADR-010-region-aware-data-abstraction-layer.md) — Abstraction layer that makes upgrade transparent
