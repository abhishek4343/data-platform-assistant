"""Create and fill a synthetic pipeline_runs table (last 30 days) for the agent's SQL tool.

Run:  python src/seed_runs.py
Safe to re-run: the table is rebuilt each time. Data is random but reproducible (fixed seed).
"""
import random
from datetime import date, datetime, time, timedelta

from db import connect

PIPELINES = {
    # name: (schedule hour, typical minutes, typical rows, failure rate)
    "market_data_api_daily": (6, 12, 250_000, 0.20),
    "crm_accounts_sftp": (2, 9, 48_000, 0.10),
    "trades_nifi": (1, 8, 1_200_000, 0.05),
    "positions_nifi": (1, 15, 800_000, 0.08),
    "risk_reports_mart": (7, 20, 5_000, 0.10),
}
ERRORS = {
    "market_data_api_daily": ["ReadTimeout on vendor API call", "HTTP 503 from vendor API"],
    "crm_accounts_sftp": ["Column count mismatch: 312 rows quarantined", "SFTP file not found"],
    "trades_nifi": ["Unable to execute SQL select query", "Queue back-pressure timeout"],
    "positions_nifi": ["Unable to execute SQL select query", "COPY INTO failed: number of columns does not match"],
    "risk_reports_mart": ["Upstream dependency late: positions_nifi", "Row count reconciliation failed (0.4% diff)"],
}

SCHEMA = """
DROP TABLE IF EXISTS pipeline_runs;
CREATE TABLE pipeline_runs (
    run_id           BIGSERIAL PRIMARY KEY,
    pipeline         TEXT        NOT NULL,
    run_date         DATE        NOT NULL,
    status           TEXT        NOT NULL CHECK (status IN ('success', 'failed')),
    started_at       TIMESTAMP   NOT NULL,
    duration_min     NUMERIC(6,1) NOT NULL,
    rows_loaded      INT         NOT NULL,
    rows_quarantined INT         NOT NULL,
    error_message    TEXT
);
"""


def generate(days: int = 30, seed: int = 7) -> list[tuple]:
    rng = random.Random(seed)
    today = date.today()
    rows = []
    for offset in range(days, 0, -1):
        day = today - timedelta(days=offset)
        for name, (hour, minutes, volume, fail_rate) in PIPELINES.items():
            failed = rng.random() < fail_rate
            started = datetime.combine(day, time(hour, rng.randint(0, 20)))
            duration = round(max(1.0, rng.gauss(minutes, minutes * 0.2)), 1)
            loaded = 0 if failed else int(rng.gauss(volume, volume * 0.05))
            quarantined = 0 if failed else max(0, int(rng.gauss(volume * 0.0005, volume * 0.0003)))
            error = rng.choice(ERRORS[name]) if failed else None
            rows.append((name, day, "failed" if failed else "success", started, duration, loaded, quarantined, error))
    return rows


def main() -> None:
    rows = generate()
    with connect() as conn:
        conn.execute(SCHEMA)
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO pipeline_runs (pipeline, run_date, status, started_at, duration_min,
                                              rows_loaded, rows_quarantined, error_message)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                rows,
            )
    failed = sum(r[2] == "failed" for r in rows)
    print(f"pipeline_runs: {len(rows)} runs stored ({failed} failed) for {len(PIPELINES)} pipelines.")


if __name__ == "__main__":
    main()
