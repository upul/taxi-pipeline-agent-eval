import duckdb
import pytest

from taxi_agent.analysis import basic_statistics


@pytest.fixture
def sample_db(tmp_path):
    """
    Prepare a small temporary DuckDB database.

    The database should contain a taxi_trips table
    with known records.
    """
    db_path = tmp_path / "taxi_test.duckdb"

    con = duckdb.connect(str(db_path))

    try:
        # TODO 1: Create the taxi_trips table.
        #
        # Required columns:
        #   source_file
        #   total_amount
        #   trip_distance

        # TODO 2: Insert the six sample records
        # described below.
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS taxi_trips (
                    source_file VARCHAR,
                    total_amount DOUBLE,
                    trip_distance DOUBLE
                )
            """
        )

        con.execute("""
            INSERT INTO taxi_trips (source_file, total_amount, trip_distance)
            VALUES
                ('december', 10, 2),
                ('december', 20, 5),
                ('december', 0,  0),
                ('december', -5, -1),
                ('december', NULL, NULL),
                ('january', 100, 10),
        """)

    finally:
        con.close()

    return str(db_path)


def test_monthly_statistics(sample_db, monkeypatch):
    """
    Verify that monthly statistics are calculated
    correctly using known sample data.
    """

    # Point the analysis module to our test database.
    monkeypatch.setattr(basic_statistics, "db_file", sample_db)

    # TODO 1: Call calculate_monthly_statistics()
    # for the December source.
    statistics = basic_statistics.calculate_monthly_statistics("december")

    # TODO 2: Assert the total record count.
    assert statistics["total_records"] == 5
    assert statistics["populated_column_count"] == 3
    assert statistics["positive_amount_trips"] == 2
    assert statistics["total_trip_cost"] == 30
    assert statistics["average_trip_cost"] == 15
    assert statistics["min_trip_distance"] == 2
    assert statistics["max_trip_distance"] == 5
    assert statistics["missing_trip_cost_pct"] == 20.0
    assert statistics["zero_trip_cost_pct"] == 20.0
    assert statistics["negative_trip_cost_pct"] == 20.0


def test_unknown_source_file(sample_db, monkeypatch):
    """
    Verify behavior when a source file has
    no matching records.
    """

    monkeypatch.setattr(basic_statistics, "db_file", sample_db)

    # TODO 1: Request statistics for an unknown source.
    statistics = basic_statistics.calculate_monthly_statistics("may")

    assert statistics["total_records"] == 0
    assert statistics["populated_column_count"] == 0
    assert statistics["positive_amount_trips"] == 0
    assert statistics["total_trip_cost"] == 0
    assert statistics["average_trip_cost"] == 0
    assert statistics["min_trip_distance"] == 0
    assert statistics["max_trip_distance"] == 0
    assert statistics["missing_trip_cost_pct"] == 0
    assert statistics["zero_trip_cost_pct"] == 0
    assert statistics["negative_trip_cost_pct"] == 0
