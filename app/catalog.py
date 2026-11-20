"""Idempotent population of the public clubs and campus location directory."""

from .catalog_data import CLUBS
from .extensions import db
from .location_data import CAMPUS_LOCATIONS
from .models import CampusLocation, Club


def ensure_catalog_data():
    existing_clubs = {club.slug for club in Club.query.all()}
    for name, slug, description, category, website_url in CLUBS:
        if slug not in existing_clubs:
            db.session.add(Club(
                name=name,
                slug=slug,
                description=description,
                category=category,
                website_url=website_url,
                recruitment_status='not listed',
            ))

    existing_places = {place.name.casefold() for place in CampusLocation.query.all()}
    for name, description, latitude, longitude, category in CAMPUS_LOCATIONS:
        if name.casefold() not in existing_places:
            db.session.add(CampusLocation(
                name=name,
                description=description,
                latitude=latitude,
                longitude=longitude,
                category=category,
                publication_status='published',
            ))

    db.session.commit()
