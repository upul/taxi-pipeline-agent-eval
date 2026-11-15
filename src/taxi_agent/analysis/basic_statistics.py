import duckdb

from taxi_agent.config import config

db_file = config["data"]["db_file"]


def calculate_monthly_statistics(source_file: str) -> dict:
    con = duckdb.connect(db_file)
    try:
        # count number of rows
        total_records = con.execute(
            "SELECT count(*) FROM taxi_trips WHERE source_file = ?", [source_file]
        ).fetchone()

        # schema column count
        # schema_column_count = con.execute(
        #     "DESCRIBE SELECT * FROM read_parquet(?)", [source_file]
        # ).fetchall()

        # count number of columns
        populated_column_count = con.execute(
            """
            SELECT count(column_name)
            FROM (
                SUMMARIZE
                SELECT *
                FROM taxi_trips
                WHERE source_file = ?
            )
            WHERE null_percentage < 100;
            """,
            [source_file],
        ).fetchone()

        # Total and average fares
        fare_data = con.execute(
            """
            SELECT
                COUNT(total_amount) AS positive_amount_trips,
                SUM(total_amount) AS total_trip_cost,
                AVG(total_amount) AS average_trip_cost
            FROM taxi_trips
            WHERE source_file = ?
              AND total_amount > 0;
            """,
            [source_file],
        ).fetchone()

        # Trip distances
        trip_data = con.execute(
            """
            SELECT
                MAX(trip_distance) AS max_trip_distance,
                MIN(trip_distance) AS min_trip_distance,
            FROM taxi_trips
            WHERE source_file = ?
              AND trip_distance > 0;
            """,
            [source_file],
        ).fetchone()

        # missing fares
        missing_trip_count = con.execute(
            """
            SELECT COUNT(*)
            FROM taxi_trips
            WHERE source_file = ? AND total_amount IS NULL
            """,
            [source_file],
        ).fetchone()

        # zero trip
        zero_trip_count = con.execute(
            """
            SELECT COUNT(*)
            FROM taxi_trips
            WHERE source_file = ? AND total_amount == 0
            """,
            [source_file],
        ).fetchone()

        # negative trip
        negative_trip_count = con.execute(
            """
            SELECT COUNT(*)
            FROM taxi_trips
            WHERE source_file = ? AND total_amount < 0
            """,
            [source_file],
        ).fetchone()

        return {
            "total_records": total_records[0],
            "populated_column_count": populated_column_count[0],
            "positive_amount_trips": fare_data[0],
            "total_trip_cost": fare_data[1] if fare_data[1] is not None else 0,
            "average_trip_cost": fare_data[2] if fare_data[2] is not None else 0,
            "max_trip_distance": trip_data[0] if trip_data[0] is not None else 0,
            "min_trip_distance": trip_data[1] if trip_data[1] is not None else 0,
            "missing_trip_cost_pct": (
                (missing_trip_count[0] / total_records[0]) * 100.00
            )
            if total_records[0] != 0
            else 0.0,
            "zero_trip_cost_pct": ((zero_trip_count[0] / total_records[0]) * 100.00)
            if total_records[0] != 0
            else 0.0,
            "negative_trip_cost_pct": (
                (negative_trip_count[0] / total_records[0]) * 100.00
            )
            if total_records[0]
            else 0.0,
            "source": source_file,
        }

    finally:
        con.close()


if __name__ == "__main__":
    base_url = config["data"]["base_url"]
    files = config["data"]["files"]
    for file in files:
        url = f"{base_url}/{file}"
        print(f"source file: {url}")
        output = calculate_monthly_statistics(url)
        print(output)
        print("")
