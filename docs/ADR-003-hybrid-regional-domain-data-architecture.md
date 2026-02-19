# ADR-003: Implement Hybrid Regional-Domain Data Architecture

**Title:** Classify data by sensitivity and domain to determine regional placement — regionalize PII, globalize catalogs, domain-own operational data

**Status:** Proposed

## Context

GDPR requires adequate protection for EU citizen personal data. Our platform handles multiple data types with different sensitivity levels: PII (user profiles, addresses, payment details), operational data (orders, inventory, fulfillment), and reference data (product catalogs, CMS content, pricing). Full data localization (everything in every region) is prohibitively expensive. Single global database with SCCs alone doesn't provide the architectural resilience we need if the EU-US regulatory framework shifts. We need a data architecture that satisfies GDPR, performs well across regions, and doesn't duplicate infrastructure unnecessarily. Only ~30-40% of our data is actually PII-sensitive.

## Decision

Implement a three-tier data placement strategy based on data sensitivity and domain:

**Tier 1 — Regional Primary (PII-Critical):** Users and payments schemas get regional primary databases. EU customer data physically resides in EU. US customer data resides in US. No cross-region replication of raw PII. These schemas support the regulatory "where does EU PII live?" question with a clear, auditable answer.

**Tier 2 — Global Shared (Non-Sensitive):** Catalog, CMS, and pricing schemas replicate globally via PostgreSQL logical replication. Product data is not PII — no residency requirement. Global replication ensures fast catalog browsing everywhere (the most common user action).

**Tier 3 — Domain-Owned with Regional Routing (Mixed):** Orders and inventory schemas are domain-owned. The orders schema requires an internal split: `order_header` (customer PII — shipping address, name) is regional; `order_items` (products, quantities, fulfillment status) is domain-local. Foreign key replaced with order ID reference.

**Build a data classification registry** before any migration. Every table and column tagged as PII-Critical, PII-Standard, Operational, or Public. Tags stored in PostgreSQL metadata comments and a central registry table. All routing, compliance, and audit decisions derive from these tags.

**Use CQRS pattern for cross-region reads** — write to regional primary, project pre-joined read-optimized views locally. Admin dashboards and reporting read from projections, never execute cross-region JOINs.

## Consequences

### Positive

- Only regionalizes ~30-40% of data — dramatically lower infrastructure cost than full isolation
- Catalog browsing (most common action) has zero latency penalty — globally replicated
- B2B tenants can be offered data residency guarantees per-tenant as a premium feature
- Compliance audits are straightforward — provable answer to "where does EU PII live?"
- Data classification registry becomes single source of truth for routing, compliance, and audit
- Supports both Active-Passive and Active-Active infrastructure models

### Negative

- Orders schema split adds complexity — two sub-schemas where there was one
- Three different data strategies means three different operational patterns and failure modes
- Replication lag for global catalog data — price updates take seconds to propagate; customers could see stale prices
- Cross-region reporting requires CQRS projections — adds infrastructure and eventual consistency
- Data classification is an upfront investment that must be maintained as schemas evolve

### Mitigations

- Price-confirmation step at checkout handles stale pricing ("price has changed since you added to cart")
- Start with easy wins: catalog goes global Day 1 (zero PII risk), users/payments go regional for market 1, orders split in Phase 2
- Automated compliance tests in CI/CD — synthetic EU data must never appear in non-EU region
- Data classification tags enforced in deployment pipeline per [ADR-009](ADR-009-compliance-as-code.md)

## Related ADRs

- [ADR-002](ADR-002-database-first-decomposition.md) — Decomposition strategy that enables this data architecture
- [ADR-005](ADR-005-data-classification-tiers.md) — Classification tiers that drive placement decisions
- [ADR-010](ADR-010-region-aware-data-abstraction-layer.md) — Abstraction layer that implements routing
- [ADR-011](ADR-011-active-passive-to-active-active.md) — Infrastructure model this architecture supports
