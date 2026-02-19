---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'International expansion of regional e-commerce monolith - architecture decisions for scaling from 2M to 10M MAU across 5 markets with GDPR/data residency compliance'
session_goals: 'Generate ADR documents (Title, Status, Context, Decision, Consequences) covering key architectural decisions for the transformation'
selected_approach: 'ai-recommended'
techniques_used: ['Constraint Mapping', 'Morphological Analysis', 'Six Thinking Hats']
ideas_generated: 148
session_active: false
workflow_completed: true
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Jaye
**Date:** 2026-02-19

## Session Overview

**Topic:** International expansion of a regional e-commerce platform — architecture decisions for scaling a monolith from 2M MAU / $50M revenue to 10M MAU / $200M revenue across 5 international markets with a B2B platform, under $2M budget and 10 new engineers/year constraints, with GDPR and data residency compliance.

**Goals:** Produce ADR documents with Title, Status (Proposed/Accepted/Deprecated), Context, Decision, and Consequences for each key architectural decision.

### Session Setup

**Current State:**
- Monolithic architecture
- 2M Monthly Active Users
- 25 engineers
- $50M revenue (regional)

**Target State:**
- 5 international markets
- B2B platform capability
- 10M Monthly Active Users
- $200M revenue

**Constraints:**
- $2M budget
- 10 new engineers/year hiring capacity
- GDPR / data residency compliance required

**Key Decision Domains:**
- Monolith decomposition strategy
- Multi-region data architecture & GDPR/data residency
- B2B platform enablement
- Team scaling & topology
- Infrastructure scaling within budget

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** International e-commerce expansion with focus on producing structured ADR documents

**Recommended Techniques:**

- **Constraint Mapping:** Map all constraints (hard vs soft) to reveal true solution space before making architecture decisions
- **Morphological Analysis:** Systematically explore parameter combinations across decision domains to surface comprehensive ADR topics
- **Six Thinking Hats:** Evaluate each ADR candidate from 6 perspectives to build robust Context, Decision, and Consequences sections

**AI Rationale:** Complex, multi-dimensional, constraint-heavy session with structured deliverables (ADRs) requires systematic constraint identification, comprehensive parameter exploration, and multi-perspective evaluation

## Technique 1: Constraint Mapping Results

### Constraint Landscape

| Domain | Hard Constraints | Soft/Negotiable |
|---|---|---|
| **Regulatory** | GDPR data protection, DPO at scale | Data localization method (SCCs viable), per-market isolation (not required) |
| **Budget** | $2M total ceiling, 10 engineers/year | Managed services vs. build, phased revenue reinvestment |
| **Technical** | Database bottleneck, monolith coupling | Already modular, cloud-native, strong stack for multi-region |
| **Team** | Component team structure, GDPR knowledge gaps | EU hybrid model, knowledge multiplier approach |

**Key Convergence:** Database-first decomposition addresses regulatory, scaling, AND budget constraints simultaneously.

### Ideas Generated (#1-23)
- Regulatory: Data Transfer Mechanism, DPO Model, Data Classification-Driven Compliance, Resilient Data Architecture, Region-Aware Abstraction Layer, B2B Data Residency Contracts
- Budget: Budget-Driven Prioritization, Strangler Fig Over Big Bang, Hire-to-Architecture Alignment, Managed Services Over Build, Phased Market Entry Funding, MVP-Per-Market Architecture
- Technical: Modular Monolith Accelerator, Next.js+.NET+PostgreSQL Multi-Region, PostgreSQL as Residency Pivot, Database Scaling Bottleneck, Cloud-Native Advantage, Database-First Decomposition Strategy
- Team: Component-to-Platform Evolution, GDPR Knowledge Multiplier, EU Consultant Hybrid Model, Inverse Conway Maneuver, Phased Hiring Aligned to Architecture

## Technique 2: Morphological Analysis Results

### Architecture Combination Matrix

| Parameter | Selection |
|---|---|
| 1. Decomposition | E — Database-First + Critical Service Extraction |
| 2. Data Architecture | E — Hybrid Regional-Domain |
| 3. B2B Platform | D — Platform-as-Product |
| 4. Team Topology | D→C — Enabling Teams evolving to Platform Teams |
| 5. Infrastructure | C (phased) — Active-Passive → Active-Active |
| 6. Compliance | D — Compliance-as-Code + Third-Party Consent |

### ADR Candidates Generated (#32-42)
1. ADR: Adopt Strangler Fig with Database-First Decomposition
2. ADR: Implement Hybrid Regional-Domain Data Architecture
3. ADR: Use SCCs as Primary GDPR Data Transfer Mechanism
4. ADR: Build Platform-as-Product for B2B Enablement
5. ADR: Adopt Phased Team Topology — Enabling to Platform
6. ADR: Phase Multi-Region from Active-Passive to Active-Active
7. ADR: Implement Compliance-as-Code with Third-Party Consent
8. ADR: Establish Data Classification-Driven Compliance Tiers
9. ADR: Adopt Region-Aware Data Abstraction Layer
10. ADR: Define Phased Market Entry Strategy
11. ADR: Adopt Managed Services by Default

## Technique 3: Six Thinking Hats Results

Applied all 6 hats (White, Red, Yellow, Black, Green, Blue) to 5 Tier 1 ADRs:

