
import os
import pickle
import html
import base64
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
# LOAD MODEL
# =========================================================

@st.cache_resource
def load_model():
    movie_file = BASE_DIR / "model" / "movie_list.pkl"
    similarity_file = BASE_DIR / "model" / "similarity.pkl"

    if not movie_file.exists() or not similarity_file.exists():
        raise FileNotFoundError(
            "Please keep movie_list.pkl and similarity.pkl "
            "inside the model folder."
        )

    with open(movie_file, "rb") as f:
        movie_data = pickle.load(f)

    with open(similarity_file, "rb") as f:
        similarity_data = pickle.load(f)

    return movie_data, similarity_data


try:
    movies, similarity = load_model()
except Exception as e:
    st.error("Unable to load movie recommendation model.")
    st.code(str(e))
    st.stop()

# =========================================================
# TMDB API KEY
# =========================================================

env_file = BASE_DIR / ".env"

if env_file.exists():
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()

        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(
                key.strip(),
                value.strip().strip('"').strip("'")
            )

API_KEY = os.getenv("TMDB_API_KEY", "").strip()

if not API_KEY:
    try:
        API_KEY = st.secrets.get("TMDB_API_KEY", "").strip()
    except Exception:
        API_KEY = ""

# =========================================================
# TMDB POSTER FETCHING
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_poster_url(movie_id, movie_title, api_key):
    if not api_key:
        return None

    headers = {
        "accept": "application/json"
    }

    try:
        # First try movie ID
        if movie_id:
            response = requests.get(
                f"https://api.themoviedb.org/3/movie/{int(movie_id)}",
                params={
                    "api_key": api_key,
                    "language": "en-US"
                },
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                poster_path = data.get("poster_path")

                if poster_path:
                    return (
                        "https://image.tmdb.org/t/p/w500"
                        + poster_path
                    )

        # Fallback: search movie by title
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": api_key,
                "query": str(movie_title),
                "include_adult": "false"
            },
            headers=headers,
            timeout=10
        )

        response.raise_for_status()
        results = response.json().get("results", [])

        for result in results:
            poster_path = result.get("poster_path")

            if poster_path:
                return (
                    "https://image.tmdb.org/t/p/w500"
                    + poster_path
                )

    except (requests.RequestException, ValueError, TypeError):
        return None

    return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_poster(movie_id, movie_title, api_key):
    """Download the poster on the server and embed it as a data URI,
    so the browser never has to reach image.tmdb.org itself."""
    url = fetch_poster_url(movie_id, movie_title, api_key)
    if not url:
        return None
    try:
        r = requests.get(url.replace("/w500/", "/w342/"), timeout=10)
        r.raise_for_status()
        mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
        return f"data:{mime};base64," + base64.b64encode(r.content).decode()
    except requests.RequestException:
        return url

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

        movie_id = movie_data.get("movie_id")
        movie_name = str(movie_data["title"])

        poster = fetch_poster(
            movie_id,
            movie_name,
            API_KEY
        )

        recommendations.append({
            "title": movie_name,
            "poster": poster
        })

    return recommendations

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
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--background);
    color: #f5f2ed;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1350px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

#MainMenu, footer {
    visibility: hidden;
}

/* NAVBAR */

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0 23px;
    border-bottom: 1px solid rgba(255,255,255,.1);
    margin-bottom: 35px;
    animation: fadeDown .7s ease both;
}

.brand {
    font-size: 23px;
    font-weight: 800;
    letter-spacing: 1px;
}

.brand span {
    color: var(--gold);
}

.nav-label {
    font-size: 11px;
    letter-spacing: 2px;
    color: #aaa;
}

/* HERO */

