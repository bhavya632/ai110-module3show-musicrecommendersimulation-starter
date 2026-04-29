# Model Card: VibeMatch Applied AI Recommender

## Model Name

VibeMatch Applied AI Music Recommender

## Intended Use

VibeMatch recommends songs from a small classroom catalog based on explicit listener preferences. It is intended for education, portfolio demonstration, and responsible AI system design practice. It should not be treated as a production music platform or as a tool for inferring sensitive facts about a user.

## Base Project

The base project was the Module 3 Music Recommender Simulation. It ranked songs using genre, mood, and energy similarity. This final version keeps that core idea but adds retrieval, an agent trace, confidence scores, guardrail warnings, logging, tests, and evaluation.

## How The System Works

The system can start from a saved profile or from a natural-language request. A transparent parser converts the request into a `UserProfile` with favorite genre, favorite mood, target energy, and acoustic preference. A retriever then searches the catalog for candidate songs using exact matches, adjacent genres and moods, energy fit, and query terms.

The ranking agent scores each retrieved song and returns recommendations with explanations. It also checks for low confidence, energy mismatch, acoustic mismatch, and catalog coverage issues. The result is an observable workflow rather than a one-step black-box answer.

An optional Spotify integration can search the live Spotify catalog from the same natural-language prompt. It uses app-level Client Credentials authentication and public catalog search results, not a user's private listening history or library.

## Data

The dataset is `data/songs.csv`, a small synthetic catalog of 20 songs. It includes metadata such as title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness. Because the catalog is small and hand-labeled, it contains subjective labels and uneven genre coverage.

## Reliability And Testing

Reliability is measured in three ways:

- Unit tests in `tests/test_recommender.py`.
- A predefined evaluation harness in `src/evaluate.py`.
- Runtime warnings and logs written through the `vibematch` logger.

Current evaluation result: 5 out of 5 predefined cases pass, with average confidence around 0.80. The most fragile case is an unknown genre request, where the system warns that the genre is missing and relies on mood/acoustic evidence instead.

## Limitations And Biases

The system can favor genres that appear more often in the catalog. Genre and mood labels are subjective and may not match every listener's interpretation. The parser uses simple keyword rules, so it can miss sarcasm, mixed preferences, or unusual wording. Confidence is a rule-based fit score, not a calibrated probability.

The recommender may also create a filter bubble if exact genre matching dominates. To reduce this, the final workflow allows adjacent genres and diversifies the ranked list when possible.

## Misuse Risks And Mitigations

VibeMatch should not be used to infer private traits, emotional state, identity, or mental health. It only uses explicit user requests and song metadata. The system explains recommendations in terms of music features, not personal judgments about the user.

The guardrails reduce misuse by warning when confidence is low or when a recommendation may not match the user's stated energy or acoustic preference.

## What Surprised Me During Testing

The biggest surprise was that exact-match tests were too strict for a recommender. A nearby genre such as indie pop for pop, or metal for intense rock, can be a reasonable recommendation even when it is not an exact match. I changed evaluation cases to allow acceptable genre and mood families, which better reflects real recommendation quality.

## AI Collaboration Reflection

AI helped by suggesting that the recommender should expose intermediate reasoning steps instead of only printing final songs. That became the `AgentTrace` design with plan, retrieved evidence, recommendations, and warnings.

One flawed AI suggestion was to describe confidence as if it were a true probability of user satisfaction. That was incorrect because the system is rule-based and not calibrated on real user feedback. I corrected the documentation to call confidence a fit score and made the limitations explicit.

## Future Improvements

Future versions could use a larger catalog, real embeddings for semantic retrieval, user feedback loops, calibrated confidence scores, and human evaluation from multiple listeners. Another improvement would be comparing baseline recommendations against retrieval-augmented recommendations to measure quality gains more formally.

The Spotify integration could be improved with user-authorized personalization, but that would require stronger consent, privacy, and data-handling controls than this classroom demo needs.
