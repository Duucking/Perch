import os
import sqlite3
import threading
import hashlib
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from PIL import Image

from config import DATABASE, UPLOAD_FOLDER, THUMBNAIL_SIZE, ALLOWED_EXTENSIONS, BASE_DIR

app = Flask(__name__)
CORS(app)

scan_lock = threading.Lock()


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
            created_at TEXT DEFAULT (datetime('now')),
            scanned_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_photos_filepath ON photos(filepath);
    """)
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


@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.get_json(silent=True) or {}
    directory = data.get('directory', '')
    if not directory or not os.path.isdir(directory):
        return jsonify({'error': 'Invalid directory'}), 400

    with scan_lock:
        added, errors = scan_directory(directory)

    return jsonify({'added': len(added), 'errors': errors})


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
    return jsonify({
        'id': row['id'],
        'filename': row['filename'],
        'filepath': row['filepath'],
        'thumbnail_path': row['thumbnail_path'],
        'file_size': row['file_size'],
        'width': row['width'],
        'height': row['height'],
        'scanned_at': row['scanned_at'],
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


@app.route('/api/suggest-dirs', methods=['GET'])
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


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)