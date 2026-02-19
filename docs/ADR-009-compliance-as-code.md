# ADR-009: Implement Compliance-as-Code with Third-Party Consent Management

**Title:** Embed GDPR compliance enforcement in CI/CD pipeline and use third-party tooling for customer-facing consent management

**Status:** Proposed

## Context

GDPR compliance must scale across 5 markets, multiple services (as the monolith decomposes), and B2B tenants. Manual compliance review creates bottlenecks and doesn't scale. Consent management UI (cookie banners, preference centers, data subject access requests) changes frequently with regulatory updates and is a solved commodity problem. Data classification enforcement, audit logging, and policy checks are core platform capabilities that touch every service and must be owned. We need continuous enforcement rather than periodic auditing.

## Decision

Split compliance into two domains — own the architecture, rent the UX:

### Owned — Compliance-as-Code in CI/CD Pipeline

Automated policy checks at deployment for every service and schema change:

- Does this service handle PII? Is it configured for the correct region?
- Is audit logging enabled? Is the data classification tag present?
- Does the schema migration include classification for new columns?

Non-compliant deployments are blocked before reaching production.

Audit logging built into the platform layer — every data access, modification, and transfer logged.

Data classification registry ([ADR-005](ADR-005-data-classification-tiers.md)) is the source of truth for all policy checks.

### Rented — Third-Party Consent Management

Use managed consent platform (OneTrust, TrustArc, or equivalent) for:

- Cookie consent banners per market (UK, Germany, France each have nuances)
- User preference centers for marketing consent
- Data Subject Access Request (DSAR) workflow automation
- Consent audit trail and reporting

Vendor tracks regulatory updates to consent requirements — we don't.

### Ongoing Compliance Operations

Annual TIA review cycle aligned with pipeline checks. Automated monitoring flags when data flows change in ways that affect the Transfer Impact Assessment ([ADR-004](ADR-004-sccs-gdpr-transfer-mechanism.md)).

## Consequences

### Positive

- Engineers can't accidentally deploy non-compliant code — pipeline blocks it
- Shifts compliance from "periodic audit" to "continuous enforcement" — always compliant, not just at audit time
- Consent management vendor tracks rapidly changing cookie/consent regulations
- Platform-level audit logging provides comprehensive compliance trail
- Scales automatically with service decomposition — new services inherit pipeline checks
- Reduces ongoing compliance engineering effort after initial setup

### Negative

- Initial CI/CD pipeline setup requires significant engineering investment
- False positives in compliance checks could slow deployments
- Third-party consent vendor is an ongoing licensing cost ($50-100K/year at scale)
- Vendor dependency for customer-facing compliance — outage impacts consent collection
- Pipeline checks add deployment latency
- Must maintain the policy rules as regulations evolve

### Mitigations

- Build pipeline checks incrementally — start with classification enforcement, add rules over time
- Allow emergency bypass with mandatory post-deployment audit (logged, not silent)
- Multi-vendor evaluation for consent management — choose based on EU market coverage
- Compliance enabling team ([ADR-006](ADR-006-phased-team-topology.md)) owns policy rule maintenance

## Related ADRs

- [ADR-004](ADR-004-sccs-gdpr-transfer-mechanism.md) — TIA monitoring integrated into pipeline
- [ADR-005](ADR-005-data-classification-tiers.md) — Classification tags are the source of truth for checks
- [ADR-006](ADR-006-phased-team-topology.md) — GDPR/Compliance enabling team owns policy rules
- [ADR-007](ADR-007-managed-services-by-default.md) — Third-party consent is a managed service
