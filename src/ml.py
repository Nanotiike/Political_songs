import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "pre-processed_data"
 
POLITICAL_PATH = DATA_DIR / "political_songs.json"
NON_POLITICAL_PATH = DATA_DIR / "non-political_songs.json"
YEAR_END_PATH = DATA_DIR / "year-end_top20_songs.json"
 
# PLACEHOLDER - change to wherever you want the results saved
OUTPUT_PATH = BASE_DIR / "data" / "processed_data" / "year-end_top20_songs_predictions.json"

TEST_SIZE = 0.2         # 80% train / 20% test
TOP_N_WORDS = 20        # words to show per class in the report
THRESHOLD = 0.5         # probability at or above which a song is "political"

POLITICAL = 1
NON_POLITICAL = 0


def load_songs(path):
    with open(path, "r", encoding="utf-8") as f:
        songs = json.load(f)
    if not isinstance(songs, list):
        raise ValueError(f"{path} should contain a JSON list of songs.")
    return songs


def lyrics_of(song):
    return song.get("lyrics") or ""


def main():
    political = load_songs(POLITICAL_PATH)
    non_political = load_songs(NON_POLITICAL_PATH)
    print(f"Loaded {len(political)} political and {len(non_political)} "
          f"non-political songs.")

    texts = [lyrics_of(s) for s in political + non_political]
    labels = np.array([POLITICAL] * len(political) +
                      [NON_POLITICAL] * len(non_political))

    train_texts, test_texts, y_train, y_test = train_test_split(
        texts, labels, test_size=TEST_SIZE, stratify=labels
    )
    print(f"Train: {len(y_train)} songs | Test: {len(y_test)} songs")

    vectorizer = TfidfVectorizer(sublinear_tf=True, min_df=2)
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)

    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n=== TEST SET RESULTS ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}\n")
    print(classification_report(
        y_test, y_pred,
        labels=[NON_POLITICAL, POLITICAL],
        target_names=["non-political", "political"],
        zero_division=0,
    ))
    cm = confusion_matrix(y_test, y_pred, labels=[NON_POLITICAL, POLITICAL])
    print("Confusion matrix (rows = actual, columns = predicted)")
    print("                 non-political  political")
    print(f"non-political    {cm[0][0]:>13}  {cm[0][1]:>9}")
    print(f"political        {cm[1][0]:>13}  {cm[1][1]:>9}")

    words = vectorizer.get_feature_names_out()
    coefs = model.coef_[0]          # positive -> political, negative -> non-political
    order = np.argsort(coefs)
    n = min(TOP_N_WORDS, len(words))

    print(f"\n=== TOP {n} WORDS: POLITICAL ===")
    for i in order[::-1][:n]:
        print(f"{words[i]:<20} {coefs[i]:+.3f}")

    print(f"\n=== TOP {n} WORDS: NON-POLITICAL ===")
    for i in order[:n]:
        print(f"{words[i]:<20} {coefs[i]:+.3f}")

    year_end = load_songs(YEAR_END_PATH)
    X_year_end = vectorizer.transform([lyrics_of(s) for s in year_end])
    political_col = list(model.classes_).index(POLITICAL)
    p_political = model.predict_proba(X_year_end)[:, political_col]

    results = []
    for song, p in zip(year_end, p_political):
        pct_political = round(float(p) * 100, 2)
        out = dict(song)  # keep all original fields (artist, song, lyrics, year, ...)
        out["political_probability"] = pct_political
        out["non_political_probability"] = round(100 - pct_political, 2)
        out["prediction"] = "political" if p >= THRESHOLD else "non-political"
        results.append(out)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    n_pol = sum(r["prediction"] == "political" for r in results)
    print(f"\nClassified {len(results)} year-end songs: "
          f"{n_pol} political, {len(results) - n_pol} non-political.")
    print(f"Saved predictions to {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()