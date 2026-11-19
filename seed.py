from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User, Event, Club, Notice, CampusLocation
from app.location_data import CAMPUS_LOCATIONS

app = create_app()
NSUT_LIST = 'https://www.nsut.ac.in/en/for-students/existing-students/co-curricular-activities-societies-and-clubs'
CLUBS = [
    ('Ashwamedh - The Dramatics Society', 'ashwamedh-the-dramatics-society', 'A campus theatre society for acting, stage performance, and dramatic storytelling.', 'Recreational', NSUT_LIST),
    ('Crescendo - The Music Society', 'crescendo-the-music-society', 'A student music society for sharing and performing music across styles.', 'Recreational', 'https://linktr.ee/crescendo.nsut'),
    ('Junoon - The Photography Club', 'junoon-the-photography-club', 'A photography and videography community for visual storytelling and sharing student work.', 'Recreational', 'https://www.junoonnsut.com/'),
    ('Mirage - The Western Dance Crew', 'mirage-the-western-dance-crew', 'NSUT’s western dance crew, bringing students together to train and perform.', 'Recreational', NSUT_LIST),
    ('Choreography Society', 'choreography-society', 'A dance society for students interested in choreography, movement, and group performances.', 'Recreational', NSUT_LIST),
    ('SPIC MACAY - NSUT Chapter', 'spic-macay-nsut-chapter', 'The NSUT chapter of SPIC MACAY, a national movement introducing students to Indian classical arts and culture.', 'Recreational', 'https://spicmacay.org/'),
    ('CSI NSUT', 'csi-nsut', 'The NSUT chapter of the Computer Society of India, for students interested in computing and technology.', 'Technical', 'https://csi-india.org/'),
    ('IEEE NSUT', 'ieee-nsut', 'A student technical society with IEEE-affiliated chapters and engineering groups.', 'Technical', 'https://www.ieeensut.com/'),
    ('Control Delvers', 'control-delvers', 'A technical society focused on control systems and related engineering concepts.', 'Technical', NSUT_LIST),
    ('Enactus NSUT', 'enactus-nsut', 'A student-led organization using entrepreneurial action and technology to address social challenges and support sustainable development.', 'Non-Technical', 'https://www.enactus.in/'),
    ('Finance & Economics Society', 'finance-economics-society', 'A community for students interested in finance, economics, markets, and related ideas.', 'Non-Technical', NSUT_LIST),
    ('The Management & Consulting Club', 'management-consulting-club', 'A student community for exploring management, consulting, business problem-solving, and case discussions.', 'Non-Technical', NSUT_LIST),
    ('E-Cell NSUT', 'e-cell-nsut', 'The university’s entrepreneurship cell, supporting student interest in entrepreneurship and startup culture.', 'Non-Technical', 'https://ecellnsut.com/'),
    ('TEDxNSIT', 'tedxnsit', 'The NSUT TEDx community, organizing independently run TED-style talks and sharing ideas.', 'Non-Technical', 'https://www.ted.com/tedx'),
    ('The Alliance', 'the-alliance', 'NSUT’s student newspaper, covering campus life and student perspectives.', 'Literary', 'https://alliancensut.com/'),
    ('Crosslinks', 'crosslinks', 'NSUT’s media management and student public relations society, sharing student-facing information.', 'Literary', 'https://linktr.ee/crosslinks.nsut'),
    ('Debating Society of NSUT', 'debating-society-of-nsut', 'A society for students to practice debate, public speaking, and reasoned discussion.', 'Literary', NSUT_LIST),
    ('The Magzine', 'the-magzine', 'A literary publication community for students interested in writing and editorial work.', 'Literary', NSUT_LIST),
    ('The NSUT Quiz Club', 'nsut-quiz-club', 'A club for students who enjoy quizzes, general knowledge, and knowledge-based competitions.', 'Literary', NSUT_LIST),
    ('Flashback - The Yearbook Society', 'flashback-yearbook-society', 'The yearbook society documenting student memories and campus life.', 'Literary', NSUT_LIST),
    ('The Page Turners', 'the-page-turners', 'A reading community for students who enjoy books and sharing literary interests.', 'Literary', NSUT_LIST),
    ('Reminisce - NSUT’s Alumni Magazine', 'reminisce-alumni-magazine', 'NSUT’s alumni magazine, sharing stories connected to the university’s alumni community.', 'Literary', NSUT_LIST),
    ('NSUT Solar Car Concept', 'nsut-solar-car-concept', 'An automotive engineering team listed by NSUT, focused on solar-powered vehicle concepts.', 'Automotive', NSUT_LIST),
    ('Bullet Hawk Racing', 'bullet-hawk-racing', 'A student racing team working on automotive design and competition projects.', 'Automotive', NSUT_LIST),
    ('NSUT Motorsports', 'nsut-motorsports', 'An automotive team listed by NSUT, building student experience in vehicle design and motorsports.', 'Automotive', NSUT_LIST),
    ('NSUT Moon Buggy', 'nsut-moon-buggy', 'A student engineering team focused on designing and building a moon-buggy style rover.', 'Automotive', NSUT_LIST),
    ('NSUT Rotaract Club', 'nsut-rotaract-club', 'A campus service club connected to Rotaract, bringing students together for community-oriented service.', 'Community Service', 'https://rotaract.org/'),
    ('Neighborhood Project', 'neighborhood-project', 'A community service initiative listed by NSUT, focused on outreach and neighborhood engagement.', 'Community Service', NSUT_LIST),
    ('Teach for India - NSUT Chapter', 'teach-for-india-nsut-chapter', 'The NSUT chapter associated with Teach For India’s education-focused movement.', 'Community Service', 'https://www.teachforindia.org/'),
    ('CollegeSpace', 'collegespace', 'A student website listed on NSUT’s societies and clubs page.', 'Campus Websites', NSUT_LIST),
    ('NSITOnline', 'nsitonline', 'A student website listed on NSUT’s societies and clubs page.', 'Campus Websites', NSUT_LIST),
]

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
