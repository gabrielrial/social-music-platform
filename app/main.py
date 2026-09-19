from fastapi import FastAPI, Request
from app.database.conf.alch_conf import engine, Base
from app.api.routes.user import router as user_router
from app.api.routes.post import router as post_router
from app.api.routes.comment import router as comment_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rate API", version="1.0.0")

#@app.middleware("http")
#async def log_time(request: Request, call_next):
#    print("Middleware")
#    response = await call_next(request)
#    return response

# Incluir routers
app.include_router(user_router)
app.include_router(post_router)
app.include_router(comment_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Rate API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)