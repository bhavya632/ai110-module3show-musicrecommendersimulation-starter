from typing import List, Dict, Tuple, Iterable
from dataclasses import dataclass
import csv
import logging
from pathlib import Path

LOGGER = logging.getLogger("vibematch")

GENRE_NEIGHBORS = {
    "pop": {"indie pop", "electronic", "synthwave"},
    "indie pop": {"pop", "lofi"},
    "lofi": {"ambient", "jazz", "folk"},
    "rock": {"metal", "synthwave"},
    "metal": {"rock"},
    "electronic": {"synthwave", "pop", "hip-hop"},
    "synthwave": {"electronic", "pop", "rock"},
    "jazz": {"lofi", "folk", "reggae"},
    "ambient": {"lofi", "classical"},
    "classical": {"ambient", "folk"},
    "reggae": {"jazz", "hip-hop"},
    "hip-hop": {"electronic", "reggae"},
    "folk": {"country", "lofi", "classical"},
    "country": {"folk"},
}

MOOD_NEIGHBORS = {
    "happy": {"excited", "relaxed"},
    "excited": {"happy", "intense"},
    "intense": {"excited", "angry", "focused"},
    "angry": {"intense"},
    "chill": {"relaxed", "focused", "calm"},
    "relaxed": {"chill", "happy", "nostalgic", "calm"},
    "focused": {"chill", "intense", "moody"},
    "moody": {"sad", "focused", "nostalgic"},
    "sad": {"moody", "nostalgic"},
    "nostalgic": {"sad", "relaxed", "moody"},
    "calm": {"chill", "relaxed"},
}

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

@dataclass
class RetrievedSong:
    """A song plus the retrieval evidence used by the applied AI workflow."""
    song: Song
    retrieval_score: float
    evidence: List[str]

@dataclass
class RecommendationResult:
    """Final recommendation with score, confidence, and guardrail notes."""
    song: Song
    score: float
    confidence: float
    reasons: List[str]
    guardrails: List[str]

@dataclass
class AgentTrace:
    """Observable intermediate steps for the agentic workflow."""
    query: str
    plan: List[str]
    retrieved: List[RetrievedSong]
    recommendations: List[RecommendationResult]
    warnings: List[str]

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        ranked_songs = sorted(self.songs, key=lambda song: self.score_song(user, song)[0], reverse=True)
        return ranked_songs[:k]

    def score_song(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        score = 0.0
        reasons = []

        if song.genre == user.favorite_genre:
            score += 2.0
            reasons.append("exact genre match (+2.00)")
        elif song.genre in GENRE_NEIGHBORS.get(user.favorite_genre, set()):
            score += 1.0
            reasons.append("nearby genre match (+1.00)")

        if song.mood == user.favorite_mood:
            score += 1.0
            reasons.append("exact mood match (+1.00)")
        elif song.mood in MOOD_NEIGHBORS.get(user.favorite_mood, set()):
            score += 0.5
            reasons.append("nearby mood match (+0.50)")

        energy_sim = clamp(1 - abs(song.energy - user.target_energy), 0.0, 1.0)
        score += energy_sim
        reasons.append(f"energy similarity (+{energy_sim:.2f})")

        if user.likes_acoustic:
            acoustic_score = song.acousticness * 0.5
            reasons.append(f"acoustic fit (+{acoustic_score:.2f})")
        else:
            acoustic_score = (1 - song.acousticness) * 0.5
            reasons.append(f"non-acoustic fit (+{acoustic_score:.2f})")
        score += acoustic_score

        return score, reasons

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

    def retrieve(self, user: UserProfile, query: str = "", limit: int = 8) -> List[RetrievedSong]:
        """Retrieve likely-relevant songs before ranking, similar to a tiny RAG step."""
        query_terms = {term.strip().lower() for term in query.replace(",", " ").split() if term.strip()}
        retrieved = []

        for song in self.songs:
            evidence = []
            retrieval_score = 0.0
            searchable = {
                song.title.lower(),
                song.artist.lower(),
                song.genre.lower(),
                song.mood.lower(),
            }

            if song.genre == user.favorite_genre:
                retrieval_score += 2.0
                evidence.append(f"catalog genre={song.genre}")
            elif song.genre in GENRE_NEIGHBORS.get(user.favorite_genre, set()):
                retrieval_score += 1.0
                evidence.append(f"adjacent genre for {user.favorite_genre}")

            if song.mood == user.favorite_mood:
                retrieval_score += 1.5
                evidence.append(f"catalog mood={song.mood}")
            elif song.mood in MOOD_NEIGHBORS.get(user.favorite_mood, set()):
                retrieval_score += 0.75
                evidence.append(f"adjacent mood for {user.favorite_mood}")

            energy_fit = clamp(1 - abs(song.energy - user.target_energy), 0.0, 1.0)
            if energy_fit >= 0.75:
                retrieval_score += energy_fit
                evidence.append("energy is close to target")

            for term in query_terms:
                if any(term in field for field in searchable):
                    retrieval_score += 0.4
                    evidence.append(f"query term '{term}' matched catalog")

            if retrieval_score > 0:
                retrieved.append(RetrievedSong(song, retrieval_score, evidence))

        retrieved.sort(key=lambda item: item.retrieval_score, reverse=True)
        LOGGER.info("retrieved_candidates", extra={"count": len(retrieved), "query": query})
        return retrieved[:limit]

    def recommend_with_context(
        self,
        user: UserProfile,
        query: str = "",
        k: int = 5,
        min_confidence: float = 0.45,
    ) -> AgentTrace:
        """Plan, retrieve, rank, check, and return explainable recommendations."""
        plan = [
            "Validate user preferences",
            "Retrieve songs with matching catalog evidence",
            "Rank retrieved songs with content-based scoring",
            "Check confidence, diversity, and safety guardrails",
        ]
        warnings = validate_user_profile(user, self.songs)
        retrieved = self.retrieve(user, query=query, limit=max(k * 2, 6))

        if not retrieved:
            warnings.append("No strong retrieval matches found; falling back to full catalog ranking.")
            retrieved = [RetrievedSong(song, 0.0, ["fallback catalog candidate"]) for song in self.songs]

        ranked = []
        max_possible = 5.0
        for item in retrieved:
            score, reasons = self.score_song(user, item.song)
            score += item.retrieval_score * 0.2
            reasons.extend(item.evidence[:2])
            confidence = clamp(score / max_possible, 0.0, 1.0)
            guardrails = []
            if confidence < min_confidence:
                guardrails.append("low confidence: weak match to stated preferences")
            if item.song.energy > 0.9 and user.target_energy < 0.35:
                guardrails.append("energy mismatch: may be too intense")
            if item.song.acousticness < 0.2 and user.likes_acoustic:
                guardrails.append("acoustic mismatch: track is mostly electronic/amplified")
            ranked.append(RecommendationResult(item.song, score, confidence, reasons, guardrails))

        ranked.sort(key=lambda result: result.score, reverse=True)
        final = diversify_results(ranked, k=k)
        if len({result.song.genre for result in final}) == 1 and len(final) > 2:
            warnings.append("Top results are genre-concentrated; consider expanding the catalog.")

        return AgentTrace(query=query, plan=plan, retrieved=retrieved, recommendations=final, warnings=warnings)

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

def load_song_objects(csv_path: str) -> List[Song]:
    """Loads songs from CSV into typed Song objects."""
    return [Song(**song) for song in load_songs(csv_path)]

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

def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))

