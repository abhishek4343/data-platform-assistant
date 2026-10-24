# On-call and Escalation Guide

## On-call rotation

One data engineer is on call each week, Monday 09:00 to Monday 09:00. The on-call engineer acknowledges alerts within 15 minutes during business hours and within 30 minutes outside business hours.

## Severity levels

- **P1**: a regulatory or client-facing report will miss its deadline, or data is materially wrong in production. Start a bridge call immediately and inform the platform lead.
- **P2**: a critical pipeline has failed or is more than 2 hours late, but there is still time to recover before the business deadline.
- **P3**: non-critical pipeline failure or data quality issue with limited business impact. Fix within the next business day.

## Triage checklist

1. Find where the failure happened: which pipeline, which step or processor.
2. Ask what changed: incoming data, source endpoint, code, or configuration. Check recent deployments and change tickets.
3. Read the logs. If there are no logs, reproduce the failing step manually in the same environment.
4. Fix, re-run, and verify the data downstream (row counts and key totals).
5. Prevent recurrence: add an alert, a retry, or a validation check, and write an incident report for P1 and P2 incidents.

## Communication

Post an update in the incident channel every 30 minutes for P1 and every hour for P2 until resolved. Include the impact, the current status and the next update time.

## Handover

At the end of the on-call week, the engineer writes a short handover note listing open incidents, recurring alerts and suggested improvements.
