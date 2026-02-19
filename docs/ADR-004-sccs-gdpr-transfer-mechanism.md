# ADR-004: Use Standard Contractual Clauses as Primary GDPR Data Transfer Mechanism

**Title:** Adopt SCCs for EU-US data transfers with architectural readiness for full localization as regulatory contingency

**Status:** Proposed

## Context

Our international expansion requires transferring some data between EU and US regions. GDPR Articles 44-49 govern cross-border data transfers and require a legal mechanism. Options include: Standard Contractual Clauses (SCCs), Binding Corporate Rules (BCRs), the EU-US Data Privacy Framework (DPF) adequacy decision, or full data localization. BCRs cost $200-500K+ and take 12-18 months for approval — incompatible with our budget and timeline. Full localization is architecturally expensive. The EU-US DPF exists but has been legally challenged (predecessors Safe Harbor and Privacy Shield were both invalidated). SCCs are used by ~90% of companies and have remained valid through multiple regulatory shifts. Our Hybrid Regional-Domain architecture ([ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md)) already minimizes the data that actually needs to cross borders.

## Decision

Adopt SCCs as the primary GDPR data transfer mechanism with a belt-and-suspenders contingency:

**Primary mechanism:** Standard Contractual Clauses for all EU-US data transfers. Cloud providers (AWS/Azure/GCP) already offer pre-signed SCCs for infrastructure-level transfers. Application-level data flows we control require our own SCC agreements.

**Transfer Impact Assessment (TIA):** Engage GDPR-specialized legal counsel in Phase 1 for SCC setup and initial TIA. Budget ~$30-40K. Annual TIA review cycle aligned with compliance-as-code pipeline.

**Minimize transfer surface:** Design the system so EU-to-US data transfer is genuinely minimal. EU user data is processed and stored in EU. Only aggregated analytics, global admin access, and catalog sync flow cross-region. The smaller the SCC scope, the lower the risk.

**Contingency: architectural readiness for localization.** The Region-Aware Data Abstraction Layer ([ADR-010](ADR-010-region-aware-data-abstraction-layer.md)) means that if SCCs or DPF are invalidated, we can switch to full data localization by reconfiguring the routing layer — not rewriting applications. Document the "SCC to Localization" escalation playbook as an ADR appendix.

**B2B tiered strategy:** B2C data uses SCCs (volume play, standard compliance). B2B enterprise customers who contractually require data localization get it as a premium offering — their data never leaves the region. Turn the constraint into a revenue differentiator.

## Consequences

### Positive

- Lowest-cost compliance mechanism — legal fees only, no architectural changes beyond performance-driven work
- Industry-standard approach with established legal precedent and readily available counsel
- ADR-003 already minimizes cross-border data volume, reducing SCC scope and risk
- Cloud providers handle infrastructure-level SCC compliance
- Belt-and-suspenders approach provides regulatory resilience without upfront localization cost
- B2B tiered offering turns compliance into revenue opportunity

### Negative

- Regulatory instability — EU courts have invalidated transfer mechanisms twice before
- TIA requires updating when US law changes — ongoing legal overhead
- Some B2B enterprise customers may not accept SCCs regardless of architectural readiness
- Reputational risk during transition periods if a high-profile invalidation occurs
- Dependence on continued EU-US diplomatic cooperation on data protection

### Mitigations

- Subscribe to regulatory monitoring (IAPP, law firm alerts) with defined trigger conditions for escalation
- Escalation playbook documented and tested annually
- The same data abstraction layer that enables localization fallback also serves performance purposes — it's not wasted investment
- B2B localization option available immediately for customers who insist

## Related ADRs

- [ADR-003](ADR-003-hybrid-regional-domain-data-architecture.md) — Data architecture that minimizes transfer surface
- [ADR-005](ADR-005-data-classification-tiers.md) — Classification determines what data needs SCCs
- [ADR-009](ADR-009-compliance-as-code.md) — Automated TIA monitoring in pipeline
- [ADR-010](ADR-010-region-aware-data-abstraction-layer.md) — Contingency mechanism for localization switch
