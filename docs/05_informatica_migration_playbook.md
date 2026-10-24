# Playbook: Migrating Legacy Informatica Workflows

This playbook describes how legacy Informatica PowerCenter workflows are migrated to cloud-native pipelines (Python and NiFi ingestion, SQL transformations in Snowflake).

## Step 1: Inventory and analysis

For each workflow, document the sources, targets, transformations, schedule, dependencies and average runtime. Identify dead logic (mappings whose output is no longer used) so it is not migrated.

## Step 2: Rebuild

Rebuild ingestion in NiFi or Python and transformations as SQL in Snowflake. Keep business logic identical in the first release; optimisations come later. Parameterise environment-specific values (hosts, schemas, credentials) instead of hard-coding them.

## Step 3: Parallel run and reconciliation

Run the old and new pipelines in parallel for at least five business days. Reconcile the outputs:

- row counts per table and per load date
- sums of key numeric columns (for example notional and quantity)
- a full row-level comparison using `EXCEPT` in both directions on a sample of dates

Any difference must be explained and signed off by the data owner.

## Step 4: Cutover

Agree the cutover date with downstream consumers. Switch consumers to the new tables, disable the Informatica workflow but keep it available for two weeks as a rollback option, then decommission it.

## Lessons learned

- Most migration defects come from implicit behaviour in Informatica, such as default date formats, trimming of strings and null handling. Check these explicitly.
- Reconciliation queries should be reusable; store them with the pipeline code.
- Track progress per workflow: analysed, rebuilt, in parallel run, reconciled, cut over.
