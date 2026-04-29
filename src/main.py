"""Command line runner for the VibeMatch applied AI music recommender."""

import argparse
from pathlib import Path
from typing import Optional

try:
    from .recommender import (
        Recommender,
        UserProfile,
        configure_logging,
        evaluate_cases,
        load_song_objects,
        profile_from_prompt,
    )
    from .spotify_client import (
        SpotifyAPIError,
        SpotifyClient,
        SpotifyConfigurationError,
        build_spotify_queries,
    )
except ImportError:
    from recommender import (
        Recommender,
        UserProfile,
        configure_logging,
        evaluate_cases,
        load_song_objects,
        profile_from_prompt,
    )
    from spotify_client import (
        SpotifyAPIError,
        SpotifyClient,
        SpotifyConfigurationError,
        build_spotify_queries,
    )


PROFILES = {
    "1": {
        "name": "High-Energy Pop",
        "profile": UserProfile("pop", "happy", 0.9, False),
        "query": "upbeat pop for a party",
    },
    "2": {
        "name": "Chill Lofi",
        "profile": UserProfile("lofi", "chill", 0.4, True),
        "query": "chill lofi study music",
    },
    "3": {
        "name": "Deep Intense Rock",
        "profile": UserProfile("rock", "intense", 0.8, False),
        "query": "intense rock workout",
    },
    "4": {
        "name": "Moody Electronic",
        "profile": UserProfile("electronic", "moody", 0.7, False),
        "query": "moody electronic night drive",
    },
    "5": {
        "name": "Relaxed Jazz",
        "profile": UserProfile("jazz", "relaxed", 0.5, True),
        "query": "relaxed acoustic coffee shop jazz",
    },
    "6": {
        "name": "Sad Pop",
        "profile": UserProfile("pop", "sad", 0.6, False),
        "query": "sad pop late night",
    },
}

