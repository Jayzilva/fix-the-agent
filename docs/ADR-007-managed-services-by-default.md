# ADR-007: Adopt Managed Services by Default

**Title:** Default all build-vs-buy decisions to managed services unless the capability is a core business differentiator

**Status:** Proposed

## Context

Our $2M budget covers all expansion costs including headcount. After salaries (~$1.2-1.5M), remaining budget for infrastructure, tooling, and services is $500-800K. Multi-region cloud infrastructure, GDPR compliance tooling, and platform capabilities all compete for this limited budget. Engineering capacity (25 current + 10/year new) must focus on business-differentiating work — the architecture decisions that directly enable international expansion and B2B revenue. Custom infrastructure is a luxury this budget cannot afford.

## Decision

Every infrastructure and platform capability decision defaults to managed services unless the capability meets ALL of these criteria:

1. It is a core business differentiator (directly impacts revenue or competitive advantage)
2. No managed service meets the requirements within acceptable constraints
3. The team has the expertise to build AND operate it long-term

**Managed services by default:**

- **Database:** Managed PostgreSQL (AWS RDS/Aurora, Azure Database for PostgreSQL, or GCP Cloud SQL) with built-in replication, backups, and multi-region support
- **Authentication:** Managed auth service (Auth0, Keycloak on managed infra) — not custom-built
- **API Gateway:** Managed API gateway (Kong, AWS API Gateway) for B2B platform and decomposition bridge
- **Monitoring/Observability:** Managed platform (Datadog, New Relic) — not self-hosted
- **Consent Management:** Third-party (OneTrust, TrustArc) per [ADR-009](ADR-009-compliance-as-code.md)
- **CDN/Edge:** Managed CDN (CloudFront, Cloudflare) — Next.js edge deployment
- **Container Orchestration:** Managed Kubernetes (EKS, AKS, GKE)
- **CI/CD:** Managed pipeline (GitHub Actions, GitLab CI)

**Custom-built (differentiators):**

- Data classification and routing engine ([ADR-005](ADR-005-data-classification-tiers.md), [ADR-010](ADR-010-region-aware-data-abstraction-layer.md)) — core to compliance and multi-region strategy
- Tenant management and SLA enforcement ([ADR-008](ADR-008-platform-as-product-b2b.md)) — core to B2B revenue
- Domain-specific business logic (pricing, catalog, orders) — core to e-commerce value

## Consequences

### Positive

- Preserves engineering capacity for business-critical, revenue-generating work
- Reduces operational burden — vendor handles patching, scaling, availability
- Faster time-to-market — managed services are production-ready immediately
- Predictable costs — subscription/usage-based pricing vs. unpredictable custom ops costs
- Built-in compliance features (encryption, audit logging, SOC2) from major vendors

### Negative

- Vendor lock-in risk — migrating away from managed services is costly
- Ongoing licensing costs that scale with usage — could become expensive at 10M MAU
- Less customization flexibility — must work within vendor constraints
- Multi-vendor environment creates integration complexity
- Vendor outages directly impact platform availability

### Mitigations

- Choose vendors with strong multi-cloud support and data portability
- Negotiate enterprise agreements as usage grows
- Abstract vendor-specific APIs behind internal interfaces where practical
- Multi-region deployment provides redundancy against single-vendor regional outages

## Related ADRs

- [ADR-002](ADR-002-database-first-decomposition.md) — Managed PostgreSQL for database instances
- [ADR-008](ADR-008-platform-as-product-b2b.md) — Managed API gateway for B2B platform
- [ADR-009](ADR-009-compliance-as-code.md) — Third-party consent management
- [ADR-011](ADR-011-active-passive-to-active-active.md) — Managed cloud infrastructure for multi-region
