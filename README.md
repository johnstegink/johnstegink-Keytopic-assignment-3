# Keytopic-assignment-3
This repository contains software developed for assignment 3 of the course IM0712: Key Topics in Artificial Intelligence at the Open Universiteit.  The software supports the small paper written by Dorothy Lekston and John Stegink.
It contains the source code for a web application and several data processing/AI testing scripts. The project primarily tests LLM (Large Language Model) interactions for neutralizing sensational Dutch news headlines.

## Directory Structure

### `Application/`
Contains the main Flask web application for the project.
*   **`run.py`**: The main entry point to start the Flask server.
*   **`main.py` / `config.py`**: Entry points, setup, and configuration logic for running the Flask server.
*   **`app/__init__.py`**: Flask app factory initialization.
*   **`app/blueprints/rss/`**: Implements the primary route and logic:
    *   **`routes.py`**: Web endpoints for viewing the application.
    *   **`utils.py`**: Utility functions for data handling.
    *   **`ai.py`**: Manages direct connections and prompts to the LLM to generate "de-sensationalized" headlines.

### `Testing LLM/`
Various scripts used for scraping data, dataset manipulation, and testing the LLM's abilities to modify and neutralize sentiment.

**`NOS news articles source/`**
*   **`Download.py`**: Script designed to fetch, download, and store news items from the NOS.
*   **`news_neutralizer_multi.py`**: LLM testing script that experiment with translating sensational titles into factual, trivial sentences.
*   **`news_neutralizer.py`**: A more focused script that takes high-subjectivity headlines and uses the LLM to neutralize them, creating a "Nieuws-Normalisator" (News Normalizer).
*   **`add_sentiment_column.py`**: Analyzes the sentiment of articles and augments the dataset with the results.
*   **`add_embedding.py`**: Generates and attaches numerical embeddings to text data for similarity search and analysis.
*   **`selection.py` / `split_csv.py` / `test.py`**: Miscellaneous data wrangling tools and scripts to process CSV dumps of the articles.
*   **`run_stress_test.py`**: Script to benchmark and stress-test the LLM pipeline for performance and stability limits.
*   **`rss_crawler.py`**: A scraper specifically designed to gather updates from alternative RSS news sources.
