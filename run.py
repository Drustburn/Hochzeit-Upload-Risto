#!/usr/bin/env python3
"""
Wedding Photo Upload Application Entry Point

Usage:
    python run.py [--config-name]
    
Config names: development, production (default: development)
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from app import create_app
from config import config


def main():
    """Main application entry point."""
    # Determine config name
    config_name = 'development'
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    elif os.getenv('FLASK_ENV') == 'production':
        config_name = 'production'
    
    # Create and run app
    app = create_app(config_name)
    
    # Print admin token for convenience
    print(f"Admin-Token: {app.config.get('ADMIN_TOKEN', config[config_name].ADMIN_TOKEN)}")
    print(f"Upload-Code: {app.config.get('UPLOAD_CODE', config[config_name].UPLOAD_CODE) or 'Not set'}")
    print(f"Running in {config_name} mode")
    
    # Run the application
    app.run(
        host=config[config_name].HOST,
        port=config[config_name].PORT,
        debug=config[config_name].DEBUG
    )


if __name__ == "__main__":
    main()