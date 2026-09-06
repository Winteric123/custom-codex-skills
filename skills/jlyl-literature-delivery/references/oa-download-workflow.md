# Open-access full-text retrieval

Use this workflow only after a paper has been selected and its identifiers and publication metadata have been verified.

## Source order

Try each applicable source once. Verify the response before moving to the next source.

1. **PMC AWS Article Dataset**
   - For a selected PMCID, use the current public PMC Article Dataset on AWS rather than the retired OA Web Service.
   - Follow the current PMC documentation at <https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/>. Do not guess an object key from the PMCID alone; resolve the current article version and its PDF object from the dataset metadata or manifest.
   - If a version contains multiple PDF objects, prefer the exact main-article key `<PMCID>.<version>.pdf`. Rank obvious `sup`, `supp`, or `supplement` objects last; a readable supplementary PDF does not count as successful article delivery.
   - Prefer a version of record over an author manuscript. Inspect the dataset metadata fields that identify article version, manuscript status, open-access status, license, and retraction status.
   - A dataset record may legitimately omit a PDF, particularly for an author manuscript without a Creative Commons license. Missing data is not an invitation to bypass access controls.

2. **Europe PMC**
   - Use the official article page for the PMCID and its public PDF route, such as `https://europepmc.org/articles/<PMCID>?pdf=render`.
   - Accept the response only if it yields HTTP success, a PDF content type when available, and bytes beginning with `%PDF-`.
   - An HTTP 500, HTML response, or JSON error means this source failed for that record; do not retry the same URL repeatedly.

3. **Publisher open PDF**
   - Follow the DOI to the official publisher page and use only a PDF explicitly available without sign-in, payment, CAPTCHA bypass, or other access-control circumvention.
   - Prefer the publisher's version of record when it is available under lawful public access.

4. **PMC webpage in Chrome**
   - Use this route only when programmatic sources failed and the user has authorized Chrome control for the task. The current user has authorized Chrome as the final PMC webpage fallback for this personal skill; still follow the installed Chrome control skill and any current task constraints.
   - Open the official `https://pmc.ncbi.nlm.nih.gov/articles/<PMCID>/` page in Chrome and use the visible PDF control. Click the download once.
   - If the page displays a JavaScript `Preparing to download` transition, allow the browser to complete it normally. Do not reproduce or bypass the transition with hidden cookies or browser-storage extraction.
   - If authentication or a CAPTCHA blocks the visible workflow, stop and ask the user to complete that step in Chrome. Do not switch to another browser when Chrome was explicitly selected.
   - If the download event is not observed, inspect recent files in the normal Chrome download folder before clicking again.

5. **聚联 fallback**
   - Use 聚联 only after all applicable lawful open-access routes above fail.
   - Follow `jlyl-workflow.md` and obtain action-time confirmation immediately before the final `提交` click.

## Staging and validation

Keep programmatic responses in a temporary staging location. Treat `.pdf` as an intended extension, not proof of file type.

Before placing a file in the final library:

- require a non-empty file beginning with `%PDF-`
- require at least one readable page from a PDF parser
- compare the first-page or metadata title with the selected record
- record the response content type when available
- compute SHA-256 and record the page count and version type

Delete invalid HTML or JSON staging responses. Create the final `<destination>/<year>/` directory only after validation succeeds, then apply the filename convention from `SKILL.md`. Do not leave empty year directories after a failed attempt.
