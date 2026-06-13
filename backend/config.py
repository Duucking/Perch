import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'data', 'perch.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
SCAN_DIRS = []
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
THUMBNAIL_SIZE = (400, 400)