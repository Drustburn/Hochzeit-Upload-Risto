import io
import qrcode
from flask import make_response, url_for, request

from config import Config


def generate_qr_code_response(endpoint: str = 'main.upload') -> any:
    """Generate QR code for the given endpoint and return Flask response."""
    # Determine base URL
    base_url = Config.PUBLIC_BASE_URL.rstrip("/") if Config.PUBLIC_BASE_URL else request.url_root.rstrip("/")
    
    # Generate target URL
    target_url = base_url + url_for(endpoint)
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    # Create response
    response = make_response(buf.read())
    response.headers["Content-Type"] = "image/png"
    response.headers["Cache-Control"] = "no-store"
    
    return response