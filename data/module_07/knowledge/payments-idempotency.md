# Duplicate Payment Requests and Idempotency Keys

## Overview

This fictional runbook covers duplicate-request handling in the Harbor microservices system and incident `SYN-PAY-338`. Every identifier, retention period, and outcome is invented. `payments-api` requires an `Idempotency-Key` for payment submission. The key identifies one intended operation, not one network attempt.

Records reside in PostgreSQL alongside the payment ledger, independently of the identity service's Redis session store. Their uniqueness scope is merchant identifier, operation type, and key. A browser-generated key such as `demo-purchase-028-attempt-a` is only a synthetic example, not an authentication credential.

## Observed Symptoms

During `SYN-PAY-338`, customers retried checkout after an HTTP 504 and later saw two captures for one purchase reference. Ledger reconciliation confirmed duplicate captures for two synthetic purchases. Other reports involved repeated receipt messages without repeated ledger captures.

The API recorded different idempotency keys for the confirmed duplicate requests. Several same-key retries instead returned HTTP 202 because the original operation was still processing; this response alone was not a duplicate-payment failure.

## Confirmed Root Cause

A client release generated a new key whenever it retried a timed-out submission. Two original requests had committed before their responses were lost. Their retries used different keys and were admitted as new operations, producing additional captures.

The uniqueness constraint behaved as configured. It prevented duplicate execution within a key's scope but did not merge different keys merely because they shared a purchase reference. The client retry policy was the confirmed defect for the two reconciled purchases.

### Unverified Hypotheses and Unresolved Outcomes

Kafka redelivery and notification duplication were considered separately. No replayed command caused the two confirmed extra captures. Two other purchase references remained under reconciliation because adapter acknowledgments were unavailable. Exposure was bounded to at most one additional capture per reference; their final financial outcomes remained unknown.

## Request Handling Rules

- Missing key: reject with HTTP 400 and `PAY-IDEM-400` before admitting work.
- Same key and canonical payload while processing: return HTTP 202 with `PAY-IDEM-202` and `Retry-After=2`.
- Same key and payload after completion: return the stored terminal result without another capture.
- Same key with changed canonical payload: return HTTP 409 and `PAY-IDEM-409`; do not overwrite the existing record.

Canonical payload comparison includes `amount_minor`, currency, and `purchase_ref`; transport trace identifiers are excluded. Terminal success and decline records remain for twenty-four hours after completion. Processing or uncertain records do not expire automatically while reconciliation is open. After terminal-record expiry, reusing an old key may admit new work and requires checking the durable purchase ledger first.

## Diagnostic and Resolution Procedure

1. Collect purchase reference, operation identifier, key, payload fingerprint, and response status without recording payment instrument details.
2. Compare keys and fingerprints across attempts. Trace a timeout through the ledger rather than assuming rollback.
3. Keep the original key and payload for retries within retention. For uncertain or expired records, pause automatic resubmission and assign the reconciliation owner.
4. Preserve the original operation identifier when handling Kafka redelivery. Commit command offsets only after durable ledger progress.

Responders restored stable client keys and reconciled the two confirmed extra captures through the standard reversal workflow. Repeated concurrent submissions with one key then produced one financial operation in a controlled exercise.

## Related Incidents

Combine [database timeout diagnostics](payments-database-timeout.md) with this runbook when a client cannot determine whether submission committed. Use [consumer lag recovery](payments-kafka-consumer-lag.md) for pending commands and [notification deduplication](notifications-retry-policy.md) for repeated receipts. Apply the [escalation rules](incident-escalation.md) immediately for confirmed duplicate captures or unbounded financial exposure.
