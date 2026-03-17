#
# Create a selection of the csv file of a year
#

import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import datetime

def display_count_records(csv_path: Path) -> int:
    # Read the CSV and count how many articles exist per calendar year.
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        count_per_year = {}
        for line in reader:
            # Parse the publication timestamp and use its year as aggregation key.
            article_date = datetime.datetime.strptime(line["datetime"], "%Y-%m-%d %H:%M:%S")
            year = article_date.year
            count_per_year[year] = count_per_year.get(year, 0) + 1

        # Print yearly totals in ascending order.
        for year in sorted(sorted( count_per_year.keys())):
            print(f"{year}: {count_per_year[year]}")

def main() -> int:
    # Load environment variables from .env so the CSV file name can be configured.
    script_dir = Path(__file__).resolve().parent
    load_dotenv()

    # Read the configured input file name from the environment.
    csv_file_name = os.environ.get("CSV_FILE_NAME_ALL_ARTICLES")
    if not csv_file_name:
        print("Fout: CSV_FILE_NAME_ALL_ARTICLES was not found in .env or environment.")
        return 1

    # Resolve the CSV path relative to this script and validate it exists.
    csv_path = script_dir / csv_file_name
    if not csv_path.exists():
        print(f"Fout: file not found: {csv_path}")
        return 1

    csv_file_name = os.environ.get("CSV_FILE_NAME_ALL_ARTICLES")
    if not csv_file_name:
        print("Fout: CSV_FILE_NAME_ALL_ARTICLES was not found in .env or environment.")
        return 1

    display_count_records(csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

