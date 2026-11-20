from datetime import datetime
import hashlib
import re
from functools import wraps
from urllib.parse import urlparse
from flask import Blueprint,render_template,request,redirect,url_for,flash,session,abort,jsonify,current_app
from sqlalchemy import or_
from werkzeug.security import safe_join
from .extensions import db, csrf
from .models import *
from .club_profiles import CATEGORY_PROFILES, ASHWAMEDH_GALLERY
from .notice_sync import sync_if_due, sync_state, SOURCE_URL
bp=Blueprint('main',__name__)
def login_required(f):
 @wraps(f)
 def w(*a,**k):
  if not session.get('user_id'): flash('Please sign in to continue.','info'); return redirect(url_for('main.login',next=request.path))
  return f(*a,**k)
 return w
def roles(*allowed):
 def deco(f):
  @wraps(f)
  def w(*a,**k):
   if not session.get('user_id'): return redirect(url_for('main.login'))
   u=User.query.get(session['user_id'])
   if not u or u.role not in allowed: abort(403)
   return f(*a,**k)
  return w
 return deco
def current(): return User.query.get(session.get('user_id')) if session.get('user_id') else None
@bp.get('/')
def home(): return render_template('landing.html',events=Event.query.filter_by(status='published').order_by(Event.starts_at).limit(3).all(),clubs=Club.query.filter_by(publication_status='published').limit(3).all())
@bp.get('/overview')
def overview():
 now=datetime.utcnow()
 events=Event.query.filter_by(status='published').all()
 live_events=sorted([e for e in events if e.starts_at<=now<=e.ends_at],key=lambda e:e.starts_at)
 upcoming_events=sorted([e for e in events if e.starts_at>now],key=lambda e:e.starts_at)
 order=(Notice.category=='Official NSUT').desc()
 recent_notices=Notice.query.filter_by(publication_status='published').order_by(order,Notice.created_at.desc()).limit(8).all()
 return render_template('overview.html',now=now,live_events=live_events,upcoming_events=upcoming_events[:4],next_event=upcoming_events[0] if upcoming_events else None,recent_notices=recent_notices)
@bp.get('/login')
def login(): return render_template('auth/login.html')
@bp.post('/logout')
def logout(): session.clear(); flash('You have been signed out.','success'); return redirect(url_for('main.home'))
@bp.get('/dashboard')
@login_required
def dashboard():
 u=current(); regs=Registration.query.filter_by(user_id=u.id,status='active').join(Event).order_by(Event.starts_at).limit(5).all(); notes=StickyNote.query.filter_by(user_id=u.id).order_by(StickyNote.is_pinned.desc(),StickyNote.updated_at.desc()).limit(4).all(); notices=Notice.query.filter_by(publication_status='published').order_by(Notice.created_at.desc()).limit(4).all(); return render_template('dashboard.html',regs=regs,notes=notes,notices=notices)
@bp.get('/events')
def events():
 q=request.args.get('q','').strip(); category=request.args.get('category',''); query=Event.query.filter_by(status='published');
 if q: query=query.filter(or_(Event.title.ilike(f'%{q}%'),Event.description.ilike(f'%{q}%')))
 if category: query=query.filter_by(category=category)
 now=datetime.utcnow(); events=query.all()
 past=sorted([e for e in events if e.ends_at<now],key=lambda e:e.starts_at,reverse=True)
 live=sorted([e for e in events if e.starts_at<=now<=e.ends_at],key=lambda e:e.starts_at)
 upcoming=sorted([e for e in events if e.starts_at>now],key=lambda e:e.starts_at)
 return render_template('events/list.html',past_events=past,live_events=live,upcoming_events=upcoming,now=now,q=q,category=category,categories=['Hackathon','Workshop','Cultural','Competition','Seminar','Sports','Other'])

