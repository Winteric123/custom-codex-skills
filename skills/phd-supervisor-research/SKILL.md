---
name: phd-supervisor-research
description: Research and verify oncology PhD supervisors by location or university, including current roles, contacts, doctoral routes, application materials, and paper-level experimental/bioinformatics/omics/clinical-translation portfolios. Prioritize adult lung/solid-tumour research, tumour immunity, translational genetics/genomics, multi-omics and cancer molecular biology. Default-exclude supervisors primarily focused on paediatric oncology or haematologic malignancies, plus nuclear medicine, radiomics/core clinical tumour imaging and engineering/computing/standalone-data-only appointments; parallel or secondary paediatric/haematologic work alone is not disqualifying. Research facts only; do not draft letters or proposals.
---

# PhD Supervisor Research

## Outcome

Build a current, traceable supervisor-research package from a location and optional school list. Default to the focused `lung_cancer` profile. Use the broader `cv_aligned_oncology` profile only when the user explicitly requests it or supplies applicant evidence that supports a broader oncology scope; configure it from the current task rather than from data embedded in this skill. Every full research run also evaluates each retained A/B/C supervisor's recent publication portfolio on independent axes: experimental/basic work, applied bioinformatics, omics, theoretical methods, pure clinical work, and the depth of genuine clinical translation. Include a route-specific application-materials audit before handing facts to a writing workflow. Stop after evidence gathering, comparison tables, deep research profiles, and application-readiness facts; do not draft application letters or a research proposal.

## Read before acting

Read these files completely on every full research run:

1. `references/search-playbook.md`
2. `references/evidence-policy.md`
3. `references/output-spec.md`

For candidate screening in either topic profile, read `references/candidate-exclusions.md`. It defines configurable screening defaults and the boundary between a research programme and an auxiliary method.

Whenever a task finds, updates, audits, compares, or displays supervisor contact channels, read `references/contact-verification-playbook.md` completely. It defines the search ladder, ownership and currentness labels, publication-correspondence-email boundary, fallback channels, and contact-output contract.

For every full supervisor-research run, and whenever recent publications, laboratory method mix, clinical relevance, translational depth, or method-based prioritisation are requested, read `references/research-method-translation-audit.md` completely. It defines the mandatory per-supervisor portfolio assessment, verifiable five-to-eight-year search stages, separate bioinformatics and omics tags, structured corresponding/senior-author evidence, paper-level experimental/methods/clinical boundaries, clinical-translation axis, review-depth labels, and independent `MTG` grade.

For the optional `cv_aligned_oncology` profile or a CV-based scope update, also read `references/cv-aligned-scope.md` completely. Inspect the evidence supplied in the current task and keep applicant-specific details in the case workspace, never in this installed skill.

When verifying doctoral applications or preparing a research-only writing handoff, read `references/application-materials-checklist.md` completely. It distinguishes motivation/personal statements, cover letters, prior supervisor contact, recommendation letters and research proposals without assuming they are required everywhere.

Use `scripts/init_case.py`, `scripts/render_outputs.py`, and `scripts/validate_case.py` as described below. Keep outputs in the user's current workspace, never in this global skill directory.

## Inputs and defaults

Accept concise input such as:

```text
地区：瑞士
学校：苏黎世大学、巴塞尔大学
```

Apply these defaults unless the user overrides them:

- Research topic/profile: `lung_cancer` by default. Use `cv_aligned_oncology` only when the user explicitly requests a broader profile or current applicant evidence supports user-approved cancer-related translational genetics/genomics, multi-omics, molecular/cell-biology or epidemiology extensions. These axes are search preferences, not proof of applicant expertise. Do not apply the broad profile to an old case by merely changing its display topic.
- Disease-breadth priority: after the institutional gate, persistent research exclusions, oncology relevance and evidence quality have been applied, distinguish programmes limited to one or a few named tumour types from broad multi-tumour/pan-cancer or general cancer-mechanism programmes. Among otherwise comparable limited-tumour programmes, rank verified thoracic malignancy work first, with lung cancer/NSCLC/SCLC ahead of oesophageal cancer, pleural mesothelioma, thymic/mediastinal and other verified thoracic tumours. This is a preference, not an eligibility shortcut: it cannot override stronger supervision, route or evidence differences, and broad programmes are assessed on their own alignment rather than automatically demoted for not being thoracic-exclusive.
- Institutional eligibility: exclude engineering-only, computer-science-only, and standalone AI/data-science/data-analytics-only appointments. A lung-cancer paper does not bypass this gate. Verified current medical/hospital/cancer-institute joint appointments and computational research based in medical units may qualify; use the boundary in `references/search-playbook.md`.
- Oncology relevance: before recommending a person, verify a current, person-specific cancer research line or named current cancer project from official evidence, then cross-check recent primary literature. Retain the actual tumour/disease, scientific question and person's role. Generic omics, immunology, genetics, metabolism or molecular biology, a medical/cancer-institute appointment, a cancer keyword in an introduction, or one historical collaborative paper is insufficient. Classify direct current oncology, current cancer-project participation, historical-only evidence and unresolved/non-oncology leads as described in `references/candidate-exclusions.md`.
- Research exclusions: exclude a supervisor for paediatric/childhood oncology or haematologic malignancy only when current person-specific evidence shows that field is the main or predominant focus of the person's overall current research programme. Do not exclude merely because it is a co-equal parallel, secondary, occasional collaborative or one-of-several pan-cancer line within an otherwise eligible programme. If dominance cannot be resolved, retain the otherwise eligible candidate with a dated `dominance_unresolved_retained` caution and recheck priority; uncertainty is not an exclusion. Separately, continue to exclude nuclear medicine/radionuclide diagnosis or treatment and radiomics/clinical or molecular tumour imaging when they are a core or explicitly parallel research line. Apply these defaults in both profiles and all locations before topic scoring, using `references/candidate-exclusions.md`. Molecular mechanisms and omics in adult solid tumours remain in scope; classify imaging and computation by their actual role. A user may explicitly override an exclusion for a named person or defined field.
- Output language: Chinese. Whenever any supervisor information is shown to the user—in chat, Markdown, spreadsheet, JSON display fields, comparison tables, profiles, or a handoff—the faculty/department/unit, current appointment/title, and research direction must each have a Chinese rendering. Put Chinese first; an official English/German/local-language label may follow in parentheses or a separate source field, but it must never be the only displayed value for those three items. Preserve official names, project titles, degrees, and paper titles in their source language where useful. Translate conservatively: do not upgrade rank, independence, clinical seniority, or supervisory authority. If an exact Chinese equivalent cannot be supported, give a bounded Chinese functional description, retain the official label, and mark the uncertainty; if the fact itself is unavailable, display `未公开` or `未核实` in Chinese rather than leaving the field blank.
- Evidence date: current date.
- Literature window: for ordinary topic verification, use the most recent five years plus older landmark work only when it defines the current research line. In every full research run, also apply the rolling five-year portfolio audit in `references/research-method-translation-audit.md` to every retained A/B/C supervisor; if fewer than five eligible candidate-led original papers are found, extend to eight years and expose the extension. A narrow factual update need not rebuild an unchanged portfolio unless the user asks for re-audit or the prior audit is stale or provisional in a way that affects the answer.
- Method/translation priority: treat the `MTG` result as a separate fit axis. When candidates are otherwise comparable within the same A/B/C tier and the user seeks clinical + experimental + omics training, use stronger verified integration and clinical-translation depth only as a secondary ordering or tie-break. Never automatically promote or demote an A/B/C tier from `MTG`, and never let it overwrite topic relevance, supervision evidence, institutional eligibility, research exclusions, opportunity status, outreach holds, or an explicit user preference.
- Output: Markdown package and structured JSON. Produce `.xlsx` only when requested or when the user asks for a spreadsheet.
- Intake year: optional. If absent, report only status as of the verification date and do not infer future recruitment.
- Initial-enquiry preference: first establish whether an accessible PhD programme/route exists for the named supervisor or institution. Do not make detailed programme type, scholarship availability or funding preferences into initial questions to the user or PI. Keep programme existence separate from the person's eligibility and an open vacancy. Official facts may still be recorded during a full requested research audit; detailed application/funding questions are deferred until the user requests them or enters that application stage.
- Vacancy-neutral retention: failure to verify a current opening, absence of a public vacancy, a closed call, an inaccessible vacancy page, or an `unverified` recruitment state is never by itself a reason to exclude or delete an otherwise eligible supervisor. Keep research eligibility, supervision evidence, priority tier, opportunity status, and outreach action state separate. An explicit negative PI/lab reply or official capacity statement may justify a dated, scope-limited temporary outreach hold, but does not remove the person's research record unless an independent institutional, research-direction, oncology-relevance, role, or user-specified exclusion also applies. Even then, preserve the historical research evidence in the coverage/source audit rather than erasing it.
- Applicant information: not required for research verification. If a current CV or background statement is supplied, use it only to configure the case-local search scope and record a neutral evidence-based alignment/gap in `notes`, not application prose. It is not proof of current skills or person-specific fit; keep `applicationReadiness.generalApplicantFit` general and analyst-derived.

