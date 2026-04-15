"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    
    user_profile = {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.4,
        "danceability": 0.5
    }

    recommendations = recommend_songs(user_profile, songs, k=5)

    print("\nTop recommendations:\n")
    for song, score, reasons in recommendations:
        print(f"Title: {song['title']}")
        print(f"Score: {score:.2f}")
        print("Reasons:")
        for reason in reasons:
            print(f"  - {reason}")
        print()  # Blank line between songs


if __name__ == "__main__":
    main()
