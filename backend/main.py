from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.upload_files_backend.upload_router import router as upload_router
from backend.fetch_from_db_backend.fetch_router import router as db_router
from backend.admin_backend.admin_router import router as admin_router
from backend.auth_backend.auth_router import router as auth_router

app = FastAPI(title="Unified Resume Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(db_router, prefix="/db")
app.include_router(admin_router, prefix="/admin")
app.include_router(auth_router,prefix="/auth")

@app.get("/")
def root():
    return {"status": "Backend running properly"}