- **ADR #32 — Decomposition:** 21 ideas (#43-63). Key discovery: separate schemas make database-first decomposition a routing exercise, not restructuring. Mitigations: schema-level feature flags, shadow replication, materialized views for cross-schema queries.
- **ADR #33 — Data Architecture:** 19 ideas (#64-82). Key discovery: orders schema needs internal split (PII header vs operational items). CQRS pattern for cross-region reads.
- **ADR #34 — GDPR/SCCs:** 20 ideas (#83-102). Key discovery: belt-and-suspenders approach (SCCs today + architectural readiness for localization). Tiered transfer strategy for B2B premium offering.
- **ADR #35 — B2B Platform:** 23 ideas (#103-125). Key discovery: MVP platform first (API gateway + keys + rate limiting), revenue-gated investment for advanced capabilities. B2B pilot before full platform build.
- **ADR #41 — Market Entry:** 23 ideas (#126-148). Key discovery: Germany-first forces hardest problems early. Market entry readiness scorecard removes emotional timing decisions.

**Total Ideas Generated: 148**

---

## Idea Organization and Prioritization

### ADR Priority Tiers

**Tier 1 — Foundation ADRs:**
1. Phased Market Entry Strategy (sequences everything)
2. Database-First Decomposition (enables data, GDPR, scaling)
3. Hybrid Regional-Domain Data Architecture (determines compliance and infra)

**Tier 2 — Enabling ADRs:**
4. SCCs as GDPR Transfer Mechanism
5. Data Classification-Driven Compliance Tiers
6. Phased Team Topology
7. Managed Services by Default

**Tier 3 — Evolution ADRs:**
8. Platform-as-Product for B2B
9. Compliance-as-Code Pipeline
10. Region-Aware Data Abstraction Layer
11. Active-Passive to Active-Active Infrastructure

### Cross-Cutting Breakthroughs
- Database-first decomposition solves regulatory, scaling, AND budget simultaneously
- API gateway serves dual purpose: B2B enablement AND decomposition bridge
- Data classification tags become single source of truth for routing, compliance, and audit
- Revenue-gated investment: every phase earns the right to fund the next

---

# Architecture Decision Records

---

## ADR-001: Adopt Phased Market Entry Strategy

**Title:** Adopt a phased 3-year market entry strategy with revenue-gated progression across 5 international markets

**Status:** Proposed

### Context

We are a regional e-commerce platform with 2M MAU, $50M revenue, 25 engineers, and a modular monolith on Next.js/.NET/PostgreSQL. We need to expand into 5 international markets (EU + US), launch a B2B platform, reach 10M MAU, and achieve $200M revenue. Our total budget is $2M covering all expansion costs including 10 new engineers/year. Attempting to launch all 5 markets simultaneously would exceed our budget, overwhelm our engineering capacity, and force premature architectural decisions without production learning. We need a sequencing strategy that manages risk, preserves budget, and lets early market revenue fund later expansion.

### Decision

Adopt a 3-phase market entry strategy over 2-3 years:

**Phase 1 (Year 1):** Launch first EU market with minimum viable internationalization. Invest ~$800K in infrastructure, first hires (enabling teams), legal/compliance setup, and database-first decomposition. Target: revenue generation within 6-9 months.

**Phase 2 (Year 2):** Expand to 2 additional EU markets using Phase 1 revenue + remaining budget. Harden architecture based on production learnings. Upgrade infrastructure, begin B2B pilot.

**Phase 3 (Year 2-3):** Launch remaining markets including US. Upgrade to Active-Active infrastructure. Scale B2B platform. Funded primarily by Phase 1-2 revenue.

**Market sequencing principle:** Consider Germany first (largest EU e-commerce market, forces hardest localization and compliance problems early) over UK (easier but teaches less). Enable passive access from other EU countries during Phase 1 to measure organic demand. Defer US entry until all EU markets are stable — US requires fundamentally different compliance, payments, and competitive strategy.

**Progression is revenue-gated, not calendar-gated.** Use a Market Entry Readiness Scorecard with quantitative criteria (revenue threshold, architecture stability metrics, team capacity score, compliance audit pass) to trigger phase transitions.

### Consequences

**Positive:**
- Each phase is a contained proving ground — mistakes are limited to one market
- Revenue from Phase 1 funds Phase 2, reducing dependence on fixed budget ceiling
- Architecture hardens progressively based on production data, not predictions
- Team capability compounds — Phase 1 veterans train Phase 2 new hires
- Allows market-specific positioning and product-market fit testing

**Negative:**
- Slower time-to-market — competitors may enter target markets first
- Phase 1 market choice carries outsized risk — poor performance could stall entire program
- Revenue timeline assumption is critical — if market 1 takes 12-18 months instead of 6-9, Phase 2 is delayed
- Team operates in perpetual launch mode for 3 years — burnout risk
- Different feature sets across markets during transition creates support complexity
- Architecture decisions optimized for Phase 1 market may not generalize perfectly

**Mitigations:**
- Phase gate reviews at 3-month intervals with go/no-go based on scorecard
- Formal architecture retrospective after each phase — findings update subsequent ADRs
- Parallel soft launch to measure demand and inform Phase 2 market prioritization
- US market entry gets its own dedicated ADR when Phase 3 approaches

---

## ADR-002: Adopt Strangler Fig with Database-First Decomposition

**Title:** Decompose the monolith using database-first separation followed by critical service extraction via Strangler Fig pattern

**Status:** Proposed

### Context

