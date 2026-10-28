# Research-method and clinical-translation audit

Use this reference whenever the user asks how a supervisor's recent work is actually performed, whether a group combines experiments and computation, whether work is clinically translational, or when method/translation fit should affect prioritisation.

This audit is an independent axis. It must not overwrite topic directness, supervision evidence, A/B/C/D readiness, vacancy status, or a correspondence-based outreach hold.

## 0. Default activation and completion standard

Run this assessment for every retained A/B/C supervisor in every full supervisor-research package, even when the user does not separately ask for a method audit. A narrow contact, title, deadline, or one-person factual update may reuse a still-current portfolio audit unless the answer depends on an unresolved or stale method claim.

Every retained A/B/C record must end in one of these explicit states:

- `confirmed`: a confirmed portfolio and unprefixed `MTG` grade that meets the review-depth rule below;
- `provisional`: a machine-assisted or partially reviewed portfolio with a `pMTG#` grade;
- `ungraded`: `MTG-U`, used only after all declared eight-year ledger searches finish without truncation and find zero usable candidate-bound eligible oncology original papers;
- `incomplete`: no grade is asserted because identity, authorship, access, search truncation, or a current-direction conflict prevents even a bounded conclusion.

Do not silently omit the audit for a retained supervisor. The minimum complete portfolio pass is:

1. record the databases, exact queries, structured window start/end dates, pages/cursors inspected, result counts, truncation status, retry and exclusion/deduplication ledger, then enumerate the bounded publicly identifiable candidate-bound eligible original-paper set in the active five-to-eight-year window;
2. assign and evidence the candidate's author-role code for each included paper;
3. assign one paper-level method code and one independent translation code;
4. record review depth and the evidence features that caused each code;
5. aggregate the complete strong-role portfolio without cherry-picking;
6. compare the publication portfolio with the current official programme description;
7. report the portfolio code, `MTG` result, confidence, unresolved conflicts, and whether the result is confirmed or provisional.

Use the result as a separate fit axis. It is not an input to A/B/C, T or S. Use it only after all eligibility and exclusion gates and only among candidates tied on A/B/C tier, T band, S band and explicit user priorities. Confirmed grades may then order `MTG1 > MTG2 > MTG3 > MTG4`; `pMTG#`, `MTG-U` and `incomplete` are uncertainty states, not lower grades. Opportunity status may order outreach actions separately, not scientific rank.

## 1. Separate scientific-audit and outreach states

Never store vacancy or correspondence control as the scientific audit state. The two fields coexist:

- `scientificAuditStatus`: `confirmed`, `provisional`, `ungraded`, or `incomplete`.
- `opportunityStatus`: the current route/vacancy state copied from the base research record.
- `outreachControl.status`: `active`, `hold_no_capacity`, or `hold_user`.

`hold_no_capacity` means a dated direct PI/lab reply or current official statement explicitly says that no position or supervision capacity is available. It pauses only further outreach for the stated intake/scope. `hold_user` records a user-requested pause or exclusion with reason, date and recheck condition. No public opening, an expired call, or an unverified vacancy belongs only in `opportunityStatus`, not in `outreachControl`. Neither opportunity nor outreach state suppresses, freezes or substitutes for a fresh scientific portfolio audit when the retained A/B/C record otherwise needs one.

For scientific conflicts, record both `material`/`resolved` and `impact`. An unresolved `BLOCKS_GRADE` conflict forces `scientificAuditStatus=incomplete`, `grade=null`, and no scores. `NONBLOCKING_PROVISIONAL` may support a defensible provisional grade but can never coexist with `confirmed` while unresolved.

## 2. Time window, paper eligibility and author role

Use a rolling five-year window ending on the verification date. Enumerate the bounded publicly identifiable candidate-bound set of eligible original research before selecting examples. Never claim absolute bibliographic completeness. For reproducibility, retain a search ledger containing every database or official publication list searched, the exact query and human-readable date filter, structured `windowStart`/`windowEnd`, search date, pages/cursors or last result inspected, reported result count, whether the result set was truncated, each retry, inclusion/exclusion decision, and deduplication key. Candidate-level and every ledger-entry window must equal the declared five- or eight-year interval ending on `caseAsOf`; a handwritten `windowYears: 8` without ledger entries covering that interval is invalid.

