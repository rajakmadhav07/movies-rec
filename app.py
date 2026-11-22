import os
import pickle
import html
import requests
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CineMatch | Discover Your Next Movie",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = Path(__file__).resolve().parent

# =========================================================
# LOAD MOVIE DATA AND SIMILARITY MODEL
# =========================================================

@st.cache_resource
def load_model():
    movie_file = BASE_DIR / "model" / "movie_list.pkl"
    similarity_file = BASE_DIR / "model" / "similarity.pkl"

    if not movie_file.exists():
        raise FileNotFoundError(f"Missing file: {movie_file}")

    if not similarity_file.exists():
        raise FileNotFoundError(f"Missing file: {similarity_file}")

    with open(movie_file, "rb") as file:
        movie_data = pickle.load(file)

    with open(similarity_file, "rb") as file:
        similarity_data = pickle.load(file)

    return movie_data, similarity_data


try:
    movies, similarity = load_model()
except Exception as error:
    st.error("Unable to load the movie recommendation model.")
    st.code(str(error))
    st.stop()

# =========================================================
# TMDB API CONFIGURATION
# =========================================================

# TMDB API CONFIGURATION

API_KEY = os.getenv("TMDB_API_KEY", "").strip()

if not API_KEY:
    try:
        API_KEY = st.secrets.get("TMDB_API_KEY", "").strip()
    except Exception:
        API_KEY = ""

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap');

