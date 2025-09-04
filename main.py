import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from openai import AsyncAzureOpenAI
from enhance_forward.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    Handles startup and shutdown events.
    """
    # Startup
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")

    # Create OpenAI client and store in app state
    app.state.openai_client = AsyncAzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=endpoint,
        api_key=api_key
    )
    print("✅ OpenAI client initialized")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down...")
    await app.state.openai_client.close()


# Create FastAPI instance with lifespan
app = FastAPI(
    title="Enhance Forward API",
    description="A basic FastAPI application with OpenAI integration",
    version="0.1.0",
    debug=True,
    lifespan=lifespan,
)

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)