Set `searchStatus=bounded_complete` only when every source and query required by the documented search plan has run through all pages or cursors without material truncation or access failure and the retrieved, excluded and deduplicated counts reconcile. This means bounded public-search completion, not bibliographic exhaustiveness. Otherwise use `search_incomplete`; do not confirm purity or an unprefixed MTG if the missing evidence could alter the denominator, code or grade.

Use these terms consistently:

- `candidate-bound`: identity is matched to the person under review by the disambiguation rule below, regardless of author position;
- `candidate-led`: an eligible candidate-bound paper coded `O3C`, `O2C`, `O2S`, `O1L`, or `O1F`; this term controls the five-to-eight-year extension and continuity score, but does not by itself prove current programme ownership;
- `strong-role`: an eligible candidate-bound paper coded `O3C`, `O2C`, or `O2S`;
- `eligible`: an original oncology research paper that enters the denominator after document-type, retraction, date and identity checks.
- `usable`: the person-paper identity and source record are strong enough to assign at least a provisional author-role, method and translation code; an unresolved name match or inaccessible record with no classifiable abstract/design is not usable.

If fewer than five eligible candidate-led papers are found in five years, extend the search to eight years and state that the extended window was used. After eight years:

- one or two usable papers permit only a provisional low-confidence type/grade;
- zero usable candidate-bound eligible papers after all declared ledger searches finish without truncation is `MTG-U`; machine-only but usable papers require a provisional `pMTG#`, not `MTG-U`;
- if identity, access or search truncation prevents deciding whether usable papers exist, use `incomplete`, not `MTG-U`;
- never claim that a programme is a pure type from a thin portfolio.

Represent this as a two-stage search, not a handwritten window label. Give every planned query a unique `queryId`. Every query must have one complete `BASE_5Y` ledger entry covering exactly `caseAsOf - 5 years` through `caseAsOf`. When the reconstructed five-year candidate-led count is below five, set `windowYears=8`, set `extensionReason=fewer_than_five_candidate_led_in_base_5y`, and add a complete `EXTENDED_8Y` entry for every planned query covering exactly `caseAsOf - 8 years` through `caseAsOf`. When the five-year count is at least five, require `windowYears=5`, `extensionReason=null`, and exclude years six to eight from the active denominator. Reconcile result counts from the active stage only so the base and extended retrievals are not double-counted.

Use the first formal online publication date and deduplicate preprint/formal versions by DOI, PMID, PMCID or other stable work ID. Reviews, editorials, guidelines, protocols, meeting abstracts, corrections, retraction notices, retracted publications and commentaries do not enter the classification denominator. Clinical-trial results are original research and must be classified by their actual design. Case reports are supplementary evidence only.

Prioritise roles in this order, while keeping the labels exact. Store the derived role code and the underlying corresponding-, senior- and first-author statuses separately, so author order can never masquerade as a correspondence declaration:

| Code | Evidence-backed role | Weight |
|---|---|---:|
| `O3C` | explicit corresponding/last-corresponding author | 1.00 |
| `O2C` | explicit co-corresponding author | 0.85 |
| `O2S` | explicit senior/co-senior author who is not a corresponding author | 0.70 |
| `O1L` | last author without corresponding proof | 0.45 |
| `O1F` | recent first/co-first author; informative for hands-on contribution but not proof of current independent programme ownership | 0.35 |
| `O0` | ordinary middle author, consortium member, or penultimate author without explicit co-corresponding/co-senior evidence | 0.15 |

Store `correspondingStatus=CORRESPONDING|CO_CORRESPONDING|NOT_CORRESPONDING|UNVERIFIED`, `seniorStatus=EXPLICIT_SENIOR|CO_SENIOR|LAST_AUTHOR_ONLY|NOT_SENIOR|UNVERIFIED`, and `authorOrderStatus=FIRST|CO_FIRST|LAST|PENULTIMATE|MIDDLE|CONSORTIUM|OTHER`. Derive the role by precedence: corresponding → `O3C`; co-corresponding → `O2C`; otherwise explicit senior/co-senior → `O2S`; otherwise last author → `O1L`; otherwise first/co-first → `O1F`; all others → `O0`. Retain candidate-bound authorship evidence source IDs and a locator; at least one authorship source must be a publication record carrying the same stable `workId` and must also appear in the paper's `sourceIds`. `O3C`/`O2C` must be backed by an explicit correspondence record and `O2S` by an explicit contribution/senior statement. Author order alone never proves corresponding authorship. A penultimate position without an explicit contribution/correspondence statement remains `O0`. Ordinary collaboration can show participation but cannot define the supervisor's group programme.

