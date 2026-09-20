# Political_songs

A mini-project done for the Data Science course from University of Helsinki. 

The topic of this project is to see if the most popular songs have political content, and whether the amount or the content itself has changed within the last 10 years.

## Methods

We will do use supervised machine learning, to go through a dataset that includes list of song lyrics we know are political, to form a basis for detecting whether a song is political or not. Then we will apply this to the top 20 most popular songs of each of the last 10 years.

## Data acquisition

We will acquire the data through data mining with the [LyricsGenious API](https://lyricsgenius.readthedocs.io/en/master/index.html).

There is a script, lyrics_extraction.py, which gets the lyrics. You can use it by running it and giving it a json with a list of songs with the artist and song title written. For this you need to have an API token from [here](https://genius.com/api-clients). 

## How to start

Sync the dependencies with your environment by running:
```
uv sync
```
Then you can run any of the scripts with.
```
uv run [file].py
```
