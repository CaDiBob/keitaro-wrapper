from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.offers.router import router as offers_router
from app.streams.router import router as streams_router
from app.campaigns.router import router as campaigns_router


app = FastAPI(title="Keitaro wrapper")

app.include_router(offers_router)
app.include_router(campaigns_router)
app.include_router(streams_router)

app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="static",
)
