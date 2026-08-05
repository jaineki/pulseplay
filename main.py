"""
PulsePlay Music - Full Stack App (Backend + Frontend)
Deploy on Render: https://render.com
"""

import os
import hashlib
import secrets
import time
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

app = FastAPI(title="PulsePlay Music", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Configuration
# ============================================================
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
PORT = int(os.getenv("PORT", 10000))

# In-memory storage
users_db = {}
tokens_db = {}
spotify_token_cache = {"token": "", "expires": 0}

# ============================================================
# Pydantic Models
# ============================================================
class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class TelegramAuthRequest(BaseModel):
    initData: str

class DownloadRequest(BaseModel):
    id: str

class TrackRecommendationRequest(BaseModel):
    tracks: dict

# ============================================================
# Helpers
# ============================================================
def generate_token():
    return secrets.token_hex(32)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def parse_duration(ms: int) -> str:
    total_seconds = ms // 1000
    return f"{total_seconds // 60}:{total_seconds % 60:02d}"

# ============================================================
# Demo Users
# ============================================================
DEMO_USERS = {
    "demo@pulseplay.com": {
        "password": "demo123",
        "username": "DemoUser",
        "email": "demo@pulseplay.com",
        "token": "",
    }
}

# ============================================================
# Demo Music Data
# ============================================================
DEMO_SONGS = [
    {"audio_id":"demo_001","track_id":"demo_001","title":"Ayye","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":214000},
    {"audio_id":"demo_002","track_id":"demo_002","title":"Mr. G (feat. Deech)","artist":"Tiji Jojo, Deech","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":198000},
    {"audio_id":"demo_003","track_id":"demo_003","title":"Sky-Dweller","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":205000},
    {"audio_id":"demo_004","track_id":"demo_004","title":"SOSOGU (feat. JJJ)","artist":"Tiji Jojo, JJJ","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":231000},
    {"audio_id":"demo_005","track_id":"demo_005","title":"Waiting for Good Time","artist":"ATARASHII GAKKO!","album":"Waiting for Good Time","cover_url":"https://i.scdn.co/image/ab67616d00001e027cabf05b9af7fa80887a71a8","preview_url":"","duration_ms":245000},
    {"audio_id":"demo_006","track_id":"demo_006","title":"Stateside","artist":"PinkPantheress","album":"Stateside","cover_url":"https://i.scdn.co/image/ab67616d00001e023c27321852b9e18e3e2ee644","preview_url":"","duration_ms":189000},
    {"audio_id":"demo_007","track_id":"demo_007","title":"Dance Dance","artist":"ATARASHII GAKKO!","album":"Waiting for Good Time","cover_url":"https://i.scdn.co/image/ab67616d00001e027cabf05b9af7fa80887a71a8","preview_url":"","duration_ms":210000},
    {"audio_id":"demo_008","track_id":"demo_008","title":"Tonight","artist":"PinkPantheress","album":"Stateside","cover_url":"https://i.scdn.co/image/ab67616d00001e023c27321852b9e18e3e2ee644","preview_url":"","duration_ms":176000},
    {"audio_id":"demo_009","track_id":"demo_009","title":"illusion","artist":"Ryokuoushoku Shakai","album":"illusion","cover_url":"https://i.scdn.co/image/ab67616d00001e02b899a3cc0c47176832190b31","preview_url":"","duration_ms":222000},
    {"audio_id":"demo_010","track_id":"demo_010","title":"Kore de E","artist":"ATARASHII GAKKO!","album":"Waiting for Good Time","cover_url":"https://i.scdn.co/image/ab67616d00001e027cabf05b9af7fa80887a71a8","preview_url":"","duration_ms":201000},
    {"audio_id":"demo_011","track_id":"demo_011","title":"Friday Night Fantasy","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":195000},
    {"audio_id":"demo_012","track_id":"demo_012","title":"Take Me with You","artist":"ATARASHII GAKKO!","album":"Waiting for Good Time","cover_url":"https://i.scdn.co/image/ab67616d00001e027cabf05b9af7fa80887a71a8","preview_url":"","duration_ms":218000},
    {"audio_id":"demo_013","track_id":"demo_013","title":"Catch That Train","artist":"ATARASHII GAKKO!","album":"Waiting for Good Time","cover_url":"https://i.scdn.co/image/ab67616d00001e027cabf05b9af7fa80887a71a8","preview_url":"","duration_ms":207000},
    {"audio_id":"demo_014","track_id":"demo_014","title":"UTAGE HIKARU","artist":"ATARASHII GAKKO!","album":"Waiting for Good Time","cover_url":"https://i.scdn.co/image/ab67616d00001e027cabf05b9af7fa80887a71a8","preview_url":"","duration_ms":193000},
    {"audio_id":"demo_015","track_id":"demo_015","title":"Party Girls (feat. Rashel)","artist":"Tiji Jojo, Rashel","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":224000},
    {"audio_id":"demo_016","track_id":"demo_016","title":"Go Up (feat. MaRI)","artist":"Tiji Jojo, MaRI","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":187000},
    {"audio_id":"demo_017","track_id":"demo_017","title":"4Season","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":199000},
    {"audio_id":"demo_018","track_id":"demo_018","title":"Malibu Dream","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":212000},
    {"audio_id":"demo_019","track_id":"demo_019","title":"Precious","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":203000},
    {"audio_id":"demo_020","track_id":"demo_020","title":"Rainy Miami","artist":"Tiji Jojo","album":"Malibu Dream","cover_url":"https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52","preview_url":"","duration_ms":191000},
]

# ============================================================
# Spotify API
# ============================================================
async def get_spotify_token():
    now = time.time()
    if spotify_token_cache["token"] and spotify_token_cache["expires"] > now + 60:
        return spotify_token_cache["token"]
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        )
        if resp.status_code == 200:
            data = resp.json()
            spotify_token_cache["token"] = data["access_token"]
            spotify_token_cache["expires"] = now + data.get("expires_in", 3600)
            return data["access_token"]
    return None

