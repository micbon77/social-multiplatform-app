from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import delle rotte
from routes.auth_user import router as auth_router
from routes.auth import router as social_auth_router
from routes.posts import router as posts_router

# Carica le variabili d'ambiente
load_dotenv()

app = FastAPI(
    title="Social Multiplatform Publisher",
    description="API per pubblicare contenuti su multiple piattaforme social",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare i domini esatti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusione delle rotte
app.include_router(auth_router)
app.include_router(social_auth_router)
app.include_router(posts_router)

@app.get("/")
async def root():
    return {"message": "Social Multiplatform Publisher API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )

