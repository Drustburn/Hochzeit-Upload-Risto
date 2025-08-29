import os
import pathlib
import secrets


class Config:
    """Base configuration class."""
    
    # Base directory
    BASE_DIR = pathlib.Path(__file__).resolve().parent
    
    # Flask configuration
    SECRET_KEY = os.getenv("FLASK_SECRET", secrets.token_urlsafe(16))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "32")) * 1024 * 1024
    
    # Upload configuration
    UPLOAD_DIR = pathlib.Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    THUMB_DIR = UPLOAD_DIR / "thumbs"
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    THUMB_SIZE = int(os.getenv("THUMB_SIZE", "640"))
    
    # Database configuration
    DB_PATH = pathlib.Path(os.getenv("DB_PATH", BASE_DIR / "uploads.db"))
    
    # Application settings
    TITLE = os.getenv("TITLE", "Hochzeitsfotos hochladen")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
    UPLOAD_CODE = os.getenv("UPLOAD_CODE")
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", secrets.token_urlsafe(16))
    
    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def init_directories(cls):
        """Create necessary directories."""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.THUMB_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}