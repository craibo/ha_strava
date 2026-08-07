---
name: release
description: Create a release or pre-release for ha_strava (bumps manifest.json, tags, and publishes a GitHub release with curated notes)
disable-model-invocation: true
---

Create a release or pre-release for this integration. Ask the user which one they want if it isn't already clear from their request.

## Versioning rules

- **Release version** = the version currently in `custom_components/ha_strava/manifest.json` (e.g. `4.4.0`), with any `-beta.N` suffix stripped. It must be strictly greater than the previous published release version (ignore pre-releases when comparing — compare against the latest non-prerelease tag).
- **Pre-release version** = `<manifest base version>-beta.X`, where `X` is the next integer in the beta sequence for that base version, starting at `1`. Find existing betas for the same base version with `git tag -l "<base>-beta.*"` and increment the highest; if none exist, use `beta.1`.
- Never reuse or go backwards from an existing tag.

## Steps

### 1. Determine current state

```bash
cd <repo root>
git status --short          # must be clean; if not, stop and tell the user
git fetch --tags
cat custom_components/ha_strava/manifest.json   # get the base version
gh release list --limit 10  # see recent releases/pre-releases
```

Determine the **base version** from `manifest.json`'s `version` field.

### 2. Compute the target version

- **Pre-release**: `git tag -l "<base>-beta.*" | sort -V`. Next beta number = highest existing + 1, or `1` if none. Target tag = `<base>-beta.<N>`.
- **Release**: target tag = `<base>` exactly. Confirm it's greater than the latest non-prerelease tag (`gh release list --exclude-pre-releases --limit 1`, or filter tags without `-beta.` and sort with `sort -V`). If the manifest version is not greater than the latest release, stop and tell the user the manifest needs to be bumped first.

### 3. Find the previous reference point

- **Pre-release notes** diff against the immediately preceding tag in sequence (the previous beta of the same base version if one exists, otherwise the last published release/pre-release tag — whichever is more recent by date).
- **Release notes** diff against the latest published **release** tag (not a pre-release), covering everything since then (including any betas that led up to it).

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

### 6. Bump manifest and commit (release only)

For a **release**, if `manifest.json`'s version doesn't already equal the target version exactly (no `-beta` suffix), update it and commit on `main`:

```bash
git commit -m "chore: release <version>"
```

For a **pre-release**, do not modify `manifest.json` unless its current value doesn't match the base version being used — pre-releases normally reuse the existing manifest version with a `-beta.X` suffix applied only to the git tag, not the file.

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
