# Evidence and conflict policy

## Contents

1. Source hierarchy
2. Claim-to-source rules
3. Person and role attribution
4. Time-aware verification
5. Recruitment and funding language
6. Conflict taxonomy
7. Confidence and missing evidence
8. Prohibited inferences

## 1. Source hierarchy

Use the most direct, current source for each field. Authority is claim-specific.

| Level | Source | Appropriate claims |
|---:|---|---|
| 1 | Current official university, hospital, institute, funder, regulator, trial registry, doctoral programme, or vacancy page | current role, affiliation, contact, project role, rules, open position, deadline |
| 2 | Primary publication record or full article; institutional repository thesis record | research content, methods, authorship, supervision recorded in a dissertation |
| 3 | ORCID or other researcher-controlled identifier linked to the current institution | identity and supporting affiliation/contact evidence |
| 4 | Reputable professional society, conference faculty page, medical media, or institutional partner | triangulation, historical role, interview statements |
| 5 | Aggregator, repost, Chinese secondary article, LinkedIn, ResearchGate, Zhihu, Xiaohongshu, forum | discovery leads, applicant experience, possible conflicts only |
| 6 | Search snippet or unopenable result | lead only; never final evidence |

An older official page can be stale. A newer official appointment announcement may be stronger for a future role, while the current role remains valid until its effective date.

## 2. Claim-to-source rules

- Link every material field to one or more source IDs.
- Use direct page links, not search-result pages.
- Keep quotations minimal; paraphrase precisely.
- Record the page date when available and the access date always.
- When a page supports only part of a sentence, split the claim.
- Do not use one source to support title, email, research ownership, and recruitment unless it actually states all four.
- Treat a stable official page with no visible date as current only after checking that the surrounding directory is active; note the date limitation.
- Mark inaccessible or deleted pages as such and retain an alternative source when possible.

Each source record must have one mutually exclusive primary `type`:

- `official_ranking`
- `official_research_profile`
- `official_role_contact`
- `official_school_structure`
- `publication`
- `grant_project`
- `clinical_trial`
- `doctoral_rule_supervision`
- `official_admissions_funding`
- `official_vacancy_portal`
- `vacancy`
- `chinese_secondary`
- `social_user_generated`
- `other_secondary`

Use `official_ranking` for the ranking publisher's own table or institutional entry. Use `official_research_profile` for an official laboratory, programme, project, or research-theme page that establishes scientific direction but is not primarily a role/contact page. Use `doctoral_rule_supervision` for an official rule, supervisor list, trainee roster, or thesis record; its `claimDomains` may contain `doctoral_rule`, `doctoral_supervision`, or both only as the page warrants. Use `official_admissions_funding` for programme admission, application, employment/stipend, tuition, or external-funding rules; use `official_vacancy_portal` for an official portal/search page and `vacancy` for one specific posting or call.

Use `discovery_lead` with the sole `discovery` claim domain only to preserve a transparent legacy or exploratory association that is not evidence. It must use `topicRelevance: not_applicable`; any person row must be `mentioned_without_role`, `topicRelevance: not_applicable`, and state `Discovery lead only; legacy association not used as role/topic evidence`. It may be cited only from `case.supportingSourceIds` or `case.discoveryPasses[].sourceIds`, never from school, coverage, candidate, role, contact, research, doctoral, recruitment, or claim-level evidence fields. Its presence in a discovery pass proves only how a name entered the candidate pool.

Also record:

- `authorityClass`: `official_ranking_publisher`, `official_institution`, `official_funder_registry`, `official_trial_registry`, `official_government_regulator`, `primary_publication`, `researcher_controlled`, `professional_secondary`, `social_user_generated`, or `other_secondary`;
- `medium`: `webpage`, `pdf`, `article`, `database_record`, `vacancy_posting`, `social_post`, `dataset`, or `other`;
- `claimDomains`: one or more of `ranking`, `school_structure`, `research`, `current_role`, `contact`, `doctoral_rule`, `doctoral_supervision`, `admissions_funding`, `recruitment`, or `conflict`, describing all claim families the page actually supports;
- `subjectIds`: stable candidate or school IDs explicitly named by the source, when applicable;
- `personRoles`: one object per named person with `subjectId`, controlled `roleType`, faithful `exactLabel`, and person-specific `topicRelevance`; use `mentioned_without_role` when a person is named but the desired role is unstated, and never attach a person who is not named;
- `workId` and `identifiers` when a DOI, PMID, PMCID, grant ID, trial ID, or posting ID exists. A publication, grant, or trial used as A-tier direct evidence must have a `workId` even when only one landing page is stored.

