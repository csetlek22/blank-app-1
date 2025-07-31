import streamlit as st
from datetime import datetime
from groq import Groq
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
MODEL_NAME = "llama3-70b-8192"

# --- INIT GROQ CLIENT ---
api_key = st.secrets["API_KEY"]
client = Groq(api_key=api_key)

# --- LANGUAGE SETUP ---
LANG_OPTIONS = {"English": "en", "Türkçe": "tr"}
lang = st.selectbox("Language / Dil", list(LANG_OPTIONS.keys()), index=0)
L = LANG_OPTIONS[lang]

# Localization dictionaries
TEXT = {
    "title": {"en": "🎁 Gift Recommendation Engine", "tr": "🎁 Hediye Öneri Motoru"},
    "subtitle": {"en": "Answer a few fun questions and get personalized gift ideas!", "tr": "Birkaç eğlenceli soruyu cevaplayın ve kişiselleştirilmiş hediye fikirleri alın!"},
    "email": {"en": "Your Email", "tr": "E-posta Adresiniz"},
    "recipient": {"en": "Gift is for", "tr": "Hediye kime"},
    "personality_prompt": {"en": "What personality traits describe this person?", "tr": "Bu kişiyi hangi kişilik özellikleri tanımlar?"},
    "interests_prompt": {"en": "What are this person’s interests?", "tr": "Bu kişinin ilgi alanları nelerdir?"},
    "occasion_prompt": {"en": "Occasion(s)", "tr": "Fırsat(lar)"},
    "custom_occasion": {"en": "Other occasion (optional)", "tr": "Diğer etkinlik (opsiyonel)"},
    "budget": {"en": "Budget (€)", "tr": "Bütçe (€)"},
    "story": {"en": "Tell us a short story about them (optional but recommended)", "tr": "Hakkında kısa bir hikaye anlatın (isteğe bağlı ama önerilir)"},
    "submit": {"en": "🎯 Get Gift Suggestions", "tr": "🎯 Hediye Önerisi Al"},
    "suggested": {"en": "🎁 Suggested Gifts", "tr": "🎁 Önerilen Hediyeler"},
    "select_liked": {"en": "👍 Select the gifts you like:", "tr": "👍 Beğendiğiniz hediyeleri seçin:"},
    "final_step": {"en": "📩 Final Step", "tr": "📩 Son Adım"},
    "save_button": {"en": "✅ Save My Gift Preferences", "tr": "✅ Hediye Tercihlerimi Kaydet"},
    "fill_required": {"en": "Please fill in your email and recipient's name.", "tr": "Lütfen e-posta ve hediye alıcısının adını girin."},
    "select_at_least": {"en": "Please select at least one gift from the list.", "tr": "Lütfen listeden en az bir hediye seçin."},
    "saved_success": {"en": "Your answers and favorite gifts were saved successfully!", "tr": "Cevaplarınız ve favori hediyeleriniz başarıyla kaydedildi!"},
}

# --- INIT SESSION STATE ---
if "liked_gifts" not in st.session_state:
    st.session_state.liked_gifts = []
if "original_suggestion" not in st.session_state:
    st.session_state.original_suggestion = ""
if "translated_suggestion" not in st.session_state:
    st.session_state.translated_suggestion = ""

# --- UI ---
st.title(TEXT["title"][L])
st.markdown(TEXT["subtitle"][L])

with st.form("gift_form"):
    email = st.text_input(TEXT["email"][L])
    recipient = st.selectbox(
        TEXT["recipient"][L],
        {
            "en": ["Myself", "Friend", "Partner", "Sibling", "Parent", "Child", "Colleague", "Other"],
            "tr": ["Kendim", "Arkadaş", "Partner", "Kardeş", "Ebeveyn", "Çocuk", "İş Arkadaşı", "Diğer"]
        }[L]
    )

    personality_traits = {
        "en": [
            "Funny", "Curious", "Introverted", "Creative", "Adventurous",
            "Kind", "Calm", "Outgoing", "Empathetic", "Ambitious",
            "Thoughtful", "Logical", "Emotional", "Playful", "Determined",
            "Optimistic", "Mindful", "Artistic", "Practical", "Romantic"
        ],
        "tr": [
            "Komik", "Meraklı", "İçe dönük", "Yaratıcı", "Macera sever",
            "Nazik", "Sakin", "Dışa dönük", "Empatik", "Hırslı",
            "Düşünceli", "Mantıklı", "Duygusal", "Oyunbaz", "Kararlı",
            "İyimser", "Farkında", "Sanatsal", "Pratik", "Romantik"
        ]
    }[L]

    personality = st.multiselect(TEXT["personality_prompt"][L], personality_traits)

    interest_options = {
        "en": [
            "Tech", "Gadgets", "AI & Robotics", "Smart Home", "Programming", "Crypto", "Gaming", "Virtual Reality",
            "Art", "Painting", "Drawing", "Photography", "Crafts", "Design", "Creative Writing",
            "Music", "Instruments", "Singing", "Podcasts", "Movies", "TV Shows", "Theater", "Anime",
            "Books", "Fiction", "Non-fiction", "Philosophy", "Science", "History", "Languages",
            "Fitness", "Running", "Yoga", "Hiking", "Biking", "Sports", "Climbing",
            "Cooking", "Baking", "Tea & Coffee", "Mixology", "Fashion", "Skincare", "Gardening", "Travel"
        ],
        "tr": [
            "Teknoloji", "Cihazlar", "Yapay Zeka ve Robotik", "Akıllı Ev", "Programlama", "Kripto", "Oyun", "Sanal Gerçeklik",
            "Sanat", "Resim", "Çizim", "Fotoğrafçılık", "El Sanatları", "Tasarım", "Yaratıcı Yazarlık",
            "Müzik", "Enstrümanlar", "Şarkı Söyleme", "Podcast", "Filmler", "TV Şovları", "Tiyatro", "Anime",
            "Kitaplar", "Kurgu", "Kurgu Dışı", "Felsefe", "Bilim", "Tarih", "Diller",
            "Fitness", "Koşu", "Yoga", "Yürüyüş", "Bisiklet", "Spor", "Tırmanış",
            "Yemek Pişirme", "Fırıncılık", "Çay ve Kahve", "Kokteyl", "Moda", "Cilt Bakımı", "Bahçecilik", "Seyahat"
        ]
    }[L]

    interests = st.multiselect(TEXT["interests_prompt"][L], interest_options)

    occasion_options = {
        "en": [
            "Birthday", "Graduation", "Anniversary", "Valentine's Day", "Christmas", "New Year's",
            "Mother's Day", "Father's Day", "Wedding", "Housewarming", "Promotion", "Farewell"
        ],
        "tr": [
            "Doğum Günü", "Mezuniyet", "Yıldönümü", "Sevgililer Günü", "Noel", "Yeni Yıl",
            "Anneler Günü", "Babalar Günü", "Düğün", "Eve Hoşgeldin", "Terfi", "Veda"
        ]
    }[L]

    occasion = st.multiselect(TEXT["occasion_prompt"][L], occasion_options)
    custom = st.text_input(TEXT["custom_occasion"][L])
    if custom:
        occasion.append(custom)

    budget = st.slider(TEXT["budget"][L], 5, 150, 5)
    story = st.text_area(TEXT["story"][L])
    submitted = st.form_submit_button(TEXT["submit"][L])

gift_choices = []

# --- TRANSLATION HELPER ---
def translate_to_turkish(text: str) -> str:
    translation_prompt = f"""
Translate the following gift suggestion list into Turkish. Preserve numbering, formatting, and keep each item concise:
{text}
"""
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": translation_prompt}],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()

