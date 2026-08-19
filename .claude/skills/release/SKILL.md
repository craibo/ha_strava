---
name: release
description: Create a release or pre-release for ha_strava (bumps manifest.json, tags, and publishes a GitHub release with curated notes)
disable-model-invocation: true
---

Create a release or pre-release for this integration. Ask the user which one they want if it isn't already clear from their request.

## Versioning rules

Both releases and pre-releases use plain patch versions (e.g. `4.6.1`, `4.6.2`) — there is no `-beta.N` suffix. A pre-release is just a normal version tag published with GitHub's "pre-release" flag instead of "latest"; the version string itself doesn't distinguish the two.

- **Target version** = the version currently in `custom_components/ha_strava/manifest.json` (e.g. `4.6.1`).
- **Pre-release**: if a tag with that exact version already exists (as either a release or a pre-release), bump the patch number by 1 and use that instead — repeat until the version is unused.
- **Release**: if a tag with that exact version already exists, STOP and tell the user the manifest needs to be bumped first — do not auto-increment a release version on their behalf.
- Never reuse or go backwards from an existing tag.

## Steps

### 1. Determine current state

```bash
cd <repo root>
git status --short          # must be clean; if not, stop and tell the user
git fetch --tags
cat custom_components/ha_strava/manifest.json   # get the current version
gh release list --limit 10  # see recent releases/pre-releases
```

### 2. Compute the target version

Start from `manifest.json`'s `version` field. Check `git tag -l "<version>"`.

- **Pre-release**: if it already exists, increment the patch number and check again, repeating until you find a version with no existing tag.
- **Release**: if it already exists, stop and tell the user to bump `manifest.json` first — do not proceed.

Use the resulting version as the target for both the manifest bump and the tag.

### 3. Find the previous reference point

- **Pre-release notes** diff against the most recently published tag overall (release or pre-release, whichever is more recent by date) — i.e. the immediately preceding entry in `gh release list`.
- **Release notes** diff against the latest published **release** tag specifically (not a pre-release), covering everything since then (including any pre-releases that led up to it): `gh release list --exclude-pre-releases --limit 1`, or filter tags without matching a pre-release marker.

```bash
git log <previous-tag>..HEAD --oneline
```

### 4. Draft release notes

Compact, clear, bullet points. Group or describe by user-facing change, not by commit.

**Exclude** commits/changes that are:

- Test-only changes (adding/updating tests, fixing test flakiness)
- `CLAUDE.md`, `.claude/`, skills, agent configuration, or other AI-tooling meta files
- Pure chore/formatting noise with no user-facing effect (unless it's the only content — in which case say so plainly)

**Include** anything user- or developer-facing: features, fixes, behavior changes, breaking changes, config/docs changes that affect setup.

Format:

```markdown
## What's Changed

- <concise bullet, semantic-prefix style, no PR/commit spam>
- ...

**Full Changelog**: https://github.com/craibo/ha_strava/compare/<previous-tag>...<target-tag>
```

Keep each bullet to one line where possible. Do not include a testing/test-plan section.

### 5. Confirm with the user before publishing

Show the user:

- The target version/tag being created
- Whether it's a release or pre-release
- The full drafted release notes

Ask them to confirm or edit before proceeding. **Do not tag, push, or create the GitHub release until the user explicitly confirms.**

### 6. Bump manifest and commit

If `manifest.json`'s version doesn't already equal the target version exactly, update it and commit on `main` — this applies to both releases and pre-releases, since the tag and the manifest always match now:

```bash
git commit -m "chore: release <version>"
```

### 7. Tag and publish

```bash
git tag <target-tag>
git push origin <target-tag>
```

Pre-release:

```bash
gh release create <target-tag> --title "<target-tag>" --notes "<confirmed notes>" --prerelease
```

Release:

```bash
gh release create <target-tag> --title "<target-tag>" --notes "<confirmed notes>" --latest
```

### 8. Share the result

Output the GitHub release URL as a clickable link.
