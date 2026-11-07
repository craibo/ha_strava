# Explicit account-scoped activity actions (unsubmitted branch)

Branch: `feat/activity-actions`, based on upstream main independently of webhook
PR #349. No additional PR is open. Rebase after that PR lands and set the release
version before proposing these changes upstream.

## Behavior

`ha_strava.get_activity` takes a Strava config entry ID and activity ID. It fetches
that resource on demand using the existing coordinator's OAuth session, verifies
its athlete ID against the configured account, and returns selected automation
fields. It does not depend on a last-N activity sensor, start polling, register
webhooks, copy tokens, or persist activity responses. Photos, routes, streams,
full athlete profiles and other unnecessary response fields are omitted.

`ha_strava.edit_activity` takes the same explicit account/activity IDs and either:

- `changes`: documented fields (`name`, `description`, `sport_type`, `gear_id`,
  `trainer`, `commute`, `hide_from_home`); or
- `append_description`: an exact line block appended once while preserving notes.

`dry_run` defaults to true. Actual writes require explicit false and an OAuth token
with the necessary activity:write scope. Missing scope errors do not secretly
reauthorize or select another account. When replacing a description derived from
a previously fetched snapshot, provide `expected_description` to reject stale
edits. Do not combine append mode with replacement fields or a precondition.

Edits serialize per coordinator/account. Before PUT, a second GET checks that
modified fields still match the initial snapshot. PUT sends only changed fields,
and GET verifies the result. A cleared gear sends `none` but verifies response
null. A network failure after PUT does not automatically repeat the write.
Replaying an append fetches current notes and returns unchanged if already applied.
The API has no atomic compare-and-swap here; an external edit between the final
GET and PUT remains a narrow, unavoidable race. Exact block matching cannot
semantically deduplicate text rewritten by another service.

The existing `update_activity` and route actions are unchanged for compatibility.
They retain their current recent-cache behavior. The new names distinguish the
explicit-account, preview-capable path until upstream agrees on an API migration.
The portable client contains no AQI/UV or job-queue behavior. HA OAuth exceptions
are translated separately. Retry scheduling belongs to the enrichment consumer.

## Trust boundary and lifecycle review

- Config entry selection is explicit; unknown, disabled or unloaded entries fail.
- Legacy entries without a numeric unique athlete ID cannot use the new path.
  Do not infer an athlete from an unauthenticated event or choose a different account.
- Activity IDs are checked before forming URLs. Unicode digits, bools, floats,
  path traversal, arbitrary write fields and malformed athlete responses are rejected.
- Fetched ownership is checked before returning details and before every write.
- Helpers never log tokens, descriptions, request payloads or raw provider errors.
- Shared actions register once during domain setup. A cached client/lock belongs
  to a single coordinator and is replaced when the entry is reloaded.
- HA service permissions and trace/recorder retention still apply. These actions
  do not introduce per-person HA authorization or a general API proxy.

## TDD and validation

Initial fake-client/action specifications failed: 27 failures and one passing
negative case. Implementing account selection, typed fields, previews, verification,
and safe API operations made those green. Additional red cases covered malformed
athlete responses, missing configured identity, description preconditions, generic
append support, and numeric IDs produced by native templates.

Further checks cover a timeout after a write that already took effect, concurrent
appends preserving both notes, cleared gear normalization, disabled/unloaded
accounts, stable error categories and safe retries. All fixtures are synthetic.
Final full-suite result: **494 passed, 11 warnings** on HA 2026.10.4 / Python 3.14.
Black, isort, flake8 and `git diff --check` pass on the changed files. The existing
photo-backoff test using `datetime.now()` elapsed time failed once on a repeated
run (0.895 seconds measured against a 1-second threshold), then passed in isolation
and on the final full run. That unrelated timing test is unchanged. The existing
sensor/camera/button AsyncMock warnings also remain outside this diff.

No live activity edits or HA installation were performed for this branch.