.hero-content {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(ellipse at 90% 10%, rgba(160,112,53,.2), transparent 40%),
        linear-gradient(115deg, #201d19, #141414 65%);
    border: 1px solid rgba(215,173,104,.25);
    border-radius: 20px;
    padding: 45px;
    animation: fadeUp .8s ease both;
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

.hero-highlight {
    color: var(--gold);
    font-style: italic;
}

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

/* GENRE ANIMATION */

.reel {
    margin-top: 28px;
    overflow: hidden;
    white-space: nowrap;
    mask-image: linear-gradient(
        90deg, transparent, #000 10%, #000 90%, transparent
    );
}

.reel-track {
    display: inline-block;
    animation: marquee 30s linear infinite;
}

.reel-track span {
    display: inline-block;
    margin-right: 12px;
    padding: 7px 14px;
    border: 1px solid rgba(215,173,104,.3);
    border-radius: 30px;
    color: #d8c7a8;
    font-size: 11px;
    letter-spacing: 1.5px;
    background: rgba(215,173,104,.06);
}

/* SECTION */

.section-heading {
    font-family: 'Playfair Display', serif;
    color: #f4efe7;
    font-size: 30px;
    font-weight: 600;
    margin-top: 28px;
}

.section-description {
    color: #96918a;
    font-size: 13px;
    margin-bottom: 15px;
}

/* SELECT BOX */

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

div[data-baseweb="select"] * {
    color: white !important;
}

/* BUTTON */

.stButton > button {
    background: linear-gradient(
        90deg, #d7ad68, #f0cf91, #d7ad68
    );
    background-size: 200% auto;
    color: #17130d;
    border: none;
    border-radius: 10px;
    min-height: 48px;
    font-weight: 800;
    letter-spacing: .3px;
    transition: all .25s ease;
    animation: shimmer 3s linear infinite;
}

.stButton > button:hover {
    color: #111;
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(215,173,104,.2);
}

/* FOOTER */

.footer-text {
    text-align: center;
    color: #777;
    font-size: 11px;
    letter-spacing: 2px;
    padding-top: 25px;
    border-top: 1px solid #292929;
    margin-top: 55px;
}

/* BACKGROUND AMBIENCE */

[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    width: 520px;
    height: 520px;
    border-radius: 50%;
    filter: blur(110px);
    opacity: .2;
    z-index: 0;
    pointer-events: none;
}

[data-testid="stAppViewContainer"]::before {
    background: #b07a2e;
    top: -160px;
    left: -140px;
    animation: drift1 18s ease-in-out infinite alternate;
}

[data-testid="stAppViewContainer"]::after {
    background: #6b2a4a;
    bottom: -200px;
    right: -160px;
    animation: drift2 22s ease-in-out infinite alternate;
}

.block-container {
    position: relative;
    z-index: 1;
}

/* ANIMATIONS */

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(22px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeDown {
    from {
        opacity: 0;
        transform: translateY(-14px);
    }
    to {
        opacity: 1;
        transform: none;
    }
}

@keyframes shimmer {
    to {
        background-position: 200% center;
    }
}

@keyframes marquee {
    to {
        transform: translateX(-50%);
    }
}

@keyframes drift1 {
    to {
        transform: translate(40vw, 30vh) scale(1.25);
    }
}

@keyframes drift2 {
    to {
        transform: translate(-35vw, -40vh) scale(1.15);
    }
}

/* RESPONSIVE */

@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero-content {
        padding: 30px 23px;
    }

    .hero-heading {
        font-size: 37px;
    }

    .nav-label {
        font-size: 9px;
    }
}

@media (max-width: 480px) {
    .hero-heading {
        font-size: 32px;
    }

    .hero-label {
        font-size: 9px;
        letter-spacing: 2px;
    }

    .nav-label {
        display: none;
    }
}

/* ===== Movie grid (no iframes) ===== */
.movie-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 18px;
    margin-top: 12px;
    perspective: 1000px;
}
@media (max-width: 1100px) { .movie-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 640px)  { .movie-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; } }
.movie-card {
    position: relative; overflow: hidden; border-radius: 16px;
    background: #191817; border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 10px 28px rgba(0,0,0,.28);
    transition: transform .4s cubic-bezier(.2,.8,.2,1), border-color .3s, box-shadow .3s;
    animation: cardIn .8s cubic-bezier(.2,.8,.2,1) both;
}
.movie-card::after {
    content: ""; position: absolute; inset: 0; z-index: 5; pointer-events: none;
    background: linear-gradient(115deg, transparent 30%, rgba(255,240,210,.22) 50%, transparent 70%);
    transform: translateX(-120%); transition: transform .9s ease;
}
.movie-card:hover::after { transform: translateX(120%); }
.movie-card:hover {
    transform: translateY(-8px) rotateX(4deg);
    border-color: rgba(215,173,104,.85);
    box-shadow: 0 20px 40px rgba(0,0,0,.5), 0 0 24px rgba(215,173,104,.15);
}
.poster-frame { position: relative; width: 100%; aspect-ratio: 2 / 3; overflow: hidden;
    background: linear-gradient(145deg,#393127,#101010); }
.poster-image { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
    display: block; transition: transform .6s ease; }
.movie-card:hover .poster-image { transform: scale(1.07); }
.poster-shade { position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,.12), transparent 38%, rgba(0,0,0,.88)); }
.poster-topline { position: absolute; top: 10px; left: 10px; right: 10px; z-index: 2;
    display: flex; justify-content: space-between; align-items: center; }
