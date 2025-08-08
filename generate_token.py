# generate_token.py
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "clave_compartida_o_firma_publica"

def generate_token():
    payload = {
        "id": 1,  # ⚠️ Aquí el ID del usuario (host)
        "email": "host@example.com",
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

print(generate_token())
