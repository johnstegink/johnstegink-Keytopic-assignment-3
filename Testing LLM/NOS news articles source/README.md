# NOS news articles



## Dutch News Articles

This dataset contains all the articles published by the NOS as of the 1st of January 2010. The data is obtained by scraping the NOS website. The NOS is one of the biggest (online) news organizations in the Netherlands.

### Features:

- **datetime**: date and time of publication of the article.
- **title**: the title of the news article.
- **content**: the content of the news article.
- **category**: the category under which the NOS filed the article.
- **url**: link to the original article.

### About the data

The title and content of features somewhat clean. Meaning extra whites spaces and newlines are removed. Furthermore, these features are normalized (NFKD). The NOS also publishes liveblogs. The posts in this live blog are not part of this dataset.

Downloaded from: [Kaggle](https://www.kaggle.com/datasets/maxscheijen/dutch-news-articles)


## Setup Instructions

### 1. Download Data from Kaggle

To use this dataset, you need to download it from Kaggle [Kaggle - Dutch News Articles](https://www.kaggle.com/datasets/maxscheijen/dutch-news-articles)
### 2. Configure Environment Variables

Create a `.env` file in this directory with the following variables:

```env
CSV_FILE_NAME_YEAR_ARTICLES=/path/to/articles_YYYY.csv
CSV_OUTPUT_SENTIMENT_FILE_PATH=/path/to/output/directory
```

#### Environment Variables Explanation

| Variable | Description | Example |
|----------|-------------|---------|
| CSV_FILE_NAME_ALL_ARTICLES=dutch-news-articles.csv | Path to the input CSV file containing all articles. | `/Users/john/Dropbox/NOS news articles source/dutch-news-articles.csv` |
| `CSV_FILE_NAME_YEAR_ARTICLES` | Path pattern to input CSV files with a `{year}` placeholder. The script will process all files matching this pattern. | `/Users/john/Dropbox/NOS news articles source/articles_{year}.csv` |
| `CSV_OUTPUT_SENTIMENT_FILE_PATH` | Directory path where the processed output files (with sentiment analysis) will be saved. The script creates this directory if it doesn't exist. | `/Users/john/Dropbox/NOS news articles source/output/sentiment/` |

#### Example `.env` file:

```env
CSV_FILE_NAME_ALL_ARTICLES=dutch-news-articles.csv
CSV_FILE_NAME_YEAR_ARTICLES=articles_{year}.csv
CSV_OUTPUT_SENTIMENT_FILE_PATH=with_sentiment_analysis
```

### 3. Run the Split CSV Script

Before running the sentiment analysis, split the combined dataset into yearly files:

```bash
python split_csv.py
```

**What it does:**
- Reads the combined CSV file (`CSV_FILE_NAME_ALL_ARTICLES`)
- Splits all articles by year based on their publication date
- Creates separate CSV files for each year (e.g., `articles_2010.csv`, `articles_2011.csv`, etc.)
- Writes output files according to the pattern specified in `CSV_FILE_NAME_YEAR_ARTICLES`

**Output example:**
```
Wrote 45832 records using pattern: articles_{year}.csv
```

### 4. Run the Sentiment Analysis Script

Once the data is split by year, run the sentiment analysis:

```bash
python add_sentiment_column.py
```

**What it does:**
- Reads each yearly CSV file matching the pattern in `CSV_FILE_NAME_YEAR_ARTICLES`
- Analyzes the sentiment of each article title using Dutch language processing (TextBlob with PatternAnalyzer)
- Adds two new columns to each file:
  - `polarity`: Sentiment polarity score ranging from -1 (negative) to 1 (positive)
  - `subjectivity`: Subjectivity score ranging from 0 (objective) to 1 (subjective)
- Saves the results as tab-delimited files to `CSV_OUTPUT_SENTIMENT_FILE_PATH`

**Output files example:**
- Input: `articles_2020.csv`
- Output: `articles_2020.txt` (tab-delimited with sentiment columns added)