Our modular monolith has separate schemas per module (orders, catalog, payments, users) on PostgreSQL, deployed cloud-native. The database is already straining at 2M MAU and will not survive 10M MAU across 5 markets. Our $2M budget eliminates any possibility of a full rewrite or parallel platform build. Traditional microservices-first decomposition is too expensive and risky for a platform generating $50M revenue. However, our existing module boundaries and separate schemas provide a significant head start — the logical separation already exists in the database layer. We need a decomposition strategy that simultaneously addresses the database scaling bottleneck, enables GDPR data residency, and stays within budget.

### Decision

Lead with database separation, not service extraction:

**Step 1 — Database-First Split:** Promote existing PostgreSQL schemas to independent database instances. Each schema (users, payments, catalog, orders) gets its own connection endpoint. Use a database proxy layer (PgBouncer) so the monolith application layer connects through a proxy that routes to the correct database instance transparently. Zero application code changes for the initial split.

**Step 2 — Regional Placement:** Once schemas are on independent instances, place them in the appropriate region per ADR-003 (Hybrid Regional-Domain Data Architecture). Users and payments schemas go to EU-regional instances for GDPR compliance. Catalog replicates globally.

**Step 3 — Critical Service Extraction:** Only after the database is separated, extract the 2-3 services that genuinely need independent deployment: payments (PCI compliance, independent scaling), user/auth (regional data sovereignty), and catalog pricing (multi-currency, market-specific pricing). Use Strangler Fig pattern — API gateway routes requests to either monolith or new service.

**Step 4 — Remaining modules stay in the monolith** until revenue or operational pressure justifies extraction. The monolith continues to run, now backed by distributed databases, which is a stable and proven architecture pattern.

**De-risking approach:** Schema-level feature flags allow routing individual schemas to regional instances one at a time. Shadow replication testing validates correctness before committing — replicate to new instances and compare query results against both before switching traffic.

### Consequences

**Positive:**
- Fastest path to international market launch — don't need microservices to go multi-region
- Solves GDPR data residency at the database layer with minimal application changes
- Addresses the immediate database scaling bottleneck (the current pain point)
- Budget-friendly — database separation is dramatically cheaper than full service decomposition
- Existing separate schemas make this a routing exercise, not a restructuring project
- Creates natural extraction points — once a schema is independent, promoting to service is just changing a connection string
- Each market launch funds the next decomposition step

**Negative:**
- Cross-schema queries break when schemas live on different hosts — reporting, admin dashboards, analytics jobs that JOIN across schemas will fail
- Distributed transactions lost between schemas on different databases — order creation touching orders + payments schemas needs saga pattern or eventual consistency
- Connection management complexity increases — monolith goes from one connection pool to multiple per-region pools
- Hidden coupling risk — shared enums, lookup tables, sequences, or stored procedures referencing multiple schemas may surface unexpectedly
- Operational complexity — monitoring, backup, disaster recovery multiplied across instances and regions
- Team may lack distributed database operations experience

**Mitigations:**
- Materialized views replace cross-schema JOINs — pre-compute joined data, reports read from views
- Audit schema independence before migration — rank schemas by cross-schema dependencies, split most independent first
- Rollback plan for each schema migration — route back to primary within minutes if issues arise
- Enabling team (Multi-Region Infrastructure) owns this decomposition and establishes patterns

---

## ADR-003: Implement Hybrid Regional-Domain Data Architecture

**Title:** Classify data by sensitivity and domain to determine regional placement — regionalize PII, globalize catalogs, domain-own operational data

**Status:** Proposed

### Context

GDPR requires adequate protection for EU citizen personal data. Our platform handles multiple data types with different sensitivity levels: PII (user profiles, addresses, payment details), operational data (orders, inventory, fulfillment), and reference data (product catalogs, CMS content, pricing). Full data localization (everything in every region) is prohibitively expensive. Single global database with SCCs alone doesn't provide the architectural resilience we need if the EU-US regulatory framework shifts. We need a data architecture that satisfies GDPR, performs well across regions, and doesn't duplicate infrastructure unnecessarily. Only ~30-40% of our data is actually PII-sensitive.

### Decision

Implement a three-tier data placement strategy based on data sensitivity and domain:

**Tier 1 — Regional Primary (PII-Critical):** Users and payments schemas get regional primary databases. EU customer data physically resides in EU. US customer data resides in US. No cross-region replication of raw PII. These schemas support the regulatory "where does EU PII live?" question with a clear, auditable answer.

**Tier 2 — Global Shared (Non-Sensitive):** Catalog, CMS, and pricing schemas replicate globally via PostgreSQL logical replication. Product data is not PII — no residency requirement. Global replication ensures fast catalog browsing everywhere (the most common user action).

**Tier 3 — Domain-Owned with Regional Routing (Mixed):** Orders and inventory schemas are domain-owned. The orders schema requires an internal split: `order_header` (customer PII — shipping address, name) is regional; `order_items` (products, quantities, fulfillment status) is domain-local. Foreign key replaced with order ID reference.

**Build a data classification registry** before any migration. Every table and column tagged as PII-Critical, PII-Standard, Operational, or Public. Tags stored in PostgreSQL metadata comments and a central registry table. All routing, compliance, and audit decisions derive from these tags.

**Use CQRS pattern for cross-region reads** — write to regional primary, project pre-joined read-optimized views locally. Admin dashboards and reporting read from projections, never execute cross-region JOINs.

### Consequences

