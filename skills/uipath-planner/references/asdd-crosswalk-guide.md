# ASDD Section Crosswalk

Maps this skill's implementation-oriented SDD sections onto an official UiPath **ASDD** (Automation Solution Design Document) section skeleton, for when the deliverable must follow the customer/PS ASDD structure.

## The rule

**The skill does not auto-generate the ASDD section structure, and does not ship the ASDD template.** (Repo rule: no committed template binaries; and the ASDD layout is a PS/customer artifact that drifts.) Instead:

1. **Styles** come from the customer's Word template via `scripts/sdd-to-docx.sh --reference-doc "<ASDD.docx>"` (fonts, headings, margins).
2. **Structure** comes from this crosswalk: you (or the user) reorganize the generated markdown SDD into the ASDD section order using the table below, then convert.
3. **The user's current ASDD is authoritative.** This table is a *starting* crosswalk based on a common ASDD layout — ask the user for their ASDD section list and reconcile the right-hand column before mapping.

Our SDD deliberately reorganizes content for implementation (it does not mirror any single external document), so the mapping is intentionally many-to-one and one-to-many in places — that is expected, not a defect.

## Crosswalk (RPA SDD → typical ASDD)

| This skill's SDD section | Typical ASDD section |
|---|---|
| §1 Process Overview | Solution Overview / Business Context |
| §2 Process Map | Process Description — TO-BE (diagram) |
| §3 Detailed Process Steps | Detailed Process Description |
| §4 Business Rules | Business Rules |
| §5 Data Definitions | Input / Output Data Definitions |
| §6 Value Mappings | Data Definitions (sub-section) or Appendix |
| §7 Exception Handling + §8 Error Handling | Exception Handling (business + system) |
| §9 Application Inventory | Applications in Scope / Systems Inventory |
| §9 Interactive Auth / Re-auth Handoff | Security & Access (or Solution Architecture note) |
| §10 Master Project Architecture + §11 Project Structure | Solution Architecture |
| §12 Queue Architecture | Solution Architecture (sub-section) |
| §13 Implementation Mode + §14 Packages | Solution Architecture / Technical Approach |
| §15 Credentials & Assets | Security & Credentials |
| §16 Deployment Environment | Infrastructure & Environment |
| §17 Testing Strategy | Testing Approach |
| §18 Next Steps | (drop — internal planner handoff, not an ASDD section) |
| `## Recommended Scope` / `## Decisions Made` | Assumptions & Dependencies / Design Decisions |
| `## Planner Handoff` marker | (drop — internal detection contract) |

For non-RPA templates (Flow, Case, Agent, Coded/low-code Apps, API Workflow), apply the same principle: map the template's TOC onto the ASDD skeleton, drop the internal-only sections (Planner Handoff, Next Steps), and fold product-specific sections (e.g. Case SLA Rules, Agent Evaluation Criteria) into the nearest ASDD architecture/approach section.

## Gaps in either direction

- **ASDD section with no SDD source** (e.g. commercials, project timeline, sign-off page) → the SDD does not produce it; flag for the user to fill from the engagement, do not invent.
- **SDD section with no ASDD home** → keep it in an ASDD Appendix rather than dropping content.

## Caveat

ASDD layouts change between PS versions and customers. Treat this crosswalk as a default; the user-supplied skeleton wins on every disagreement.