If the user names schools, include every named school even when it is outside QS top 300 or is a specialist institution not ranked in the main table. If the user supplies only a country or region, first resolve the literal place to the exact country/subnational/multi-jurisdiction ranking filter in `locationResolution`, then use the latest official QS World University Rankings top 300 as the default school scope. Record the ranking system, edition, publication date, included school IDs, and official source IDs in `scopeAudit`; also retain checked-but-excluded institutions with an explicit reason. Every positive inclusion needs a parseable rank or rank band within the threshold. Never recall ranks from memory, and never let `namedByUser` bypass a location-only rank threshold.

Ask a blocking question only when the location, institution, or scope is genuinely ambiguous in a way that changes the result. An explicit broader or narrower topic overrides the default; otherwise begin directly.

## Initialize the case

For a new case, run:

```powershell
python <skill-dir>/scripts/init_case.py `
  --workspace <current-workspace> `
  --location "<country-or-region>" `
  --schools "<school 1>;<school 2>" `
  --topic-profile lung_cancer `
  --as-of YYYY-MM-DD
```

Omit `--schools` when the case begins from a location-only QS screen. The script defaults to `lung_cancer`; pass `--topic-profile cv_aligned_oncology` only for an explicitly selected broad profile. Add `--topic` or `--intake` only when supplied. Reuse an existing matching case rather than reinitializing it. A deliberate scope expansion of an existing lung case belongs in a new case/report with provenance, not an in-place relabelling of old T codes or sources.

If an existing case uses a schema earlier than `1.2`, preserve its JSON and rendered files as a historical snapshot. Retain the matching schema-version tools with that snapshot if historical re-rendering is needed; the `1.2` tools are not a drop-in replacement for a `1.1` case and must not re-render it in place. Migrate into a new dated case directory, populate the new scope, affiliation, opportunity, audit, and source-metadata fields, and pass strict validation before treating it as current. Do not overwrite or silently reinterpret an older rendered table.

## Research workflow

### 1. Fix the scope

- Record location, named schools, research topic, QS rule, verification date, and optional intake.
- Record `case.topicProfile` and the accepted broad-oncology axes/priority bands when applicable. Missing `topicProfile` in a historical schema-1.2 case means `lung_cancer`; free-text `case.topic` does not switch classification semantics.
- Record the default institutional eligibility gate and any explicit user override separately from research-topic relevance. Naming a technical university is not permission to include its engineering-only staff. A skill update alone does not authorize rescreening or removing people from an existing user-approved list.
- Record the active research exclusions from `references/candidate-exclusions.md` in `case.limitations`; preserve case-specific overrides. A medical/cancer appointment does not waive a research-direction exclusion. Apply updated defaults to new searches; revisit an existing list when the user requests filtering or rescreening.
- Verify each school's current official name, QS status, medical or health-sciences structure, and affiliated hospitals/cancer centres.
- Do not silently exclude a named school because it lacks a medical school. Record the actual structure and relevant collaborating institutions.
- Distinguish a university-owned hospital, an affiliated hospital, and a research collaborator.
- Keep only included schools in `schools.json`; for a location-only ranking screen, put checked exclusions in `case.json.scopeAudit.excludedInstitutions` so omissions remain auditable.

### 2. Search every relevant institutional branch

Cover medicine/clinical services, life sciences, cancer centres and affiliated hospitals, pathology/diagnostics, public health/biostatistics, engineering/AI/imaging, pharmacy/drug discovery, and veterinary/comparative oncology. Inspect excluded-field units to document their structure and find independently eligible groups or joint appointments. Apply both the institutional gate and research exclusions before adding names to the deliverable or assigning topic/supervision/priority codes. Mark every branch as `searched`, `candidates_found`, `not_present`, or `blocked_unverified` in `data/coverage.json`. List only units actually inspected and documented by the row's sources; for `candidates_found`, retain school-bound branch evidence and current official candidate-bound research/current-role evidence for every listed eligible person.

Search official directories, faculty and department pages, laboratory pages, cancer-centre programmes, doctoral programme PI lists, thesis repositories, institutional research portals, and job portals. Use English, local-language, and Chinese name variants. Search across all faculties, not only the medical school.

Use parallel agents by school or evidence type when helpful. Give each agent a separate structured batch file and merge centrally. Do not let multiple agents edit the same final file.

Run at least two deliberate expansion passes, then a separate final saturation pass. End discovery only after the coverage matrix is complete and that final pass adds no qualified candidate. Describe the result as the publicly identifiable candidate set within the stated scope, not as every possible internal supervisor. `case.status: complete` means the package is generated, not that every branch was exhausted. A zero-addition pass with any `blocked_unverified` branch must document a retry/recheck and is only bounded public-search saturation, never proof of exhaustive coverage.

### 3. Verify every person

- Disambiguate names with at least two of affiliation, email, ORCID, specialty, stable co-author network, or official profile.
- Verify the actual faculty/department and current appointments before inclusion. Engineering-only (including biomedical engineering), computer-science-only, or standalone AI/data-science/data-analytics-only candidates stay outside the supervisor roster, including its D tier; preserve a sourced exclusion note instead. An official medical joint appointment may qualify, but collaboration or publication affiliations alone do not establish one.
- Verify the dominant disease focus for the paediatric/haematologic rule and the core or explicit parallel role for the nuclear-medicine/imaging rule against `references/candidate-exclusions.md`. Record a retained secondary or parallel paediatric/haematologic line in the candidate notes; it is not a user exception because it passes the default rule. A confirmed main/predominant disease-focus exclusion remains outside the roster and counts. If disease-focus dominance is unresolved, retain an otherwise eligible candidate with a dated caution rather than deleting or excluding the person. A department label or one collaborative paper alone establishes neither programme dominance nor a current excluded research line.
- For every recommended A/B/C person, record an oncology-relevance audit in `notes`: actual disease/model or cancer-risk endpoint, cancer-specific question, current official source IDs, literature cross-check and exact person role. Mark project participation separately from an independent oncology programme. Confirmed non-oncology and unresolved-relevance leads remain outside the recommended roster; historical-only discoveries may be retained solely as explicit D-tier warnings when otherwise permitted.
- Separate academic title, administrative/clinical role, group leadership, and formal doctoral-supervision evidence.
- Record personal email, unit/group mailbox, assistant contact, and secretariat address as different contact types. A personal/clinical email must visibly identify the candidate, not another person or an office alias. Never infer an email pattern.
- Follow `references/contact-verification-playbook.md` before declaring a contact unavailable. Search current official person pages and every applicable official fallback (including person-directed forms, group/unit/department/secretariat channels, assistants and phones) before candidate-bound recent correspondence records. Preserve publication-only email addresses as time-stamped leads rather than current official personal contacts, and never let `not_public` overwrite an existing fallback route.
- Verify current role and contact from a current official source. Preserve future announced changes and stale-page conflicts.
- Store the person's actual current-role `verifiedAt` date rather than forcing it to equal `case.asOf`; back it with at least one current official role source accessed on that date, and do not use it as a catch-all literature or recruitment date. When it is more than 30 days older, surface “核验已陈旧，使用前需复核”, and reverify before strict delivery once it exceeds 90 days.
- Represent joint and cross-institution appointments with `affiliations[]` and `additionalSchoolIds`; do not flatten a university, hospital, cancer centre, and collaborator into one ambiguous affiliation string. For every affiliation assigned to an `additionalSchoolId`, retain at least one current official-institution source whose `subjectIds` explicitly include both the candidate ID and that additional school ID; a person-only page or a school-only page cannot be spliced together to assert cross-school membership.
- Give every published contact its own source IDs. A department mailbox or contact form is not a personal email. A `published_current` personal or clinical email needs one same current official, contact-domain, candidate-bound source; do not assemble those properties across different records. Treat a researcher-controlled ORCID address as a lead until an institutional page independently verifies it.
- For person-level role, affiliation, personal/clinical contact, research, direct-evidence, and research-anchor claims, put the candidate's stable ID in each supporting source's `subjectIds` and record a structured `personRoles[]` entry. Use the exact role actually stated; do not infer a project or authorship role from academic rank or another person's clause on a shared page, and do not use migration placeholders as `exactLabel`. Explicit equal-contribution/co-senior authorship is allowed. Use `independent_faculty` only for explicit full/associate (or tenure-track assistant) professor titles and `unit_head` only for explicit department/division/service/centre/institute leadership; PD/attending alone is not independence. If a page does not name the person, do not bind it to that person. A generic programme page can support programme rules, but not a personal title, contact, or direct research claim unless it explicitly states that fact.
- Map current-role evidence by field, not as one undifferentiated pool. `claimSourceIds.academicRole`, `.adminClinicalRole`, and `.group` may cite only current official candidate-bound sources whose `personRoles[].roleType` and retained label are compatible with that field. A label saying `specific title not retained or inferred` proves no concrete role and must not support those fields or a concrete `affiliations[].role`; downgrade the displayed value to an explicit unverified marker until the page is reread. In particular, programme-host, doctoral-supervisor, trial, grant, collaboration, team-member, or authorship roles do not prove an academic title or lab/unit appointment; `programme_host` may support an administrative programme role only.
- Keep school-level doctoral-programme existence, person-level supervision eligibility, and current vacancy status as three separate fields.

### 4. Deepen research evidence

- Apply the declared topic profile, institutional gate and research exclusions before T1–T4. For `cv_aligned_oncology`, a current independent cancer-immunity, immunometabolism, precision-oncology or other approved broad-oncology line can be direct even without lung cancer, but must have candidate-bound cancer/oncology evidence and a stated match axis. For `lung_cancer`, retain the original direct lung-cancer requirement. Generic immunology, omics, AI or biomaterials without an approved cancer connection do not qualify merely through transferable methods. Keep discovery bands L1–L3 separate from T evidence quality and A–D readiness.
- Use official group pages for declared focus.
- Use PubMed, Europe PMC, publisher pages, or lawful full text to verify publications and methods.
- Use official grant databases, project pages, and trial registries to verify current work and exact roles.
- Distinguish first, senior, corresponding, co-PI, site contact, data contributor, and ordinary co-author roles. A collaborative paper proves participation, not ownership of every sample, platform, or work package.
- For every retained A/B/C supervisor in a full run, enumerate the bounded publicly identifiable set of eligible candidate-bound original papers before selecting examples and follow `references/research-method-translation-audit.md`. Record a unique query plan and structured `BASE_5Y` ledger; when the reconstructed five-year candidate-led count is below five, record a complete `EXTENDED_8Y` ledger for every planned query. Retain pagination/cursors, result counts, truncation, retries, exclusions and deduplication. No retained row may silently omit this assessment: use `confirmed`, `provisional`, `ungraded`, or `incomplete` exactly as defined there. `MTG-U` is allowed only after a complete, non-truncated eight-year search finds zero usable candidate-bound eligible papers; machine-only usable evidence produces `pMTG#`, while blocking conflicts produce `incomplete`.
- Code paper method (`RM-E`, `RM-B`, `RM-EB`, `RM-M`, `RM-C`) separately from clinical-translation depth (`TR0`–`TR3` or `CLIN_ONLY`). Also record controlled method-family tags so applied bioinformatics and omics can be counted separately. Treat same-paper wet/computational integration and a split portfolio of separate experimental and separate bioinformatics/omics papers as distinct but both meaningful mixed forms. Keep RWE, routine outcomes, efficacy/safety and ordinary clinical studies as pure-clinical supplementary evidence unless a molecular/omics/functional bridge is demonstrated.
- For each eligible paper, retain the evidence used to make those codes: patient/cohort or trial anchor, cell/organoid/animal/molecular perturbation, omics contribution, applied-bioinformatics contribution, theoretical-method contribution, mechanism, biomarker or outcome endpoint, functional or orthogonal validation, and structured corresponding/senior/author-order evidence. Prioritise explicit corresponding and co-corresponding records; last-author position without correspondence proof remains lower confidence, and penultimate position alone never proves co-corresponding or co-senior status. Do not classify from title keywords, author position, or tool names alone.
- Record review depth and `reviewActor` per paper. Keep `machine_rule`, `model_manual`, and `human_manual` distinct; never describe model inspection as human review. Machine-assisted title/abstract triage remains provisional. Deliberately review every strong-role paper and inspect the full design for every validator-derived score/portfolio trigger and every borderline `RM-EB`, `TR2`, `TR3`, purity, or dominant-type claim. The validator must recompute author roles, all five score components, portfolio codes and trigger flags rather than trusting handwritten values. M4 is a supervisor-level current-programme cross-check, never a paper-level depth. If full text, authorship, search completeness, or a material conflict cannot be resolved, retain `pMTG#` or `incomplete` with a visible limitation rather than upgrading the label.
- Cross-check the publication portfolio against the current official programme description. Show disagreements explicitly; do not let an old publication portfolio silently replace a newer declared direction, and do not let a generic current group description erase a candidate-bound recent publication line.
- Store the resulting portfolio codes and `MTG1`–`MTG4`/provisional/ungraded result as an independent method-translation fit axis. It must not overwrite A/B/C readiness, T topic directness, S supervision evidence, opportunity status, or an outreach hold. Store scientific audit state separately from outreach/vacancy control, so a no-capacity reply never suppresses an otherwise required fresh research audit. Until the base case schema supports this object, use the separately validated supplemental structured audit rather than inserting unvalidated keys into `records.json`.
- For each A-tier candidate, include at least two recent, direct topic-evidence records when available. If unavailable, lower the tier or state the exception explicitly.
- Require T1/T2 to have two candidate-bound current official facts: an independent group-leader/PI role and a direct research line within the declared profile. They may come from one page or from separate official role and research pages; never copy a role from one page into another source record. A publication alone does not prove a current independent line. Future evidence cannot support a current classification before it becomes effective or public.
- Write a 150–250 Chinese-character direction overview and structured profile exceeding 500 Chinese characters for each A-tier candidate. These are different length requirements.