**Positive:**
- Only regionalizes ~30-40% of data — dramatically lower infrastructure cost than full isolation
- Catalog browsing (most common action) has zero latency penalty — globally replicated
- B2B tenants can be offered data residency guarantees per-tenant as a premium feature
- Compliance audits are straightforward — provable answer to "where does EU PII live?"
- Data classification registry becomes single source of truth for routing, compliance, and audit
- Supports both Active-Passive and Active-Active infrastructure models

**Negative:**
- Orders schema split adds complexity — two sub-schemas where there was one
- Three different data strategies means three different operational patterns and failure modes
- Replication lag for global catalog data — price updates take seconds to propagate; customers could see stale prices
- Cross-region reporting requires CQRS projections — adds infrastructure and eventual consistency
- Data classification is an upfront investment that must be maintained as schemas evolve

**Mitigations:**
- Price-confirmation step at checkout handles stale pricing ("price has changed since you added to cart")
- Start with easy wins: catalog goes global Day 1 (zero PII risk), users/payments go regional for market 1, orders split in Phase 2
- Automated compliance tests in CI/CD — synthetic EU data must never appear in non-EU region
- Data classification tags enforced in deployment pipeline per ADR-009

---

## ADR-004: Use Standard Contractual Clauses as Primary GDPR Data Transfer Mechanism

**Title:** Adopt SCCs for EU-US data transfers with architectural readiness for full localization as regulatory contingency

**Status:** Proposed

### Context

Our international expansion requires transferring some data between EU and US regions. GDPR Articles 44-49 govern cross-border data transfers and require a legal mechanism. Options include: Standard Contractual Clauses (SCCs), Binding Corporate Rules (BCRs), the EU-US Data Privacy Framework (DPF) adequacy decision, or full data localization. BCRs cost $200-500K+ and take 12-18 months for approval — incompatible with our budget and timeline. Full localization is architecturally expensive. The EU-US DPF exists but has been legally challenged (predecessors Safe Harbor and Privacy Shield were both invalidated). SCCs are used by ~90% of companies and have remained valid through multiple regulatory shifts. Our Hybrid Regional-Domain architecture (ADR-003) already minimizes the data that actually needs to cross borders.

### Decision

Adopt SCCs as the primary GDPR data transfer mechanism with a belt-and-suspenders contingency:

**Primary mechanism:** Standard Contractual Clauses for all EU-US data transfers. Cloud providers (AWS/Azure/GCP) already offer pre-signed SCCs for infrastructure-level transfers. Application-level data flows we control require our own SCC agreements.

**Transfer Impact Assessment (TIA):** Engage GDPR-specialized legal counsel in Phase 1 for SCC setup and initial TIA. Budget ~$30-40K. Annual TIA review cycle aligned with compliance-as-code pipeline.

**Minimize transfer surface:** Design the system so EU-to-US data transfer is genuinely minimal. EU user data is processed and stored in EU. Only aggregated analytics, global admin access, and catalog sync flow cross-region. The smaller the SCC scope, the lower the risk.

**Contingency: architectural readiness for localization.** The Region-Aware Data Abstraction Layer (ADR-010) means that if SCCs or DPF are invalidated, we can switch to full data localization by reconfiguring the routing layer — not rewriting applications. Document the "SCC → Localization" escalation playbook as an ADR appendix.

**B2B tiered strategy:** B2C data uses SCCs (volume play, standard compliance). B2B enterprise customers who contractually require data localization get it as a premium offering — their data never leaves the region. Turn the constraint into a revenue differentiator.

### Consequences

**Positive:**
- Lowest-cost compliance mechanism — legal fees only, no architectural changes beyond performance-driven work
- Industry-standard approach with established legal precedent and readily available counsel
- ADR-003 already minimizes cross-border data volume, reducing SCC scope and risk
- Cloud providers handle infrastructure-level SCC compliance
- Belt-and-suspenders approach provides regulatory resilience without upfront localization cost
- B2B tiered offering turns compliance into revenue opportunity

**Negative:**
- Regulatory instability — EU courts have invalidated transfer mechanisms twice before
- TIA requires updating when US law changes — ongoing legal overhead
- Some B2B enterprise customers may not accept SCCs regardless of architectural readiness
- Reputational risk during transition periods if a high-profile invalidation occurs
- Dependence on continued EU-US diplomatic cooperation on data protection

**Mitigations:**
- Subscribe to regulatory monitoring (IAPP, law firm alerts) with defined trigger conditions for escalation
- Escalation playbook documented and tested annually
- The same data abstraction layer that enables localization fallback also serves performance purposes — it's not wasted investment
- B2B localization option available immediately for customers who insist

---

## ADR-005: Establish Data Classification-Driven Compliance Tiers

**Title:** Define data classification tiers that drive all residency, encryption, retention, and access decisions across the platform

**Status:** Proposed

### Context

Our platform handles data ranging from public product catalogs to sensitive payment information. GDPR, PCI-DSS, and B2B customer contracts each impose different requirements on different data types. Applying blanket maximum-protection to all data is expensive and operationally burdensome. Applying insufficient protection to sensitive data creates compliance risk. We need a systematic framework that maps data types to protection requirements and drives automated enforcement. This classification underpins ADR-003 (data placement), ADR-004 (transfer mechanisms), ADR-009 (compliance-as-code), and ADR-010 (data routing).

### Decision

Define four data classification tiers with per-tier rules:

