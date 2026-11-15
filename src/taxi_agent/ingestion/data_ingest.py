import duckdb

from taxi_agent.config import config

db_file = config["data"]["db_file"]
base_url = config["data"]["base_url"]
files = config["data"]["files"]

con = duckdb.connect(db_file)

try:
    # Track successfully ingested files
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_log (
            source_file VARCHAR PRIMARY KEY,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    for file in files:
        url = f"{base_url}/{file}"

        exists = con.execute(
            "SELECT 1 FROM ingestion_log WHERE source_file = ?",
            [url],
        ).fetchone()

        if exists:
            print(f"SKIPPED: {url}")
            continue

        print(f"INGESTING: {url}")

        try:
            con.execute("BEGIN TRANSACTION")

            # Create the table with the first file's schema
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS taxi_trips AS
                SELECT *, CAST('' AS VARCHAR) AS source_file
                FROM read_parquet(?)
                LIMIT 0
                """,
                [url],
            )

            # Get existing database columns
            existing_columns = {
                row[1].lower()
                for row in con.execute("PRAGMA table_info('taxi_trips')").fetchall()
            }

            # Get incoming Parquet columns
            source_columns = con.execute(
                "DESCRIBE SELECT * FROM read_parquet(?)",
                [url],
            ).fetchall()

            # Add missing columns automatically
            for name, dtype, *_ in source_columns:
                if name.lower() not in existing_columns:
                    safe_name = name.replace('"', '""')
                    con.execute(
                        f'ALTER TABLE taxi_trips ADD COLUMN "{safe_name}" {dtype}'
                    )
                    existing_columns.add(name.lower())
                    print(f"NEW COLUMN: {name}")

            # Append data without recreating the table
            con.execute(
                """
                INSERT INTO taxi_trips BY NAME
                SELECT *, ? AS source_file
                FROM read_parquet(?)
                """,
                [url, url],
            )

            # Record successful ingestion
            con.execute(
                """
                INSERT INTO ingestion_log (source_file)
                VALUES (?)
                """,
                [url],
            )

            con.execute("COMMIT")
            print(f"COMPLETED: {url}")

        except Exception as ex:
            con.execute("ROLLBACK")
            print(f"FAILED: {url}, error: {ex}")
            raise

finally:
    con.close()
