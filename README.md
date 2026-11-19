# CampusBeacon

A beginner-friendly Flask + SQLAlchemy campus discovery platform for campus information. It includes database-backed event discovery, registrations, favorites, clubs, notices, sticky notes, notifications, a Leaflet map, protected sessions, and the foundation for organizer/admin workflows.

## Features
- Responsive landing page, navigation, events, clubs, notices, dashboard, notes, and map.
- SQLite persistence through SQLAlchemy; models include users, events, registrations, clubs, notices, favorites, notes, notifications, and map locations.
- Protected sessions, duplicate registration and favorite constraints, owner-scoped notes, and protected admin metrics.
- Automated smoke tests with pytest.
- Live notices imported from the public NSUT notifications listing.
- Overview page with recent notices, live/upcoming events, and browser-saved pinned notice reminders.
- Full event list grouped into finished, live, and upcoming events.

Overview notice pins and personal deadlines are stored in the current browser's local storage because this demo does not offer sign-in. They are not shared between devices or browsers.

Sign-in is currently unavailable. The project has no authentication provider enabled, and private account features remain protected until a secure method is implemented. No default administrator is created.

## Quick start (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python seed.py
python run.py
```
Open http://127.0.0.1:5000.

## Live NSUT notices
While the Flask server is running, CampusBeacon checks the public [NSUT notices and circulars page](https://www.imsnsit.org/imsnsit/notifications.php) every 45 seconds and imports new items without removing existing notices. An open Notices page refreshes its list every 15 seconds. The sync reads notice titles, dates, and publishers; the portal's protected document links are not copied. If the portal is temporarily unavailable, the latest saved notices remain visible and CampusBeacon retries automatically.

## Database and tests
The app creates the local SQLite database on startup for a simple demo. Run `python -m pytest`. The seed command is repeatable and creates clearly labeled demo content only when rows are absent.

## First administrator
Do not promote a user automatically. Use a controlled shell command only after a secure authentication method is available and the account is verified. Never expose a public admin-registration route or commit credentials.

## Architecture
Browser → Flask blueprints → SQLAlchemy models → SQLite (replaceable with PostgreSQL). Templates use Jinja and Bootstrap; the map uses Leaflet + OpenStreetMap tiles.

## Deployment notes
Use HTTPS, a strong secret key, production environment variables, and Gunicorn or another WSGI server. SQLite is suitable for local demos but should move to PostgreSQL for concurrent production writes. Ephemeral hosting filesystems may lose SQLite data, so use persistent storage or PostgreSQL. Run migrations during deployment.

## Honest limitations
Core public-facing flows and protected admin metrics are implemented. Sign-in and private account features are unavailable until a secure authentication method is implemented. Full organizer CRUD, notice moderation UI, uploads, automated reminders, and audit screens are future milestones. Campus coordinates must be verified before adding them as published locations.



## Contributors
- *Garima Verma* – [@garimaverma2009](https://github.com)
