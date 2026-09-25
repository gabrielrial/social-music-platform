import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database.conf.alch_conf import engine, Base, SessionLocal
from app.api.routes.user import router as user_router
from app.api.routes.post import router as post_router
from app.api.routes.comment import router as comment_router
from app.api.routes.genre import router as genre_router
from app.api.routes.home import router as home_router
from app.services.genres import seed_genres


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_genres(db)  # the genre catalog is reference data: every database needs it
    yield

app = FastAPI(title="Rate API", version="1.0.0", lifespan=lifespan)


CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:8080,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=False,  # auth goes in the Authorization header, not in cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(user_router)
app.include_router(post_router)
app.include_router(comment_router)
app.include_router(genre_router)
app.include_router(home_router)



@app.get("/")
def read_root():
    return {"message": "Welcome to Rate API"}


# The demo frontend, served by the API itself at /app. Same origin as the
# API, so it needs no CORS and a single tunnel (ngrok http 8000) shares both.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