EVALUATION_CASES = [
    {
        "name": "High energy pop",
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
        "name": "Chill study",
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
        "name": "Rock workout",
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
        "name": "Unknown genre guardrail",
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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SONG_DATA_PATH = PROJECT_ROOT / "data" / "songs.csv"
LOG_PATH = PROJECT_ROOT / "logs" / "recommender.log"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the VibeMatch applied AI recommender.")
    parser.add_argument("--profile", choices=PROFILES.keys(), help="Run a saved profile without prompting.")
    parser.add_argument("--query", help="Natural-language listening request.")
    parser.add_argument("--k", type=int, default=5, help="Number of recommendations to show.")
    parser.add_argument("--show-trace", action="store_true", help="Print retrieval and planning steps.")
    parser.add_argument("--spotify", action="store_true", help="Fetch real Spotify catalog recommendations.")
    parser.add_argument("--market", default="US", help="Spotify market code, such as US, GB, or CA.")
    return parser


def build_recommender() -> Recommender:
    configure_logging(str(LOG_PATH))
    songs = load_song_objects(str(SONG_DATA_PATH))
    return Recommender(songs)


def is_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        return False
    return get_script_run_ctx() is not None


def render_streamlit_app() -> None:
    import streamlit as st

    st.set_page_config(page_title="VibeMatch Recommender", page_icon="V", layout="wide")
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        [data-testid="stMetric"] {
            background: rgba(148, 163, 184, 0.10);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 8px;
            padding: 0.8rem 0.9rem;
        }
        [data-testid="stMetric"] [data-testid="stMetricLabel"] p {
            color: rgba(148, 163, 184, 0.95);
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: inherit;
        }
        div[data-testid="stVerticalBlock"] > div:has(> div.recommendation-card) {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            background: rgba(148, 163, 184, 0.06);
        }
        .recommendation-card h3 { margin-bottom: 0.1rem; }
        .muted { color: #64748b; font-size: 0.95rem; }
        .small-label { color: #475569; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("VibeMatch")
    st.caption("An applied AI music recommender with retrieval, confidence scoring, guardrails, and evaluation.")

    recommender = build_recommender()
    spotify_client = SpotifyClient()
    songs = recommender.songs
    genres = sorted({song.genre for song in songs})
    moods = sorted({song.mood for song in songs})

    with st.sidebar:
        st.header("Controls")
        mode = st.radio(
            "Input mode",
            ["Saved profile", "Natural-language request", "Custom profile"],
        )
        k = st.slider("Number of recommendations", min_value=1, max_value=5, value=3)
        min_confidence = st.slider("Minimum displayed confidence", 0.0, 1.0, 0.0, 0.05)
        use_spotify = st.checkbox("Use real Spotify catalog", value=False)
        show_trace = st.checkbox("Show reasoning trace", value=True)
        if use_spotify and not spotify_client.is_configured:
            st.warning("Spotify credentials are missing. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")

    query: str
    user: Optional[UserProfile]
    user = None

    if mode == "Saved profile":
        with st.sidebar:
            profile_names = {item["name"]: key for key, item in PROFILES.items()}
            selected_name = st.selectbox("Choose a listener profile", list(profile_names.keys()), index=1)
            selected = PROFILES[profile_names[selected_name]]
            query = st.text_input("Request context", value=selected["query"])
            user = selected["profile"]
    else:
        with st.sidebar:
            if mode == "Natural-language request":
                query = st.text_area("Listening request", value="chill lofi study music", height=90)
                if query.strip():
                    user = profile_from_prompt(query)
                else:
                    st.info("Enter a request to generate recommendations.")
            else:
                query = st.text_input("Request context", value="focused electronic work session")
                favorite_genre = st.selectbox("Favorite genre", genres, index=genres.index("electronic") if "electronic" in genres else 0)
                favorite_mood = st.selectbox("Favorite mood", moods, index=moods.index("focused") if "focused" in moods else 0)
                target_energy = st.slider("Target energy", 0.0, 1.0, 0.65, 0.05)
                likes_acoustic = st.checkbox("Prefers acoustic sound", value=False)
                user = UserProfile(favorite_genre, favorite_mood, target_energy, likes_acoustic)

    if user is None:
        return

    trace = recommender.recommend_with_context(user, query=query, k=k)
    visible_recommendations = [
        result for result in trace.recommendations if result.confidence >= min_confidence
    ]
    spotify_tracks = []
    spotify_error = None
    if use_spotify:
        try:
            spotify_tracks = spotify_client.recommend_from_prompt(query, user, limit=max(k, 5))
            spotify_tracks = [track for track in spotify_tracks if track.confidence >= min_confidence]
        except (SpotifyConfigurationError, SpotifyAPIError) as error:
            spotify_error = str(error)

    profile_cols = st.columns(5)
    profile_cols[0].metric("Genre", user.favorite_genre)
    profile_cols[1].metric("Mood", user.favorite_mood)
    profile_cols[2].metric("Energy", f"{user.target_energy:.2f}")
    profile_cols[3].metric("Acoustic", "Yes" if user.likes_acoustic else "No")
    average_confidence = (
        sum(result.confidence for result in trace.recommendations) / len(trace.recommendations)
        if trace.recommendations
        else 0
    )
    profile_cols[4].metric("Avg confidence", f"{average_confidence:.2f}")

    if trace.warnings:
        for warning in trace.warnings:
            st.warning(warning)

    tabs = st.tabs(["Recommendations", "Spotify", "Reasoning", "Evaluation", "Catalog"])

    with tabs[0]:
        if not visible_recommendations:
            st.info("No recommendations met the current confidence filter.")

        for index, result in enumerate(visible_recommendations, start=1):
            with st.container():
                st.markdown("<div class='recommendation-card'>", unsafe_allow_html=True)
                title_cols = st.columns([3, 1])
                title_cols[0].markdown(f"### {index}. {result.song.title}")
                title_cols[0].markdown(
                    f"<div class='muted'>{result.song.artist} | {result.song.genre} | {result.song.mood}</div>",
                    unsafe_allow_html=True,
                )
                title_cols[1].metric("Confidence", f"{result.confidence:.2f}")
                st.progress(result.confidence)

                detail_cols = st.columns(5)
                detail_cols[0].metric("Score", f"{result.score:.2f}")
                detail_cols[1].metric("Energy", f"{result.song.energy:.2f}")
                detail_cols[2].metric("Tempo", f"{result.song.tempo_bpm:.0f}")
                detail_cols[3].metric("Dance", f"{result.song.danceability:.2f}")
                detail_cols[4].metric("Acoustic", f"{result.song.acousticness:.2f}")

                reason_cols = st.columns([2, 1])
                with reason_cols[0]:
                    st.markdown("<div class='small-label'>Why this match works</div>", unsafe_allow_html=True)
                    for reason in result.reasons[:5]:
                        st.write(f"- {reason}")
                with reason_cols[1]:
                    st.markdown("<div class='small-label'>Guardrails</div>", unsafe_allow_html=True)
                    if result.guardrails:
                        for note in result.guardrails:
                            st.error(note)
                    else:
                        st.success("No guardrail warnings.")
                st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Real Spotify Recommendations")
        st.caption("Results come from Spotify catalog search, then VibeMatch reranks them using the parsed prompt intent.")

        if not use_spotify:
            st.info("Turn on 'Use real Spotify catalog' in the sidebar to fetch live Spotify tracks.")
        elif spotify_error:
            st.error(spotify_error)
            with st.expander("How to configure Spotify"):
                st.write("1. Create an app in the Spotify Developer Dashboard.")
                st.write("2. Copy the app's Client ID and Client Secret.")
                st.write("3. Set them before launching Streamlit:")
                st.code(
                    "export SPOTIFY_CLIENT_ID='your-client-id'\n"
                    "export SPOTIFY_CLIENT_SECRET='your-client-secret'\n"
                    "streamlit run src/main.py",
                    language="bash",
                )
        elif not spotify_tracks:
            st.info("Spotify returned no tracks for this prompt. Try a more specific genre, artist, mood, or activity.")
        else:
            query_cols = st.columns(3)
            for index, spotify_query in enumerate(build_spotify_queries(query, user)[:3]):
                query_cols[index].metric(f"Search {index + 1}", spotify_query)

            for index, track in enumerate(spotify_tracks[:k], start=1):
                with st.container():
                    title_cols = st.columns([1, 3, 1])
                    if track.image_url:
                        title_cols[0].image(track.image_url, width="stretch")
                    title_cols[1].markdown(f"### {index}. {track.title}")
                    title_cols[1].write(f"{track.artist} | {track.album}")
                    if track.url:
                        title_cols[1].link_button("Open in Spotify", track.url)
                    title_cols[2].metric("Confidence", f"{track.confidence:.2f}")
                    title_cols[2].metric("Popularity", track.popularity)
                    st.progress(track.confidence)

                    for reason in track.reasons:
                        st.write(f"- {reason}")
                    if track.preview_url:
                        st.audio(track.preview_url)
                    st.divider()

    with tabs[2]:
        if show_trace:
            step_cols = st.columns(len(trace.plan))
            for index, step in enumerate(trace.plan):
                step_cols[index].metric(f"Step {index + 1}", step)

            retrieved_rows = [
                {
                    "title": item.song.title,
                    "artist": item.song.artist,
                    "genre": item.song.genre,
                    "mood": item.song.mood,
                    "retrieval_score": round(item.retrieval_score, 2),
                    "evidence": "; ".join(item.evidence[:3]),
                }
                for item in trace.retrieved
            ]
            st.dataframe(retrieved_rows, use_container_width=True)
        else:
            st.info("Turn on reasoning trace in the sidebar to inspect retrieval evidence.")

    with tabs[3]:
        summary = evaluate_cases(recommender, EVALUATION_CASES)
        eval_cols = st.columns(3)
        eval_cols[0].metric("Passed", f"{summary['passed']} / {summary['total']}")
        eval_cols[1].metric("Average confidence", f"{summary['average_confidence']:.2f}")
        eval_cols[2].metric("Warnings", sum(len(result["warnings"]) for result in summary["results"]))
        eval_rows = [
            {
                "status": "PASS" if result["passed"] else "FAIL",
                "case": result["name"],
                "top_song": result["top_song"],
                "top_genre": result["top_genre"],
                "avg_confidence": round(result["average_confidence"], 2),
                "warnings": "; ".join(result["warnings"]),
            }
            for result in summary["results"]
        ]
        st.dataframe(eval_rows, use_container_width=True)

    with tabs[4]:
        catalog_rows = [
            {
                "title": song.title,
                "artist": song.artist,
                "genre": song.genre,
                "mood": song.mood,
                "energy": song.energy,
                "tempo": song.tempo_bpm,
                "valence": song.valence,
                "danceability": song.danceability,
                "acousticness": song.acousticness,
            }
            for song in songs
        ]
        catalog_filter_cols = st.columns(2)
        selected_genres = catalog_filter_cols[0].multiselect("Filter genres", genres)
        selected_moods = catalog_filter_cols[1].multiselect("Filter moods", moods)
        if selected_genres:
            catalog_rows = [row for row in catalog_rows if row["genre"] in selected_genres]
        if selected_moods:
            catalog_rows = [row for row in catalog_rows if row["mood"] in selected_moods]
        st.dataframe(catalog_rows, use_container_width=True)


def main() -> None:
    args = build_parser().parse_args()
    recommender = build_recommender()
    
    if args.query:
        user = profile_from_prompt(args.query)
        query = args.query
        print(f"Parsed request: {query}")
        print(
            "Profile: "
            f"genre={user.favorite_genre}, mood={user.favorite_mood}, "
            f"energy={user.target_energy:.2f}, acoustic={user.likes_acoustic}"
        )
    else:
        choice = args.profile
        if choice is None:
            print("Select a user profile:")
            for key, item in PROFILES.items():
                print(f"{key}. {item['name']}")
            choice = input("Enter number (1-6): ").strip()

        if choice not in PROFILES:
            print("Invalid choice, using default High-Energy Pop.")
            choice = "1"
        user = PROFILES[choice]["profile"]
        query = PROFILES[choice]["query"]
        print(f"Selected: {PROFILES[choice]['name']}")

    trace = recommender.recommend_with_context(user, query=query, k=args.k)

    if args.spotify:
        spotify_client = SpotifyClient()
        print("\nSpotify recommendations:\n")
        try:
            spotify_tracks = spotify_client.recommend_from_prompt(query, user, limit=args.k, market=args.market)
            for track in spotify_tracks:
                print(f"Title: {track.title} by {track.artist}")
                print(f"Album: {track.album}")
                print(f"Popularity: {track.popularity} | Confidence: {track.confidence:.2f}")
                print(f"Spotify: {track.url}")
                print("Reasons:")
                for reason in track.reasons:
                    print(f"  - {reason}")
                print()
        except (SpotifyConfigurationError, SpotifyAPIError) as error:
            print(f"Spotify unavailable: {error}")

    if args.show_trace:
        print("\nAgent plan:")
        for step in trace.plan:
            print(f"- {step}")
        print("\nRetrieved evidence:")
        for item in trace.retrieved[: min(5, len(trace.retrieved))]:
            print(f"- {item.song.title}: {item.retrieval_score:.2f} ({'; '.join(item.evidence[:3])})")

    if trace.warnings:
        print("\nGuardrail warnings:")
        for warning in trace.warnings:
            print(f"- {warning}")

    print("\nTop recommendations:\n")
    for result in trace.recommendations:
        print(f"Title: {result.song.title} by {result.song.artist}")
        print(f"Score: {result.score:.2f} | Confidence: {result.confidence:.2f}")
        print("Reasons:")
        for reason in result.reasons[:5]:
            print(f"  - {reason}")
        if result.guardrails:
            print("Guardrails:")
            for note in result.guardrails:
                print(f"  - {note}")
        print()


if __name__ == "__main__":
    if is_streamlit_runtime():
        render_streamlit_app()
    else:
        main()
