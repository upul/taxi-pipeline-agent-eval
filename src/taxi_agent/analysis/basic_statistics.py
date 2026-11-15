import duckdb

from taxi_agent.config import config

db_file = config["data"]["db_file"]


def calculate_monthly_statistics(source_file: str) -> dict:
    con = duckdb.connect(db_file)
    try:
        # count number of rows
        total_rec = con.execute(
            "SELECT count(*) FROM taxi_trips WHERE source_file = ?", [source_file]
        ).fetchone()

        # count number of columns
        num_cols = con.execute(
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
                COUNT(*) AS total_trips,
                SUM(total_amount) AS total_revenue,
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
        missing_fares = con.execute(
            """
            SELECT COUNT(*)
            FROM taxi_trips
            WHERE source_file = ? AND (total_amount IS NULL OR total_amount <= 0)
            """,
            [source_file],
        ).fetchone()

        return {
            "total_records": total_rec[0],
            "num_cols": num_cols[0],
            "total_trips": fare_data[0],
            "total_revenue": fare_data[1],
            "average_trip_cost": fare_data[2],
            "max_trip_distance": trip_data[0],
            "min_trip_distance": trip_data[1],
            "missing_fares": missing_fares[0],
            "missing_fare_percentage": (missing_fares[0] / total_rec[0]) * 100.00,
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
