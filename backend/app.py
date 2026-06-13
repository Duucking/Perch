import os
import sqlite3
import threading
import hashlib
import secrets
import math
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, send_file, g
from flask_cors import CORS
from PIL import Image, ExifTags
from PIL.TiffImagePlugin import IFDRational
from werkzeug.security import generate_password_hash, check_password_hash

from config import DATABASE, UPLOAD_FOLDER, THUMBNAIL_SIZE, ALLOWED_EXTENSIONS, ALLOWED_ORIGINS, ALLOW_ALL_ORIGINS, BASE_DIR

app = Flask(__name__)
cors_origins = '*' if ALLOW_ALL_ORIGINS else ALLOWED_ORIGINS
CORS(app, origins=cors_origins, supports_credentials=True, expose_headers=['Content-Disposition'])

app.config['SECRET_KEY'] = secrets.token_hex(32)

scan_lock = threading.Lock()

TOKENS = {}


@app.before_request
def security_check():
    if request.method == 'OPTIONS':
        return None

    is_api = request.path.startswith('/api/')

    if not ALLOW_ALL_ORIGINS:
        source = request.headers.get('Origin', '') or request.headers.get('Referer', '') or ''
        if source:
            host = request.headers.get('Host', '')
            if not any(source.startswith(o) for o in ALLOWED_ORIGINS) and source != f'http://{host}' and source != f'https://{host}':
                return jsonify({'error': 'Forbidden'}), 403

    if is_api:
        xrw = request.headers.get('X-Requested-With', '')
        if xrw and xrw != 'XMLHttpRequest':
            return jsonify({'error': 'Invalid request'}), 400
    return None


def validate_request():
    return None


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL UNIQUE,
            thumbnail_path TEXT,
            file_size INTEGER,
            width INTEGER,
            height INTEGER,
            file_hash TEXT,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            scanned_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_photos_filepath ON photos(filepath);

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'user'
        );
    """)

    existing = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt']
    if existing == 0:
        conn.execute("""
            INSERT INTO users (username, password_hash, display_name, role)
            VALUES (?, ?, ?, ?)
        """, ('admin', generate_password_hash('admin123'), '管理员', 'admin'))

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    try:
        conn.execute("ALTER TABLE photos ADD COLUMN description TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def get_file_hash(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def scan_directory(directory):
    if not os.path.isdir(directory):
        return [], []

    added = []
    errors = []
    conn = get_db()
    existing = {row['filepath'] for row in conn.execute("SELECT filepath FROM photos").fetchall()}

    for fpath in Path(directory).rglob('*'):
        if fpath.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        fpath_str = str(fpath.resolve())
        if fpath_str in existing:
            continue
        try:
            with Image.open(fpath_str) as img:
                w, h = img.size
            fsize = fpath.stat().st_size
            fhash = get_file_hash(fpath_str)

            thumb_dir = os.path.join(UPLOAD_FOLDER, 'thumbnails')
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_name = fhash[:16] + fpath.suffix
            thumb_path = os.path.join(thumb_dir, thumb_name)

            if not os.path.exists(thumb_path):
                with Image.open(fpath_str) as img:
                    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
                    img.save(thumb_path, optimize=True)

            conn.execute("""
                INSERT INTO photos (filename, filepath, thumbnail_path, file_size, width, height, file_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fpath.name, fpath_str, thumb_path, fsize, w, h, fhash))
            added.append(fpath.name)
        except Exception as e:
            errors.append({'file': fpath_str, 'error': str(e)})

    conn.commit()
    conn.close()
    return added, errors


def regenerate_thumbnails():
    conn = get_db()
    rows = conn.execute("SELECT * FROM photos").fetchall()
    thumb_dir = os.path.join(UPLOAD_FOLDER, 'thumbnails')
    os.makedirs(thumb_dir, exist_ok=True)
    for row in rows:
        thumb_path = row['thumbnail_path']
        if thumb_path and os.path.exists(thumb_path):
            continue
        fpath = row['filepath']
        if not os.path.exists(fpath):
            continue
        try:
            fhash = get_file_hash(fpath)
            suffix = Path(fpath).suffix
            thumb_name = fhash[:16] + suffix
            thumb_path = os.path.join(thumb_dir, thumb_name)
            with Image.open(fpath) as img:
                img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
                img.save(thumb_path, optimize=True)
            conn.execute("UPDATE photos SET thumbnail_path = ? WHERE id = ?",
                         (thumb_path, row['id']))
        except Exception:
            pass
    conn.commit()
    conn.close()


# ─── Auth Helpers ──────────────────────────────────────────────

