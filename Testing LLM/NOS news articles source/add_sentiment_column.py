#
# Add a polarity and subjectivity column
#
import glob
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from textblob import TextBlob
from textblob_nl import PatternAnalyzer

def add_sentiment_column(input_file, output_file):
    """
    Read CSV file, add sentiment analysis columns, and write to output file.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path where the output CSV file should be saved, tab-delimited
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Loop through each row and analyze sentiment
    for index, row in df.iterrows():
        title = row.get('title')
        content = row.get('content')

        # Create TextBlob with Dutch analyzer
        blob_title = TextBlob(str(title), analyzer=PatternAnalyzer())
        blob_content = TextBlob(str(content), analyzer=PatternAnalyzer())

        df.at[index, 'title_polarity'] = blob_title.sentiment[0]
        df.at[index, 'title_subjectivity'] = blob_title.sentiment[1]
        df.at[index, 'content_polarity'] = blob_content.sentiment[0]
        df.at[index, 'content_subjectivity'] = blob_content.sentiment[1]


    # Write the data with sentiment columns to the output file as tab-delimited
    df.to_csv(output_file, sep='\t', index=False)




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
        filename = Path(file.replace(".csv", ".txt")).name
        output_file = output_dir / filename

        add_sentiment_column(file, output_file)
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

