# Redis Unavailability During Session Validation

## Overview

This fictional runbook covers incident `SYN-ID-259` in the Harbor microservices system. All names, observations, and configuration revisions are synthetic. `identity-core` uses Redis deployment `session-store` for session metadata and refresh-token rotation records. Protected requests require both a valid access JWT and a successful active-session check.

On 2025-06-11, session lookups failed even though access-token signatures remained valid. New sign-ins, token renewal, and protected account requests were affected. Public catalog browsing continued because it did not require a user session.

## Observed Symptoms

The identity service returned HTTP 503 with `SESSION-STORE-UNAVAILABLE`. Its session lookup latency reached the 250-millisecond connection deadline, and `session_store_connect_failures_total` increased across every identity replica. One older gateway revision translated this dependency failure into a generic HTTP 401, so some users saw an inaccurate sign-in prompt.

Redis reported normal memory use and no increase in evictions. A diagnostic workload outside the identity deployment could connect successfully. This did not prove that identity replicas had the same network access.

## Confirmed Root Cause

Network policy revision `session-access-v18` allowed incoming Redis connections from workloads labeled `app=identity-edge`. Actual identity workloads carried `app=identity-core`. The policy therefore removed their access while leaving the Redis process healthy.

Responders compared the effective policy selectors with identity workload labels. Connectivity failed from an affected identity replica and succeeded after restoring the previous policy. This evidence confirmed a network authorization error, rather than Redis memory exhaustion or expired session records.

### Unknowns and Unverified Hypotheses

A Redis leader failure and a signing-key rotation problem were suggested but unsupported by role metrics and JWT validation results. Four refresh requests lost their responses near the policy transition. Whether their rotations committed before connectivity was interrupted remained unknown until reconciliation; a connection failure alone did not establish the outcome.

## Diagnostic Procedure

1. Separate signature validation from session lookup in the request trace. `unknown_kid` requires the [JWT rotation procedure](identity-jwt-validation.md), not a Redis restart.
2. Check Redis role, memory, eviction count, and connection metrics. Test connectivity from the actual identity workload context.
3. Compare workload labels, network policy revisions, and the start of connection failures. Avoid treating a successful operator diagnostic connection as universal reachability.
4. Distinguish a completed lookup returning no session from an unavailable lookup. The former can justify `session_expired`; the latter requires a dependency error.

## Resolution and Recovery

The platform responder restored `session-access-v17`, then verified connections from every identity replica. The gateway operator corrected the legacy error mapping to preserve HTTP 503 for unavailable session storage. Signature checks and active-session enforcement remained enabled.

Responders did not restore an old Redis snapshot, because that could reintroduce revoked sessions. They inspected rotation records for the four uncertain refresh requests and required fresh sign-in where the current token family could not be established safely.

## Verification and Related Procedures

Recovery required successful sign-in, refresh, protected access, and revoked-session rejection across all replicas, followed by fifteen minutes without connection failures. The policy release checklist now includes a connectivity check from the selected application identity.

Use [session management](identity-session-management.md) for idle expiration and replay handling. The gateway's [rate-limit store](gateway-rate-limiting.md) is a separate Redis deployment; resetting its buckets cannot restore identity sessions. Follow [incident escalation](incident-escalation.md) for widespread authentication disruption.