### 5. Verify doctoral paths and opportunities

Use current official programme rules, admissions/funding pages, and vacancy portals. Store each materially different person-, lab-, or programme-level route in `opportunities[]`; keep its status, deadline type, deadline, contact policy, and source IDs separate. A programme call does not prove that one named PI is accepting a student. For person-scoped `open_current`, the vacancy must explicitly name the candidate and its source record must list that candidate in `subjectIds`; apply the same candidate-binding rule to lab-scoped openings until a validated lab-entity registry exists. Treat legacy top-level opportunity fields only as a conservative summary and never let them override the route-level evidence.

Apply vacancy-neutral retention before interpreting the audit: `route_confirmed_no_vacancy`, `closed_expired`, `no_public_evidence`, `unverified`, a zero-result portal search, or inability to confirm private capacity changes only the opportunity/recruitment field. None of these states may remove the person from `records.json`, suppress a scientifically eligible A/B/C record, lower topic/supervision evidence, or appear as the exclusion reason. If a PI or lab explicitly replies that no position or capacity is available, preserve that communication in a separate correspondence/outreach-control layer and, when requested, pause further contact with the date, intake/scope and recheck condition; do not rewrite the public-evidence research roster on that basis alone. If this state must be visible in the research package, put only minimal metadata in `records[].notes` and, for A-tier handoff, `applicationReadiness.cautions[]`, pointing to the external correspondence ledger; never present a private email or screenshot as a public `sources.json` record. If the same communication independently proves retirement, a move, or loss of supervision eligibility, assess that distinct fact under the relevant role/supervision rule while preserving the research evidence in coverage/source audit.

