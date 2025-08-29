from flask import Flask
from jinja2 import ChoiceLoader, DictLoader

from config import config


def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_directories()
    
    # Initialize database
    from app.models.database import init_db
    init_db()
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Setup templates
    from app.templates.base import BASE_TEMPLATE
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        DictLoader({"base.html": BASE_TEMPLATE})
    ])
    
    return app