@bp.post('/events/new')
def create_event():
 title=request.form.get('title','').strip()
 description=request.form.get('description','').strip()
 category=request.form.get('category','').strip()
 venue=request.form.get('venue','').strip()
 starts_raw=request.form.get('starts_at','').strip()
 ends_raw=request.form.get('ends_at','').strip()
 errors=[]
 for value,label,limit in ((title,'Event name',180),(description,'Description',None),(category,'Category',60),(venue,'Venue',180)):
  if not value: errors.append(f'{label} is required.')
  elif limit and len(value)>limit: errors.append(f'{label} must be {limit} characters or fewer.')
 try: starts_at=datetime.fromisoformat(starts_raw) if starts_raw else None
 except ValueError: starts_at=None
 try: ends_at=datetime.fromisoformat(ends_raw) if ends_raw else None
 except ValueError: ends_at=None
 if not starts_at: errors.append('Start time must be a valid date and time.')
 if not ends_at: errors.append('End time must be a valid date and time.')
 if starts_at and ends_at and ends_at<=starts_at: errors.append('End time must be after the start time.')
 if errors:
  for message in errors: flash(message,'danger')
  return redirect(url_for('main.events'))
 base_slug=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-') or 'event'
 slug=base_slug
 suffix=2
 while Event.query.filter_by(slug=slug).first():
  slug=f'{base_slug}-{suffix}'
  suffix+=1
 try:
  organizer=User.query.filter_by(email='community-submissions@example.invalid').first()
  if not organizer:
   organizer=User(email='community-submissions@example.invalid',name='CampusBeacon Community',role='organizer')
   db.session.add(organizer)
   db.session.flush()
  event=Event(title=title,slug=slug,description=description,category=category,venue=venue,starts_at=starts_at,ends_at=ends_at,organizer_id=organizer.id,status='published')
  db.session.add(event)
  db.session.commit()
 except Exception:
  db.session.rollback()
  current_app.logger.exception('Unable to save a public event submission')
  flash('The event could not be saved. Please try again.','danger')
  return redirect(url_for('main.events'))
 flash('Event added and shared with everyone.','success')
 return redirect(url_for('main.events'))

@bp.get('/registrations')
def registrations(): return render_template('registrations.html')

@bp.get('/api/registrations')
def api_guest_registrations():
 key_hash=_guest_registration_key_hash()
 if not key_hash: return jsonify({'error':'A valid browser registration key is required.'}),400
 rows=(GuestRegistration.query.join(Event).filter(GuestRegistration.key_hash==key_hash,GuestRegistration.status=='active',Event.status=='published').order_by(Event.starts_at).all())
 return jsonify({'registrations':[{'id':r.event.id,'title':r.event.title,'category':r.event.category,'venue':r.event.venue,'startsAt':r.event.starts_at.isoformat(),'endsAt':r.event.ends_at.isoformat(),'registeredAt':r.registered_at.isoformat()} for r in rows]})

@bp.post('/api/events/<int:event_id>/registrations')
@csrf.exempt
def api_register_guest(event_id):
 key_hash=_guest_registration_key_hash()
 if not key_hash: return jsonify({'error':'A valid browser registration key is required.'}),400
 e=Event.query.get_or_404(event_id); now=datetime.utcnow()
 if e.status!='published' or e.starts_at<=now or (e.registration_deadline and e.registration_deadline<now):
  return jsonify({'error':'Registration is closed for this event.'}),409
 row=GuestRegistration.query.filter_by(event_id=e.id,key_hash=key_hash).first()
 if row and row.status=='active': return jsonify({'message':'Already registered.'}),200
 if e.capacity:
  user_count=Registration.query.filter_by(event_id=e.id,status='active').count()
  guest_count=GuestRegistration.query.filter_by(event_id=e.id,status='active').count()
  if user_count+guest_count>=e.capacity: return jsonify({'error':'This event is full.'}),409
 if row:
  row.status='active'; row.registered_at=now; row.cancelled_at=None
 else:
  row=GuestRegistration(event_id=e.id,key_hash=key_hash,status='active',registered_at=now)
  db.session.add(row)
 db.session.commit()
 return jsonify({'message':'Registration saved.','registration':{'id':e.id,'title':e.title,'category':e.category,'venue':e.venue,'startsAt':e.starts_at.isoformat(),'endsAt':e.ends_at.isoformat(),'registeredAt':row.registered_at.isoformat()}}),201

@bp.delete('/api/events/<int:event_id>/registrations')
@csrf.exempt
def api_cancel_guest_registration(event_id):
 key_hash=_guest_registration_key_hash()
 if not key_hash: return jsonify({'error':'A valid browser registration key is required.'}),400
 row=GuestRegistration.query.filter_by(event_id=event_id,key_hash=key_hash,status='active').first()
 if not row: return jsonify({'error':'Registration not found.'}),404
 row.status='cancelled'; row.cancelled_at=datetime.utcnow(); db.session.commit()
 return jsonify({'message':'Registration removed.'})

def _guest_registration_key_hash():
 raw=request.headers.get('X-CampusBeacon-Registration-Key','').strip().lower()
 if len(raw)!=64 or any(char not in '0123456789abcdef' for char in raw): return None
 return hashlib.sha256(raw.encode('ascii')).hexdigest()

@bp.get('/events/<int:event_id>')
def event_detail(event_id):
 e=Event.query.get_or_404(event_id); u=current(); reg=Registration.query.filter_by(user_id=u.id,event_id=e.id,status='active').first() if u else None; fav=Favorite.query.filter_by(user_id=u.id,event_id=e.id).first() if u else None; return render_template('events/detail.html',event=e,registration=reg,favorite=fav)
