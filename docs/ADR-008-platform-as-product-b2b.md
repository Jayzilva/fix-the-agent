# ADR-008: Build Platform-as-Product for B2B Enablement

**Title:** Create an internal platform layer consumed by both B2C and B2B, with B2C as the first tenant and configurable isolation for B2B customers

**Status:** Proposed

## Context

Our growth target from $50M to $200M requires B2B revenue alongside B2C international expansion. B2B e-commerce commands 3-5x higher revenue per customer but requires multi-tenancy, API access, SLA differentiation, and potentially per-tenant data isolation. Our B2B customers are a mix of large enterprises (needing strong isolation) and smaller businesses (accepting shared infrastructure). Building a separate B2B platform would double engineering effort and fragment the codebase. Our modular monolith with separate schemas already has the foundation for tenant isolation. The API gateway needed for the Strangler Fig decomposition ([ADR-002](ADR-002-database-first-decomposition.md)) can serve double duty as the B2B access layer.

## Decision

Build a Platform-as-Product where B2C is the first tenant:

**Phase 1 — MVP Platform (Year 1, alongside market 1 launch):**

- API gateway (managed, per [ADR-007](ADR-007-managed-services-by-default.md)) with API key management and rate limiting
- Basic tenant configuration (feature flags, branding)
- Enough to onboard first 2-3 B2B pilot customers
- The same API gateway serves as the Strangler Fig decomposition bridge

**Phase 2 — Tenant Management (Year 2, informed by pilot feedback):**

- Tenant management service with configurable isolation levels
- Schema-level isolation for enterprise tenants (following existing separate-schema pattern)
- Shared infrastructure with feature-flag differentiation for smaller tenants
- Per-tenant data residency selection for B2B customers who require it ([ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) enables this)

**Phase 3 — Full Platform (Year 3, revenue-gated):**

- SLA enforcement and monitoring per tenant
- Usage-based billing and metering integration
- Self-service tenant onboarding portal
- Dedicated infrastructure option for premium enterprise tenants

**Revenue-gated investment:** Platform capability tiers are funded by B2B revenue milestones. First $1M B2B revenue funds tenant management. $5M funds dedicated infrastructure options. The platform grows with the business case.

**Find 2-3 B2B pilot customers before building.** Their actual requirements define the platform roadmap — avoid premature abstraction.

## Consequences

### Positive

- B2C-as-first-tenant forces clean API boundaries — improves overall architecture quality
- API gateway serves dual purpose — B2B access AND decomposition bridge (one investment, two returns)
- Configurable isolation serves mixed B2B customer base (enterprise and SMB)
- Data residency per B2B tenant becomes a sellable competitive feature
- Platform layer becomes natural home for cross-cutting concerns (auth, rate limiting, compliance)
- Revenue-gated investment prevents overbuilding before market validation

### Negative

- Scope creep risk — "platform" is infinitely expandable without strict boundaries
- Premature abstraction if built before having real B2B customer feedback
- Noisy neighbor problem — B2B heavy API usage could impact B2C performance
- Competes with international expansion for engineering attention and budget
- Tenant onboarding operational overhead scales linearly with customers

### Mitigations

- Strict MVP scope for Phase 1 — API gateway + keys + rate limiting only
- B2B pilot customers co-design the platform requirements
- SLA enforcement and rate limiting from Phase 1 prevent noisy neighbor issues
- Platform team is the evolved enabling team ([ADR-006](ADR-006-phased-team-topology.md)) — doesn't steal from expansion effort

## Related ADRs

- [ADR-002](ADR-002-database-first-decomposition.md) — API gateway shared with Strangler Fig decomposition
- [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) — Per-tenant data residency enabled by data architecture
- [ADR-006](ADR-006-phased-team-topology.md) — Platform team evolves from enabling teams
- [ADR-007](ADR-007-managed-services-by-default.md) — Managed API gateway and billing services
