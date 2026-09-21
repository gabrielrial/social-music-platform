from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.models.genre import Genre
from app.database.conf.dependencies import get_db
from app.database.schema.genre import GenreResponse

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("/", response_model=list[GenreResponse])
def get_genres(db: Session = Depends(get_db)):
    return db.query(Genre).order_by(Genre.name).all()
