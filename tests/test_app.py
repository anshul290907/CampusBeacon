import pytest
from app import create_app
from app.extensions import db
@pytest.fixture
def client(tmp_path):
 app=create_app({'TESTING':True,'SECRET_KEY':'test','SQLALCHEMY_DATABASE_URI':f'sqlite:///{tmp_path}/test.db','WTF_CSRF_ENABLED':False})
 with app.test_client() as c:
  with app.app_context(): db.drop_all(); db.create_all()
  yield c
def test_home(client):
 r=client.get('/'); assert r.status_code==200; assert b'CampusBeacon' in r.data
def test_events(client):
 r=client.get('/events?q=missing'); assert r.status_code==200; assert b'No events match' in r.data
def test_protected_dashboard(client):
 r=client.get('/dashboard'); assert r.status_code==302; assert '/login' in r.location
def test_login_is_unavailable_without_a_provider(client):
 r=client.get('/login'); assert r.status_code==200; assert b'Campus life starts here' in r.data; assert b'Explore events' in r.data; assert b'Google' not in r.data
def test_google_oauth_routes_are_removed(client):
 assert client.get('/auth/google').status_code==404
 assert client.get('/auth/google/callback').status_code==404

def test_any_visitor_can_create_an_event_saved_to_database(client):
 from app.models import Event, User
 page=client.get('/events')
 assert page.status_code==200 and b'/events/new' in page.data
 response=client.post('/events/new',data={
  'title':'Spring Demo Day','description':'Student project showcase.','category':'Workshop','venue':'Main Auditorium',
  'starts_at':'2030-04-10T10:00','ends_at':'2030-04-10T12:00'
 })
 assert response.status_code==302 and response.location.endswith('/events')
 with client.application.app_context():
  event=Event.query.filter_by(slug='spring-demo-day').one()
  assert event.status=='published'
  assert event.organizer.name=='CampusBeacon Community'
  assert User.query.filter_by(email='community-submissions@example.invalid').count()==1
 with client.session_transaction() as session: assert any('Event added and shared' in item[1] for item in session['_flashes'])

def test_public_event_creation_rejects_invalid_dates(client):
 from app.models import Event
 response=client.post('/events/new',data={
  'title':'Bad Event','description':'Invalid event.','category':'Other','venue':'Hall',
  'starts_at':'2030-04-10T12:00','ends_at':'2030-04-10T11:00'
 })
 assert response.status_code==302
 with client.application.app_context(): assert Event.query.count()==0
 with client.session_transaction() as session:
  assert any('End time must be after the start time.' in item[1] for item in session['_flashes'])

def _create_future_event(client, capacity=None):
 from datetime import datetime, timedelta
 from app.models import Event, User
 with client.application.app_context():
  organizer=User(email='organizer@example.edu',name='Organizer')
  db.session.add(organizer); db.session.flush()
  event=Event(title='Database event',slug='database-event',description='Test event',category='Workshop',venue='Main Auditorium',starts_at=datetime.utcnow()+timedelta(days=2),ends_at=datetime.utcnow()+timedelta(days=2,hours=2),organizer_id=organizer.id,capacity=capacity,status='published')
  db.session.add(event); db.session.commit(); return event.id

def test_guest_registration_is_saved_in_database_and_can_be_removed(client):
 from app.models import GuestRegistration
 event_id=_create_future_event(client)
 headers={'X-CampusBeacon-Registration-Key':'a'*64}
 created=client.post(f'/api/events/{event_id}/registrations',headers=headers,json={})
 assert created.status_code==201
 listed=client.get('/api/registrations',headers=headers)
 assert listed.status_code==200
 assert [item['id'] for item in listed.json['registrations']]==[event_id]
 with client.application.app_context(): assert GuestRegistration.query.filter_by(event_id=event_id,status='active').count()==1
 removed=client.delete(f'/api/events/{event_id}/registrations',headers=headers)
 assert removed.status_code==200
 assert client.get('/api/registrations',headers=headers).json['registrations']==[]

def test_guest_registration_requires_a_valid_browser_key(client):
 event_id=_create_future_event(client)
 assert client.post(f'/api/events/{event_id}/registrations',json={}).status_code==400