The single `type` states the page's primary evidence function; `claimDomains` permits the same page to support, for example, both current role and contact without duplicating it. One source page may support several claims but is stored once and reused by source ID. Different landing pages for the same paper, grant, trial, or posting do not become independent direct evidence: use the same `workId` across them and retain all known stable identifiers. An identifier alone does not reconcile a DOI landing page with a PubMed landing page when the two records expose disjoint IDs.

Publisher-host consistency is mandatory. The URL host, `authorityClass`, and primary `type` must describe the page actually inspected, not the downstream institution mentioned in its metadata. In particular, PubMed/PMC/Europe PMC/DOI pages are publication evidence, ClinicalTrials.gov is a trial-registry source, SNSF pages are funder sources, and QS/TopUniversities pages are ranking-publisher sources. None may be relabelled `official_institution` or `official_role_contact` to make a paper affiliation, correspondence address, registry investigator name, grant participant, or ranking entry look like a current institutional role/contact page.

An official thesis record classified as `doctoral_rule_supervision` may support a historical or collaborative topic link when it also carries `research` and a faithful person role. It does not count toward the A-tier recent direct-publication/grant/trial requirement and does not prove a current independent laboratory line by itself.

## 3. Person and role attribution

### Academic and organizational roles

Keep these fields separate:

- academic appointment;
- clinical appointment;
- administrative office;
- laboratory or programme leadership;
- grant role;
- trial role;
- doctoral supervision status.

Represent each verified university, hospital, centre, or institute relationship separately in `affiliations[]`, with its relationship/role and source IDs. `schoolId` is the primary grouping school; `additionalSchoolIds` lists other included universities supported by those affiliations. Every affiliation whose `schoolId` differs from the record's primary `schoolId` needs at least one current official-institution source in that affiliation's `sourceIds`, and that one source must bind both the candidate ID and the additional school ID in `subjectIds`. Do not combine a candidate-only page with a separate school-only page to manufacture a cross-school affiliation, and do not describe a collaboration as an affiliation.

Give each contact its own type, status, value, and source IDs. A general mailbox, secretariat address, phone number, or contact form is not a personal email.

For a `personal_email` or `clinical_email`, the mailbox must visibly identify the candidate rather than another named person and must not be an obvious office, department, centre, group, or secretariat alias. Classify those alternatives as `unit_email`, `group_email`, `department_mailbox`, `secretariat_email`, or `assistant_contact` as appropriate. Candidate binding on a profile page does not convert an assistant's or unit's address into the candidate's personal address.

For a person-level role, affiliation, personal or clinical contact, research line, direct evidence item, or research anchor, the supporting source must name that person and include the candidate's stable ID in `subjectIds`. Generic school, programme, or vacancy-portal pages may support programme rules or search audits, but cannot be substituted for person attribution.

A doctoral-programme page can support only what it actually states. A generic programme listing does not establish a person's academic/current title, published personal contact, or direct research line. Those extra domains are allowed only when the page itself gives an explicit person-specific title, contact statement, research/project description, or named thesis record. A page that names one candidate in its claim/title must not be rebound to a different candidate unless a separate source-faithful `personRoles` entry states that second person's actual role on the same page.

Do not translate `senior lecturer`, `associate professor`, `docent`, `Privatdozent`, `MER`, `maître d'enseignement et de recherche`, or local clinical grades into a higher rank. Preserve the original title and provide a cautious Chinese gloss.

### Publication roles

Record only what the article or bibliographic record supports:

- first author;
- co-first/equal contribution;
- corresponding author;
- senior/last author;
- co-senior/equal supervision;
- ordinary co-author;
- consortium author;
- role not stated.

Do not infer intellectual ownership from author order alone when equal-contribution notes or consortium structures matter. CRediT can refine contribution but does not automatically establish current laboratory ownership.

### Project and trial roles

Distinguish PI, co-PI, principal applicant, co-applicant, applicant, grant recipient, work-package lead, site PI, national contact, responsible party/study director, sub-investigator, project partner, collaborator, advisory member, team member, and institutional participant. Academic rank must never be used to infer a project role, and another person's PI label must never leak across a shared page. Use neutral wording such as `named participant; specific role not stated` when role detail is unavailable. The `exactLabel` must reproduce or tightly paraphrase what the source says; migration placeholders such as `role described on page`, `named profile/group member`, `contact record`, or `anchor attribution is described in the linked source` are not evidence.

