#
# Adds an embedding for the title and the contents of the article
#
import glob
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F

def add_embeddings(model, input_file, output_file):
    """
    Read CSV file, add embeddings write to output file.
    
    Args:
        model: SentenceTransformer model
        input_file: Path to the input CSV file
        output_file: Path where the output CSV file should be saved, tab-delimited
    """
    # Read the CSV file
    df = pd.read_csv(input_file, sep='\t')
    
    # Initialize sentiment column
    df['title_embedding'] = None
    df['text_embedding'] = None
    df['title_text_distance'] = None

    # Loop through each row and analyze sentiment
    for index, row in df.iterrows():
        title = row.get('title')
        text = row.get('text')

        # Create TextBlob with Dutch analyzer
        embeddings = model.encode([title, text], convert_to_tensor=True, device="mps")
        cosine_sim = F.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0), dim=1)
        cosine_distance = 1 - cosine_sim

        df.at[index, 'title_embedding'] = embeddings[0].tolist()
        df.at[index, 'text_embedding'] = embeddings[1].tolist()
        df.at[index, 'title_text_distance'] = cosine_distance.tolist()[0]

    # Write the data with sentiment columns to the output file as tab-delimited
    df.to_csv(output_file, sep='\t', index=False)




def main() -> int:
    # Load environment variables from .env so the CSV file name can be configured.
    script_dir = Path(__file__).resolve().parent
    load_dotenv()

    input_path = os.environ.get("CSV_OUTPUT_SENTIMENT_FILE_PATH")
    if not input_path:
        print("Error: CSV_OUTPUT_SENTIMENT_FILE_PATH was not found in .env or environment.")
        return 1

    output_path = os.environ.get("CSV_OUTPUT_EMBEDDING_FILE_PATH")
    if not output_path:
        print("Error: CSV_OUTPUT_EMBEDDING_FILE_PATH was not found in .env or environment.")
        return 1

    model_name = os.environ.get("SENTENCE_EMBEDDING_MODEL")
    if not model_name:
        print("Error: SENTENCE_EMBEDDING_MODEL was not found in .env or environment.")
        return 1

    # Ensure output_path is a Path object
    output_dir = Path(output_path)
    os.makedirs(output_path, exist_ok=True)

    pattern = input_path + "/articles_*.txt"
    files = glob.glob(pattern)
    model = SentenceTransformer(model_name, device='mps')

    for file in files:

        # Get the filename from the input csv_path and construct the full output path
        filename = Path(file.replace(".csv", ".txt")).name
        output_file = output_dir / filename
        add_embeddings(model, file, output_file)
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