@bp.post('/events/<int:event_id>/register')
@login_required
def register(event_id):
 e=Event.query.get_or_404(event_id); u=current();
 if e.status!='published' or (e.registration_deadline and e.registration_deadline<datetime.utcnow()): flash('Registration is closed for this event.','warning')
 elif e.capacity and Registration.query.filter_by(event_id=e.id,status='active').count()>=e.capacity: flash('This event is full.','warning')
 elif Registration.query.filter_by(event_id=e.id,user_id=u.id).first(): flash('You are already registered.','info')
 else:
  db.session.add(Registration(user_id=u.id,event_id=e.id)); db.session.add(Notification(user_id=u.id,title='Registration confirmed',message=f'You are registered for {e.title}.')); db.session.commit(); flash('Registration confirmed.','success')
 return redirect(url_for('main.event_detail',event_id=event_id))
@bp.post('/events/<int:event_id>/favorite')
@login_required
def favorite(event_id):
 if not Favorite.query.filter_by(user_id=session['user_id'],event_id=event_id).first(): db.session.add(Favorite(user_id=session['user_id'],event_id=event_id)); db.session.commit(); flash('Event saved.','success')
 return redirect(request.referrer or url_for('main.events'))
@bp.get('/clubs')
def clubs(): return render_template('clubs/list.html',clubs=Club.query.filter_by(publication_status='published').order_by(Club.category,Club.name).all())
@bp.get('/clubs/<slug>')
def club_detail(slug):
 c=Club.query.filter_by(slug=slug,publication_status='published').first_or_404()
 return render_template('clubs/detail.html',club=c,profile=CATEGORY_PROFILES.get(c.category,CATEGORY_PROFILES['Recreational']),gallery=ASHWAMEDH_GALLERY if slug=='ashwamedh-the-dramatics-society' else [])
@bp.get('/notices')
def notices():
 sync_if_due(current_app._get_current_object())
 order=(Notice.category=='Official NSUT').desc()
 rows=Notice.query.filter_by(publication_status='published').order_by(order,Notice.created_at.desc()).all()
 return render_template('notices/list.html',notices=rows,sync=sync_state())
@bp.get('/api/notices')
def notices_api():
 sync_if_due(current_app._get_current_object())
 order=(Notice.category=='Official NSUT').desc()
 rows=Notice.query.filter_by(publication_status='published').order_by(order,Notice.created_at.desc()).all()
 return jsonify({
  'notices':[{'id':n.id,'title':n.title,'content':n.content,'category':n.category,'issuer':n.issuer,'created_at':n.created_at.strftime('%d %b %Y'),'deadline':n.deadline.strftime('%d %b') if n.deadline else None,'source_url':SOURCE_URL if n.source_url and n.source_url.startswith(SOURCE_URL) else None} for n in rows],
  'last_synced':sync_state()['last_synced'].strftime('%d %b %Y, %I:%M:%S %p') if sync_state()['last_synced'] else None,
  'sync_error':bool(sync_state()['last_error']),
 })
@bp.get('/campus-map')
def campus_map():
 locations=CampusLocation.query.filter_by(publication_status='published').order_by(CampusLocation.name).all()
 events=Event.query.filter_by(status='published').all()
 map_places=[{'id':p.id,'name':p.name,'description':p.description,'category':p.category,'latitude':p.latitude,'longitude':p.longitude} for p in locations]
 map_events=[{'title':e.title,'venue':e.venue,'startsAt':e.starts_at.isoformat(),'endsAt':e.ends_at.isoformat()} for e in events]
 return render_template('map.html',locations=locations,map_places=map_places,map_events=map_events)
@bp.route('/notes',methods=['GET','POST'])
@login_required
def notes():
 if request.method=='POST':
  title=request.form.get('title','').strip(); content=request.form.get('content','').strip()
  if not title or not content: flash('Title and content are required.','danger')
  else: db.session.add(StickyNote(user_id=session['user_id'],title=title,content=content,is_pinned=bool(request.form.get('is_pinned')))); db.session.commit(); flash('Note saved.','success')
 return render_template('notes.html',notes=StickyNote.query.filter_by(user_id=session['user_id']).order_by(StickyNote.is_pinned.desc(),StickyNote.updated_at.desc()).all())
@bp.post('/notes/<int:note_id>/delete')
@login_required
def delete_note(note_id):
 n=StickyNote.query.filter_by(id=note_id,user_id=session['user_id']).first_or_404(); db.session.delete(n); db.session.commit(); flash('Note deleted.','success'); return redirect(url_for('main.notes'))
@bp.get('/admin')
@roles('admin')
def admin(): return render_template('admin/index.html',users=User.query.count(),events=Event.query.count(),clubs=Club.query.count(),notices=Notice.query.count(),registrations=Registration.query.count())
@bp.app_errorhandler(404)
def not_found(e): return render_template('errors/404.html'),404
@bp.app_errorhandler(403)
def forbidden(e): return render_template('errors/403.html'),403