For every retained A/B/C candidate, audit application materials for each viable route using `references/application-materials-checklist.md`. Store the sourced rows in `applicationReadiness.documentRequirements`; include motivation letter, supervisor enquiry/pre-contact, recommendation letters and research proposal even when the result is an explicit missing state. Add personal statement, cover letter, CV, transcripts, degree certificates, language proof, writing samples or other documents when the route warrants them. Distinguish formal application, PI contact, fellowship and employment-style doctoral applications; their material lists are not interchangeable. New initialized cases set `applicationMaterialsAuditRequired: true`; older cases remain unchanged until explicitly updated.

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
- a route-specific material checklist for all A/B/C candidates: whether motivation/personal statements, cover letters, prior PI contact or supervisor agreement, recommendation letters and a proposal are required, optional, conditional, explicitly not required or unverified; record length/format, quantity, submitter, submission method, stage and source IDs;
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
- the dated route-specific documentRequirements checklist, including official document names and whether prior supervisor contact is mandatory, optional, discouraged or unverified; a suggested outreach strategy is not a required admissions document;
- the sourced `researchAnchor`;
- `researchGap` and `proposedAim`, explicitly marked analyst-derived and not approved by the supervisor;
- open questions, resource assumptions that require confirmation, and cautions.

Do not pre-compose a subject line, salutation, opening sentence, personalized fit paragraph, promise of methods/resources, or proposal prose. The later writing workflow must independently collect the applicant's CV/background, target intake, language, title preference, exclusions, and output preferences, then recheck unstable facts before using the handoff.

