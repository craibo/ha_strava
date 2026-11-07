# Explicit account-scoped activity actions

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
- Activity IDs are canonical positive ASCII IDs, checked before forming URLs. Unicode digits, bools, floats,
  path traversal, arbitrary write fields and malformed athlete responses are rejected.
- Fetched ownership is checked before returning details and before every write.
- Helpers never log tokens, descriptions, request payloads or raw provider errors.
- Shared actions register once during domain setup. A cached client/lock belongs
  to a single coordinator and is replaced when the entry is reloaded.
- Before every request, the coordinator checks that its entry still exists,
  remains enabled, has the same identity, and has not been unloaded or replaced.
  This prevents a pending PUT after a source transition; it cannot retract a
  request the provider has already accepted.
- Description preconditions are checked again immediately before PUT, including
  when the edited field is different. Sports and gear identifiers are validated
  locally. Malformed upstream descriptions abort without writing.
- HA service permissions and trace/recorder retention still apply. These actions
  do not introduce per-person HA authorization or a general API proxy.

## Validation

The regression suite covers preview/write isolation, shared-account ownership,
HA service registration, malformed inputs, stale descriptions, concurrent appends,
uncertain-write retries, source unload/replacement, and OAuth/provider failures.
A local HTTP server exercises the actual form-encoded GET/GET/PUT/GET path.
All fixtures are synthetic; no real accounts, tokens, routes or activities are included.

The full suite passes 516 tests on HA 2026.10.4 / Python 3.14, with 11 existing
AsyncMock warnings. Black, isort, flake8, Pylint error checks for the new modules,
and local hassfest pass. A broader HA-version runtime matrix has not been run.
The independent photo-retry test fix is included for deterministic validation;
[PR #353](https://github.com/craibo/ha_strava/pull/353) identifies that dependency so it can be removed from the final diff.
