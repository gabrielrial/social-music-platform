from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.conf.alch_conf import engine, Base
from app.api.routes.user import router as user_router
from app.api.routes.post import router as post_router
from app.api.routes.comment import router as comment_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Rate API", version="1.0.0", lifespan=lifespan)

app.include_router(user_router)
app.include_router(post_router)
app.include_router(comment_router)



@app.get("/")
def read_root():
    return {"message": "Welcome to Rate API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)