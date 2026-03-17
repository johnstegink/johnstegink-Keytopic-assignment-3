#
# Splits the articles in CSV files per year.
#

import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import datetime

def split_files(csv_path: Path, output_path: str) -> int:
    # Read the CSV and write each original row to a year-specific CSV file.
    open_files = {}
    writers = {}
    records_written = 0

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames

        for line in reader:
            article_date = datetime.datetime.strptime(line["datetime"], "%Y-%m-%d %H:%M:%S")
            year = article_date.year
            file_name = output_path.format(year=year)
            target_path = csv_path.parent / file_name

            # Create a new writer
            if year not in writers:
                output_file = target_path.open("w", encoding="utf-8", newline="")
                open_files[year] = output_file
                writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                writer.writeheader()
                writers[year] = writer

            # Write the original row values back to the corresponding year file.
            writers[year].writerow(line)
            records_written += 1

    return records_written

def main() -> int:
    # Load environment variables from .env so the CSV file name can be configured.
    script_dir = Path(__file__).resolve().parent
    load_dotenv()

    # Read the configured input file name from the environment.
    csv_file_name = os.environ.get("CSV_FILE_NAME_ALL_ARTICLES")
    if not csv_file_name:
        print("Error: CSV_FILE_NAME_ALL_ARTICLES was not found in .env or environment.")
        return 1

    # Resolve the CSV path relative to this script and validate it exists.
    csv_path = script_dir / csv_file_name
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}")
        return 1

    output_path = os.environ.get("CSV_FILE_NAME_YEAR_ARTICLES")
    if not output_path:
        print("Error: CSV_FILE_NAME_YEAR_ARTICLES was not found in .env or environment.")
        return 1

    records_written = split_files(csv_path, output_path)
    print(f"Wrote {records_written} records using pattern: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

