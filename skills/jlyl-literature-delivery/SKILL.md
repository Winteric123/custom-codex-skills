---
name: jlyl-literature-delivery
description: Search scientific literature by topic, title, DOI, PMID, or PMCID; download lawful open-access full text directly when available; otherwise submit the selected paper to 聚联文献传递; and verify the resulting local PDF. Use when the user wants to find and obtain papers, with 聚联 as a fallback rather than the default for open-access papers. Do not use for literature synthesis that does not require delivery.
license: Apache-2.0
metadata:
  short-description: Retrieve OA PDFs directly, with 聚联 fallback
  adapted-from: https://github.com/xuzhougeng/wisp-science/tree/main/skills/literature-review
---

# 文献检索、开放获取下载与聚联传递

Turn a literature request into a verified local file: retrieve live metadata, let the user choose when the query is ambiguous, download lawful open-access full text directly when available, and use 聚联 only when no usable public full text is available.

This skill adapts the live-retrieval and DOI-verification approach of `wisp-science`'s Apache-2.0 `literature-review` skill. It adds PubMed lookup and the site-specific 聚联 delivery workflow.

## Inputs

Accept any of these:

- DOI, PMID, or PMCID
- an exact or approximate paper title
- a topic, question, or short description
- an optional year bound, result limit, and destination folder

Never place passwords, API keys, patient identifiers, or other sensitive personal data in a literature query. If a query itself contains sensitive data, obtain action-time confirmation before transmitting it to literature APIs or 聚联.

## Retrieve and select

Use `scripts/literature_lookup.py` for deterministic live retrieval from PubMed, OpenAlex, and Crossref. Locate a usable Python runtime; on Codex desktop, `load_workspace_dependencies` can provide one.

```powershell
<python> scripts/literature_lookup.py "<query>" --limit 8 --output <workdir>/literature-results.json
```

Optional API configuration is documented in [references/api-configuration.md](references/api-configuration.md). Keys are not required for ordinary one-off use.

Interpret `selection.status` as follows:

- `auto`: an exact identifier or exact-title match was resolved; use its `delivery_identifier`.
- `needs_user_choice`: show a compact numbered list with title, year, journal, DOI/PMID, and OA status; ask the user to choose. Do not silently select a topical match.
- `not_found`: refine the query once using a distinctive title phrase or identifier. If still empty, report that retrieval failed rather than inventing a citation.

Reject a candidate marked `retracted: true` unless the user explicitly wants that paper. Prefer delivery identifiers in this order: DOI, PMID, PMCID, exact title.

## Choose the retrieval path

Use an open-access source before 聚联. Read [references/oa-download-workflow.md](references/oa-download-workflow.md) before attempting full-text retrieval. Check the selected record's `oa_url`, PMCID, DOI landing page, and official publisher or repository links for a lawful public full-text PDF.

For a selected PMCID, use `scripts/oa_download.py` to try the programmatic PMC AWS and Europe PMC routes and validate the response before browser work:

```powershell
<python> scripts/oa_download.py --pmcid <PMCID> --output <temporary-pdf-path>
```

- Try lawful sources in this order: the current PMC AWS Article Dataset, Europe PMC, the publisher's explicitly open PDF, and then the PMC webpage in Chrome when the user has authorized Chrome control for the task. Use 聚联 only after these applicable routes fail.
- The legacy PMC OA Web Service was retired in August 2026. Do not call its old `oa.fcgi` endpoint or treat an `/articles/<PMCID>/pdf/...` webpage URL as a raw PDF without validation.
- An `oa_url` is a lead, not proof that the response is a PDF. Follow the official page to its PDF link when needed, then verify the downloaded bytes.
- Do not bypass a paywall, access control, CAPTCHA, or publisher restriction. A freely visible abstract is not full-text availability.
- If a valid public PDF is available, download it directly. Do not open or submit a 聚联 request for that paper unless the user explicitly asks to use 聚联 anyway.
- A failed source does not prove that the paper lacks lawful open access. Try each applicable source once, in the stated order. Never repeat the same download merely because an event or response observation timed out.
- If programmatic sources fail and Chrome control is authorized, use the installed Chrome control skill to open the official PMC article page and click its PDF download once. Do not inspect cookies, passwords, or browser storage. If Chrome shows a CAPTCHA or other access-control step, stop and ask the user to complete it.
- If no lawful public full text is available after the applicable programmatic and Chrome routes, use the 聚联 fallback below.

Direct open-access download does not create an external request and therefore does not require the 聚联 submission confirmation.

## Deliver through 聚联 as fallback

Read [references/jlyl-workflow.md](references/jlyl-workflow.md) before controlling the website. Use the installed Browser control skill for the live page; do not reproduce or bypass its authentication and confirmation rules.

The submission creates a real request in the user's 聚联 account. Obtain action-time confirmation immediately before clicking the final `提交` button. A general request to find a paper is not a substitute for that confirmation.

After submission, record the task number and status. Never resubmit the same identifier merely because status polling or download-event observation timed out.

## Download and verify

For direct open-access retrieval, download to a temporary location first. For Chrome or 聚联, use the browser's normal download folder as the staging location. For 聚联, when `下载资源` appears, click it once. If a browser download event times out, inspect recently modified PDF or archive files before attempting another click.

Use the user-specified destination when provided. Otherwise keep the browser download in the local Downloads folder; in a projectless Codex chat, also copy the verified deliverable to the task's `outputs/literature-delivery/` folder. Do not overwrite an existing file: choose a unique name.

Only after the staged file passes PDF verification, create a publication-year subfolder beneath the selected destination and move or copy the PDF into that folder. Remove invalid staged responses and do not leave empty year folders:

```text
<destination>/<year>/
```

Use the four-digit publication year from the verified metadata. If no reliable publication year is available, use an `unknown-year` subfolder rather than guessing.

Name each downloaded PDF inside its year subfolder using this convention:

```text
<first-author>_<short-title>_PMID<pmid>.pdf
```

- Use the first author's family name and a concise, recognizable title segment.
- When PMID is unavailable, use `PMCID<pmcid>`; when neither is available, use `DOI_<sanitized-doi>`.
- Replace Windows-invalid filename characters (`\ / : * ? " < > |`) and whitespace runs with underscores, collapse repeated underscores, and remove trailing spaces or periods.
- Keep the complete filename, including `.pdf`, at or below approximately 150 characters. Preserve the author, identifier, and extension; shorten only the title segment when necessary.
- If the filename already exists, append `_2`, `_3`, and so on instead of overwriting it.

For a PDF, verify all of these before reporting success:

- the file exists and is non-empty
- its first five bytes are `%PDF-`
- the HTTP content type is `application/pdf` when available; for the official PMC AWS object store, `application/octet-stream` or `binary/octet-stream` is acceptable only when the PDF signature and parser checks pass
- a PDF parser can read at least one page and reports that the file is not corrupt
- the filename and selected paper are plausibly consistent
- the first-page title or metadata title is plausibly consistent with the selected paper
- a parseable supplementary table or figure is not the article: reject files whose first page says `Supplementary` or whose object key is clearly a supplement, then continue to the main-article PDF

Prefer the publisher's version of record when it is lawfully open. If only a lawful author manuscript is available, accept it unless the user requested the version of record, and label the downloaded version in the report.

For every attempted paper, record the DOI, PMID, PMCID, version type, source URL, retrieval route, local path, file size, page count, SHA-256, and verification status. Report the selected citation, identifier, retrieval route (`open access`, `Chrome PMC`, or `聚联`), final status, and a clickable absolute path to the verified file. For 聚联 retrieval, also report the task number. If 聚联 is still processing, preserve the browser tab for handoff and report the task number without claiming that a download completed.
