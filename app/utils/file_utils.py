import secrets
import pathlib
from datetime import datetime
from typing import Optional
from PIL import Image, ExifTags
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from config import Config


def is_allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext in Config.ALLOWED_EXTENSIONS


def autorotate_image(img: Image.Image) -> Image.Image:
    """Auto-rotate image based on EXIF orientation data."""
    try:
        if hasattr(img, '_getexif'):
            exif = img._getexif()
            if exif:
                orient_key = next((k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None)
                if orient_key:
                    orientation = exif.get(orient_key)
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
    except Exception:
        # If EXIF processing fails, return original image
        pass
    return img


def create_thumbnail(src_path: pathlib.Path, dst_path: pathlib.Path, 
                    size: int = None) -> bool:
    """Create a thumbnail from the source image."""
    if size is None:
        size = Config.THUMB_SIZE
    
    try:
        with Image.open(src_path) as img:
            img = autorotate_image(img)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            img.save(dst_path, "WEBP", quality=85, method=6)
        return True
    except Exception:
        # If thumbnail creation fails, copy original file
        try:
            dst_path.write_bytes(src_path.read_bytes())
            return True
        except Exception:
            return False


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename with timestamp and random suffix."""
    secured_name = secure_filename(original_filename or "upload")
    ext = secured_name.rsplit('.', 1)[-1].lower() if '.' in secured_name else 'jpg'
    
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    random_suffix = secrets.token_hex(4)
    
    return f"{timestamp}-{random_suffix}.{ext}"


def save_uploaded_file(file_storage: FileStorage, uploader_ip: str) -> tuple[str, Optional[str]]:
    """
    Save uploaded file and create thumbnail.
    
    Returns:
        tuple: (filename, error_message) - error_message is None on success
    """
    if not file_storage or not file_storage.filename:
        return "", "Keine Datei ausgewählt"
    
    original_filename = file_storage.filename
    
    # Validate file type
    if not is_allowed_file(original_filename):
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else "unknown"
        return "", f"Dateityp .{ext} nicht erlaubt"
    
    # Generate unique filename
    unique_filename = generate_unique_filename(original_filename)
    file_path = Config.UPLOAD_DIR / unique_filename
    
    try:
        # Save original file
        file_storage.save(file_path)
        
        # Create thumbnail
        thumb_path = Config.THUMB_DIR / (file_path.stem + ".webp")
        if not create_thumbnail(file_path, thumb_path):
            # If thumbnail creation fails, clean up and return error
            if file_path.exists():
                file_path.unlink()
            return "", f"Fehler beim Erstellen des Vorschaubildes für {original_filename}"
        
        return unique_filename, None
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        return "", f"Fehler beim Speichern von {original_filename}"


def delete_file_and_thumbnail(filename: str) -> bool:
    """Delete both the original file and its thumbnail."""
    success = True
    
    # Delete original file
    file_path = Config.UPLOAD_DIR / filename
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            success = False
    
    # Delete thumbnail
    thumb_path = Config.THUMB_DIR / (pathlib.Path(filename).stem + ".webp")
    if thumb_path.exists():
        try:
            thumb_path.unlink()
        except Exception:
            success = False
    
    return success


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"