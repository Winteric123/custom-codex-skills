# Output specification

## Contents

1. Case directory
2. Classification axes
3. Structured JSON schema
4. Markdown outputs
5. Length and evidence requirements
6. Validation and delivery

## 1. Case directory

Store each run under the user's workspace:

```text
outputs/<location>-lung-cancer-phd-supervisors-<YYYY-MM-DD>/
├── 00-INDEX.md
├── 01-SCHOOL-SCOPE.md
├── 02-SUPERVISOR-TABLE.md
├── 03-COVERAGE-MATRIX.md
├── 04-EVIDENCE-CONFLICTS.md
├── 05-A-TIER-DEEP-PROFILES.md
├── 06-APPLICATION-READINESS.md
├── 07-SOURCE-LEDGER.md
└── data/
    ├── case.json
    ├── schools.json
    ├── coverage.json
    ├── records.json
    └── sources.json
```

Keep the JSON files as the only hand-edited source of truth. Regenerate Markdown after any correction.

Schema `1.2` is intentionally stricter than earlier cases. Preserve pre-`1.2` data and reports as a historical snapshot, migrate them into a new dated case directory, add the required scope/affiliation/opportunity/audit/source metadata, and validate the migrated case. Never overwrite an older report in place merely to make it appear current.

## 2. Classification axes

Do not use one label for research relevance, supervision evidence, and recruitment.

### Topic directness

| Code | Meaning |
|---|---|
| `T1` | Current independent or sustained direct lung-cancer line. |
| `T2` | Current thoracic-oncology line with lung cancer and another thoracic disease in parallel. |
| `T3` | Pan-cancer or methods platform with an explicit current lung-cancer project or application. |
| `T4` | Lung cancer is collaborative, historical, exploratory, or not clearly independent. |

In strict delivery, `T1` and `T2` require two candidate-bound current official facts: a direct lung-cancer research line and an independent group-leader or PI role. One page may prove both, but a paired official research page and official role page is also valid; each source record must retain only the fact it actually states. A publication alone does not prove a current independent line. `T3` requires a current candidate-bound explicit lung-cancer project or application. Historical, collaborative, future, or role-unclear evidence remains `T4` unless stronger current evidence exists.

### Supervision evidence

| Code | Meaning |
|---|---|
| `S1` | Official source names the person as main/co-supervisor or confirms person-level eligibility. |
| `S2` | Independent PI/group lead with doctoral trainees or programme participation, but current person-project mapping is incomplete. |
| `S3` | Project leader, clinician, platform lead, or collaborator; formal doctoral authority needs confirmation. |
| `S4` | Historical, moved, retired, conflicting, insufficient current evidence, or documented co-supervision that does not establish independent prospective authority. |

### Priority tier

| Tier | Use |
|---|---|
| `A` | Strong current topic match with credible supervision/doctoral route; suitable for deep profiling. |
| `B` | Strong topic or method fit but supervision, current independence, or doctoral path is incomplete. |
| `C` | Useful collaborator, shared platform, adjacent field, or conditional co-supervisor. |
| `D` | Historical, moved, out of scope, materially conflicted, or too weak to approach now. |

Tier does not encode vacancy status. A-tier does not mean currently recruiting.

A/B/C records need a current source-bound affiliation. A D-tier discovery lead may keep an empty `affiliations` array only when `currentRoleSourceIds` is also empty and `academicRole` explicitly begins with `unverified`/`未确认`; this preserves candidate-discovery provenance without presenting the person as a verified current supervisor.

The coverage matrix maps only candidates with retained substantive current role or research evidence. A D-tier record kept solely through a quarantined `discovery_lead` must remain absent from `coverage[].candidateIds`; its provenance belongs in `case.discoveryPasses`, and the affected branch remains `blocked_unverified` unless other supported candidates were found.

### Opportunity status

Use only the eight codes in `evidence-policy.md`: `open_current`, `planned_official`, `route_confirmed_no_vacancy`, `direct_enquiry_recommended`, `historical_only`, `closed_expired`, `no_public_evidence`, `unverified`.

### Scientific categories for the default topic

Use the closest primary category and optional secondary categories:

- `C1` clinical systemic therapy and outcome stratification
- `C2` thoracic surgery and local treatment
- `C3` screening and interventional diagnosis
- `C4` precision radiotherapy and treatment physics
- `C5` molecular diagnostics and translational biomarkers
- `C6` tumour immunity and microenvironment
- `C7` tumour-cell-intrinsic mechanisms and therapeutic vulnerabilities
- `C8` functional precision models and drug discovery

Add a clearly defined category when the evidence does not fit; do not force a misleading label.

## 3. Structured JSON schema

Use UTF-8 JSON with two-space indentation. IDs must be stable lowercase ASCII slugs derived from identity, never from input order; use a deterministic hash suffix only for true slug collisions.

### `case.json`

