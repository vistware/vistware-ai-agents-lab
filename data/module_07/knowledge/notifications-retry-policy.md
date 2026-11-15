# Notification Retries and Duplicate Delivery Prevention

## Overview

This fictional runbook covers `notification-dispatcher` in the Harbor microservices system and incident `SYN-NOT-063`. All identifiers, policies, and outcomes are invented. The dispatcher receives order and payment events, then sends email or push notifications through a fictional delivery adapter. Delivery failure does not reverse a payment or cancel an order.

Each logical notification has a deduplication tuple of `event_id`, channel, and `template_revision`. The dispatcher retains that tuple for thirty days and assigns one stable `delivery_id` to its delivery attempts. A legitimate resend with changed content requires an explicitly approved new template revision or event.

## Observed Symptoms

During `SYN-NOT-063`, customers reported two payment receipt messages for one purchase. Eleven synthetic delivery records showed two adapter acceptances associated with the same logical notification. Payment ledger inspection showed one capture per corresponding purchase reference.

The retry queue grew after the adapter intermittently returned HTTP 503 or closed connections without an acknowledgment. This was different from two independent payment requests producing separate financial operations; message count alone could not establish duplicate charging.

## Confirmed Root Cause

A dispatcher release generated a new `delivery_id` for each transport retry. When the adapter accepted the first attempt but its acknowledgment was lost, the next attempt appeared to be a new delivery. Event-level deduplication prevented a second queue entry but did not stop retries within the existing entry from using new identifiers.

Correlated acceptance records confirmed this sequence for eleven notifications. Three additional deliveries had no definitive acceptance record from their first attempt; whether they produced duplicates remains unknown pending reconciliation.

### Unverified Hypotheses

Duplicate Kafka events and repeated payment captures were considered. The affected records had one logical notification entry, and the checked ledger entries contained one capture. These observations did not support either hypothesis for the confirmed set.

## Retry Policy

### Transient and Permanent Failures

Retry connection failures, HTTP 408, HTTP 429, and HTTP 5xx responses. Stop automatic delivery for HTTP 400, 401, 403, or 422 and record the rejection reason for operator review. A 401 may require restoring adapter authorization before an approved replay.

Allow six total attempts, including the initial send. The five retry ceilings are ten, twenty, forty, eighty, and 120 seconds, controlled by `NOTIFY_BACKOFF_BASE_SECONDS=10` and `NOTIFY_BACKOFF_CAP_SECONDS=120`. Draw each delay randomly between zero and its ceiling. If the adapter supplies a valid `Retry-After`, use it as the minimum wait, even when it exceeds the backoff cap.

### Unknown Acceptance

An interrupted response means acceptance is unknown. Retain the same `delivery_id`; the fictional adapter deduplicates that identifier for thirty days. Do not generate a new identifier to make a retry appear fresh. After the final failed attempt, move the record to `notification.review` with its attempt history.

## Resolution and Verification

Responders restored stable delivery identifiers and paused manual replays until they checked adapter acceptance records. A controlled lost-acknowledgment exercise then produced one recipient delivery across repeated attempts. The three unresolved records remained assigned to the notification owner; they were not reported as confirmed duplicates or confirmed successes.

## Related Procedures

Before replaying events older than thirty days, review the expired deduplication window. Consult [payment idempotency](payments-idempotency.md) when duplicate receipts raise concerns about duplicate captures. Inbound [gateway throttling](gateway-rate-limiting.md) is separate from adapter-side 429 responses. Use the [escalation runbook](incident-escalation.md) when delays affect required customer updates.