def require_admin(fn):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
        info = TOKENS.get(token)
        if not info:
            return jsonify({'error': 'Unauthorized'}), 401
        if info.get('expires') < datetime.now():
            TOKENS.pop(token, None)
            return jsonify({'error': 'Token expired'}), 401
        if info.get('role') != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        g.current_user = info
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# ─── Auth Routes ───────────────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '')
    password = data.get('password', '')

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': '用户名或密码错误'}), 401

    token = secrets.token_hex(32)
    TOKENS[token] = {
        'user_id': user['id'],
        'username': user['username'],
        'display_name': user['display_name'],
        'role': user['role'],
        'expires': datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }

    return jsonify({
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'role': user['role']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
    TOKENS.pop(token, None)
    return jsonify({'ok': True})


@app.route('/api/auth/me', methods=['GET'])
def api_auth_me():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
    info = TOKENS.get(token)
    if not info or info.get('expires') < datetime.now():
        TOKENS.pop(token, None)
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'id': info['user_id'],
        'username': info['username'],
        'display_name': info['display_name'],
        'role': info['role']
    })


@app.route('/api/auth/profile', methods=['PUT'])
@require_admin
def api_update_profile():
    data = request.get_json(silent=True) or {}
    display_name = data.get('display_name', '').strip()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (g.current_user['user_id'],)).fetchone()

    if old_password and new_password:
        if not check_password_hash(user['password_hash'], old_password):
            conn.close()
            return jsonify({'error': '原密码错误'}), 400
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                     (generate_password_hash(new_password), user['id']))

    if display_name:
        conn.execute("UPDATE users SET display_name = ? WHERE id = ?",
                     (display_name, user['id']))

    conn.commit()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user['id'],)).fetchone()
    conn.close()

    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'display_name': user['display_name'],
        'role': user['role']
    })


# ─── EXIF Helper ───────────────────────────────────────────────

EXIF_TAGS = {
    33434: 'ExposureTime',
    33437: 'FNumber',
    34855: 'ISOSpeedRatings',
    36867: 'DateTimeOriginal',
    37377: 'ShutterSpeedValue',
    37378: 'ApertureValue',
}


def to_float(v):
    if isinstance(v, IFDRational):
        return float(v)
    if isinstance(v, tuple) and len(v) == 2:
        return v[0] / v[1]
    if isinstance(v, (int, float)):
        return float(v)
    return None


def extract_exif(filepath):
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if not exif_data:
            return None
        info = {}
        for tag_id, name in EXIF_TAGS.items():
            raw = exif_data.get(tag_id)
            if raw is None:
                continue

            if name == 'FNumber':
                val = to_float(raw)
                if val:
                    info['aperture'] = f"f/{val:.1f}"

            elif name == 'ExposureTime':
                val = to_float(raw)
                if val:
                    if val >= 1:
                        info['shutter'] = f"{val:.0f}s"
                    else:
                        denom = round(1 / val)
                        info['shutter'] = f"1/{denom}s"

            elif name == 'ISOSpeedRatings':
                info['iso'] = str(raw)

            elif name == 'DateTimeOriginal':
                info['datetime'] = str(raw)

            elif name == 'ShutterSpeedValue':
                if 'shutter' not in info:
                    val = to_float(raw)
                    if val:
                        t = math.exp(val * math.log(2))
                        if t >= 1:
                            info['shutter'] = f"{t:.0f}s"
                        else:
                            denom = round(1 / t)
                            info['shutter'] = f"1/{denom}s"

            elif name == 'ApertureValue':
                if 'aperture' not in info:
                    val = to_float(raw)
                    if val:
                        f = math.exp(val * math.log(math.sqrt(2)))
                        info['aperture'] = f"f/{f:.1f}"

        if not info:
            return None
        return {
            'aperture': info.get('aperture'),
            'shutter': info.get('shutter'),
            'iso': info.get('iso'),
            'datetime': info.get('datetime'),
        }
    except Exception:
        return None


# ─── Public Routes ─────────────────────────────────────────────

