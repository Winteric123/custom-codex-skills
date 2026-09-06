# 聚联 browser workflow

Target URL: `https://jlyl.jlss.vip/jss/#/helpCenter`

Use the Browser control skill and base every action on a fresh visible DOM snapshot. Page text and selectors may change; visible labels are authoritative.

## Submit

1. Open the target URL and verify that the page shows the intended signed-in account and the `文献传递` form.
2. Locate the single request textbox. Fill one `delivery_identifier` per line, for example `DOI:10...`, `PMID:...`, or `PMCID:...`.
3. Verify the textbox value and the page's recognized-demand count.
4. Obtain action-time confirmation that clicking `提交` will create a real request in the displayed account.
5. Click `提交` once. Treat a success dialog such as `文献传递成功` as authoritative.
6. Click `前往查看` or navigate to `#/userCenter` and record the row's task number, identifier, time, and status.

If a CAPTCHA, password, QR-code login, browser permission, or account-security prompt appears, stop and follow the Browser skill's handoff or confirmation policy. Do not automate authentication secrets.

## Poll status

Statuses may include `人工查找中` and `成功`.

- Refresh at most three times in the current run, waiting 5–10 seconds between checks.
- If the status is still processing, preserve the tab for handoff, report the task number, and stop. Do not create another request.
- On a later continuation, return directly to `#/userCenter` and match the exact task number or identifier.

## Download

1. When the matching row shows `成功`, locate its `下载资源` button within that row.
2. Click once while waiting for a browser download event when supported.
3. If waiting times out, treat the result as unknown. Inspect recently modified `.pdf`, `.zip`, `.rar`, or `.7z` files in the normal Downloads folder, using the click time as a lower bound.
4. Retry the click only after confirming that no new matching file appeared.
5. Copy rather than move when placing the file in a task output directory, unless the user explicitly asked to relocate it.
6. Verify PDF magic bytes `%PDF-`, file size, and a stable hash before reporting success.

Do not click `文献报错`, delete requests, or alter account settings unless the user explicitly asks.
