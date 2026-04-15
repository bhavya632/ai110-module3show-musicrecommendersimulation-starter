# 🎵 Music Recommender Simulation

## Project Summary

Music recommendation systems, like those used by Spotify and YouTube, analyze user behavior and song attributes to suggest tracks users might enjoy, often combining collaborative filtering (based on similar users) with content-based methods. This music recommender uses content-based filtering, which recommends songs by comparing their features to a user's preferences, without relying on other users' data. Songs are scored based on genre (2 points for exact match), mood (1 point for match), and energy similarity (0-1 score based on closeness to the user's target). For each song, the total score combines these elements, rewarding closer matches. Songs are then ranked by score in descending order, with the top recommendations presented first. This approach ensures personalized suggestions tailored to individual tastes. However, it may have bias toward genre matches, potentially overlooking great songs in similar but unmatched genres. Future versions could adjust weights or add more features for balance.
---

## How The System Works

### Features for Song and UserProfile Objects

#### 1. Song Object Features
The Song object represents individual tracks with attributes extracted from the dataset. Each feature is stored as a simple data type for easy comparison.

- **genre** (string): The musical style category, e.g., "pop", "rock", or "lofi". Used to match broad preferences.
- **mood** (string): The emotional tone, e.g., "happy", "chill", or "intense". Helps capture the song's vibe.
- **energy** (float, 0-1): A measure of intensity and loudness, where 1 is high energy (e.g., for upbeat tracks).
- **tempo_bpm** (integer): The speed in beats per minute, e.g., 120 for moderate pace. Affects rhythm.
- **valence** (float, 0-1): A measure of positivity, where 1 is very happy/sad (optional for mood refinement).

#### 2. UserProfile Features
The UserProfile object stores a user's preferences, initialized from input or defaults. It mirrors Song features for direct comparison.

- **preferred_genre** (string or list of strings): The user's favorite genre(s), e.g., "pop". Used for exact or partial matches.
- **preferred_mood** (string or list of strings): The user's desired mood(s), e.g., "chill". Matches emotional tone.
- **preferred_energy** (float, 0-1): The user's ideal energy level, e.g., 0.8 for high intensity.
- **preferred_tempo_bpm** (integer): The user's preferred tempo, e.g., 100 for moderate speed.
- **preferred_valence** (float, 0-1): The user's desired positivity level, e.g., 0.7 for upbeat (optional).

These features keep the system beginner-friendly: use dictionaries or classes in Python, with simple scoring (e.g., 1 if genre matches, 1 - |diff| for numerical). Load from CSV for Songs, prompt user for UserProfile.

### Designing a Scoring Function for Numerical Features

For content-based recommenders, a scoring function for numerical features (e.g., energy on a 0-1 scale) should output higher values for songs closer to the user's preferred value and lower values for those farther away. This creates a similarity score where 1 is perfect match and 0 is maximum difference.

#### 1. Simple Mathematical Formula
Assuming features are normalized to [0, 1] (common for energy, valence, etc.), use:

**score = 1 - |feature_value - user_preference|**

- `feature_value`: The song's value (e.g., 0.8 for energy).
- `user_preference`: The user's preferred value (e.g., 0.7 for energy).
- `| |`: Absolute value to handle both directions.

For features not in [0, 1] (e.g., tempo_bpm), first normalize: `normalized_feature = (feature - min_value) / (max_value - min_value)`.

#### 2. Explanation of How It Works
- The absolute difference `|feature_value - user_preference|` measures dissimilarity (0 = identical, 1 = opposite).
- Subtracting from 1 inverts it: closer values yield higher scores (rewarding similarity), farther values yield lower scores (penalizing difference).
- Result is always between 0 and 1, making it easy to combine with other features (e.g., average scores across multiple attributes).
- This is a linear penalty—simple and intuitive, but you could use exponential decay (e.g., `exp(-|diff| * weight)`) for sharper rewards/penalties.

#### 3. Small Example Calculation
User prefers energy = 0.7.  
- Song A: energy = 0.8 → |0.8 - 0.7| = 0.1 → score = 1 - 0.1 = **0.9** (high reward, very similar).  
- Song B: energy = 0.5 → |0.5 - 0.7| = 0.2 → score = 1 - 0.2 = **0.8** (moderate reward).  
- Song C: energy = 0.2 → |0.2 - 0.7| = 0.5 → score = 1 - 0.5 = **0.5** (moderate penalty).  
- Song D: energy = 0.0 → |0.0 - 0.7| = 0.7 → score = 1 - 0.7 = **0.3** (strong penalty, very different).  

In a recommender, sort songs by total score (sum across features) to prioritize the best matches.

### Potential Biases

1. **Genre Lock-In**: Heavy prioritization of genre can trap users in a single style (e.g., always recommending pop), reducing exposure to similar but unmatched genres like indie or alternative, limiting musical discovery.
2. **Mood Overshadowing**: With mood as secondary, subtle emotional differences (e.g., "relaxed" vs. "chill") may be ignored, leading to recommendations that don't align with the user's current emotional state.
3. **Energy Insensitivity**: Low weighting on energy means small intensity differences (e.g., 0.8 vs. 0.9) have minimal impact, potentially recommending overly energetic songs for calm users or vice versa.
4. **Dataset Imbalance**: If the CSV has more songs in certain genres (e.g., pop dominates), the system biases toward those, even if user preferences lean elsewhere, reflecting data collection flaws rather than true taste.
---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

**Experiment Summary:**
I tested how different weight configurations affected recommendation quality across user profiles. When I reduced the genre weight from 2.0 to 0.5, the system began recommending songs from adjacent genres (e.g., indie for pop-lovers), which improved discovery but sometimes felt less cohesive. Adding valence (0.5 weight) to the scoring function made a noticeable difference for users with strong emotional preferences—happy-seeking users got more upbeat recommendations. Testing with three different user archetypes (the "chill listener" preferring low energy, the "workout enthusiast" wanting high energy, and the "genre chameleon" with mixed preferences) revealed a clear bias: the system excelled for users who matched the dataset's dominant pop/lofi blend but struggled to serve the workout user well due to limited high-energy rock tracks. This confirmed the README's concern about genre lock-in and dataset imbalance.

---

## Limitations and Risks

**Key Limitations:**
This recommender operates on a tiny catalog (~20 songs), making it prone to repetitive recommendations and unable to serve users with niche preferences. The system only considers structured metadata (genre, mood, energy, tempo, valence) and cannot understand song lyrics, cultural context, or subtle nuances in musical taste—a song's themes or storytelling are completely invisible to the algorithm. It significantly over-favors genre matches due to the 2-point weight, which can trap users in filter bubbles and suppress discovery of cross-genre gems. The energy and valence features, while helpful, rely on simplistic numerical comparisons that don't capture subjective listener preferences (some users enjoy variability, others consistency). Finally, any dataset imbalances in the CSV directly translate to systematic bias: if pop songs outnumber rock songs 3-to-1, the system will inherently recommend more pop even if the user's preferences are perfectly balanced. These limitations are intentional trade-offs for a classroom simulation but would require significant enhancement for real-world deployment.

---

