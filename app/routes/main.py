from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app

from app.models.database import MediaRepository
from app.utils.file_utils import save_uploaded_file, is_allowed_file
from app.utils.qr_utils import generate_qr_code_response
from config import Config


main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def index():
    """Main gallery page."""
    admin = request.args.get("admin")
    items = MediaRepository.get_all_media()
    
    return render_template(
        "index.html",
        items=items,
        admin=admin if admin == Config.ADMIN_TOKEN else None,
        config=Config
    )


@main_bp.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload page for handling file uploads."""
    if request.method == "POST":
        # Check upload code if required
        if Config.UPLOAD_CODE and request.form.get("code") != Config.UPLOAD_CODE:
            flash("Falscher Code.")
            return redirect(url_for("main.upload"))

        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            flash("Keine Dateien ausgewählt.")
            return redirect(url_for("main.upload"))

        saved_count = 0
        error_count = 0
        error_details = []
        
        for file_storage in files:
            if not file_storage or not file_storage.filename:
                continue
            
            # Check file size before processing
            if hasattr(file_storage, 'content_length') and file_storage.content_length:
                if file_storage.content_length > Config.MAX_CONTENT_LENGTH:
                    error_count += 1
                    size_mb = file_storage.content_length / (1024 * 1024)
                    error_details.append(f"'{file_storage.filename}': Datei zu groß ({size_mb:.1f} MB)")
                    continue
            
            # Save file and get result
            filename, error_msg = save_uploaded_file(file_storage, request.remote_addr or "")
            
            if error_msg:
                error_count += 1
                error_details.append(f"'{file_storage.filename}': {error_msg}")
            else:
                # Save to database
                file_size = getattr(file_storage, 'content_length', None)
                file_type = file_storage.filename.rsplit('.', 1)[-1].lower() if '.' in file_storage.filename else None
                
                if MediaRepository.create_media(
                    filename=filename,
                    orig_name=file_storage.filename,
                    uploader_ip=request.remote_addr or "",
                    file_size=file_size,
                    file_type=file_type
                ):
                    saved_count += 1
                else:
                    error_count += 1
                    error_details.append(f"'{file_storage.filename}': Datenbankfehler")

        # Generate user feedback
        _generate_upload_feedback(saved_count, error_count, error_details)
        return redirect(url_for("main.index"))

    return render_template(
        "upload.html",
        upload_code_required=bool(Config.UPLOAD_CODE),
        config=Config
    )


def _generate_upload_feedback(saved: int, errors: int, error_details: list):
    """Generate appropriate flash message based on upload results."""
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


@main_bp.route("/uploads/<path:filename>")
def file_raw(filename):
    """Serve uploaded files."""
    return send_from_directory(Config.UPLOAD_DIR, filename, conditional=True)


@main_bp.route("/thumbs/<path:thumb>")
def thumb_raw(thumb):
    """Serve thumbnail files."""
    return send_from_directory(Config.THUMB_DIR, thumb, conditional=True)


@main_bp.route("/qr.png")
def qr_png():
    """Generate and serve QR code."""
    return generate_qr_code_response('main.upload')


@main_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files."""
    return send_from_directory(Config.BASE_DIR / "static", filename)


@main_bp.route("/favicon.ico")
def favicon():
    """Handle favicon requests."""
    return ("", 204)


@main_bp.route("/healthz")
def healthz():
    """Health check endpoint."""
    return "ok"