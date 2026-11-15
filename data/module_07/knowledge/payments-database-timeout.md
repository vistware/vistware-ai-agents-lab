# Database Connection Pool Exhaustion in Payment Requests

## Overview

This fictional operational record covers incident `SYN-PAY-326` in the Harbor microservices system. All technical settings and observations are invented. The synchronous `payments-api` service records payment attempts in the PostgreSQL database `payments_store`. Eight API replicas each allow twelve database connections, leaving twenty-four connections reserved within the API database role's limit of 120.

On 2025-05-19, a receipt-enrichment release caused HTTP 504 responses during payment submission. Some clients described the result as “checkout frozen,” although the immediate failure was waiting for a database connection rather than waiting for a Kafka consumer.

## Observed Symptoms

The API returned `PAY-DB-POOL-017` after its 750-millisecond pool-acquisition deadline. `db_pool_in_use` stayed at twelve on each affected replica, while `db_pool_waiters` rose sharply. Request latency approached the gateway timeout and successful throughput fell by sixty percent.

Database CPU remained at thirty-five percent. Several sessions appeared as `idle in transaction`, and query execution time itself remained normal. Kafka's oldest-command age stayed below two minutes during the first ten minutes of the incident.

## Confirmed Root Cause

The new receipt lookup held an open database transaction while waiting as long as twelve seconds for an external receipt response. Connections remained checked out during that network wait. At the observed arrival rate, all ninety-six API connections became occupied, leaving new requests queued until acquisition timed out.

Responders matched connection checkout spans to receipt-call spans and reproduced the behavior with a deliberately delayed receipt response. The database was reachable; neither a slow SQL query nor the configured connection count alone explained the incident.

### Unverified Hypotheses

A database lock storm and excessive Kafka replay were considered. Lock-wait metrics and consumer progress did not support those explanations. The receipt service's own reason for responding slowly was not established in this investigation and remains unknown.

## Diagnostic Procedure

1. Compare connection acquisition time with query execution time. `PAY-DB-POOL-017` identifies pool waiting, not necessarily SQL execution failure.
2. Count active connections across every API replica and inspect transaction age. Include rollout overlap when checking the database role's connection budget.
3. Correlate long checkouts with outbound calls and record transaction identifiers without copying payment payloads.
4. Find each timed-out request using its original idempotency key or purchase reference. A client timeout does not establish whether an earlier transaction committed.
5. If API admission is healthy but commands remain pending, use the [Kafka lag procedure](payments-kafka-consumer-lag.md) instead.

## Resolution

Responders set `PAYMENT_RECEIPT_LOOKUP_IN_TX=false` through the existing emergency feature switch. This disabled optional receipt enrichment and restored the previously verified transaction path. Connections drained as outstanding receipt calls reached their deadlines.

Operators did not raise every pool limit: eight pools of twenty would exceed the API role's total allowance before reserving operational headroom. They reconciled indeterminate payment attempts under the [idempotency procedure](payments-idempotency.md), retaining the original key for retries.

## Verification and Prevention

Recovery required pool acquisition below fifty milliseconds at the ninety-fifth percentile, no growing waiter queue, and fewer than one percent payment request errors for fifteen minutes. Twenty-seven timed-out attempts were reconciled; the ledger showed one capture per purchase reference in that set.

Release checks now include delayed receipt responses and connection-hold duration. Use the [escalation procedure](incident-escalation.md) if reconciliation cannot bound financial exposure, even after request latency returns to normal.
