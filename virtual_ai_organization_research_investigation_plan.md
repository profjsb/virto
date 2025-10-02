# Vision & Scope
**Goal:** Stand up a virtual organization (VO) staffed by AI agents with distinct personae that can ideate, design, build, ship, and grow a real product with real users and revenue, while escalating only the necessary approvals and purchases to a human creator.

---

## Phase 0 — Foundational Questions (Answer Before Building)
1. **Success criteria**
   - What is the first outcome that “proves” the VO? (e.g., public MVP with ≥100 weekly active users, first $1k MRR, or a shipped OSS tool with ≥500 GitHub stars.)
   - What is the max budget and timebox for the pilot? (e.g., $3k / 60 days.)
2. **Risk posture**
   - Appetite for novel model use vs. reliability? Data sensitivity? Rate-limit ceilings?
   - Definition of **irreversible** actions requiring explicit human approval (e.g., payments, legal filings, data sharing outside allowlist).
3. **Operating constraints**
   - Permitted tools/APIs; cloud accounts; code license defaults; data residency.
   - Security baseline (secrets handling, audit logs, PII redaction.)

> **Deliverable:** 1-page VO Charter (goals, constraints, human decision rights, budget).

---

## Phase 1 — Architecture & Orchestration Research
1. **Agent Orchestration Options**
   - Graph-based orchestration (e.g., DAG/flow) vs. chat/round-based vs. planner–executor.
   - Evaluate frameworks (by your criteria, not the marketing):
     - Graph/State: LangGraph-style DAG, custom event bus.
     - Group/Role: CrewAI-/AutoGen-style multi-agent with roles.
     - **MCP** (Model Context Protocol) for tools, file mounts, and capabilities.
     - Message bus: lightweight pub/sub (Redis, NATS) for decoupling.
   - **Decision:** Pick an orchestration primitive first (graph+events recommended), then layer “meetings” and “hiring” as flows on top.
2. **Memory & Knowledge**
   - Short-term: per-agent scratchpad + per-meeting minutes.
   - Long-term: project wiki + vector store for retrieval + structured registries (personae, roles, artifacts).
   - Context hygiene: automatic summarization, deduping, and **context packs** per task.
3. **Artifacts & Storage**
   - Code: mono-repo with `apps/`, `services/`, `infra/`.
   - Docs: `/docs` with ADRs (Architecture Decision Records), meeting minutes, lessons learned.
   - Data: `/data` with schemas, synthetic datasets, evaluation fixtures.
   - Registry services: **Persona Registry**, **Role Registry**, **Tooling/Capability Registry**, **Meeting Template Registry**.
4. **Observability**
   - Event log (who/what/why), run IDs, traces, prompt/version pinning.
   - Metrics: task SLA, cost, token usage, quality scores, incident rate.

> **Deliverables:** Architecture diagram; ADR-001 (orchestration choice); ADR-002 (memory strategy).

---

## Phase 2 — Governance & Decision Rights
1. **The Constitution** (machine-readable + human-readable)
   - Invariants: safety rails, budget guardrails, escalation matrix.
   - Decision Rights: which roles can approve what; thresholds (e.g., spend ≤$50 auto-approve, >$50 route to human).
   - Alignment: mission, user promise, Do-No-Harm rules.
2. **Approval Workflow**
   - Proposal → Risk/Cost Estimator → Auto-checklist → Human Approval (if needed) → Execution → Post-mortem stub.
3. **Auditability**
   - Immutable logs, diffable prompts, reproducible runs, changelog of model/tool versions.

> **Deliverable:** `governance/constitution.md` + `governance/policies.yaml` (schema below).

```yaml
# governance/policies.yaml (excerpt)
spend_thresholds:
  auto_approve_usd: 50
  human_review_usd: 50-500
  executive_review_usd: >500
forbidden_actions:
  - external_data_sharing_without_dpa
  - mass_email_without_unsubscribe
required_checks:
  code_deploy:
    - unit_tests_pass
    - license_scan_clean
    - security_scan_low
  user_research:
    - consent_captured
    - pii_redacted
escalation_matrix:
  legal: [GeneralCounsel]
  security: [CISO]
```

---

## Phase 3 — Role System & Hiring Plan Generator
1. **Role Catalogue (start small)**
   - **Co‑Founders (3)**: Product/CEO, Technical/CTO, Design/CXO.
   - **Makers (expand as needed)**: PM, UX, Eng (FE/BE/ML), DevOps, QA, Data, GTM (Marketing/Growth), Finance/Ops, Legal/Policy.