# --- HANDLE AI SUGGESTIONS ---
if submitted:
    st.subheader(TEXT["suggested"][L])

    # Build prompt in selected language
    if L == "tr":
        prompt = f"""
Sen, benzersiz ve anlamlı hediyeler seçen yaratıcı bir hediye öneri uzmanısın.
Aşağıdaki kişi için 15 adet özgün ve düşünülmüş hediye önerisi yap.

Alıcı: {recipient}
Kişilik: {', '.join(personality)}
İlgi Alanları: {', '.join(interests)}
Etkinlik: {', '.join(occasion)}
Bütçe: {budget} Euro
Hikaye: {story if story else "Yok"}

Her öneriyi numaralandırılmış liste olarak yaz ve her biri kısa açıklama içersin. Örnek format:
1. Hediye Adı - Neden uygun olduğu açıklaması

Sıradan ve kişisel dokunuşu olmayan hediyelerden kaçın. Farklı fiyat aralıklarında, çeşitli, yaratıcı ve alıcıya özel öneriler ver.
"""
    else:
        prompt = f"""
You are a creative gift recommendation specialist with a keen eye for unique and thoughtful presents. You have a deep understanding of individual preferences and interests, allowing you to curate personalized gift ideas that stand out.

Your task is to suggest 15 unique and thoughtful gift ideas for the following person:  

Recipient: {recipient}
Personality: {', '.join(personality)}
Interests: {', '.join(interests)}
Occasion: {occasion}
Budget: {budget} Euros
Story: {story if story else "N/A"}

The gift suggestions should be formatted as a numbered list, with each entry containing a brief description of the gift and why it would be suitable for the individual mentioned above. Aim for creativity and originality in your recommendations. Avoid generic gifts.
Format each suggestion as:
1. Gift Name - Short explanation why it's a good fit
Only return the list.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    suggestion = response.choices[0].message.content.strip()
    st.session_state.original_suggestion = suggestion

    # Always translate if Turkish selected
    if L == "tr":
        translated = translate_to_turkish(suggestion)
        st.session_state.translated_suggestion = translated
        display_text = translated
        st.text_area("💡 AI Öneriler", translated, height=250)
    else:
        display_text = suggestion
        st.text_area("💡 AI Suggestions", suggestion, height=250)

    # --- Parse Suggestions & Add Checkboxes ---
    suggestion_lines = [line.strip() for line in display_text.split("\n") if line.strip()]
    gift_choices = [line for line in suggestion_lines if line and line[0].isdigit()]
    st.session_state.generated_gifts = gift_choices

# --- Show checkboxes for liked gifts ---
if "generated_gifts" in st.session_state:
    st.subheader(TEXT["select_liked"][L])
    for i, gift in enumerate(st.session_state.generated_gifts):
        checked = st.checkbox(gift, key=f"gift_{i}")
        if checked and gift not in st.session_state.liked_gifts:
            st.session_state.liked_gifts.append(gift)
        elif not checked and gift in st.session_state.liked_gifts:
            st.session_state.liked_gifts.remove(gift)

# --- Final Submission ---
st.subheader(TEXT["final_step"][L])

if st.button(TEXT["save_button"][L]):
    if not email or not recipient:
        st.error(TEXT["fill_required"][L])
    elif not st.session_state.liked_gifts:
        st.warning(TEXT["select_at_least"][L])
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

        # Connect to Google Sheets
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
        client_gs = gspread.authorize(creds)

        # Open or create your sheet
        try:
            sheet = client_gs.open("Gift Preferences").sheet1
        except gspread.SpreadsheetNotFound:
            spreadsheet = client_gs.create("Gift Preferences")
            spreadsheet.share(st.secrets["gspread"]["client_email"], perm_type='user', role='writer')
            sheet = spreadsheet.sheet1

        # Append the data
        sheet.append_row([
            datetime.now().isoformat(),
            email,
            recipient,
            ", ".join(personality),
            ", ".join(interests),
            ", ".join(occasion),
            budget,
            story,
            ", ".join(st.session_state.liked_gifts)
        ])

        st.success(TEXT["saved_success"][L])
        st.session_state.liked_gifts = []
