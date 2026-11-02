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
