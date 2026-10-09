import string
import json
import os
import re


def downcase_lyrics(lyrics: str) -> str:
    return lyrics.lower()

def normalize_utf(lyrics: str) -> str:
    replacements = {
            "\u2018": "'", "\u2019": "'",   # ‘ ’
            "\u201c": '"', "\u201d": '"',   # “ ”
            "\ufeff": "", "\u200b": "",     # BOM zero-width space
            "\u2005": " ", "\u205f": " ",   # Four-per-em space medium mathematical space
            "\u2013": " ", "\u2014": " ",   # en dash em dash
            "\u0435": "e", "…": " "         # e …
        }
    for curly, straight in replacements.items():
        lyrics = lyrics.replace(curly, straight)
    return lyrics

def remove_bracket_contents(lyrics: str) -> str:
    start = "["
    end = "]"
    pattern = "%s(.*?)%s" % (re.escape(start), re.escape(end))
    cleaned_str = re.sub(pattern, "", lyrics, flags=re.DOTALL)
    return cleaned_str

def remove_newline_char(lyrics: str) -> str:
    # Remove any number of consecutive whitespaces/newline char etc. and replace with a single whitespace
    cleaned_str = re.sub(r"\s+", " ", lyrics).strip()
    return cleaned_str

def standardize_word_beginnings(lyrics: str, word_mapping) -> str:
    for word, standardized in word_mapping.items():
        lyrics = re.sub(re.escape(word), standardized, lyrics)

    return lyrics

def standardize_word_endings_ing(lyrics: str) -> str:
    pattern = r"\b(\w+)in'(?!\w)"
    cleaned_str = re.sub(pattern, r"\1ing", lyrics)
    return cleaned_str

def standardize_word_endings_will(lyrics: str) -> str:
    pattern = r"\b(\w+)'ll"
    cleaned_str = re.sub(pattern, r"\1 will", lyrics)
    return cleaned_str

def standardize_words(lyrics: str, word_mapping) -> str:
    # Standardize word beginnings
    lyrics = standardize_word_beginnings(lyrics, word_mapping)

    # Standardize word endings
    lyrics = standardize_word_endings_ing(lyrics)
    lyrics = standardize_word_endings_will(lyrics)

    return lyrics
    
def remove_punc_and_stopws(lyrics: str, stopwords: set) -> str:
    lyrics = lyrics.translate(str.maketrans("", "", string.punctuation))
    words = lyrics.split()

    filtered_lyrics = []

    for word in words:
        if word not in stopwords:
            filtered_lyrics.append(word)

    return " ".join(filtered_lyrics)

def remove_non_english_words(lyrics: str, remove_words: set) -> str:
    words = lyrics.split()

    filtered_lyrics = []

    for word in words:
        if word not in remove_words:
            filtered_lyrics.append(word)

    return " ".join(filtered_lyrics)

def save_word(word: str, filename: str):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{word}\n")

def show_context(lyrics: list, word: str, context_words=3):
    words = lyrics

    for i, current_word in enumerate(words):
        if current_word == word:
            start = max(0, i - context_words)
            end = min(len(words), i + context_words + 1)

            print("Context:")
            print(" ".join(words[start:end]))
            print()

def review_word(word: str, lyrics: list, removed_file: str, approved_file: str) -> str:
    print(f"Flagged word: {word}")
    show_context(lyrics, word)

    while True:
        answer = input(f"Remove this word: {word} ? [y (yes) / n (no)]: ").strip().lower()

        if answer == "y":
            save_word(word, removed_file)
            print(f"Added '{word}' to {removed_file}.")
            return "removed"

        elif answer == "n":
            save_word(word, approved_file)
            print(f"Added '{word}' to {approved_file}.")
            return "approved"

        else:
            print("Enter a valid input: y or n.")

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

    # Open and load english words
    english_words_file = "data/english_words.txt"
    with open(english_words_file, "r", encoding="utf-8") as f:
        english_words = set(word.strip() for word in f)

    # Open and load words that should be removed in addition to stopwords
    removed_words_file = "data/removed_words.txt"
    with open(removed_words_file, "r", encoding="utf-8") as f:
        removed_words = set(word.strip() for word in f)

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

        # Normalize unicode
        normalize_lyrics = normalize_utf(brackets_removed_lyrics)

        # Lowercase lyrics
        lowercased_lyrics = downcase_lyrics(normalize_lyrics)

        # Remove newline char and double spaces
        single_line_lyrics = remove_newline_char(lowercased_lyrics)

        # Standardized lyrics: words starting or ending with ' are standardized
        # + some other contractions are spelled out so that stopword removal works
        standardized_lyrics = standardize_words(single_line_lyrics, standardized_word_mapping)

        # Remove stopwords and punctuation marks
        stopwords_rem_lyrics = remove_punc_and_stopws(standardized_lyrics, stopwords)

        stopwords_rem_list = stopwords_rem_lyrics.split()
        for word in stopwords_rem_list:
            print(word)
            if (word not in stopwords and word not in removed_words and word not in english_words):
                decision = review_word(word, stopwords_rem_list, removed_words_file, english_words_file)

                if decision == "removed":
                    removed_words.add(word)

                elif decision == "approved":
                    english_words.add(word)

        preprocessed_lyrics = remove_non_english_words(stopwords_rem_lyrics, removed_words)

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