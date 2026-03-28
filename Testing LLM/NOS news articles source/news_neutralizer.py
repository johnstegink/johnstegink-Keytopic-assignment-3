import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import ollama
from concurrent.futures import ThreadPoolExecutor  # Added for speed

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
        "ALWAYS answer in Dutch. Maximum 10 words."
    )

    # Simplified user prompt focusing only on the title
    user_prompt = f"""Task: Rewrite the sensational title into a factual and funny Dutch sentence of max 10 words. Do not translate to English.

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
    Loads the datasets across multiple years, filters for clickbait titles based on subjectivity,
    and processes them using concurrent threads for maximum speed.
    """
    all_yearly_data = []

    # Loop through all the years from 2010 to 2023
    for year in range(2010, 2024):
        input_file = Path(f"with_sentiment_analysis/articles_{year}.txt")

        # Check if the specific year file exists before trying to load it
        if input_file.exists():
            df_year = pd.read_csv(input_file, sep='\t')
            all_yearly_data.append(df_year)
        else:
            print(f"File Note: {input_file} not found. Skipping...")

    # Stop the script if no files were found at all
    if not all_yearly_data:
        print("Error: No data files found in the specified directory.")
        return

    # Combine all individual yearly dataframes into one large dataframe
    df = pd.concat(all_yearly_data, ignore_index=True)
    df = df.drop_duplicates(subset=['title'], keep='first')

    # EXTREME FILTER: Maximum subjectivity and near-zero polarity for "pure" clickbait
    df_clickbait = df[
        (df['subjectivity'] > 0.95) &
        (df['polarity'] > -0.05) &
        (df['polarity'] < 0.05)
        ].head(10).copy()

    # Fallback if the extreme filter is too strict (no results found)
    if df_clickbait.empty:
        print("No extreme matches found. Using high-quality fallback (Subj > 0.8)...")
        df_clickbait = df[
            (df['subjectivity'] > 0.8) &
            (df['polarity'] > -0.1) &
            (df['polarity'] < 0.1)
            ].head(10).copy()

    print(f"Starting title-only neutralization for {len(df_clickbait)} articles...")
    print("-" * 50)

    # SPEED IMPROVEMENT: Use ThreadPoolExecutor to run tasks in parallel
    # max_workers=4 is a safe start; increase if your laptop handles it well.
    with ThreadPoolExecutor(max_workers=4) as executor:
        df_clickbait['neutral_title'] = list(executor.map(ollama_neutralizer, df_clickbait['title']))

    # Display results
    for index, row in df_clickbait.iterrows():
        print(f"ORIGINAL: {row['title']}")
        print(f"RESULT: {row['neutral_title']}")
        print("-" * 50)

    # Save output
    output_path = Path("with_sentiment_analysis/nos_articles_title_only.txt")
    df_clickbait.to_csv(output_path, sep='\t', index=False)
    print(f"Process complete. Results saved to: {output_path}")


if __name__ == "__main__":
    process_nos_dataset()