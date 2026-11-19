"""Read-only synchronization with NSUT's public notices listing."""

from datetime import datetime, timedelta
from hashlib import sha256
from html.parser import HTMLParser
import os
import re
from threading import Event, Lock, Thread
from urllib.request import Request, urlopen

from .extensions import db
from .models import Notice

SOURCE_URL = 'https://www.imsnsit.org/imsnsit/notifications.php'
SYNC_INTERVAL = timedelta(seconds=45)
REQUEST_TIMEOUT = 15

_sync_lock = Lock()
_state_lock = Lock()
_stop_event = Event()
_started_pids = set()
_last_attempt = None
_last_success = None
_last_error = None
_last_added = 0


class _NoticePageParser(HTMLParser):
    """Extract date, linked subject and publisher from the portal's table rows."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.cell = None
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.row = {'cells': [], 'links': []}
        elif self.row is not None and tag == 'td':
            self.cell = []
            self.row['cells'].append(self.cell)
        elif self.row is not None and tag == 'a':
            self.anchor = {'href': attrs.get('href', ''), 'text': []}

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
        if self.anchor is not None:
            self.anchor['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.anchor is not None:
            link = self.anchor
            link['text'] = ' '.join(' '.join(link['text']).split())
            self.row['links'].append(link)
            self.anchor = None
        elif tag == 'td':
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None
            self.cell = None


def read_public_notices():
    request = Request(SOURCE_URL, headers={
        'User-Agent': 'CampusBeacon/1.0 (+public NSUT notices reader)',
        'Accept': 'text/html',
    })
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        if response.status != 200:
            raise RuntimeError(f'NSUT notice page returned HTTP {response.status}')
        html = response.read(3_000_001)
    if len(html) > 3_000_000:
        raise RuntimeError('NSUT notice page was larger than expected')

    parser = _NoticePageParser()
    parser.feed(html.decode('utf-8', 'replace'))
    notices = []
    for row in parser.rows:
        cells = [' '.join(cell).strip() for cell in row['cells']]
        if len(cells) < 2:
            continue
        date_match = re.search(r'\b(\d{2}-\d{2}-\d{4})\b', cells[0])
        subject_link = next((link for link in row['links'] if link['text']), None)
        if not date_match or not subject_link:
            continue
        publisher_match = re.search(r'Published\s+By:\s*(.*)', ' '.join(cells[1:]), re.I)
        issuer = ' '.join(publisher_match.group(1).split()) if publisher_match else 'NSUT'
        try:
            posted = datetime.strptime(date_match.group(1), '%d-%m-%Y')
        except ValueError:
            continue
        title = subject_link['text'][:180]
        key = sha256(f'{posted:%Y-%m-%d}|{title}|{issuer}'.encode('utf-8')).hexdigest()[:24]
        notices.append({
            'key': key,
            'title': title,
            'issuer': issuer[:140],
            'posted': posted,
        })
    if not notices:
        raise RuntimeError('No notice rows were found on the NSUT page')
    return notices


def sync_once(app, force=True):
    """Import new portal rows and refresh existing imported rows; never delete data."""
    global _last_attempt, _last_success, _last_error, _last_added
    with _sync_lock:
        attempted = datetime.utcnow()
        if not force:
            with _state_lock:
                if _last_attempt and attempted - _last_attempt < SYNC_INTERVAL:
                    return 0
        with _state_lock:
            _last_attempt = attempted
            _last_error = None
        try:
            rows = read_public_notices()
            added = 0
            with app.app_context():
                for row in rows:
                    source_key = f"{SOURCE_URL}#campusbeacon-{row['key']}"
                    notice = Notice.query.filter_by(source_url=source_key).first()
                    if notice is None:
                        notice = Notice(
                            title=row['title'],
                            content='Published on the official NSUT notices and circulars portal.',
                            category='Official NSUT',
                            issuer=row['issuer'],
                            source_url=source_key,
                            publication_status='published',
                            created_at=row['posted'],
                        )
                        db.session.add(notice)
                        added += 1
                    else:
                        notice.title = row['title']
                        notice.issuer = row['issuer']
                        notice.created_at = row['posted']
                db.session.commit()
            with _state_lock:
                _last_success = datetime.utcnow()
                _last_error = None
                _last_added = added
            return added
        except Exception as exc:
            with app.app_context():
                db.session.rollback()
                db.session.remove()
            app.logger.warning('NSUT notice sync failed: %s', exc)
            with _state_lock:
                _last_error = str(exc)
                _last_added = 0
            return 0


def sync_if_due(app):
    if app.testing or not app.config.get('NOTICE_SYNC_ENABLED', True):
        return 0
    return sync_once(app, force=False)


def sync_state():
    with _state_lock:
        return {
            'last_synced': _last_success,
            'last_error': _last_error,
            'last_added': _last_added,
            'source_url': SOURCE_URL,
        }


def _worker(app):
    while not _stop_event.is_set():
        sync_if_due(app)
        _stop_event.wait(SYNC_INTERVAL.total_seconds())


def start_notice_sync(app):
    """Start one polling worker per server process; skip test app instances."""
    if app.testing or not app.config.get('NOTICE_SYNC_ENABLED', True):
        return
    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return
    pid = os.getpid()
    with _state_lock:
        if pid in _started_pids:
            return
        _started_pids.add(pid)
    thread = Thread(target=_worker, args=(app,), name='nsut-notice-sync', daemon=True)
    thread.start()
