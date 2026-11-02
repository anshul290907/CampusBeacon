from flask import Flask, session
from .config import Config
from .extensions import db,migrate,csrf,oauth

def create_app(test_config=None):
    app=Flask(__name__,instance_relative_config=True); app.config.from_object(Config)
    if test_config: app.config.update(test_config)
    db.init_app(app); migrate.init_app(app,db); csrf.init_app(app); oauth.init_app(app)
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(name='google', client_id=app.config['GOOGLE_CLIENT_ID'], client_secret=app.config['GOOGLE_CLIENT_SECRET'], server_metadata_url='https://accounts.google.com/.well-known/openid-configuration', client_kwargs={'scope':'openid email profile'})
    from .routes import bp; app.register_blueprint(bp)
    with app.app_context(): db.create_all()
    @app.context_processor
    def inject_user():
        from .models import User,Notification
        user=User.query.get(session.get('user_id')) if session.get('user_id') else None
        unread=Notification.query.filter_by(user_id=user.id,read_at=None).count() if user else 0
        return {'current_user':user,'unread_count':unread}
    return app
