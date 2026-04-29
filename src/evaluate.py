"""Reliability harness for the VibeMatch applied AI recommender."""

from pathlib import Path

try:
    from .recommender import Recommender, configure_logging, evaluate_cases, load_song_objects
except ImportError:
    from recommender import Recommender, configure_logging, evaluate_cases, load_song_objects


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SONG_DATA_PATH = PROJECT_ROOT / "data" / "songs.csv"
LOG_PATH = PROJECT_ROOT / "logs" / "recommender.log"


CASES = [
    {
        "name": "high energy pop should stay upbeat",
        "query": "upbeat pop for a party",
        "profile": {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.9,
            "likes_acoustic": False,
        },
        "acceptable_genres": ["pop", "indie pop", "electronic"],
        "acceptable_moods": ["happy", "excited"],
    },
    {
        "name": "study request should avoid intense tracks",
        "query": "chill lofi study music",
        "profile": {
            "favorite_genre": "lofi",
            "favorite_mood": "chill",
            "target_energy": 0.35,
            "likes_acoustic": True,
        },
        "acceptable_genres": ["lofi", "ambient", "jazz"],
        "acceptable_moods": ["chill", "focused", "relaxed", "calm"],
    },
    {
        "name": "rock workout should retrieve intense catalog items",
        "query": "intense rock workout",
        "profile": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.85,
            "likes_acoustic": False,
        },
        "acceptable_genres": ["rock", "metal", "synthwave"],
        "acceptable_moods": ["intense", "excited", "angry"],
    },
    {
        "name": "relaxed jazz should prefer acoustic calm options",
        "query": "relaxed acoustic coffee shop jazz",
        "profile": {
            "favorite_genre": "jazz",
            "favorite_mood": "relaxed",
            "target_energy": 0.5,
            "likes_acoustic": True,
        },
        "acceptable_genres": ["jazz", "lofi", "folk", "reggae"],
        "acceptable_moods": ["relaxed", "chill", "calm"],
    },
    {
        "name": "unknown genre should still produce guarded recommendations",
        "query": "space banjo meditation",
        "profile": {
            "favorite_genre": "space banjo",
            "favorite_mood": "calm",
            "target_energy": 0.25,
            "likes_acoustic": True,
        },
        "acceptable_genres": ["ambient", "classical", "lofi", "folk"],
        "acceptable_moods": ["calm", "chill", "relaxed"],
    },
]


def main() -> None:
    configure_logging(str(LOG_PATH))
    recommender = Recommender(load_song_objects(str(SONG_DATA_PATH)))
    summary = evaluate_cases(recommender, CASES)

    print("VibeMatch reliability evaluation")
    print(f"Passed: {summary['passed']} / {summary['total']}")
    print(f"Average confidence: {summary['average_confidence']:.2f}")
    print()

    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} - {result['name']}")
        print(
            f"  top={result['top_song']} "
            f"genre={result['top_genre']} "
            f"avg_confidence={result['average_confidence']:.2f}"
        )
        for warning in result["warnings"]:
            print(f"  warning={warning}")


if __name__ == "__main__":
    main()