| Tier | Examples | Residency | Encryption | Retention | Access |
|---|---|---|---|---|---|
| **PII-Critical** | Payment details, government IDs, health data | Regional primary, no cross-region transfer | At-rest + in-transit + field-level | Minimum required by law | Named individuals, audit-logged |
| **PII-Standard** | Names, emails, addresses, order history | Regional primary, SCC for limited transfer | At-rest + in-transit | Defined retention policy | Role-based, audit-logged |
| **Operational** | Order items, inventory, fulfillment status | Domain-owned, regional routing | At-rest + in-transit | Business-defined | Role-based |
| **Public** | Product catalog, CMS content, pricing | Global replicated | In-transit only | No restriction | Open |

**Implementation:** Every table and column in PostgreSQL tagged with classification tier via metadata comments and a central `data_classification` registry table. CI/CD pipeline reads classification tags to enforce routing rules and block non-compliant deployments. New tables/columns require classification as part of schema migration review.

### Consequences

**Positive:**
- Precision over paranoia — different data gets appropriate protection levels
- Single source of truth for all compliance, routing, and audit decisions
- Enables automated enforcement via CI/CD pipeline (ADR-009)
- Reduces infrastructure cost — only PII-Critical/Standard needs regional primaries
- Makes compliance audits straightforward — "show me all PII-Critical data and where it lives"
- Scales naturally as new data types are added

**Negative:**
- Upfront classification effort across all existing schemas
- Classification must be maintained as schemas evolve — risk of drift
- Edge cases and mixed-sensitivity data require judgment calls
- Over-classification (marking too much as PII-Critical) negates cost benefits
- Under-classification creates compliance risk

**Mitigations:**
- Automated drift detection — CI/CD flags unclassified columns in schema migrations
- Quarterly classification review as part of compliance cycle
- Default to PII-Standard for ambiguous cases — safe without being maximally expensive
- Classification review is part of the enabling team's (GDPR/Compliance) responsibilities

---

## ADR-006: Adopt Phased Team Topology — Enabling Teams to Platform Teams

**Title:** Evolve team structure from component teams through enabling teams to platform + stream-aligned teams over 3 years

**Status:** Proposed

### Context

Our current 25 engineers are organized as component teams (database team, frontend team, payments team, etc.). This structure creates handoff bottlenecks — every cross-cutting feature (like multi-currency) requires coordination across multiple teams. We're adding 10 engineers/year for 3 years (reaching 55). Some engineers have GDPR experience, most don't. We're hiring a mix of local and EU-based engineers supplemented by EU consultants. We need a team structure that supports the phased international expansion without a disruptive Day 1 reorganization, while ensuring GDPR knowledge and multi-region expertise are distributed across the organization. Conway's Law tells us our team structure will dictate our system architecture.

### Decision

Phase the team topology evolution to mirror architecture phases:

**Year 1 (25→35 engineers): Add Enabling Teams.** Keep existing component teams intact — they continue shipping. Create two new enabling teams from new hires:
- **GDPR/Compliance Enabling Team** (2-3 people including EU-based engineers + consultant access): upskills other teams on compliance, owns data classification registry, reviews schema changes
- **Multi-Region Infrastructure Enabling Team** (2-3 people): owns database-first decomposition, proxy layer, regional deployment, establishing patterns other teams follow

Seed 2-3 GDPR-experienced engineers across different existing teams as local experts who upskill their teammates.

**Year 2 (35→45 engineers): Begin Evolution to Platform Teams.** Enabling teams have built the platform layer (data abstraction, tenant management, compliance tooling). They naturally become the **Platform Team** owning shared infrastructure. Existing component teams begin reforming into **stream-aligned teams** around business domains (orders, catalog, B2B) as services are extracted from the monolith.

**Year 3 (45→55 engineers): Full Platform + Stream-Aligned Model.** Platform Team owns cross-cutting infrastructure, compliance, and data layer. Stream-aligned domain teams own end-to-end business capabilities. Markets are a configuration handled by the platform, not a team responsibility.

**Hiring roadmap is a function of architecture roadmap:** Year 1 hires focus on infrastructure/compliance. Year 2 hires focus on platform/B2B capabilities. Year 3 hires focus on market-specific and domain engineering.

### Consequences

**Positive:**
- No disruptive Day 1 reorg — existing teams keep shipping during the most critical execution year
- Enabling teams build expertise and patterns that scale to the whole organization
- GDPR knowledge distributed across teams rather than siloed in a compliance department
- EU hire + consultant hybrid provides local expertise without overcommitting headcount
- Team evolution mirrors architecture evolution — organizational changes feel natural, not forced
- Each hiring cohort maps to the specific capability they'll build

**Negative:**
- Component team bottlenecks persist during Year 1 transition — cross-team dependencies still exist
- Enabling teams could become bottlenecks themselves if understaffed or overloaded with requests
- Year 2 transition from component to stream-aligned teams is the most disruptive organizational change
- Dual-mode operation (component teams + enabling teams) creates coordination overhead
- Risk of enabling teams building solutions without sufficient input from domain teams

**Mitigations:**
- Enabling teams have clear mandates — unblock and upskill, not own and control
- Define explicit interaction models between enabling teams and component teams
- Phase 2 team restructuring planned during Phase 1 — not a surprise
- Regular retrospectives on team topology effectiveness at each phase gate

---

## ADR-007: Adopt Managed Services by Default