## Structured data is the source of truth

Write all verified content first to the JSON files defined in `references/output-spec.md`. Link every material claim to source IDs. Generate reports only from those files.

When the task includes a contact search, refresh, comparison, audit, or contact-inclusive roster, write the supplemental contract in `data/contact-audit.json` with stable `candidateId`, per-candidate `channelId`, `owner`, `currentness`, `sourceIds`, ordered official-first search steps, and a `preferredRoute` that selects an existing usable channel. Render `08-CONTACT-AUDIT.md` and validate the optional file before delivery. Do not add a `not_public` marker when any form, mailbox, assistant, phone, or other public route is retained.

Do not manually type evidence totals into Markdown. `render_outputs.py` must compute evidence-record counts and canonicalized unique-URL counts from `data/sources.json`, then reuse one identical statistics line across outputs. Give each source exactly one primary `type`, an `authorityClass`, a `medium`, and the applicable `claimDomains`; reuse one source ID across claims. Add `workId` or stable identifiers when DOI/PMID/PMCID, grant, trial, or posting identifiers exist so alternate landing pages cannot be counted as independent underlying evidence.

The page host, `authorityClass`, and primary `type` must describe the page that was actually opened. A PubMed/PMC/Europe PMC/DOI publication page, ClinicalTrials registry record, SNSF funder record, or QS ranking page must never be relabelled as `official_institution` or as an institutional role/contact profile to satisfy a current-role or contact requirement.

