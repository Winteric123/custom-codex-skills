# Supervisor contact verification playbook

Read this reference whenever supervisor contacts are found, updated, compared, audited, or displayed. The goal is to identify every usable public route while preserving who owns it, when it was current, and whether it is suitable for direct outreach. A published channel is not automatically a personal mailbox or an invitation to send unsolicited mail.

## 1. Contact search ladder

Search in this order and retain the exact opened page for each result:

1. Current official personal profile at the person's university, hospital, cancer institute, or research institute.
2. Current official staff directory, clinical specialist page, laboratory page, departmental directory, doctoral-supervisor page, or institution-hosted CV.
3. Another current official page from a verified joint appointment. Do not use a collaborator's institution unless it explicitly publishes the person's own current role and contact.
4. Current official project, grant, trial, conference, or vacancy page only when it explicitly maps the named person to the displayed channel. Keep the page's actual source type and role boundary.
5. Every applicable current official fallback: person-directed contact form, unit/group mailbox, department or secretariat mailbox, assistant contact, published telephone number, and institution-directed transfer route. Preserve each result under its actual owner; do not suppress a safe official fallback because it is not personal.
6. Only after the current official routes and fallbacks above have been checked, inspect candidate-bound primary publications. Use the author-information or correspondence footnote in the publisher full text, PubMed/PMC/Europe PMC record, or lawful article PDF. Start with the most recent five years; extend to eight years only when fewer than two usable candidate-bound correspondence records are found or the current institutional route remains unresolved.
7. Researcher-controlled ORCID or similar profile as a lead only. Independently verify the address through an institution or a candidate-bound publication before displaying it.

Do not stop at the first generic mailbox when a current official personal page remains reasonably searchable. Complete and record the applicable official fallback checks before searching papers. Conversely, do not replace a safe current official department/form route with an old paper email merely because the latter looks personal.

Useful query families include:

```text
site:[current-institution-domain] "Full Name" (email OR e-mail OR contact)
site:[hospital-domain] "Full Name" (researcher OR specialist OR staff)
site:[current-institution-domain] "Full Name" filetype:pdf
"Full Name" (corresponding author OR correspondence) email
"Full Name" [current affiliation] 2022..2026
```

Search name variants, initials, particles such as `van`, `de`, or `von`, diacritics, and verified former names. Never infer an address from an institutional naming convention.

## 2. Ownership types

Classify each public route separately:

- `personal_email`: the address visibly identifies the candidate and a current official institution publishes it for that person.
- `clinical_email`: the same standard as personal email, on a current clinical/hospital page.
- `publication_correspondence_email`: a primary publication explicitly maps the candidate to the address as corresponding author or named correspondence contact. This is publication-time evidence, not automatically a current official address.
- `group_email`, `unit_email`, `department_mailbox`, `secretariat_email`: an organizational alias; never relabel it as personal.
- `assistant_contact`: another named person's address published for scheduling or contact assistance.
- `phone`: preserve whether it is a personal/direct line, clinic number, group line, or switchboard.
- `contact_form`: state whether it is person-directed or a general institution form. A person-directed form does not reveal its underlying recipient mailbox.
- `not_public`: no usable public route after the recorded search. This means not found publicly, not that no contact exists.

The local part of an email can support owner plausibility but is never sufficient evidence by itself. A page must explicitly associate the mailbox with the candidate. An address naming another person belongs to that other person even when it appears on the candidate's page.

## 3. Currentness and evidence labels

For every channel record:

- owner: `candidate`, `assistant`, `group`, `unit`, `department`, `secretariat`, `institution`, or `unclear`;
- currentness: `current_official`, `publication_time_only`, `former_institution`, `currentness_unverified`, `historical`, or `not_public`;
- source kind and direct URL;
- source publication/update date when visible and access date always;
- current institution at the time of checking;
- any conflict, move, retirement, bounce, or reply-based caution.

Use a current official institutional page as the only basis for `current_official` personal or clinical email. A recent paper from the current affiliation may make an address a strong practical lead, but keep `publication_time_only` until a current official page independently confirms it. A publication affiliation proves the time of publication, not current employment.

If the person moved institutions, mark the old institutional mailbox `former_institution` even when ownership is certain. If two official pages conflict, retain both and resolve the preferred route by recency, directness, and current institutional affiliation; do not silently delete the conflict.

## 4. Publication correspondence audit

Bind a paper email to the candidate only when the article explicitly links the name or correspondence symbol to that address. Do not assign every correspondence email in a multi-corresponding-author paper to every corresponding author unless the mapping is explicit.

Record:

- paper title, year, DOI/PMID/PMCID when present;
- candidate's exact author role: corresponding, co-corresponding, senior/last without correspondence proof, or other;
- the displayed address and affiliation at publication;
- whether the email domain matches the verified current institution;
- whether a second recent candidate-bound paper repeats the same address.

Last-author or penultimate-author position alone is not proof of correspondence ownership. Search snippets, metadata aggregators, inferred author-email databases, ResearchGate uploads, and email-pattern services are leads only.

## 5. Preferred route and outreach-permission boundary

Choose one `preferredRoute` for operational use, but keep all verified alternatives. In general:

1. current official personal/clinical email;
2. current official person-directed form;
3. current official group/assistant/secretariat route that explicitly handles research contact;
4. publication-time personal correspondence email, with a visible same-day currentness warning;
5. general department or institutional channel for a transfer enquiry.

