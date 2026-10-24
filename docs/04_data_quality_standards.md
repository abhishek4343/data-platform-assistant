# Data Quality Standards

These standards apply to every pipeline that loads data into the Snowflake RAW, CURATED and MART layers.

## Layers

- **RAW**: exact copy of the source, append-only, with load metadata columns `_LOADED_AT` and `_SOURCE_FILE`.
- **CURATED**: cleaned, typed and de-duplicated data. One row per business key, keeping the latest version by `LAST_MODIFIED_TS`.
- **MART**: business-ready models used by Tableau and Power BI dashboards.

## Mandatory checks

Every pipeline must implement these checks before data moves from RAW to CURATED:

1. **Row count reconciliation**: the number of rows loaded must match the source count or the control file. A difference of more than 0.1% fails the run.
2. **Schema drift**: compare the incoming column list with the registered schema. New columns raise a warning; missing or renamed columns fail the run.
3. **Primary key uniqueness**: no duplicate business keys in CURATED.
4. **Not-null checks** on business keys and mandatory attributes.
5. **Freshness**: each source has an expected arrival time. If data is more than 2 hours late, an alert is raised.

## De-duplication rule

To keep the latest record per key, use `ROW_NUMBER() OVER (PARTITION BY business_key ORDER BY LAST_MODIFIED_TS DESC)` and keep row number 1. Add a tie-breaker column, such as `_LOADED_AT`, so the result is deterministic.

## Quarantine

Rows that fail validation go to a `QUARANTINE` schema with the failure reason. The data owner reviews quarantined rows within one business day.

## Reporting

A daily data quality summary lists failed checks, quarantined row counts and late sources per pipeline. It is posted to the data platform channel at 08:00.
