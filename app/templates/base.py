BASE_TEMPLATE = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>{{ config.TITLE }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;600;700&family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
  <div class="container">
    <header>
      <div class="header-content">
        <h1 class="logo">{{ config.TITLE }}</h1>
        <div class="nav-buttons">
          <a href="{{ url_for('main.index') }}" class="btn btn-secondary">📸 Galerie</a>
          <a href="{{ url_for('main.upload') }}" class="btn">💕 Fotos hochladen</a>
          <div class="qr-container">
            <button class="qr-toggle" onclick="toggleQR()">QR Code</button>
            <div class="qr-dropdown" id="qrDropdown">
              <img class="qr-code" alt="QR Code" src="{{ url_for('main.qr_png') }}">
              <div style="font-size: 0.8rem; color: var(--wedding-accent);">
                {{ config.PUBLIC_BASE_URL or request.url_root.rstrip('/') }}
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
      <p>💝 Max {{ (config.MAX_CONTENT_LENGTH / (1024*1024))|int }} MB pro Datei • Erlaubt: {{ config.ALLOWED_EXTENSIONS|list|sort|join(', ')|upper }} 💝</p>
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

  <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
"""