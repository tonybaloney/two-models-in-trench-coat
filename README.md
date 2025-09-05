# Two models in a trench coat

An OpenAI prompt rewriting API acting as a proxy.

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd enhance-forward
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -e .
   ```

5. **Install development dependencies** (optional):
   ```bash
   pip install -e ".[dev]"
   ```

## Running the Application

### Configuration

You need the following environment variables:

`FULL_DEPLOYMENT` and `MINI_DEPLOYMENT` are the deployment/model names for Azure OpenAI. If you want to use regular OpenAI, change the `main.py` file to initialize a different client and use the main async client class. 

`OTLP_GRPC_ENDPOINT` is optional if you want tracing (see below)

```
OPENAI_API_KEY=key.
FULL_DEPLOYMENT=gpt-4.1
MINI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_ENDPOINT=https://example.cognitiveservices.azure.com/
OTLP_GRPC_ENDPOINT=http://localhost:4317
```

### Development Server

Start the FastAPI development server with hot reload:

```bash
uvicorn main:app --reload --port 8080
```

### Running tracing dashboard

The easiest option for OTEL tracing is the Aspire dashboard, run this command for a local one in docker, look at the docker 

```bash
docker run --rm -it -p 18888:18888 -p 4317:18889 -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS='true' -d --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:9.4
```