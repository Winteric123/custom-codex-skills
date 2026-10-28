# Doctoral application-materials audit

Use this reference when verifying applications or producing a research-only handoff for later writing. It defines required-material facts; it does not authorize drafting letters, contacting supervisors, requesting recommendations or submitting applications.

## Scope and sources

When the user requests a minimal initial enquiry, limit the immediate question to whether a PhD programme or accessible doctoral route exists. Do not require detailed programme-type or scholarship/funding questions at that stage. A full research audit may collect available official facts without asking the user to settle them; the detailed materials checklist is used when preparing the relevant application/writing task. Unknown scholarship or programme subtype is not a reason to block a simple initial enquiry. Keep programme existence, supervisor eligibility and vacancies separate.

Audit every retained A/B/C candidate and every viable `opportunities[]` route. Keep programme admission, PI/lab pre-contact, fellowship/funding and employment-style doctoral applications distinct. Skip historical/closed routes as current application routes, retaining their history where relevant.

Open current official admissions checklists, doctoral rules, application guidance, named vacancies and relevant official PI/lab contact instructions. A generic programme can establish programme documents, but not a named supervisor's current availability. Use the exact document name used by the route. Motivation letter, personal statement, statement of purpose, cover letter, research proposal and CV are not automatically interchangeable.

## Minimum checklist

For every viable route, explicitly check these four kinds even when information is missing:

| Kind | What to verify |
|---|---|
| `motivation_letter` | Whether a motivation letter is required, optional or conditional; if the official label is personal statement/SOP, record that exact label and a separate relevant entry when appropriate; word/page limits, template, content prompts and language |
| `supervisor_enquiry` | Whether prior PI contact is mandatory, recommended, optional or discouraged; whether a supervisor agreement, acceptance letter or signature is required; separate pre-contact from a document uploaded in the application |
| `recommendation_letters` | Whether letters or only referee contact details are required; quantity; eligible referees; applicant upload versus confidential referee submission; separate reference deadline |
| `research_proposal` | Whether a proposal/project outline is required at initial application or later; page/word limits, template, sections, format and submission method |

Add `personal_statement`, `cover_letter`, `cv`, `transcripts`, `degree_certificates`, `language_test`, `writing_sample` and `other` where applicable. Check official certification/translation rules and provisional/final documents when relevant. For recommendation letters, an applicant may provide referee details while referees submit letters later; describe both stages accurately. For PI contact, record the precise instruction in `summary`; `optional` does not erase a source saying unsolicited contact is discouraged.

## Evidence and missing states

Allowed `requirementStatus`: `required`, `optional`, `not_required`, `conditional`, `not_public`, `unverified`.

- Assert `required`, `optional` or `conditional` only with current official evidence for the route; explain each condition.
- Use `not_required` only when an official source explicitly states this or waives the document. A document absent from a visible checklist is not enough to conclude it is unnecessary.
- Use `not_public` when the reviewed public instructions do not state the rule; use `unverified` for inaccessible, conflicting or not-yet-checked rules. A login wall must be recorded as an access limitation.
- Do not turn `direct_enquiry_recommended` (analyst opportunity advice) into an official requirement to send a cold email. An email address proves a channel, not a contact policy.
- Record the actual check date and applicable application cycle. A later writing workflow rechecks unstable requirements and uses only the documents the actual route requests.

## Structured storage

Keep schema `1.2` and existing summary fields. Add optional `applicationReadiness.documentRequirements` for traceable item/route rows:

```json
{
  "routeId": "candidate-programme-route",
  "materialType": "recommendation_letters",
  "requirementStatus": "unverified",
  "submissionStage": "not_stated",
  "summary": "unverified: official referee/letter requirement still needs checking",
  "formatAndLength": "unverified",
  "quantity": null,
  "submitter": "not_stated",
  "submissionMethod": "unverified",
  "checkedAt": "YYYY-MM-DD",
  "sourceIds": []
}
```

- `routeId` must match that candidate's `opportunities[].id`. Do not splice rules from a different programme.
- `materialType`: one of the four minimum kinds or `personal_statement`, `cover_letter`, `cv`, `transcripts`, `degree_certificates`, `language_test`, `writing_sample`, `other`.
- `submissionStage`: `pre_contact`, `initial_application`, `after_shortlisting`, `after_offer`, `not_stated`.
- `quantity`: positive integer when official count is explicit, otherwise `null`. Zero is not a missing marker.
- `submitter`: `applicant`, `referee`, `not_stated`. `submissionMethod` records the official portal, direct referee link, email, signed consent route or missing state.
- `summary` preserves the official name, conditions and scope. `formatAndLength` records limits/template/file format or an explicit missing state. Reference deadlines or cycle differences can be retained here with source IDs and in `applicationWindow`/route contact policy; do not substitute the programme deadline for a referee deadline.
- `checkedAt`: actual ISO date no later than `case.asOf`; cited sources must not have been accessed later. Positive rule claims need current official candidate- or school-bound evidence with the appropriate rule/admissions/recruitment/contact domains. Missing-state rows may have an empty source list.

Keep `requiredDocuments`, `contactProtocol`, `proposalRequirement` and `applicationClaimSourceIds` as conservative summaries; the itemized matrix distinguishes parallel routes. Store material-requirement sources in the existing applicable aggregate source arrays as well. New cases use `case.applicationMaterialsAuditRequired: true`; legacy cases lacking this flag need not be silently rewritten. In new strict complete cases, every A/B/C viable route includes the four minimum rows. All factual strings remain research-only facts, without email subjects, salutations, applicant pitches or proposal prose.

## Delivery and writing handoff

Render the A/B/C material matrix in `06-APPLICATION-READINESS.md` before the A-tier deeper profiles. Include candidate, route, official document/type, status, stage, count, who submits, format/length/method, verification date and sources. Missing rules remain visible.

Hand off this checklist to a separate writing workflow. That workflow chooses motivation/SOP, PI enquiry, cover letter or proposal according to the verified route and the user's requested task. Recommendation requirements support referee planning, not ghostwriting a referee-authored letter or implying referee agreement.
