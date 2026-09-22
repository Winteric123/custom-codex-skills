---
name: phd-supervisor-research
description: Research and verify potential PhD supervisors for a specified country, region, or university list, defaulting to thoracic oncology and especially lung cancer. Use when the user supplies a location and schools, asks to screen QS-ranked universities, confirm medical schools or cancer institutions, search all relevant faculties and affiliated hospitals, verify current appointments, contacts, publications, grants, doctoral routes or recruitment status, cross-check Chinese and social sources, label conflicts, or produce evidence-backed Markdown tables, deep profiles, and application-readiness information. Do not use to draft outreach emails, cover letters, research proposals, or other application correspondence.
---

# PhD Supervisor Research

## Outcome

Build a current, traceable supervisor-research package from a location and optional school list. Default to thoracic oncology, especially lung cancer. Stop after evidence gathering, comparison tables, deep research profiles, and application-readiness facts. Do not write outreach text or a research proposal.

## Read before acting

Read these files completely on every full research run:

1. `references/search-playbook.md`
2. `references/evidence-policy.md`
3. `references/output-spec.md`

Use `scripts/init_case.py`, `scripts/render_outputs.py`, and `scripts/validate_case.py` as described below. Keep outputs in the user's current workspace, never in this global skill directory.

## Inputs and defaults

Accept concise input such as:

```text
地区：瑞士
学校：苏黎世大学、巴塞尔大学
```

Apply these defaults unless the user overrides them:

- Research topic: thoracic oncology, with lung cancer as the primary focus.
- Output language: Chinese; preserve official names, project titles, degrees, and paper titles in their source language where useful.
- Evidence date: current date.
- Literature window: the most recent five years plus older landmark work only when it defines the current research line.
- Output: Markdown package and structured JSON. Produce `.xlsx` only when requested or when the user asks for a spreadsheet.
- Intake year: optional. If absent, report only status as of the verification date and do not infer future recruitment.
- Applicant information: not required. Describe general applicant fit, not personal fit.

If the user names schools, include every named school even when it is outside QS top 300 or is a specialist institution not ranked in the main table. If the user supplies only a country or region, first resolve the literal place to the exact country/subnational/multi-jurisdiction ranking filter in `locationResolution`, then use the latest official QS World University Rankings top 300 as the default school scope. Record the ranking system, edition, publication date, included school IDs, and official source IDs in `scopeAudit`; also retain checked-but-excluded institutions with an explicit reason. Every positive inclusion needs a parseable rank or rank band within the threshold. Never recall ranks from memory, and never let `namedByUser` bypass a location-only rank threshold.

Ask a blocking question only when the location or institution name is genuinely ambiguous or the requested research topic differs materially from the default. Otherwise begin directly.

## Initialize the case

For a new case, run:

```powershell
python <skill-dir>/scripts/init_case.py `
  --workspace <current-workspace> `
  --location "<country-or-region>" `
  --schools "<school 1>;<school 2>" `
  --as-of YYYY-MM-DD
```

Omit `--schools` when the case begins from a location-only QS screen. Add `--topic` or `--intake` only when supplied. Reuse an existing case directory instead of reinitializing it.

If an existing case uses a schema earlier than `1.2`, preserve its JSON and rendered files as a historical snapshot. Retain the matching schema-version tools with that snapshot if historical re-rendering is needed; the `1.2` tools are not a drop-in replacement for a `1.1` case and must not re-render it in place. Migrate into a new dated case directory, populate the new scope, affiliation, opportunity, audit, and source-metadata fields, and pass strict validation before treating it as current. Do not overwrite or silently reinterpret an older rendered table.

## Research workflow

### 1. Fix the scope

- Record location, named schools, research topic, QS rule, verification date, and optional intake.
- Verify each school's current official name, QS status, medical or health-sciences structure, and affiliated hospitals/cancer centres.
- Do not silently exclude a named school because it lacks a medical school. Record the actual structure and relevant collaborating institutions.
- Distinguish a university-owned hospital, an affiliated hospital, and a research collaborator.
- Keep only included schools in `schools.json`; for a location-only ranking screen, put checked exclusions in `case.json.scopeAudit.excludedInstitutions` so omissions remain auditable.

