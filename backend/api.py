from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from main_backend.main import router as main_router
from fetch_from_db_backend.main import router as db_router

app = FastAPI(title="Unified Resume Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
app.include_router(db_router, prefix="/db")

@app.get("/")
def root():
    return {"status": "Backend running properly"}