Before binding a paper to a person, disambiguate with at least two of affiliation, ORCID, existing candidate-bound PMID/DOI, specialty, official publication list, and stable co-author network. Common-name query results without such corroboration remain unresolved.

### Review depth and required evidence features

Record the established review-depth label for every included paper and record the portfolio cross-check separately. Preserve these meanings so new audits remain comparable with historical snapshots:

- `M0_MACHINE_ABSTRACT`: machine-assisted title/abstract triage only; always provisional.
- `M2_HUMAN_ABSTRACT`: legacy token for a deliberate paper-by-paper review of the complete title and abstract plus the bibliographic and available author-role record; still provisional for claims that depend on design details omitted from the abstract. Because the historical token contains `HUMAN`, reports must call it “逐篇摘要深读” unless `reviewActor=human_manual`.
- `M3_FULL_TEXT_DESIGN`: full methods/results and the relevant contribution/correspondence record were inspected sufficiently to resolve methods, cohorts, validation, trial linkage and author role. A publisher summary or abstract alone is not equivalent; an accessible publisher record qualifies only when it exposes the necessary full design and contribution content.
- `M4_CURRENT_PROGRAM_CROSSCHECK`: portfolio-level only. The M3-supported portfolio was reconciled with a current candidate-bound official programme or group description, with conflicts exposed. Never assign M4 to an individual paper.

`M1` is intentionally unused in this established scale. Do not renumber or reinterpret older M0/M2/M3/M4 audit snapshots.

Also record `reviewActor` independently for every paper-level review: `machine_rule`, `model_manual`, or `human_manual`. `model_manual` means the agent deliberately inspected the cited record; it is not a human review. Never set or describe `human_manual` unless an actual human reviewed the evidence. Review depth describes the evidence inspected, while `reviewActor` describes who or what performed that inspection. Record `reviewedAt` and a page, section, paragraph, table or record locator showing where the decisive evidence was inspected. `machine_rule` may pair only with M0; M2/M3 require `model_manual` or `human_manual`.

For each paper, retain explicit evidence for the following features rather than only the final code:

- patient cohort, clinical sample, treatment, trial, RWE or other clinical anchor;
- cell, organoid, animal, immune, biochemical or molecular-perturbation work;
- genomics, transcriptomics, single-cell, spatial, proteomic or other omics generation/analysis;
- applied bioinformatics used to answer the cancer question, kept distinct from omics generation/analysis and from theoretical method development;
- algorithm, statistical framework, software or benchmark as a possible primary contribution;
- mechanism, biomarker, outcome, efficacy, safety, toxicity or workflow endpoint;
- functional, orthogonal, independent-cohort, prospective or interventional validation;
- the exact candidate-bound author role and its source.

Tool names and keywords are leads, not decisions. R/Python, machine learning, sequencing or routine statistics do not establish `RM-B` or `RM-EB`; a patient sample or trial does not establish `TR2` or `TR3`; coexistence of wet and computational terms does not establish that both are indispensable to the main conclusion.

Deliberate evidence verification is mandatory for every `O3C`/`O2C`/`O2S` paper that triggers a supervisor-level portfolio label or score, and for every borderline `RM-EB`, `TR2`, `TR3`, pure-type or dominant-type claim. Use `M3` when the claim requires details absent from the abstract, and complete the portfolio-level M4 cross-check before presenting the portfolio as the person's confirmed current programme. If access prevents the required review, preserve the provisional label and access warning.

An unprefixed `MTG#` is allowed only when all of the following hold: at least one strong-role paper exists; the uniquely derived evidence-completeness score is at least 7; `searchStatus=bounded_complete`; every included strong-role paper received at least M2 paper-by-paper review; every validator-derived score/portfolio trigger received M3 review; all borderline `RM-EB`, `TR2`, `TR3`, pure and dominant claims are resolved at the depth their design requires; M4 is completed with a current official programme source and no blocking conflict remains. Confirmed pure programmes require every strong-role denominator paper at M3; confirmed dominant programmes require every included denominator paper at sufficient M3 design depth. Use `pMTG#` when a numerical grade remains defensible but any confirmation gate is unmet; use `incomplete` when uncertainty prevents even a defensible provisional grade. The reviewer may be `model_manual` or `human_manual`, but the report must preserve the actor truthfully. M4 never upgrades an individual paper or cures an unresolved conflict.

