import os
import json
import time
from lyricsgenius import Genius

REQUEST_DELAY_SECONDS = 0.75  # small pause between API calls to avoid rate limiting

def get_genius_client():
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "GENIUS_ACCESS_TOKEN environment variable is not set. "
            "Get a token from https://genius.com/api-clients and set it before running this script."
        )
    return Genius(token)


def read_json(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No file found at '{file_path}'. Check the path and try again.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_lyrics_to_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _normalize(text):
    """Normalize text for loose comparison: lowercase, strip, and unify quote characters."""
    text = text.strip().lower()
    # Map curly quotes/apostrophes to straight ones
    replacements = {
        "\u2018": "'", "\u2019": "'",   # ‘ ’
        "\u201c": '"', "\u201d": '"',   # “ ”
    }
    for curly, straight in replacements.items():
        text = text.replace(curly, straight)
    return text


def titles_match(requested_title, requested_artist, result):
    """Loose check that Genius's top result is actually the song we asked for."""
    requested_title = _normalize(requested_title)
    requested_artist = _normalize(requested_artist)
    result_title = _normalize(result.title or "")
    result_artist = _normalize(result.artist or "")
    return requested_title in result_title and requested_artist in result_artist


def get_lyrics(genius, song_title, artist_name):
    try:
        song_data = genius.search_song(song_title, artist_name)
    except Exception as e:
        print(f"  Error while searching for '{song_title}' by {artist_name}: {e}")
        return None

    if not song_data:
        return None

    if not titles_match(song_title, artist_name, song_data):
        print(
            f"  Warning: closest match was '{song_data.title}' by {song_data.artist}, "
            f"which doesn't look like a match for '{song_title}' by {artist_name}. Skipping."
        )
        return None

    return song_data.lyrics


def main(file_path):
    genius = get_genius_client()

    print(f"Reading songs from {file_path}...")
    data = read_json(file_path)

    for song in data:
        song_title = song["song"]
        artist_name = song["artist"]

        if song.get("lyrics"):
            print(f"Lyrics for '{song_title}' already exist. Skipping.\n")
            continue

        print(f"Searching for '{song_title}' by {artist_name}...")
        lyrics = get_lyrics(genius, song_title, artist_name)

        if lyrics:
            song["lyrics"] = lyrics
            print(f"Lyrics for '{song_title}' found and added.\n")
        else:
            song["lyrics"] = None
            print(f"Lyrics for '{song_title}' not found.\n")

        save_lyrics_to_json(data, file_path)

        time.sleep(REQUEST_DELAY_SECONDS)

    print("Done.")


if __name__ == "__main__":
    path = input("Input file path: ").strip()
    try:
        main(path)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Error: {e}")