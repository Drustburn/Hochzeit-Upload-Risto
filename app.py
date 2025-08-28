#!/usr/bin/env python3
import os
import io
import secrets
import pathlib
import sqlite3
from datetime import datetime
from typing import Iterable

from flask import (
    Flask, request, redirect, url_for, send_from_directory, abort,
    render_template_string, flash, jsonify, make_response
)
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags
import qrcode
from jinja2 import ChoiceLoader, DictLoader

# -------------------- Konfiguration --------------------
BASE_DIR = pathlib.Path(__file__).resolve().parent
UPLOAD_DIR = pathlib.Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
THUMB_DIR = UPLOAD_DIR / "thumbs"
DB_PATH = pathlib.Path(os.getenv("DB_PATH", BASE_DIR / "uploads.db"))

ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "32")) * 1024 * 1024
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")  # z.B. https://fotos.deine-hochzeit.de
UPLOAD_CODE = os.getenv("UPLOAD_CODE")          # optionaler Code fürs Upload-Formular
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", secrets.token_urlsafe(16))
THUMB_SIZE = int(os.getenv("THUMB_SIZE", "640"))  # Kantenlänge Thumbnail
TITLE = os.getenv("TITLE", "Hochzeitsfotos hochladen")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", secrets.token_urlsafe(16))
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- DB --------------------
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            filename TEXT UNIQUE,
            orig_name TEXT,
            uploader_ip TEXT,
            created_at TEXT
        )
        """)
init_db()

# -------------------- Utils --------------------
def allowed(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXT

def autorotate(img: Image.Image) -> Image.Image:
    try:
        exif = img._getexif()
        if exif:
            orient_key = next(k for k, v in ExifTags.TAGS.items() if v == "Orientation")
            orientation = exif.get(orient_key)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img

def make_thumb(src: pathlib.Path, dst: pathlib.Path):
    try:
        with Image.open(src) as im:
            im = autorotate(im)
            im.thumbnail((THUMB_SIZE, THUMB_SIZE))
            im.save(dst, "WEBP", quality=85, method=6)
    except Exception:
        dst.write_bytes(src.read_bytes())

def save_image(file_storage, uploader_ip: str) -> str:
    orig = secure_filename(file_storage.filename or "upload")
    ext = orig.rsplit(".", 1)[-1].lower()
    if not allowed(orig):
        raise ValueError("Dateityp nicht erlaubt")

    name = f"{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}.{ext}"
    path = UPLOAD_DIR / name
    file_storage.save(path)

    thumb = THUMB_DIR / (path.stem + ".webp")
    make_thumb(path, thumb)

    with db() as con:
        con.execute(
            "INSERT OR IGNORE INTO media(filename, orig_name, uploader_ip, created_at) VALUES(?,?,?,?)",
            (name, orig, uploader_ip, datetime.utcnow().isoformat())
        )
    return name

# -------------------- Templates --------------------
BASE_TMPL = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;600;700&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --wedding-primary: #d4af37;
      --wedding-secondary: #f8f4e8;
      --wedding-accent: #8b4513;
      --wedding-text: #2c2c2c;
      --wedding-light: #ffffff;
      --wedding-shadow: rgba(212, 175, 55, 0.2);
      --gradient-overlay: linear-gradient(135deg, rgba(248, 244, 232, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
    }

    * {
      box-sizing: border-box;
    }

    body {
      font-family: 'Poppins', sans-serif;
      margin: 0;
      padding: 0;
      background: var(--wedding-secondary);
      background-image: 
        url('/static/backgroundBild.JPG'),
        url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="hearts" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M10,6 C12,4 15,4 17,6 C19,4 22,4 24,6 C22,8 17,13 12,18 C7,13 2,8 0,6 C2,4 5,4 7,6" fill="%23d4af37" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23hearts)"/></svg>'),
        linear-gradient(45deg, #f8f4e8 25%, transparent 25%),
        linear-gradient(-45deg, #f8f4e8 25%, transparent 25%);
      background-size: cover, 200px 200px, 60px 60px, 60px 60px;
      background-attachment: fixed, scroll, scroll, scroll;
      background-repeat: no-repeat, repeat, repeat, repeat;
      color: var(--wedding-text);
      line-height: 1.6;
      min-height: 100vh;
      position: relative;
    }

    body::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: var(--gradient-overlay);
      z-index: -1;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      position: relative;
      z-index: 1;
    }

    header {
      background: var(--wedding-light);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      box-shadow: 0 10px 30px var(--wedding-shadow);
      margin-bottom: 30px;
      padding: 25px 30px;
      border: 1px solid rgba(212, 175, 55, 0.3);
    }

    .header-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 20px;
    }

    .logo {
      font-family: 'Dancing Script', cursive;
      font-size: 2.5rem;
      font-weight: 700;
      color: var(--wedding-primary);
      margin: 0;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    .nav-buttons {
      display: flex;
      gap: 15px;
      align-items: center;
    }

    .btn {
      background: var(--wedding-primary);
      color: var(--wedding-light);
      border: none;
      padding: 12px 24px;
      border-radius: 25px;
      font-family: 'Poppins', sans-serif;
      font-weight: 500;
      font-size: 0.95rem;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-block;
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }

    .btn:hover {
      background: var(--wedding-accent);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
      color: var(--wedding-light);
      text-decoration: none;
    }

    .btn-secondary {
      background: transparent;
      color: var(--wedding-primary);
      border: 2px solid var(--wedding-primary);
    }

    .btn-secondary:hover {
      background: var(--wedding-primary);
      color: var(--wedding-light);
    }

    .qr-container {
      position: relative;
    }

    .qr-toggle {
      background: var(--wedding-secondary);
      color: var(--wedding-primary);
      border: 2px solid var(--wedding-primary);
      padding: 8px 16px;
      border-radius: 20px;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 500;
    }

    .qr-dropdown {
      position: absolute;
      top: 100%;
      right: 0;
      background: var(--wedding-light);
      border-radius: 15px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.2);
      margin-top: 10px;
      min-width: 200px;
      text-align: center;
      display: none;
      z-index: 1000;
    }

    .qr-dropdown.show {
      display: block;
    }

    .qr-code {
      border-radius: 10px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
      margin-bottom: 10px;
    }

    main {
      background: var(--wedding-light);
      border-radius: 20px;
      padding: 40px;
      box-shadow: 0 10px 30px var(--wedding-shadow);
      margin-bottom: 30px;
      border: 1px solid rgba(212, 175, 55, 0.3);
    }

    .page-title {
      font-family: 'Dancing Script', cursive;
      font-size: 2.2rem;
      color: var(--wedding-primary);
      text-align: center;
      margin-bottom: 30px;
      text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }

    .modal {
      display: none;
      position: fixed;
      z-index: 10000;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.95);
      backdrop-filter: blur(10px);
    }

    .modal.show {
      display: flex;
      align-items: center;
      justify-content: center;
      animation: modalFadeIn 0.3s ease;
    }

    @keyframes modalFadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .modal-content {
      position: relative;
      max-width: 95vw;
      max-height: 95vh;
      margin: auto;
      text-align: center;
      animation: modalSlideIn 0.4s ease;
    }

    @keyframes modalSlideIn {
      from { 
        opacity: 0;
        transform: scale(0.8) translateY(20px);
      }
      to { 
        opacity: 1;
        transform: scale(1) translateY(0);
      }
    }

    .modal img {
      max-width: 100%;
      max-height: 85vh;
      object-fit: contain;
      border-radius: 15px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
      transition: transform 0.3s ease;
    }

    .modal-header {
      position: absolute;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      padding: 10px 20px;
      border-radius: 25px;
      color: var(--wedding-text);
      font-weight: 500;
      font-size: 0.9rem;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
      z-index: 1001;
    }

    .modal-nav {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      background: var(--wedding-primary);
      color: var(--wedding-light);
      border: none;
      width: 50px;
      height: 50px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 1.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
      z-index: 1001;
    }

    .modal-nav:hover {
      background: var(--wedding-accent);
      transform: translateY(-50%) scale(1.1);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.6);
    }

    .modal-prev {
      left: 30px;
    }

    .modal-next {
      right: 30px;
    }

    .modal-close {
      position: absolute;
      top: 20px;
      right: 30px;
      background: rgba(255, 255, 255, 0.9);
      color: var(--wedding-text);
      border: none;
      width: 45px;
      height: 45px;
      border-radius: 50%;
      cursor: pointer;
      font-size: 1.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
      z-index: 1001;
    }

    .modal-close:hover {
      background: #dc3545;
      color: white;
      transform: rotate(90deg) scale(1.1);
    }

    .modal-counter {
      position: absolute;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(10px);
      padding: 8px 16px;
      border-radius: 20px;
      color: var(--wedding-text);
      font-size: 0.9rem;
      font-weight: 500;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
      z-index: 1001;
    }

    .modal-download {
      position: absolute;
      bottom: 20px;
      right: 30px;
      background: var(--wedding-primary);
      color: var(--wedding-light);
      border: none;
      padding: 12px 20px;
      border-radius: 25px;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
      z-index: 1001;
    }

    .modal-download:hover {
      background: var(--wedding-accent);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.6);
    }

    @media (max-width: 768px) {
      .modal-header {
        position: fixed;
        top: 10px;
        left: 10px;
        right: 10px;
        transform: none;
        font-size: 0.8rem;
        padding: 8px 15px;
      }

      .modal-close {
        top: 10px;
        right: 10px;
        width: 40px;
        height: 40px;
        font-size: 1.2rem;
      }

      .modal-nav {
        width: 45px;
        height: 45px;
        font-size: 1.2rem;
      }

      .modal-prev {
        left: 15px;
      }

      .modal-next {
        right: 15px;
      }

      .modal-counter {
        bottom: 15px;
        font-size: 0.8rem;
        padding: 6px 12px;
      }

      .modal-download {
        bottom: 15px;
        right: 15px;
        padding: 10px 16px;
        font-size: 0.8rem;
      }
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 25px;
      margin-top: 30px;
    }

    .photo-card {
      background: var(--wedding-light);
      border-radius: 15px;
      overflow: hidden;
      box-shadow: 0 8px 25px rgba(0,0,0,0.1);
      transition: all 0.3s ease;
      border: 1px solid rgba(212, 175, 55, 0.2);
    }

    .photo-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 15px 40px rgba(0,0,0,0.2);
    }

    .photo-card img {
      width: 100%;
      height: 250px;
      object-fit: cover;
      transition: transform 0.3s ease;
    }

    .photo-card:hover img {
      transform: scale(1.05);
    }

    .card-content {
      padding: 20px;
    }

    .photo-date {
      color: var(--wedding-accent);
      font-size: 0.9rem;
      font-weight: 500;
      margin-bottom: 10px;
    }

    .upload-form {
      background: var(--wedding-secondary);
      border-radius: 15px;
      padding: 30px;
      margin: 30px 0;
      border: 2px dashed var(--wedding-primary);
    }

    .form-group {
      margin-bottom: 25px;
    }

    label {
      display: block;
      font-weight: 500;
      color: var(--wedding-text);
      margin-bottom: 8px;
      font-size: 1.1rem;
    }

    input[type="password"], input[type="file"] {
      width: 100%;
      padding: 15px 20px;
      border: 2px solid rgba(212, 175, 55, 0.3);
      border-radius: 10px;
      font-size: 1rem;
      background: var(--wedding-light);
      transition: border-color 0.3s ease;
    }

    input[type="password"]:focus, input[type="file"]:focus {
      outline: none;
      border-color: var(--wedding-primary);
      box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.2);
    }

    .alert {
      background: #fee;
      border: 1px solid #fcc;
      color: #c33;
      padding: 15px 20px;
      border-radius: 10px;
      margin-bottom: 20px;
      font-weight: 500;
    }

    .alert.success {
      background: #efe;
      border-color: #cfc;
      color: #363;
    }

    footer {
      text-align: center;
      color: var(--wedding-accent);
      font-size: 0.9rem;
      padding: 20px;
      background: rgba(255,255,255,0.8);
      border-radius: 15px;
      backdrop-filter: blur(10px);
    }

    .delete-btn {
      background: #dc3545;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.3s ease;
      width: 100%;
      margin-top: 10px;
    }

    .delete-btn:hover {
      background: #c82333;
      transform: translateY(-1px);
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: var(--wedding-accent);
    }

    .empty-state::before {
      content: "💍";
      font-size: 4rem;
      display: block;
      margin-bottom: 20px;
    }

    .file-upload-area {
      border: 3px dashed var(--wedding-primary);
      border-radius: 15px;
      padding: 40px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      background: var(--wedding-light);
      position: relative;
      overflow: hidden;
    }

    .file-upload-area:hover {
      border-color: var(--wedding-accent);
      background: var(--wedding-secondary);
      transform: translateY(-2px);
    }

    .file-upload-area.dragover {
      border-color: var(--wedding-accent);
      background: rgba(212, 175, 55, 0.1);
      border-style: solid;
    }

    .upload-icon {
      font-size: 3rem;
      margin-bottom: 15px;
      opacity: 0.8;
    }

    .upload-text {
      color: var(--wedding-text);
      font-size: 1.1rem;
    }

    .file-list {
      margin-top: 20px;
    }

    .file-item {
      background: var(--wedding-light);
      border: 1px solid rgba(212, 175, 55, 0.3);
      border-radius: 10px;
      padding: 12px 15px;
      margin: 8px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: all 0.2s ease;
    }

    .file-item:hover {
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    .file-info {
      display: flex;
      align-items: center;
      flex: 1;
    }

    .file-icon {
      margin-right: 10px;
      font-size: 1.2rem;
    }

    .file-details {
      flex: 1;
    }

    .file-name {
      font-weight: 500;
      color: var(--wedding-text);
      margin-bottom: 2px;
    }

    .file-size {
      font-size: 0.8rem;
      color: var(--wedding-accent);
    }

    .file-remove {
      background: #dc3545;
      color: white;
      border: none;
      border-radius: 50%;
      width: 24px;
      height: 24px;
      cursor: pointer;
      font-size: 0.8rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
    }

    .file-remove:hover {
      background: #c82333;
      transform: scale(1.1);
    }

    .progress-bar {
      width: 100%;
      height: 4px;
      background: rgba(212, 175, 55, 0.2);
      border-radius: 2px;
      margin-top: 8px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--wedding-primary);
      border-radius: 2px;
      transition: width 0.3s ease;
      width: 0%;
    }

    @media (max-width: 768px) {
      .container {
        padding: 15px;
      }

      .header-content {
        flex-direction: column;
        text-align: center;
      }

      .logo {
        font-size: 2rem;
      }

      main {
        padding: 25px 20px;
      }

      .grid {
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 20px;
      }

      .nav-buttons {
        justify-content: center;
        flex-wrap: wrap;
      }
    }

    @media (max-width: 480px) {
      .grid {
        grid-template-columns: 1fr;
      }
      
      .btn {
        padding: 10px 20px;
        font-size: 0.9rem;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-content">
        <h1 class="logo">{{ title }}</h1>
        <div class="nav-buttons">
          <a href="{{ url_for('index') }}" class="btn btn-secondary">📸 Galerie</a>
          <a href="{{ url_for('upload') }}" class="btn">💕 Fotos hochladen</a>
          <div class="qr-container">
            <button class="qr-toggle" onclick="toggleQR()">QR Code</button>
            <div class="qr-dropdown" id="qrDropdown">
              <img class="qr-code" alt="QR Code" src="{{ url_for('qr_png') }}">
              <div style="font-size: 0.8rem; color: var(--wedding-accent);">
                {{ public_url or request.url_root.rstrip('/') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
    
    <main>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="alert {% if 'hochgeladen' in messages[0] or 'Datei(en)' in messages[0] %}success{% endif %}">
            {{ messages[0] }}
          </div>
        {% endif %}
      {% endwith %}
      {% block content %}{% endblock %}
    </main>
    
    <footer>
      <p>💝 Max {{ max_mb }} MB pro Datei • Erlaubt: {{ allowed|join(', ') | upper }} 💝</p>
      <p style="margin-top: 10px; font-size: 0.8rem; opacity: 0.8;">
        Teile deine schönsten Momente unserer Hochzeit ✨
      </p>
    </footer>
  </div>

  <!-- Image Modal -->
  <div id="imageModal" class="modal">
    <div class="modal-content">
      <div class="modal-header">
        <span id="modalImageName"></span>
      </div>
      <button class="modal-close" id="modalClose">&times;</button>
      <button class="modal-nav modal-prev" id="modalPrev">&#8249;</button>
      <button class="modal-nav modal-next" id="modalNext">&#8250;</button>
      <img id="modalImage" src="" alt="">
      <div class="modal-counter">
        <span id="modalCounter"></span>
      </div>
      <a class="modal-download" id="modalDownload" download>
        📥 Download
      </a>
    </div>
  </div>

  <script>
    function toggleQR() {
      const dropdown = document.getElementById('qrDropdown');
      dropdown.classList.toggle('show');
    }

    // Close QR dropdown when clicking outside
    document.addEventListener('click', function(event) {
      const qrContainer = document.querySelector('.qr-container');
      const dropdown = document.getElementById('qrDropdown');
      
      if (!qrContainer.contains(event.target)) {
        dropdown.classList.remove('show');
      }
    });

    // Image Modal Functionality
    let currentImageIndex = 0;
    let allImages = [];

    function initImageModal() {
      const modal = document.getElementById('imageModal');
      const modalImage = document.getElementById('modalImage');
      const modalClose = document.getElementById('modalClose');
      const modalPrev = document.getElementById('modalPrev');
      const modalNext = document.getElementById('modalNext');
      const modalCounter = document.getElementById('modalCounter');
      const modalImageName = document.getElementById('modalImageName');
      const modalDownload = document.getElementById('modalDownload');

      // Collect all images from the gallery
      const imageCards = document.querySelectorAll('.photo-card');
      allImages = Array.from(imageCards).map(card => {
        const img = card.querySelector('img');
        const link = card.querySelector('a');
        const date = card.querySelector('.photo-date');
        return {
          thumb: img.src,
          full: link.href,
          alt: img.alt,
          name: img.alt,
          date: date ? date.textContent : ''
        };
      });

      // Add click handlers to all photo cards
      imageCards.forEach((card, index) => {
        const link = card.querySelector('a');
        if (link) {
          link.addEventListener('click', (e) => {
            e.preventDefault();
            openModal(index);
          });
        }
      });

      function openModal(index) {
        currentImageIndex = index;
        updateModalContent();
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus management for accessibility
        modalClose.focus();
      }

      function closeModal() {
        modal.classList.remove('show');
        document.body.style.overflow = '';
      }

      function updateModalContent() {
        if (allImages.length === 0) return;
        
        const image = allImages[currentImageIndex];
        modalImage.src = image.full;
        modalImage.alt = image.alt;
        modalImageName.textContent = image.name;
        modalCounter.textContent = `${currentImageIndex + 1} von ${allImages.length}`;
        modalDownload.href = image.full;
        modalDownload.download = image.name;

        // Update navigation button states
        modalPrev.style.opacity = currentImageIndex === 0 ? '0.5' : '1';
        modalNext.style.opacity = currentImageIndex === allImages.length - 1 ? '0.5' : '1';
      }

      function showPrevImage() {
        if (currentImageIndex > 0) {
          currentImageIndex--;
          updateModalContent();
        }
      }

      function showNextImage() {
        if (currentImageIndex < allImages.length - 1) {
          currentImageIndex++;
          updateModalContent();
        }
      }

      // Event listeners
      modalClose.addEventListener('click', closeModal);
      modalPrev.addEventListener('click', showPrevImage);
      modalNext.addEventListener('click', showNextImage);

      // Close modal when clicking outside the image
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeModal();
        }
      });

      // Keyboard navigation
      document.addEventListener('keydown', (e) => {
        if (modal.classList.contains('show')) {
          switch(e.key) {
            case 'Escape':
              closeModal();
              break;
            case 'ArrowLeft':
              showPrevImage();
              break;
            case 'ArrowRight':
              showNextImage();
              break;
          }
        }
      });

      // Touch/swipe support for mobile
      let touchStartX = 0;
      let touchEndX = 0;

      modal.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      });

      modal.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
      });

      function handleSwipe() {
        const swipeThreshold = 50;
        const swipeDistance = touchEndX - touchStartX;
        
        if (Math.abs(swipeDistance) > swipeThreshold) {
          if (swipeDistance > 0) {
            showPrevImage(); // Swipe right = previous image
          } else {
            showNextImage(); // Swipe left = next image
          }
        }
      }

      // Preload adjacent images for smoother experience
      function preloadImages() {
        const preloadNext = currentImageIndex < allImages.length - 1 ? currentImageIndex + 1 : null;
        const preloadPrev = currentImageIndex > 0 ? currentImageIndex - 1 : null;
        
        [preloadNext, preloadPrev].forEach(index => {
          if (index !== null) {
            const img = new Image();
            img.src = allImages[index].full;
          }
        });
      }

      // Add image load event listener for preloading
      modalImage.addEventListener('load', preloadImages);
    }

    // File upload functionality
    document.addEventListener('DOMContentLoaded', function() {
      // Initialize image modal
      initImageModal();
      
      const uploadArea = document.querySelector('.file-upload-area');
      const fileInput = document.getElementById('fileInput');
      const fileList = document.getElementById('fileList');
      const uploadForm = document.querySelector('form[enctype="multipart/form-data"]');
      
      let selectedFiles = [];
      const maxFileSize = {{ max_mb }} * 1024 * 1024;
      const allowedTypes = [{% for ext in allowed %}'{{ ext }}'{% if not loop.last %}, {% endif %}{% endfor %}];
      
      // File input change handler
      if (fileInput) {
        fileInput.addEventListener('change', function(e) {
          handleFiles(e.target.files);
        });
      }
      
      // Drag and drop handlers
      if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
          e.preventDefault();
          this.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
          e.preventDefault();
          this.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', function(e) {
          e.preventDefault();
          this.classList.remove('dragover');
          handleFiles(e.dataTransfer.files);
        });
      }
      
      // Handle selected files
      function handleFiles(files) {
        for (let file of files) {
          if (validateFile(file)) {
            if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
              selectedFiles.push(file);
            }
          }
        }
        updateFileList();
        updateFileInput();
      }
      
      // Validate file
      function validateFile(file) {
        const fileExt = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExt)) {
          showMessage('Dateityp nicht erlaubt: ' + file.name, 'error');
          return false;
        }
        
        if (file.size > maxFileSize) {
          showMessage('Datei zu groß: ' + file.name + ' (' + formatFileSize(file.size) + ')', 'error');
          return false;
        }
        
        return true;
      }
      
      // Update file list display
      function updateFileList() {
        if (!fileList) return;
        
        fileList.innerHTML = '';
        selectedFiles.forEach((file, index) => {
          const fileItem = document.createElement('div');
          fileItem.className = 'file-item';
          fileItem.innerHTML = `
            <div class="file-info">
              <div class="file-icon">🖼️</div>
              <div class="file-details">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
              </div>
            </div>
            <button type="button" class="file-remove" onclick="removeFile(${index})" title="Datei entfernen">×</button>
          `;
          fileList.appendChild(fileItem);
        });
      }
      
      // Remove file from selection
      window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFileList();
        updateFileInput();
      };
      
      // Update hidden file input with selected files
      function updateFileInput() {
        if (!fileInput) return;
        
        const dt = new DataTransfer();
        selectedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
      }
      
      // Format file size
      function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
      }
      
      // Show message
      function showMessage(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert' + (type === 'error' ? '' : ' success');
        alertDiv.textContent = message;
        
        const main = document.querySelector('main');
        if (main) {
          main.insertBefore(alertDiv, main.firstChild);
          setTimeout(() => alertDiv.remove(), 5000);
        }
      }
      
      // Form submission handler
      if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
          if (selectedFiles.length === 0) {
            e.preventDefault();
            showMessage('Bitte wählt mindestens eine Datei aus.', 'error');
            return;
          }
          
          const submitBtn = this.querySelector('button[type="submit"]');
          if (submitBtn) {
            submitBtn.innerHTML = '💕 Wird hochgeladen...';
            submitBtn.disabled = true;
            
            // Add progress bar
            const progressDiv = document.createElement('div');
            progressDiv.innerHTML = `
              <div class="progress-bar">
                <div class="progress-fill"></div>
              </div>
              <div style="text-align: center; margin-top: 10px; font-size: 0.9rem; color: var(--wedding-accent);">
                Eure Fotos werden hochgeladen... ✨
              </div>
            `;
            submitBtn.parentNode.appendChild(progressDiv);
            
            // Simulate progress (since we can't track real progress easily)
            let progress = 0;
            const progressBar = progressDiv.querySelector('.progress-fill');
            const interval = setInterval(() => {
              progress += Math.random() * 20;
              if (progress > 90) progress = 90;
              progressBar.style.width = progress + '%';
            }, 200);
            
            // Clean up on form completion (this won't run due to redirect, but good practice)
            setTimeout(() => clearInterval(interval), 30000);
          }
        });
      }
    });
  </script>
</body>
</html>
"""

INDEX_TMPL = """
{% extends "_base" %}
{% block content %}
<h2 class="page-title">✨ Unsere Hochzeitsfotos ✨</h2>

{% if items %}
  <div class="grid">
    {% for f in items %}
      <div class="photo-card">
        <a href="{{ url_for('file_raw', filename=f['filename']) }}" target="_blank" title="Original in voller Größe öffnen">
          <img loading="lazy" src="{{ url_for('thumb_raw', thumb=f['thumb']) }}" alt="{{ f['orig_name'] or f['filename'] }}">
        </a>
        <div class="card-content">
          <div class="photo-date">📅 {{ f['created_at'] }}</div>
          {% if admin %}
          <form method="post" action="{{ url_for('delete_file') }}" onsubmit="return confirm('Möchtest du dieses Foto wirklich löschen? 🗑️');" style="margin: 0;">
            <input type="hidden" name="filename" value="{{ f['filename'] }}">
            <input type="hidden" name="admin_token" value="{{ admin }}">
            <button class="delete-btn" type="submit">🗑️ Löschen</button>
          </form>
          {% endif %}
        </div>
      </div>
    {% endfor %}
  </div>
{% else %}
  <div class="empty-state">
    <h3 style="font-family: 'Dancing Script', cursive; font-size: 1.8rem; margin: 20px 0;">
      Noch keine Fotos hochgeladen
    </h3>
    <p style="margin-bottom: 30px;">
      Seid die ersten, die eure schönsten Momente teilt! 📸✨
    </p>
    <a href="{{ url_for('upload') }}" class="btn" style="font-size: 1.1rem; padding: 15px 30px;">
      💕 Erstes Foto hochladen
    </a>
  </div>
{% endif %}
{% endblock %}
"""

UPLOAD_TMPL = """
{% extends "_base" %}
{% block content %}
<h2 class="page-title">💕 Hochzeitsfotos hochladen</h2>

<div style="text-align: center; margin-bottom: 40px;">
  <p style="font-size: 1.1rem; color: var(--wedding-accent); margin-bottom: 15px;">
    Teilt eure schönsten Momente unserer Hochzeit mit allen! ✨
  </p>
  <p style="font-size: 0.95rem; color: var(--wedding-text); opacity: 0.8;">
    QR Code scannen oder Link teilen, dann eure Lieblingsfotos auswählen und hochladen 📸
  </p>
</div>

<div class="upload-form">
  <form method="post" enctype="multipart/form-data">
    {% if upload_code_required %}
      <div class="form-group">
        <label>🔐 Hochzeitscode eingeben</label>
        <input name="code" type="password" inputmode="numeric" placeholder="z.B. 2025" required style="text-align: center; font-size: 1.2rem; letter-spacing: 2px;">
      </div>
    {% endif %}
    
    <div class="form-group">
      <label>📷 Eure Fotos auswählen</label>
      <div class="file-upload-area" onclick="document.getElementById('fileInput').click();">
        <input type="file" id="fileInput" name="files" accept="image/*" multiple required style="display: none;">
        <div class="upload-icon">📸</div>
        <div class="upload-text">
          <strong>Klickt hier oder zieht eure Fotos hierher</strong>
          <div style="margin-top: 8px; font-size: 0.9rem; opacity: 0.8;">
            Mehrere Dateien gleichzeitig möglich
          </div>
        </div>
      </div>
      <div id="fileList" class="file-list"></div>
      <div style="margin-top: 15px; font-size: 0.9rem; color: var(--wedding-accent); text-align: center;">
        💡 Max. {{ max_mb }} MB pro Datei • {{ allowed|join(', ')|upper }}
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
      <button type="submit" class="btn" style="font-size: 1.2rem; padding: 18px 40px; box-shadow: 0 8px 25px rgba(212, 175, 55, 0.4);">
        💝 Fotos hochladen
      </button>
    </div>
  </form>
</div>

<div style="background: rgba(212, 175, 55, 0.1); border-radius: 15px; padding: 25px; margin-top: 30px; text-align: center;">
  <h4 style="font-family: 'Dancing Script', cursive; color: var(--wedding-primary); margin-bottom: 15px; font-size: 1.5rem;">
    💌 Liebe Hochzeitsgäste
  </h4>
  <p style="color: var(--wedding-text); line-height: 1.7; margin: 0;">
    Danke, dass ihr unseren besonderen Tag mit uns geteilt habt! Jedes Foto erzählt eine Geschichte 
    und hilft uns, diese wundervollen Erinnerungen für immer zu bewahren. ❤️
  </p>
</div>
{% endblock %}
"""

# Base-Template als virtuelles Jinja-Template registrieren
app.jinja_loader = ChoiceLoader([
    app.jinja_loader,
    DictLoader({"_base": BASE_TMPL})
])

# -------------------- Routes --------------------
@app.route("/")
def index():
    admin = request.args.get("admin")
    items = []
    with db() as con:
        for row in con.execute("SELECT filename, orig_name, created_at FROM media ORDER BY id DESC"):
            items.append({
                "filename": row["filename"],
                "thumb": pathlib.Path(row["filename"]).stem + ".webp",
                "orig_name": row["orig_name"],
                "created_at": row["created_at"].replace("T", " ")[:19],
            })
    return render_template_string(
        INDEX_TMPL,
        title=TITLE, items=items, allowed=sorted(ALLOWED_EXT),
        max_mb=MAX_CONTENT_LENGTH // (1024*1024), admin=admin,
        public_url=PUBLIC_BASE_URL
    )

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if UPLOAD_CODE and request.form.get("code") != UPLOAD_CODE:
            flash("Falscher Code.")
            return redirect(url_for("upload"))

        files = request.files.getlist("files")
        if not files:
            flash("Keine Dateien ausgewählt.")
            return redirect(url_for("upload"))

        saved, errors = 0, 0
        error_details = []
        
        for f in files:
            if not f or not getattr(f, "filename", ""):
                continue
                
            filename = f.filename
            if not allowed(filename):
                errors += 1
                ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "?"
                error_details.append(f"'{filename}': Dateityp .{ext} nicht erlaubt")
                continue
                
            # Check file size
            if f.content_length and f.content_length > MAX_CONTENT_LENGTH:
                errors += 1
                size_mb = f.content_length / (1024 * 1024)
                error_details.append(f"'{filename}': Datei zu groß ({size_mb:.1f} MB)")
                continue
                
            try:
                save_image(f, request.remote_addr or "")
                saved += 1
            except ValueError as e:
                errors += 1
                error_details.append(f"'{filename}': {str(e)}")
            except Exception as e:
                errors += 1
                error_details.append(f"'{filename}': Upload fehlgeschlagen")

        # Generate detailed feedback message
        if saved == 0 and errors > 0:
            if len(error_details) <= 3:
                flash("Upload fehlgeschlagen: " + "; ".join(error_details))
            else:
                flash(f"Upload fehlgeschlagen: {errors} Datei(en) konnten nicht hochgeladen werden.")
        elif errors == 0:
            flash(f"🎉 Erfolgreich! {saved} Foto{'s' if saved > 1 else ''} hochgeladen.")
        else:
            success_msg = f"✅ {saved} Foto{'s' if saved > 1 else ''} hochgeladen"
            if len(error_details) <= 2:
                flash(f"{success_msg}. ❌ Fehler: {'; '.join(error_details)}")
            else:
                flash(f"{success_msg}. ❌ {errors} Datei(en) hatten Probleme.")
        return redirect(url_for("index"))

    return render_template_string(
        UPLOAD_TMPL,
        title=TITLE, allowed=sorted(ALLOWED_EXT),
        max_mb=MAX_CONTENT_LENGTH // (1024*1024),
        upload_code_required=bool(UPLOAD_CODE),
        public_url=PUBLIC_BASE_URL
    )

@app.route("/uploads/<path:filename>")
def file_raw(filename):
    return send_from_directory(UPLOAD_DIR, filename, conditional=True)

@app.route("/thumbs/<path:thumb>")
def thumb_raw(thumb):
    return send_from_directory(THUMB_DIR, thumb, conditional=True)

@app.route("/qr.png")
def qr_png():
    base = PUBLIC_BASE_URL.rstrip("/") if PUBLIC_BASE_URL else request.url_root.rstrip("/")
    target = base + url_for("upload")
    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers["Content-Type"] = "image/png"
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/api/list")
def api_list():
    with db() as con:
        rows = con.execute("SELECT filename, orig_name, created_at FROM media ORDER BY id DESC").fetchall()
    return jsonify([
        {
            "filename": r["filename"],
            "url": url_for("file_raw", filename=r["filename"], _external=True),
            "thumb": url_for("thumb_raw", thumb=pathlib.Path(r["filename"]).stem + ".webp", _external=True),
            "orig_name": r["orig_name"],
            "created_at": r["created_at"]
        } for r in rows
    ])

@app.route("/admin/delete", methods=["POST"])
def delete_file():
    token = request.form.get("admin_token", "")
    if token != ADMIN_TOKEN:
        abort(403)
    filename = request.form.get("filename", "")
    if not filename:
        abort(400)
    f = UPLOAD_DIR / filename
    t = THUMB_DIR / (pathlib.Path(filename).stem + ".webp")
    with db() as con:
        con.execute("DELETE FROM media WHERE filename = ?", (filename,))
    if f.exists():
        f.unlink()
    if t.exists():
        t.unlink()
    return redirect(url_for("index", admin=ADMIN_TOKEN))

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR / "static", filename)

@app.route("/favicon.ico")
def favicon():
    return ("", 204)

@app.route("/healthz")
def healthz():
    return "ok"

# -------------------- Start --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Admin-Token: {ADMIN_TOKEN}")
    app.run(host=host, port=port, debug=False)