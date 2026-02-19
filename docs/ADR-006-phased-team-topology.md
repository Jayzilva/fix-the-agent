# ADR-006: Adopt Phased Team Topology — Enabling Teams to Platform Teams

**Title:** Evolve team structure from component teams through enabling teams to platform + stream-aligned teams over 3 years

**Status:** Proposed

## Context

Our current 25 engineers are organized as component teams (database team, frontend team, payments team, etc.). This structure creates handoff bottlenecks — every cross-cutting feature (like multi-currency) requires coordination across multiple teams. We're adding 10 engineers/year for 3 years (reaching 55). Some engineers have GDPR experience, most don't. We're hiring a mix of local and EU-based engineers supplemented by EU consultants. We need a team structure that supports the phased international expansion without a disruptive Day 1 reorganization, while ensuring GDPR knowledge and multi-region expertise are distributed across the organization. Conway's Law tells us our team structure will dictate our system architecture.

## Decision

Phase the team topology evolution to mirror architecture phases:

**Year 1 (25 to 35 engineers): Add Enabling Teams.** Keep existing component teams intact — they continue shipping. Create two new enabling teams from new hires:

- **GDPR/Compliance Enabling Team** (2-3 people including EU-based engineers + consultant access): upskills other teams on compliance, owns data classification registry, reviews schema changes
- **Multi-Region Infrastructure Enabling Team** (2-3 people): owns database-first decomposition, proxy layer, regional deployment, establishing patterns other teams follow

Seed 2-3 GDPR-experienced engineers across different existing teams as local experts who upskill their teammates.

**Year 2 (35 to 45 engineers): Begin Evolution to Platform Teams.** Enabling teams have built the platform layer (data abstraction, tenant management, compliance tooling). They naturally become the **Platform Team** owning shared infrastructure. Existing component teams begin reforming into **stream-aligned teams** around business domains (orders, catalog, B2B) as services are extracted from the monolith.

**Year 3 (45 to 55 engineers): Full Platform + Stream-Aligned Model.** Platform Team owns cross-cutting infrastructure, compliance, and data layer. Stream-aligned domain teams own end-to-end business capabilities. Markets are a configuration handled by the platform, not a team responsibility.

**Hiring roadmap is a function of architecture roadmap:** Year 1 hires focus on infrastructure/compliance. Year 2 hires focus on platform/B2B capabilities. Year 3 hires focus on market-specific and domain engineering.

## Consequences

### Positive

- No disruptive Day 1 reorg — existing teams keep shipping during the most critical execution year
- Enabling teams build expertise and patterns that scale to the whole organization
- GDPR knowledge distributed across teams rather than siloed in a compliance department
- EU hire + consultant hybrid provides local expertise without overcommitting headcount
- Team evolution mirrors architecture evolution — organizational changes feel natural, not forced
- Each hiring cohort maps to the specific capability they'll build

### Negative

- Component team bottlenecks persist during Year 1 transition — cross-team dependencies still exist
- Enabling teams could become bottlenecks themselves if understaffed or overloaded with requests
- Year 2 transition from component to stream-aligned teams is the most disruptive organizational change
- Dual-mode operation (component teams + enabling teams) creates coordination overhead
- Risk of enabling teams building solutions without sufficient input from domain teams

### Mitigations

- Enabling teams have clear mandates — unblock and upskill, not own and control
- Define explicit interaction models between enabling teams and component teams
- Phase 2 team restructuring planned during Phase 1 — not a surprise
- Regular retrospectives on team topology effectiveness at each phase gate

## Related ADRs

- [ADR-001](ADR-001-phased-market-entry-strategy.md) — Team phases align with market entry phases
- [ADR-002](ADR-002-database-first-decomposition.md) — Multi-Region Infrastructure enabling team owns decomposition
- [ADR-005](ADR-005-data-classification-tiers.md) — GDPR/Compliance enabling team owns classification
- [ADR-008](ADR-008-platform-as-product-b2b.md) — Platform team evolves from enabling teams
