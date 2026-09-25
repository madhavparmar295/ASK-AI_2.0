from fastapi import FastAPI

from routers import auth
from routers import gmail_webhook


app = FastAPI(title="ask ai")

app.include_router(auth.router)
app.include_router(gmail_webhook.router)