async def spotify_search(query: str, search_type: str = "track", limit: int = 20):
    token = await get_spotify_token()
    if not token:
        return {}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": search_type, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
    return {}

def parse_spotify_tracks(data: dict) -> list:
    tracks = []
    for item in data.get("tracks", {}).get("items", []):
        cover_url = item.get("album", {}).get("images", [{}])[0].get("url", "")
        tracks.append({
            "audio_id": item["id"], "track_id": item["id"],
            "title": item["name"],
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "album": item.get("album", {}).get("name", ""),
            "cover_url": cover_url, "preview_url": item.get("preview_url", ""),
            "duration_ms": item.get("duration_ms", 0),
        })
    return tracks

def parse_spotify_albums(data: dict) -> list:
    albums = []
    for item in data.get("albums", {}).get("items", []):
        cover_url = item.get("images", [{}])[0].get("url", "")
        albums.append({
            "id": item["id"], "title": item["name"],
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "cover_url": cover_url, "release_date": item.get("release_date", ""),
            "total_tracks": item.get("total_tracks", 0),
        })
    return albums

def parse_spotify_artists(data: dict) -> list:
    artists = []
    for item in data.get("artists", {}).get("items", []):
        image_url = item.get("images", [{}])[0].get("url", "")
        artists.append({
            "id": item["id"], "name": item["name"],
            "genres": item.get("genres", []), "image_url": image_url,
            "followers": item.get("followers", {}).get("total", 0),
        })
    return artists

def parse_spotify_playlists(data: dict) -> list:
    playlists = []
    for item in data.get("playlists", {}).get("items", []):
        cover_url = item.get("images", [{}])[0].get("url", "")
        playlists.append({
            "id": item["id"], "name": item["name"],
            "owner": item.get("owner", {}).get("display_name", ""),
            "cover_url": cover_url, "tracks_total": item.get("tracks", {}).get("total", 0),
            "description": item.get("description", ""),
        })
    return playlists