Use `independent_faculty` only for an explicit full/associate professor title (or an explicitly tenure-track assistant-professor title) and `unit_head` only for an explicit department, division, service, centre, institute, or unit leadership title. `PD`/Privatdozent or attending/consultant status alone is not an independence role. These types, together with explicit group-leader/PI/co-PI roles, may support the independent-role half of T1/T2 and S1/S2; doctoral eligibility remains a separate fact.

Authorship is person-specific. `first_author`, `senior_or_corresponding_author`, and `coauthor` must match the clause about that person, not another name elsewhere in a shared abstract or contribution statement. A label saying the candidate is first author or an ordinary/second/middle coauthor while another named person is last/corresponding cannot be encoded as the candidate's senior/corresponding role. Explicit co-senior or equal-contribution language is allowed, including a penultimate author explicitly marked as contributing equally with the last author.

## 4. Time-aware verification

For all unstable fields, store:

- `verifiedAt`;
- source publication/update date if present;
- effective date for announced moves;
- current, future, historical, or unclear status.

`record.verifiedAt` is the actual person-level current-role verification date. It must be no later than `case.asOf`, need not equal it, and must have at least one current official role source accessed on that date; other role sources may be older but none may be accessed later. When it is more than 30 days older than `case.asOf`, flag “核验已陈旧，使用前需复核”; a record older than 90 days fails strict delivery until reverified. This is a role-check date, not a source publication date or a catch-all date for literature and recruitment.

Use these rules:

1. A future appointment does not replace the current appointment before its effective date.
2. After the effective date, re-open both old and new official pages before contacting the person.
3. A historical title may be accurate for its time but cannot be reported as current.
4. A paper affiliation proves affiliation at publication, not current employment.
5. An ORCID entry may lag; use it as supporting evidence, not automatic override of current institution pages.
6. An expired vacancy proves historical recruitment only.
7. A future-dated or future-status source cannot establish a present role, present supervision, direct current topic line, or current opening before it becomes effective/public.

## 5. Recruitment and funding language

Allowed opportunity statuses:

| Code | Exact meaning |
|---|---|
| `open_current` | An official, currently open doctoral vacancy or call explicitly accepts applications. |
| `planned_official` | An official source explicitly announces a future doctoral opening or call. |
| `route_confirmed_no_vacancy` | A doctoral route or supervisor eligibility is verified, but no open position is shown. |
| `direct_enquiry_recommended` | A current personal role, published contact channel, and official doctoral/recruitment route are verified, but availability and funding still require inquiry. Never use for D-tier or role-unverified records. |
| `historical_only` | Past supervision or a closed position is verified; current status is unknown. |
| `closed_expired` | A specific position or call is no longer open. |
| `no_public_evidence` | Current official materials show no public recruitment evidence. This is not proof of no internal plans. |
| `unverified` | Official information is insufficient or inaccessible. |

Only `open_current` permits wording equivalent to `currently recruiting`. Store materially different routes separately in `opportunities[]` with scope (`person`, `lab`, or `programme`), route name, status, deadline type, deadline, contact policy, and source IDs. A programme opening is not a person-level opening. A person-scoped `open_current` vacancy source must explicitly identify that candidate and include the candidate ID in `source.subjectIds`; until a validated lab-entity registry is added to the schema, a lab-scoped opening must also be candidate-bound. For a fixed deadline, include a future ISO date; `rolling` and `until_filled` are allowed only when the official source uses that rule.

For `route_confirmed_no_vacancy`, `no_public_evidence`, or `direct_enquiry_recommended`, a dated `recruitmentAudit` must include required `checkedScopes`, non-empty official person/lab/programme `portals`, actual `queries`, summary, and source IDs. No cited source may have been accessed after `checkedAt`, and at least one current official vacancy portal bound to the candidate or school must have been accessed on `checkedAt`. This supports only the statement that no public position was found in that search; it does not establish internal plans.

`direct_enquiry_recommended` is not a mechanical replacement for missing recruitment evidence. In strict output it additionally requires a high/medium-confidence current role backed by a candidate-bound current official role source, a published contact channel, a current official doctoral or recruitment route, and a non-D priority tier. Otherwise use `no_public_evidence` or `unverified`.

Do not infer salary, stipend adequacy, project duration, consumables, sequencing budget, visa support, CSC acceptance, or full doctoral funding from a grant title or PI status. Separate:

- project funding exists;
- a doctoral salary or stipend line exists;
- the position is approved;
- applications are open;
- the person has formal supervision authority;
- admission is decided.

