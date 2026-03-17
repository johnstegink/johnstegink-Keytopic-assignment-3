## Download the news articles. Copied manually to this repository
import kagglehub

# Download latest version
path = kagglehub.dataset_download("maxscheijen/dutch-news-articles")

print("Path to dataset files:", path)