For every full run, create `data/research-method-audit.json` with its verification date inside the file and generate `08-RESEARCH-METHOD-TRANSLATION-AUDIT.md` as defined in `references/research-method-translation-audit.md`. Keep the base schema valid: until `output-spec.md` and the base validator explicitly support `researchMethodAudit`, do not insert ad hoc keys into `records.json`. The separately validated supplement is the source of truth for paper-level method and translation claims.

## Render and validate

After research data are complete, run:

```powershell
python <skill-dir>/scripts/validate_case.py --case-dir <case-directory>
python <skill-dir>/scripts/render_outputs.py --case-dir <case-directory>
python <skill-dir>/scripts/validate_case.py --case-dir <case-directory> --strict
python <skill-dir>/scripts/validate_method_audit.py --case-dir <case-directory>
python <skill-dir>/scripts/render_method_audit.py --case-dir <case-directory>
python <skill-dir>/scripts/validate_method_audit.py --case-dir <case-directory> --strict
```

Fix both preflight validators before rendering, then fix every error from both strict validators before delivery. Base strict validation alone never proves that the method audit is complete. Warnings about inaccessible sources, uncertain roles, missing public contacts, truncated searches or unresolved paper-level claims must remain visible in the report.

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
- `08-CONTACT-AUDIT.md` when `data/contact-audit.json` exists

