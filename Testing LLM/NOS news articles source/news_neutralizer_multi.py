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
# Imports required for calculating Sentiment Score on the neutralized output
from textblob import TextBlob
from textblob_nl import PatternAnalyzer

# Load environment variables from the .env file
load_dotenv()


def generate_findings_plot(df_results, prompt_name):
    """
    Generates a scatter plot visualizing the neutralization efficacy for a specific prompt.
    """
    # Define the directory where you want to save the output
    output_folder = "report_figures"

    # Create the directory if it does not already exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Directory '{output_folder}' created successfully.")

    # Determine which subjectivity column to use
    subj_col = 'subjectivity'

    # Set the aesthetic style of the plots
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    # Create a scatter plot comparing Lie-Meter and Validation
    plot = sns.scatterplot(
        data=df_results,
        x='title_text_distance',
        y='neutral_content_distance',
        hue='neutralization_distance',
        size=subj_col,
        palette='viridis',
        sizes=(50, 200)
    )

    plt.title(f'Neutralization Efficacy: {prompt_name}', fontsize=15)
    plt.xlabel('Lie-Meter (Original Mismatch)', fontsize=12)
    plt.ylabel('Validation Score (Neutral Title vs Content)', fontsize=12)

    # Add a reference line for "Perfect Honesty"
    plt.axhline(0.2, ls='--', color='red', alpha=0.5, label='Factual Accuracy Goal')
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2)
    plt.tight_layout()

    # Save the file with a unique name based on the prompt
    filename = f"findings_{prompt_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.png"
    file_path = os.path.join(output_folder, filename)
    plt.savefig(file_path)
    plt.close()
    print(f"Graph successfully saved as {file_path}")


def plot_metric_correlation(df_results):
    """
    Generates a heatmap with properly rotated and visible axis labels.
    """
    output_folder = "report_figures"
    plt.figure(figsize=(10, 8)) # Slightly larger for better readability

    # Select numeric columns
    cols = ['subjectivity', 'polarity', 'title_text_distance',
            'neutralization_distance', 'neutral_content_distance']

    # Filter for columns that actually exist in the dataframe
    cols_present = [c for c in cols if c in df_results.columns]
    corr = df_results[cols_present].corr()

    # Create heatmap
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)

    plt.title('Correlation Heatmap of Quality Metrics', fontsize=14, pad=20)

    # Rotate the bottom labels and align them
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(rotation=0, fontsize=10)

    # Force enough space at the bottom and left
    plt.tight_layout()

    # Save the file
    plt.savefig(os.path.join(output_folder, 'metric_correlation.png'), bbox_inches='tight')
    plt.close()


def plot_distance_boxplot(df_all_results):
    """
    Final fix for the boxplot legend to ensure both prompt colors
    and the accuracy target are clearly visible.
    """
    output_folder = "report_figures"
    plt.figure(figsize=(10, 6))

    # 1. Create the boxplot with hue assigned and legend explicitly enabled
    ax = sns.boxplot(
        data=df_all_results,
        x='prompt_type',
        y='neutral_content_distance',
        hue='prompt_type',
        palette='Set2',
        legend=True # Keep this True to capture the handles
    )

    # 2. Add the target line
    line = plt.axhline(0.2, ls='--', color='red', alpha=0.6, label='Accuracy Target (Ideal)')

    plt.title('Validation Distance Spread by Prompt Type', fontsize=15)
    plt.ylabel('Distance to Content (Lower is Better)')
    plt.xlabel('Prompt Strategy')

    # 3. Fix the legend: Combine the prompt labels and the line label
    # This prevents the 'redundant' feel but keeps the line info
    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles=handles, labels=labels, loc='upper right', title="Legend")

    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'prompt_consistency_boxplot.png'))
    plt.close()


def plot_sentiment_comparison(df_all_results):
    """
    Compares original sentiment scores with neutral sentiment scores.
    Added value labels to ensure low scores are visible.
    """
    output_folder = "report_figures"
    plt.figure(figsize=(10, 6))

    # Prepare data
    plot_data = pd.melt(df_all_results, id_vars=['prompt_type'],
                        value_vars=['orig_sentiment_score', 'new_sentiment_score'],
                        var_name='Type', value_name='Score')

    plot_data['Type'] = plot_data['Type'].map({
        'orig_sentiment_score': 'Original (Clickbait)',
        'new_sentiment_score': 'Neutralized'
    })

    # Create the barplot
    ax = sns.barplot(data=plot_data, x='prompt_type', y='Score', hue='Type', palette='muted')

    # Add text labels on top of each bar
    for p in ax.patches:
        if p.get_height() > 0:  # Only label bars with height
            ax.annotate(format(p.get_height(), '.3f'),
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center',
                        xytext=(0, 9),
                        textcoords='offset points',
                        fontsize=10, fontweight='bold')

    plt.title('Average Sentiment Score Reduction', fontsize=15)
    plt.ylabel('Sentiment Score (|Pol| * Subj)')
    plt.xlabel('Strategy')

    # Adjust y-axis slightly to make room for labels
    plt.ylim(0, plot_data['Score'].max() * 1.2)

    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'sentiment_reduction.png'))
    plt.close()

