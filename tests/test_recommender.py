from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    evaluate_cases,
    profile_from_prompt,
)
from src.spotify_client import build_spotify_queries, spotify_track_from_item

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_recommend_with_context_includes_trace_confidence_and_guardrails():
    user = UserProfile(
        favorite_genre="lofi",
        favorite_mood="chill",
        target_energy=0.4,
        likes_acoustic=True,
    )
    rec = make_small_recommender()

    trace = rec.recommend_with_context(user, query="chill lofi study", k=1)

    assert trace.plan
    assert trace.retrieved
    assert len(trace.recommendations) == 1
    assert trace.recommendations[0].song.genre == "lofi"
    assert 0 <= trace.recommendations[0].confidence <= 1


def test_profile_from_prompt_extracts_transparent_preferences():
    user = profile_from_prompt("I need chill lofi study music for rain")

    assert user.favorite_genre == "lofi"
    assert user.favorite_mood == "chill"
    assert user.target_energy < 0.5
    assert user.likes_acoustic is True


def test_evaluate_cases_returns_pass_fail_summary():
    rec = make_small_recommender()
    summary = evaluate_cases(
        rec,
        [
            {
                "name": "pop happy",
                "query": "happy pop",
                "profile": {
                    "favorite_genre": "pop",
                    "favorite_mood": "happy",
                    "target_energy": 0.8,
                    "likes_acoustic": False,
                },
                "acceptable_genres": ["pop"],
                "acceptable_moods": ["happy"],
            }
        ],
    )

    assert summary["total"] == 1
    assert summary["passed"] == 1
    assert summary["average_confidence"] > 0


def test_build_spotify_queries_uses_prompt_and_profile():
    user = UserProfile(
        favorite_genre="rock",
        favorite_mood="intense",
        target_energy=0.9,
        likes_acoustic=False,
    )

    queries = build_spotify_queries("intense rock workout", user)

    assert queries[0] == "intense rock workout"
    assert any("rock" in query for query in queries)
    assert any("high energy" in query or "workout" in query for query in queries)


def test_spotify_track_from_item_returns_rankable_track():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    item = {
        "id": "abc123",
        "name": "Happy Test Song",
        "popularity": 80,
        "preview_url": "https://example.com/preview.mp3",
        "external_urls": {"spotify": "https://open.spotify.com/track/abc123"},
        "artists": [{"name": "Test Artist"}],
        "album": {
            "name": "Test Album",
            "images": [{"url": "https://example.com/image.jpg"}],
        },
    }

    track = spotify_track_from_item(item, "pop upbeat", "happy pop", user)

    assert track.title == "Happy Test Song"
    assert track.artist == "Test Artist"
    assert track.url.endswith("abc123")
    assert track.confidence > 0.5
