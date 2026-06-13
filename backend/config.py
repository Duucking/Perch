import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'data', 'perch.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
SCAN_DIRS = []
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
THUMBNAIL_SIZE = (1080, 1080)
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
]