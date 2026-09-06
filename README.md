# Custom Codex Skills

Three reusable skills for Codex and Wisp Science:

- `phd-supervisor-outreach`: Draft personalized PhD supervisor outreach emails and optionally save them to an IMAP drafts folder.
- `jlyl-literature-delivery`: Search scientific literature, retrieve lawful open-access PDFs, and use 聚联文献传递 as a fallback.
- `wisp-codex-skill-manager`: Create, validate, and share personal skills between Codex and Wisp Science while keeping one authoritative source.

## Repository layout

```text
skills/
├── phd-supervisor-outreach/
├── jlyl-literature-delivery/
└── wisp-codex-skill-manager/
```

## Install for Codex

Copy the selected skill directory into:

```text
%USERPROFILE%\.codex\skills\
```

## Install for Wisp Science

Copy the selected skill directory into:

```text
%USERPROFILE%\.wisp\skills\
```

Then reload skills and start a new conversation so the updated skill list takes effect.

For `wisp-codex-skill-manager`, prefer keeping the canonical copy in the Codex skills directory and adding that directory to `WISP_SKILLS_PATH` so both products read the same files.

## Security

No credentials are included. Configure optional email or literature API credentials through the environment variables or encrypted local credential mechanisms documented in each skill.