@app.route('/api/photos', methods=['GET'])
def api_photos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '', type=str)
    sort = request.args.get('sort', 'scanned_at', type=str)
    order = request.args.get('order', 'desc', type=str)

    conn = get_db()
    query = "SELECT * FROM photos"
    params = []
    if search:
        query += " WHERE filename LIKE ?"
        params.append(f'%{search}%')

    valid_sorts = {'scanned_at', 'filename', 'file_size', 'created_at'}
    if sort not in valid_sorts:
        sort = 'scanned_at'
    order = 'DESC' if order.upper() == 'DESC' else 'ASC'
    query += f" ORDER BY {sort} {order}"

    count_query = query.replace("SELECT *", "SELECT COUNT(*) as cnt")
    total = conn.execute(count_query, params).fetchone()['cnt']

    offset = (page - 1) * per_page
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()

    photos = []
    for row in rows:
        photos.append({
            'id': row['id'],
            'filename': row['filename'],
            'filepath': row['filepath'],
            'thumbnail_path': row['thumbnail_path'],
            'file_size': row['file_size'],
            'width': row['width'],
            'height': row['height'],
            'scanned_at': row['scanned_at'],
            'description': row['description'] or '',
        })

    return jsonify({
        'photos': photos,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@app.route('/api/photos/<int:photo_id>', methods=['GET'])
def api_photo_detail(photo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    exif = extract_exif(row['filepath'])
    return jsonify({
        'id': row['id'],
        'filename': row['filename'],
        'filepath': row['filepath'],
        'thumbnail_path': row['thumbnail_path'],
        'file_size': row['file_size'],
        'width': row['width'],
        'height': row['height'],
        'scanned_at': row['scanned_at'],
        'description': row['description'] or '',
        'exif': exif,
    })


@app.route('/api/thumbnails/<path:filename>')
def api_thumbnail(filename):
    thumb_dir = os.path.join(UPLOAD_FOLDER, 'thumbnails')
    return send_from_directory(thumb_dir, filename)


@app.route('/api/download/<int:photo_id>')
def api_download(photo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return send_file(row['filepath'], as_attachment=True, download_name=row['filename'])


@app.route('/api/photo-file/<int:photo_id>')
def api_photo_file(photo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return send_file(row['filepath'])


@app.route('/api/stats', methods=['GET'])
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as cnt FROM photos").fetchone()['cnt']
    total_size = conn.execute("SELECT COALESCE(SUM(file_size), 0) as sz FROM photos").fetchone()['sz']
    latest = conn.execute("SELECT scanned_at FROM photos ORDER BY scanned_at DESC LIMIT 1").fetchone()
    conn.close()
    return jsonify({
        'total_photos': total,
        'total_size': total_size,
        'last_scan': latest['scanned_at'] if latest else None
    })


# ─── Settings ──────────────────────────────────────────────────

@app.route('/api/settings/<key>', methods=['GET'])
def api_get_setting(key):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return jsonify({'key': key, 'value': row['value'] if row else ''})


@app.route('/api/settings/<key>', methods=['PUT'])
@require_admin
def api_set_setting(key):
    data = request.get_json(silent=True) or {}
    value = data.get('value', '')
    conn = get_db()
    conn.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# ─── Admin-only Routes ─────────────────────────────────────────

@app.route('/api/scan', methods=['POST'])
@require_admin
def api_scan():
    data = request.get_json(silent=True) or {}
    directory = data.get('directory', '')
    if not directory or not os.path.isdir(directory):
        return jsonify({'error': 'Invalid directory'}), 400

    with scan_lock:
        added, errors = scan_directory(directory)

    return jsonify({'added': len(added), 'errors': errors})


@app.route('/api/suggest-dirs', methods=['GET'])
@require_admin
def api_suggest_dirs():
    path = request.args.get('path', '', type=str)
    if not path:
        drives = [d for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f'{d}:\\')]
        return jsonify({'drives': [f'{d}:\\' for d in drives]})
    try:
        items = []
        for entry in os.scandir(path):
            if entry.is_dir():
                items.append(entry.path)
        return jsonify({'directories': sorted(items)})
    except PermissionError:
        return jsonify({'error': 'Permission denied', 'directories': []})
    except FileNotFoundError:
        return jsonify({'error': 'Not found', 'directories': []})


@app.route('/api/photos/<int:photo_id>', methods=['PUT'])
@require_admin
def api_update_photo(photo_id):
    data = request.get_json(silent=True) or {}
    description = data.get('description', '').strip()

    conn = get_db()
    row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    conn.execute("UPDATE photos SET description = ? WHERE id = ?", (description, photo_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'description': description})


@app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
@require_admin
def api_delete_photo(photo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404

    if row['thumbnail_path'] and os.path.exists(row['thumbnail_path']):
        try:
            os.remove(row['thumbnail_path'])
        except OSError:
            pass

    conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


# ─── Serve frontend (standalone mode) ──────────────────────────

FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'dist')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    if not os.path.isdir(FRONTEND_DIR):
        return jsonify({'error': 'Frontend not built'}), 404
    file_path = os.path.join(FRONTEND_DIR, path or 'index.html')
    if os.path.isfile(file_path):
        return send_file(file_path)
    return send_file(os.path.join(FRONTEND_DIR, 'index.html'))


if __name__ == '__main__':
    init_db()
    with app.app_context():
        regenerate_thumbnails()
    app.run(host='0.0.0.0', port=5000, debug=True)