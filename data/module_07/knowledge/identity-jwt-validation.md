# JWT Validation Failures After Signing Key Rotation

## Overview

This fictional incident record describes `SYN-ID-241` in the Harbor microservices system. All identifiers, measurements, and events are invented. On 2025-04-08, `identity-core` began signing access tokens with key identifier `sig-r32` at 09:10 UTC. Several API services continued accepting older tokens but rejected newly issued tokens for eighteen minutes.

Access tokens are signed JWTs with an eight-minute lifetime. Services validate the issuer, audience, expiry, and signature using a cached JSON Web Key Set, abbreviated JWKS. A successful signature check does not establish that the associated user session remains active.

## Observed Symptoms

- Protected requests returned HTTP 401 with `AUTH-JWT-013` and reason `unknown_kid`.
- Newly signed-in users failed immediately, while some existing sessions continued working until their next token refresh.
- The `jwt_unknown_key_total` counter increased only on replicas using the older JWKS cache generation.
- Session-store connectivity and token issuance latency remained normal.

The same browser displayed a generic “Please sign in again” message for both this failure and ordinary session expiry. The response reason and validation stage were therefore more useful than the visible message.

## Confirmed Root Cause

The new public key was published at the same time that signing switched to `sig-r32`. Validators used `JWKS_CACHE_TTL_SECONDS=3600` and did not refresh their cache when they encountered an unknown key identifier. Replicas that had fetched keys before 09:10 could not validate the new signatures.

Responders confirmed the cause by comparing the published key identifiers with each replica's cache metadata. Both `sig-r31` and `sig-r32` were present in the published JWKS; affected replicas held only `sig-r31`. This was a key-discovery failure, not evidence that a private signing key had leaked.

### Unverified Hypotheses

Clock drift and an incorrect audience were considered initially. Recorded clock offsets remained below two seconds, and sampled audience values matched the configured audience. Neither hypothesis explained the selective `unknown_kid` errors. No evidence established malicious token forgery.

## Diagnostic Procedure

1. Record the failing request's correlation identifier, service replica, error reason, and token `kid`. Do not copy the bearer token into incident notes.
2. Compare the `kid` with the published public-key inventory and the replica's cached inventory.
3. Check issuer, audience, `exp`, and clock offset separately. An expired token should produce `token_expired`, not `unknown_kid`.
4. If signature validation succeeds, continue with [session lifecycle diagnostics](identity-session-management.md) or the [Redis outage procedure](identity-redis-outage.md), depending on the session lookup result.

## Resolution and Verification

Responders verified the public-key inventory and invalidated JWKS caches through the controlled cache-refresh operation. They confirmed that every replica loaded `sig-r32` before resuming the rotation schedule. Signature checks and session checks remained enabled throughout recovery.

Synthetic sign-in, refresh, and protected-resource requests succeeded across all replicas by 09:28 UTC. The incident was marked recovered after fifteen minutes without another `AUTH-JWT-013` failure.

## Prevention and Related Incidents

Publish a replacement public key at least seventy minutes before activating its signer, covering the sixty-minute cache lifetime and a ten-minute margin. Retain the previous public key for at least the eight-minute token lifetime plus sixty seconds of permitted clock skew after its final issuance. Record both deadlines in the rotation checklist.

Use the [escalation procedure](incident-escalation.md) if authentication failures become widespread. Changing session idle limits does not resolve an unknown signing key.
