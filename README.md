# DailyUs 💛

A private daily-photo app for couples. Each day, both partners upload one photo. Only the two of you can ever see them — timeline, chat, and auto-generated collages included.

## Features
- **Signup/login** with hashed passwords + JWT sessions
- **Private pairing** via a one-time, expiring (24h) invite code
- **One photo a day per person** — daily check-in mechanic
- **Couple-scoped access control** — every photo/message query is filtered by `couple_id`, and photo files are served only via short-lived signed tokens (5 min expiry), never as public static files
- **EXIF/metadata stripping** — uploaded photos are re-encoded server-side (strips GPS/location metadata automatically)
- **Simple 1:1 chat**
- **Auto-collage generator** — grid collage from the last 7/14/30 days, built with Pillow
- **Unpair** — cleanly revokes both partners' access to shared content

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   cd dailyus
   python3 -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. (Optional but recommended) Set your own secret keys as environment variables before running in anything beyond local testing:
   ```bash
   export SECRET_KEY="something-long-and-random"
   export JWT_SECRET_KEY="something-else-long-and-random"
   ```

3. Run it:
   ```bash
   python3 app.py
   ```

4. Open `http://localhost:5000` in your browser. Open it in two different browsers (or one normal + one incognito window) to simulate two partners pairing with each other.

## How pairing works
1. User A signs up, goes to the pairing screen, clicks "Generate invite code"
2. User A shares that 6-character code with their partner (text it to them!)
3. User B signs up, enters the code under "Have a code?"
4. Both are now paired — User A's screen auto-detects the pairing (it polls every 3s) and both land on the main app

## Project structure
```
dailyus/
├── app.py                  # Flask app factory + entry point
├── config.py                # App configuration
├── models.py                 # SQLAlchemy models: User, Couple, Photo, Message
├── security_utils.py         # Signed photo tokens, access-control helpers
├── routes_auth.py             # /api/auth/*
├── routes_couple.py            # /api/couple/*
├── routes_photos.py             # /api/photos/*
├── routes_messages.py            # /api/messages
├── routes_collage.py              # /api/collage/*
├── templates/index.html            # Single-page app shell
├── static/css/style.css             # Styling
├── static/js/app.js                  # Frontend logic
├── uploads/                           # Private photo storage (not web-accessible directly)
├── collages/                           # Generated collages
└── instance/dailyus.db                  # SQLite database (auto-created)
```

## Security notes (for your resume/interview talking points)
- Photos are **never** served from a public static folder — every request to view one requires a signed, time-limited token (`itsdangerous`), and the server independently re-verifies that the requesting user still belongs to that photo's couple before returning bytes.
- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2), never stored in plaintext.
- Login errors are intentionally vague ("Invalid email or password") to avoid leaking which field was wrong.
- Uploaded images are re-encoded through Pillow server-side — this strips EXIF metadata (including GPS location data a phone might embed) and validates the file is actually a real image, not just a renamed script.
- Deleting a photo requires you to be its uploader; a 404 (not 403) is returned for another couple's photo ID so an attacker can't even confirm it exists.

## What to build next
- Push notifications / reminders for the daily upload
- "On this day last year" memory resurfacing
- Client-side end-to-end encryption (a differentiator for interviews — even the server couldn't decrypt photos)
- Move from local disk storage to S3/Firebase with signed URLs at the storage layer too
- Real-time chat via WebSockets instead of polling
