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

## Recordtelling met selection.py

Zet de CSV-bestandsnaam in `.env`:

`CSV_FILE_NAME=dutch-news-articles.csv`

Voer daarna het script uit:

`python3 selection.py`

Het script telt het aantal records (rijen zonder header) in het opgegeven CSV-bestand.

