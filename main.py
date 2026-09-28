from dotenv import load_dotenv

load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, user_auth, chat_history, gmail_webhook, query, upload, website
from services.postgres import init_db
from database import engine, Base
import models

app = FastAPI(
    title="ASK-AI 2.0",
    description="AI-powered email & document Q&A system",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        Base.metadata.create_all(bind=engine)
    except Exception:
        if os.getenv("ENVIRONMENT") == "test" and not (os.getenv("VECTOR_DB_URL") or os.getenv("DATABASE_URL")):
            return
        raise

app.include_router(auth.router)
app.include_router(user_auth.router)
app.include_router(chat_history.router)
app.include_router(gmail_webhook.router)
app.include_router(query.router)
app.include_router(upload.router)
app.include_router(website.router)