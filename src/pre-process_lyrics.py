import string
import json
import os
import re


def downcase_lyrics(lyrics: str) -> str:
    return lyrics.lower()

def normalize_apostrophe(lyrics: str) -> str:
    replacements = {
            "\u2018": "'", "\u2019": "'",   # ‘ ’
            "\u201c": '"', "\u201d": '"',   # “ ”
        }
    for curly, straight in replacements.items():
        lyrics = lyrics.replace(curly, straight)
    return lyrics

def remove_bracket_contents(lyrics: str) -> str:
    start = "["
    end = "]"
    pattern = "%s(.*?)%s" % (re.escape(start), re.escape(end))
    cleaned_str = re.sub(pattern, "", lyrics)
    return cleaned_str

def remove_newline_char(lyrics: str) -> str:
    # Remove any number of consecutive whitespaces/newline char etc. and replace with a single whitespace
    cleaned_str = re.sub(r"\s+", " ", lyrics).strip()
    return cleaned_str

def standardize_word_beginnings(lyrics: str, word_mapping) -> str:
    for word, standardized in word_mapping.items():
        lyrics = re.sub(re.escape(word), standardized, lyrics)

    return lyrics

def standardize_word_endings(lyrics: str) -> str:
    pattern = r"\b(\w+)in'(?!\w)"
    cleaned_str = re.sub(pattern, r"\1ing", lyrics)
    return cleaned_str

def standardize_words(lyrics: str, word_mapping) -> str:
    # Standardize word beginnings
    lyrics = standardize_word_beginnings(lyrics, word_mapping)

    # Standardize word endings
    lyrics = standardize_word_endings(lyrics)

    return lyrics
    
def remove_punc_and_stopws(lyrics: str, stopwords: set) -> str:
    lyrics = lyrics.translate(str.maketrans("", "", string.punctuation))
    words = lyrics.split()

    filtered_lyrics = []

    for word in words:
        if word not in stopwords:
            filtered_lyrics.append(word)

    return " ".join(filtered_lyrics)


def read_json(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No file found at '{file_path}'. Check the path and try again.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def preprocessed_lyrics_to_json(data, preprocessed_path):
    with open(preprocessed_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main(file_path):
    # Open and load standardized words
    standardized_words = "data/standardized_words.json"
    with open(standardized_words, "r", encoding="utf-8") as f:
        standardized_word_mapping = json.load(f)

    # Open and load stopwords
    stopwords_file = "data/stopwords-en.txt"
    with open(stopwords_file, "r") as file:
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

        # Remove brackets and [] contents
        brackets_removed_lyrics = remove_bracket_contents(song_lyrics)

        # Normalize apostrophe
        norm_apostr_lyrics = normalize_apostrophe(brackets_removed_lyrics)

        # Lowercase lyrics
        lowercased_lyrics = downcase_lyrics(norm_apostr_lyrics)

        # Remove newline char and double spaces
        single_line_lyrics = remove_newline_char(lowercased_lyrics)

        # Standardized lyrics: words starting or ending with ' are standardized
        # + some other contractions are spelled out so that stopword removal works
        standardized_lyrics = standardize_words(single_line_lyrics, standardized_word_mapping)

        # Remove stopwords and punctuation marks
        preprocessed_lyrics = remove_punc_and_stopws(standardized_lyrics, stopwords)

        # Store the preprocessed lyrics in memory
        song["lyrics"] = preprocessed_lyrics
        print(f"Lyrics for '{song_title}' preprocessed.\n")

    # Write the pre-processed results to a new JSON file
    os.makedirs("data/pre-processed_data", exist_ok=True)

    preprocessed_path=os.path.join("data/pre-processed_data/", os.path.basename(file_path))

    preprocessed_lyrics_to_json(data, preprocessed_path)

    print(f"Pre-processed lyrics saved to '{preprocessed_path}'.")


if __name__ == "__main__":
    path = input("Input file path: ").strip()
    try:
        main(path)
    except FileNotFoundError as e:
        print(f"Error: {e}")