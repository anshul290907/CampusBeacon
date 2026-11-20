from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User, Event, Club, Notice, CampusLocation
from app.location_data import CAMPUS_LOCATIONS
from app.catalog_data import CLUBS

app = create_app()

with app.app_context():
    db.create_all()
    organizer = User.query.filter_by(email='organizer@example.invalid').first()
    if not organizer:
        organizer = User(email='organizer@example.invalid', name='Demo Organizer', role='organizer')
        db.session.add(organizer)
        db.session.flush()
    if not Event.query.first():
        base = datetime.utcnow() + timedelta(days=3)
        db.session.add_all([
            Event(title='Campus Innovation Sprint', slug='campus-innovation-sprint', description='A practical build day for ideas, prototypes, and ambitious teams.', category='Hackathon', venue='Innovation Lab', starts_at=base, ends_at=base + timedelta(hours=8), registration_deadline=base - timedelta(hours=12), capacity=80, organizer_id=organizer.id),
            Event(title='Designing for Student Life', slug='designing-for-student-life', description='A hands-on workshop on research, prototyping, and inclusive campus products.', category='Workshop', venue='Lecture Hall 2', starts_at=base + timedelta(days=2), ends_at=base + timedelta(days=2, hours=2), organizer_id=organizer.id),
        ])
    existing = {club.slug for club in Club.query.all()}
    added = 0
    for name, slug, description, category, source in CLUBS:
        if slug not in existing:
            db.session.add(Club(name=name, slug=slug, description=description, category=category, website_url=source, recruitment_status='not listed'))
            added += 1
    existing_places = {place.name.casefold() for place in CampusLocation.query.all()}
    added_places = 0
    for name, description, latitude, longitude, category in CAMPUS_LOCATIONS:
        if name.casefold() not in existing_places:
            db.session.add(CampusLocation(
                name=name, description=description, latitude=latitude,
                longitude=longitude, category=category,
                publication_status='published'
            ))
            added_places += 1

    if not Notice.query.first():
        db.session.add(Notice(title='Welcome to CampusBeacon', content='This notice is sample development content. Replace it with verified announcements before presenting publicly.', category='General', issuer='CampusBeacon demo', author_id=organizer.id))
    db.session.commit()
    print(f'Added {added} missing NSUT society/community entries and {added_places} campus locations; existing records were kept.')