def validate_user_profile(user: UserProfile, songs: Iterable[Song]) -> List[str]:
    warnings = []
    catalog = list(songs)
    genres = {song.genre for song in catalog}
    moods = {song.mood for song in catalog}

    if not 0 <= user.target_energy <= 1:
        warnings.append("target_energy should be between 0 and 1; confidence may be unreliable")
    if user.favorite_genre not in genres and user.favorite_genre not in GENRE_NEIGHBORS:
        warnings.append(f"favorite_genre '{user.favorite_genre}' is not represented in the catalog")
    if user.favorite_mood not in moods and user.favorite_mood not in MOOD_NEIGHBORS:
        warnings.append(f"favorite_mood '{user.favorite_mood}' is not represented in the catalog")
    return warnings

def diversify_results(results: List[RecommendationResult], k: int) -> List[RecommendationResult]:
    """Keep the strongest matches while avoiding an all-one-genre list when possible."""
    selected = []
    seen_genres = set()

    for result in results:
        if len(selected) >= k:
            break
        if result.song.genre not in seen_genres or len(selected) < 2:
            selected.append(result)
            seen_genres.add(result.song.genre)

    for result in results:
        if len(selected) >= k:
            break
        if result not in selected:
            selected.append(result)

    selected.sort(key=lambda result: result.score, reverse=True)
    return selected[:k]

def profile_from_prompt(prompt: str, default_acoustic: bool = False) -> UserProfile:
    """Build a user profile from a natural-language prompt using transparent rules."""
    text = prompt.lower()
    genres = sorted(GENRE_NEIGHBORS.keys(), key=len, reverse=True)
    moods = sorted(MOOD_NEIGHBORS.keys(), key=len, reverse=True)

    favorite_genre = next((genre for genre in genres if genre in text), "pop")
    favorite_mood = next((mood for mood in moods if mood in text), "happy")
    likes_acoustic = default_acoustic or any(word in text for word in ["acoustic", "calm", "study", "rain", "coffee"])

    if any(word in text for word in ["workout", "high energy", "party", "run", "hype"]):
        target_energy = 0.9
    elif any(word in text for word in ["sleep", "calm", "study", "chill", "relax", "rain"]):
        target_energy = 0.35
    elif any(word in text for word in ["focus", "coding", "work"]):
        target_energy = 0.55
    else:
        target_energy = 0.7

    return UserProfile(
        favorite_genre=favorite_genre,
        favorite_mood=favorite_mood,
        target_energy=target_energy,
        likes_acoustic=likes_acoustic,
    )

def configure_logging(log_path: str = "logs/recommender.log") -> None:
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

def evaluate_cases(recommender: Recommender, cases: List[Dict]) -> Dict:
    """Run a compact reliability harness over predefined recommendation cases."""
    results = []
    for case in cases:
        user = UserProfile(**case["profile"])
        trace = recommender.recommend_with_context(user, query=case.get("query", ""), k=3)
        top = trace.recommendations[0] if trace.recommendations else None
        passed = bool(top) and (
            top.song.genre in case.get("acceptable_genres", [])
            or top.song.mood in case.get("acceptable_moods", [])
        )
        avg_confidence = (
            sum(result.confidence for result in trace.recommendations) / len(trace.recommendations)
            if trace.recommendations
            else 0.0
        )
        results.append(
            {
                "name": case["name"],
                "passed": passed,
                "top_song": top.song.title if top else "none",
                "top_genre": top.song.genre if top else "none",
                "average_confidence": avg_confidence,
                "warnings": trace.warnings,
            }
        )

    passed_count = sum(1 for result in results if result["passed"])
    avg_conf = sum(result["average_confidence"] for result in results) / len(results) if results else 0.0
    return {
        "passed": passed_count,
        "total": len(results),
        "average_confidence": avg_conf,
        "results": results,
    }