:root {
    --gold: #d7ad68;
    --gold-light: #f0cf91;
    --background: #101010;
    --surface: #191919;
    --muted: #a5a5a5;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--background);
    color: #f5f2ed;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] { background: transparent; }

.block-container {
    max-width: 1350px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

#MainMenu, footer { visibility: hidden; }

/* Navbar */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0 23px;
    border-bottom: 1px solid rgba(255,255,255,0.10);
    margin-bottom: 35px;
}
.brand {
    font-size: 23px;
    font-weight: 800;
    letter-spacing: 1px;
}
.brand span { color: var(--gold); }
.nav-label {
    font-size: 11px;
    letter-spacing: 2px;
    color: #aaa;
}

/* Hero */
.hero-content {
    background:
        radial-gradient(ellipse at 90% 10%, rgba(160,112,53,0.20), transparent 40%),
        linear-gradient(115deg, #201d19, #141414 65%);
    border: 1px solid rgba(215,173,104,0.25);
    border-radius: 20px;
    padding: 45px 45px 35px;
    animation: fadeUp 0.8s ease both;
}
.hero-label {
    color: var(--gold);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 4px;
}
.hero-heading {
    font-family: 'Playfair Display', serif;
    font-size: clamp(36px, 5vw, 62px);
    font-weight: 600;
    line-height: 1.15;
    color: #f8f4ed;
    margin-top: 18px;
    margin-bottom: 12px;
}
.hero-highlight { color: var(--gold); font-style: italic; }
.hero-description {
    color: #aaa49c;
    font-size: 15px;
    line-height: 1.8;
    max-width: 620px;
}
.hero-divider {
    width: 55px;
    height: 3px;
    background: var(--gold);
    margin-top: 25px;
    border-radius: 5px;
}

/* Section headings */
.section-heading {
    font-family: 'Playfair Display', serif;
    color: #f4efe7;
    font-size: 30px;
    font-weight: 600;
    margin-top: 15px;
}
.section-description {
    color: #96918a;
    font-size: 13px;
    margin-bottom: 15px;
}

/* Selectbox */
.stSelectbox label {
    color: #d8cfc1 !important;
    font-weight: 600 !important;
}
div[data-baseweb="select"] > div {
    background: #242424;
    border: 1px solid #444 !important;
    border-radius: 10px;
    min-height: 48px;
}
div[data-baseweb="select"] * { color: white !important; }

/* Buttons */
.stButton > button {
    background: var(--gold);
    color: #17130d;
    border: none;
    border-radius: 10px;
    min-height: 48px;
    font-weight: 800;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
}
.stButton > button:hover {
    background: var(--gold-light);
    color: #111;
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(215,173,104,0.20);
}
.stButton > button:active { transform: scale(0.98); }

/* =========================================================
   PREMIUM MOVIE POSTER CARDS
   ========================================================= */

.movie-card {
    position: relative;
    overflow: hidden;
    width: 100%;
    border-radius: 16px;
    background: linear-gradient(155deg, #28231d, #151515 68%);
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 10px 28px rgba(0,0,0,0.28);
    transition:
        transform 350ms cubic-bezier(.2,.8,.2,1),
        border-color 350ms ease,
        box-shadow 350ms ease;
    animation: cardReveal 650ms ease both;
}
.movie-card:hover {
    transform: translateY(-8px);
    border-color: rgba(215,173,104,0.78);
    box-shadow: 0 18px 38px rgba(0,0,0,0.48), 0 0 0 1px rgba(215,173,104,0.10);
}
.poster-frame {
    position: relative;
    width: 100%;
    aspect-ratio: 2 / 3;
    overflow: hidden;
    background:
        radial-gradient(circle at 50% 28%, rgba(215,173,104,0.20), transparent 34%),
        linear-gradient(145deg, #393127, #1b1916 55%, #111);
}
.poster-image {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform 650ms cubic-bezier(.2,.8,.2,1), filter 450ms ease;
}
.movie-card:hover .poster-image {
    transform: scale(1.065);
    filter: saturate(1.08);
}
.poster-shade {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        180deg,
        rgba(0,0,0,0.10) 0%,
        transparent 35%,
        rgba(0,0,0,0.12) 54%,
        rgba(0,0,0,0.88) 100%
    );
    pointer-events: none;
}
.poster-topline {
    position: absolute;
    top: 11px;
    left: 11px;
    right: 11px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;
}
.poster-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 31px;
    height: 27px;
    padding: 0 9px;
    border-radius: 30px;
    color: #17130d;
    background: rgba(240,207,145,0.96);
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.22);
}
.poster-tag {
    color: #f4e7d0;
    background: rgba(12,12,12,0.58);
    border: 1px solid rgba(255,255,255,0.18);
    backdrop-filter: blur(8px);
    border-radius: 30px;
    padding: 6px 9px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
}
.poster-caption {
    position: absolute;
    z-index: 2;
    left: 14px;
    right: 14px;
    bottom: 15px;
}
.poster-kicker {
    color: var(--gold-light);
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 6px;
}
.poster-title {
    color: #fffaf2;
    font-size: 15px;
    font-weight: 800;
    line-height: 1.35;
    text-shadow: 0 2px 12px rgba(0,0,0,0.55);
    overflow-wrap: anywhere;
}
.poster-rule {
    width: 30px;
    height: 2px;
    margin-top: 10px;
    border-radius: 5px;
    background: var(--gold);
    transition: width 300ms ease;
}
.movie-card:hover .poster-rule { width: 58px; }

/* Empty / missing poster state */
.poster-placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 18px;
    text-align: center;
    background:
        radial-gradient(ellipse at 50% 35%, rgba(215,173,104,0.20), transparent 45%),
        linear-gradient(145deg, #393127, #1b1916 58%, #101010);
}
.placeholder-icon {
    width: 66px;
    height: 66px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    border: 1px solid rgba(240,207,145,0.48);
    background: rgba(215,173,104,0.08);
    color: var(--gold-light);
    font-size: 30px;
    margin-bottom: 17px;
    box-shadow: 0 0 35px rgba(215,173,104,0.10);
}
.placeholder-label {
    color: var(--gold-light);
    font-size: 9px;
    letter-spacing: 2px;
    font-weight: 800;
    margin-bottom: 8px;
}
.placeholder-title {
    color: #f7f0e6;
    font-size: 14px;
    font-weight: 700;
    line-height: 1.4;
    overflow-wrap: anywhere;
}
.placeholder-note {
    color: #a9a095;
    font-size: 10px;
    margin-top: 9px;
}
.card-foot {
    padding: 13px 13px 14px;
    min-height: 69px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    background: linear-gradient(180deg, #1c1b19, #171717);
}
.card-foot-label {
    color: #9b8c76;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.8px;
}
.card-foot-title {
    color: #f2eee7;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.35;
    overflow-wrap: anywhere;
}

/* Messages and footer */
div[data-testid="stAlert"] { border-radius: 10px; }
.footer-text {
    text-align: center;
    color: #777;
    font-size: 11px;
    letter-spacing: 2px;
    padding-top: 25px;
    border-top: 1px solid #292929;
    margin-top: 55px;
}

/* Animations */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(22px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes cardReveal {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Responsive */
@media (max-width: 768px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .hero-content { padding: 30px 23px; }
    .hero-heading { font-size: 37px; }
    .nav-label { font-size: 9px; letter-spacing: 1px; }
    .brand { font-size: 19px; }
    .section-heading { font-size: 25px; }
    .poster-title { font-size: 13px; }
}
@media (max-width: 480px) {
    .hero-heading { font-size: 32px; }
    .hero-label { font-size: 9px; letter-spacing: 2px; }
    .hero-description { font-size: 13px; }
    .nav-label { display: none; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# TMDB POSTER FUNCTION
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_poster(movie_id, api_key):
    if not api_key:
        return None

    try:
        url = f"https://api.themoviedb.org/3/movie/{int(movie_id)}"
        response = requests.get(
            url,
            params={"api_key": api_key, "language": "en-US"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")

        if poster_path:
            return "https://image.tmdb.org/t/p/w500" + poster_path

    except (requests.RequestException, ValueError, TypeError):
        return None

    return None

# =========================================================
# RECOMMENDATION FUNCTION
# =========================================================

def recommend(movie_title):
    matching_movies = movies.index[
        movies["title"] == movie_title
    ].tolist()

    if not matching_movies:
        return []

    movie_index = matching_movies[0]

    distances = sorted(
        enumerate(similarity[movie_index]),
        key=lambda item: item[1],
        reverse=True
    )

    recommendations = []

    for item in distances[1:6]:
        movie_data = movies.iloc[item[0]]
        movie_id = movie_data["movie_id"]
        movie_name = movie_data["title"]
        poster = fetch_poster(movie_id, API_KEY)

        recommendations.append({
            "title": str(movie_name),
            "poster": poster
        })

    return recommendations

# =========================================================
# MOVIE CARD HTML
# =========================================================

def render_movie_card(movie, index):
    """
    Render each poster in an isolated HTML component.
    This avoids Streamlit Markdown displaying HTML tags as literal text.
    """
    title = html.escape(str(movie.get("title") or "Untitled movie"))
    poster = movie.get("poster")
    safe_poster = html.escape(str(poster), quote=True) if poster else ""

    if safe_poster:
        visual = f"""
            <img class="poster-image"
                 src="{safe_poster}"
                 alt="Poster for {title}">
            <div class="shade"></div>
            <div class="topline">
                <span class="number">0{index + 1}</span>
                <span class="tag">CINEMATCH PICK</span>
            </div>
            <div class="caption">
                <div class="kicker">YOUR NEXT WATCH</div>
                <div class="poster-title">{title}</div>
                <div class="rule"></div>
            </div>
        """
    else:
        visual = f"""
            <div class="placeholder">
                <div class="placeholder-icon">🎬</div>
                <div class="placeholder-label">CINEMATCH PICK · 0{index + 1}</div>
                <div class="placeholder-title">{title}</div>
                <div class="placeholder-note">Your next movie night starts here</div>
            </div>
        """

    card_html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        * {{ box-sizing: border-box; }}
        html, body {{
          margin: 0;
          padding: 0;
          width: 100%;
          background: transparent;
          font-family: Arial, Helvetica, sans-serif;
          overflow: hidden;
        }}
        .card {{
          width: 100%;
          overflow: hidden;
          border-radius: 16px;
          background: #191817;
          border: 1px solid rgba(255,255,255,.12);
          box-shadow: 0 10px 28px rgba(0,0,0,.28);
          transition: transform .3s ease, border-color .3s ease, box-shadow .3s ease;
          animation: reveal .55s ease both;
        }}
        .card:hover {{
          transform: translateY(-6px);
          border-color: rgba(215,173,104,.85);
          box-shadow: 0 18px 35px rgba(0,0,0,.42);
        }}
        .poster {{
          width: 100%;
          aspect-ratio: 2 / 3;
          position: relative;
          overflow: hidden;
          background:
            radial-gradient(circle at 50% 30%, rgba(215,173,104,.22), transparent 38%),
            linear-gradient(145deg, #393127, #1b1916 58%, #101010);
        }}
        .poster-image {{
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
          transition: transform .6s ease;
        }}
        .card:hover .poster-image {{ transform: scale(1.06); }}
        .shade {{
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, rgba(0,0,0,.12), transparent 38%, rgba(0,0,0,.88));
        }}
        .topline {{
          position: absolute;
          top: 11px;
          left: 11px;
          right: 11px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }}
        .number {{
          min-width: 30px;
          padding: 7px 9px;
          border-radius: 30px;
          background: #f0cf91;
          color: #17130d;
          font-size: 10px;
          font-weight: 800;
          text-align: center;
        }}
        .tag {{
          padding: 7px 9px;
          border: 1px solid rgba(255,255,255,.2);
          border-radius: 30px;
          background: rgba(12,12,12,.65);
          color: #f4e7d0;
          font-size: 8px;
          font-weight: 700;
          letter-spacing: 1px;
        }}
        .caption {{
          position: absolute;
          left: 13px;
          right: 13px;
          bottom: 14px;
        }}
        .kicker, .placeholder-label {{
          color: #f0cf91;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 1.7px;
          margin-bottom: 7px;
        }}
        .poster-title {{
          color: #fffaf2;
          font-size: 15px;
          line-height: 1.35;
          font-weight: 800;
          overflow-wrap: anywhere;
          text-shadow: 0 2px 12px rgba(0,0,0,.6);
        }}
        .rule {{
          width: 30px;
          height: 2px;
          margin-top: 10px;
          border-radius: 5px;
          background: #d7ad68;
          transition: width .3s ease;
        }}
        .card:hover .rule {{ width: 58px; }}
        .placeholder {{
          position: absolute;
          inset: 0;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          padding: 16px;
          text-align: center;
          background:
            radial-gradient(ellipse at 50% 35%, rgba(215,173,104,.2), transparent 45%),
            linear-gradient(145deg, #393127, #1b1916 58%, #101010);
        }}
        .placeholder-icon {{
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid rgba(240,207,145,.5);
          border-radius: 50%;
          color: #f0cf91;
          background: rgba(215,173,104,.08);
          font-size: 29px;
          margin-bottom: 16px;
        }}
        .placeholder-label {{ text-align: center; }}
        .placeholder-title {{
          color: #f7f0e6;
          font-size: 14px;
          font-weight: 700;
          line-height: 1.4;
          overflow-wrap: anywhere;
        }}
        .placeholder-note {{
          color: #aaa095;
          font-size: 10px;
          margin-top: 9px;
        }}
        .foot {{
          min-height: 68px;
          padding: 12px 13px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          gap: 6px;
          background: linear-gradient(180deg, #1c1b19, #171717);
        }}
        .foot-label {{
          color: #a28e70;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 1.5px;
        }}
        .foot-title {{
          color: #f2eee7;
          font-size: 12px;
          line-height: 1.35;
          font-weight: 700;
          overflow-wrap: anywhere;
        }}
        @keyframes reveal {{
          from {{ opacity: 0; transform: translateY(14px); }}
          to {{ opacity: 1; transform: translateY(0); }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          *, *::before, *::after {{
            animation: none !important;
            transition: none !important;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="poster">{visual}</div>
        <div class="foot">
          <div class="foot-label">RECOMMENDED FILM 0{index + 1}</div>
          <div class="foot-title">{title}</div>
        </div>
      </div>
    </body>
    </html>
    """

    # A real HTML component renders markup instead of showing tags as text.
    components.html(card_html, height=440, scrolling=False)

# =========================================================
# NAVBAR
# =========================================================

st.markdown("""
<div class="navbar">
    <div class="brand">CINE<span>MATCH.</span></div>
    <div class="nav-label">THE ART OF DISCOVERING FILMS</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# HERO SECTION
# =========================================================

st.markdown("""
<div class="hero-content">
    <div class="hero-label">YOUR NEXT GREAT FILM AWAITS</div>
    <div class="hero-heading">
        Not sure what to watch?<br>
        Find your next <span class="hero-highlight">favourite.</span>
    </div>
    <div class="hero-description">
        Discover films that match your taste. Choose a movie you love
        and explore five similar films selected just for your next
        movie night.
    </div>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SEARCH SECTION
# =========================================================

st.markdown(
    '<div class="section-heading">Find your next watch</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="section-description">'
    "Start with a movie you already love. We'll take it from there."
    '</div>',
    unsafe_allow_html=True
)

movie_list = (
    movies["title"]
    .dropna()
    .astype(str)
    .sort_values()
    .unique()
    .tolist()
)

selected_movie = st.selectbox(
    "Choose a movie",
    movie_list,
    index=None,
    placeholder="Search or select a movie..."
)

search_clicked = st.button(
    "✦  Discover Similar Movies",
    use_container_width=True
)

# =========================================================
# BUTTON ACTION
# =========================================================

if search_clicked:
    if selected_movie:
        with st.spinner("Finding films you'll love..."):
            results = recommend(selected_movie)
            st.session_state["recommendations"] = results
            st.session_state["selected_title"] = selected_movie

        if not results:
            st.warning("No recommendations found. Try another movie.")
    else:
        st.warning("Please select a movie first.")

# =========================================================
# RECOMMENDATION RESULTS
# =========================================================

if "recommendations" in st.session_state:
    recommendations = st.session_state["recommendations"]

    st.markdown(
        '<div class="section-heading">Selected for you</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-description">'
        "Films inspired by your choice. Your next watch might be here."
        '</div>',
        unsafe_allow_html=True
    )

    selected_title = html.escape(
        str(st.session_state.get("selected_title", "your movie"))
    )
    st.markdown(
        f"**Because you selected:** :orange[{selected_title}]"
    )

    if recommendations:
        columns = st.columns(5, gap="medium")

        for index, (column, movie) in enumerate(
            zip(columns, recommendations)
        ):
            with column:
                render_movie_card(movie, index)
    else:
        st.info("No similar movies were found.")

    if not API_KEY:
        st.info(
            "Movie recommendations are working. Add your TMDB API key "
            "to load official movie posters."
        )

# =========================================================
# API KEY STATUS
# =========================================================

if not API_KEY:
    with st.expander("How to enable movie posters"):
        st.write(
            "Add your TMDB API key to the Streamlit secrets file."
        )
        st.code(
            'TMDB_API_KEY = "YOUR_ACTUAL_TMDB_API_KEY"',
            language="toml"
        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer-text">
    CINE MATCH &nbsp; • &nbsp; MADE FOR MOVIE LOVERS
</div>
""", unsafe_allow_html=True)