2. **Persona Model** (schema)
```json
{
  "id": "cxo.design.v1",
  "name": "Rina Kim, Design Co‑founder",
  "style": {"tone": "decisive, user‑obsessed", "writing": "structured bullets + Figma references"},
  "skills": ["ux_research", "wireframing", "brand_systems"],
  "biases": ["prioritize_usability_over_novelty"],
  "risk_limits": {"max_spend": 50, "pii": false},
  "tools": ["figma_mcp", "jira_mcp", "repo"],
  "context_pack": ["charter", "market_briefs", "design_system"]
}
```
3. **Hiring Plan Generator**
   - Input: human “idea prompt” + constraints (budget, deadline, target market).
   - Output: role list with rationales, seniority mix, hiring order, first 3 high‑impact workstreams.

**Prompt (sketch):**
> “Given IDEA, budget B, deadline D, and goal G, propose a minimal founding team (≤5 roles) and the first three workstreams. Each role must include success metrics, required tools, and deliverables within D/3. Produce JSON matching `hiring_plan.schema.json`.”

**`hiring_plan.schema.json` (excerpt):**
```json
{
  "roles": [{
    "role_id": "cto",
    "persona_ref": "cto.core.v1",
    "mission": "Choose stack, ship walking skeleton",
    "deliverables": ["arch ADR", "hello‑world deploy", "CI pipeline"],
    "tools": ["repo", "ci", "cloud"],
    "metrics": {"lead_time_days": 7}
  }],
  "workstreams": [
    {"name": "Walking Skeleton", "owner": "cto", "milestone": "prod hello‑world", "eta_days": 7},
    {"name": "Problem Interviews", "owner": "ceo", "milestone": "10 cust interviews", "eta_days": 10},
    {"name": "Wireframes v1", "owner": "cxo", "milestone": "Figma prototype", "eta_days": 10}
  ]
}
```

---

## Phase 4 — Meeting Rituals as Programs
Represent each meeting as a **templated agent flow** that consumes context packs and produces standardized artifacts.

1. **Stand‑up (daily)**
   - Inputs: sprint board, burndown, blockers.
   - Outputs: `standups/YYYY‑MM‑DD.md` with owner→next action; updated Jira; risk log updates.
2. **Brainstorm (on demand)**
   - Inputs: problem brief, competitive landscape.
   - Outputs: idea map, top‑3 concepts, decision memo.
3. **All‑hands (weekly)**
   - Inputs: metrics dashboard, incident log, spend report.
   - Outputs: company update, OKR check, lessons learned appended.
4. **Design Crit / Arch Review / Post‑Mortem**
   - Structured templates; decisions recorded as ADRs.

> **Deliverables:** `/meetings/templates/*.md` + execution flows wired to orchestration.

---

## Phase 5 — Execution Loops & Quality Gates
1. **Task Inception** → Planner breaks into subtasks → Owners accept → Work → Review → Merge/Deploy.
2. **Quality Gates**
   - Code: unit tests, linters, security scan, license scan, e2e smoke, sandbox deploy.
   - Content: hallucination checks, fact‑source citations, style guide.
   - Research: literature review sheet + confidence score + replication plan.
3. **Evaluation Harness**
   - Golden tasks (fixed), live A/B tasks (rotating), and user‑in‑the‑loop spot checks.
   - Metrics: pass@k, review defect rate, cycle time, blended cost per task, user impact.

---

## Phase 6 — Real‑World Integration (MCP & Tools)
- **MCP tooling map:**
  - Code: repo (git), CI/CD, test runner, package managers.
  - Design: Figma via MCP, asset store.
  - Research: web browse with allowlist, citation capture.
  - Ops: ticketing (Jira/Linear), docs (Notion/Markdown), calendar for meetings.
  - Growth: email, social posting, analytics, ad platforms (gated by approvals).
- **Guardrails:** tool allowlist per persona; spend limits; environment variables via secure vault; redaction proxy for PII.

---

## Phase 7 — Compliance, Legal, and Ethics Checklists
- Data: DPA readiness, consent, retention windows, encryption at rest/in‑transit.
- Privacy UX: consent language for research and telemetry; opt out.
- IP: default license, contributor agreements, model output ownership.
- Jurisdiction: payment provider KYC, ad policy compliance.

> **Deliverable:** `compliance/checklists/*.md` used by approval flows.

---

## Phase 8 — Market & Product Validation
- **Discovery:** problem interviews, JTBD mapping, competitor teardown.
- **Prototyping:** lo‑fi wireframes → interactive prototype → landing page.
- **MVP Criteria:** choose narrow slice (walking skeleton + 1 killer feature).
- **User Tests:** scripted sessions, remote async tests, funnel analytics.
- **Monetization:** pricing experiments; waitlist conversions; payment wiring.

---

