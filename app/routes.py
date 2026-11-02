from datetime import datetime
from functools import wraps
from urllib.parse import urlparse
from flask import Blueprint,render_template,request,redirect,url_for,flash,session,abort,jsonify,current_app
from sqlalchemy import or_
from werkzeug.security import safe_join
from .extensions import db,oauth
from .models import *
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
@bp.get('/login')
def login(): return render_template('auth/login.html',oauth_ready=bool(current_app.config['GOOGLE_CLIENT_ID']))
@bp.get('/auth/google')
def google_login():
 if not current_app.config['GOOGLE_CLIENT_ID']: flash('Google OAuth is not configured. Add credentials to .env.','warning'); return redirect(url_for('main.login'))
 google=oauth.create_client('google'); return google.authorize_redirect(url_for('main.google_callback',_external=True))
@bp.get('/auth/google/callback')
def google_callback():
 google=oauth.create_client('google'); token=google.authorize_access_token(); info=google.userinfo(); email=info.get('email','').lower().strip(); domain=email.rsplit('@',1)[-1] if '@' in email else ''
 if not info.get('email_verified') or domain not in current_app.config['ALLOWED_EMAIL_DOMAINS']: flash('Only verified accounts from an approved NSUT email domain may access CampusBeacon.','danger'); return redirect(url_for('main.login'))
 u=User.query.filter_by(email=email).first() or User(email=email,name=info.get('name',email.split('@')[0]),google_sub=info.get('sub'))
 u.google_sub=info.get('sub'); u.name=info.get('name',u.name); u.profile_image_url=info.get('picture'); u.last_login_at=datetime.utcnow(); db.session.add(u); db.session.commit(); session['user_id']=u.id; return redirect(url_for('main.dashboard'))
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
 return render_template('events/list.html',events=query.order_by(Event.starts_at).all(),q=q,category=category,categories=['Hackathon','Workshop','Cultural','Competition','Seminar','Sports','Other'])
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
def clubs(): return render_template('clubs/list.html',clubs=Club.query.filter_by(publication_status='published').all())
@bp.get('/notices')
def notices(): return render_template('notices/list.html',notices=Notice.query.filter_by(publication_status='published').order_by(Notice.created_at.desc()).all())
@bp.get('/campus-map')
def campus_map(): return render_template('map.html',locations=CampusLocation.query.filter_by(publication_status='published').all())
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
