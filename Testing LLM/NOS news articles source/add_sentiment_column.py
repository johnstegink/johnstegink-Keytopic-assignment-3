#
# Splits the articles in CSV files per year.
#
import glob
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

def add_sentiment_column(input_file, output_file):
    """
    Read CSV file and write data to output file.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path where the output CSV file should be saved
    """
    # Read the CSV file
    df = pd.read_csv(input_file)

    # Write the data to the output file
    df.to_csv(output_file, index=False)




def main() -> int:
    # Load environment variables from .env so the CSV file name can be configured.
    script_dir = Path(__file__).resolve().parent
    load_dotenv()


    article_names = os.environ.get("CSV_FILE_NAME_YEAR_ARTICLES")
    if not article_names:
        print("Error: CSV_FILE_NAME_YEAR_ARTICLES was not found in .env or environment.")
        return 1

    output_path = os.environ.get("CSV_OUTPUT_SENTIMENT_FILE_PATH")
    if not output_path:
        print("Error: CSV_OUTPUT_SENTIMENT_FILE_PATH was not found in .env or environment.")
        return 1


    # Ensure output_path is a Path object
    output_dir = Path(output_path)
    os.makedirs(output_path, exist_ok=True)


    pattern = article_names.format(year="*")
    files = glob.glob(pattern)
    for file in files:

        # Get the filename from the input csv_path and construct the full output path
        filename = Path(file).name
        output_file = output_dir / filename

        add_sentiment_column(file, output_file)
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

