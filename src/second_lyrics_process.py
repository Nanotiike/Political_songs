import json
import re
import os

from preprocess_lyrics import read_json, preprocessed_lyrics_to_json, remove_punc_and_stopws, remove_non_english_words

def spelling_check(lyrics: str, word_mapping: dict[str, str]) -> str:
    # Match complete words or phrases only.
    pattern = r"(?<!\w)(?:" + "|".join(
        re.escape(word)
        for word in sorted(word_mapping, key=len, reverse=True)
    ) + r")(?!\w)"

    corrected_lyrics = re.sub(
        pattern,
        lambda match: word_mapping[match.group(0)],
        lyrics
    )

    return corrected_lyrics


def main(file_path):
    correct_spelling_file = "data/correct_spelling.json"
    stopwords_file = "data/stopwords-en.txt"
    removed_words_file = "data/removed_words.txt"

    with open(correct_spelling_file, "r", encoding="utf-8") as f:
        correct_spelling = json.load(f)

    with open(removed_words_file, "r", encoding="utf-8") as f:
        removed_words = set(word.strip() for word in f)

    with open(stopwords_file, "r", encoding="utf-8") as file:
        stopwords = set(word.strip() for word in file)

    print(f"Reading lyrics from {file_path}...")
    data = read_json(file_path)

    for song in data:
        song_title = song["song"]
        artist_name = song["artist"]
        song_lyrics = song["lyrics"]

        print(f"Preprocessing '{song_title}' by {artist_name}...")

        if song_lyrics is None:
            print(f"No lyrics found for '{song_title}'.\n")
            continue

        corrected_spelling_lyrics = spelling_check(song_lyrics, correct_spelling)

        preprocessed_lyrics = remove_punc_and_stopws(corrected_spelling_lyrics, stopwords)

        preprocessed_lyrics = remove_non_english_words(preprocessed_lyrics, removed_words)

        song["lyrics"] = preprocessed_lyrics
        print(f"Lyrics for '{song_title}' preprocessed.\n")

        # Write the pre-processed results to a new JSON file
        os.makedirs("data/pre-processed_data/second_processing", exist_ok=True)
    
        preprocessed_path=os.path.join("data/pre-processed_data/second_processing", os.path.basename(file_path))
    
        preprocessed_lyrics_to_json(data, preprocessed_path)
    
        print(f"Pre-processed lyrics saved to '{preprocessed_path}'.")

if __name__ == "__main__":
    path = input("Input file path: ").strip()
    try:
        main(path)
    except FileNotFoundError as e:
        print(f"Error: {e}")