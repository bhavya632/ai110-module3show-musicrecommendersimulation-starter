from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        def song_score(song: Song) -> float:
            score = 0.0

            if song.genre == user.favorite_genre:
                score += 2.0

            if song.mood == user.favorite_mood:
                score += 1.0

            score += 1 - abs(song.energy - user.target_energy)
            return score

        ranked_songs = sorted(self.songs, key=song_score, reverse=True)
        return ranked_songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        reasons = []

        if song.genre == user.favorite_genre:
            reasons.append(f"it matches your favorite genre ({song.genre})")

        if song.mood == user.favorite_mood:
            reasons.append(f"it fits your preferred mood ({song.mood})")

        energy_diff = abs(song.energy - user.target_energy)
        reasons.append(
            f"its energy level is close to your target ({song.energy:.1f} vs {user.target_energy:.1f})"
        )

        if user.likes_acoustic and song.acousticness >= 0.5:
            reasons.append("it has a more acoustic sound")
        elif not user.likes_acoustic and song.acousticness < 0.5:
            reasons.append("it leans away from an acoustic sound")

        return f"{song.title} by {song.artist} was recommended because " + ", ".join(reasons) + "."

def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file into a list of dictionaries."""
    songs = []
    with open(csv_path, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            song = {
                'id': int(row['id']),
                'title': row['title'],
                'artist': row['artist'],
                'genre': row['genre'],
                'mood': row['mood'],
                'energy': float(row['energy']),
                'tempo_bpm': float(row['tempo_bpm']),
                'valence': float(row['valence']),
                'danceability': float(row['danceability']),
                'acousticness': float(row['acousticness'])
            }
            songs.append(song)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Scores a song based on user preferences and returns the score with reasons."""
    score = 0.0
    reasons = []
    
    # Genre match
    if song['genre'] == user_prefs['favorite_genre']:
        score += 2.0
        reasons.append("genre match (+2.0)")
    
    # Mood match
    if song['mood'] == user_prefs['favorite_mood']:
        score += 1.0
        reasons.append("mood match (+1.0)")
    
    # Energy similarity
    energy_diff = abs(song['energy'] - user_prefs['target_energy'])
    energy_sim = 1 - energy_diff
    score += energy_sim
    reasons.append(f"energy similarity (+{energy_sim:.2f})")
    
    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, List[str]]]:
    """Recommends the top k songs based on user preferences."""
    # Score each song and collect results
    scored_songs = [
        (song, *score_song(user_prefs, song))
        for song in songs
    ]
    
    # Sort by score in descending order
    scored_songs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top k
    return scored_songs[:k]