# ============================================================
# Auth Routes
# ============================================================
@app.post("/auth/login")
async def login(request: LoginRequest):
    user = DEMO_USERS.get(request.email)
    if user and (request.password == user.get("password", "") or hash_password(request.password) == user.get("password_hash", "")):
        token = generate_token()
        tokens_db[token] = user
        user["token"] = token
        return {"token": token, "username": user["username"], "email": user["email"]}
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/auth/signup")
async def signup(request: SignupRequest):
    if request.email in DEMO_USERS:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = {"username": request.username, "email": request.email, "password": request.password, "password_hash": hash_password(request.password)}
    DEMO_USERS[request.email] = user
    token = generate_token()
    tokens_db[token] = user
    return {"token": token, "username": request.username, "email": request.email}

@app.post("/auth/telegram")
async def telegram_auth(request: TelegramAuthRequest):
    return {"token": generate_token(), "username": "TelegramUser", "email": "telegram@pulseplay.com", "telegram_id": "demo", "authenticated_bot": "pulseplay_bot"}

# ============================================================
# Search & Music Routes
# ============================================================
@app.get("/search")
async def search(q: str = "", search_type: str = "track", limit: int = 20):
    if SPOTIFY_CLIENT_ID:
        data = await spotify_search(q, search_type, limit)
        if search_type == "track": return {"tracks": parse_spotify_tracks(data)}
        elif search_type == "album": return {"albums": parse_spotify_albums(data)}
        elif search_type == "artist": return {"artists": parse_spotify_artists(data)}
        elif search_type == "playlist": return {"playlists": parse_spotify_playlists(data)}
    # Fallback demo data
    if search_type == "track":
        results = [s for s in DEMO_SONGS if q.lower() in s["title"].lower() or q.lower() in s["artist"].lower()]
        return {"tracks": results if results else DEMO_SONGS[:limit]}
    elif search_type == "album":
        albums, seen = [], set()
        for s in DEMO_SONGS:
            if s["album"] not in seen:
                seen.add(s["album"])
                albums.append({"id": s["album"].lower().replace(" ", "_"), "title": s["album"], "artist": s["artist"].split(",")[0].strip(), "cover_url": s["cover_url"], "release_date": "", "total_tracks": sum(1 for x in DEMO_SONGS if x["album"] == s["album"])})
        return {"albums": albums[:limit]}
    elif search_type == "artist":
        artists, seen = [], set()
        for s in DEMO_SONGS:
            for a in s["artist"].split(","):
                name = a.strip()
                if name not in seen:
                    seen.add(name)
                    artists.append({"id": name.lower().replace(" ", "_"), "name": name, "genres": [], "image_url": s["cover_url"], "followers": 0})
        return {"artists": artists[:limit]}
    elif search_type == "playlist":
        return {"playlists": [{"id": "top_hits", "name": "Top Hits", "owner": "PulsePlay", "cover_url": DEMO_SONGS[0]["cover_url"], "tracks_total": 10, "description": "Today's top hits"}, {"id": "chill_vibes", "name": "Chill Vibes", "owner": "PulsePlay", "cover_url": DEMO_SONGS[4]["cover_url"], "tracks_total": 8, "description": "Relax and unwind"}]}
    return {"tracks": DEMO_SONGS}

@app.get("/recommendations")
async def recommendations(q: str = ""):
    track_ids = q.split(",") if q else []
    if SPOTIFY_CLIENT_ID and track_ids:
        token = await get_spotify_token()
        if token:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.spotify.com/v1/recommendations", headers={"Authorization": f"Bearer {token}"}, params={"seed_tracks": ",".join(track_ids[:5]), "limit": 20})
                if resp.status_code == 200:
                    return {"tracks": parse_spotify_tracks({"tracks": resp.json()})}
    return {"tracks": DEMO_SONGS}

@app.post("/trackRecommendation")
async def track_recommendation(request: TrackRecommendationRequest):
    return await recommendations(",".join(request.tracks.get("track_ids", [])))

