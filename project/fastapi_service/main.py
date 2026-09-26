from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models  # Ensure all models are registered with Base.metadata
from routers import auth, gmail_webhook, query, upload, user_auth, chat_history

load_dotenv()

# Create all database tables on application startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ASK-AI",
    description="AI-powered email & document Q&A system",
    version="1.0",
)

# Allow the chatbot frontend (any origin) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


app.include_router(user_auth.router)
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(gmail_webhook.router)
app.include_router(chat_history.router)
