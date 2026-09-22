# Custom Codex Skills

Five reusable personal skills for Codex and Wisp Science:

- `jlyl-literature-delivery`: Search scientific literature, retrieve lawful open-access PDFs, and use 聚联文献传递 as a fallback.
- `phd-supervisor-outreach`: Draft personalized PhD supervisor outreach emails and optionally save them to an IMAP drafts folder.
- `phd-supervisor-research`: Research and verify prospective PhD supervisors, appointments, contacts, publications, grants, and recruitment evidence.
- `wisp-acp-weekly-check`: Check the versions of ACP adapters configured in Wisp and optionally register a weekly Windows check.
- `wisp-codex-skill-manager`: Reconcile and verify personal skills shared between Codex and Wisp while keeping one reviewed source.

`artificial-writing-skill` is maintained separately at [Winteric123/artificial-writing-skill](https://github.com/Winteric123/artificial-writing-skill).

## Repository layout

```text
skills/
├── jlyl-literature-delivery/
├── phd-supervisor-outreach/
├── phd-supervisor-research/
├── wisp-acp-weekly-check/
└── wisp-codex-skill-manager/
```

## Install for Codex

If Wisp uses an independent skill root, copy the selected skill directory into:

```text
%USERPROFILE%\.codex\skills\
```

## Install for Wisp Science

Copy the selected skill directory into:

```text
%USERPROFILE%\.wisp\skills\
```

If Codex and Wisp already share a verified root, update the shared source once and do not create a duplicate same-name copy. Use `wisp-codex-skill-manager` to establish or verify sharing.

Then select **Settings → Skills → Reload Skills** and start a new conversation so the updated skill list takes effect.

For shared use, keep one reviewed source and inspect the current installation before choosing a root junction, an extra discovery path, or a deliberate copy workflow.

## Security

No credentials, recipient lists, research cases, downloaded papers, or generated reports are included. Configure optional email or literature API credentials through the environment variables or encrypted local credential mechanisms documented in each skill.

`phd-supervisor-research/scripts/test_validator_contract.py` is a case-specific regression harness. It requires a compatible, already-valid case directory supplied through `--case-dir`; the repository does not include that research fixture.
