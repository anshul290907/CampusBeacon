# CampusBeacon

A beginner-friendly Flask + SQLAlchemy campus discovery platform for NSUT-style campus information. It includes database-backed event discovery, registrations, favorites, clubs, notices, sticky notes, notifications, a Leaflet map, protected sessions, and the foundation for organizer/admin workflows.

## What works
- Responsive landing page, navigation, events, clubs, notices, dashboard, notes, and map.
- SQLite persistence through SQLAlchemy; models include users, events, registrations, clubs, notices, favorites, notes, notifications, and map locations.
- Real Google OAuth flow through Authlib when credentials are configured.
- Server-side verified-email and exact-domain allow-list checks.
- Duplicate registration and favorite constraints.
- Student dashboard and owner-scoped notes.
- Protected admin metrics route; no default administrator is created.
- Automated smoke tests with pytest.

## Quick start (Windows PowerShell)
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python seed.py
python run.py
```
Open http://127.0.0.1:5000.

## Google OAuth setup
1. Open Google Cloud Console and create/select a project.
2. Configure the OAuth consent screen.
3. Create an OAuth Client ID for a Web application.
4. Add `http://127.0.0.1:5000/auth/google/callback` as an authorized redirect URI.
5. Put `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SECRET_KEY`, and the confirmed `ALLOWED_EMAIL_DOMAINS` in `.env`.

CampusBeacon does not fake login when OAuth is unconfigured. Add a separate HTTPS callback URI for production.

## Database and tests
The app creates the local SQLite database on startup for a simple demo. Run `python -m pytest`. The seed command is repeatable and creates clearly labeled demo content only when rows are absent.

## First administrator
Do not promote the first login automatically. After verifying an account you control, use a controlled shell command to set `User.role='admin'`. Never expose a public admin-registration route or commit credentials.

## Architecture
Browser → Flask blueprints → SQLAlchemy models → SQLite (replaceable with PostgreSQL). Templates use Jinja and Bootstrap; the map uses Leaflet + OpenStreetMap tiles. OAuth is handled by Authlib.

## Deployment notes
Use HTTPS, a strong secret key, production environment variables, and Gunicorn or another WSGI server. SQLite is suitable for local demos but should move to PostgreSQL for concurrent production writes. Ephemeral hosting filesystems may lose SQLite data, so use persistent storage or PostgreSQL. Run migrations during deployment and configure the production OAuth callback exactly.

## Honest limitations
Core student-facing flows and protected admin metrics are implemented. Full organizer CRUD, notice moderation UI, uploads, automated reminders, and audit screens are next milestones, not fake buttons. Campus coordinates must be verified before adding them as published locations.
