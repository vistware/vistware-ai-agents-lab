# Incident Severity, Escalation, and Operational Ownership

## Overview

This fictional runbook defines incident response for the Harbor microservices system. All severity rules, role names, and examples are invented. It applies to identity, orders, payments, gateway, and notification services. Times are measured from the first actionable alert, and incident timelines use UTC.

An alert is evidence of a symptom, not a diagnosis. The incident record must distinguish observed impact, confirmed causes, and unverified hypotheses. A responder may begin mitigation before the underlying cause is known, provided the action and its outcome are recorded.

## Severity and Response Targets

| Severity | Operational trigger | Primary acknowledgment | Status update cadence |
| --- | --- | --- | --- |
| SEV1 | Widespread sign-in or checkout failure; confirmed duplicate captures; or financial exposure that cannot be bounded | Five minutes | Every fifteen minutes |
| SEV2 | Partial service degradation sustained for ten minutes, or payment command age above fifteen minutes across multiple partitions | Ten minutes | Every thirty minutes |
| SEV3 | Limited impact with a verified workaround and no unresolved financial exposure | Four business hours | Daily while active |

The incident commander can raise severity immediately as scope becomes clearer. A second receipt message alone is not proof of duplicate capture. A request timeout alone does not establish whether a payment committed.

## Escalation Procedure

For SEV1, page the service primary immediately. If acknowledgment is absent at five minutes, contact the secondary rotation. Assign an incident commander by ten minutes, involving the platform duty lead if that role remains vacant.

For SEV2, contact the secondary at twenty minutes without acknowledgment. Do not wait for that deadline when new evidence satisfies SEV1 criteria. For SEV3, assign a named role owner and a next review time in the issue tracker.

Use the fictional role directory rather than personal contact details. Keep request correlation identifiers, affected revisions, and aggregate counts in updates; exclude credentials, bearer tokens, and customer payment payloads.

## Responsibilities

The service primary diagnoses the affected component and proposes mitigation. The incident commander coordinates sequencing, severity changes, and status updates. The release operator executes an approved rollback or configuration correction and records the resulting revision.

The payments reconciliation owner determines whether indeterminate attempts reached capture. The communications owner describes confirmed user impact without presenting hypotheses as established facts. The scribe maintains the evidence timeline and assigns unresolved questions before handoff.

## Example: Delayed Response to a Payment Alert

### Observed Symptoms and Confirmed Cause

In fictional incident `SYN-OPS-039`, a payment error alert remained unacknowledged for nine minutes. The alerting system showed successful dispatch to rotation `payments-legacy-primary`, which had no assigned responder. A retired routing rule was the confirmed cause of the delayed acknowledgment.

### Unverified Hypotheses

A paging-provider outage was suggested but unsupported: the dispatch log showed acceptance, and the configured destination was already incorrect. The underlying payment failure required its own investigation; the paging defect did not explain payment errors.

## Recovery, Closure, and Related Procedures

Observe restored service for at least fifteen minutes and verify the affected user journey. Lower error rates alone are insufficient when payment outcomes remain uncertain. Keep reconciliation explicitly open with an owner and deadline, and retain SEV1 while financial exposure cannot be bounded.

Use [Kafka backlog recovery criteria](payments-kafka-consumer-lag.md), [database timeout diagnostics](payments-database-timeout.md), or [identity Redis recovery](identity-redis-outage.md) for component-specific checks. Apply [payment idempotency rules](payments-idempotency.md) before replaying financial work. Close the incident only after impact, unresolved work, and ownership are documented.
