
import os
import certifi
from flask import Flask, session
from .config import Config
from .extensions import db, migrate, csrf


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # TiDB Cloud requires TLS; keep these MySQL-specific options off SQLite
    # engines used by tests and local development.
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('mysql+pymysql://'):
        ca_path = os.getenv('TIDB_CA') or certifi.where()
        engine_options = dict(app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}))
        connect_args = dict(engine_options.get('connect_args', {}))
        connect_args.update({
            'ssl_verify_cert': True,
            'ssl_verify_identity': True,
            'ssl_ca': ca_path,
        })
        engine_options['connect_args'] = connect_args
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

    # Create instance folder for SQLite database
    if os.getenv('VERCEL') != '1':
        os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    # Register routes
    from .routes import bp
    app.register_blueprint(bp)

    # Create database tables
    with app.app_context():
        db.create_all()
        from .catalog import ensure_catalog_data
        ensure_catalog_data()

    # Inject current user into templates
    @app.context_processor
    def inject_user():
        from .models import User, Notification

        user = User.query.get(session.get('user_id')) if session.get('user_id') else None

        unread = Notification.query.filter_by(
            user_id=user.id,
            read_at=None
        ).count() if user else 0

        return {
            'current_user': user,
            'unread_count': unread
        }

    from .notice_sync import start_notice_sync
    start_notice_sync(app)

    return app
