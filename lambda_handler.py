#!/usr/bin/env python3
"""
Minimal Lambda handler that sets up environment before any imports.
"""

import os
import sys

# Critical: Set ALL environment variables before ANY imports
os.environ["ORT_LOGGING_LEVEL"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["NUMEXPR_MAX_THREADS"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["ORT_DISABLE_ALL_LOGS"] = "1"
os.environ["ONNX_DISABLE_EXCEPTIONS"] = "1"
os.environ["ORT_DISABLE_PYTHON_PACKAGE_PATH_SEARCH"] = "1"

# Suppress stderr to hide cpuinfo errors
original_stderr = sys.stderr
sys.stderr = open(os.devnull, "w")

# Now import FastAPI and create a minimal app for health checks
from fastapi import FastAPI

# Create minimal app that responds immediately to health checks
app = FastAPI(title="MarkItDown Lambda", version="0.1.0")

# Track if we've loaded the real app
real_app_loaded = False
real_app = None


@app.get("/")
async def root():
    """Root endpoint for readiness checks."""
    return {"status": "ready", "service": "markitdown-lambda"}


@app.get("/health")
async def health_check():
    """Health check endpoint - loads real app on first call."""
    global real_app_loaded, real_app

    if not real_app_loaded:
        # Restore stderr
        sys.stderr = original_stderr

        # Now load the real app
        try:
            from main import app as main_app

            real_app = main_app
            real_app_loaded = True
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "markitdown_available": False,
                "python_version": sys.version,
            }

    # If we have the real app, delegate to it
    if real_app:
        from main import get_markitdown

        markitdown_instance = get_markitdown()
        return {
            "status": "healthy",
            "markitdown_available": markitdown_instance is not None,
            "python_version": sys.version,
        }

    return {
        "status": "loading",
        "markitdown_available": False,
        "python_version": sys.version,
    }


@app.post("/events")
async def convert_to_markdown(request: dict):
    """Convert endpoint - loads real app if needed."""
    global real_app_loaded, real_app

    if not real_app_loaded:
        # Load the real app
        sys.stderr = original_stderr
        from main import app as main_app

        real_app = main_app
        real_app_loaded = True

    # Delegate to the real app
    if real_app:
        from main import convert_to_markdown as real_convert
        from main import MarkItDownRequest

        return await real_convert(MarkItDownRequest(**request))

    from fastapi import HTTPException

    raise HTTPException(status_code=503, detail="Service not ready")


# For local development with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
