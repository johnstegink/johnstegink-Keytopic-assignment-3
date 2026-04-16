import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import ollama
from concurrent.futures import ThreadPoolExecutor
import ast
import torch
import matplotlib.pyplot as plt
import seaborn as sns
# Imports for the Neutralization Check (Based on embedding method)
from sentence_transformers import SentenceTransformer
import torch.nn.functional as F

# Load environment variables from the .env file
load_dotenv()


def generate_findings_plot(df_results):
    """
    Generates a scatter plot visualizing the neutralization efficacy.
    """
    # Define the directory where you want to save the output
    output_folder = "report_figures"

    # Create the directory if it does not already exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Directory '{output_folder}' created successfully.")

    # Determine which subjectivity column to use (support for both old and new naming conventions)
    subj_col = 'title_subjectivity' if 'title_subjectivity' in df_results.columns else 'subjectivity'

    # Set the aesthetic style of the plots
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    # Create a scatter plot comparing Lie-Meter and Validation
    # Note: we use 'title_text_distance' as the Lie-Meter
    plot = sns.scatterplot(
        data=df_results,
        x='title_text_distance',
        y='neutral_content_distance',
        hue='neutralization_distance',
        size=subj_col,  # Dynamically sized based on available column
        palette='viridis',
        sizes=(50, 200)
    )

    plt.title('Neutralization Efficacy: Lie-Meter vs. Validation Score', fontsize=15)
    plt.xlabel('Lie-Meter (Original Mismatch)', fontsize=12)
    plt.ylabel('Validation Score (Neutral Title vs Content)', fontsize=12)

    # Add a reference line for "Perfect Honesty"
    plt.axhline(0.2, ls='--', color='red', alpha=0.5, label='Factual Accuracy Goal')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.tight_layout()

    # Save the file to the specific directory
    file_path = os.path.join(output_folder, 'neutralization_findings.png')
    plt.savefig(file_path)
    print(f"Graph successfully saved as {file_path}")
    # plt.show()


def plot_validation_distribution(df_results):
    output_folder = "report_figures"
    plt.figure(figsize=(8, 6))

    sns.histplot(df_results['neutral_content_distance'], kde=True, color='green', bins=10, label='Neutralized Articles')

    plt.axvline(0.2, color='red', linestyle='--', label='Hallucination Threshold (Ideal)')
    plt.axvline(0.5, color='orange', linestyle=':', label='Observed NOS Baseline')

    plt.title('Validation Score Distribution (Hallucination Mitigation)', fontsize=14)
    plt.xlabel('Neutral Title vs. Content Distance (Lower is better)')
    plt.ylabel('Number of Articles')
    plt.legend()
    plt.savefig(os.path.join(output_folder, 'validation_distribution.png'))
    plt.close()


def ollama_neutralizer(title, model_name="mistral"):
    """
    Focuses purely on the title to strip away sensationalism.
    Forces the model to provide a mundane, bureaucratic Dutch alternative.
    """
    system_instruction = (
        "You are a factual Dutch news editor. Your job is to read a sensational "
        "title and extract ONLY the most dry, underlying fact."
        "ALWAYS answer in Dutch. Never use English words. Maximum 10 words. Do not translate to English."
    )

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
        response = ollama.chat(model=model_name, messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': user_prompt}
        ])
        output = response['message']['content'].strip()
        clean_output = output.split('\n')[0].replace('Output:', '').replace('"', '').strip()
        if clean_output.endswith('.'):
            clean_output = clean_output[:-1]
        return clean_output
    except Exception as e:
        return f"Error during AI processing: {e}"


