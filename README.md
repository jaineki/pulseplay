# PulsePlay Music

A Spotify-like music streaming web application with a dark theme, album cards, music player, and bottom navigation. Built with Python FastAPI backend and vanilla HTML/CSS/JS frontend.

## Project Structure

```
pulseplay/
├── main.py              # Python backend (FastAPI)
├── requirements.txt     # Python dependencies
├── render-build.sh      # Render build script
├── render-start.sh      # Render start script
├── .env.example         # Environment variables template
├── README.md            # This file
└── public/
    └── index.html       # Frontend (single file: HTML + CSS + JS)
```

## Quick Start (Local)

```bash
pip install -r requirements.txt
python main.py
```

Open http://localhost:10000 in your browser.

Demo login: `demo@pulseplay.com` / `demo123`

## Deploy to Render

### Step 1: Push to GitHub

```bash
cd pulseplay
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pulseplay.git
git push -u origin main
```

### Step 2: Create Service on Render

1. Go to https://render.com and sign in
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure:

| Setting | Value |
|---------|-------|
| Name | pulseplay |
| Environment | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

### Step 3: Add Environment Variables (Optional)

In the Render dashboard, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| SPOTIFY_CLIENT_ID | (from Spotify Developer Dashboard) |
| SPOTIFY_CLIENT_SECRET | (from Spotify Developer Dashboard) |

### Step 4: Deploy

Click **Create Web Service**. Your app will be live at `https://pulseplay.onrender.com`.

## Features

| Feature | Description |
|---------|-------------|
| Dark Theme UI | Deep navy/purple gradient background |
| Song Grid | Album artwork cards with titles and artists |
| Search | Search tracks, albums, playlists, artists |
| Music Player | Bottom bar with play/pause/next/prev/like |
| Full-Screen Player | Large album art with lyrics |
| Album Detail | Tracklist view with play all |
| Favorites | Like/unlike songs |
| Auth | Login/signup with tokens |
| Spotify API | Real music data (with credentials) |
| Demo Data | Works without Spotify credentials |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login |
| POST | `/auth/signup` | Create account |
| GET | `/search` | Search music |
| GET | `/album/{id}` | Album details |
| GET | `/recommendations` | Recommendations |
| POST | `/download` | Stream audio |
| GET | `/getLyrics` | Get lyrics |
| GET | `/favorites` | Get favorites |
| GET | `/playlists` | Get playlists |
| GET | `/profile` | Get profile |

## Spotify Integration

To use real Spotify data:

1. Go to https://developer.spotify.com/dashboard
2. Create a new app
3. Copy Client ID and Client Secret
4. Add them as environment variables in Render

Without Spotify credentials, the app uses built-in demo data.

## License

MIT
