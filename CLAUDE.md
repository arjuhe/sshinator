# CLAUDE.md

## Project documentation

Design notes, decisions, and workflows live in the Obsidian vault at `docs/`.

- For project context, start with the home note. A sanitized sample is at `docs/Templates/Home-Sample.md`; the project's own `docs/Home.md` is kept local.
- Record new architectural decisions as ADR notes in `docs/02 - Architecture/Decisions/`, using `docs/Templates/ADR.md`.
- Do not edit accepted ADRs. To change a decision, create a new ADR that supersedes the old one.
- Put new feature specs in `docs/03 - Features/<feature name>/` using `docs/Templates/Feature Spec.md`.
- Put plans in the feature folder as `docs/03 - Features/<feature name>/Plan.md`, using `docs/Templates/Plan.md`. Every plan keeps its plan header.
- For how to use the vault, including the plan header and forking the project, see `docs/00 - Start Here/How to Use This Vault.md`.
- Use `[[wikilinks]]` to connect notes rather than duplicating content.
- Do not put secrets, API keys, or credentials in any note.
