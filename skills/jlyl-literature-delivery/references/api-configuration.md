# API configuration

The lookup script is designed for low-frequency, one-off use and runs without keys.

## Optional environment variables

- `NCBI_API_KEY`: optional PubMed E-utilities API key.
- `NCBI_EMAIL`: contact email sent to NCBI as the `email` parameter.
- `OPENALEX_API_KEY`: optional OpenAlex API key.
- `OPENALEX_EMAIL`: optional contact email for OpenAlex requests.
- `CROSSREF_EMAIL`: optional contact email for Crossref's polite pool.

Do not store keys in `SKILL.md`, scripts, shell history, generated reports, or project files. Prefer a process/user environment variable or the Windows-encrypted credential file below. Never ask the user to paste an API key into a public artifact.

## Windows-encrypted credential file

The script automatically checks this file after checking environment variables:

`%USERPROFILE%\.codex\secrets\jlyl-literature-delivery\credentials.json`

The file stores only DPAPI ciphertext protected for the current Windows user. It is not portable to another Windows account. Override the path with `JLYL_CREDENTIALS_FILE` when needed.

Use `scripts/store_windows_credential.ps1` to create or rotate a value. The helper reads the secret as one line from standard input, encrypts it with Windows DPAPI, restricts the file ACL to the current user, and prints only non-secret metadata.

Credential precedence is: environment variable, encrypted credential file, then anonymous API access.

## Limits and behavior

PubMed E-utilities supports anonymous low-frequency use. An NCBI API key raises the supported request rate, but this script still uses a small number of sequential requests. OpenAlex and Crossref also permit ordinary anonymous metadata queries; keys or contact email mainly improve quotas and service etiquette.

The script reports only whether optional keys were present. It never writes key values to output.