**Title:** Default all build-vs-buy decisions to managed services unless the capability is a core business differentiator

**Status:** Proposed

### Context

Our $2M budget covers all expansion costs including headcount. After salaries (~$1.2-1.5M), remaining budget for infrastructure, tooling, and services is $500-800K. Multi-region cloud infrastructure, GDPR compliance tooling, and platform capabilities all compete for this limited budget. Engineering capacity (25 current + 10/year new) must focus on business-differentiating work — the architecture decisions that directly enable international expansion and B2B revenue. Custom infrastructure is a luxury this budget cannot afford.

### Decision

Every infrastructure and platform capability decision defaults to managed services unless the capability meets ALL of these criteria:
1. It is a core business differentiator (directly impacts revenue or competitive advantage)
2. No managed service meets the requirements within acceptable constraints
3. The team has the expertise to build AND operate it long-term

**Managed services by default:**
- **Database:** Managed PostgreSQL (AWS RDS/Aurora, Azure Database for PostgreSQL, or GCP Cloud SQL) with built-in replication, backups, and multi-region support
- **Authentication:** Managed auth service (Auth0, Keycloak on managed infra) — not custom-built
- **API Gateway:** Managed API gateway (Kong, AWS API Gateway) for B2B platform and decomposition bridge
- **Monitoring/Observability:** Managed platform (Datadog, New Relic) — not self-hosted
- **Consent Management:** Third-party (OneTrust, TrustArc) per ADR-009
- **CDN/Edge:** Managed CDN (CloudFront, Cloudflare) — Next.js edge deployment
- **Container Orchestration:** Managed Kubernetes (EKS, AKS, GKE)
- **CI/CD:** Managed pipeline (GitHub Actions, GitLab CI)

**Custom-built (differentiators):**
- Data classification and routing engine (ADR-005, ADR-010) — core to compliance and multi-region strategy
- Tenant management and SLA enforcement (ADR-008) — core to B2B revenue
- Domain-specific business logic (pricing, catalog, orders) — core to e-commerce value

### Consequences

**Positive:**
- Preserves engineering capacity for business-critical, revenue-generating work
- Reduces operational burden — vendor handles patching, scaling, availability
- Faster time-to-market — managed services are production-ready immediately
- Predictable costs — subscription/usage-based pricing vs. unpredictable custom ops costs
- Built-in compliance features (encryption, audit logging, SOC2) from major vendors

**Negative:**
- Vendor lock-in risk — migrating away from managed services is costly
- Ongoing licensing costs that scale with usage — could become expensive at 10M MAU
- Less customization flexibility — must work within vendor constraints
- Multi-vendor environment creates integration complexity
- Vendor outages directly impact platform availability

**Mitigations:**
- Choose vendors with strong multi-cloud support and data portability
- Negotiate enterprise agreements as usage grows
- Abstract vendor-specific APIs behind internal interfaces where practical
- Multi-region deployment provides redundancy against single-vendor regional outages

---

## ADR-008: Build Platform-as-Product for B2B Enablement

**Title:** Create an internal platform layer consumed by both B2C and B2B, with B2C as the first tenant and configurable isolation for B2B customers

**Status:** Proposed

### Context

Our growth target from $50M to $200M requires B2B revenue alongside B2C international expansion. B2B e-commerce commands 3-5x higher revenue per customer but requires multi-tenancy, API access, SLA differentiation, and potentially per-tenant data isolation. Our B2B customers are a mix of large enterprises (needing strong isolation) and smaller businesses (accepting shared infrastructure). Building a separate B2B platform would double engineering effort and fragment the codebase. Our modular monolith with separate schemas already has the foundation for tenant isolation. The API gateway needed for the Strangler Fig decomposition (ADR-002) can serve double duty as the B2B access layer.

### Decision

Build a Platform-as-Product where B2C is the first tenant:

**Phase 1 — MVP Platform (Year 1, alongside market 1 launch):**
- API gateway (managed, per ADR-007) with API key management and rate limiting
- Basic tenant configuration (feature flags, branding)
- Enough to onboard first 2-3 B2B pilot customers
- The same API gateway serves as the Strangler Fig decomposition bridge

**Phase 2 — Tenant Management (Year 2, informed by pilot feedback):**
- Tenant management service with configurable isolation levels
- Schema-level isolation for enterprise tenants (following existing separate-schema pattern)
- Shared infrastructure with feature-flag differentiation for smaller tenants
- Per-tenant data residency selection for B2B customers who require it (ADR-003 enables this)

**Phase 3 — Full Platform (Year 3, revenue-gated):**
- SLA enforcement and monitoring per tenant
- Usage-based billing and metering integration
- Self-service tenant onboarding portal
- Dedicated infrastructure option for premium enterprise tenants

**Revenue-gated investment:** Platform capability tiers are funded by B2B revenue milestones. First $1M B2B revenue funds tenant management. $5M funds dedicated infrastructure options. The platform grows with the business case.

**Find 2-3 B2B pilot customers before building.** Their actual requirements define the platform roadmap — avoid premature abstraction.

### Consequences

**Positive:**
- B2C-as-first-tenant forces clean API boundaries — improves overall architecture quality
- API gateway serves dual purpose — B2B access AND decomposition bridge (one investment, two returns)
- Configurable isolation serves mixed B2B customer base (enterprise and SMB)
- Data residency per B2B tenant becomes a sellable competitive feature
- Platform layer becomes natural home for cross-cutting concerns (auth, rate limiting, compliance)
- Revenue-gated investment prevents overbuilding before market validation

