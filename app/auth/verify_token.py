import jwt
from jwt import PyJWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings  # importa settings

security = HTTPBearer()

# estamos jalando el  settings.SECRET_KEY de .env a travez de  setting 

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except PyJWTError:
        raise HTTPException(status_code=403, detail="Token inválido")
