from flask import Blueprint, jsonify, url_for
from pathlib import Path

from app.models.database import MediaRepository


api_bp = Blueprint('api', __name__)


@api_bp.route("/list")
def list_media():
    """API endpoint to list all media files."""
    media_items = MediaRepository.get_all_media()
    
    response_data = []
    for item in media_items:
        response_data.append({
            "filename": item["filename"],
            "url": url_for("main.file_raw", filename=item["filename"], _external=True),
            "thumb": url_for("main.thumb_raw", thumb=item["thumb"], _external=True),
            "orig_name": item["orig_name"],
            "created_at": item["created_at"],
            "file_size": item.get("file_size"),
            "file_type": item.get("file_type")
        })
    
    return jsonify(response_data)


@api_bp.route("/stats")
def get_stats():
    """API endpoint to get basic statistics."""
    return jsonify({
        "total_photos": MediaRepository.get_media_count(),
        "status": "active"
    })