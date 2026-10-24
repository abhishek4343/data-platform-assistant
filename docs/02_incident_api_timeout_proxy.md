# Incident Report INC-2041: Market Data API Ingestion Failed at Startup

Severity: P2. Duration: 3 hours 40 minutes. Affected pipeline: `market_data_api_daily`.

## Summary

The daily market data ingestion job failed immediately on its first POST call to the vendor API. Because the failure happened before the pipeline's logging was initialised, no pipeline logs were produced and the scheduler only showed exit code 1. Downstream risk reports for the morning were delayed by about two hours.

## Detection

The job scheduler raised a job-failure alert at 06:05. The on-call engineer found no application log for the run, which made the usual log-based triage impossible.

## Root cause analysis

The engineer obtained temporary access to run the Python extraction script manually on the production host. Running it interactively surfaced a `ReadTimeout` on the very first request. All outbound calls from the production network must go through the corporate outbound proxy. A configuration change released the previous evening had set the proxy port incorrectly in the job's config file, so every request timed out instead of reaching the vendor.

## Resolution

The proxy port was corrected in the configuration, the job was re-run manually, and the data was loaded by 09:45. Downstream reports were then refreshed.

## Preventive actions

1. Initialise logging before any network call, so startup failures are always captured.
2. Add a retry with exponential backoff (3 attempts) around vendor API calls.
3. Add an alert that fires when a job exits without writing a log file.
4. Add a pre-deployment check that validates proxy host and port values against the approved list.

## Lessons learned

When logs are missing, reproduce the failing step manually in the same environment. Always ask what changed recently: the incoming data, the endpoint, the code, or the configuration.
