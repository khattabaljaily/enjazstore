import base64
from io import BytesIO

import pyotp
import qrcode


def random_secret():
    return pyotp.random_base32()


def verify_totp(secret, code):
    return bool(secret) and bool(code) and pyotp.TOTP(secret).verify(code.strip(), valid_window=1)


def provisioning_uri(user, secret):
    return pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name='Enjaz')


def qr_data_uri(data):
    image = qrcode.make(data)
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'
