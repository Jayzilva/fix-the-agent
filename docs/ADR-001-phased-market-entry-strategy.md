# ADR-001: Adopt Phased Market Entry Strategy

**Title:** Adopt a phased 3-year market entry strategy with revenue-gated progression across 5 international markets

**Status:** Proposed

## Context

We are a regional e-commerce platform with 2M MAU, $50M revenue, 25 engineers, and a modular monolith on Next.js/.NET/PostgreSQL. We need to expand into 5 international markets (EU + US), launch a B2B platform, reach 10M MAU, and achieve $200M revenue. Our total budget is $2M covering all expansion costs including 10 new engineers/year. Attempting to launch all 5 markets simultaneously would exceed our budget, overwhelm our engineering capacity, and force premature architectural decisions without production learning. We need a sequencing strategy that manages risk, preserves budget, and lets early market revenue fund later expansion.

## Decision

Adopt a 3-phase market entry strategy over 2-3 years:

**Phase 1 (Year 1):** Launch first EU market with minimum viable internationalization. Invest ~$800K in infrastructure, first hires (enabling teams), legal/compliance setup, and database-first decomposition. Target: revenue generation within 6-9 months.

**Phase 2 (Year 2):** Expand to 2 additional EU markets using Phase 1 revenue + remaining budget. Harden architecture based on production learnings. Upgrade infrastructure, begin B2B pilot.

**Phase 3 (Year 2-3):** Launch remaining markets including US. Upgrade to Active-Active infrastructure. Scale B2B platform. Funded primarily by Phase 1-2 revenue.

**Market sequencing principle:** Consider Germany first (largest EU e-commerce market, forces hardest localization and compliance problems early) over UK (easier but teaches less). Enable passive access from other EU countries during Phase 1 to measure organic demand. Defer US entry until all EU markets are stable — US requires fundamentally different compliance, payments, and competitive strategy.

**Progression is revenue-gated, not calendar-gated.** Use a Market Entry Readiness Scorecard with quantitative criteria (revenue threshold, architecture stability metrics, team capacity score, compliance audit pass) to trigger phase transitions.

## Consequences

### Positive

- Each phase is a contained proving ground — mistakes are limited to one market
- Revenue from Phase 1 funds Phase 2, reducing dependence on fixed budget ceiling
- Architecture hardens progressively based on production data, not predictions
- Team capability compounds — Phase 1 veterans train Phase 2 new hires
- Allows market-specific positioning and product-market fit testing

### Negative

- Slower time-to-market — competitors may enter target markets first
- Phase 1 market choice carries outsized risk — poor performance could stall entire program
- Revenue timeline assumption is critical — if market 1 takes 12-18 months instead of 6-9, Phase 2 is delayed
- Team operates in perpetual launch mode for 3 years — burnout risk
- Different feature sets across markets during transition creates support complexity
- Architecture decisions optimized for Phase 1 market may not generalize perfectly

### Mitigations

- Phase gate reviews at 3-month intervals with go/no-go based on scorecard
- Formal architecture retrospective after each phase — findings update subsequent ADRs
- Parallel soft launch to measure demand and inform Phase 2 market prioritization
- US market entry gets its own dedicated ADR when Phase 3 approaches

## Related ADRs

- [ADR-002](ADR-002-database-first-decomposition.md) — Decomposition strategy phased with market entry
- [ADR-006](ADR-006-phased-team-topology.md) — Team topology evolves per phase
- [ADR-011](ADR-011-active-passive-to-active-active.md) — Infrastructure upgrades gated by phase revenue
