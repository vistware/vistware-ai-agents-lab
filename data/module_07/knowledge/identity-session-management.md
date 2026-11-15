# Session Expiration and Refresh Token Failures

## Overview

This fictional runbook covers browser authentication in the Harbor microservices system and incident `SYN-ID-248`. All service names, policies, and observations are synthetic. `identity-core` issues eight-minute access JWTs and rotating refresh tokens. Session metadata resides in the Redis deployment named `session-store`.

A session expires after thirty minutes without authenticated activity or twelve hours after sign-in, whichever comes first. Each refresh token has a seven-day expiry, but it cannot extend those session limits. A cryptographically valid access token is rejected when its referenced session has expired or been revoked.

## Observed Symptoms

During `SYN-ID-248`, users with several browser tabs saw intermittent sign-outs shortly after a successful refresh. Protected requests returned HTTP 401 with `AUTH-SESSION-021`; refresh requests reported `refresh_replayed`. Other users received `session_expired` after leaving a tab inactive overnight, which was expected behavior.

The incident affected twelve percent of active synthetic browser sessions. Redis latency remained below four milliseconds, and JWT signature checks succeeded. Repeating sign-in temporarily restored access until another concurrent refresh occurred.

## Confirmed Root Cause

Two browser tabs submitted the same single-use refresh token with different `refresh_attempt_id` values. The first request rotated the token. The second looked like reuse of an already consumed credential and revoked the refresh-token family, including the current session.

An identical retry carrying the same attempt identifier is permitted for three seconds and returns the previously recorded rotation result. That allowance did not apply because each tab generated its own identifier. Correlated rotation records confirmed this ordering; ordinary access-token expiration did not cause the family revocation.

### Unverified Hypotheses

Responders initially suspected cookie loss and session-store eviction. Browser diagnostics showed the cookie was present, and Redis eviction counters did not increase. The record does not establish whether every reported sign-out shared the refresh race; four reports lacked correlation identifiers and remain unclassified.

## Diagnostic Procedure

1. Identify whether the failing operation is access validation, token renewal, or session lookup. Capture reason codes without recording cookies or refresh-token values.
2. Check the session's creation time, last authenticated activity, and revocation reason. Distinguish idle expiration from the absolute twelve-hour limit.
3. Compare rotation sequence numbers, attempt identifiers, and timestamps across tabs. A consumed token followed by family revocation supports replay detection.
4. Check for HTTP 429 responses before investigating token lifetime. A refresh loop may trigger the separate [gateway quota](gateway-rate-limiting.md).
5. If session lookup times out, follow the [Redis outage runbook](identity-redis-outage.md). A missing signing key instead requires [JWT validation diagnostics](identity-jwt-validation.md).

## Resolution

The browser team restored the previous release, which coordinated renewal through a single refresh owner across tabs. Transport retries retained their original attempt identifier. Responders did not disable replay detection or increase session lifetimes.

Users whose token families were already revoked had to sign in again. Sessions that reached their idle or absolute deadline also required new authentication; refreshing the page could not revive them. After rollback, a twenty-minute multi-tab exercise completed without unintended family revocation.

## Prevention and Operational Notes

Monitor `refresh_family_revoked_total` separately from expected `session_expired` responses. Exercise concurrent tabs, delayed responses, and lost refresh acknowledgments before releasing browser authentication changes. Treat an unavailable session backend as a dependency failure rather than proof that the user supplied an invalid password.

For broad login disruption, apply the [incident severity rules](incident-escalation.md). Keep unresolved reports explicitly separate from sessions whose revocation sequence has been confirmed.
