# Windows sharing and recovery

Use this reference for discovery failures, migration between copies and a shared source, or a broken link. Inspect the current installation before applying a workaround and revalidate version-sensitive behavior against the installed Wisp release.

## Why a root junction can work

The installed arrangement is:

```text
%USERPROFILE%\.wisp\skills
  -> %USERPROFILE%\.codex\skills
       <skill-name>\SKILL.md
       <skill-name>\scripts\...
```

Wisp scans each source with `WalkDir::new(base).max_depth(2)` without enabling traversal of child links. A root directory junction works because root links are followed; a `<root>/<skill-name>` junction is not recursively scanned. Nested `.system/<name>/SKILL.md` files are at depth 3 and are outside that scan. Sources: [Wisp scanner](https://github.com/xuzhougeng/wisp-science/blob/e58b72f35e167ac441faf25613af9b5042518aa0/crates/wisp-skills/src/index.rs), [WalkDir root-link behavior](https://docs.rs/walkdir/latest/walkdir/struct.WalkDir.html#method.follow_root_links).

The observed source precedence is bundled, project, global, extra, then plugin, with an earlier same-name entry winning. Check actual Wisp source paths after reload; do not infer the winning source from a folder's presence.

## Environment-only discovery is a fallback

In the verified [Wisp source parser](https://github.com/xuzhougeng/wisp-science/blob/e58b72f35e167ac441faf25613af9b5042518aa0/src-tauri/src/lib.rs#L4950-L4954), `WISP_SKILLS_PATH` is split on both `:` and `;`. This splits Windows drive letters. A remaining `\Users\...` fragment may accidentally work from C: and fail when Wisp starts from D:.

When a root junction already works, leave the environment alone. If an environment-based route is needed, `mountvol C: /L` returns the existing volume GUID path; append the canonical directory's drive-relative suffix to obtain a colon-free alias. Verify directory/file identity against the canonical path before configuring it. This is an alias, not a second copy and not a new volume or share.

Preserve other environment entries and retain a rollback value when an authorized change is needed. User/Machine environment settings and the verifier's Process environment do not establish what running Wisp inherited. Broadcast environment changes when appropriate, then arrange a safe full restart if Wisp must inherit them. Reload reads Wisp's existing process environment; it does not reload User environment settings from the registry. Never kill the active Wisp/ACP process to force a refresh mid-task.

## Safe migration or repair

1. Check all affected roots, same-name copies, link targets and unrelated global skills. Do not write into Wisp's bundled installation or edit its internal database to imitate a reload.
2. Prepare and validate the merged source, then back up all distinct versions outside discovery roots. A copied backup must contain real files; copying only a link would not preserve a historical snapshot.
3. Preserve unrelated installed skills in the resulting discoverable root.
4. Before a directory move, resolve and verify exact source/destination paths against the intended roots. Keep Windows filesystem operations in one shell; do not build cross-shell recursive removal commands. Prefer an archive move over deleting the old root. Do not recursively delete through a junction.
5. Preserve the user's already authorized shared arrangement. A materially different location, destructive conflict resolution or new external sharing needs user input; routine repair and verification within the authorized scope do not require repeat approval.
6. Verify the link's real target, directory identity and relevant file identity, then reload and inspect Wisp. Save the evidence and identify the current conversation separately. If a repair fails, keep the originals and report the actual partial state rather than claiming a successful deployment.

No continuously running sync daemon is needed for the root junction: both paths are the same files. Edits to a different project-local or staged folder are separate until deliberately deployed.

## Runtime and test limits

Filesystem identity and an actual Wisp catalog load are usually sufficient for a sharing task. Do not start extra runtimes merely to strengthen a claim that is already supported.

If a particular tool's write capability matters, verify it with that tool and a uniquely named temporary marker, then remove only that marker. Label the execution channel accurately. A successful ACP shell write does not prove that native Wisp file tools or background Runs can write the same path. Do not bypass a failed preflight by relabeling the same work; use a genuinely independent supported route and report its scope.

Existing validator tests may require real case-specific fixtures. Do not fabricate scientific evidence or modify user cases to make them pass; run appropriate syntax, initialization or error-path checks and state which contract tests were not executed.
