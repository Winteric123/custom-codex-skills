# Search playbook

## Contents

1. Scope and school screen
2. Institution mapping
3. Candidate discovery
4. Person-level verification
5. Literature and method deepening
6. Grants, trials, doctoral routes, and vacancies
7. Chinese and social-source checks
8. Search saturation and handoff

## 1. Scope and school screen

Record the exact verification date. Current ranks, appointments, jobs, rules, and funding always require live browsing.

Declare `case.topicProfile` before searching. The default is `lung_cancer`, which is also the interpretation of historical cases with no profile. Use `cv_aligned_oncology` only when the user explicitly selects the broader axes and L1–L3 discovery bands in `cv-aligned-scope.md`; pass that profile explicitly to the initializer. A display-topic string alone does not authorize broader evidence labels.

### Location-only input

1. Resolve the literal location to the exact country/subnational/multi-jurisdiction filter used by the ranking source; retain the mapping and an official jurisdiction source in `locationResolution`.
2. Open the latest official QS World University Rankings material.
3. Record the ranking edition and the page's publication/current date separately.
4. Select institutions in the requested country or region with overall rank at or above the user's threshold; default threshold is top 300.
5. Preserve equal ranks and rank bands exactly. Do not convert a band into a single number, and require every positive inclusion to have a parseable rank or band within the threshold.
6. If an institution is specialist, unranked, excluded from the overall table, or only present in a subject ranking, state that status rather than guessing.
7. Write the exact included school IDs to `scopeAudit.includedSchoolIds`. Record each checked-but-excluded institution, its observed QS status/rank, exclusion reason, and source IDs in `scopeAudit.excludedInstitutions`.

`schools.json` is the included set. Do not add an out-of-threshold school and then excuse it with `namedByUser=true`; location-only and named-school runs are distinct scope modes.

### Named-school input

Include every named school. Add current QS status as context, not as an exclusion rule. Resolve renamed institutions, campuses, and similarly named schools through official sites.

### Medical-system classification

Use one of:

- `medical_faculty_present`
- `medical_program_without_medical_faculty`
- `health_sciences_without_medical_degree`
- `specialist_medical_institution`
- `no_medical_faculty`
- `unclear`

Verify official faculties, degree-awarding responsibility, and hospital relationships separately. A teaching hospital, university hospital, affiliated hospital, and collaborative cancer centre are not interchangeable.

## 2. Institution mapping

Create a school-by-branch coverage matrix before collecting names. Always inspect these branches, recording `not_present` when appropriate:

| Coverage area | Typical units and keywords |
|---|---|
| medicine-clinical | medicine, oncology, pulmonology, thoracic surgery, radiation oncology, respiratory medicine |
| life-science-biomedicine | molecular medicine, cancer biology, immunology, genetics, biochemistry, cell biology |
| cancer-hospital | comprehensive cancer centre, university hospital, thoracic oncology centre, research institute |
| pathology-diagnostics | pathology, molecular pathology, cytology, radiology, nuclear medicine, interventional pulmonology |
| public-health-data | epidemiology, biostatistics, registries, clinical trials, population health, health data science |
| engineering-ai-imaging | biomedical engineering, AI, medical imaging, robotics, computer science, physics |
| pharmacy-drug-discovery | pharmacy, pharmacology, medicinal chemistry, drug discovery, chemical biology |
| veterinary-comparative | veterinary oncology, comparative pathology, animal cancer models |

### Institutional eligibility gate (before topic scoring)

Search coverage is not candidate eligibility. By default, exclude a person whose only verified current appointments are in an engineering faculty/school/department (including engineering-based biomedical engineering), computer science, or a standalone AI, data science, data analytics, or equivalent computing/data unit. Apply this to the actual organizational home, not merely keywords in a research title. A lung-cancer publication, medical application, funded project, clinical collaborator, or professor title does not override the gate.

Use these boundaries:

- Eligible homes can include medicine/health sciences, affiliated hospitals, cancer centres/institutes, biomedical/life sciences, pharmacy, public health, and the other non-excluded topic-relevant branches above. They still need research and supervision verification; being outside engineering is not sufficient.
- Medical informatics, clinical data science, biostatistics, computational pathology and cancer bioinformatics within an actual medical/hospital/cancer unit are not excluded just because they use computation. Medical imaging must independently pass the research-direction gate below.
- Pure mathematics or statistical-methods appointments without a verified eligible biomedical/medical/cancer appointment follow the same institutional exclusion; medical biostatistics is judged by its actual organizational home and cancer research line.
- An engineering/computing primary appointment may qualify through a separately verified current appointment in medicine, a hospital, or a cancer institute. Preserve both appointments and identify the qualifying one. A candidate-bound current official appointment/group-role page must establish it; being a collaborator, co-author, network participant, or listed project partner does not count.
- A generic joint centre name, a biomedical label, or an old article affiliation is not proof of a qualifying current appointment. Where the organizational home or joint role remains unclear, keep a sourced pending/exclusion note outside the recommended roster until resolved.
- Do not exclude a whole technical university without inspecting its medical partnerships and genuinely eligible joint appointments. Equally, naming that university does not waive the person-level gate.
- A user's explicit request to include a named engineering/computing candidate or this class can override the default for that case. Record the exception and its reason; do not infer it from a school name or a change of research topic. Do not retroactively remove candidates from an existing user-approved list merely because the global skill was updated.

Keep excluded people outside `records.json`, A/B/C/D counts, `coverage[].candidateIds`, and discovery-pass `newCandidateIds`/`newCandidateCount`. Log the name, verified unit, check date, decision, reason, and evidence IDs in the relevant `coverage[].notes`, and cite the actual inspected official pages in that row's `sourceIds` (plus a `case.limitations[]` summary when needed). Preserve each page in `sources.json` with its actual authority/type and the name/role in `claim`; encode only the `current_role`/`school_structure` claims actually used for this exclusion audit and use `topicRelevance: not_applicable`, not a research match. Because excluded people are not schema entities, do not invent their IDs in `subjectIds` or `personRoles`. Bind only applicable existing school IDs explicitly supported by the page. These school-bound exclusion audits are not substitutes for retained-candidate role evidence. Do not invent schema fields or use `discovery_lead` sources as coverage evidence. If an inspected branch exists but yields no eligible person, use `searched` with empty `candidateIds`, not `not_present`; use `blocked_unverified` when a missing/inaccessible appointment page prevents resolving a material lead. Where eligible and excluded people coexist, keep only eligible IDs and make the exclusion note person-specific, not a contradictory branch-wide "no qualifying candidates" statement. The exclusion notes must remain visible in the coverage report.

Use official organization charts, faculty lists, department indexes, people directories, and research-group indexes. Record every actually inspected unit and its source ID in `coverage.json`; do not infer a unit name from a candidate's research-focus keywords. A `candidates_found` row retains both school-bound branch evidence and current official candidate-bound research/current-role evidence for each listed person.

Map organizational relationships conservatively. “University hospital”, “affiliated hospital”, “teaching partner”, “joint centre”, and “research collaborator” are not synonyms. For a candidate with joint roles, create one `affiliations[]` entry per verified university/institution relationship and list every additional in-scope university in `additionalSchoolIds`; retain a primary `schoolId` only for grouping and stable identity.

### Research-direction gate (before topic scoring)

First establish the candidate's current person-specific oncology relevance using the disease/question/role audit in `candidate-exclusions.md`. Record the actual cancer question, not just method names, and cross-check the primary literature. Keep direct current programmes separate from named current cancer-project participation; non-oncology or unresolved leads cannot enter the recommended A/B/C set.

Read `candidate-exclusions.md` and apply its configured defaults in both profiles. Exclude paediatric oncology or haematologic malignancy only when current person-specific evidence shows that it is the main or predominant focus of the person's overall current research programme; retain an otherwise eligible candidate when those diseases are co-equal and parallel, secondary or collaborative, and record that balance in candidate notes. If dominance remains unresolved, retain the candidate with a dated caution and recheck priority rather than treating uncertainty as exclusion. Separately exclude nuclear medicine and radiomics/core clinical or molecular tumour-imaging programmes when current core or explicitly parallel. Keep the inspected unit in coverage and its sourced exclusions visible; passing the institutional gate does not waive a threshold that is actually met. Use current official person/programme evidence, resolving material ambiguity with recent primary research or current projects. Apply the same gates to later additions from papers, grants, trainees and collaborators. Record defaults/explicit overrides in `case.limitations`; keep confirmed exclusions and unresolved nuclear-medicine/imaging leads outside roster and discovery-addition counts.

## 3. Candidate discovery

Use several query families. Replace bracketed terms with official, local-language, and common English variants.

### Official-site queries

```text
site:[university-domain] (lung cancer OR NSCLC OR SCLC OR mesothelioma OR thoracic oncology)
site:[hospital-domain] (lung tumor OR thoracic surgery OR pulmonary oncology) (research OR group OR laboratory)
site:[university-domain] (doctoral OR PhD OR dissertation OR supervisor) (lung OR thoracic OR cancer)
site:[university-domain] [person-name] (profile OR publications OR projects)
```

### Method and adjacent-field queries

```text
[school] (lung cancer) (single-cell OR spatial OR organoid OR liquid biopsy OR multi-omics)
[school] (NSCLC) (immunotherapy OR resistance OR metabolism OR pathology OR radiotherapy)
[school] (lung nodule OR bronchoscopy OR screening OR metastasis) research group
```

### Local-language queries

Translate only stable concept words such as lung cancer, thoracic oncology, doctoral student, supervisor, grant, and vacancy. Keep the person's official spelling. Search diacritic and ASCII variants.

### Discovery expansion

Expand from:

- group members and collaborator lists;
- cancer-centre programmes;
- current grants and trial investigator lists;
- recent relevant papers' first, senior, and corresponding authors;
- current and completed dissertations;
- doctoral programme PI or host lists;
- core facilities when a lung-cancer project is explicit.

For `cv_aligned_oncology`, expand these same sources across the approved cancer axes, not only lung-keyword results. Use the query sets in `cv-aligned-scope.md`; inspect oncology, tumour immunology, molecular medicine, pathology, cancer genomics, clinical pharmacology and public-health cancer groups that pass the institutional gate.

Do not include a person solely because a search engine associates their page with a keyword. Open the page, record the direct relationship, and apply the institutional eligibility and research-direction gates before retaining the candidate. The imaging/nuclear-medicine branches remain coverage and exclusion checks, not default positive recruitment-target query families.

### Research-topic boundary

Under `lung_cancer`, the topic is thoracic oncology, primarily lung cancer (including NSCLC and SCLC); other thoracic cancers such as mesothelioma are secondary, not an automatic substitute for a lung-cancer line. Relevant lines can span systemic therapy, resistance, tumour immunity/microenvironment, biomarkers, molecular pathology, screening/diagnosis, surgery, radiotherapy, disease mechanisms, organoids/models, and drug discovery. These are search families, not proof that every person using those methods studies lung cancer.

Under `cv_aligned_oncology`, prioritize lung cancer but also search current solid-tumour/pan-cancer immunity, immune escape, immunometabolism, clinical treatment-response biomarkers, molecular precision oncology, translational genetics/genomics, multi-omics, cancer molecular/cell biology and bounded cancer-epidemiology/causal-inference lines in the case's approved broad scope. Cancer-linked DNA replication/repair, chromatin, RNA, cell-cycle and signalling mechanisms can qualify without an immediate clinical trial or lung-cancer project. A non-lung cancer line is not automatically T4 or low priority: judge its current direct fit to an approved axis, independence, supervision evidence and the training gap separately. Generic genetics, molecular biology, immunology, multi-omics, AI or biomaterials without a current cancer relationship is not enough.

For priority ordering under `cv_aligned_oncology`, also classify disease breadth from the verified current programme. When a supervisor works in only one or a few named tumour types, prefer thoracic malignancy programmes over otherwise comparable narrow non-thoracic programmes; within thoracic oncology, lung cancer/NSCLC/SCLC comes first, followed by oesophageal cancer, pleural mesothelioma, thymic/mediastinal and other verified thoracic malignancies. Keep broad multi-tumour, pan-cancer and general cancer-mechanism programmes on a separate comparison track and judge their axis fit, supervision and route rather than mechanically placing them below every thoracic lead. Record the result and supporting diseases/source IDs in `records[].notes`; do not change a T code or A–D tier solely because the preferred disease name appears.

Use the profile-specific topic codes in `output-spec.md` only after both gates pass: T1/T2 need both a current official direct line within the declared profile and an independent group-leader/PI role; T3 needs an explicit current in-scope project/application; T4 covers collaborative, historical, exploratory or unclear independence. Record the actual cancer/disease, approved CV axis, L1–L3 band and any transfer/training gap in `records[].notes`. Keep the evidence faithful to the source; do not add lung cancer to an otherwise non-lung professor's description. An institutionally or research-direction-excluded person remains excluded regardless of topic code or the applicant's R/Python skills.

## 4. Person-level verification

For each candidate, verify:

1. Official name and spelling.
2. Current institution and department.
3. Academic title.
4. Administrative or clinical role.
5. Group-leadership role.
6. Direct research evidence within the declared profile; record lung versus non-lung scope honestly.
7. Formal supervisory evidence or uncertainty.
8. Published contact and contact type.
9. Current recruitment evidence or absence of a public posting.

For item 8, follow `contact-verification-playbook.md` completely. A completed contact audit must inspect the current official person/institution routes and every applicable official fallback (person-directed form, group/unit/department/secretariat channel, assistant and telephone) before opening recent candidate-bound correspondence records. Preserve every usable fallback channel and label its owner; do not collapse it into a personal email, and never use `not_public` while any real fallback remains. Record the ordered search in optional `data/contact-audit.json` so validation can confirm that official fallback steps preceded paper searching.

For each recommended person, retain a dated oncology-relevance statement in `notes` with disease/model or cancer-risk endpoint, the cancer-specific question, current official source IDs, primary-paper cross-check and actual person role. Verify whether oncology is their current line or a named project contribution; a general immunology/omics lab with only a historical cancer coauthorship is insufficient for a current recommendation.

Attach source IDs to each affiliation and each contact. If an official page publishes only a department or secretariat channel, preserve that type instead of presenting it as the person's direct address.

A paper can prove that an address was assigned to the named corresponding author at that publication time. It does not by itself prove that the address is current, institutionally recommended, or permission for unsolicited outreach. Keep publication-only channels in the dated supplemental contact audit described in `contact-verification-playbook.md`; promote an address to a strict `personal_email` or `clinical_email` record only when a current official institutional source independently publishes it for the same person.

Use `unit_email` for an institutional unit alias and `assistant_contact` for a named assistant's published address. A personal/clinical email must visibly match the candidate, not another person's name, and must not be an obvious office, centre, department, group, or secretariat mailbox.

Set `verifiedAt` to the actual date that person's current role was last checked. It must be an ISO date no later than `case.asOf`, with at least one official current-role source accessed on that date and none accessed later. Do not use this field as a catch-all date for literature or recruitment. If it is more than 30 days before `case.asOf`, surface “核验已陈旧，使用前需复核”; a record older than 90 days must be reverified before strict delivery.

Disambiguate common names with at least two stable identifiers. Prefer an official profile plus affiliation-linked publication, ORCID, institutional email, or stable collaborator network. Keep conflicting author identities out of the record.

## 5. Literature and method deepening

### Search order

1. Official publication list or ORCID for identity anchors.
2. PubMed author query with affiliation and disease terms.
3. Europe PMC for abstracts, grants, and open full text.
4. PMC or publisher full text for Methods, cohorts, models, and limitations.
5. Crossref or DOI resolver for metadata correction.

### Suggested PubMed patterns

```text
"Surname Initials"[Author] AND (lung neoplasms[MeSH Terms] OR lung cancer OR NSCLC OR SCLC)
"Full Name"[Author] AND (mesothelioma OR thoracic)
("Institution"[Affiliation]) AND "Surname Initials"[Author] AND 2022:3000[dp]
```

Verify identity through affiliation and co-authors; do not trust an author-name match alone. For each included paper record:

- title, journal, year, DOI and PMID/PMCID when present;
- paper type and evidence maturity;
- disease, cohort/model, sample scale if verified;
- discovery methods, validation methods, and outcome;
- exact candidate role and source for that role;
- direct/adjacent/background topic relevance;
- limitation relevant to a possible doctoral extension.

Prefer original research. Label reviews, protocols, conference abstracts, preprints, and corrections. Do not count a preprint and its final article twice.

Topic codes also need role-aware evidence. `T1` and `T2` require candidate-bound current official facts for the declared direct topic and independent group-leader/PI role; a paper alone is not enough to prove a current independent line. `T3` needs a current candidate-bound explicit project/application within the selected profile (lung cancer in narrow mode, an approved oncology axis in broad mode). Keep collaborative, historical, future or role-unclear evidence at `T4` unless stronger current evidence exists. Never count a future publication/status as current direct evidence before `case.asOf`.

### Build the research-method profile

Organize each A-tier profile by:

- scientific problem;
- direct and secondary research lines;
- patient material, data, cells, organoids, animals, or computational models;
- discovery, functional, statistical, and translational methods;
- validation level: internal, external, orthogonal, in vivo, prospective;
- what the evidence does and does not establish;
- bounded doctoral work packages.

Do not infer platform ownership from one co-authored paper. Describe use as collaborative when the source does not show control by the candidate's group.

## 6. Grants, trials, doctoral routes, and vacancies

Search official national funder databases, institutional project portals, EU CORDIS where relevant, and official trial registries. Record project title, funder, amount only if explicit, dates, status, and exact person role.

Apply vacancy-neutral retention throughout this section. Failure to verify `open_current`, no public posting, a closed call, an inaccessible portal, or an `unverified` recruitment state changes only the opportunity/recruitment result; it cannot remove an otherwise eligible candidate, lower T/S/A–D, or alter research source links. Keep the candidate in `records.json` and coverage. A direct PI/lab reply stating no place or capacity is available for a specified intake may be recorded as a dated, scope-limited outreach hold with the intake/scope and recheck condition, not as a research exclusion. Keep the private message in an external correspondence ledger; surface only minimal metadata in `records[].notes` and, for A-tier, `applicationReadiness.cautions[]`, never as a public source. Evaluate retirement, institutional move, or loss of supervision eligibility separately if the same communication explicitly establishes it, while preserving historical evidence in coverage/source audit.

Search each school's:

- doctoral regulations and admissions pages;
- programme or graduate-school pages;
- supervisor eligibility rules;
- official vacancy portal;
- faculty-specific vacancy portal;
- scholarship and external-funding rules;
- current host/rotation list when relevant.

Also collect the facts needed for a later outreach email or research-plan workflow without drafting either document:

- whether direct PI contact is accepted and the official contact channel;
- application windows, deadlines, eligibility, language requirements, and required documents;
- whether a research proposal is required, including official format, length, template, and submission route;
- employment, stipend, tuition/fees, project funding, and external-scholarship constraints when explicitly stated;
- main/co-supervision rules, daily-supervision arrangements when public, and required committee structure.

For every viable A/B/C candidate, use `application-materials-checklist.md` to inspect the separate programme, PI/lab, scholarship and doctoral-employment routes. Record motivation/personal statements, cover letters, pre-contact/supervisor agreement, recommendation letters, research proposals and other official documents as separate items in `applicationReadiness.documentRequirements`. Check required/optional/conditional/not-required status, official label, length/format, number, who submits, portal/email route, stage and verification date. A public email, supervisor list or suggestion to contact a PI does not make a cold email a mandatory admissions document. An omitted item is unverified/not public, not automatically not required.

For jobs, record posting ID, title, host, deadline, employment/funding type, topic scope, and current status. Open the full posting. A search snippet or aggregator is only a lead.

Create one `opportunities[]` item for each distinct route. Set `scope` to `person`, `lab`, or `programme`; record route name, status, deadline type (`fixed`, `rolling`, `until_filled`, `not_stated`, or `not_applicable`), date when applicable, official contact policy, and source IDs. Keep a programme-wide call separate from a lab statement and from a named-person vacancy. A programme-level opening cannot be rolled up to person-level `open_current` unless the official call actually accepts applications for that person or lab. For a person-scoped current opening, the vacancy source must explicitly name the candidate and list the candidate ID in `subjectIds`. Until the schema has a separately validated lab-entity registry, apply the same candidate binding to a lab-scoped `open_current` claim.

Check the date logic:

- `open_current`: an official posting accepts applications; a fixed deadline is future, while `rolling` or `until_filled` must be stated by the source.
- `planned_official`: official page explicitly announces a future call or position.
- `route_confirmed_no_vacancy`: valid doctoral route or supervisor eligibility exists, but no current vacancy is shown.
- `direct_enquiry_recommended`: a non-D candidate has a verified current personal role, published contact channel, and official doctoral/recruitment route, but public availability and funding remain unresolved. Do not use it mechanically for role-unverified or D-tier records.
- `historical_only`: a past supervision route or position is verified, but current availability is unknown.
- `closed_expired`: posting is closed or deadline passed.
- `no_public_evidence`: no current public recruitment evidence was found; internal plans remain unknown.
- `unverified`: official evidence is insufficient.

For `route_confirmed_no_vacancy`, `no_public_evidence`, and `direct_enquiry_recommended`, add `recruitmentAudit` with the date, required `checkedScopes`, non-empty official person/lab/programme `portals`, actual `queries`, concise result, and official source IDs. At least one current official vacancy portal bound to the candidate or school must be accessed on that date, and no cited audit source may postdate it. This supports the negative public-search statement without converting it into a claim about internal plans.

## 7. Chinese and social-source checks

Run at least three Chinese-web query variants and at least two Xiaohongshu query variants per person. In CV-aligned mode, add/replace topic terms with the person's actual accepted axis and disease (for example 肿瘤免疫, 免疫代谢, 精准肿瘤学, 食管癌, 肿瘤遗传流行病学); do not audit a non-lung candidate only through lung queries. Start with:

```text
"[English full name]" [school Chinese name] 肺癌
"[English full name]" 博士 招生
"[English full name]" 任职 OR 教授 OR 主任
site:xiaohongshu.com "[English full name]"
site:zhihu.com "[English full name]"
```

Also search reliable Chinese medical media, conference faculty pages, institutional Chinese releases, and public WeChat indexes. Record in each `chineseCheck` and `xiaohongshuCheck`:

- the exact check date and queries;
- a source that directly names the person;
- publication date and the date described;
- which field it supports or conflicts with;
- whether it is a translation, repost, interview, conference page, or user-generated post;
- an access note when login, robots restrictions, regional access, or indexing limits prevent inspection.

Do not use a Chinese article about the institution to verify an unnamed person's role. Do not use patient-trial `招募中` to claim employment recruitment. If a platform is inaccessible, use `public_access_blocked` and state why. `not_found_publicly` is reserved for an actually executed and accessible public search; `not_searched` is draft-only.

## 8. Search saturation and handoff

Before finalization:

1. Complete every coverage-matrix row.
2. Run a first expansion pass from official units and research groups.
3. Run a second pass from papers, grants, dissertations, and collaborators.
4. Run a final query pass for omitted faculties, local-language terms, and name variants.
5. Record how many qualified candidates each pass added.
6. Resolve duplicates and moved/retired people.
7. Keep historical, moved, or weak topic/role leads in D tier only when their warning matters and they have not been rejected by either eligibility gate. Put institutional and research-direction exclusions, and materially unresolved institutional/research-direction gate leads, in sourced coverage notes outside the roster, not in D tier. Count only retained candidates as additions.

End with an explicit coverage statement and limitations. `case.status: complete` means that the research package was generated and passed its structural checks; it never means that every branch was exhausted. A zero-addition saturation pass establishes only saturation of the documented public queries and accessible branches. If any row is `blocked_unverified`, the final saturation pass must record an actual retry/recheck of those gaps and the limitations must describe the result as bounded by them, never as exhaustive coverage. Never claim access to private vacancies, internal funding, unindexed staff, or closed social-platform content.

The handoff to a later writing workflow is data-only: verified application facts, a sourced `researchAnchor`, analyst-derived `researchGap`/`proposedAim`, questions, and cautions. Do not generate reusable email phrases, subject lines, salutations, claims about the applicant, or proposal prose in this research run. The writing workflow must separately collect applicant inputs and recheck unstable role/contact/opportunity facts.