### 2. Search every relevant institutional branch

Cover medicine/clinical services, life sciences, cancer centres and affiliated hospitals, pathology/diagnostics, public health/biostatistics, engineering/AI/imaging, pharmacy/drug discovery, and veterinary/comparative oncology. Mark every branch as `searched`, `candidates_found`, `not_present`, or `blocked_unverified` in `data/coverage.json`. List only units actually inspected and documented by the row's sources; for `candidates_found`, retain school-bound branch evidence and current official candidate-bound research/current-role evidence for every listed person.

Search official directories, faculty and department pages, laboratory pages, cancer-centre programmes, doctoral programme PI lists, thesis repositories, institutional research portals, and job portals. Use English, local-language, and Chinese name variants. Search across all faculties, not only the medical school.

Use parallel agents by school or evidence type when helpful. Give each agent a separate structured batch file and merge centrally. Do not let multiple agents edit the same final file.

Run at least two deliberate expansion passes, then a separate final saturation pass. End discovery only after the coverage matrix is complete and that final pass adds no qualified candidate. Describe the result as the publicly identifiable candidate set within the stated scope, not as every possible internal supervisor. `case.status: complete` means the package is generated, not that every branch was exhausted. A zero-addition pass with any `blocked_unverified` branch must document a retry/recheck and is only bounded public-search saturation, never proof of exhaustive coverage.

### 3. Verify every person

- Disambiguate names with at least two of affiliation, email, ORCID, specialty, stable co-author network, or official profile.
- Separate academic title, administrative/clinical role, group leadership, and formal doctoral-supervision evidence.
- Record personal email, unit/group mailbox, assistant contact, and secretariat address as different contact types. A personal/clinical email must visibly identify the candidate, not another person or an office alias. Never infer an email pattern.
- Verify current role and contact from a current official source. Preserve future announced changes and stale-page conflicts.
- Store the person's actual current-role `verifiedAt` date rather than forcing it to equal `case.asOf`; back it with at least one current official role source accessed on that date, and do not use it as a catch-all literature or recruitment date. When it is more than 30 days older, surface “核验已陈旧，使用前需复核”, and reverify before strict delivery once it exceeds 90 days.
- Represent joint and cross-institution appointments with `affiliations[]` and `additionalSchoolIds`; do not flatten a university, hospital, cancer centre, and collaborator into one ambiguous affiliation string. For every affiliation assigned to an `additionalSchoolId`, retain at least one current official-institution source whose `subjectIds` explicitly include both the candidate ID and that additional school ID; a person-only page or a school-only page cannot be spliced together to assert cross-school membership.
- Give every published contact its own source IDs. A department mailbox or contact form is not a personal email. A `published_current` personal or clinical email needs one same current official, contact-domain, candidate-bound source; do not assemble those properties across different records. Treat a researcher-controlled ORCID address as a lead until an institutional page independently verifies it.
- For person-level role, affiliation, personal/clinical contact, research, direct-evidence, and research-anchor claims, put the candidate's stable ID in each supporting source's `subjectIds` and record a structured `personRoles[]` entry. Use the exact role actually stated; do not infer a project or authorship role from academic rank or another person's clause on a shared page, and do not use migration placeholders as `exactLabel`. Explicit equal-contribution/co-senior authorship is allowed. Use `independent_faculty` only for explicit full/associate (or tenure-track assistant) professor titles and `unit_head` only for explicit department/division/service/centre/institute leadership; PD/attending alone is not independence. If a page does not name the person, do not bind it to that person. A generic programme page can support programme rules, but not a personal title, contact, or direct research claim unless it explicitly states that fact.
- Map current-role evidence by field, not as one undifferentiated pool. `claimSourceIds.academicRole`, `.adminClinicalRole`, and `.group` may cite only current official candidate-bound sources whose `personRoles[].roleType` and retained label are compatible with that field. A label saying `specific title not retained or inferred` proves no concrete role and must not support those fields or a concrete `affiliations[].role`; downgrade the displayed value to an explicit unverified marker until the page is reread. In particular, programme-host, doctoral-supervisor, trial, grant, collaboration, team-member, or authorship roles do not prove an academic title or lab/unit appointment; `programme_host` may support an administrative programme role only.
- Keep school-level doctoral-programme existence, person-level supervision eligibility, and current vacancy status as three separate fields.

