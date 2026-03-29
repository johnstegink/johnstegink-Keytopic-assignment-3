import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import ollama
from concurrent.futures import ThreadPoolExecutor  # Added for speed
import ast  # Required to parse the stringified list from the CSV
import torch  # Required to rebuild the tensor for calculation

# Imports for the Neutralization Check (Based on embedding method)
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F

# Load environment variables from the .env file
load_dotenv()


def ollama_neutralizer(title, model_name="mistral"):
    """
    Focuses purely on the title to strip away sensationalism.
    Forces the model to provide a mundane, bureaucratic Dutch alternative.
    """

    # Persona: A humorless Dutch official who simplifies everything to a mundane fact
    system_instruction = (
        "You are a factual Dutch news editor. Your job is to read a sensational "
        "title and extract ONLY the most dry, underlying fact."
        "ALWAYS answer in Dutch. Never use English words. Maximum 10 words. Do not translate to English."
    )

    # Simplified user prompt focusing only on the title
    user_prompt = f"""Task: Rewrite the sensational title into a factual Dutch sentence of max 10 words. Do not translate to English.

    Examples:
    Input: "JE GELOOFT NOOIT wat deze BN'er nu weer heeft gedaan! (SCHOKKEND)"
    Output: "Bekende Nederlander kocht brood bij de bakker."

    Input: "Bizar! Dit is hoe deze zangeres er nu uitziet na haar transformatie!"
    Output: "Zangeres heeft een nieuw kapsel."

    Now process this input:
    Input: "{title}"
    Output:"""

    try:
        # Request generation using only the title
        response = ollama.chat(model=model_name, messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': user_prompt}
        ])

        # Clean the output
        output = response['message']['content'].strip()
        # Take the first line and strip common AI prefixes or formatting
        clean_output = output.split('\n')[0].replace('Output:', '').replace('"', '').strip()

        # Remove trailing periods to keep it looking like a title
        if clean_output.endswith('.'):
            clean_output = clean_output[:-1]

        return clean_output
    except Exception as e:
        return f"Error during AI processing: {e}"