Record the supervision conclusion in `supervisionBasis`, not just an S-code. S1 needs a candidate-bound official source that explicitly confirms person-level eligibility, documents thesis supervision, explicitly names a current supervision/co-supervision relationship, or names the person in a doctoral posting; keep `eligibilityStatus: not_confirmed` unless eligibility itself is explicit. Use `named_current_supervision` for the current explicit relationship, not for a roster that merely lists students. S2 needs candidate-bound current official PI/role evidence plus a candidate-bound official current-trainee roster or programme PI/host listing; use `personSupervisionStatus: activity_supported` and `eligibilityStatus: not_confirmed`. A generic programme page supports only the doctoral route. If person-level doctoral activity is not public, use S3 rather than promoting an independent PI to S2 by assumption. S4 may preserve official co-supervision evidence for an emeritus or otherwise unsuitable principal candidate through `co_supervision_only`, but it still does not establish prospective main-supervisor authority.

## 6. Conflict taxonomy

Use one category per conflict:

| Category | Definition | Resolution approach |
|---|---|---|
| `substantive_current_conflict` | Sources disagree about a current factual field such as employer, title, or email. | Prefer the more direct and current official source; preserve both and explain. |
| `announced_future_change` | A verified change has a future effective date. | Keep present role and add a dated warning. |
| `stale_or_timepoint_difference` | An older source was accurate then but is no longer current. | Mark historical; do not call it misinformation. |
| `translation_naming_difference` | Different translations, abbreviations, spelling, or institutional labels describe the same entity. | Preserve official wording and explain the variant. |
| `low_confidence_unverifiable` | A claim cannot be traced, may reflect extraction error, or relies on a weak source. | Do not modify authoritative fields; retain as a caution only if relevant. |
| `scope_or_role_difference` | A source proves participation, while another is being read as ownership, supervision, or recruitment. | Narrow the claim to the verified role. |

A conflict entry must include the field, both claims, decision, effective date if relevant, and source IDs for both sides. Absence of a Chinese or social result is not a conflict.

## 7. Confidence and missing evidence

Use `confidenceByClaim` rather than one vague score. Record separate confidence for current role, contact, research, supervision and recruitment:

- `high`: current direct official evidence and identity match.
- `medium`: primary evidence plus indirect current institutional support, or official evidence with date limitations.
- `low`: secondary or incomplete evidence; do not use for decisive fields.
- `unverified`: no acceptable source.

Use `not_applicable` only when that claim family truly does not apply. The legacy scalar `confidence` is optional and deprecated. Material group, role, research, PhD-type, doctoral-route, direction, scientific-question, model, method, validation-maturity and role-boundary claims require field-level references in `claimSourceIds`; a large undifferentiated evidence pool is not adequate traceability. Current-role fields also require semantic compatibility: a programme-director source may support `adminClinicalRole` but not `academicRole`, while trial, grant, publication, collaboration, team-member and doctoral-supervision role labels cannot be reused as proof of an academic title, lab/group appointment, or administrative/clinical leadership. Each such citation must be current, official-institution, candidate-bound, and carry a compatible `personRoles[].roleType` plus the actual retained role wording. `specific title not retained or inferred` and equivalent identity-only labels cannot support a concrete role field or concrete affiliation role; use an explicit unverified display value instead.

Write missing values as `not_public`, `not_found_publicly`, `not_applicable`, or `unverified`. Do not collapse them into `none`.

For contacts, `not_public` is a source-free missing-value marker: leave `value` blank, use `status: not_public`, and provide no source IDs. Every published contact needs a current candidate- or school-bound official source; never cite a page that did not publish the displayed address or number.

Examples:

- `No public personal email found; official pathology secretariat available.`
- `No current doctoral vacancy found on the official portal as of 2026-09-06; internal plans remain unknown.`
- `Formal main-supervisor eligibility was not stated on the pages reviewed.`

## 8. Prohibited inferences

Do not infer:

- an email address from an institutional naming pattern;
- current employment from publication affiliation alone;
- a professor title from `Dr`, `PD`, group lead, or senior physician;
- doctoral authority from PI status;
- current recruitment from an active grant, trial, or supervisor list;
- an individual's platform ownership from collaborative authorship;
- direct lung-cancer focus from a generic cancer project;
- predictive biomarkers from prognosis-only association;
- patient benefit from preclinical response;
- available samples, ethics, data access, equipment time, or funding for a proposed doctoral project;
- exhaustive coverage of people who are not publicly indexed;
- `no results` when a platform was blocked or required login.

When evidence is insufficient, narrow the sentence or mark it unverified. Traceability takes priority over completeness.