```json
{
  "schemaVersion": "1.2",
  "location": "Switzerland",
  "topic": "thoracic oncology, especially lung cancer",
  "asOf": "2026-09-07",
  "intake": "",
  "scopeMode": "qs_top_300",
  "requestedSchools": [],
  "requestedSchoolResolutions": [],
  "qsThreshold": 300,
  "locationResolution": {
    "requestedLocation": "Switzerland",
    "resolvedJurisdictions": ["Switzerland"],
    "relationshipType": "country_exact",
    "sourceIds": ["src-official-jurisdiction"]
  },
  "scopeAudit": {
    "rankingSystem": "QS World University Rankings",
    "rankingEdition": "QS World University Rankings 2027",
    "rankingPublicationDate": "2026-06-18",
    "jurisdictions": ["Switzerland"],
    "rankingQuery": "Official 2027 ranking filtered to Switzerland and checked through the complete country result.",
    "eligibleInstitutionCount": 7,
    "sourceIds": ["src-qs-ranking"],
    "includedSchoolIds": [
      "eth-zurich",
      "epfl",
      "university-of-zurich",
      "university-of-basel",
      "university-of-geneva",
      "university-of-bern",
      "university-of-lausanne"
    ],
    "excludedInstitutions": [
      {
        "id": "checked-institution",
        "officialName": "Checked Institution",
        "countryRegion": "Switzerland",
        "inclusionDecision": "excluded",
        "qs": {
          "edition": "QS World University Rankings 2027",
          "publicationDate": "2026-06-18",
          "rank": "301",
          "status": "ranked",
          "sourceIds": ["src-qs-checked-institution"]
        },
        "reason": "Outside the top-300 threshold.",
        "sourceIds": ["src-qs-ranking"]
      }
    ]
  },
  "status": "draft",
  "discoveryPasses": [],
  "limitations": []
}
```

Use `scopeMode` = `named_schools` or `qs_top_300`. Preserve the literal user input in `requestedSchools` for named-school cases and map every literal one-to-one to a verified `schoolId` in `requestedSchoolResolutions`; this allows a Chinese name or abbreviation to resolve to a different official name without losing provenance. Strict delivery requires `decision: resolved` and official identity-resolution sources. Use empty arrays for both fields in location-only screening. For a location-only run, `locationResolution` preserves the literal request, resolves it to the exact jurisdictions used by the ranking filter, records `country_exact`, `subnational_within_country`, or `multi_jurisdiction_region`, and cites an official jurisdiction source. `schools.json` contains only included schools; a location-only run also records the official country/region filter in `rankingQuery`, the covered `jurisdictions`, the independently counted number of eligible institutions, and checked exclusions in `scopeAudit.excludedInstitutions`. `includedSchoolIds` must exactly match the included school IDs and `eligibleInstitutionCount`. A positive ranked school must have a parseable rank or rank band within the threshold; a ranked excluded institution must be outside the threshold. Each record retains the same edition/date and an official ranking source. Before final rendering, set `status` to `complete`, meaning the package is generated rather than that all branches are exhausted, and record at least two search-expansion passes plus a separate final saturation pass, for at least three entries total; each pass records `passType`, `performedAt`, non-empty `queriesOrUnits`, `sourceIds`, `newCandidateIds`, and matching `newCandidateCount`. The first pass is `official_expansion`, at least one intermediate pass is `literature_expansion`, and the final `saturation` pass adds zero qualified candidates. A literature pass must cite at least one publication, grant, or trial record rather than only profile pages. Across passes, each final candidate ID must appear exactly once; ghost IDs and repeated IDs are invalid. If any coverage row is `blocked_unverified`, the final pass must document a retry/recheck and `limitations[]` must state that coverage remains bounded/non-exhaustive.

### `schools.json`

Each array item:

```json
{
  "id": "university-of-zurich",
  "officialName": "University of Zurich",
  "displayNameZh": "苏黎世大学",
  "countryRegion": "Switzerland",
  "namedByUser": false,
  "origin": "ranking_screen",
  "inclusionDecision": "included",
  "inclusionReason": "Current overall QS rank is within the top-300 threshold.",
  "qs": {
    "edition": "QS World University Rankings 2027",
    "publicationDate": "2026-06-18",
    "rank": "98",
    "status": "ranked",
    "sourceIds": ["src-qs-uzh"]
  },
  "medicalSystem": {
    "status": "medical_faculty_present",
    "summary": "Faculty of Medicine; affiliated university hospital mapped separately.",
    "sourceIds": ["src-uzh-medicine"]
  },
  "affiliatedInstitutions": [
    {
      "id": "university-hospital-zurich",
      "name": "University Hospital Zurich",
      "relationshipType": "formal_clinical_partner",
      "relationship": "Official university-medicine clinical and research relationship.",
      "sourceIds": ["src-uzh-usz-relationship"]
    }
  ],
  "sourceIds": []
}
```

