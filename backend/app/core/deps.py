"""Shared FastAPI dependencies."""
from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db

DBSession = Annotated[Session, Depends(get_db)]