### 4. Deepen research evidence

- Use official group pages for declared focus.
- Use PubMed, Europe PMC, publisher pages, or lawful full text to verify publications and methods.
- Use official grant databases, project pages, and trial registries to verify current work and exact roles.
- Distinguish first, senior, corresponding, co-PI, site contact, data contributor, and ordinary co-author roles. A collaborative paper proves participation, not ownership of every sample, platform, or work package.
- For each A-tier candidate, include at least two recent, direct topic-evidence records when available. If unavailable, lower the tier or state the exception explicitly.
- Require T1/T2 to have two candidate-bound current official facts: an independent group-leader/PI role and a direct lung-cancer research line. They may come from one page or from separate official role and research pages; never copy a role from one page into another source record. A publication alone does not prove a current independent line. Future evidence cannot support a current classification before it becomes effective or public.
- Write a 150–250 Chinese-character direction overview and structured profile exceeding 500 Chinese characters for each A-tier candidate. These are different length requirements.

### 5. Verify doctoral paths and opportunities

Use current official programme rules, admissions/funding pages, and vacancy portals. Store each materially different person-, lab-, or programme-level route in `opportunities[]`; keep its status, deadline type, deadline, contact policy, and source IDs separate. A programme call does not prove that one named PI is accepting a student. For person-scoped `open_current`, the vacancy must explicitly name the candidate and its source record must list that candidate in `subjectIds`; apply the same candidate-binding rule to lab-scoped openings until a validated lab-entity registry exists. Treat legacy top-level opportunity fields only as a conservative summary and never let them override the route-level evidence.

Never convert any of the following into “currently recruiting a PhD” without an explicit current vacancy or official call:

- PI or group-leader status
- participation in a funded grant
- a project containing doctoral students
- a supervisor list or host list
- patient recruitment for a clinical trial
- a past or expired vacancy

Report deadlines, funding, employment status, eligibility, and application route only when directly supported.

For `route_confirmed_no_vacancy`, `no_public_evidence`, and `direct_enquiry_recommended`, retain a dated `recruitmentAudit` with required `checkedScopes`, non-empty `portals` and `queries`, showing which official person/lab/programme pages or vacancy portals were checked, a summary, and source IDs. At least one current official vacancy portal bound to the candidate or school must be accessed on `checkedAt`, and no cited audit source may postdate it. Absence of a vacancy after that audit is still not proof of private availability or non-availability.

Use `direct_enquiry_recommended` only for a non-D record with high/medium-confidence current role, a candidate-bound current official personal-role source, a published contact channel, and a current official doctoral/recruitment route. Otherwise use `no_public_evidence` or `unverified`; this label never means currently recruiting.

### 6. Cross-check Chinese and social sources

For each candidate, run at least three wider Chinese-web query variants and at least two public Xiaohongshu query variants using the English name plus institution/topic. Include professional medical media, public WeChat indexing, and Zhihu where accessible. Store the check date, actual queries, summary, access note, and source IDs. Treat these sources as discovery or conflict signals unless they reproduce an attributable primary source.

Do not bypass login walls. If Xiaohongshu or another platform cannot be inspected, use `public_access_blocked` with an access note, not `not_found_publicly`. `not_searched` is draft-only and is rejected for a complete strict run. Never let a social post override a newer official source without explicit corroboration.

### 7. Build application-readiness facts

Treat this as the final pre-writing step. For each A-tier candidate, record:

- the official contact protocol and whether unsolicited PI contact is supported, discouraged, or unverified;
- the application window, eligibility rules, required documents, and doctoral-programme deadline;
- whether a proposal is required, plus any official format, length, template, or submission rule;
- the verified funding model, employment/stipend status, tuition/fees, and external-funding constraints when public;
- the expected main/co-supervision setup and any programme-level co-supervisor requirement;
- the safest recent research anchor;
- the verified unresolved research gap;
- one bounded proposed aim derived from that gap;
- general applicant backgrounds that fit;
- doctoral route and supervision questions;
- resource, samples, platform, ethics, funding, and daily-supervision questions;
- cautions about role, evidence maturity, or topic transfer.

