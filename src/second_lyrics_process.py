import json
import re
import os

from preprocess_lyrics import read_json, preprocessed_lyrics_to_json

def spelling_check(lyrics: str, word_mapping) -> str:
    for word, standardized in word_mapping.items():
        lyrics = re.sub(re.escape(word), standardized, lyrics)
    
    return lyrics


def main(file_path):
    correct_spelling_file = "data/correct_spelling.json"
    with open(correct_spelling_file, "r", encoding="utf-8") as f:
        correct_spelling = json.load(f)

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

        song["lyrics"] = corrected_spelling_lyrics
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