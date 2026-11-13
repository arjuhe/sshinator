---
status: accepted
updated: 2026-11-12
tags: [howto, vault]
---

# How to Use This Vault

This is the instruction set for the `docs/` vault. It is written for anyone who forks this project and continues it on their own. Once you fork, the notes in this vault are yours. Replace them with your own.

## What the vault is

`docs/` is an Obsidian vault. It holds the design notes, decisions, plans, and how-tos for the project. Open the `docs/` folder in Obsidian (File > Open folder as vault) and start at `Home.md`.

Claude Code reads the vault too. `CLAUDE.md` at the project root points to it, so keep that pointer current.

## Folder map

| Folder | What it is for | What belongs in it |
|---|---|---|
| `00 - Start Here/` | How to use this vault. Start here if you fork the project. | This file and any other how-to about the docs themselves |
| `01 - Inbox/` | Temporary holding area for new notes. | Quick captures. Move each note to its proper folder once it has a home. |
| `02 - Architecture/` | How the system is built. | System overview, data model, and the `Decisions/` folder |
| `02 - Architecture/Decisions/` | Architecture Decision Records (ADRs), one per decision. | `ADR-NNN ...` notes, made from `Templates/ADR.md` |
| `03 - Features/` | One folder per feature. | Each feature's spec and plan. See "Where plans go" below. |
| `04 - Workflows/` | How to do things, plus the project-wide index of next steps. | Setup, testing, and `Next Steps.md` |
| `05 - Sessions/` | Dated logs of working sessions. | One note per session: what was done and what was decided |
| `06 - Reference/` | Lookup material you come back to. | Decision log, gotchas, safety notes, anything you look up rather than read in order |
| `07 - Archive/` | Finished or superseded originals. | Old notes that have been migrated. Kept for reference. Not edited. |
| `Templates/` | Blank templates for new notes. | `ADR.md`, `Feature Spec.md`, `Plan.md` |
| `Attachments/` | Images and files that notes link to. | Pasted images, PDFs, other files |

## Where things go

- **A decision** that is hard to reverse goes in `02 - Architecture/Decisions/` as an ADR. Use `Templates/ADR.md`.
- **A feature** gets a folder in `03 - Features/`, named after the feature. The feature's spec goes in `<Feature>/<Feature>.md`, from `Templates/Feature Spec.md`.
- **A plan** goes in the folder of the feature it belongs to, as `03 - Features/<Feature>/Plan.md`. Use `Templates/Plan.md`. Every plan must have the plan header (see below).
- **A project-wide plan** that does not belong to one feature goes in `03 - Features/` under its own folder, with a `Plan.md`. Then link it from `04 - Workflows/Next Steps.md`.
- **A how-to** goes in `04 - Workflows/`. How-tos about the docs themselves go in `00 - Start Here/`.
- **Finished or superseded material** is migrated, then moved to `07 - Archive/`. Do not edit archived files.

## The plan header

Every plan starts with this header block. It is what makes a note a plan, and what the index uses to show status.

```markdown
---
type: plan
status: open          # open | in-progress | blocked | done
updated: YYYY-MM-DD
feature: <Feature name>
---

# Plan: <Feature name>
```

Keep `status` and `updated` current when you change the plan. When a plan is done, set `status: done` and leave the note in its feature folder. Do not delete it, because the history is useful.

## Frontmatter conventions

- `status` is the state of the note: `draft`, `living`, `accepted`, `superseded`, `done`, or, for plans, the values above.
- `updated` is the date you last changed the note, as `YYYY-MM-DD`.
- `tags` is optional, a short list such as `[feature, gate]`.

## Writing rules

- Link notes with `[[wikilinks]]` rather than copying content. Use the note's file name, without `.md`.
- **Accepted ADRs are never edited.** To change a decision, write a new ADR that supersedes the old one. Then set the old one's `status: superseded` and link to the new one.
- **Never put secrets in a note.** That means no API keys, passwords, tokens, or private keys. Real host names and IP addresses are also private; use placeholders such as `web-1` and `10.0.0.12`.
- Mark anything you have not verified as `TODO`, so it is easy to find later.

## Starting your own fork

1. Fork the project and clone your fork.
2. Read this file, then `Home.md`.
3. Decide what to keep. The how-tos and templates are general. The notes about this project's decisions, plans, hosts, and history are specific to it. Move any you still need into `07 - Archive/` and delete the rest. Keep the folder structure.
4. Rewrite `Home.md` for your project. Its links must point at notes that exist.
5. Update `CLAUDE.md` so it points to your `Home.md`.
6. Start your own decisions as ADRs. Numbering is yours to choose. If you keep `ADR-001`, make it your first decision, not a copy of this project's.
7. Check your links. In Obsidian, an unresolved link shows as a link to a note that does not exist. Fix or remove each one.

## Keeping the docs private or public

Before you publish a fork, check every note for personal details. The notes in this project name the author's real host names and local paths. Decide per folder whether it is shared, and make sure ignored notes do not break the links in shared notes.

## Checking the vault

- Open the vault in Obsidian and look at the graph and the unresolved-links list.
- Confirm every plan has the plan header.
- Confirm no note contains a secret or a private address.