**Negative:**
- Scope creep risk — "platform" is infinitely expandable without strict boundaries
- Premature abstraction if built before having real B2B customer feedback
- Noisy neighbor problem — B2B heavy API usage could impact B2C performance
- Competes with international expansion for engineering attention and budget
- Tenant onboarding operational overhead scales linearly with customers

**Mitigations:**
- Strict MVP scope for Phase 1 — API gateway + keys + rate limiting only
- B2B pilot customers co-design the platform requirements
- SLA enforcement and rate limiting from Phase 1 prevent noisy neighbor issues
- Platform team is the evolved enabling team (ADR-006) — doesn't steal from expansion effort

---

## ADR-009: Implement Compliance-as-Code with Third-Party Consent Management

**Title:** Embed GDPR compliance enforcement in CI/CD pipeline and use third-party tooling for customer-facing consent management

**Status:** Proposed

### Context

GDPR compliance must scale across 5 markets, multiple services (as the monolith decomposes), and B2B tenants. Manual compliance review creates bottlenecks and doesn't scale. Consent management UI (cookie banners, preference centers, data subject access requests) changes frequently with regulatory updates and is a solved commodity problem. Data classification enforcement, audit logging, and policy checks are core platform capabilities that touch every service and must be owned. We need continuous enforcement rather than periodic auditing.

### Decision

Split compliance into two domains — own the architecture, rent the UX:

**Owned — Compliance-as-Code in CI/CD Pipeline:**
- Automated policy checks at deployment for every service and schema change:
  - Does this service handle PII? Is it configured for the correct region?
  - Is audit logging enabled? Is the data classification tag present?
  - Does the schema migration include classification for new columns?
- Non-compliant deployments are blocked before reaching production
- Audit logging built into the platform layer — every data access, modification, and transfer logged
- Data classification registry (ADR-005) is the source of truth for all policy checks

**Rented — Third-Party Consent Management:**
- Use managed consent platform (OneTrust, TrustArc, or equivalent) for:
  - Cookie consent banners per market (UK, Germany, France each have nuances)
  - User preference centers for marketing consent
  - Data Subject Access Request (DSAR) workflow automation
  - Consent audit trail and reporting
- Vendor tracks regulatory updates to consent requirements — we don't

**Annual TIA review cycle** aligned with pipeline checks. Automated monitoring flags when data flows change in ways that affect the Transfer Impact Assessment.

### Consequences

**Positive:**
- Engineers can't accidentally deploy non-compliant code — pipeline blocks it
- Shifts compliance from "periodic audit" to "continuous enforcement" — always compliant, not just at audit time
- Consent management vendor tracks rapidly changing cookie/consent regulations
- Platform-level audit logging provides comprehensive compliance trail
- Scales automatically with service decomposition — new services inherit pipeline checks
- Reduces ongoing compliance engineering effort after initial setup

**Negative:**
- Initial CI/CD pipeline setup requires significant engineering investment
- False positives in compliance checks could slow deployments
- Third-party consent vendor is an ongoing licensing cost ($50-100K/year at scale)
- Vendor dependency for customer-facing compliance — outage impacts consent collection
- Pipeline checks add deployment latency
- Must maintain the policy rules as regulations evolve

**Mitigations:**
- Build pipeline checks incrementally — start with classification enforcement, add rules over time
- Allow emergency bypass with mandatory post-deployment audit (logged, not silent)
- Multi-vendor evaluation for consent management — choose based on EU market coverage
- Compliance enabling team (ADR-006) owns policy rule maintenance

---

## ADR-010: Adopt Region-Aware Data Abstraction Layer

**Title:** Build a data routing abstraction layer that keeps applications region-ignorant while handling data residency transparently

**Status:** Proposed

### Context

Our Hybrid Regional-Domain Data Architecture (ADR-003) means different data types live in different regions. Our Active-Passive to Active-Active migration path (ADR-011) means data routing will change over time. If applications embed region-awareness directly, every routing change requires application code modifications across potentially dozens of services. We need an abstraction that decouples "where data lives" from "how applications access data." This same abstraction serves as the regulatory contingency — if SCCs are invalidated (ADR-004), we reconfigure routing, not applications.

### Decision

Introduce a data routing abstraction layer between applications and databases:

**Implementation:** Database proxy layer (built on PgBouncer or similar) that applications connect to. The proxy routes queries to the correct regional PostgreSQL instance based on:
- Data classification tags (ADR-005) — PII-Critical routes to regional primary
- Request context — EU user requests route to EU data, US to US
- Operation type — reads may go to replicas, writes to primary

**Applications remain region-ignorant.** They connect to a single logical endpoint per schema. The abstraction layer handles:
- Regional routing based on data classification and user context
- Read/write splitting for Active-Passive mode (ADR-011)
- Future Active-Active write routing when infrastructure upgrades
- Failover and connection management across regional instances

**The abstraction layer evolves with the infrastructure:** Phase 1 it routes to Active-Passive (reads to replica, writes to primary). Phase 2-3 it upgrades to Active-Active routing (writes to nearest regional primary). Applications don't change — only proxy configuration changes.

### Consequences

**Positive:**
- Applications never need to know which region they're talking to — clean separation of concerns
- Infrastructure upgrades (Active-Passive → Active-Active) are transparent to applications
- Regulatory contingency is a routing configuration change, not a code rewrite
- Same abstraction enables performance optimization (route to nearest replica)
- Reduces complexity in application code — developers don't think about regions

