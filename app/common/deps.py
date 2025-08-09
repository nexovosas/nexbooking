from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db

DB = Annotated[Session, Depends(get_db)]