## 3. Paper-level method codes

Assign one primary method code to each eligible paper after reading at least its abstract and methods description when available. Also store controlled `methodFamilyTags` and `omicsModalities`. `methodFamilyTags` may contain `EXPERIMENTAL`, `BIOINFORMATICS`, `OMICS`, `THEORETICAL_METHOD`, and `CLINICAL_OUTCOMES`; `omicsModalities` may contain `GENOMICS`, `TRANSCRIPTOMICS`, `EPIGENOMICS`, `PROTEOMICS`, `METABOLOMICS`, `SINGLE_CELL`, `SPATIAL`, `MULTI_OMICS`, and `OTHER_OMICS`. These fields preserve the difference between applied bioinformatics, generation/analysis of omics data, theoretical method development, wet experiments, and pure clinical-outcome work; the primary code records what drives the main conclusion.

| Code | Meaning | Boundary |
|---|---|---|
| `RM-E` | experimental/basic-mechanistic | cell, organoid, animal, molecular perturbation, biochemistry or immune experiments drive the main conclusion; routine statistics or sequencing QC do not make it bioinformatics |
| `RM-B` | applied bioinformatics/omics | genomics, transcriptomics, single-cell, spatial, multi-omics or computational analysis answers a specific cancer question, without substantial functional experimental validation |
| `RM-EB` | within-paper experimental-computational integration | omics/computational discovery and functional wet-lab validation are both indispensable to the paper's main conclusion |
| `RM-M` | theoretical/computational methods | the main contribution is an algorithm, statistical framework, software, model or benchmark; cancer data are mainly a test case |
| `RM-C` | pure clinical research | efficacy, safety, survival, toxicity, workflow, routine cohort, screening or real-world outcome is the main question, without a molecular/omics/functional bridge |

For consistency: `RM-E` must include only `EXPERIMENTAL`; `RM-B` must include `BIOINFORMATICS` and/or `OMICS` but neither `EXPERIMENTAL`, `THEORETICAL_METHOD` nor `CLINICAL_OUTCOMES`; `RM-EB` must include `EXPERIMENTAL` plus `BIOINFORMATICS` and/or `OMICS`, but neither `THEORETICAL_METHOD` nor `CLINICAL_OUTCOMES`; `RM-M` must include `THEORETICAL_METHOD` and may also use `BIOINFORMATICS`/`OMICS` for method evaluation; `RM-C` must contain exactly `CLINICAL_OUTCOMES`. `OMICS` requires at least one modality, and modalities are forbidden without `OMICS`. `RM-C` and `CLIN_ONLY` are equivalent boundaries: each requires the other. Using R/Python, machine learning or sequencing does not by itself establish `RM-B` or `RM-EB`; the analysis must carry a principal scientific conclusion.

## 4. Clinical-translation codes

Assign this axis independently of the method code and retain a structured `translationEvidence` object. It contains booleans for `hasClinicalAnchor`, `hasMolecularOmicsOrMechanisticBridge`, `hasIndependentOrOrthogonalValidation`, `hasProspectiveOrInterventionalLink`, `hasFunctionalValidation`, and `hasClinicalLevelValidation`.

| Code | Meaning |
|---|---|
| `TR0` | no real clinical anchor; basic discovery or only a speculative clinical statement |
| `TR1` | patient samples or clinical data are connected to a molecular, omics, biomarker or mechanistic anchor, but the work is descriptive or a single-cohort association without adequate functional/independent validation |
| `TR2` | a defined diagnostic, stratification, response, resistance, recurrence or monitoring problem is linked to a molecular/omics/biomarker layer and independent or orthogonal validation |
| `TR3` | a prospective or interventional trial-linked clinical question, patient material/outcome, molecular mechanism or biomarker layer, functional/orthogonal validation and clinical-level validation form a closed translational loop |
| `CLIN_ONLY` | pure clinical outcome/efficacy/safety/workflow research without a mechanistic, biomarker, omics or functional bridge |

Tag `CLIN_ONLY` papers more specifically as `CO-RWE`, `CO-TRIAL`, `CO-OBS`, `CO-EPID` or `CO-PROC`. These papers can demonstrate access to patients, cohorts and clinical implementation, but they do not automatically count as translational-mechanistic research. `TR1` requires a clinical anchor plus a molecular/omics/biomarker/mechanistic bridge; `TR2` additionally requires independent or orthogonal validation; `TR3` additionally requires prospective/interventional linkage, functional validation, and clinical-level validation. `CLIN_ONLY` requires a clinical anchor and no such bridge.

Do not call a biomarker predictive without a treatment-interaction design or equivalent evidence. A single-cohort survival association with a molecular/omics/biomarker anchor is normally `TR1`, not `TR2/TR3`; the same association without such a bridge is `CLIN_ONLY`. A trial that reports only efficacy/safety remains `CLIN_ONLY`; a trial-linked molecular or functional correlative programme may qualify for `TR2`, and only a verified prospective/interventional trial-linked closed loop may qualify for `TR3`. Automatic abstract coding may emit only a provisional `TR3` candidate label until the full design and correlative programme are checked. Before M3 full-text design verification, score an automatic `TR3` candidate no higher than `TR2`; it cannot by itself create automatic MTG1-level translation points.

## 5. Supervisor-level portfolio codes

Allow multiple codes when warranted:

- `RP-E-PURE`: experimental/basic-mechanistic only.
- `RP-B-PURE`: applied bioinformatics/omics only.
- `RP-EB-INTRA`: repeated within-paper experimental-computational integration.
- `RP-EB-SPLIT`: a split portfolio containing independently experimental papers and independently bioinformatics/omics papers. This counts as a genuine mixed programme even if no single paper combines both.
- `RP-M-PURE`: theoretical method/algorithm/software only.
- `RP-TRANS`: clinically anchored molecular/mechanistic translation.
- `RP-C-PURE`: pure clinical/RWE/trial/outcome programme.
- `RP-C-DOMINANT`: predominantly pure clinical/RWE/trial/outcome work, but not sufficiently uniform to call pure.

Use all eligible `O3C`/`O2C`/`O2S` papers in the time window to test purity; do not cherry-pick five favourable examples. A confirmed pure type requires at least five strong-role original papers, all of the same primary method type. Otherwise label it provisional or dominant, not pure.

Confirmation thresholds:

- `RP-EB-INTRA`: at least two strong-role `RM-EB` papers; one is provisional.
- `RP-EB-SPLIT`: at least two strong-role `RM-E` and two strong-role `RM-B`; one of each is provisional.
- `RP-TRANS`: at least two strong-role `TR2/TR3`; one is provisional, and a strong translational programme has at least two `TR3` papers.
- a dominant type requires at least 70% of role-weighted eligible evidence. Compute the denominator across all eligible candidate-bound papers using the `O3C`/`O2C`/`O2S`/`O1L`/`O1F`/`O0` weights above; report numerator, denominator and ratio.
- `RP-C-PURE` follows the same purity rule as every other pure code: at least five strong-role original papers, all `RM-C + CLIN_ONLY`, with no stable `TR2/TR3` line. A clinical share of at least 70% but less than 100% is `RP-C-DOMINANT`, not `RP-C-PURE`.

If an official current programme page conflicts with the publication portfolio, show the conflict. Do not use old papers to overwrite the current declared direction.

## 6. Method-translation fit grade

The `MTG` grade measures the combination defined by the selected training-fit profile, not scientific prestige. Keep it beside, never inside, the existing A/B/C tier.

### Method integration, 0–30

- 30: at least two strong-role `RM-EB` papers.
- 26: one strong-role `RM-EB` plus a confirmed split experimental/omics portfolio.
- 22: at least two strong-role `RM-E` and two strong-role `RM-B` papers.
- 16: one strong-role `RM-EB`, or at least one strong-role `RM-E` plus one strong-role `RM-B` paper.
- 10: at least two strong-role `RM-E` papers plus at least one candidate-led `RM-B`/`RM-EB` paper, or the mirror image with two strong-role `RM-B` papers plus one candidate-led `RM-E`/`RM-EB` paper.
- 6: at least one strong-role paper exists and the strong-role method set is exclusively `RM-E` or exclusively `RM-B`.
- 0: purely theoretical methods or pure clinical outcomes.

### Clinical-translation depth, 0–30

- 30: at least two strong-role `TR3` papers.
- 25: one strong-role effective `TR3` plus at least one strong-role effective `TR2`.
- 20: at least two strong-role effective `TR2/TR3` papers.
- 14: one strong-role effective `TR2/TR3` paper.
- 6: at least two strong-role `TR1` papers.
- 0: `TR0` only, or pure clinical/RWE/routine-trial evidence only.

### Research ownership, 0–20

- 20: at least five strong-role papers.
- 16: three or four.
- 12: two.
- 6: one.
- 0: none.

### Recent continuity, 0–10

- 10: at least five candidate-led papers in the five-year window.
- 8: three or four.
- 5: one or two candidate-led papers in five years plus `M4_CURRENT_PROGRAM_CROSSCHECK` with `result=consistent`.
- 2: the higher conditions are unmet and candidate-led papers from years six to eight outnumber those in the most recent five years.
- 0: no confirmed recent line.

### Evidence completeness, 0–10

- 10: at least one strong-role paper exists, M4 is complete with `result=consistent`, no material unresolved conflict remains, and every strong-role paper is verified at M3 full-text/design depth.
- 7: at least one strong-role paper exists, no material unresolved conflict remains and every strong-role paper is at least M2, but the 10-point gate is not met.
- 3: a defensible provisional grade remains, but one or more included papers are still M0 or strong-role evidence has not reached M2.
- 0: no defensible grade; use `incomplete` with no numerical scores rather than a graded record.

The validator computes the unique highest applicable value for every component. A lower self-selected score is invalid. It also derives `scoreTrigger` by removing each paper and recomputing method integration, clinical translation, ownership and continuity, and derives `portfolioTrigger` by recomputing portfolio codes. These booleans are audit outputs, not user-controlled exemptions from M3 review.

| Grade | Score | Interpretation |
|---|---:|---|
| `MTG1` | 80–100 | strong experimental-omics integration with a true clinical-translational loop |
| `MTG2` | 65–79 | strong combined programme or clinically anchored applied omics/partial mechanistic translation |
| `MTG3` | 45–64 | relevant science but primarily a single experimental or applied-computational mode, with limited clinical translation |
| `MTG4` | 0–44 | primarily theoretical methods or pure clinical/RWE/outcome work; supplementary for the target training profile |
| `pMTG#` | any grade not yet meeting the required paper-depth, search-completeness, actor-provenance and programme-cross-check rules; one or two strong-role papers are additionally low-confidence | provisional grade; do not present it as a confirmed MTG grade |
| `MTG-U` | a complete, non-truncated eight-year search found zero usable candidate-bound eligible oncology original papers | ungraded because no classifiable portfolio was publicly identifiable |

`MTG1` or `pMTG1` additionally requires a method-integration score of at least 22, at least one M3-verified strong-role `TR3` paper, and a second M3-verified strong-role `TR2` or `TR3` paper. An unprefixed `MTG1` must also meet every confirmed-grade gate and M4. A numerical score of 80 or more without this floor is capped at `MTG2` or `pMTG2`; preserve the raw total and record `gradeAdjustment={applied:true, from:"MTG1", to:"MTG2", reason:"..."}` so the intentional exception to the ordinary 65–79 MTG2 band is auditable. `MTG-U` is restricted to the zero-paper condition defined in Section 2; the presence of usable machine-only evidence produces `pMTG#`, while a blocking conflict produces `incomplete`.

A high-quality pure-basic laboratory may correctly be `A + MTG3`; a clinical multi-omics group without functional validation may be `A + MTG2`; a pure RWE professor may be `B + MTG4 + CO-RWE`. A no-capacity reply may coexist as `outreachControl.status=hold_no_capacity`; it does not freeze or replace the scientific audit.

## 7. Storage and reporting

Until the base case schema explicitly defines `researchMethodAudit`, do not add an unvalidated field to `records.json`. Preserve the base case as a historical snapshot and write `data/research-method-audit.json`, with its verification date inside the file, plus the generated report `08-RESEARCH-METHOD-TRANSLATION-AUDIT.md`. The supplemental JSON must contain:

