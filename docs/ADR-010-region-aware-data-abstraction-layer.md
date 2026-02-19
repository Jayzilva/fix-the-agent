# ADR-010: Adopt Region-Aware Data Abstraction Layer

**Title:** Build a data routing abstraction layer that keeps applications region-ignorant while handling data residency transparently

**Status:** Proposed

## Context

Our Hybrid Regional-Domain Data Architecture ([ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md)) means different data types live in different regions. Our Active-Passive to Active-Active migration path ([ADR-011](ADR-011-active-passive-to-active-active.md)) means data routing will change over time. If applications embed region-awareness directly, every routing change requires application code modifications across potentially dozens of services. We need an abstraction that decouples "where data lives" from "how applications access data." This same abstraction serves as the regulatory contingency — if SCCs are invalidated ([ADR-004](ADR-004-sccs-gdpr-transfer-mechanism.md)), we reconfigure routing, not applications.

## Decision

Introduce a data routing abstraction layer between applications and databases:

**Implementation:** Database proxy layer (built on PgBouncer or similar) that applications connect to. The proxy routes queries to the correct regional PostgreSQL instance based on:

- Data classification tags ([ADR-005](ADR-005-data-classification-tiers.md)) — PII-Critical routes to regional primary
- Request context — EU user requests route to EU data, US to US
- Operation type — reads may go to replicas, writes to primary

**Applications remain region-ignorant.** They connect to a single logical endpoint per schema. The abstraction layer handles:

- Regional routing based on data classification and user context
- Read/write splitting for Active-Passive mode ([ADR-011](ADR-011-active-passive-to-active-active.md))
- Future Active-Active write routing when infrastructure upgrades
- Failover and connection management across regional instances

**The abstraction layer evolves with the infrastructure:** Phase 1 it routes to Active-Passive (reads to replica, writes to primary). Phase 2-3 it upgrades to Active-Active routing (writes to nearest regional primary). Applications don't change — only proxy configuration changes.

## Consequences

### Positive

- Applications never need to know which region they're talking to — clean separation of concerns
- Infrastructure upgrades (Active-Passive to Active-Active) are transparent to applications
- Regulatory contingency is a routing configuration change, not a code rewrite
- Same abstraction enables performance optimization (route to nearest replica)
- Reduces complexity in application code — developers don't think about regions

### Negative

- Adds a network hop and potential latency to every database query
- Proxy layer becomes a critical single point of failure per region
- Debugging is harder — issues could be in application, proxy, or database
- Connection pooling across proxy adds operational complexity
- Custom routing logic in the proxy must be built and maintained

### Mitigations

- PgBouncer adds <1ms latency per query — negligible for most operations
- Deploy proxy as highly-available cluster per region (managed where possible)
- Structured logging across all layers with correlation IDs for debugging
- Start simple — basic read/write split first, add classification-based routing incrementally

## Related ADRs

- [ADR-002](ADR-002-database-first-decomposition.md) — Decomposition strategy this layer enables
- [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) — Data placement rules this layer implements
- [ADR-004](ADR-004-sccs-gdpr-transfer-mechanism.md) — Regulatory contingency this layer provides
- [ADR-005](ADR-005-data-classification-tiers.md) — Classification tags drive routing decisions
- [ADR-011](ADR-011-active-passive-to-active-active.md) — Infrastructure evolution this layer abstracts