.poster-index { padding: 6px 9px; border-radius: 30px; background: #f0cf91; color: #17130d;
    font-size: 10px; font-weight: 800; }
.poster-tag { padding: 6px 9px; border-radius: 30px; border: 1px solid rgba(255,255,255,.2);
    background: rgba(12,12,12,.65); color: #f4e7d0; font-size: 8px; font-weight: 700; letter-spacing: 1px; }
.poster-caption { position: absolute; left: 13px; right: 13px; bottom: 14px; z-index: 2; }
.poster-kicker, .placeholder-label { color: #f0cf91; font-size: 9px; font-weight: 800;
    letter-spacing: 1.7px; margin-bottom: 6px; }
.poster-title { color: #fffaf2; font-size: 15px; font-weight: 800; line-height: 1.35;
    overflow-wrap: anywhere; text-shadow: 0 2px 12px rgba(0,0,0,.6); }
.poster-rule { width: 30px; height: 2px; margin-top: 9px; background: #d7ad68; transition: width .3s; }
.movie-card:hover .poster-rule { width: 58px; }
.poster-placeholder { position: absolute; inset: 0; display: flex; flex-direction: column;
    justify-content: center; align-items: center; padding: 16px; text-align: center;
    background: radial-gradient(ellipse at 50% 35%,rgba(215,173,104,.2),transparent 45%),
                linear-gradient(145deg,#393127,#101010); }
.placeholder-icon { width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;
    border: 1px solid rgba(240,207,145,.5); border-radius: 50%; font-size: 27px; margin-bottom: 14px; }
.placeholder-title { color: #f7f0e6; font-size: 14px; font-weight: 700; overflow-wrap: anywhere; }
.placeholder-note { color: #aaa095; font-size: 10px; margin-top: 8px; }
.card-foot { padding: 12px 13px; min-height: 64px; display: flex; flex-direction: column;
    justify-content: center; gap: 5px; background: linear-gradient(180deg,#1c1b19,#171717); }
.card-foot-label { color: #a28e70; font-size: 9px; font-weight: 800; letter-spacing: 1.5px; }
.card-foot-title { color: #f2eee7; font-size: 12px; font-weight: 700; line-height: 1.35; overflow-wrap: anywhere; }
@keyframes cardIn {
    from { opacity: 0; transform: translateY(40px) rotateX(16deg) scale(.94); }
    to   { opacity: 1; transform: none; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .01ms !important;
        transition-duration: .01ms !important;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# MOVIE CARD
# =========================================================

def render_movie_card(movie, index):
    title = html.escape(
        str(movie.get("title") or "Untitled movie")
    )

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
            <div class="placeholder-label">
                CINEMATCH PICK · 0{index + 1}
            </div>
            <div class="placeholder-title">{title}</div>
            <div class="placeholder-note">
                Your next movie night starts here
            </div>
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
        font-family: Arial, sans-serif;
        overflow: hidden;
    }}

    body {{
        padding: 8px 4px;
        perspective: 900px;
    }}

    .card {{
        width: 100%;
        overflow: hidden;
        border-radius: 16px;
        background: #191817;
        border: 1px solid rgba(255,255,255,.12);
        box-shadow: 0 10px 28px rgba(0,0,0,.28);
        transition: transform .3s ease, box-shadow .3s ease;
        animation: reveal .8s ease {index * 0.15:.2f}s both;
    }}

    .card:hover {{
        box-shadow: 0 18px 35px rgba(0,0,0,.42);
        border-color: rgba(215,173,104,.85);
    }}

    .poster {{
        width: 100%;
        aspect-ratio: 2 / 3;
        position: relative;
        overflow: hidden;
        background: linear-gradient(145deg,#393127,#101010);
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

    .card:hover .poster-image {{
        transform: scale(1.06);
    }}

    .shade {{
        position: absolute;
        inset: 0;
        background: linear-gradient(
            180deg,
            rgba(0,0,0,.12),
            transparent 38%,
            rgba(0,0,0,.88)
        );
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
        padding: 7px 9px;
        border-radius: 30px;
        background: #f0cf91;
        color: #17130d;
        font-size: 10px;
        font-weight: 800;
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
    }}

    .rule {{
        width: 30px;
        height: 2px;
        margin-top: 10px;
        background: #d7ad68;
        transition: width .3s ease;
    }}

    .card:hover .rule {{
        width: 58px;
    }}

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
            radial-gradient(ellipse at 50% 35%,rgba(215,173,104,.2),transparent 45%),
            linear-gradient(145deg,#393127,#101010);
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
        font-size: 29px;
        margin-bottom: 16px;
    }}

    .placeholder-label {{
        text-align: center;
    }}

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
        background: linear-gradient(180deg,#1c1b19,#171717);
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
        from {{
            opacity: 0;
            transform: translateY(35px) scale(.94);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    </style>
    </head>

    <body>
        <div class="card">
            <div class="poster">
                {visual}
            </div>

            <div class="foot">
                <div class="foot-label">
                    RECOMMENDED FILM 0{index + 1}
                </div>
                <div class="foot-title">{title}</div>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(
        card_html,
        height=460,
        scrolling=False
    )

def build_movie_grid(recommendations):
    """Render all cards as one HTML grid (no iframes), on single lines so
    Markdown never turns indented HTML into a code block."""
    cards = []
    for index, movie in enumerate(recommendations):
        title = html.escape(str(movie.get("title") or "Untitled movie"))
        poster = movie.get("poster")
        if poster:
            src = html.escape(str(poster), quote=True)
            visual = (
                f'<img class="poster-image" src="{src}" alt="Poster for {title}">'
                '<div class="poster-shade"></div>'
                f'<div class="poster-topline"><span class="poster-index">0{index + 1}</span>'
                '<span class="poster-tag">CINEMATCH PICK</span></div>'
                f'<div class="poster-caption"><div class="poster-kicker">YOUR NEXT WATCH</div>'
                f'<div class="poster-title">{title}</div><div class="poster-rule"></div></div>'
            )
        else:
            visual = (
                '<div class="poster-placeholder"><div class="placeholder-icon">🎬</div>'
                f'<div class="placeholder-label">CINEMATCH PICK · 0{index + 1}</div>'
                f'<div class="placeholder-title">{title}</div>'
                '<div class="placeholder-note">Your next movie night starts here</div></div>'
            )
        cards.append(
            f'<div class="movie-card" style="animation-delay:{index * 0.12:.2f}s">'
            f'<div class="poster-frame">{visual}</div>'
            f'<div class="card-foot"><div class="card-foot-label">RECOMMENDED FILM 0{index + 1}</div>'
            f'<div class="card-foot-title">{title}</div></div></div>'
        )
    return '<div class="movie-grid">' + "".join(cards) + "</div>"


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
<div class="hero-label">
YOUR NEXT GREAT FILM AWAITS
</div>
<div class="hero-heading">
Not sure what to watch?<br>
Find your next <span class="hero-highlight">favourite.</span>
</div>
<div class="hero-description">
Discover films that match your taste.
Choose a movie you love and explore five similar films
selected just for your next movie night.
</div>
<div class="hero-divider"></div>
<div class="reel">
<div class="reel-track">
<span>🎬 ACTION</span>
<span>💘 ROMANCE</span>
<span>👽 SCI-FI</span>
<span>😂 COMEDY</span>
<span>🕵️ THRILLER</span>
<span>🧙 FANTASY</span>
<span>👻 HORROR</span>
<span>🎭 DRAMA</span>
<span>🚀 ADVENTURE</span>
<span>🎬 ACTION</span>
<span>💘 ROMANCE</span>
<span>👽 SCI-FI</span>
<span>😂 COMEDY</span>
<span>🕵️ THRILLER</span>
<span>🧙 FANTASY</span>
<span>👻 HORROR</span>
<span>🎭 DRAMA</span>
<span>🚀 ADVENTURE</span>
</div>
</div>
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
        st.markdown(build_movie_grid(recommendations), unsafe_allow_html=True)

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
            "Add your TMDB API key to your .env file."
        )

        st.code(
            'TMDB_API_KEY="YOUR_ACTUAL_TMDB_API_KEY"',
            language="text"
        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer-text">
    CINE MATCH &nbsp; • &nbsp; MADE FOR MOVIE LOVERS
</div>
""", unsafe_allow_html=True)
