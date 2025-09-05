import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from openai import AsyncAzureOpenAI
from enhance_forward.api import router as api_router
from enhance_forward.otel_grpc import configure_otel_otlp



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
    
    otel_endpoint = os.getenv("OTLP_GRPC_ENDPOINT") # e.g. "http://localhost:4317"
    if otel_endpoint:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        trace_provider = configure_otel_otlp("enhance-forward", endpoint=otel_endpoint)
        FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)
        OpenAIInstrumentor().instrument()

        print("✅ OpenTelemetry configured")
    else:
        print("⚠️ OTLP_GRPC_ENDPOINT not set, skipping OpenTelemetry configuration")

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