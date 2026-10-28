# CV-aligned oncology scope

## Purpose and privacy

This reference defines reusable logic for a broad, applicant-aligned oncology search. Use `case.topicProfile: cv_aligned_oncology` only when the user explicitly selects it or current task inputs support a broader scope than `lung_cancer`. Missing profile in an existing case means the legacy narrow profile.

Keep every applicant-specific filename, file hash, identifier, contact detail, project title, manuscript status and contribution claim in the case workspace. Never copy those details into the installed skill. Record only the accepted search axes and bounded alignment/gap summaries in case outputs. Applicant statements configure discovery; they are not independent proof of publication status, contribution, technical proficiency or supervisor fit.

The engineering/computer-science/standalone-AI/data institutional exclusion remains unchanged in both profiles. Apply `candidate-exclusions.md` after checking current person-specific official research evidence, and preserve explicit case-specific user overrides.

## Applicant evidence boundaries

- Use the current CV or background supplied for the task; do not rely on a stored applicant snapshot.
- Translate education, research themes, disease areas and methods into search cues only when the source actually supports them.
- Treat coauthorship, equal-contribution, conference participation, manuscript status and project leadership as separate claims. Do not infer one from another.
- `submitted`, `under review`, `in preparation` and `ready to submit` are not accepted or published. A heading labelled preprints does not prove that a public preprint exists.
- Method names and software in a CV do not establish independent execution, original algorithm development, wet-lab proficiency, clinical licensing, access to samples/data or supervision eligibility.
- User-reported experience may support a bounded search preference, but its methods, duration and independence remain unspecified unless the current evidence states them.

## Discovery preference bands and approved axes

These bands describe search preference, not admissions/recruitment, T-code evidence quality or A–D readiness. A well-supported L2 supervisor may be more appropriate than a weak L1 lead. Record actual disease, band, axis and transfer/training gaps in `records[].notes` and the case's scope/limitations; do not add unvalidated record fields.

### Disease-breadth priority modifier

Consider disease breadth before using tumour site as a preference. First establish from current person-specific evidence whether the programme is limited to one or a few named tumour types, or instead spans multiple tumours/pan-cancer cohorts or a broadly applicable cancer mechanism.

- For a programme limited to one or a few tumour types, give priority to thoracic malignancies; within thoracic oncology, lung cancer/NSCLC/SCLC remains the leading preference, followed by oesophageal cancer and other verified thoracic tumours such as pleural mesothelioma or thymic/mediastinal malignancy.
- Do not let a narrow non-thoracic programme outrank an otherwise comparable narrow thoracic programme merely because both satisfy an L2 method axis.
- Do not mechanically demote a strong pan-cancer, multi-tumour or general cancer-mechanism programme for lacking a thoracic-exclusive label. Judge its verified scientific axis, transfer value, supervision and route separately.
- Apply this modifier only after the institutional gate, persistent research exclusions and person-specific oncology-relevance audit. It is a ranking preference, not evidence of fit, independence, supervision eligibility, recruitment or funding.
- Record the bounded result in `records[].notes`, for example `Disease-breadth priority: narrow_thoracic`, `broad_multi_tumour`, or `narrow_non_thoracic`, with the verified diseases and source IDs. Do not create an unvalidated schema field in a standard case.

### L1 — directly aligned, lung/thoracic first

- Lung cancer/NSCLC/SCLC translational oncology; neoadjuvant or perioperative chemoimmunotherapy, response/resistance and clinically grounded precision treatment.
- Lung tumour immune microenvironment, immune escape, immunotherapy biomarkers, genotype-dependent vulnerabilities and tumour multi-omics.
- STK11/LKB1, KEAP1/NFE2L2 and SMARCA4 are useful discovery terms, not mandatory requirements for every eligible supervisor.
- Other lung clinical/pathology research can remain eligible, but surgery, radiotherapy physics or device-focused work must show a documented applicant-side bridge and training gap rather than being ranked highly just for the disease name.

### L2 — priority extensions across adult solid tumours/pan-cancer

Require a current candidate-bound cancer research line in at least one approved axis:

For each person, verify the actual tumour/disease or cancer-risk endpoint, cancer-specific question and current role from official person/lab/project evidence, cross-checked with primary literature. An accepted axis describes what to search; its method label is not evidence that a particular supervisor studies cancer. Follow the oncology-relevance audit in `candidate-exclusions.md` and retain it in `records[].notes`.

1. **Tumour immunity/microenvironment:** immune escape, immune-cell states, treatment-associated immune response, cancer immunotherapy and resistance.
2. **Cancer immunometabolism:** tumour/immune metabolic interactions and metabolite-linked treatment response, not general metabolism without cancer relevance.
3. **Molecular precision oncology:** somatic alterations, tumour-cell vulnerabilities, molecular subtyping, target/therapy-response relationships and patient-linked drug-response research.
4. **Cancer multi-omics/translational bioinformatics:** genomic/transcriptomic/single-cell integration and clinically meaningful tumour heterogeneity or biomarkers; spatial/proteomic/functional validation may be a training extension, not a claimed existing skill.
5. **Clinical/translational biomarkers and treatment-outcome research:** patient cohorts, trial-linked correlative analyses, response/resistance, evidence-calibrated biomarker validation and clinically meaningful endpoints.
6. **Cancer translational genetics/genomics:** connect tumour somatic alterations, inherited susceptibility where cancer-linked, gene regulation or functional genomic findings to tumour phenotypes, clinical biomarkers, vulnerabilities or therapeutic hypotheses. Include translational genetics, translational genomics, cancer genetics and functional genomics as discovery terms; do not require one specific genotype or a lung-cancer cohort.
7. **Cancer molecular/cell biology:** current cancer-linked mechanisms in DNA replication/repair and genome stability, chromatin/epigenetic regulation, RNA biology/epitranscriptomics, cell-cycle control, signal transduction, programmed cell death and molecular interactions. Mechanistic or experimental labs may qualify before immediate clinical translation when their current research explicitly addresses tumour initiation/progression, response/resistance or treatment vulnerability.