def process_nos_dataset():
    """
    Loads the datasets across multiple years, filters for clickbait titles based on the
    semantic distance between title and text (colleague's embedding data),
    processes them using concurrent threads, and calculates a Neutralization Score.
    """
    all_yearly_data = []

    print("Starting data loading process (Optimized Memory Mode)...")

    # Loop through all the years from 2010 to 2023
    for year in range(2010, 2024):
        input_file = Path(f"with_sentiment_analysis/articles_{year}.txt")

        # Check if the specific year file exists before trying to load it
        if input_file.exists():
            # SPEED IMPROVEMENT 1: Read only header to check for embedding columns
            available_cols = pd.read_csv(input_file, sep='\t', nrows=0).columns.tolist()

            # Specify exactly which columns to load.
            cols_to_use = ['title', 'subjectivity', 'polarity']
            if 'title_embedding' in available_cols:
                cols_to_use.append('title_embedding')
            # Also load the distance calculated
            if 'title_text_distance' in available_cols:
                cols_to_use.append('title_text_distance')

            # Load only the specified columns
            df_year = pd.read_csv(input_file, sep='\t', usecols=cols_to_use)
            all_yearly_data.append(df_year)

            print(f"Successfully loaded data for {year}...")
        else:
            print(f"File Note: {input_file} not found. Skipping...")

    # Stop the script if no files were found at all
    if not all_yearly_data:
        print("Error: No data files found in the specified directory.")
        return

    # Combine all individual yearly dataframes into one large dataframe
    df = pd.concat(all_yearly_data, ignore_index=True)
    print(f"Total records combined: {len(df)}. Removing duplicates...")
    df = df.drop_duplicates(subset=['title'], keep='first')

    # Find highly subjective titles that ARE related to the text
    if 'title_text_distance' in df.columns:
        print("Filtering for high subjectivity but relevant titles...")
        # We want High Subjectivity (>0.99) AND no relevance (distance >= 1.0)
        # This targets "Emotional Truths" rather than "Random Mismatches"
        df_clickbait = df[
            (df['subjectivity'] > 0.99) &
            (df['title_text_distance'] >= 1.0)
            ].sort_values(by='subjectivity', ascending=False).head(10).copy()
    else:
        # Fallback to the old sentiment-based logic if title_text_distance is missing
        print("Warning: 'title_text_distance' not found. Falling back to Sentiment filters...")
        df_clickbait = df[
            (df['subjectivity'] == 1.0) &
            (df['polarity'] == 0.0)
            ].head(10).copy()

        if df_clickbait.empty:
            df_clickbait = df[
                (df['subjectivity'] > 0.99) &
                (df['polarity'] > -0.02) &
                (df['polarity'] < 0.02)
                ].head(10).copy()

    print(f"Starting title-only neutralization for {len(df_clickbait)} articles...")
    print("-" * 50)

    # SPEED IMPROVEMENT 2: Use ThreadPoolExecutor to run tasks in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        df_clickbait['neutral_title'] = list(executor.map(ollama_neutralizer, df_clickbait['title']))

    # Neutralization Check (Calculate semantic distance between original and new title)
    print("Calculating Neutralization Scores (Semantic Distance)...")

    # Load the model name from .env
    model_name = os.environ.get("SENTENCE_EMBEDDING_MODEL")

    # Strict check: if the variable is missing, stop the execution
    if not model_name:
        print("Error: SENTENCE_EMBEDDING_MODEL was not found in .env or environment.")
        return  # Exit the function early

    # Detect the best available hardware for the current machine
    if torch.backends.mps.is_available():
        device_type = "mps"  # Apple Silicon
    elif torch.cuda.is_available():
        device_type = "cuda"  # Nvidia GPU
    else:
        device_type = "cpu"  # Fallback to standard processor

    print(f"Loading embedding model: {model_name} on {device_type}...")
    embedding_model = SentenceTransformer(model_name, device=device_type)

    # Initialize the new column
    df_clickbait['neutralization_distance'] = None

    # Calculate the distance for each row
    for index, row in df_clickbait.iterrows():
        original = str(row['title'])
        neutral = str(row['neutral_title'])

        # Skip calculation if AI failed to generate a proper title
        if "Error" in neutral or not neutral.strip():
            df_clickbait.at[index, 'neutralization_distance'] = 0.0
            continue

        # Try to grab the existing title embedding from script output
        if 'title_embedding' in row and pd.notna(row['title_embedding']):
            try:
                # Convert string "[0.1, 0.2]" back to Python list, then to the correct device tensor
                orig_list = ast.literal_eval(row['title_embedding'])
                orig_tensor = torch.tensor(orig_list, device=device_type).unsqueeze(0)
            except Exception:
                # Fallback: re-calculate if the data formatting is broken using dynamic device
                orig_tensor = embedding_model.encode(original, convert_to_tensor=True, device=device_type).unsqueeze(0)
        else:
            # Fallback: calculate if the column doesn't exist using dynamic device
            orig_tensor = embedding_model.encode(original, convert_to_tensor=True, device=device_type).unsqueeze(0)

        # Calculate embedding ONLY for the newly generated title using dynamic device
        neutral_tensor = embedding_model.encode(neutral, convert_to_tensor=True, device=device_type).unsqueeze(0)

        # Calculate cosine similarity and the resulting distance
        cosine_sim = F.cosine_similarity(orig_tensor, neutral_tensor, dim=1)
        cosine_distance = 1 - cosine_sim

        # Save the score (convert tensor to standard float)
        df_clickbait.at[index, 'neutralization_distance'] = cosine_distance.item()

    # Display results including the new score
    for index, row in df_clickbait.iterrows():
        print(f"ORIGINAL: {row['title']}")
        print(f"RESULT:   {row['neutral_title']}")
        print(f"SCORE:    {row['neutralization_distance']:.4f} (Neutralization Distance)")
        if 'title_text_distance' in row:
            print(f"LIE-METER: {row['title_text_distance']:.4f} (Original Title vs Text Mismatch)")
        print("-" * 50)

    # Define only the relevant columns we want to keep
    relevant_columns = [
        'title',
        'subjectivity',
        'polarity',
        'neutral_title',
        'neutralization_distance'
    ]

    # Add title_text_distance column to the output file
    if 'title_text_distance' in df_clickbait.columns:
        relevant_columns.append('title_text_distance')

    # Save only the selected columns
    output_path = Path("with_sentiment_analysis/nos_articles_title_only.txt")
    df_clickbait[relevant_columns].to_csv(output_path, sep='\t', index=False)

    print(f"Process complete. Clean results saved to: {output_path}")

if __name__ == "__main__":
    process_nos_dataset()