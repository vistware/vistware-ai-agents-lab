# Kafka Consumer Lag and Delayed Payment Processing

## Overview

This fictional incident record describes `SYN-PAY-317` in the Harbor microservices system. Every event, identifier, and measurement is invented. `payments-api` accepts asynchronous payment requests and returns HTTP 202 after durable admission. The `payments-worker` service consumes commands from Kafka topic `payment.commands.v2`, using consumer group `payment-executors` across twelve partitions.

On 2025-05-12, accepted payments remained pending while checkout requests continued succeeding. This runbook concerns delayed execution after admission; a successful HTTP 202 does not mean that money has been captured.

## Observed Symptoms

Consumer lag reached 18,400 records, and the oldest pending command was twenty-four minutes old. Customers saw “Payment processing” for longer than the normal two-minute target. The group repeatedly logged `PAY-CONSUMER-REBALANCE`, and partition ownership moved among three worker replicas.

Database pool acquisition stayed below twenty milliseconds. Broker storage utilization and produce acknowledgment latency remained normal. These observations distinguished the backlog from the [database timeout incident](payments-database-timeout.md), which disrupted request handling before clients received a reliable outcome.

## Confirmed Root Cause

A worker performed a blocking risk-service call while processing a batch of up to 1,000 records. Its `RISK_CHECK_TIMEOUT_MS=360000` exceeded `MAX_POLL_INTERVAL_MS=300000`. A single slow risk assessment could therefore prevent the next poll for longer than the group allowed.

The broker removed that consumer, reassigned its partitions, and replayed commands whose offsets had not been committed. Trace timestamps showed six-minute waits immediately before each membership loss. Increasing replicas alone did not remove this blocking call.

### Unknown and Unverified Causes

The reason for the risk-service delay remained unknown when this record was closed. A network interruption and an overloaded risk-service dependency were hypotheses without sufficient trace evidence. Responders did not classify either as a confirmed downstream outage. Broker capacity exhaustion was investigated but unsupported by the collected metrics.

## Diagnostic Procedure

1. Measure lag per partition and oldest-command age. Aggregate lag alone can hide one stalled partition.
2. Compare group membership changes with poll intervals and worker traces. Identify which processing stage holds the batch.
3. Check database checkout time and durable ledger progress before attributing every pending payment to Kafka.
4. Inspect the command's payment identifier and idempotency record before replaying it. A repeated Kafka delivery can refer to an already completed capture.

## Resolution and Recovery

Responders applied the established worker profile: `RISK_CHECK_TIMEOUT_MS=5000` and `MAX_POLL_RECORDS=50`. Timed-out assessments were recorded durably as deferred work before transfer to `payment.risk-retry.v1`. The worker acknowledged an original command only after the corresponding ledger state was durable.

With poll stability restored, operators increased workers from three to six within the twelve-partition limit. They avoided resetting offsets to the topic beginning. The backlog drained in thirty-one minutes; recovery required oldest-command age below two minutes and stable membership for fifteen minutes.

## Prevention and Related Procedures

Alert on command age as well as offset distance. Exercise a slow risk assessment during worker release checks and compare processing deadlines with the poll limit.

Use [payment idempotency rules](payments-idempotency.md) when reconciling redelivered commands. Send delayed customer updates through the [notification retry procedure](notifications-retry-policy.md), preserving the original event identity. Follow the [escalation runbook](incident-escalation.md) if pending age exceeds fifteen minutes across multiple partitions.