Do not state that a person “allows email” merely because an address is public. Record contact policy separately as `explicitly_supported`, `explicitly_discouraged`, `restricted_to_route`, or `not_stated`, and require a current official instruction for any value other than `not_stated`.

## 6. Structured supplemental audit

Strict schema-1.2 `records[].contacts` remains limited to current official channels and the explicit `not_public` marker. Store the full channel audit, including publication-only or historically useful channels, in optional `data/contact-audit.json`. When present, `scripts/render_outputs.py` renders `08-CONTACT-AUDIT.md`, and `scripts/validate_case.py` validates it. The top level is an object with `schemaVersion: "1.0"`, `checkedAt`, and `records[]`.

Each record must use the stable candidate ID from `records.json`, retain an ordered search audit, list every channel separately, and select a preferred channel only by its `channelId`. The ordered `searchAudit.steps[]` is the evidence that current official primary and fallback routes were checked before any publication step. `officialFallbacksExhaustedBeforePublication` must be `true` whenever a publication step or publication-only channel is present.

```json
{
  "schemaVersion": "1.0",
  "checkedAt": "YYYY-MM-DD",
  "records": [
    {
      "candidateId": "school-person-name",
      "checkedAt": "YYYY-MM-DD",
      "currentInstitutionZh": "当前机构中文名",
      "searchAudit": {
        "officialFallbacksExhaustedBeforePublication": true,
        "steps": [
          {
            "stage": "current_official_primary",
            "routeType": "personal_profile",
            "resultZh": "官网个人页未公开邮箱。",
            "sourceIds": ["src-person-profile"]
          },
          {
            "stage": "current_official_fallback",
            "routeType": "person_directed_form",
            "resultZh": "找到本人定向联系表单。",
            "sourceIds": ["src-person-contact-form"]
          },
          {
            "stage": "publication",
            "routeType": "primary_publication",
            "resultZh": "近年论文明确列出本人通讯邮箱。",
            "sourceIds": ["src-person-paper"]
          }
        ]
      },
      "channels": [
        {
          "channelId": "person-directed-form",
          "type": "contact_form",
          "value": "https://institution.example/person/contact",
          "owner": "candidate",
          "currentness": "current_official",
          "sourceIds": ["src-person-contact-form"],
          "candidateBound": true,
          "notesZh": "当前官方本人定向入口；底层收件邮箱未公开。"
        },
        {
          "channelId": "paper-email-2025",
          "type": "publication_correspondence_email",
          "value": "person@example.org",
          "owner": "candidate",
          "currentness": "publication_time_only",
          "sourceIds": ["src-person-paper"],
          "candidateBound": true,
          "sourceDate": "2025",
          "notesZh": "论文明确列为本人通讯邮箱；当前机构官网未独立确认。"
        }
      ],
      "preferredRoute": {
        "preferredChannelId": "person-directed-form",
        "reasonZh": "优先使用当前官方本人定向入口。",
        "sameDayRecheckRequired": false
      },
      "contactPolicy": "not_stated",
      "cautionZh": "论文邮箱不能自动视为当前官方邮箱。"
    }
  ]
}
```

Allowed `searchAudit.steps[].stage` values are `current_official_primary`, `current_official_fallback`, `publication`, `researcher_controlled`, and `other`. Once a `publication` step begins, no current-official primary or fallback step may appear later in the ordered array. Every step has a non-empty `routeType`, a Chinese `resultZh`, and a `sourceIds` array; a documented zero-result search may use an empty array only when no page exists to cite.

Every channel has a unique lowercase-ASCII `channelId`, controlled `type`, `owner`, `currentness`, and a `sourceIds` array. A real value needs at least one valid source ID. `not_public` is exclusive: it may appear only when no usable email, form, group/unit/department/secretariat/assistant route, phone, or other public channel was found; its `value` is empty, `owner` is `unclear`, `currentness` is `not_public`, and `preferredRoute` is `null`. Never add `not_public` beside a real channel or use it to conceal an available form or organizational route.

A `current_official` channel needs one same source that is current, `official_institution`, contact-domain, and bound to the candidate or applicable school; a publication-correspondence channel needs a candidate-bound contact-domain primary-publication source. If any usable `current_official` channel exists, `preferredRoute` must select one of those current official channels rather than a publication-time, historical, former-institution, or currentness-unverified alternative. A same-day recheck flag does not waive this official-first preference.

For user-facing supervisor lists, render the contact type, owner, currentness, and caution beside the value. Never display an unlabeled office or publication-only address as “本人邮箱”. If no personal email exists, show the best verified fallback and explicitly state its ownership.

## 7. Completion check

Before declaring the contact audit complete, verify that:

1. every retained candidate in the requested contact-audit scope has at least one structured channel or an exclusive `not_public` result;
2. every displayed value has a direct source URL and an owner classification;
3. current official and publication-only evidence are not conflated;
4. current and former institutions are distinguished;
5. generic mailboxes, assistants, forms, and telephone numbers are labeled accurately;
6. no email is inferred from a pattern or search snippet;
7. the preferred route references an existing usable `channelId`, and any same-day recheck requirement is visible;
8. publication of a contact is not described as consent to unsolicited contact.
9. all recorded current-official fallback steps precede publication steps, and `not_public` does not coexist with a form, mailbox, phone, or any other real channel.