def plot_validation_distribution(df_results, prompt_name):
    """
    Generates a distribution plot for a specific prompt run.
    """
    output_folder = "report_figures"
    plt.figure(figsize=(8, 6))

    sns.histplot(df_results['neutral_content_distance'], kde=True, color='green', bins=10, label='Neutralized Articles')

    plt.axvline(0.2, color='red', linestyle='--', label='Hallucination Threshold (Ideal)')
    plt.axvline(0.5, color='orange', linestyle=':', label='Observed NOS Baseline')

    plt.title(f'Validation Score Distribution: {prompt_name}', fontsize=14)
    plt.xlabel('Neutral Title vs. Content Distance (Lower is better)')
    plt.ylabel('Number of Articles')
    plt.legend()

    # Save with unique name per prompt
    filename = f"dist_{prompt_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.png"
    file_path = os.path.join(output_folder, filename)
    plt.savefig(file_path)
    plt.close()
    print(f"Distribution plot saved as {file_path}")


def ollama_neutralizer(title, system_instruction, model_name="mistral"):
    """
    Focuses purely on the title to strip away sensationalism.
    Now accepts dynamic system instructions for multi-prompt testing.
    """
    user_prompt = f"""Task: Rewrite the sensational title according to the instructions. Do not translate to English.

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
            available_cols = pd.read_csv(input_file, sep='\t', nrows=0).columns.tolist()
            cols_to_use = ['title']

            if 'title_subjectivity' in available_cols: cols_to_use.append('title_subjectivity')
            if 'subjectivity' in available_cols: cols_to_use.append('subjectivity')
            if 'title_polarity' in available_cols: cols_to_use.append('title_polarity')
            if 'polarity' in available_cols: cols_to_use.append('polarity')
            if 'title_text_distance' in available_cols: cols_to_use.append('title_text_distance')
            if 'content' in available_cols: cols_to_use.append('content')
            if 'extraction_method' in available_cols: cols_to_use.append('extraction_method')

            df_year = pd.read_csv(input_file, sep='\t', usecols=cols_to_use)

            if 'title_subjectivity' in df_year.columns:
                df_year = df_year.rename(columns={'title_subjectivity': 'subjectivity'})
            if 'title_polarity' in df_year.columns:
                df_year = df_year.rename(columns={'title_polarity': 'polarity'})
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
        full_text_matches = df[
            (df['extraction_method'].str.startswith('full_', na=False)) & (df['subjectivity'] >= 0.3) & (
                        df['title_text_distance'] >= 0.9)]
        summary_matches = df[(df['extraction_method'] == 'rss_summary') & (df['subjectivity'] >= 0.3) & (
                    df['title_text_distance'] >= 0.5)]
        missing_method_matches = df[
            (df['extraction_method'].isna()) & (df['subjectivity'] >= 0.3) & (df['title_text_distance'] >= 0.9)]
        all_matches = pd.concat([full_text_matches, summary_matches, missing_method_matches])

    if all_matches.empty:
        print("Warning: No distance matches found. Check your thresholds.")
        return

    print(f"Found {len(all_matches)} articles matching the criteria.")
    df_clickbait = all_matches.sort_values(by='title_text_distance', ascending=False).head(30).copy()

    # STEP 3: START NEUTRALIZATION
    print(f"Starting neutralization for {len(df_clickbait)} articles...")

    df_clickbait['polarity'] = pd.to_numeric(df_clickbait.get('polarity', 0.0), errors='coerce').fillna(0.0)
    df_clickbait['subjectivity'] = pd.to_numeric(df_clickbait.get('subjectivity', 0.0), errors='coerce').fillna(0.0)
    df_clickbait['orig_sentiment_score'] = df_clickbait['polarity'].abs() * df_clickbait['subjectivity']

    prompts = {
        "Prompt 1 (Editor)": "You are a factual Dutch news editor. Your job is to read a sensational title and extract ONLY the most dry, underlying fact. ALWAYS answer in Dutch. Maximum 10 words.",
        "Prompt 2 (Anti-Sensation)": "You are a 'Anti-Sensation Editor'.Your job is to take Dutch headlines and turn them into the most boring, trivial, and mundane Dutch sentences possible. Remove all emotion and imagery. ALWAYS answer in Dutch. Maximum 10 words.",
        "Prompt 3 (Official)": "You are a Dutch government spokesperson. Rewrite this headline as a formal, neutral administrative announcement. Use official language. ALWAYS answer in Dutch. Maximum 10 words."
    }

    model_name = os.environ.get("SENTENCE_EMBEDDING_MODEL")
    device_type = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    embedding_model = SentenceTransformer(model_name, device=device_type)

    results_accumulator = []

    for prompt_name, sys_instruction in prompts.items():
        print(f"\n" + "█" * 30 + f" STARTING RUN: {prompt_name.upper()} " + "█" * 30)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(ollama_neutralizer, t, sys_instruction) for t in df_clickbait['title']]
            neutral_titles = [f.result() for f in futures]

        df_run = df_clickbait.copy()
        df_run['neutral_title'] = neutral_titles
        df_run['prompt_type'] = prompt_name

        # We prepare columns to avoid KeyErrors
        df_run['new_sentiment_score'] = 0.0
        df_run['neutralization_distance'] = 0.0
        df_run['neutral_content_distance'] = 0.0

        for idx, row in df_run.iterrows():
            # Calculate Sentiment
            blob = TextBlob(str(row['neutral_title']), analyzer=PatternAnalyzer())
            current_sent = abs(blob.sentiment[0]) * blob.sentiment[1]

            # Embedding Calculations
            orig_tensor = embedding_model.encode(str(row['title']), convert_to_tensor=True,
                                                 device=device_type).unsqueeze(0)
            neutral_tensor = embedding_model.encode(str(row['neutral_title']), convert_to_tensor=True,
                                                    device=device_type).unsqueeze(0)
            content_tensor = embedding_model.encode(str(row['content']), convert_to_tensor=True,
                                                    device=device_type).unsqueeze(0)

            # Distance Scores
            neut_dist = (1 - F.cosine_similarity(orig_tensor, neutral_tensor, dim=1)).item()
            val_dist = (1 - F.cosine_similarity(neutral_tensor, content_tensor, dim=1)).item()

            # Save to DataFrame
            df_run.at[idx, 'new_sentiment_score'] = current_sent
            df_run.at[idx, 'neutralization_distance'] = neut_dist
            df_run.at[idx, 'neutral_content_distance'] = val_dist

            # --- INDIVIDUAL TERMINAL OUTPUT ---
            # Use the local variables (current_sent, neut_dist, val_dist)
            # instead of row['...'] to avoid KeyError
            print(f"ORIGINAL:  {row['title']}")
            print(f"RESULT:    {row['neutral_title']}")
            print(f"SENTIMENT: {current_sent:.4f} (Pol*Subj)")
            print(f"SCORE:     {neut_dist:.4f} (Neutralization Distance)")
            print(f"METHOD:    {row.get('extraction_method', 'unknown')}")
            print(f"LIE-METER: {row.get('title_text_distance', 0):.4f} (Orig Title vs Content)")
            print(f"VALIDATION:{val_dist:.4f} (Neutral Title vs Content)")
            print("-" * 50)

        # Store results for each prompt
        results_accumulator.append(df_run)

        # Print Summary after each prompt run
        avg_dist = df_run['neutral_content_distance'].mean()
        avg_sent = df_run['new_sentiment_score'].mean()
        print(f"\n>>> SUMMARY {prompt_name.upper()} <<<")
        print(f"AVERAGE VALIDATION DISTANCE: {avg_dist:.3f}")
        print(f"AVERAGE SENTIMENT SCORE:     {avg_sent:.3f}")
        print("=" * 60)

        # Generate per-prompt plots
        generate_findings_plot(df_run, prompt_name)
        plot_validation_distribution(df_run, prompt_name)

    # --- AFTER ALL PROMPTS ARE FINISHED ---
    df_all_results = pd.concat(results_accumulator, ignore_index=True)

    if not df_all_results.empty:
        print("\nGenerating expanded report visualizations...")
        # 1. Compare original vs. neutralized sentiment scores (Bar Chart)
        plot_sentiment_comparison(df_all_results)
        # 2. Check the consistency of prompt performance and outliers (Box Plot)
        plot_distance_boxplot(df_all_results)
        # 3. Analyze correlations between all quality metrics (Heatmap)
        plot_metric_correlation(df_all_results)

        print("\nGenerating comparison findings scatter plot...")
        plt.figure(figsize=(12, 7))
        sns.scatterplot(data=df_all_results, x='title_text_distance', y='neutral_content_distance',
                        hue='prompt_type', size='subjectivity', palette='coolwarm', sizes=(50, 250), alpha=0.7)
        plt.savefig(os.path.join("report_figures", 'comparison_findings.png'))

        # Final CSV/TXT Export
        relevant_columns = ['title', 'prompt_type', 'neutral_title', 'subjectivity', 'polarity',
                            'new_sentiment_score', 'neutralization_distance', 'neutral_content_distance']
        if 'title_text_distance' in df_all_results.columns: relevant_columns.append('title_text_distance')
        if 'extraction_method' in df_all_results.columns: relevant_columns.append('extraction_method')

        final_export_cols = [col for col in relevant_columns if col in df_all_results.columns]
        output_path = Path("with_embeddings/nos_articles_title_only.txt")
        df_all_results[final_export_cols].to_csv(output_path, sep='\t', index=False)

    print("\nProcess complete. All visualizations saved.")


if __name__ == "__main__":
    process_nos_dataset()