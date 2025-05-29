import requests
import qrcode
import base64
from io import BytesIO
from django.http import JsonResponse
from django.shortcuts import render

def get_ngrok_url():
    """Get the current ngrok URL."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except:
        return None

def generate_qr_code(url):
    """Generate QR code for the given URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url + '/ble-bridge/')
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def redirect_page(request):
    """Render the redirect page."""
    ngrok_url = get_ngrok_url()
    qr_code = generate_qr_code(ngrok_url) if ngrok_url else None
    
    return render(request, 'redirect.html', {
        'ngrok_url': ngrok_url,
        'qr_code': qr_code
    }) 