Link the factual items to source IDs. Use explicit missing states when information is not public. Mark `researchGap`, `proposedAim`, and `generalApplicantFit` with their explicit `...AnalystDerived: true` flags; `researchAnchor` must remain a sourced description of the supervisor's work. No string anywhere in `applicationReadiness` or a doctoral work package may become an email subject, salutation, sign-off, first-person application request, CV-attachment sentence, personalized pitch, or full research plan. This skill ends after this evidence package is rendered and validated.

### Research-only handoff boundary

If the user later invokes a separate outreach or proposal-writing workflow, hand off only:

- verified role, affiliation, contact, programme, admissions, funding, and opportunity facts with source IDs;
- the sourced `researchAnchor`;
- `researchGap` and `proposedAim`, explicitly marked analyst-derived and not approved by the supervisor;
- open questions, resource assumptions that require confirmation, and cautions.

Do not pre-compose a subject line, salutation, opening sentence, personalized fit paragraph, promise of methods/resources, or proposal prose. The later writing workflow must independently collect the applicant's CV/background, target intake, language, title preference, exclusions, and output preferences, then recheck unstable facts before using the handoff.

## Structured data is the source of truth

Write all verified content first to the JSON files defined in `references/output-spec.md`. Link every material claim to source IDs. Generate reports only from those files.

Do not manually type evidence totals into Markdown. `render_outputs.py` must compute evidence-record counts and canonicalized unique-URL counts from `data/sources.json`, then reuse one identical statistics line across outputs. Give each source exactly one primary `type`, an `authorityClass`, a `medium`, and the applicable `claimDomains`; reuse one source ID across claims. Add `workId` or stable identifiers when DOI/PMID/PMCID, grant, trial, or posting identifiers exist so alternate landing pages cannot be counted as independent underlying evidence.

The page host, `authorityClass`, and primary `type` must describe the page that was actually opened. A PubMed/PMC/Europe PMC/DOI publication page, ClinicalTrials registry record, SNSF funder record, or QS ranking page must never be relabelled as `official_institution` or as an institutional role/contact profile to satisfy a current-role or contact requirement.

## Render and validate

After research data are complete, run:

```powershell
python <skill-dir>/scripts/validate_case.py --case-dir <case-directory>
python <skill-dir>/scripts/render_outputs.py --case-dir <case-directory>
python <skill-dir>/scripts/validate_case.py --case-dir <case-directory> --strict
```

Fix preflight errors before rendering, then fix every strict-validation error before delivery. Warnings about inaccessible sources, uncertain roles, or missing public contacts must remain visible in the report.

If the user requests Excel, use the spreadsheet artifact workflow to create and verify an `.xlsx` from the same JSON data; do not maintain a second hand-edited dataset.

## Required deliverables

Deliver clickable paths to:

- `00-INDEX.md`
- `01-SCHOOL-SCOPE.md`
- `02-SUPERVISOR-TABLE.md`
- `03-COVERAGE-MATRIX.md`
- `04-EVIDENCE-CONFLICTS.md`
- `05-A-TIER-DEEP-PROFILES.md`
- `06-APPLICATION-READINESS.md`
- `07-SOURCE-LEDGER.md`

State the verification date, included-school count, checked-exclusion count, candidate count, A-tier count, evidence-record count, unique-URL count, and unresolved warnings exactly as produced by validation. Explicitly say that the package excludes outreach-email and research-proposal drafting.

## Non-negotiable boundaries

- Do not invent ranks, titles, emails, positions, grants, PMIDs, DOIs, samples, methods, or supervisory authority.
- Do not cite search-result snippets as evidence; open and inspect the underlying page.
- Do not use a paper's method to claim that the person's own laboratory controls the platform.
- Do not label an association predictive without a treatment-interaction design or equivalent evidence.
- Do not equate `not found publicly` with `does not exist`.
- Do not claim exhaustive coverage beyond the documented search scope.
- Do not write outreach correspondence or a research proposal in this skill.
