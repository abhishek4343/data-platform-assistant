# Runbook: NiFi Ingestion into Snowflake

Owner: Data Platform team. Applies to all Apache NiFi flows that land source data in the Snowflake RAW layer.

## Architecture overview

Every source system has one NiFi process group. Database sources use the QueryDatabaseTable processor with a maximum-value column (usually `LAST_MODIFIED_TS`) so each run only pulls new or changed rows. File sources arrive by SFTP and are picked up by ListSFTP and FetchSFTP. All flows write Parquet files to the internal stage and finish with a `COPY INTO` command into the RAW schema.

Flows run every 15 minutes during business hours and hourly overnight. Concurrent Tasks on QueryDatabaseTable is kept at 1 to avoid duplicate reads; downstream processors such as ConvertRecord and PutFile can run with 4 concurrent tasks.

## How incremental loading works

QueryDatabaseTable stores the last seen maximum value of the watermark column in processor state. On the next run it only selects rows where the column is greater than that value. On the very first run the state is empty, so the processor performs a full load of the table.

To force a full reload, stop the processor, open "View state", click "Clear state", and start it again. Always tell the downstream data owners before doing this, because a full reload can take several hours for large tables such as `TRADES` and `POSITIONS`.

## Common failures and fixes

- **Processor shows a red bulletin "Unable to execute SQL select query"**: the source database credentials expired or the network path is down. Check the DBCPConnectionPool controller service, then test connectivity from the NiFi node.
- **COPY INTO fails with "Number of columns in file does not match"**: the source file changed shape. Check the schema-drift section of the data quality runbook before forcing a load.
- **Queue back-pressure (connection shows red)**: downstream is slower than upstream. Increase concurrent tasks on the slow processor or temporarily raise the back-pressure threshold to 20,000 flow files.

## Escalation

If a flow has failed for more than two consecutive runs, page the on-call data engineer through the incident channel. Source-system outages are escalated to the owning application team with the run ID and the exact error from the bulletin board.
