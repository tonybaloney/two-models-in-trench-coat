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

### Development Server

Start the FastAPI development server with hot reload:

```bash
uvicorn main:app --reload --port 8080
```

### Running tracing dashboard

```bash
docker run --rm -it -p 18888:18888 -p 4317:18889 -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS='true' -d --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:9.4
```