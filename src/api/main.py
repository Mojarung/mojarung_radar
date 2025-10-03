"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import analysis
from src.api.schemas import HealthResponse
from src.core.config import get_settings
from src.core.logging_config import log

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="RADAR - Financial News Analysis System",
    description="Real-time detection and analysis of hot financial news",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    log.info("Starting RADAR API server")
    log.info(f"Configuration: {settings.model_dump()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    log.info("Shutting down RADAR API server")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(status="healthy")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(status="healthy")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )

