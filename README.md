# Wedding Photo Upload 💍✨

A beautiful, modern wedding photo sharing application built with Flask. This application allows wedding guests to easily upload and share their photos from your special day.

## Features

- 📸 **Beautiful UI**: Modern, wedding-themed design with elegant animations
- 🖼️ **Photo Gallery**: Responsive grid layout with lightbox modal viewer
- 📱 **Mobile Friendly**: Fully responsive design works on all devices
- 🔐 **Secure Uploads**: Optional upload codes and admin controls
- 🖼️ **Automatic Thumbnails**: Auto-generated WebP thumbnails for fast loading
- 📏 **Image Auto-rotation**: Automatically corrects image orientation using EXIF data
- 📱 **QR Code**: Auto-generated QR codes for easy sharing
- 🗑️ **Admin Panel**: Delete inappropriate photos with admin token
- 🌐 **API Endpoints**: RESTful API for external integrations

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python run.py
   ```

3. **Open your browser:**
   Visit `http://localhost:8000`

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Flask Configuration
FLASK_SECRET=your-secret-key-here
DEBUG=False

# File Upload Configuration
MAX_CONTENT_LENGTH_MB=32
THUMB_SIZE=640
TITLE="Your Wedding Photos"
UPLOAD_CODE=your-upload-code
PUBLIC_BASE_URL=https://your-domain.com

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Directory Structure

```
wedding-photo-upload/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # Route blueprints
│   ├── templates/       # HTML templates
│   ├── utils/           # Utility functions
│   └── static/
│       ├── css/         # Stylesheets
│       └── js/          # JavaScript
├── uploads/             # Uploaded photos
│   └── thumbs/         # Generated thumbnails
├── config.py           # Configuration classes
├── run.py             # Application entry point
└── requirements.txt   # Dependencies
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run in development mode
python run.py development
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Run tests
pytest
```

## Production Deployment

### Using Gunicorn

```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

### Using Docker (Example)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py", "production"]
```

## API Endpoints

- `GET /api/list` - List all uploaded photos
- `GET /api/stats` - Get basic statistics
- `GET /uploads/<filename>` - Serve uploaded files
- `GET /thumbs/<filename>` - Serve thumbnail files
- `GET /qr.png` - Generate QR code

## Security Features

- **File Type Validation**: Only allows image files
- **File Size Limits**: Configurable maximum file sizes
- **Upload Codes**: Optional codes required for uploads
- **Admin Controls**: Secure admin panel for photo management
- **CSRF Protection**: Built-in Flask security features

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ for your special day
