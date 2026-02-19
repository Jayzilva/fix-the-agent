# ADR-005: Establish Data Classification-Driven Compliance Tiers

**Title:** Define data classification tiers that drive all residency, encryption, retention, and access decisions across the platform

**Status:** Proposed

## Context

Our platform handles data ranging from public product catalogs to sensitive payment information. GDPR, PCI-DSS, and B2B customer contracts each impose different requirements on different data types. Applying blanket maximum-protection to all data is expensive and operationally burdensome. Applying insufficient protection to sensitive data creates compliance risk. We need a systematic framework that maps data types to protection requirements and drives automated enforcement. This classification underpins [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) (data placement), [ADR-004](ADR-004-sccs-gdpr-transfer-mechanism.md) (transfer mechanisms), [ADR-009](ADR-009-compliance-as-code.md) (compliance-as-code), and [ADR-010](ADR-010-region-aware-data-abstraction-layer.md) (data routing).

## Decision

Define four data classification tiers with per-tier rules:

| Tier | Examples | Residency | Encryption | Retention | Access |
|---|---|---|---|---|---|
| **PII-Critical** | Payment details, government IDs, health data | Regional primary, no cross-region transfer | At-rest + in-transit + field-level | Minimum required by law | Named individuals, audit-logged |
| **PII-Standard** | Names, emails, addresses, order history | Regional primary, SCC for limited transfer | At-rest + in-transit | Defined retention policy | Role-based, audit-logged |
| **Operational** | Order items, inventory, fulfillment status | Domain-owned, regional routing | At-rest + in-transit | Business-defined | Role-based |
| **Public** | Product catalog, CMS content, pricing | Global replicated | In-transit only | No restriction | Open |

**Implementation:** Every table and column in PostgreSQL tagged with classification tier via metadata comments and a central `data_classification` registry table. CI/CD pipeline reads classification tags to enforce routing rules and block non-compliant deployments. New tables/columns require classification as part of schema migration review.

## Consequences

### Positive

- Precision over paranoia — different data gets appropriate protection levels
- Single source of truth for all compliance, routing, and audit decisions
- Enables automated enforcement via CI/CD pipeline ([ADR-009](ADR-009-compliance-as-code.md))
- Reduces infrastructure cost — only PII-Critical/Standard needs regional primaries
- Makes compliance audits straightforward — "show me all PII-Critical data and where it lives"
- Scales naturally as new data types are added

### Negative

- Upfront classification effort across all existing schemas
- Classification must be maintained as schemas evolve — risk of drift
- Edge cases and mixed-sensitivity data require judgment calls
- Over-classification (marking too much as PII-Critical) negates cost benefits
- Under-classification creates compliance risk

### Mitigations

- Automated drift detection — CI/CD flags unclassified columns in schema migrations
- Quarterly classification review as part of compliance cycle
- Default to PII-Standard for ambiguous cases — safe without being maximally expensive
- Classification review is part of the enabling team's (GDPR/Compliance) responsibilities per [ADR-006](ADR-006-phased-team-topology.md)

## Related ADRs

- [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) — Data placement driven by these tiers
- [ADR-004](ADR-004-sccs-gdpr-transfer-mechanism.md) — Transfer mechanism scope determined by classification
- [ADR-009](ADR-009-compliance-as-code.md) — Pipeline enforcement reads classification tags
- [ADR-010](ADR-010-region-aware-data-abstraction-layer.md) — Routing decisions based on classification
