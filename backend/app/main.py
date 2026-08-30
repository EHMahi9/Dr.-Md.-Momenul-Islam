from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import router as api_router
from app.services.retrieval_service import get_retrieval_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm retrieval service on startup
    get_retrieval_service()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.PROJECT_VERSION,
    description="Local Research Prototype API with Abstracted Retrieval Service (LLM Generation Disabled)",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for Production and Local Development
cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "project": settings.APP_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