- `schemaVersion`, `caseAsOf`, `generatedAt`, `searchScope`, and `rosterReconciliation` with retained A/B/C IDs, audited IDs and an empty missing-ID list;
- for every retained A/B/C candidate: stable ID; Chinese department, current role and research direction; `scientificAuditStatus`; separate `outreachControl`; exact search date and five/eight-year window; reproducible search ledger and retry/truncation state;
- every included or explicitly excluded retrieved paper's stable work ID, inclusion decision/reason, identity-binding evidence, role code/basis, method code, translation code, clinical-only subtype, `reviewDepth`, `reviewActor`, score/portfolio-trigger flags, evidence features, source URL/ID and conflicts;
- complete candidate-led and strong-role counts, portfolio codes, role-weighted dominance calculation, five component scores, total, grade, confidence and M4 current-programme cross-check;
- identity, authorship, access, search, method, translation and current-direction conflicts, plus a separate outreach-held table whose reason never changes the original A/B/C tier.

Use these exact core field names so the supplemental validator can reconcile the audit:

```json
{
  "schemaVersion": "research-method-audit-1.1",
  "caseAsOf": "YYYY-MM-DD",
  "generatedAt": "YYYY-MM-DD",
  "searchScope": {"coverageClaim": "bounded_public_search", "defaultWindowYears": 5, "extendedWindowYears": 8},
  "rosterReconciliation": {
    "retainedAbcCandidateIds": [],
    "auditedCandidateIds": [],
    "missingCandidateIds": []
  },
  "candidates": [{
    "candidateId": "stable-id",
    "name": "Name",
    "priorityTier": "A",
    "departmentZh": "中文院系或课题组",
    "currentRoleZh": "中文当前任职",
    "researchDirectionZh": "中文研究方向",
    "scientificAuditStatus": "confirmed|provisional|ungraded|incomplete",
    "opportunityStatus": "copied exactly from records.json",
    "outreachControl": {"status": "active|hold_no_capacity|hold_user", "reason": "", "recordedAt": "", "scope": "", "recheckCondition": ""},
    "searchDate": "YYYY-MM-DD",
    "windowYears": 5,
    "windowStart": "YYYY-MM-DD",
    "windowEnd": "YYYY-MM-DD",
    "extensionReason": null,
    "searchStatus": "bounded_complete|search_incomplete",
    "searchPlan": [{"queryId": "stable-query-id", "sourceKey": "pubmed", "source": "PubMed", "query": "exact query"}],
    "searchLedger": [{
      "queryId": "stable-query-id",
      "source": "database or official list",
      "query": "exact query",
      "searchStage": "BASE_5Y|EXTENDED_8Y",
      "windowStart": "YYYY-MM-DD",
      "windowEnd": "YYYY-MM-DD",
      "searchedAt": "YYYY-MM-DD",
      "pagesOrCursorsChecked": "all pages / last cursor",
      "resultCount": 0,
      "truncated": false,
      "accessStatus": "complete|partial|blocked",
      "retryNotes": ""
    }],
    "searchReconciliation": {"rawResults": 0, "duplicateRecords": 0, "uniqueWorks": 0, "includedWorks": 0, "excludedWorks": 0},
    "papers": [{
      "workId": "doi:...",
      "title": "...",
      "publicationDate": "YYYY-MM-DD",
      "inclusionDecision": "included|excluded",
      "exclusionReason": "",
      "identityEvidence": ["affiliation", "ORCID or second discriminator"],
      "authorRole": "O3C|O2C|O2S|O1L|O1F|O0",
      "roleBasis": "...",
      "correspondingStatus": "CORRESPONDING|CO_CORRESPONDING|NOT_CORRESPONDING|UNVERIFIED",
      "seniorStatus": "EXPLICIT_SENIOR|CO_SENIOR|LAST_AUTHOR_ONLY|NOT_SENIOR|UNVERIFIED",
      "authorOrderStatus": "FIRST|CO_FIRST|LAST|PENULTIMATE|MIDDLE|CONSORTIUM|OTHER",
      "authorshipEvidenceSourceIds": [],
      "authorshipEvidenceLocator": "correspondence/contribution statement locator",
      "methodCode": "RM-E|RM-B|RM-EB|RM-M|RM-C",
      "methodFamilyTags": ["EXPERIMENTAL|BIOINFORMATICS|OMICS|THEORETICAL_METHOD|CLINICAL_OUTCOMES"],
      "omicsModalities": ["GENOMICS|TRANSCRIPTOMICS|EPIGENOMICS|PROTEOMICS|METABOLOMICS|SINGLE_CELL|SPATIAL|MULTI_OMICS|OTHER_OMICS"],
      "translationCode": "TR0|TR1|TR2|TR3|CLIN_ONLY",
      "translationEvidence": {"hasClinicalAnchor": false, "hasMolecularOmicsOrMechanisticBridge": false, "hasIndependentOrOrthogonalValidation": false, "hasProspectiveOrInterventionalLink": false, "hasFunctionalValidation": false, "hasClinicalLevelValidation": false},
      "clinicalOnlySubtype": null,
      "reviewDepth": "M0_MACHINE_ABSTRACT|M2_HUMAN_ABSTRACT|M3_FULL_TEXT_DESIGN",
      "reviewActor": "machine_rule|model_manual|human_manual",
      "reviewedAt": "YYYY-MM-DD",
      "reviewLocator": "page, section, paragraph, table or record locator",
      "scoreTrigger": false,
      "portfolioTrigger": false,
      "evidenceFeatures": {"clinicalAnchor": "...", "experimentalWork": "...", "omicsWork": "...", "bioinformaticsWork": "...", "theoreticalMethodContribution": "...", "endpoint": "...", "validation": "..."},
      "sourceIds": [],
      "sourceUrls": [],
      "conflicts": []
    }],
    "portfolioCounts": {"eligible": 0, "candidateLed": 0, "strongRole": 0},
    "portfolioCodes": [],
    "dominance": {"methodCode": null, "weightedNumerator": 0, "weightedDenominator": 0, "ratio": 0},
    "scores": {
      "methodIntegration": 0,
      "clinicalTranslation": 0,
      "researchOwnership": 0,
      "recentContinuity": 0,
      "evidenceCompleteness": 0,
      "total": 0
    },
    "scoreBasis": {
      "methodIntegration": "paper IDs and threshold",
      "clinicalTranslation": "paper IDs and threshold",
      "researchOwnership": "role counts and threshold",
      "recentContinuity": "five/eight-year counts and threshold",
      "evidenceCompleteness": "review-depth and conflict basis"
    },
    "grade": "MTG1|MTG2|MTG3|MTG4|pMTG1|pMTG2|pMTG3|pMTG4|MTG-U or null for incomplete",
    "gradeAdjustment": {"applied": false, "from": "", "to": "", "reason": ""},
    "confidence": "high|medium|low",
    "currentProgramCrossCheck": {"status": "M4_CURRENT_PROGRAM_CROSSCHECK|not_completed", "result": "consistent|mixed|conflicting|not_assessed", "sourceIds": [], "summary": ""},
    "conflicts": [{"type": "...", "summary": "...", "material": true, "resolved": false, "impact": "NONBLOCKING_PROVISIONAL|BLOCKS_GRADE"}]
  }]
}
```