These axes may be studied in esophageal or other upper-GI cancers, colorectal, breast, melanoma or other solid tumours, or pan-cancer cohorts. No lung project is mandatory in this profile. Cancer multi-omics includes genomic, transcriptomic, epigenomic, proteomic, metabolomic, single-cell and spatial integration when the official work establishes a cancer question. Another tumour type or a molecular-method label alone is not enough: the source must establish an approved research question, and the report must explain disease/method transfer rather than claiming prior expertise in every cancer or assay. Pure synthetic/materials engineering, device development or algorithm performance with a token oncology dataset remains outside the institutional/scientific boundary.

### L3 — bounded secondary/bridge searches

- Medically/public-health anchored cancer genetic epidemiology, immune-phenotype/metabolite Mendelian randomization, prospective cancer-risk cohorts and mediation/causal-inference research. Broader cancer epidemiology needs a documented applicant-side research/method bridge, not generic population analytics.
- Inflammatory lung disease–lung-cancer overlap when the current group explicitly studies the cancer connection. General ILD, infection or respiratory immunology with no cancer link is not an automatic extension.
- Medically based clinical data science/biostatistics or multi-omics platforms with an explicit current cancer project and a credible doctoral route. A pure standalone data faculty remains excluded.

Paediatric oncology and haematologic malignancies are default exclusions only when they are the main or predominant focus of the person's overall current research programme; their co-equal parallel, secondary or collaborative presence does not itself exclude an otherwise eligible candidate, and unresolved dominance is retained with a caution. Nuclear medicine and radiomics/core clinical or molecular tumour imaging remain excluded when core or explicitly parallel, under `candidate-exclusions.md`. Other unlisted fields such as non-cancer immunology, infectious disease, neuroscience, generic metabolism, general AI/ML, robotics, materials and non-medical data analytics are not blanket extensions of this CV profile. An approved-axis bridge does not waive an exclusion whose stated threshold is met; a later explicit user override can do so. Label any accepted transfer and do not silently broaden the default.

## Query expansion

Inspect actual faculty/department structure first, then run lung and extension families in each eligible school/system:

```text
site:[institution] (lung cancer OR NSCLC) (neoadjuvant OR chemoimmunotherapy OR biomarker OR resistance)
site:[institution] (cancer OR tumour OR tumor) (immunology OR immune escape OR microenvironment OR immunometabolism)
site:[institution] (precision oncology OR translational oncology) (genomics OR transcriptomics OR multiomics OR single-cell)
site:[institution] (cancer OR tumour OR tumor) (translational genetics OR translational genomics OR cancer genetics OR functional genomics)
site:[institution] (cancer OR tumour OR tumor) (molecular biology OR DNA repair OR replication stress OR epigenetics OR RNA modification OR cell cycle)
site:[institution] (cancer OR tumour OR tumor) (multiomics OR multi-omics OR proteomics OR metabolomics OR spatial transcriptomics)
site:[institution] (cancer) (predictive biomarker OR treatment response OR clinical cohort OR trial correlative)
site:[institution] (esophageal cancer OR oesophageal cancer) (metabolite OR immune OR genetic susceptibility)
site:[institution] (cancer epidemiology OR cancer risk) (Mendelian randomization OR prospective cohort OR mediation)
```

Use local-language and Chinese equivalents tied to the person's actual disease/axis. For literature expansion use the verified author identity plus the accepted cancer/axis terms, not only lung MeSH. Search terms are leads, never final evidence.

## Match and skill-gap discipline

- Keep supervisor fit, applicant experience, formal eligibility, vacancy and funding separate. Do not infer access to patient data/samples, platforms or funding.
- A neutral note may read: `CV scope: L2; axis: tumour immunometabolism; disease: colorectal cancer; bridge: documented oncology/multi-omics experience; gap: wet-lab validation not established by the supplied evidence.` This is analyst-derived research metadata, not outreach prose or a promise of proficiency.
- Do not infer independent MR/mediation execution, original AI development, trial design, patient recruitment, organoid culture, animal work, CRISPR or flow cytometry solely from paper titles/coauthorship. A bounded self-report supports only what it explicitly states. Absence from the supplied evidence means not established, not that the applicant cannot learn or has never done it.
- Wet-lab-heavy labs may qualify when the research question is aligned and an appropriate training/co-supervision route is documented or explicitly left for inquiry. State the gap instead of silently claiming readiness or automatically excluding all experimental labs.
- Keep adult cancer multi-omics, digital pathology and spatial/imaging mass cytometry eligible when both gates pass; an imaging-word match alone is not a radiomics programme. Use the method/programme distinctions in `candidate-exclusions.md`.
- Retain official source-quality, independence, supervision, doctoral-route and A-tier depth requirements, while auditing opportunity status on its separate axis. Lack of a verified opening, a closed call or an `unverified` recruitment state never removes or downgrades an otherwise qualified record. Broad-profile direct evidence needs an explicit cancer/oncology anchor, but a keyword hit alone does not establish an approved axis or current independent line.
- Do not rewrite the user's existing roster or historical case merely because this configuration changed. Apply it to new searches or an explicitly requested scope expansion, preserving the narrower case as provenance.
