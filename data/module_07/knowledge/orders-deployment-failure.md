# Order Creation Failures After a Configuration Deployment

## Overview

This fictional incident report describes `SYN-ORD-114` in the Harbor microservices system. All identifiers, timings, and configuration values are synthetic. The `orders-api` service creates orders and contacts `payments-api` through a named routing profile. On 2025-06-03, a deployment introduced HTTP 500 responses for new checkout orders while order-history reads remained available.

The new release used the same application image as the preceding release. Only the deployment configuration changed. This distinction helped responders investigate runtime settings without assuming that an application binary regression had occurred.

## Observed Symptoms

Forty percent of order-creation requests returned `ORD-CONFIG-500`. The affected replicas logged `PAYMENT_PROFILE_NOT_FOUND` before opening an outbound connection. Existing orders remained readable, and the process health endpoint returned HTTP 200.

Payment service dashboards showed normal latency and no corresponding increase in incoming order requests. Clients occasionally retried checkout and received another 500 from the same replica. Requests routed to older replicas succeeded with the same synthetic test account and basket.

## Confirmed Root Cause

The deployment set `PAYMENTS_ENDPOINT_PROFILE=mesh-v3`, but the release's profile catalog contained only `mesh-v2`. The order-creation handler resolved this setting lazily on its first payment call. Basic readiness checked the process and order database, so replicas entered service before the missing profile was detected.

Responders compared effective configuration across old and new replicas and reproduced the error using the unsupported profile. `PAYMENTS_CLIENT_TOKEN_SOURCE=workload` was correct on both generations. The confirmed problem was selecting a nonexistent route profile, rather than an expired service credential or unavailable payment backend.

### Unverified Hypotheses

An expired JWT, database pool exhaustion, and a broken service route were initial hypotheses. Signature diagnostics and order database metrics were normal. Traces showed no attempted payment connection, so downstream network failure could not explain these requests. No evidence linked the deployment to the earlier payment database incident.

## Diagnostic Procedure

1. Group failures by replica and deployment revision. Compare order creation with order-history reads to establish the affected path.
2. Read the effective `PAYMENTS_ENDPOINT_PROFILE`, not only the source manifest. Compare it with the profile catalog bundled with that release.
3. Check whether a payment client span exists. Missing outbound spans plus `PAYMENT_PROFILE_NOT_FOUND` identify failure before remote execution.
4. Match the order's purchase reference with the payment ledger before advising a retry. Other failure modes may reach the payment service and lose the response.

## Resolution and Recovery

The release operator halted the rollout and restored `PAYMENTS_ENDPOINT_PROFILE=mesh-v2`. A canary then completed order creation, payment admission, and order-history retrieval using a synthetic purchase. Responders resumed traffic only after the canary's effective configuration matched the verified profile.

The application image remained unchanged during recovery. Error rates fell below one percent within seven minutes. Responders observed the repaired generation for fifteen minutes before completing the rollout.

## Prevention and Related Incidents

The deployment checklist now requires validating named profiles before accepting traffic and exercising an order-creation transaction on the canary. A process liveness response alone is insufficient evidence that checkout dependencies are configured correctly.

For post-admission payment delays, consult [consumer lag diagnostics](payments-kafka-consumer-lag.md). For uncertain payment outcomes after a retry, apply [idempotency rules](payments-idempotency.md). Assign release rollback and incident coordination responsibilities according to the [escalation runbook](incident-escalation.md).
