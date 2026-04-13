---
name: spec-lifecycle
description: "Specification file naming, folder structure, templates, and status management. Use when: creating a spec file, naming a spec, determining spec folder path, calculating quarter folders, applying spec templates, updating spec status frontmatter, obsoleting a spec, checking spec naming conventions."
---

# Specification Lifecycle

Unified conventions for creating, naming, placing, templating, and managing the lifecycle status of specification files under `specs/`.

Used by `Specification / Orchestrator`, `Specification / Scribe`, `Specification / Planner`, and `Specification / Status`.

## Quick Reference

Always read `specs/index.md` first for the authoritative description of each spec type and the quality bar.

## Folder Structure

### Date-Based Types (Bugfix, Rebrush, Technical Initiative)

```
specs/<type>/<YYYY>/<YYq#>/
```

- `<type>` — `bugfixing`, `rebrushes`, or `technical-initiatives`
- `<YYYY>` — Four-digit year
- `<YYq#>` — Two-digit year + quarter: `q1` (Jan–Mar), `q2` (Apr–Jun), `q3` (Jul–Sep), `q4` (Oct–Dec)

Example: `specs/bugfixing/2026/26q2/`

### Product-Area Stories

```
specs/product-areas/<area>/<sub-area>/
```

Use kebab-case folder and file names. One user story per leaf file. If complexity grows, split into sub-stories using a child folder.

## File Naming

### Date-Based Types

```
<YYYY-MM-DD>-<NNN>-<slug>.<type-suffix>.md
```

| Component | Rule |
|-----------|------|
| `YYYY-MM-DD` | Date of creation |
| `NNN` | Sequence number — scan same-date files in the target quarter folder and increment the highest |
| `slug` | Kebab-case short description |
| `type-suffix` | `bugfix`, `rebrush`, or `tech-initiative` |

Example: `2026-04-13-001-fix-login-redirect.bugfix.md`

### Stories

```
<slug>.story.md
```

Example: `view-team-calendar.story.md`

## Templates

Template files are stored under `templates/`. Read the appropriate template file before creating a new spec.

| Spec Type | Template File |
|-----------|--------------|
| Bugfix | `templates/bugfix.template.md` |
| User Story | `templates/story.template.md` |
| Rebrush | `templates/rebrush.template.md` |
| Technical Initiative | `templates/technical-initiative.template.md` |

## Common Rules

1. If information is missing for a section, keep the heading and write `TBD`.
2. Never add implementation details — specs describe **what** and **why** only.
3. Each spec must be explicitly scoped to one resolved app. Record the target app folder in `ADDITIONAL INFORMATION` when helpful.
4. Before obsoleting or removing a spec, verify no other spec references the target file.

## Status Management

Every spec file carries a `status` field in YAML frontmatter.

### Status Values

| Status | Meaning | Set When |
|--------|---------|----------|
| `NEW` | Spec just created, not yet implemented | After initial creation |
| `CHANGED` | Spec modified after initial creation | After any content update |
| `DONE` | Fully implemented, tested, and pushed to `origin/develop` | During Jira `Finalizing` phase |
| `OBSOLETE` | No longer relevant or superseded | When spec is retired |

### Frontmatter Format

```yaml
---
status: NEW
---
```

If no frontmatter exists, insert it at the top of the file. Only `Specification / Status` agent updates this field. Never modify other frontmatter fields or content outside the frontmatter block when updating status.

## Scribe Assignment

All spec types are handled by `Specification / Scribe`. The orchestrator includes the spec type in each delegation so the scribe selects the correct folder, naming convention, and template.

| Spec Type | Folder |
|-----------|--------|
| Bugfix | `specs/bugfixing/` |
| User Story | `specs/product-areas/` |
| Rebrush | `specs/rebrushes/` |
| Technical Initiative | `specs/technical-initiatives/` |