For an excluded retrieved paper, retain `workId`, title/date when known, `inclusionDecision=excluded`, and `exclusionReason`; paper-level method/review fields are required only for included papers. `priorityTier` must match `records.json`. `confidence` is required for every status. `ungraded` and `incomplete` use no scores; `incomplete` stores JSON `null` in `grade`. The validator recomputes the author-role code, method/translation compatibility, role-weighted dominance values, five-year candidate-led count, all five component scores, score/portfolio triggers, MTG band, portfolio/purity labels, MTG1 floor and roster coverage rather than trusting handwritten totals.

Run `scripts/validate_method_audit.py --case-dir <case-directory>` before rendering and again with `--strict` after rendering. Generate the report only with `scripts/render_method_audit.py --case-dir <case-directory>`. A full run is not complete merely because the base `validate_case.py --strict` succeeds; both strict validators must succeed, and roster reconciliation must show every retained A/B/C candidate exactly once. An `incomplete` record is allowed only after the required search ledger and at least one documented retry expose the blocking cause; it is a visible unresolved result, not permission to skip the audit.

Machine-assisted abstract coding is triage, not final proof. Mark it as provisional until the required evidence-depth checks resolve borderline papers and all purity claims. The rendered report must explain that `MTG` and A/B/C measure different things.

The rendered report must also state, for the retained A/B/C roster, how many supervisors are confirmed, provisional, ungraded, or incomplete; how many eligible papers were coded; how many papers reached M0, M2 and M3; how many supervisor portfolios completed M4; and which identity, authorship, full-text-access, search, method, translation, or current-direction conflicts remain unresolved. M4 must never be counted as a paper review depth.
