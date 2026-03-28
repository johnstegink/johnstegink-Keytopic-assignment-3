#
# Adds articles to the postgresql database
#

import glob
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from pgvector.sqlalchemy import Vector
import ast
import json

def to_postgresql(input_file, connection_string, first_time):
    """
    Read CSV/TXT file and write articles to PostgreSQL database.
    
    Args:
        input_file: Path to the input CSV or TXT file
        connection_string: PostgreSQL connection string (format: postgresql://user:password@host:port/dbname)
        first_time: Boolean indicating if table should be created
    """
    # Read the file
    df = pd.read_csv(input_file, sep='\t')

    # Zet string-weergave van lijsten om naar echte lijsten
    df['text_embedding'] = df['text_embedding'].apply(ast.literal_eval)
    df['title_embedding'] = df['title_embedding'].apply(ast.literal_eval)

    dimension = len(df["title_embedding"][0])
    engine = create_engine( connection_string)
    action = 'replace' if first_time else 'append'

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    df.to_sql('artikel', engine, index=False, if_exists=action,
              dtype={
                  'text_embedding': Vector(dimension),
                  'title_embedding': Vector(dimension)
              },
              chunksize=100
    )

    return True
    



def main() -> int:
    # Load environment variables from .env so the CSV file name can be configured.
    script_dir = Path(__file__).resolve().parent
    load_dotenv()

    input_path = os.environ.get("CSV_OUTPUT_EMBEDDING_FILE_PATH")
    if not input_path:
        print("Error: CSV_OUTPUT_EMBEDDING_FILE_PATH was not found in .env or environment.")
        return 1

    connection_string = "postgresql+psycopg2://john:geheimwachtwoord@localhost:5432/nos"

    pattern = input_path + "/articles_*.txt"
    files = sorted(glob.glob(pattern))
    
    if not files:
        print(f"Error: No files found matching pattern: {pattern}")
        return 1

    print(f"Found {len(files)} files to import")

    is_first = True
    for file in files:
        print(f"\nProcessing: {file}")
        if not to_postgresql(file, connection_string, is_first):
            print(f"Error importing {file}")
            return 1
        is_first = False

    print("\n✓ All files imported successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

