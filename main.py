from fastapi import FastAPI
from routers import auth

app = FastAPI(title="ask ai")

app.include_router(auth.router)
