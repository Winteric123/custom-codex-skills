---
name: wisp-codex-skill-manager
description: Create, reconcile, update, and verify personal skills shared by Codex and Wisp Science. Use for shared skill installation, version differences, missing Wisp skills, discovery and reload problems, or questions about where either product saves skills. Do not use merely to run an existing skill.
---

# Wisp-Codex Skill Manager

Maintain one reviewed set of skill files that both products can discover. Separate the file-sharing result, Wisp's loaded catalog, and the current conversation's skill snapshot.

## Resolve the actual arrangement first

- Use `$CODEX_HOME/skills`, otherwise `%USERPROFILE%\.codex\skills`, as the canonical Codex location. Personal skills do not belong in `.system`.
- Inspect the existing canonical skill, Wisp global root, the active project's `.wisp/skills`, and relevant extra roots before choosing an installation method. Include scripts, references, assets and metadata when comparing copies.
- A canonical path is a storage convention, not evidence that its contents are newer. Neither application of origin, file modification time, schema number nor number of files establishes the user's intended latest version.
- Detect root links and compare actual directory/file identity. Equal hashes prove equal contents, not a shared file. Inspect the path Wisp actually reports; a same-name project or global skill can shadow the expected source.

On Windows, a verified whole-root junction such as `%USERPROFILE%\.wisp\skills -> %USERPROFILE%\.codex\skills` can make both products read one skill tree. Preserve unrelated skills and inspect the existing topology before changing it; never assume a recorded arrangement still matches the current machine.

With a verified root junction, no extra copy or `WISP_SKILLS_PATH` change is needed. Wisp's **Settings -> Skills** installation target then resolves into the canonical directory, so inspect conflicts before installing over an existing skill. Do not substitute child skill-directory junctions: the observed Wisp scanner follows a linked scan root but skips linked child directories. Read [Windows sharing and recovery](references/windows-sharing.md) only when diagnosing or repairing discovery or links.

## Create, reconcile or update

1. Use the built-in `$skill-creator` for skill structure and validation. For an existing shared skill, edit its current shared folder rather than initializing another copy. Switching the AI model does not change the host application's save location.
2. If copies differ, identify meaningful instruction, script, schema and resource changes. Use authoring records when available; preserve useful changes from either side. Resolve routine additive differences directly. Ask the user only when contradictory behavior requires a preference that the conversation does not establish.
3. Before merging or changing discovery topology, back up every distinct affected version outside all scanned skill roots. Preserve unrelated skills. Record the original locations and the chosen merged result. Never classify a copy as obsolete using timestamps alone.
4. Write the reviewed result to the shared source. Keep existing metadata and intentional resources. If schema/tool contracts changed, explain compatibility; do not silently rewrite the user's historical cases or run newer renderers over incompatible data. Check affected task/script paths when moving a skill with scheduled execution.
5. Run the applicable skill validator and meaningful checks for changed scripts. Reuse existing tests when their prerequisites are available. Record missing fixtures or failed launches as unexecuted/failed, not passed; do not invent research evidence to satisfy a test fixture.
6. Verify file identity and discovery with the workflow below. A staging folder, proposed command, `-WhatIf`, or a successful copy alone is not completion.

## Authoring from Wisp

- For an existing shared skill, resolve and update its shared folder when the available tool permits it. Wisp's project-local creation default is `<project>/.wisp/skills/<name>`; writing there does not automatically update the global/shared skill.
- If the request is deliberately project-only, keep it local and report that scope. Otherwise deploy the reviewed project change through an authorized filesystem workflow and check for a same-name project copy shadowing the shared one.
- A root junction makes the two paths expose the same files. It does not grant every Wisp tool access outside its project. A successful ACP shell or PowerShell write proves that channel's access, not the native Wisp file tool's access.
- If direct editing is unavailable, use an available authorized channel or leave a clearly identified staged change. Do not silently maintain independent copies or promise automatic synchronization of files authored elsewhere.

## Verify files, catalog and conversation separately

Run the read-only [verification script](scripts/verify_wisp_sync.ps1) against the canonical skill directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File '<manager>\scripts\verify_wisp_sync.ps1' -SkillPath '<canonical-root>\<skill-name>'
```

The script checks filesystem/discovery configuration; it cannot refresh Wisp or observe its UI. It must not report Wisp loaded merely because environment variables match. A root junction can provide sharing even when `WISP_SKILLS_PATH` is absent. Script execution through the Wisp alias must still resolve the Codex canonical root correctly.

Then obtain **current evidence**, after the final file edit:

- Reload through Wisp **Settings -> Skills -> Reload Skills** when UI control is available. Confirm the target is listed and enabled, inspect its source path, and open its file view when confirming updated contents. A changed total skill count alone is insufficient.
- Alternatively, use `wisp_list_skills` plus `wisp_use_skill` (or equivalent Wisp tools), and compare the returned source/content with the shared source. A tool's failure to find a newly loaded skill can be an old ACP conversation snapshot; check the current UI catalog before changing files again.
- A UI source beneath `.wisp\skills` is valid when file identity confirms the root junction reaches the canonical skill. A separate copy with identical text is not proof of ongoing sharing.
- Only after observing the source in Wisp, record the evidence with `-WispDiscoveryVerified -WispDiscoveryEvidence '<what was observed and when>'` and the actual source path through `-WispObservedSkillPath` (accepts the skill directory or its `SKILL.md` file). These parameters record caller-observed evidence; they do not perform the observation.
- **Reload and a shared file do not refresh every existing conversation.** Record current-conversation loading separately. If the current ACP snapshot is stale or untested, report that the catalog is ready for a new conversation; do not claim all active chats now use the new instructions. Do not restart Wisp during an active task merely to manufacture a passing check.
- Use `-ConversationDiscoveryVerified` only after the current conversation actually retrieves the final skill contents. UI Reload or a successful catalog check does not establish this fact.

Keep the verification output, actual command/exit result and any UI/tool source evidence in the task's report area. Use the script's returned status and fields; an exit of 2 means verification is incomplete, even if part of the setup succeeded.

When changing the verifier, run [its regression tests](tests/test_verify_wisp_sync.ps1) with `powershell.exe -NoProfile -ExecutionPolicy Bypass -File '<manager>\tests\test_verify_wisp_sync.ps1'`. Tests use synthetic skills in the OS temporary directory by default (override with `-FixtureRoot`) and do not modify the user's Wisp or Codex configuration. Retained fixtures and test reports stay outside installed skill roots.

## Completion report

Report the concrete changes, exact canonical skill path, validation performed and three separate results:

1. **Files:** same shared source, reconciled copies, or still separate.
2. **Wisp catalog:** actually listed/enabled and source-verified, or not yet verified.
3. **Current conversation:** refreshed and checked, or a new conversation is required/untested.

Always end a skill creation/update with a Wisp reminder. If no shared discovery path is verified, state that Wisp has not been confirmed updated and direct the user to **Settings -> Skills**. If the shared catalog was verified, say whether Reload was already performed and remind the user to start a new conversation when existing instructions may be cached. Do not ask again for work already authorized by the user.