## Phase 9 — Metrics & Operating Reviews
- **North Star** (choose one): weekly active collaborators, task‑to‑value lead time, revenue run‑rate.
- **System Health:** success/defect rate, cost per task, mean time to recovery, model/tool drift.
- **Cadence:** weekly all‑hands; monthly Board (human) review.

---

## Phase 10 — 30/60/90 Pilot Plan
**Day 0–7 (Walking Skeleton)**
- Repo + CI + sandbox env; governance files; hiring plan generator v1.
- Three co‑founder personas online; first stand‑ups and brainstorms.
- Ship landing page + waitlist; schedule 10 discovery interviews.

**Day 8–30 (MVP Loop)**
- Lo‑fi prototype → user tests → iterate; minimal analytics; payment test.
- Add 3–5 maker roles as needed; wire quality gates; enable spend approvals.

**Day 31–60 (Public Beta)**
- Ship MVP to early users; support loop; growth experiments.
- Observability dashboards; monthly board review; lessons-learned v1.

**Day 61–90 (Scale or Kill)**
- Hard review vs. success criteria; either sharpen focus and scale, or archive learnings.

---

## Data Schemas (Ready‑to‑Use)
**Meeting Minutes**
```json
{
  "id": "standup-2025-10-01",
  "type": "standup",
  "attendees": ["cto.core.v1", "cxo.design.v1", "ceo.prod.v1"],
  "inputs": ["sprint_board", "risk_log"],
  "decisions": [{"id":"D-123","title":"Adopt FastAPI","adr":"/docs/adr/003.md"}],
  "actions": [{"owner":"cto","task":"setup CI","due":"2025-10-05"}],
  "risks": [{"severity":"M","note":"rate limits"}]
}
```

**Lessons Learned & Ethos (append‑only)**
```json
{
  "id": "ll-2025-10-01",
  "theme": "bias to small bets",
  "evidence": ["experiment-17"],
  "change_to_playbook": "cap spend at $50 per experiment by default"
}
```

---

## Example: End‑to‑End Flow for “Twitter for Cats”
1. Human provides idea prompt + guardrails (budget=$500, timeline=60d).
2. Hiring generator outputs 3 co‑founders + 3 starter workstreams.
3. Stand‑up instantiates tasks; CTO ships walking skeleton; Design ships wireframes; CEO runs interviews.
4. Brainstorm produces 10 concepts; decision memo picks 1 killer feature (e.g., paw‑print reactions).
5. Approval request: buy domain ($12) → auto‑approved; run $100 ad test → human approved.
6. All‑hands reviews metrics; lessons learned updated; next sprint planned.

---

## Research Worklist (What to Investigate Now)
1. **Framework bake‑off:** DAG (LangGraph‑like) vs. role‑chat (CrewAI/AutoGen‑like) vs. planner–executor. Criteria: reliability, tooling support (MCP), traceability, cost.
2. **Memory & Retrieval:** choose vector DB; summarize+pack strategy; context window budgets; dedupe.
3. **Tooling via MCP:** which integrations first (repo, CI, Figma, ticketing, browse, payments sandbox)?
4. **Quality & Safety:** hallucination and source‑required tasks; secure secret management; PII redaction.
5. **Compliance:** privacy/telemetry defaults; open‑source license; ToS for beta users.
6. **User Research:** who’s the first 25 target users; schedule 10 interviews; prepare discussion guide.
7. **Monetization Hypotheses:** subscriptions vs. usage fees; early pricing test design.

---

## Risks & Mitigations
- **Runaway costs:** strict spend caps, per‑agent max tokens, per‑tool quotas.
- **Decision chaos:** machine‑readable constitution + ADRs + owner per workstream.
- **Context drift:** rolling summaries + freshness heuristics + “context packs.”
- **Security leaks:** proxy redaction; strict allowlist; no external data without DPA.
- **Low product–market fit:** force weekly user interviews; kill experiments quickly.

---

## Minimal Tech Stack (Pilot)
- **Core:** Python or TypeScript runtime; orchestration as evented graph; MCP client.
- **Storage:** Postgres (facts), S3-compatible (artifacts), vector DB (retrieval).
- **Infra:** Docker, one-node k8s or serverless; CI (GitHub Actions); monitoring (OpenTelemetry + logs).
- **UI:** Simple ops console (agent runs, approvals, spend, lessons learned).

---

## Next Actions (Concrete, 1–2 Days)
1. Write VO Charter & Policies (use provided YAML skeletons).
2. Implement **Hiring Plan Generator v1** (schema here); generate 3 co‑founder personas.
3. Stand up repo + CI + event log + three meeting templates.
4. Run first Brainstorm for your seed idea; produce decision memo + week‑1 sprint plan.
5. Ship “walking skeleton” service with MCP tool stubs (repo, docs, browse) and an approvals endpoint.

