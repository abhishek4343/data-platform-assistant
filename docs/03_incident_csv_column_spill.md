# Incident Report INC-2077: Column Spill in Customer Accounts File

Severity: P3. Duration: 1 day (detected the morning after load). Affected pipeline: `crm_accounts_sftp`.

## Summary

The nightly customer accounts CSV from the CRM vendor contained free-text address values with unescaped commas. Values shifted one or more columns to the right ("column spill"), so city names landed in the postcode column and some balances were loaded as text. The load itself succeeded, which is why the problem was not caught immediately.

## Detection

A business analyst noticed postcodes containing city names in a dashboard. A query on the RAW table showed 312 out of 48,000 rows where the `POSTCODE` column failed the expected pattern, and 41 rows where `BALANCE` could not be cast to a number.

## Root cause analysis

The vendor changed their export tool and stopped wrapping text fields in double quotes. The pipeline used a simple comma split without quote handling, and there was no row-level validation of column counts or data types before loading.

## Resolution

1. The affected rows were deleted from RAW and reloaded after the vendor re-sent a correctly quoted file.
2. The file parser was switched to a proper CSV reader with quote and escape handling.

## Preventive actions

1. Validate the column count of every row before loading; rows with the wrong count go to a quarantine table instead of RAW.
2. Add type and pattern checks for key columns (postcode pattern, numeric balance, valid dates).
3. Fail the load if more than 0.5% of rows are quarantined, and alert the on-call engineer.
4. Agree a file specification with the vendor that requires quoted text fields.
