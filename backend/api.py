from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from main_backend.main import router as main_router
from fetch_from_db_backend.main import router as db_router
from admin_backend.main import router as admin_router
from auth_backend.main import router as auth_router

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
app.include_router(admin_router, prefix="/admin")
app.include_router(auth_router,prefix="/auth")

@app.get("/")
def root():
    return {"status": "Backend running properly"}
