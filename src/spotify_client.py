"""Spotify catalog integration for VibeMatch.

This module uses Spotify's Client Credentials flow, which is appropriate for
searching public catalog metadata without reading or changing a user's account.
"""

from dataclasses import dataclass
import base64
import json
import os
from pathlib import Path
import ssl
import time
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from .recommender import UserProfile
except ImportError:
    from recommender import UserProfile


TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


@dataclass
class SpotifyTrack:
    title: str
    artist: str
    album: str
    url: str
    preview_url: Optional[str]
    image_url: Optional[str]
    popularity: int
    spotify_id: str
    matched_query: str
    confidence: float
    reasons: List[str]


class SpotifyConfigurationError(Exception):
    """Raised when Spotify credentials are missing."""


class SpotifyAPIError(Exception):
    """Raised when Spotify returns an API or network error."""


class SpotifyClient:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        load_env_file()
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self._access_token: Optional[str] = None
        self._token_expires_at = 0.0

    @property
    def is_configured(self) -> bool:
        return bool(
            self.client_id
            and self.client_secret
            and "your-client-id" not in self.client_id
            and "your-client-secret" not in self.client_secret
        )

    def get_access_token(self) -> str:
        if not self.is_configured:
            raise SpotifyConfigurationError(
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to enable Spotify recommendations."
            )

        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        body = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        headers = {
            "Authorization": "Basic " + base64.b64encode(credentials).decode("utf-8"),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = self._request_json(TOKEN_URL, method="POST", data=body, headers=headers)
        self._access_token = payload["access_token"]
        self._token_expires_at = time.time() + int(payload.get("expires_in", 3600))
        return self._access_token

    def search_tracks(self, query: str, limit: int = 10, market: str = "US") -> List[Dict]:
        token = self.get_access_token()
        params = urlencode(
            {
                "q": query,
                "type": "track",
                "limit": max(1, min(limit, 50)),
                "market": market,
            }
        )
        url = f"{SEARCH_URL}?{params}"
        payload = self._request_json(url, headers={"Authorization": f"Bearer {token}"})
        return payload.get("tracks", {}).get("items", [])

    def recommend_from_prompt(
        self,
        prompt: str,
        profile: UserProfile,
        limit: int = 8,
        market: str = "US",
    ) -> List[SpotifyTrack]:
        queries = build_spotify_queries(prompt, profile)
        found: Dict[str, SpotifyTrack] = {}

        for query in queries:
            for item in self.search_tracks(query, limit=limit, market=market):
                spotify_id = item.get("id")
                if not spotify_id or spotify_id in found:
                    continue
                track = spotify_track_from_item(item, query, prompt, profile)
                found[spotify_id] = track

        ranked = sorted(found.values(), key=lambda track: (track.confidence, track.popularity), reverse=True)
        return ranked[:limit]

    def _request_json(
        self,
        url: str,
        method: str = "GET",
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict:
        request = Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urlopen(request, timeout=12, context=get_ssl_context()) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise SpotifyAPIError(f"Spotify API error {error.code}: {details}") from error
        except URLError as error:
            raise SpotifyAPIError(f"Could not reach Spotify: {error.reason}") from error


def build_spotify_queries(prompt: str, profile: UserProfile) -> List[str]:
    clean_prompt = " ".join(prompt.strip().split())
    mood_terms = {
        "happy": "upbeat",
        "excited": "party",
        "intense": "workout",
        "angry": "heavy",
        "chill": "chill",
        "relaxed": "relaxing",
        "focused": "focus",
        "moody": "moody",
        "sad": "sad",
        "nostalgic": "nostalgic",
        "calm": "calm",
    }
    energy_term = "high energy" if profile.target_energy >= 0.75 else "low energy" if profile.target_energy <= 0.4 else "mid tempo"
    acoustic_term = "acoustic" if profile.likes_acoustic else ""
    mood_term = mood_terms.get(profile.favorite_mood, profile.favorite_mood)

    queries = [
        clean_prompt,
        " ".join(part for part in [profile.favorite_genre, mood_term, acoustic_term] if part),
        " ".join(part for part in [profile.favorite_genre, energy_term] if part),
    ]
    unique_queries = []
    for query in queries:
        if query and query not in unique_queries:
            unique_queries.append(query)
    return unique_queries


def load_env_file(path: Path = ENV_PATH) -> None:
    """Load simple KEY=VALUE pairs from .env without overriding real env vars."""
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_ssl_context() -> ssl.SSLContext:
    """Use certifi's CA bundle when available to avoid local macOS cert issues."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def spotify_track_from_item(item: Dict, query: str, prompt: str, profile: UserProfile) -> SpotifyTrack:
    artists = ", ".join(artist.get("name", "Unknown Artist") for artist in item.get("artists", []))
    album = item.get("album", {})
    images = album.get("images", [])
    image_url = images[0]["url"] if images else None
    external_urls = item.get("external_urls", {})
    popularity = int(item.get("popularity") or 0)

    reasons = [f"matched Spotify search query: {query}"]
    lowered = f"{item.get('name', '')} {artists} {album.get('name', '')}".lower()
    prompt_terms = {term for term in prompt.lower().replace(",", " ").split() if len(term) > 3}
    overlap = sorted(term for term in prompt_terms if term in lowered)
    if overlap:
        reasons.append("title/artist/album overlaps prompt terms: " + ", ".join(overlap[:4]))
    if profile.favorite_genre in query:
        reasons.append(f"query includes target genre: {profile.favorite_genre}")
    if profile.favorite_mood in query or profile.favorite_mood in prompt.lower():
        reasons.append(f"query reflects target mood: {profile.favorite_mood}")
    if profile.likes_acoustic:
        reasons.append("prompt/profile asked for acoustic-friendly results")

    confidence = min(1.0, 0.45 + (popularity / 200) + (0.08 * min(len(reasons), 4)))
    return SpotifyTrack(
        title=item.get("name", "Unknown Track"),
        artist=artists or "Unknown Artist",
        album=album.get("name", "Unknown Album"),
        url=external_urls.get("spotify", ""),
        preview_url=item.get("preview_url"),
        image_url=image_url,
        popularity=popularity,
        spotify_id=item.get("id", ""),
        matched_query=query,
        confidence=confidence,
        reasons=reasons,
    )
