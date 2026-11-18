from taxi_agent.analysis import basic_statistics
from taxi_agent.config import config

base_url = config["data"]["base_url"]
files = config["data"]["files"]
file_list = [f"{base_url}/{file}" for file in files]


def get_trip_breakdown(year: int, month: int) -> dict:
    monthly_data_file = _get_taxi_source_url(year, month, file_list)
    if not monthly_data_file:
        raise ValueError(f"year: {year} and month:{month} is not in our DB")

    return basic_statistics.calculate_trip_breakdown(monthly_data_file)


def get_monthly_statistics(year: int, month: int) -> dict:
    monthly_data_file = _get_taxi_source_url(year, month, file_list)
    if not monthly_data_file:
        raise ValueError(f"year: {year} and month:{month} is not in our DB")

    return basic_statistics.calculate_monthly_statistics(monthly_data_file)


def _get_taxi_source_url(year: int, month: int, file_list: list[str]) -> str | None:
    """Finds and returns the taxi parquet filename for a given year and month."""
    # Format month to always be two digits (e.g., 1 -> "01", 12 -> "12")
    target_url = f"{base_url.rstrip('/')}/yellow_tripdata_{year}-{month:02d}.parquet"

    # Check if the file exists in the list
    if target_url in file_list:
        return target_url

    return None


if __name__ == "__main__":
    result = get_monthly_statistics(2025, 1)
    print(result["average_trip_cost"])