@app.post("/download")
async def download_song(request: DownloadRequest):
    song = None
    for s in DEMO_SONGS:
        if s["audio_id"] == request.id:
            song = s
            break
    if song and song.get("preview_url"):
        async with httpx.AsyncClient() as client:
            resp = await client.get(song["preview_url"])
            if resp.status_code == 200:
                return StreamingResponse(iter([resp.content]), media_type="audio/mpeg", headers={"Content-Length": str(len(resp.content))})
    if SPOTIFY_CLIENT_ID:
        token = await get_spotify_token()
        if token:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://api.spotify.com/v1/tracks/{request.id}", headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200 and resp.json().get("preview_url"):
                    return StreamingResponse(client.stream("GET", resp.json()["preview_url"]), media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Song not found or preview unavailable")

@app.get("/getLyrics")
async def get_lyrics(track_id: str, is_sync: bool = False):
    demo_lyrics = "🎵 PulsePlay Music 🎵\n\nThis is a demo track.\nIn production, lyrics would be fetched\nfrom a lyrics API service.\n\nConnect the Spotify API for\nreal track data and previews."
    if is_sync:
        return {"data": [{"startTimeMs": 0, "words": "🎵 PulsePlay Music 🎵", "endTimeMs": 3000}, {"startTimeMs": 3000, "words": "This is a demo track.", "endTimeMs": 6000}, {"startTimeMs": 6000, "words": "In production, lyrics would be fetched", "endTimeMs": 9000}, {"startTimeMs": 9000, "words": "from a lyrics API service.", "endTimeMs": 12000}, {"startTimeMs": 12000, "words": "Connect the Spotify API for", "endTimeMs": 15000}, {"startTimeMs": 15000, "words": "real track data and previews.", "endTimeMs": 18000}]}
    return {"data": demo_lyrics}

@app.get("/album/{album_id}")
async def get_album(album_id: str):
    if SPOTIFY_CLIENT_ID:
        token = await get_spotify_token()
        if token:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://api.spotify.com/v1/albums/{album_id}", headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    data = resp.json()
                    cover_url = data.get("images", [{}])[0].get("url", "")
                    tracks = []
                    for t in data.get("tracks", {}).get("items", []):
                        tracks.append({"audio_id": t["id"], "track_id": t["id"], "title": t["name"], "artist": ", ".join(a["name"] for a in t.get("artists", [])), "album": data["name"], "cover_url": cover_url, "preview_url": t.get("preview_url", ""), "duration_ms": t.get("duration_ms", 0), "track_number": t.get("track_number", 0)})
                    return {"id": album_id, "title": data["name"], "artist": ", ".join(a["name"] for a in data.get("artists", [])), "cover_url": cover_url, "release_date": data.get("release_date", ""), "tracks": tracks}
    demo_album = {"id": album_id, "title": "Malibu Dream", "artist": "Tiji Jojo", "cover_url": "https://i.scdn.co/image/ab67616d00001e02befc8137de3448ed44e9de52", "release_date": "2024-01-15", "tracks": [s for s in DEMO_SONGS if s["album"] == "Malibu Dream"]}
    return demo_album

# ============================================================
# User Routes
# ============================================================
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    if token in tokens_db:
        return tokens_db[token]
    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/favorites")
async def get_favorites(user=Depends(get_current_user)):
    return {"tracks": DEMO_SONGS[:5]}

@app.post("/favorites/{track_id}")
async def add_favorite(track_id: str, user=Depends(get_current_user)):
    return {"message": "Added to favorites", "track_id": track_id}

@app.delete("/favorites/{track_id}")
async def remove_favorite(track_id: str, user=Depends(get_current_user)):
    return {"message": "Removed from favorites", "track_id": track_id}

@app.get("/playlists")
async def get_playlists(user=Depends(get_current_user)):
    return {"playlists": [{"id": "pl_1", "name": "My Favorites", "track_count": 10}, {"id": "pl_2", "name": "Chill Mix", "track_count": 15}]}

@app.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return {"username": user.get("username", ""), "email": user.get("email", "")}

# ============================================================
# Health & Static Files
# ============================================================
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api")
async def root():
    return {"name": "PulsePlay Music", "version": "1.0.0", "status": "running", "spotify_connected": bool(SPOTIFY_CLIENT_ID)}

# Serve frontend static files from public/ folder (mounted first to catch / and index.html)
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