Allowed QS status: `ranked`, `rank_band`, `specialist_not_in_overall`, `not_ranked`, `not_verified`.

Allowed medical-system status: `medical_faculty_present`, `medical_program_without_medical_faculty`, `health_sciences_without_medical_degree`, `specialist_medical_institution`, `no_medical_faculty`, `unclear`. Use `medical_program_without_medical_faculty` when an institution teaches a named medical programme but has no independent medical faculty; explain degree level and partner institutions in `summary`.

Allowed `origin` values are `user_named` and `ranking_screen`. Included records use `inclusionDecision: included`; the reason must explain either explicit user inclusion or the rank-threshold rule. In a location-only QS run, every included school must have a machine-readable current rank/band within the threshold regardless of `namedByUser`.

Every `affiliatedInstitutions[]` item is an object with a stable `id`, official `name`, explanatory `relationship`, source IDs, and one of these `relationshipType` values: `owned_university_hospital`, `affiliated_teaching_hospital`, `formal_clinical_partner`, `cross_institutional_research_network`, or `multi_institutional_cancer_centre`. The evidence must be an official, school-bound `school_structure` source. A one-off collaborator does not belong in this list.

### `coverage.json`

Each school must have one row for every coverage area listed in `search-playbook.md`:

```json
{
  "schoolId": "university-of-zurich",
  "area": "medicine-clinical",
  "units": ["Faculty of Medicine"],
  "status": "candidates_found",
  "candidateIds": ["university-of-zurich-person-name"],
  "sourceIds": ["src-unit-page"],
  "notes": ""
}
```

Allowed status: `pending`, `searched`, `candidates_found`, `not_present`, `blocked_unverified`. `pending` is initializer-only and is rejected by strict validation. `units[]` must name units actually inspected and documented by the row's sources; never manufacture unit names from a candidate's focus keywords. A `candidates_found` row must not contain “no qualifying candidate” language, must retain school-bound official branch evidence, and must also list at least one current official candidate-bound `research`/`current_role` source for every candidate ID in that row.

### `records.json`

Each candidate record:

```json
{
  "id": "university-of-zurich-person-name",
  "name": "Person Name",
  "schoolId": "university-of-zurich",
  "additionalSchoolIds": [],
  "affiliations": [
    {
      "schoolId": "university-of-zurich",
      "institution": "University Hospital Zurich",
      "faculty": "Faculty of Medicine",
      "department": "Department name",
      "relationship": "university-affiliated hospital appointment",
      "role": "Current verified role",
      "sourceIds": ["src-person-profile"]
    }
  ],
  "faculty": "",
  "department": "",
  "affiliatedInstitution": "",
  "group": "",
  "academicRole": "",
  "adminClinicalRole": "",
  "contacts": [
    {
      "type": "personal_email",
      "value": "person@example.edu",
      "status": "published_current",
      "sourceIds": ["src-person-profile"]
    }
  ],
  "primaryCategory": "C1",
  "secondaryCategories": [],
  "topicDirectness": "T1",
  "supervisionEvidence": "S1",
  "supervisionBasis": {
    "basisType": "person_eligibility_explicit",
    "status": "person_level_supported",
    "summary": "The official doctoral page explicitly identifies this person as eligible to supervise.",
    "independenceSourceIds": ["src-person-profile"],
    "traineeOrProgrammeSourceIds": ["src-person-supervision"],
    "personSupervisionStatus": "confirmed",
    "eligibilityStatus": "confirmed"
  },
  "priorityTier": "A",
  "focus": "",
  "directionOverviewZh": "",
  "structuredProfileZh": "",
  "scientificQuestions": [],
  "researchLines": [
    {
      "title": "",
      "summary": "",
      "sourceIds": []
    }
  ],
  "materialsModels": [],
  "methods": [],
  "validationMaturity": "",
  "roleBoundary": "",
  "doctoralWorkPackages": [
    {
      "title": "Bounded validation package",
      "scope": "Test one stated mechanism in one verified model family with predefined readouts.",
      "analystDerived": true,
      "assumptions": "Requires supervisor approval, model access, feasibility review and secured funding.",
      "sourceIds": ["src-person-research"]
    }
  ],
  "directEvidenceException": "",
  "phdTypes": [],
  "doctoralRoute": "",
  "opportunityStatus": "no_public_evidence",
  "opportunityDetail": "",
  "opportunityDeadline": "",
  "opportunities": [
    {
      "id": "person-name-programme-route",
      "scope": "programme",
      "routeName": "Official doctoral programme",
      "status": "route_confirmed_no_vacancy",
      "deadlineType": "not_stated",
      "deadline": "",
      "contactPolicy": "Use the programme's published contact route.",
      "sourceIds": ["src-doctoral-route"]
    }
  ],
  "recruitmentAudit": {
    "checkedAt": "2026-09-07",
    "checkedScopes": ["person", "lab", "programme"],
    "portals": [
      {
        "name": "Official doctoral programme page",
        "result": "Route confirmed; no person-specific vacancy stated.",
        "sourceIds": ["src-doctoral-route"]
      }
    ],
    "queries": ["official profile", "lab opportunities", "official vacancy portal"],
    "summary": "No current person-specific doctoral vacancy was found publicly; internal plans remain unknown.",
    "sourceIds": ["src-person-profile", "src-vacancy-portal"]
  },
  "verifiedAt": "2026-09-07",
  "currentRoleSourceIds": [],
  "researchSourceIds": [],
  "doctoralSourceIds": [],
  "recruitmentSourceIds": [],
  "directEvidenceIds": [],
  "chineseCheck": {
    "status": "not_found_publicly",
    "checkedAt": "2026-09-07",
    "queries": [
      "Person Name 中文名 肺癌",
      "Person Name university lung cancer 中文",
      "Person Name 导师 博士"
    ],
    "summary": "No attributable person-specific Chinese source was found in the recorded public search.",
    "accessNote": "Public search results were accessible.",
    "sourceIds": []
  },
  "xiaohongshuCheck": {
    "status": "public_access_blocked",
    "checkedAt": "2026-09-07",
    "queries": [
      "site:xiaohongshu.com Person Name",
      "site:xiaohongshu.com Person Name university"
    ],
    "summary": "Public indexing did not provide an inspectable person-specific post.",
    "accessNote": "Login/access controls blocked direct inspection.",
    "sourceIds": []
  },
  "conflicts": [],
  "applicationReadiness": {
    "contactProtocol": "",
    "applicationWindow": "",
    "eligibilityRequirements": "",
    "requiredDocuments": "",
    "proposalRequirement": "",
    "fundingModel": "",
    "supervisionSetup": "",
    "researchAnchor": "",
    "anchorSourceIds": [],
    "researchGap": "",
    "gapSourceIds": [],
    "researchGapAnalystDerived": true,
    "proposedAim": "",
    "proposedAimAnalystDerived": true,
    "generalApplicantFit": "",
    "generalApplicantFitAnalystDerived": true,
    "applicationSourceIds": [],
    "proposalSourceIds": [],
    "fundingSourceIds": [],
    "applicationClaimSourceIds": {
      "contactProtocol": [],
      "applicationWindow": [],
      "eligibilityRequirements": [],
      "requiredDocuments": [],
      "proposalRequirement": [],
      "fundingModel": [],
      "supervisionSetup": [],
      "generalApplicantFit": []
    },
    "doctoralQuestions": [],
    "resourceQuestions": [],
    "fundingQuestions": [],
    "cautions": []
  },
  "confidenceByClaim": {
    "currentRole": "high",
    "contact": "high",
    "research": "high",
    "supervision": "high",
    "recruitment": "medium"
  },
  "claimSourceIds": {
    "group": ["src-person-profile"],
    "academicRole": ["src-person-profile"],
    "adminClinicalRole": ["src-person-profile"],
    "focus": ["src-person-research"],
    "phdTypes": ["src-person-supervision"],
    "doctoralRoute": ["src-doctoral-route"],
    "directionOverviewZh": ["src-person-research"],
    "structuredProfileZh": ["src-person-research"],
    "scientificQuestions": ["src-person-research"],
    "materialsModels": ["src-person-research"],
    "methods": ["src-person-research"],
    "validationMaturity": ["src-person-research"],
    "roleBoundary": ["src-person-research"]
  },
  "confidence": "Optional deprecated compatibility summary; do not use instead of confidenceByClaim.",
  "notes": ""
}
```

Contact types: `personal_email`, `clinical_email`, `group_email`, `unit_email`, `department_mailbox`, `secretariat_email`, `assistant_contact`, `phone`, `contact_form`, `not_public`. A `not_public` contact is a missing-value marker: set `value` to an empty string, `status` to `not_public`, and `sourceIds` to an empty array. Never attach an inferred address or a source that did not publish a value. For `personal_email` and `clinical_email` with `published_current`, at least one single cited record must simultaneously be current, `official_institution`, contact-domain, and candidate-bound; do not combine unrelated sources to satisfy those properties. The mailbox must visibly identify the candidate and must not be an obvious unit/office/secretariat alias; use `assistant_contact` for another named person's published address and `unit_email` or the more specific group/department/secretariat type for generic mailboxes. A researcher-controlled ORCID email is a discovery lead, not official current contact evidence: independently verify it on an institutional page or omit it from the deliverable and use the blank `not_public` marker.

`schoolId` is the primary grouping university, not the whole affiliation claim. `additionalSchoolIds` lists other included universities with a verified current relationship, and the school-ID set represented by `affiliations[]` must match the primary plus additional IDs exactly. Each affiliation records `schoolId`, `institution`, `faculty`, `department`, precise `relationship`, `role`, and source IDs; use an explicit `not_applicable` marker rather than leaving a required unit field blank. For an affiliation assigned to an additional school, at least one cited current `official_institution` source with the `current_role` claim domain must include both the candidate ID and that additional school ID in `subjectIds`. Two separately bound sources cannot be combined to meet this requirement. Keep the legacy scalar `faculty`, `department`, and `affiliatedInstitution` only as a concise compatibility summary; do not use it to erase cross-school or hospital distinctions.

`supervisionBasis` is mandatory in strict cases. Keep person-level supervision/activity and formal prospective eligibility separate. `S1` uses `person_eligibility_explicit`, `documented_thesis_supervision`, `named_current_supervision`, or `named_supervisor_in_doctoral_posting`, with `personSupervisionStatus: confirmed`; only the first basis may use `eligibilityStatus: confirmed`, while the others keep eligibility `not_confirmed`. `person_eligibility_explicit` requires one same current official candidate-bound doctoral-rule record whose person role is `eligible_supervisor`; a generic programme rule and a separate person page cannot be combined into eligibility. `named_current_supervision` requires a current official person-bound page that explicitly names the person as supervisor or co-supervisor. `S2` uses `current_doctoral_trainees` or `programme_pi_or_host`, sets `personSupervisionStatus: activity_supported`, and keeps eligibility `not_confirmed`. S1/S2 both require candidate-bound current official independent-role evidence (`group_leader`, PI/co-PI, `independent_faculty`, or `unit_head`) plus candidate-bound official `doctoral_supervision` or `doctoral_rule` evidence. `independent_faculty` requires an explicit full/associate professor or tenure-track assistant-professor title; `unit_head` requires explicit department/division/service/centre/institute leadership. PD/Privatdozent or attending alone is not independence. A generic programme page proves only a route and cannot by itself support S2. `S3` is always `basisType: unverified`, `status: route_only_unverified`, and `personSupervisionStatus: unverified`. `S4` may use that same unverified form, or may preserve documented co-supervision as `basisType: co_supervision_only`, `status: limited_person_level`, and `personSupervisionStatus: co_supervision_supported` when an official candidate-bound source identifies the person as co-supervisor. S3/S4 always keep `eligibilityStatus: not_confirmed`.

For a source with `research` in `claimDomains`, the source-level `topicRelevance` is a derived summary of `personRoles[].topicRelevance`: `direct` takes precedence over `adjacent`, which takes precedence over `background`. A source without the `research` domain must use `not_applicable`. This scalar must never contradict the person-specific rows shown in the source ledger.

Every `direct` or `adjacent` person-topic attribution needs a source-specific claim or faithful page paraphrase. A candidate summary copied into a source record during Markdown migration (for example, `Institutional research page retained for NAME's documented focus: ...`) is circular and can remain only as a `background` discovery lead until the linked page is re-read and the exact person-topic relationship is captured.

`confidenceByClaim` is authoritative and must include `currentRole`, `contact`, `research`, `supervision`, and `recruitment`, each as `high`, `medium`, `low`, `unverified`, or `not_applicable`. The legacy scalar `confidence` is optional and deprecated. `claimSourceIds` provides field-level traceability for `group`, `academicRole`, `adminClinicalRole`, `focus`, `phdTypes`, `doctoralRoute`, `directionOverviewZh`, `structuredProfileZh`, `scientificQuestions`, `materialsModels`, `methods`, `validationMaturity`, and `roleBoundary`; include every field that carries a material claim. For the three current-role fields, every cited source must be current, official-institution, candidate-bound and carry a compatible `personRoles[].roleType` plus retained wording appropriate to that field: `programme_host` is allowed only for `adminClinicalRole`; project/trial/grant/publication/collaboration/team-member/doctoral-supervision roles cannot support any of the three. A source label that expressly says the specific title was not retained cannot support these fields or a concrete `affiliations[].role`. Do not copy all `currentRoleSourceIds` into all three fields.

For A-tier application-readiness facts, `applicationClaimSourceIds` maps contact protocol, application window, eligibility, required documents, proposal requirement, funding model, supervision setup, and general applicant fit to claim-appropriate evidence. Generic programme pages may support rules but not person-level supervision. `researchGap`, `proposedAim`, and `generalApplicantFit` are bounded analyst syntheses, each explicitly marked by its corresponding `...AnalystDerived: true` flag; their research basis still needs candidate-bound evidence. They are writing inputs, not approved projects or applicant-specific prose. The legacy aggregate `applicationSourceIds`, `proposalSourceIds`, and `fundingSourceIds` remain for compatibility but do not replace field-level mapping.

`opportunities[]` is authoritative for parallel routes. Each item uses a unique lowercase slug `id`; `scope` = `person`, `lab`, or `programme`; one of the eight opportunity statuses; non-empty `routeName` and `contactPolicy`; `deadlineType` = `fixed`, `rolling`, `until_filled`, `not_stated`, or `not_applicable`; a deadline value when applicable; and source IDs. The legacy `opportunityDetail` field is unsupported in strict schema 1.2 and must remain blank; put route-specific details in `opportunities[].contactPolicy`. The compatibility summary `opportunityStatus` must equal one status represented in the array, `opportunityDeadline` must match the summarized fixed-date route when one exists, and `recruitmentSourceIds` must include all opportunity and recruitment-audit sources. These summary fields must not upgrade a programme route into a person-specific vacancy.

For summary or route status `route_confirmed_no_vacancy`, `no_public_evidence`, or `direct_enquiry_recommended`, `recruitmentAudit` is required and records the actual check date, required `checkedScopes` string array covering every audited route scope, non-empty `portals` objects (`name`, narrow `result`, and official `sourceIds`), concrete `queries`, a narrow overall result, and aggregate official source IDs. A negative audit must include a current official vacancy-portal source bound to the candidate or school. It establishes only the public-search result as of that date. `direct_enquiry_recommended` additionally requires a non-D record, high/medium-confidence candidate-bound current official personal role, a published contact channel, and a current official doctoral/recruitment route; otherwise use `no_public_evidence` or `unverified`.

`verifiedAt` records the actual date the person's current role was checked. It must be ISO `YYYY-MM-DD`, no later than `case.asOf`, and backed by at least one current official role source accessed on that date; no current-role source may postdate it. It is not forced to equal the case date and is not a catch-all date for literature or recruitment. When the gap exceeds 30 days, render “核验已陈旧，使用前需复核”; when it exceeds 90 days, reverify before strict delivery.

Chinese/Xiaohongshu check status: `verified_source_found`, `lead_only`, `not_found_publicly`, `public_access_blocked`, `not_searched`.

Each completed Chinese/Xiaohongshu check records `checkedAt`, the actual query variants (at least three for the wider Chinese-web check and at least two for Xiaohongshu), a concise `summary`, an `accessNote`, and source IDs when evidence was found. `not_searched` is draft-only. Use `public_access_blocked` rather than `not_found_publicly` when the target content could not be inspected.

Each conflict object:

```json
{
  "field": "current affiliation",
  "category": "announced_future_change",
  "officialValue": "Current role",
  "otherValue": "Future role from 2026-12-01",
  "decision": "Keep current role until effective date and flag recheck.",
  "effectiveDate": "2026-12-01",
  "sourceIds": ["src-current", "src-future"]
}
```

Use the conflict categories in `evidence-policy.md`.

### `sources.json`

Each evidence record:

```json
{
  "id": "src-person-profile",
  "type": "official_role_contact",
  "claimDomains": ["current_role", "contact"],
  "authorityClass": "official_institution",
  "medium": "webpage",
  "title": "Official staff profile",
  "url": "https://example.edu/person",
  "publisher": "Example University",
  "publishedDate": "",
  "accessedDate": "2026-09-06",
  "claim": "Current role and published email.",
  "personRoles": [
    {
      "subjectId": "university-of-zurich-person-name",
      "roleType": "group_leader",
      "exactLabel": "Head of Example Research Group",
      "topicRelevance": "background"
    }
  ],
  "subjectIds": ["university-of-zurich-person-name"],
  "workId": "",
  "identifiers": {},
  "topicRelevance": "not_applicable",
  "status": "current"
}
```

Each record has one mutually exclusive primary `type`; use `claimDomains` to record every claim family actually supported by the page: `ranking`, `school_structure`, `research`, `current_role`, `contact`, `doctoral_rule`, `doctoral_supervision`, `admissions_funding`, `recruitment`, `conflict`, or the discovery-only `discovery`. `doctoral_rule_supervision` may support `doctoral_rule`, `doctoral_supervision`, or both, but only when the page actually carries that claim; it cannot prove a personal current title, contact, or direct research line unless the page explicitly states that person-specific fact. `subjectIds` lists the stable school/candidate IDs explicitly named by the source. It is mandatory for person-level role, affiliation, personal/clinical contact, research, direct-evidence, and research-anchor claims; a generic programme page does not bind those claims to a person. `personRoles[]` maps each person subject through `subjectId`, `roleType`, verbatim or tightly faithful `exactLabel`, and person-specific `topicRelevance`; never concatenate unscoped roles from several people into one scalar. Allowed role types are `subject_profile`, `group_leader`, `independent_faculty`, `unit_head`, `principal_investigator`, `co_principal_investigator`, `co_investigator`, `principal_applicant`, `co_applicant`, `grant_applicant`, `grant_recipient`, `trial_responsible_investigator`, `sub_investigator`, `collaborator`, `team_member`, `senior_or_corresponding_author`, `first_author`, `coauthor`, `mentioned_without_role`, `named_investigator`, `programme_host`, `eligible_supervisor`, `doctoral_supervisor`, and `co_supervisor`. Use the page's own distinction: an applicant, co-applicant, award recipient, sub-investigator, collaborator, or team member is not a PI unless the same source explicitly says so. Authorship is person-specific: another person's last/corresponding label cannot upgrade the candidate, while explicit equal-contribution/co-senior wording is valid. Use `mentioned_without_role` when a source names a person but does not establish the desired role; a source that does not name the person must not carry that person's ID or role. `exactLabel` must contain the actual role wording or a narrow faithful paraphrase, not migration placeholders such as `role described on page`, `named profile/group member`, `Candidate-associated official research URL`, `Candidate-bound official profile/contact URL`, or `anchor attribution is described in the linked source`. `topicRelevance: direct` is invalid when the same person's label or the source claim explicitly says the work is not/non-lung or that lung cancer is not that person's research line. `authorityClass` and `medium` are mandatory and must match the actual publisher and carrier, not the desired claim. The special `discovery_lead` source type uses only `claimDomains: ["discovery"]`, scalar/person topic `not_applicable`, `mentioned_without_role`, and the fixed transparent label `Discovery lead only; legacy association not used as role/topic evidence`; it may appear only in `case.supportingSourceIds` or `case.discoveryPasses[].sourceIds`, never in substantive evidence fields. A discovery-pass citation records how a candidate entered the pool and does not validate any role, topic, contact, affiliation, supervision, recruitment, or ranking claim.

The URL's publishing host, `authorityClass`, and primary `type` must agree. Publication hosts such as PubMed, PMC, Europe PMC, and DOI resolvers cannot be encoded as `official_institution`; ClinicalTrials.gov must remain a trial-registry authority, SNSF a funder authority, and QS/TopUniversities a ranking-publisher authority. These pages may expose affiliations, correspondence emails, investigators, awards, or institutional names, but they do not thereby become current institutional role/contact profiles.

Allowed authority classes are `official_ranking_publisher`, `official_institution`, `official_funder_registry`, `official_trial_registry`, `official_government_regulator`, `primary_publication`, `researcher_controlled`, `professional_secondary`, `social_user_generated`, and `other_secondary`. Do not label a trial registry as a funder merely to satisfy validation.

Allowed source types: `official_ranking`, `official_research_profile`, `official_role_contact`, `official_school_structure`, `publication`, `grant_project`, `clinical_trial`, `doctoral_rule_supervision`, `official_admissions_funding`, `official_vacancy_portal`, `vacancy`, `chinese_secondary`, `social_user_generated`, `other_secondary`, `discovery_lead`.

Allowed topic relevance: `direct`, `adjacent`, `background`, `not_applicable`. Allowed status: `current`, `future`, `historical`, `closed`, `unclear`. Future-dated or `status: future` evidence may document an announced change, but it cannot support a current role, direct topic claim, current recruitment status, or supervision classification before its effective/publication date.

Canonicalize URLs for statistics by lowercasing host, removing fragments, removing default ports, sorting query parameters, and dropping common tracking parameters. Preserve the original URL in the source record. Reuse one source record when one URL supports several claims. Assign the same shared `workId` to alternate landing pages for one underlying paper, grant, trial, or posting, and retain all known DOI/PMID/PMCID/grant/trial/posting identifiers. A publication, grant, or trial used as A-tier direct evidence must always carry `workId`; this prevents a DOI page and PubMed page with disjoint identifiers from being counted twice.

The validator also rejects one formal identifier assigned to multiple `workId` values, conflicting same-type identifiers inside one `workId`, and DOI/PubMed/ClinicalTrials URL-to-identifier mismatches. It cannot discover a deliberately omitted DOI-to-PMID crosswalk without external lookup, so researchers must still reconcile alternate landing pages before finalization.

## 4. Markdown outputs

### `00-INDEX.md`

Include case scope, verification date, links to every output, candidate/tier counts, one computed evidence-statistics line, unresolved warnings, and coverage limitations.

### `01-SCHOOL-SCOPE.md`

Render the scope-audit ranking system, edition, publication date, and official sources; then render both included schools and checked exclusions. The included-school table contains stable school ID, origin, QS publication date, inclusion decision/reason, medical-system relationship, and all sources.

| ID | Country/region | School | Origin | QS edition/publication date/rank/status | Medical-system status | Formal related hospitals/centres/networks | Decision/reason | Sources |
|---|---|---|---|---|---|---|---|---|

### `02-SUPERVISOR-TABLE.md`

Group by school, then A/B/C/D. Include at least:

| Name/group/ID | Universities, faculties, departments, and institutional relationships | Research focus and overview | Academic role | Administrative/clinical role | Published contact, type, and source | Topic/Supervision/Tier | Suitable PhD types | Doctoral route | Scoped opportunities | Sources and cautions |
|---|---|---|---|---|---|---|---|---|---|---|

