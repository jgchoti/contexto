from sentence_transformers import SentenceTransformer
import requests
from backend.database import initialize_word_list

def setup_initial_words():
    url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa-no-swears.txt"
    response = requests.get(url)
    words = response.text.strip().split('\n')

    print(f"Downloaded {len(words)} words")
    print("Generating embeddings...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(words, convert_to_numpy=True)
    print("Storing in MongoDB...")
    initialize_word_list(words, embeddings)
    print("✅ Setup complete!")

if __name__ == "__main__":
    setup_initial_words()