For every full run, additionally deliver `08-RESEARCH-METHOD-TRANSLATION-AUDIT.md` and `data/research-method-audit.json`. State how many retained A/B/C supervisors are confirmed, provisional, ungraded, or incomplete; report the number of eligible papers, separate applied-bioinformatics and omics counts, paper counts at M0/M2/M3, supervisor portfolios completing M4, and all unresolved identity, authorship, access, search, method, translation, or current-direction conflicts. These supplemental deliverables do not replace the eight base files above.

State the verification date, included-school count, checked-exclusion count, candidate count, A-tier count, evidence-record count, unique-URL count, and unresolved warnings exactly as produced by validation. Explicitly say that the package excludes outreach-email and research-proposal drafting.

## Non-negotiable boundaries

- Do not invent ranks, titles, emails, positions, grants, PMIDs, DOIs, samples, methods, or supervisory authority.
- Do not deliver supervisor information with the faculty/department/unit, current appointment/title, or research direction only in English, German, or another non-Chinese language. Each must be Chinese-first or bilingual with a substantive Chinese rendering; exact official wording remains in the evidence record. A Chinese heading above an untranslated value does not satisfy this rule.
- Do not cite search-result snippets as evidence; open and inspect the underlying page.
- Do not use a paper's method to claim that the person's own laboratory controls the platform.
- Do not label an association predictive without a treatment-interaction design or equivalent evidence.
- Do not present machine-assisted title/abstract coding as a confirmed method, purity, dominance, clinical-translation, or `MTG` result. Do not call a programme pure from a thin portfolio, infer experimental-computational integration from the coexistence of tool names, or treat patient data, a clinical trial, RWE, survival analysis, or routine outcomes as mechanistic translation without the required molecular/omics/functional bridge.
- Do not claim a full run complete when any retained A/B/C candidate is absent from `data/research-method-audit.json`, when its bounded search ledger is missing, or when `validate_method_audit.py --strict` has not passed. Do not use `MTG-U` to hide machine-only evidence or a blocked search.
- Do not equate `not found publicly` with `does not exist`.
- Do not exclude, delete, or downgrade an otherwise eligible research candidate merely because a current vacancy was not verified, no public opening was found, or recruitment remains `unverified`; recruitment is a separate axis from research eligibility and priority.
- Do not claim exhaustive coverage beyond the documented search scope.
- Do not reinstate an institutionally or research-direction-excluded candidate as a lower-tier target or let topic/publication strength override either gate without an explicit user exception.
- Do not write outreach correspondence or a research proposal in this skill.
