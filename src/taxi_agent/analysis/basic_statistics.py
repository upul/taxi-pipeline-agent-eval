import duckdb

from taxi_agent.config import config

db_file = config["data"]["db_file"]


def calculate_trip_breakdown(source_file: str) -> dict:
    con = duckdb.connect(db_file)
    try:
        # Run the distance-bucketed aggregation query
        result = con.execute(
            """
            SELECT
                CASE
                    WHEN trip_distance <= 2.0 THEN '0-2 miles'
                    WHEN trip_distance > 2.0 AND trip_distance <= 5.0 THEN '2-5 miles'
                    WHEN trip_distance > 5.0 AND trip_distance <= 10.0 THEN '5-10 miles'
                    ELSE 'Over 10 miles'
                END AS distance_bucket,
                COUNT(*) AS trip_count,
                ROUND(AVG(total_amount), 2) AS avg_cost
            FROM taxi_trips
            WHERE source_file = ? AND trip_distance > 0 AND total_amount > 0
            GROUP BY distance_bucket
            ORDER BY
                CASE distance_bucket
                    WHEN '0-2 miles' THEN 1
                    WHEN '2-5 miles' THEN 2
                    WHEN '5-10 miles' THEN 3
                    ELSE 4
                END
        """,
            [source_file],
        ).fetchall()
        output = {}
        for bucket, trip_count, ave_cost in result:
            output[bucket] = {"trip_count": trip_count, "ave_cost": ave_cost}
        return output

    finally:
        con.close()


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
        print(f"basic statistics: {output}")
        print("")

        output = calculate_trip_breakdown(f"{base_url}/{file}")
        print(f"breakdown statistics: {output}")
        print("")