**Negative:**
- Adds a network hop and potential latency to every database query
- Proxy layer becomes a critical single point of failure per region
- Debugging is harder — issues could be in application, proxy, or database
- Connection pooling across proxy adds operational complexity
- Custom routing logic in the proxy must be built and maintained

**Mitigations:**
- PgBouncer adds <1ms latency per query — negligible for most operations
- Deploy proxy as highly-available cluster per region (managed where possible)
- Structured logging across all layers with correlation IDs for debugging
- Start simple — basic read/write split first, add classification-based routing incrementally

---

## ADR-011: Phase Multi-Region Infrastructure from Active-Passive to Active-Active

**Title:** Launch market 1 with Active-Passive multi-region infrastructure and upgrade to Active-Active when Phase 2 revenue justifies the cost

**Status:** Proposed

### Context

Our target is 5 international markets across EU + US. Multi-region infrastructure is required for both performance (low latency for local users) and compliance (data residency). Active-Active (both regions handle reads and writes independently) provides the lowest latency and highest availability but is the most expensive and operationally complex option. Active-Passive (primary region handles writes, secondary serves reads) is simpler and cheaper but adds write latency for remote users. Our $2M budget cannot afford Active-Active from Day 1 alongside all other expansion costs. However, our Hybrid Regional-Domain data architecture (ADR-003) means most writes are already region-local (EU users write to EU data, US users write to US data), which dramatically reduces Active-Active complexity when we're ready.

### Decision

Phase the infrastructure evolution:

**Phase 1 — Active-Passive (Market 1 launch):**
- Primary region: home region (all writes)
- EU region: read replicas for EU users (catalog, product browsing)
- EU-regional primary for PII schemas only (users, payments) per ADR-003
- Write latency for EU users on non-PII data (orders) acceptable for Phase 1 volume

**Phase 2 — Active-Active (triggered by revenue milestone and market demand):**
- Both EU and US regions handle reads AND writes independently
- Hybrid Regional-Domain model ensures most writes are already region-local — EU user data writes to EU, US to US
- Only globally-shared data (catalog updates, CMS changes) needs cross-region conflict resolution
- Catalog/CMS changes are infrequent — eventual consistency acceptable (ADR-003 mitigations apply)
- Data abstraction layer (ADR-010) handles the routing upgrade transparently — applications don't change

**Upgrade trigger:** Market revenue milestone (defined in ADR-001 readiness scorecard) AND measured write latency exceeding acceptable thresholds for EU users.

**Next.js edge functions** handle personalization, i18n, and request routing from Phase 1 — these provide low-latency user experience even in Active-Passive mode.

### Consequences

**Positive:**
- Phase 1 cost is incremental — one additional region with read replicas, not full Active-Active infrastructure
- Hybrid Regional-Domain data model makes Active-Active upgrade a configuration change via the abstraction layer
- Only globally-shared data needs conflict resolution — dramatically simpler than "true" Active-Active for all data
- Revenue-gated upgrade means the business case is proven before the investment
- Next.js edge functions provide good UX even in Active-Passive mode
- Buy the option for Active-Active without paying upfront

**Negative:**
- Phase 1 EU users experience write latency for non-PII operations (orders, cart updates)
- Active-Passive has a single point of write failure — primary region outage affects all writes
- Upgrade to Active-Active still requires engineering effort for conflict resolution strategy
- Global catalog eventual consistency means brief windows of stale data across regions
- Maintaining two operational modes (AP and AA) during transition adds complexity

**Mitigations:**
- Next.js optimistic UI updates mask write latency for EU users
- Phase 1 volume (single market) is manageable on Active-Passive — write volume is low initially
- Conflict resolution only needed for catalog/CMS — well-understood problem with mature solutions (last-write-wins, vector clocks)
- Design for Active-Active from Day 1 in the data abstraction layer — just don't activate it until Phase 2

---

## Session Summary and Insights

### Key Achievements

- **148 breakthrough ideas** generated for international e-commerce expansion architecture
- **7 organized themes** spanning decomposition, data, compliance, B2B, teams, infrastructure, and market entry
- **11 comprehensive ADR documents** with full Title, Status, Context, Decision, and Consequences
- **Clear execution roadmap** phased across 3 years with revenue-gated progression

### Session Reflections

**Breakthrough Moments:**
- The discovery that separate schemas per module make database-first decomposition a routing exercise, not restructuring — this single fact reshaped the entire strategy
- The convergence of three constraints (budget, GDPR, database bottleneck) on a single solution (database-first decomposition) — three birds, one architectural stone
- API gateway serving dual purpose (B2B access + decomposition bridge) — one investment, two strategic returns
- Revenue-gated investment model turning budget constraints into disciplined phasing

**Creative Facilitation Journey:**
- Constraint Mapping revealed the true solution space by separating hard from soft constraints
- Morphological Analysis systematically explored every parameter combination, preventing tunnel vision
- Six Thinking Hats stress-tested each ADR from 6 perspectives, producing balanced decisions with honest tradeoffs

**Architecture Philosophy That Emerged:**
- Hybrid over purist — every decision chose pragmatic middle ground over ideological extremes
- Phase over plan — build for today's reality, design for tomorrow's option
- Own the differentiator, rent the commodity — invest engineering in what creates competitive advantage
