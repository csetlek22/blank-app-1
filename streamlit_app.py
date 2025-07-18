import streamlit as st
from datetime import datetime
import json
from groq import Groq
import os

# --- CONFIGURATION ---

MODEL_NAME = "llama3-70b-8192"

# --- INIT GROQ CLIENT ---
# Fallback for local dev if secrets is missing
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    with open("apikey.txt") as f:
        api_key = f.read().strip()

client = Groq(api_key=api_key)


# --- INIT SESSION STATE ---
if "liked_gifts" not in st.session_state:
    st.session_state.liked_gifts = []

# --- STREAMLIT FORM ---
st.title("🎁 Gift Recommendation Engine")
st.markdown("Answer a few fun questions and get **personalized** gift ideas!")

with st.form("gift_form"):
    email = st.text_input("Your Email")
    recipient = st.selectbox("Gift is for", ["Myself", "Friend", "Partner", "Sibling", "Parent", "Child", "Colleague", "Other"])

    personality_traits = [
        "Funny", "Curious", "Introverted", "Creative", "Adventurous",
        "Kind", "Calm", "Outgoing", "Empathetic", "Ambitious",
        "Thoughtful", "Logical", "Emotional", "Playful", "Determined",
        "Optimistic", "Mindful", "Artistic", "Practical", "Romantic"
    ]

    personality = st.multiselect("What personality traits describe this person?", personality_traits)

    interest_options = [
        # Tech & Digital
        "Tech", "Gadgets", "AI & Robotics", "Smart Home", "Programming", "Crypto", "Gaming", "Virtual Reality",

        # Arts & Creativity
        "Art", "Painting", "Drawing", "Photography", "Crafts", "Design", "Creative Writing",

        # Music & Media
        "Music", "Instruments", "Singing", "Podcasts", "Movies", "TV Shows", "Theater", "Anime",

        # Books & Learning
        "Books", "Fiction", "Non-fiction", "Philosophy", "Science", "History", "Languages",

        # Active Lifestyle
        "Fitness", "Running", "Yoga", "Hiking", "Biking", "Sports", "Climbing",

        # Food & Lifestyle
        "Cooking", "Baking", "Tea & Coffee", "Mixology", "Fashion", "Skincare", "Gardening", "Travel"
    ]

    interests = st.multiselect("What are this person’s interests?", interest_options)
    occasion_options = [
        "Birthday",
        "Graduation",
        "Anniversary",
        "Valentine's Day",
        "Christmas",
        "New Year's",
        "Mother's Day",
        "Father's Day",
        "Wedding",
        "Housewarming",
        "Promotion",
        "Farewell"
    ]

    occasion = st.multiselect("Occasion(s)", occasion_options)
    custom_occasion = st.text_input("Other occasion (optional)")
    if custom_occasion:
        occasion.append(custom_occasion)

    budget = st.slider("Budget (€)", 5, 150, 5)
    story = st.text_area("Tell us a short story about them (optional but recommended)")
    submitted = st.form_submit_button("🎯 Get Gift Suggestions")

gift_choices = []

# --- HANDLE AI SUGGESTIONS ---
if submitted:
    st.subheader("🎁 Suggested Gifts")

    prompt = f"""
You are a creative gift recommendation specialist with a keen eye for unique and thoughtful presents. You have a deep understanding of individual preferences and interests, allowing you to curate personalized gift ideas that stand out.

Your task is to suggest 15 unique and thoughtful gift ideas for the following person:  


Recipient: {recipient}
Personality: {', '.join(personality)}
Interests: {', '.join(interests)}
Occasion: {occasion}
Budget: {budget} Euros
Story: {story if story else "N/A"}

---

The gift suggestions should be formatted as a numbered list, with each entry containing a brief description of the gift and why it would be suitable for the individual mentioned above. Aim for creativity and originality in your recommendations. 

---

Please ensure that the suggestions are diverse and cater to different price ranges, keeping in mind the recipient's interests and the occasion. Avoid common or generic gifts that lack personal touch.

---

Example:  
1. Custom Star Map - A beautifully framed map showcasing the stars on a specific date significant to the recipient.  
2. Subscription Box for Art Supplies - A monthly delivery of curated art materials for the aspiring artist.  
3. Personalized Recipe Book - A collection of family recipes curated and printed in a custom book format.

--- 

Be cautious of overly commercialized items and trends that may not resonate with the recipient's personality. Focus on unique finds that reflect thoughtfulness and care in the selection process.


Format each suggestion as:
1. Gift Name - Short explanation why it's a good fit
Only return the list.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    suggestion = response.choices[0].message.content
    st.text_area("💡 AI Suggestions", suggestion, height=250)

    # --- Parse Suggestions & Add Checkboxes ---
    suggestion_lines = [line.strip() for line in suggestion.split("\n") if line.strip()]
    gift_choices = [line for line in suggestion_lines if line[0].isdigit()]

    st.session_state.generated_gifts = gift_choices  # Store for use outside if submitted

# --- Show checkboxes for liked gifts ---
if "generated_gifts" in st.session_state:
    st.subheader("👍 Select the gifts you like:")
    for i, gift in enumerate(st.session_state.generated_gifts):
        checked = st.checkbox(gift, key=f"gift_{i}")
        if checked and gift not in st.session_state.liked_gifts:
            st.session_state.liked_gifts.append(gift)
        elif not checked and gift in st.session_state.liked_gifts:
            st.session_state.liked_gifts.remove(gift)

# --- Final Submission ---
st.subheader("📩 Final Step")

if st.button("✅ Save My Gift Preferences"):
    if not email or not recipient:
        st.error("Please fill in your email and recipient's name.")
    elif not st.session_state.liked_gifts:
        st.warning("Please select at least one gift from the list.")
    else:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "recipient": recipient,
            "personality": personality,
            "interests": interests,
            "occasion": occasion,
            "budget": budget,
            "story": story,
            "liked_gifts": st.session_state.liked_gifts
        }

        with open("user_choices.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        st.success("Your answers and favorite gifts were saved successfully!")
        st.session_state.liked_gifts = []
 
