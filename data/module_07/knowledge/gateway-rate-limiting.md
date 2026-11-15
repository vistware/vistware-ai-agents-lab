# Gateway Rate Limits and Unexpected HTTP 429 Responses

## Overview

This fictional runbook describes throttling in the Harbor microservices system and incident `SYN-EDGE-082`. All limits, service names, and observations are invented. `edge-gateway` maintains shared token buckets in Redis deployment `edge-quota-store`. That deployment is separate from the identity service's `session-store`.

Authenticated quotas use the principal and route identifier. The default bucket refills at two requests per second, equivalent to 120 requests per minute, with capacity for a burst of twenty. Payment submission uses thirty requests per minute with burst capacity five. Token refresh uses six requests per minute with burst capacity two.

## Observed Symptoms

During `SYN-EDGE-082`, authenticated payment clients received HTTP 429 with `EDGE-RATE-429` after approximately six submissions per minute. Responses included `Retry-After`, expressed in seconds, and `RateLimit-Remaining=0`. Rejected requests had no matching `payments-api` trace because the gateway stopped them before forwarding.

Payment processing latency, database acquisition time, and Kafka command age were normal for admitted requests. Several clients nevertheless displayed “Payment timed out,” making client-facing wording an unreliable guide to the response's actual origin.

## Confirmed Root Cause

A route-classifier configuration placed the broad `authenticated-write` rule ahead of the specific payment rule. The broad rule incorrectly selected bucket `auth-refresh`, applying the six-per-minute renewal quota to payment submissions. Bucket metadata and effective matcher order confirmed this mapping on every gateway replica.

The shared quota store was reachable throughout the incident. This was a policy-selection error, not evidence that payment consumers were slow or that sessions had expired.

### Unverified Hypotheses

An automated traffic surge was suggested early in the incident. Traffic volume stayed near its previous baseline, and no investigation established abusive activity. Some mobile clients may have amplified retries after receiving 429, but the available traces did not quantify that contribution.

## Diagnostic Procedure

1. Capture HTTP status, gateway reason code, route identifier, selected bucket, and `Retry-After`. Do not infer throttling solely from a client timeout message.
2. Check whether the request reached its backend. A gateway rejection should have no backend processing span for that attempt.
3. Compare the selected bucket with the route's expected refill rate and burst capacity. Shared counters mean that changing gateway replicas does not reset the allowance.
4. Distinguish HTTP 401 authentication rejection from HTTP 429 quota exhaustion. Dependency failure in `edge-quota-store` produces HTTP 503 with `EDGE-LIMIT-STORE-UNAVAILABLE` under the configured fail-closed policy.

## Resolution and Client Recovery

Operators restored the specific payment matcher ahead of the broad rule and verified bucket selection with synthetic traffic. They retained the configured quotas and allowed depleted buckets to refill. Payment admission returned to normal within three minutes.

Clients must honor `Retry-After` and add jitter when resuming requests. An explicitly rejected attempt was not admitted, but an earlier attempt may still have succeeded. Reuse the same payment idempotency key and payload when retrying the same purchase, following [payment deduplication rules](payments-idempotency.md).

## Prevention and Related Procedures

Include route-to-bucket checks in configuration release validation. Alert separately on quota rejections and limiter dependency failures.

Repeated refresh calls can exhaust the legitimate renewal bucket; use [session diagnostics](identity-session-management.md) to investigate their cause. An outage of [identity Redis](identity-redis-outage.md) affects a different store and requires different recovery actions. Follow the [escalation procedure](incident-escalation.md) for widespread checkout rejection.
