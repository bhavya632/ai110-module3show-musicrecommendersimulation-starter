"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 
    
    profiles = {
    "1": {"name": "High-Energy Pop", "prefs": {"favorite_genre": "pop", "favorite_mood": "happy", "target_energy": 0.9}},
    "2": {"name": "Chill Lofi", "prefs": {"favorite_genre": "lofi", "favorite_mood": "chill", "target_energy": 0.4}},
    "3": {"name": "Deep Intense Rock", "prefs": {"favorite_genre": "rock", "favorite_mood": "intense", "target_energy": 0.8}},
    "4": {"name": "Moody Electronic", "prefs": {"favorite_genre": "electronic", "favorite_mood": "moody", "target_energy": 0.7}},
    "5": {"name": "Relaxed Jazz", "prefs": {"favorite_genre": "jazz", "favorite_mood": "relaxed", "target_energy": 0.5}},
    "6": {"name": "Sad Pop", "prefs": {"favorite_genre": "pop", "favorite_mood": "sad", "target_energy": 0.9}}
    }

    # Prompt user to select a profile
    print("Select a user profile:")
    for key, profile in profiles.items():
        print(f"{key}. {profile['name']}")
    choice = input("Enter number (1-6): ").strip()

    if choice in profiles:
        user_prefs = profiles[choice]["prefs"]
        print(f"Selected: {profiles[choice]['name']}")
    else:
        print("Invalid choice, using default.")
        user_prefs = profiles["1"]["prefs"]  # Default to High-Energy Pop

    recommendations = recommend_songs(user_prefs, songs, k=5)

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
