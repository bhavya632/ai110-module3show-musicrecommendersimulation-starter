# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch Recommender**  

---

## 2. Intended Use  

This recommender suggests songs based on user preferences. It is for classroom exploration, not real users. It assumes users pick a favorite genre, mood, and energy level.  

---

## 3. How the Model Works  

The model looks at song features like genre, mood, and energy. It gives 2 points for matching genre, 1 point for matching mood, and a score from 0 to 1 for energy closeness. It adds these up for each song and picks the top ones. I changed the starter code to use these simple scores instead of nothing.  

---

## 4. Data  

The dataset has 19 songs. It includes genres like pop, lofi, rock, and electronic. Moods are happy, chill, intense, and moody. I added a few new songs to make it more diverse. Some musical tastes, like rare genres, are missing.  

---

## 5. Strengths  

It works well for users who like chill lofi or intense rock. The scoring captures genre matches correctly. Recommendations often match my intuition for clear preferences.  

---

## 6. Limitations and Bias 

It ignores features like tempo and danceability fully. Genres like jazz are underrepresented. It overfits to genre, so mood mismatches happen. It might favor users with common tastes over unique ones.  

---

## 7. Evaluation  

I tested with profiles like high-energy pop and chill lofi. I checked if top songs matched the preferences. Surprised that energy scores were low for mismatches. I ran simple tests by changing profiles and seeing results.  

---

## 8. Future Work  

Add tempo and danceability to scoring. Make explanations clearer. Ensure top results are diverse. Handle mixed or changing user tastes.  

---

## 9. Personal Reflection  

I learned that recommender systems use simple math to match user likes with item features. It was unexpected how much genre dominates recommendations, even with mood and energy. This makes me think music apps like Spotify must balance many factors to avoid boring suggestions.  