def process_nos_dataset():
    """
    Loads the datasets, filters for clickbait titles based on the
    semantic distance, and calculates a Neutralization Score.
    """
    all_yearly_data = []

    print("Starting data loading process...")

    input_dir = Path(os.environ.get("CSV_OUTPUT_EMBEDDING_FILE_PATH", "with_embeddings"))
    files = list(input_dir.glob("articles_*.txt"))

    if not files:
        print(f"Error: No data files found in {input_dir}.")
        return

    # STEP 1: LOAD DATA
    for input_file in files:
        if input_file.exists():
            # Quickly read headers to see which columns are available
            available_cols = pd.read_csv(input_file, sep='\t', nrows=0).columns.tolist()

            cols_to_use = ['title']

            # Support both subjectivity naming flavors
            if 'title_subjectivity' in available_cols: cols_to_use.append('title_subjectivity')
            if 'subjectivity' in available_cols: cols_to_use.append('subjectivity')

            # Support both polarity naming flavors
            if 'title_polarity' in available_cols: cols_to_use.append('title_polarity')
            if 'polarity' in available_cols: cols_to_use.append('polarity')

            # Distance and content columns
            if 'title_text_distance' in available_cols: cols_to_use.append('title_text_distance')
            if 'content' in available_cols: cols_to_use.append('content')
            if 'extraction_method' in available_cols: cols_to_use.append('extraction_method')

            # Load the file with only the relevant columns
            df_year = pd.read_csv(input_file, sep='\t', usecols=cols_to_use)

            # Standardize subjectivity and polarity names immediately
            if 'title_subjectivity' in df_year.columns:
                df_year = df_year.rename(columns={'title_subjectivity': 'subjectivity'})
            if 'title_polarity' in df_year.columns:
                df_year = df_year.rename(columns={'title_polarity': 'polarity'})

            # Handle missing extraction_method (for NOS files)
            if 'extraction_method' not in df_year.columns:
                df_year['extraction_method'] = pd.NA

            all_yearly_data.append(df_year)
            print(f"Successfully loaded and standardized {input_file.name}...")

    if not all_yearly_data:
        return

    df = pd.concat(all_yearly_data, ignore_index=True)
    df = df.drop_duplicates(subset=['title'], keep='first')

    # STEP 2: FIND MATCHES WITH DYNAMIC THRESHOLDS
    all_matches = pd.DataFrame()

    if 'title_text_distance' in df.columns:
        print(f"Filtering {len(df)} unique articles using dynamic Lie-Meter thresholds...")

        # Scenario A: Full text articles (Crawler)
        full_text_matches = df[
            (df['extraction_method'].str.startswith('full_', na=False)) &
            (df['subjectivity'] >= 0.3) &
            (df['title_text_distance'] >= 0.9)
            ]

        # Scenario B: RSS Summaries
        summary_matches = df[
            (df['extraction_method'] == 'rss_summary') &
            (df['subjectivity'] >= 0.3) &
            (df['title_text_distance'] >= 0.5)
            ]

        # Scenario C: Missing extraction method (NOS files)
        missing_method_matches = df[
            (df['extraction_method'].isna()) &
            (df['subjectivity'] >= 0.3) &
            (df['title_text_distance'] >= 0.9)
            ]

        all_matches = pd.concat([full_text_matches, summary_matches, missing_method_matches])

    # FALLBACK & SUCCESS CHECK
    if all_matches.empty:
        print("Warning: No distance matches found. Check your thresholds.")
        return

    print(f"Found {len(all_matches)} articles matching the criteria.")
    df_clickbait = all_matches.sort_values(by='title_text_distance', ascending=False).head(10).copy()

    # STEP 3: START NEUTRALIZATION
    print(f"Starting neutralization for {len(df_clickbait)} articles...")
    print("-" * 50)

    with ThreadPoolExecutor(max_workers=4) as executor:
        df_clickbait['neutral_title'] = list(executor.map(ollama_neutralizer, df_clickbait['title']))

    # Setting up the model for Validation
    model_name = os.environ.get("SENTENCE_EMBEDDING_MODEL")
    if not model_name: return

    device_type = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    embedding_model = SentenceTransformer(model_name, device=device_type)

    df_clickbait['neutralization_distance'] = None
    df_clickbait['neutral_content_distance'] = None

    for index, row in df_clickbait.iterrows():
        original = str(row['title'])
        neutral = str(row['neutral_title'])
        content_text = str(row.get('content', ''))

        if "Error" in neutral or not neutral.strip(): continue

        # Calculate Tensors
        orig_tensor = embedding_model.encode(original, convert_to_tensor=True, device=device_type).unsqueeze(0)
        neutral_tensor = embedding_model.encode(neutral, convert_to_tensor=True, device=device_type).unsqueeze(0)

        # Score 1: Neutralization Distance
        cos_sim_neut = F.cosine_similarity(orig_tensor, neutral_tensor, dim=1)
        df_clickbait.at[index, 'neutralization_distance'] = (1 - cos_sim_neut).item()

        # Score 2: Validation (Neutral Title vs Content)
        if content_text and content_text.strip() != 'nan':
            content_tensor = embedding_model.encode(content_text, convert_to_tensor=True, device=device_type).unsqueeze(
                0)
            cos_sim_val = F.cosine_similarity(neutral_tensor, content_tensor, dim=1)
            df_clickbait.at[index, 'neutral_content_distance'] = (1 - cos_sim_val).item()

    # --- Display results (TERMINAL OUTPUT) ---
    print("\n" + "=" * 50)
    for index, row in df_clickbait.iterrows():
        print(f"ORIGINAL:  {row['title']}")
        print(f"RESULT:    {row['neutral_title']}")
        print(f"METHOD:    {row.get('extraction_method', 'unknown')}")
        print(f"SCORE:     {row['neutralization_distance']:.4f} (Original Title vs Neutral Title --> High score proves the title was misleading)")

        if 'title_text_distance' in row:
            print(f"LIE-METER: {row['title_text_distance']:.4f} (Original Title vs Content Mismatch --> High score proves the AI significantly cleaned up the title)")

        if pd.notna(row.get('neutral_content_distance')):
            print(f"VALIDATION: {row['neutral_content_distance']:.4f} (Neutral Title vs Content Mismatch --> Low score proves the new title is actually honest about the content)")

        print("-" * 50)

    # STAP 5: VISUALISATION
    if not df_clickbait.empty:
        print("Generating comprehensive visualizations for the report...")

        # 1. The main scatter plot (Efficiency)
        generate_findings_plot(df_clickbait)

        # 2. Hallucination Distribution (RQ 3)
        plot_validation_distribution(df_clickbait)

        print("All visualizations have been saved to 'report_figures/'.")

    # Add relevant columns for export dynamically based on the available names
    relevant_columns = [
        'title',
        'subjectivity',
        'polarity',
        'neutral_title',
        'neutralization_distance',
    ]

    if 'title_text_distance' in df_clickbait.columns:
        relevant_columns.append('title_text_distance')
    # Add validation distance to save file
    if 'neutral_content_distance' in df_clickbait.columns:
        relevant_columns.append('neutral_content_distance')

    output_path = Path("with_embeddings/nos_articles_title_only.txt")
    df_clickbait[relevant_columns].to_csv(output_path, sep='\t', index=False)

    print(f"Process complete. Clean results saved to: {output_path}")


if __name__ == "__main__":
    process_nos_dataset()