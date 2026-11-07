# Legacy account reauthorization

Older Strava entries can lack a unique athlete ID. The previous reauthorization
flow compared that missing value with the newly authorized athlete and rejected
the correct account. Successful reauthorization also replaced the entire data
mapping, dropping webhook and other settings absent from the OAuth response.

The fix checks the legacy entry's authenticated saved-token/coordinator identity,
then assigns the missing unique ID only after the new profile matches. Missing,
conflicting or wrong identities abort. An existing entry for that athlete cannot
be duplicated. Identified accounts retain the normal unique-ID mismatch guard.
The profile request is bounded and malformed/unavailable responses abort without
changing the existing token. Entry updates preserve webhook data, arbitrary
existing settings and options; no storage file is edited directly.

Regression tests cover legacy and identified entries, cached identity, unknown
and wrong accounts, duplicate identities, malformed profiles and request failures.
Two tests run HA's native reauthorization flow manager and OAuth exchange through
to the saved entry, checking preservation of settings and that no entry is added.
All credentials, accounts and provider records in the tests are synthetic.

This branch is queued after webhook PR #349, whose authenticated identity helper
it reuses. Rebase onto the merged upstream commit and choose the next release
version before opening the separate fix PR. The initial fix was verified live;
the additional profile-failure hardening has only been tested locally.
