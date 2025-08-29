from flask import Blueprint, request, redirect, url_for, abort

from app.models.database import MediaRepository
from app.utils.file_utils import delete_file_and_thumbnail
from config import Config


admin_bp = Blueprint('admin', __name__)


@admin_bp.route("/delete", methods=["POST"])
def delete_file():
    """Admin endpoint to delete a file."""
    # Verify admin token
    token = request.form.get("admin_token", "")
    if token != Config.ADMIN_TOKEN:
        abort(403)
    
    filename = request.form.get("filename", "")
    if not filename:
        abort(400)
    
    # Delete from database
    if MediaRepository.delete_media(filename):
        # Delete files from filesystem
        delete_file_and_thumbnail(filename)
    
    return redirect(url_for("main.index", admin=Config.ADMIN_TOKEN))