---
name: wisp-codex-skill-manager
description: Create, update, validate, and synchronize personal skills that must be available in both Codex and Wisp Science, and explain where each product stores newly authored skills. Use when the user asks to create, revise, fix, validate, install, locate, or synchronize a shared Codex/Wisp skill, including after switching models or authoring from Wisp. Do not use merely to run an existing skill.
---

# Wisp-Codex Skill Manager

Maintain one canonical skill folder and leave Codex and Wisp on the same version after every authorized creation or update.

## Storage model and synchronization direction

- Treat the host product and authoring workflow—not the selected AI model—as the determinant of the save location. Switching models inside Wisp does not change Wisp's skill paths.
- A skill created or updated through Codex belongs in the canonical Codex root described below. When Wisp's `WISP_SKILLS_PATH` includes that root, Wisp discovers the same files; no second copy is required.
- A project-local skill created through Wisp's own `skill-creator` defaults to `<current-project>/.wisp/skills/<skill-name>`.
- Installing a Wisp project skill through **Settings -> Skills** copies it into Wisp's user skill directory. It does not install the skill into Codex.
- `WISP_SKILLS_PATH` is a discovery setting, not a guarantee that Wisp's authoring tools can write to every configured path. Wisp file tools may be limited to the current project.
- Describe the default arrangement accurately as **Codex-authored shared source -> Wisp discovery**. Do not claim automatic Wisp-to-Codex synchronization.

## Canonical layout

- Use `$CODEX_HOME/skills` when `CODEX_HOME` is set; otherwise use `%USERPROFILE%\.codex\skills`.
- Keep each shared skill at `<canonical-root>/<skill-name>`.
- Never create or edit a personal skill inside the canonical root's `.system` directory.
- Prefer shared discovery over duplicate copies: configure Wisp's `WISP_SKILLS_PATH` to include the canonical root so both products read the same files.
- Never write into Wisp's bundled installation directory or undocumented application-data directories.

## Create or update

1. Resolve the target skill name and canonical path. Update an existing canonical folder in place; do not initialize it again.
2. When the built-in `$skill-creator` is available, follow it for authoring quality, structure, metadata, and validation. This skill owns the shared path and Wisp synchronization checks.
3. Preserve the complete skill folder, including `SKILL.md` and any intentional `agents`, `scripts`, `references`, or `assets` resources.
4. Run the applicable Codex validator and any deterministic tests for changed scripts.
5. Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <manager-skill>/scripts/verify_wisp_sync.ps1 -SkillPath <canonical-skill-folder>`.
6. Treat a successful verifier result as synchronized because Wisp reads the canonical folder directly. Do not claim synchronization when the verifier reports a missing or mismatched `WISP_SKILLS_PATH`.
7. Report the canonical path, validation result, Wisp synchronization status, and whether Wisp must reload skills or start a new conversation.

## When authoring from Wisp

1. Keep the default Wisp-created skill at `<current-project>/.wisp/skills/<skill-name>` unless the user has explicitly established another writable shared source.
2. Validate it with Wisp's bundled `skill-creator` workflow.
3. Explain that changing the AI model does not alter this location.
4. If the skill is only for that Wisp project, leave it project-local.
5. If the skill must be available throughout Wisp, direct the user to install it through **Settings -> Skills** and explain that Wisp creates or manages its own installed copy.
6. If the skill must also be available in Codex, do not report it as synchronized yet. Use an authorized Codex or filesystem workflow to place the validated skill in the canonical Codex root, resolve conflicts deliberately, and run the synchronization verifier.
7. When both a Wisp-local folder and a canonical Codex folder exist, name the authoritative source explicitly. Never allow two independently edited copies without warning about version drift.

## True bidirectional sharing

The default configuration is not bidirectional. If the user requests authoring from either product into one shared source:

- propose a neutral user-selected directory that both products can read and write;
- configure Wisp discovery for that directory;
- expose the shared skill folders to Codex using a supported installation or link strategy;
- verify actual write permissions from both products before calling the setup bidirectional;
- preserve one authoritative copy and avoid copy-on-edit workflows.

Do not silently redesign an existing installation or create filesystem links without explicit approval.

## Missing Wisp configuration

If `WISP_SKILLS_PATH` does not include the canonical root:

- explain that the Codex files changed but Wisp did not;
- ask before changing the user's persistent environment;
- when authorized, append the canonical root without deleting other configured roots;
- tell the user to fully restart Wisp after changing the environment;
- rerun the verifier after the configuration change.

Do not use a copied Wisp folder as a silent fallback. If the user explicitly requests physical mirrors, establish one authoritative source and use a separately approved one-way deployment workflow.

## Reload boundary

File synchronization does not hot-reload an already running conversation. After a successful create or update, remind the user to select **Settings -> Skills -> Reload Skills** in Wisp and start a new conversation when the updated instructions must be guaranteed.
