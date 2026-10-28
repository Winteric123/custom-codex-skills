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
├── 08-CONTACT-AUDIT.md (only when data/contact-audit.json exists)
└── data/
    ├── case.json
    ├── schools.json
    ├── coverage.json
    ├── records.json
    ├── sources.json
    └── contact-audit.json (optional)
```

Keep the JSON files as the only hand-edited source of truth. Regenerate Markdown after any correction.

The directory tree above illustrates the narrow profile. New `cv_aligned_oncology` cases use the initializer's distinct `cv-oncology-<topic-hash>` scope tag instead of `lung-cancer`; do not reuse a narrow case directory to switch profile.

Schema `1.2` is intentionally stricter than earlier cases. Preserve pre-`1.2` data and reports as a historical snapshot, migrate them into a new dated case directory, add the required scope/affiliation/opportunity/audit/source metadata, and validate the migrated case. Never overwrite an older report in place merely to make it appear current.

## 2. Classification axes

Do not use one label for research relevance, supervision evidence, and recruitment.

Apply the institutional eligibility gate in `search-playbook.md` before these axes. Engineering/computing/standalone-data-only exclusions, and unresolved gate leads, belong in sourced `coverage[].notes` outside the supervisor roster, not in a lower tier. They do not count in `records.json`, coverage candidate IDs, discovery-pass additions, or A/B/C/D totals. An explicit user exception must be recorded in the case notes/limitations and the retained person's `notes`; the schema remains `1.2`. Updating this default does not itself rescreen historical cases or a user-approved list.

Apply the independent research-direction gate from `candidate-exclusions.md` before these axes as well. Paediatric oncology and haematologic malignancies are excluded only when current person-specific evidence shows that they are the main or predominant focus of the person's overall current research programme; a co-equal parallel, secondary or collaborative line does not itself exclude an otherwise eligible candidate. Retain unresolved dominance with a dated caution. Nuclear medicine and radiomics/core clinical or molecular tumour imaging remain excluded when current core or explicit parallel lines. Store defaults/overrides in `case.limitations` and named, dated, sourced exclusions in `coverage[].notes`, outside every candidate count and discovery addition. Preserve real research exclusion evidence in school-bound source records with no ghost candidate IDs/person roles. Record retained parallel/secondary or dominance-unresolved paediatric/haematologic lines and the balance decision in `records[].notes`. Do not add unvalidated schema fields; these defaults are initialized as limitations in new cases and do not rewrite resumed historical cases.

### Topic directness

Interpret T codes using `case.topicProfile`. Missing means `lung_cancer` for backward compatibility. Explicit `cv_aligned_oncology` uses the broader approved axes in `cv-aligned-scope.md`; never change an old case's profile or its source relevance in place merely to pass validation.

| Code | Meaning |
|---|---|
| `T1` | Current independent or sustained direct lung-cancer line. |
| `T2` | Current thoracic-oncology line with lung cancer and another thoracic disease in parallel. |
| `T3` | Pan-cancer or methods platform with an explicit current lung-cancer project or application. |
| `T4` | Lung cancer is collaborative, historical, exploratory, or not clearly independent. |

The table above retains the narrow lung-profile meanings. Under `cv_aligned_oncology`: T1 is a current independent/sustained direct line in an approved oncology axis; T2 is a current multi-cancer or multi-axis oncology programme that explicitly includes an approved axis; T3 is a broader platform with an explicit current application in an approved cancer axis; T4 is collaborative, historical, exploratory or unclear independence in that declared scope. L1–L3 discovery bands express lung-first/broad-oncology preference and are not replacements for T codes or A–D tiers; retain the matched band/axis, actual disease and training gap in `records[].notes`.

In strict delivery, `T1` and `T2` require two candidate-bound current official facts: a direct line within the declared profile and an independent group-leader or PI role. One page may prove both, but a paired official research page and official role page is also valid; each source record must retain only the fact it actually states. A publication alone does not prove a current independent line. `T3` requires a current candidate-bound explicit in-profile project or application. Historical, collaborative, future, or role-unclear evidence remains `T4` unless stronger current evidence exists. Broad-profile direct claims require a source-specific cancer/oncology anchor; keyword validation is not a substitute for manually verifying the approved scientific axis or institutional gate.

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
| `D` | Historical, moved, weak topic fit, materially conflicted, or too weak to approach now; never a container for institutional/research-direction exclusions. |

Tier does not encode vacancy status. A-tier does not mean currently recruiting. Conversely, failure to verify a vacancy, `route_confirmed_no_vacancy`, `closed_expired`, `no_public_evidence`, or `unverified` recruitment must not exclude/delete an otherwise eligible record or lower its topic, supervision, or A–D classification. Preserve the candidate and record opportunity status separately. An explicit negative PI/lab reply belongs in a dated, intake/scope-limited correspondence/outreach-control overlay with a recheck condition unless an independent research-roster exclusion also applies. If surfaced in the research package, store only minimal metadata in `records[].notes` and A-tier `applicationReadiness.cautions[]`, linked to an external correspondence ledger; private email/screenshots are not public `sources.json` evidence.

Disease preference does not replace readiness grading. Under `cv_aligned_oncology`, apply the disease-breadth modifier from `cv-aligned-scope.md` within otherwise comparable evidence/readiness groups: a verified programme limited to one or a few thoracic malignancies ranks ahead of a similarly supported narrow non-thoracic programme, with lung cancer/NSCLC/SCLC first and oesophageal, pleural or thymic/mediastinal malignancies retained as thoracic. Broad multi-tumour, pan-cancer and general cancer-mechanism programmes remain separately comparable on axis fit, supervision and route and are not automatically demoted. Store the bounded classification and supporting disease/source IDs in `records[].notes`; do not raise a weak thoracic lead to A or alter T evidence quality merely because of the tumour site.

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

The C1–C8 themes can also describe the broader oncology profile; do not force a thoracic label onto another cancer. For cancer genetic/clinical epidemiology and causal inference, a defined additional category such as C9 is acceptable, with its meaning retained in the case notes.

## 3. Structured JSON schema

Use UTF-8 JSON with two-space indentation. IDs must be stable lowercase ASCII slugs derived from identity, never from input order; use a deterministic hash suffix only for true slug collisions.

### `case.json`

```json
{
  "schemaVersion": "1.2",
  "location": "Switzerland",
  "topic": "thoracic oncology, especially lung cancer",
  "topicProfile": "lung_cancer",
  "applicationMaterialsAuditRequired": true,
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

`case.topicProfile` is an optional backward-compatible schema-1.2 field with exactly two values: `lung_cancer` and `cv_aligned_oncology`. Absence alone defaults to legacy lung; an explicit empty/unknown value is invalid. `case.topic` is a display description, not an implicit mode selector. New broad cases must declare their profile and summarize accepted applicant-aligned axes/preferences in `case.limitations[]` or discovery queries; mark band/axis and any neutral evidence gap in the candidate's existing `notes`. Do not insert an applicant CV as official supervisor evidence or add unvalidated candidate-fit fields. Broad output directories are distinct from narrow cases; preserve and never silently reclassify existing cases.

`case.applicationMaterialsAuditRequired` is an optional boolean in schema 1.2. New initializations set it to `true`; absence/false preserves legacy validation without rewriting historical files. In a strict complete case with this flag, every A/B/C candidate's viable opportunity routes need `applicationReadiness.documentRequirements` covering motivation letter, supervisor enquiry/pre-contact, recommendation letters and research proposal. Additional official documents are recorded as applicable. Arrays present in legacy cases are still validated; an absent flag is not permission to present unsupported material claims.

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

Chinese display contract for every new or touched candidate record:

- The user-facing faculty/department/unit, current appointment/title, and research direction must be Chinese-first. This applies to chat answers and every rendered artifact, not only `02-SUPERVISOR-TABLE.md`.
- Populate `faculty`, `department`, `group`, `academicRole`, `adminClinicalRole`, `focus`, and `directionOverviewZh` with a substantive Chinese rendering when the field is applicable. A bilingual value may retain the exact official label after the Chinese text, for example `研究组负责人（Head of Research Group）`; an English/German/local-language-only value is not delivery-ready.
- Apply the same rule to the displayed content of `affiliations[].institution`, `.faculty`, `.department`, `.relationship`, and `.role`. Preserve exact source-language role wording in `sources[].personRoles[].exactLabel` and official names/URLs in source records, so translation never replaces evidence.
- Translate conservatively and never upgrade title, rank, independence, clinical seniority, or supervision authority. Where no safe exact equivalent exists, use a bounded Chinese functional description followed by the official label and an uncertainty note. Where the underlying fact is absent, use an explicit Chinese missing marker such as `未公开` or `未核实`; do not invent a translation or leave a user-facing cell blank.
- Chinese column headings alone are insufficient: the value in each of these fields must itself contain meaningful Chinese text.

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
  "opportunityStatus": "route_confirmed_no_vacancy",
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
    "documentRequirements": [],
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

Contact types: `personal_email`, `clinical_email`, `group_email`, `unit_email`, `department_mailbox`, `secretariat_email`, `assistant_contact`, `phone`, `contact_form`, `not_public`. A `not_public` contact is an exclusive missing-value marker: set `value` to an empty string, `status` to `not_public`, and `sourceIds` to an empty array, and use it only when no public form, mailbox, assistant, phone, or other usable route was found. Never attach an inferred address or a source that did not publish a value. For `personal_email` and `clinical_email` with `published_current`, at least one single cited record must simultaneously be current, `official_institution`, contact-domain, and candidate-bound; do not combine unrelated sources to satisfy those properties. The mailbox must visibly identify the candidate and must not be an obvious unit/office/secretariat alias; use `assistant_contact` for another named person's published address and `unit_email` or the more specific group/department/secretariat type for generic mailboxes. A researcher-controlled ORCID email is a discovery lead, not official current contact evidence: independently verify it on an institutional page or omit that address from the deliverable. Preserve any verified fallback route; use the blank `not_public` marker only if no such route exists.

In strict schema 1.2, each `records[].contacts[]` object is closed to exactly `type`, `value`, `status`, and `sourceIds`. The validator rejects extra keys such as `owner`, `currentness`, `channelId`, or `preferredRoute` in that strict object. Put those richer audit fields only in optional `data/contact-audit.json`; this prevents the strict current-contact record from silently accepting unsupported supplemental metadata.

When a publication explicitly binds an email to the candidate as corresponding author but no current official institutional page confirms that mailbox, retain it only in the dated supplemental contact audit defined by `contact-verification-playbook.md` as `publication_correspondence_email`, with publication year, owner binding, currentness caution, and source URL. Do not insert that supplemental type into strict schema-1.2 `records[].contacts`, and do not replace an available current official non-personal route with it. If a current official institutional page independently publishes the same mailbox, store the official evidence as the strict personal/clinical contact and keep the publication source only as corroboration when useful.

### Optional `contact-audit.json`

Use this supplemental file whenever a run specifically finds, refreshes, compares, or displays contact channels. Its presence activates both strict validation and rendering of `08-CONTACT-AUDIT.md`. It must be an object, not a bare array:

```json
{
  "schemaVersion": "1.0",
  "checkedAt": "2026-10-25",
  "records": [
    {
      "candidateId": "example-university-person-name",
      "checkedAt": "2026-10-25",
      "currentInstitutionZh": "示例大学医学中心",
      "searchAudit": {
        "officialFallbacksExhaustedBeforePublication": true,
        "steps": [
          {
            "stage": "current_official_primary",
            "routeType": "personal_profile",
            "resultZh": "官网本人页面已检查。",
            "sourceIds": ["src-person-profile"]
          },
          {
            "stage": "current_official_fallback",
            "routeType": "person_directed_form",
            "resultZh": "找到本人定向表单。",
            "sourceIds": ["src-person-form"]
          },
          {
            "stage": "publication",
            "routeType": "primary_publication",
            "resultZh": "论文列出本人通讯邮箱。",
            "sourceIds": ["src-person-paper"]
          }
        ]
      },
      "channels": [
        {
          "channelId": "official-person-form",
          "type": "contact_form",
          "value": "https://example.edu/person/contact",
          "owner": "candidate",
          "currentness": "current_official",
          "sourceIds": ["src-person-form"],
          "candidateBound": true,
          "notesZh": "当前官方本人定向入口。"
        },
        {
          "channelId": "paper-email-2025",
          "type": "publication_correspondence_email",
          "value": "person@example.edu",
          "owner": "candidate",
          "currentness": "publication_time_only",
          "sourceIds": ["src-person-paper"],
          "candidateBound": true,
          "sourceDate": "2025",
          "notesZh": "仅由论文通讯作者栏确认。"
        }
      ],
      "preferredRoute": {
        "preferredChannelId": "official-person-form",
        "reasonZh": "当前官方且本人定向。",
        "sameDayRecheckRequired": false
      },
      "contactPolicy": "not_stated",
      "cautionZh": "公开联系方式不等于允许未经邀请的联系。"
    }
  ]
}
```

`candidateId` must resolve to exactly one `records.json` record. `channelId` is a per-candidate unique lowercase ASCII slug. Allowed channel types are `personal_email`, `clinical_email`, `publication_correspondence_email`, `group_email`, `unit_email`, `department_mailbox`, `secretariat_email`, `assistant_contact`, `phone`, `contact_form`, and `not_public`. Allowed owners are `candidate`, `assistant`, `group`, `unit`, `department`, `secretariat`, `institution`, and `unclear`. Allowed currentness values are `current_official`, `publication_time_only`, `former_institution`, `currentness_unverified`, `historical`, and `not_public`. Every channel must contain `owner`, `currentness`, and `sourceIds`; every real-valued channel needs at least one valid source ID. A `current_official` channel needs one same current `official_institution`, contact-domain source bound to the candidate or applicable school. A `publication_correspondence_email` needs one same candidate-bound, contact-domain `primary_publication` source.

`preferredRoute` must select one existing non-`not_public` channel through `preferredChannelId`, explain the Chinese reason, and state whether a same-day recheck is needed. If any usable `current_official` channel exists, the preferred route must select a current-official channel; a same-day recheck flag cannot justify preferring a paper, historical, former-institution, or unverified route over it. A publication-time or otherwise not-current channel must set `sameDayRecheckRequired: true` only when no current-official channel is available. If and only if the sole channel is `not_public`, set `preferredRoute` to `null`. A `not_public` channel cannot coexist with any valued channel in either `contact-audit.json` or `records.json`; it must have empty `value`, owner `unclear`, currentness `not_public`, and an explicit `sourceIds` array (which may be empty for a documented negative search).

The ordered `searchAudit.steps[]` records official-primary, official-fallback, publication, researcher-controlled, or other checks. When a publication step or `publication_correspondence_email` exists, `officialFallbacksExhaustedBeforePublication` must be `true`, at least one official-primary and one official-fallback step must precede it, and no official step may occur after the first publication step. This protects person-directed forms, group/unit/department/secretariat channels, assistants, and phones from being overwritten by a paper email or `not_public` marker.

`schoolId` is the primary grouping university, not the whole affiliation claim. `additionalSchoolIds` lists other included universities with a verified current relationship, and the school-ID set represented by `affiliations[]` must match the primary plus additional IDs exactly. Each affiliation records `schoolId`, `institution`, `faculty`, `department`, precise `relationship`, `role`, and source IDs; use an explicit `not_applicable` marker rather than leaving a required unit field blank. For an affiliation assigned to an additional school, at least one cited current `official_institution` source with the `current_role` claim domain must include both the candidate ID and that additional school ID in `subjectIds`. Two separately bound sources cannot be combined to meet this requirement. Keep the legacy scalar `faculty`, `department`, and `affiliatedInstitution` only as a concise compatibility summary; do not use it to erase cross-school or hospital distinctions.

`supervisionBasis` is mandatory in strict cases. Keep person-level supervision/activity and formal prospective eligibility separate. `S1` uses `person_eligibility_explicit`, `documented_thesis_supervision`, `named_current_supervision`, or `named_supervisor_in_doctoral_posting`, with `personSupervisionStatus: confirmed`; only the first basis may use `eligibilityStatus: confirmed`, while the others keep eligibility `not_confirmed`. `person_eligibility_explicit` requires one same current official candidate-bound doctoral-rule record whose person role is `eligible_supervisor`; a generic programme rule and a separate person page cannot be combined into eligibility. `named_current_supervision` requires a current official person-bound page that explicitly names the person as supervisor or co-supervisor. `S2` uses `current_doctoral_trainees` or `programme_pi_or_host`, sets `personSupervisionStatus: activity_supported`, and keeps eligibility `not_confirmed`. S1/S2 both require candidate-bound current official independent-role evidence (`group_leader`, PI/co-PI, `independent_faculty`, or `unit_head`) plus candidate-bound official `doctoral_supervision` or `doctoral_rule` evidence. `independent_faculty` requires an explicit full/associate professor or tenure-track assistant-professor title; `unit_head` requires explicit department/division/service/centre/institute leadership. PD/Privatdozent or attending alone is not independence. A generic programme page proves only a route and cannot by itself support S2. `S3` is always `basisType: unverified`, `status: route_only_unverified`, and `personSupervisionStatus: unverified`. `S4` may use that same unverified form, or may preserve documented co-supervision as `basisType: co_supervision_only`, `status: limited_person_level`, and `personSupervisionStatus: co_supervision_supported` when an official candidate-bound source identifies the person as co-supervisor. S3/S4 always keep `eligibilityStatus: not_confirmed`.

For a source with `research` in `claimDomains`, the source-level `topicRelevance` is a derived summary of `personRoles[].topicRelevance`: `direct` takes precedence over `adjacent`, which takes precedence over `background`. A source without the `research` domain must use `not_applicable`. This scalar must never contradict the person-specific rows shown in the source ledger.

Every `direct` or `adjacent` person-topic attribution needs a source-specific claim or faithful page paraphrase. A candidate summary copied into a source record during Markdown migration (for example, `Institutional research page retained for NAME's documented focus: ...`) is circular and can remain only as a `background` discovery lead until the linked page is re-read and the exact person-topic relationship is captured.

`confidenceByClaim` is authoritative and must include `currentRole`, `contact`, `research`, `supervision`, and `recruitment`, each as `high`, `medium`, `low`, `unverified`, or `not_applicable`. The legacy scalar `confidence` is optional and deprecated. `claimSourceIds` provides field-level traceability for `group`, `academicRole`, `adminClinicalRole`, `focus`, `phdTypes`, `doctoralRoute`, `directionOverviewZh`, `structuredProfileZh`, `scientificQuestions`, `materialsModels`, `methods`, `validationMaturity`, and `roleBoundary`; include every field that carries a material claim. For the three current-role fields, every cited source must be current, official-institution, candidate-bound and carry a compatible `personRoles[].roleType` plus retained wording appropriate to that field: `programme_host` is allowed only for `adminClinicalRole`; project/trial/grant/publication/collaboration/team-member/doctoral-supervision roles cannot support any of the three. A source label that expressly says the specific title was not retained cannot support these fields or a concrete `affiliations[].role`. Do not copy all `currentRoleSourceIds` into all three fields.

For A-tier application-readiness facts, `applicationClaimSourceIds` maps contact protocol, application window, eligibility, required documents, proposal requirement, funding model, supervision setup, and general applicant fit to claim-appropriate evidence. Generic programme pages may support rules but not person-level supervision. `researchGap`, `proposedAim`, and `generalApplicantFit` are bounded analyst syntheses, each explicitly marked by its corresponding `...AnalystDerived: true` flag; their research basis still needs candidate-bound evidence. They are writing inputs, not approved projects or applicant-specific prose. The legacy aggregate `applicationSourceIds`, `proposalSourceIds`, and `fundingSourceIds` remain for compatibility but do not replace field-level mapping.

`applicationReadiness.documentRequirements` is a backward-compatible optional array usable for every A/B/C candidate, independently of whether the candidate receives an A-tier deep profile. Each object records `routeId`, controlled `materialType`, `requirementStatus`, `submissionStage`, non-empty `summary`, `formatAndLength`, `submissionMethod`, positive-integer-or-null `quantity`, controlled `submitter`, ISO `checkedAt` and `sourceIds`. The full enums and evidence rules are in `application-materials-checklist.md`. The route ID must belong to the same candidate's opportunities. Asserted required/optional/conditional/not-required states need appropriate current official candidate- or school-bound sources accessed no later than the check date. `not_public`/`unverified` may be source-free. Do not infer not-required from omission or force PI enquiry into a formal-upload document. Avoid duplicate same route/type/stage rows; use the actual stage when a rule changes at shortlisting or offer. Missing-state rows keep uncertainty visible, not zero counts or implied exemptions.

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

Each record has one mutually exclusive primary `type`; use `claimDomains` to record every claim family actually supported by the page: `ranking`, `school_structure`, `research`, `current_role`, `contact`, `doctoral_rule`, `doctoral_supervision`, `admissions_funding`, `recruitment`, `conflict`, or the discovery-only `discovery`. `doctoral_rule_supervision` may support `doctoral_rule`, `doctoral_supervision`, or both, but only when the page actually carries that claim; it cannot prove a personal current title, contact, or direct research line unless the page explicitly states that person-specific fact. `subjectIds` lists the stable school/candidate IDs explicitly named by the source. It is mandatory for person-level role, affiliation, personal/clinical contact, research, direct-evidence, and research-anchor claims; a generic programme page does not bind those claims to a person. `personRoles[]` maps each person subject through `subjectId`, `roleType`, verbatim or tightly faithful `exactLabel`, and person-specific `topicRelevance`; never concatenate unscoped roles from several people into one scalar. Allowed role types are `subject_profile`, `group_leader`, `independent_faculty`, `unit_head`, `principal_investigator`, `co_principal_investigator`, `co_investigator`, `principal_applicant`, `co_applicant`, `grant_applicant`, `grant_recipient`, `trial_responsible_investigator`, `sub_investigator`, `collaborator`, `team_member`, `senior_or_corresponding_author`, `first_author`, `coauthor`, `mentioned_without_role`, `named_investigator`, `programme_host`, `eligible_supervisor`, `doctoral_supervisor`, and `co_supervisor`. Use the page's own distinction: an applicant, co-applicant, award recipient, sub-investigator, collaborator, or team member is not a PI unless the same source explicitly says so. Authorship is person-specific: another person's last/corresponding label cannot upgrade the candidate, while explicit equal-contribution/co-senior wording is valid. Use `mentioned_without_role` when a source names a person but does not establish the desired role; a source that does not name the person must not carry that person's ID or role. `exactLabel` must contain the actual role wording or a narrow faithful paraphrase, not migration placeholders such as `role described on page`, `named profile/group member`, `Candidate-associated official research URL`, `Candidate-bound official profile/contact URL`, or `anchor attribution is described in the linked source`. In `lung_cancer`, `topicRelevance: direct` is invalid when the same person's label or source claim expressly negates a lung/thoracic research line. In `cv_aligned_oncology`, non-lung disease is allowed when a positive approved cancer axis is supported; an overall non-oncology claim or generic methods with no cancer anchor cannot be direct. A negated lung statement alone is not a positive broad oncology anchor. `authorityClass` and `medium` are mandatory and must match the actual publisher and carrier, not the desired claim. The special `discovery_lead` source type uses only `claimDomains: ["discovery"]`, scalar/person topic `not_applicable`, `mentioned_without_role`, and the fixed transparent label `Discovery lead only; legacy association not used as role/topic evidence`; it may appear only in `case.supportingSourceIds` or `case.discoveryPasses[].sourceIds`, never in substantive evidence fields. A discovery-pass citation records how a candidate entered the pool and does not validate any role, topic, contact, affiliation, supervision, recruitment, or ranking claim.

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

For every row, render the faculty/department/unit, academic and administrative/clinical appointment, and research focus/direction in Chinese. Chinese comes first; the verified official label may follow in parentheses. Never emit only the untranslated source string in these columns. If a value is unavailable, show `未公开` or `未核实` and the applicable caution/source boundary.

### `03-COVERAGE-MATRIX.md`

Show every school and coverage area, units inspected, result, candidates found, evidence, and access limitations.

Render `coverage[].notes` visibly, including the name/unit, reason and source IDs for institutionally excluded or unresolved leads. An existing engineering/data branch with no eligible candidates is `searched`, not `not_present`. The candidate table and its tier counts must not reintroduce these names as D-tier targets.

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

Begin with the sourced application-materials matrix for all A/B/C candidates and their viable routes. Display official document names/type, required/optional/conditional/explicitly-not-required/missing status, stage, number, applicant/referee submission, format/length/method, check date and sources. Distinguish PI enquiry or supervisor consent from programme materials. If a legacy case lacks the structured audit, display that limitation instead of saying documents are unnecessary.

For every A-tier record include contact protocol, application window, eligibility, required documents, proposal rules, funding model, supervision setup, doctoral route, every scoped opportunity, the dated recruitment audit, safest sourced `researchAnchor`, evidence-based `researchGap`, bounded `proposedAim`, general-fit backgrounds, resource/supervision/funding questions, and cautions. Mark gap, aim, and general fit as analyst-derived and state that they are not approved projects or personal-fit claims. This is a data-only handoff: no string anywhere in `applicationReadiness`, or in any doctoral work-package field, may contain an email subject, salutation, sign-off, first-person application request, CV-attachment sentence, personalized fit prose, or full proposal prose.

### `07-SOURCE-LEDGER.md`

List every evidence record exactly once with type, claim domains, subject IDs, authority class, medium, work ID/identifiers, title, publisher, dates, claim, person role, relevance, status, and direct URL.

### Optional `08-CONTACT-AUDIT.md`

Render this file only when `data/contact-audit.json` exists. Show every audited candidate, check date, current institution in Chinese, ordered official-first search steps, every channel's type/value/owner/currentness/source, preferred route, contact-policy boundary, cautions, and whether same-day rechecking is required. The index must link it. A publication-only email is always visibly labelled as publication-time evidence, never as a current official personal mailbox.

## 5. Length and evidence requirements

- A-tier direction overview: 150–250 Chinese characters after whitespace removal.
- A-tier structured profile: more than 500 Chinese characters after whitespace removal.
- Do not claim the direction overview itself exceeds 500 characters.
- A-tier: at least one current official role source and normally two direct recent topic-evidence sources.
- Count independent direct evidence by underlying `workId`, not merely by source ID, URL, or one landing page's identifier. A and T4 are incompatible; lower the tier or correct topic directness.
- T3: at least one current official candidate-bound research/project record with person-specific `topicRelevance: direct`; a historical paper or merely adjacent platform cannot establish a current in-profile application (lung cancer in narrow mode, an approved oncology axis in broad mode).
- B/C candidates also need at least one topic-evidence source appropriate to the claimed fit.
- Every candidate: at least one current role source or explicit unverified/D-tier status.
- Every strict-schema contact: candidate- or school-bound source ID, or a blank/source-free `not_public` marker. When `contact-audit.json` exists, each real supplemental channel also has owner, currentness, a unique channel ID, and at least one valid source ID; its preferred channel ID resolves within the same candidate record.
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
13. Every retained candidate passes the institutional eligibility and research-direction gates or has an explicit recorded user exception; confirmed exclusions and unresolved nuclear-medicine/imaging leads remain in sourced coverage notes outside the roster and candidate counts. Manually check whether paediatric or haematologic oncology is the main/predominant focus of the person's overall current programme, and separately check current core/parallel nuclear-medicine and radiomics/imaging lines, using `candidate-exclusions.md`. A retained parallel/secondary or dominance-unresolved paediatric/haematologic line needs a dated balance note but is not an exception. Schema validation and positive-topic anchor regexes alone establish neither faculty eligibility nor research-direction eligibility.
14. The selected topic profile and actual disease/axis are visible; broad-profile candidates have a manual approved-axis check and no invented lung link. L1–L3 preferences, T evidence quality, A–D readiness, applicant skill gaps and opportunity/funding status remain separate.
    Every recommended A/B/C candidate also has a dated oncology-relevance statement in `notes`, retaining disease/model or cancer-risk endpoint, cancer-specific question, current official source IDs, primary-literature cross-check and actual person role. Classify current programme leadership and current project participation separately using `candidate-exclusions.md`; non-oncology or unresolved relevance is not rescued by method overlap or a cancer-institute affiliation.
15. New cases require a route-specific materials audit for every A/B/C candidate; motivation/SOP, PI pre-contact, reference letters and proposals are not inferred from another route or a visible email address. Keep missing states explicit and confirm count, submitter, format, stage and source date.
16. No candidate is excluded, deleted, or downgraded solely because a current vacancy could not be verified, no public opening was found, a call is closed, or recruitment is `unverified`. Recruitment/opportunity state remains separate from research eligibility, topic/supervision evidence, priority tier, and any correspondence-based outreach hold.
17. Every user-facing supervisor row or profile has substantive Chinese values for faculty/department/unit, current appointment/title, and research direction. Chinese headings with English-only values fail this check. Official labels may follow the Chinese rendering, and an unavailable fact is shown with an explicit Chinese missing marker rather than a blank or invented translation.
18. If `data/contact-audit.json` exists, `08-CONTACT-AUDIT.md` exists and is linked from the index; every candidate/channel/source reference resolves, official fallbacks precede paper searching, `preferredChannelId` names a usable channel, and `not_public` never coexists with a form, organizational mailbox, phone, or other valued route.