### `03-COVERAGE-MATRIX.md`

Show every school and coverage area, units inspected, result, candidates found, evidence, and access limitations.

### `04-EVIDENCE-CONFLICTS.md`

Include source-priority rules, all conflicts, future changes, stale information, Chinese checks, Xiaohongshu checks, inaccessible pages, and unresolved fields. Preserve both sides and source links. Every social check row shows candidate ID, status, check date, actual queries, summary, access note, and sources.

### `05-A-TIER-DEEP-PROFILES.md`

For every A-tier record include:

- one-sentence positioning;
- 150–250-character direction overview;
- structured profile over 500 characters;
- scientific questions and research lines;
- sample/model and method workflow;
- validation maturity and authorship/project-role boundary;
- 2–3 bounded doctoral work-package objects, each marked `analystDerived: true` with scope, assumptions, and candidate-bound evidence;
- evidence links.

### `06-APPLICATION-READINESS.md`

For every A-tier record include contact protocol, application window, eligibility, required documents, proposal rules, funding model, supervision setup, doctoral route, every scoped opportunity, the dated recruitment audit, safest sourced `researchAnchor`, evidence-based `researchGap`, bounded `proposedAim`, general-fit backgrounds, resource/supervision/funding questions, and cautions. Mark gap, aim, and general fit as analyst-derived and state that they are not approved projects or personal-fit claims. This is a data-only handoff: no string anywhere in `applicationReadiness`, or in any doctoral work-package field, may contain an email subject, salutation, sign-off, first-person application request, CV-attachment sentence, personalized fit prose, or full proposal prose.

### `07-SOURCE-LEDGER.md`

List every evidence record exactly once with type, claim domains, subject IDs, authority class, medium, work ID/identifiers, title, publisher, dates, claim, person role, relevance, status, and direct URL.

## 5. Length and evidence requirements

- A-tier direction overview: 150–250 Chinese characters after whitespace removal.
- A-tier structured profile: more than 500 Chinese characters after whitespace removal.
- Do not claim the direction overview itself exceeds 500 characters.
- A-tier: at least one current official role source and normally two direct recent topic-evidence sources.
- Count independent direct evidence by underlying `workId`, not merely by source ID, URL, or one landing page's identifier. A and T4 are incompatible; lower the tier or correct topic directness.
- T3: at least one current official candidate-bound research/project record with person-specific `topicRelevance: direct`; a historical paper or merely adjacent platform cannot establish a current lung-cancer application.
- B/C candidates also need at least one topic-evidence source appropriate to the claimed fit.
- Every candidate: at least one current role source or explicit unverified/D-tier status.
- Every contact: candidate- or school-bound source ID, or a blank/source-free `not_public` marker.
- Every route is represented in `opportunities[]`; a programme-, lab-, and person-level route remain distinguishable.
- Every `open_current` opportunity: at least one current official vacancy source. For `scope: person`, that source explicitly names the candidate and includes the candidate ID in `subjectIds`; until a separately validated lab registry exists in the schema, a `scope: lab` opening must also be candidate-bound. A `fixed` deadline requires a future ISO date; `rolling` and `until_filled` require explicit official wording.
- Every `route_confirmed_no_vacancy`, `no_public_evidence`, or `direct_enquiry_recommended` summary or route: a dated, sourced `recruitmentAudit` across person/lab/programme official pages or portals.
- Every conflict: both sides and at least two source IDs, except a clearly labeled low-confidence single-source warning.
- Every complete Chinese/Xiaohongshu check: check date, actual queries, summary, access note, and no `not_searched` status.
- Evidence totals: compute from `sources.json`; report one consistent set of evidence-record and unique-URL numbers.

## 6. Validation and delivery

`validate_case.py --strict` must return zero errors. Warnings may remain only when surfaced in `00-INDEX.md` and the relevant table/profile.

Before delivery, verify:

1. Every included school ID appears in `schools.json` and `01-SCHOOL-SCOPE.md`; every checked exclusion appears in the exclusion table.
2. Every school has all coverage areas.
3. No duplicate candidate ID or same name/school pair exists.
4. Every referenced source ID exists.
5. Every material current claim has a field-level source mapping in `claimSourceIds`; group, academic-role and administrative/clinical-role citations are current official candidate-bound sources with field-compatible person roles.
6. Every contact, affiliation, opportunity, and negative recruitment audit has traceable source IDs where required.
7. Every source URL is valid; authority/medium/claim-domain metadata are coherent; canonical URL and underlying-work deduplication do not inflate evidence.
8. Recruitment language matches each scoped opportunity and deadline type; programme openings are not presented as person openings.
9. A-tier length and evidence requirements pass.
10. All generated Markdown links resolve locally.
11. Every included school and candidate ID is visibly represented in the rendered outputs.
12. No outreach-email, cover-letter, applicant-specific pitch, or full research-proposal content appears.
