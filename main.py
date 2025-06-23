import sys
import os
from pathlib import Path
import re
from io import BytesIO
import warnings
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from aws_lambda_powertools import Logger

logger = Logger()

# Configure environment variables before importing libraries that use ONNX
os.environ.setdefault('ORT_LOGGING_LEVEL', '4')  # Suppress ONNX warnings
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

# Additional Lambda environment handling
if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
    # Running in Lambda, suppress additional warnings and configure threading
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    os.environ.setdefault('NUMEXPR_MAX_THREADS', '1')

# Import s3 module (safe to import early)
from s3 import fetch_from_s3

s3 = boto3.client("s3")

# Global variable for MarkItDown instance
md = None
md_initialized = False

def get_markitdown():
    """Lazy initialization of MarkItDown."""
    global md, md_initialized
    if not md_initialized:
        try:
            logger.info("Initializing MarkItDown...")
            # Configure ONNX right before importing
            try:
                import onnxruntime as ort
                ort.set_default_logger_severity(4)
            except Exception as e:
                logger.warning(f"Could not configure ONNX logging: {e}")
            
            # Import MarkItDown only when needed
            from markitdown import MarkItDown
            md = MarkItDown()
            logger.info("MarkItDown initialized successfully")
            md_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize MarkItDown: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            md = None
            md_initialized = True  # Don't keep trying
    return md

app = FastAPI(title="MarkItDown Lambda", version="0.1.0")

# Filter out deprecation warnings from botocore
warnings.filterwarnings("ignore", category=DeprecationWarning, module="botocore.*")

VALID_EXTENSIONS = {
    "pdf",
    "ppt",
    "pptx",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "jpg",
    "jpeg",
    "png",
    "tiff",
    "mp3",
    "wav",
    "ogg",
    "html",
    "htm",
    "csv",
    "json",
    "xml",
    "zip",
    "youtube",
    "epub",
}
S3_URI_PATTERN = r"s3://([^/]+)/(.+)"
DEFAULT_CONTENT_TYPE = "text/markdown"


class MarkItDownRequest(BaseModel):
    """Request model for file-to-markdown conversion."""

    source: str

    def is_s3_uri(self) -> bool:
        """Check if the source is an S3 URI."""
        return bool(re.match(S3_URI_PATTERN, self.source))


class MarkItDownResponse(BaseModel):
    """Response model for markdown-formatted content."""

    title: str
    text_content: str
    content_type: str = Field(default=DEFAULT_CONTENT_TYPE)


def extract_title(text_content: str, fallback_name: str) -> str:
    """Extract title from markdown content or use fallback."""
    if title_match := re.search(r"^#\s+(.+)$", text_content, re.MULTILINE):
        return title_match.group(1)
    return Path(fallback_name).stem


def validate_source(source: str) -> None:
    """Validate source file extension."""
    if not source:
        raise HTTPException(status_code=400, detail="Source must be provided")

    extension = source.lower().split(".")[-1]
    if extension not in VALID_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Must be one of: {', '.join(VALID_EXTENSIONS)}",
        )


@app.get("/")
async def root():
    """Root endpoint for readiness checks."""
    return {"status": "ready", "service": "markitdown-lambda"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    markitdown_instance = get_markitdown()
    return {
        "status": "healthy",
        "markitdown_available": markitdown_instance is not None,
        "python_version": sys.version
    }

@app.post("/events", response_model=MarkItDownResponse)
async def convert_to_markdown(request: MarkItDownRequest) -> MarkItDownResponse:
    """Convert various file types to markdown format."""
    markitdown_instance = get_markitdown()
    if markitdown_instance is None:
        raise HTTPException(
            status_code=500,
            detail="MarkItDown service is not available due to initialization failure"
        )
    
    validate_source(request.source)

    logger.info(f"Using Python version {sys.version}")

    # Fetch content from S3 or local file
    if request.is_s3_uri():
        bucket, key = request.source[5:].split("/", 1)
        source_content = fetch_from_s3(
            bucket_name=bucket, object_key=key, max_retries=2
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Only S3 URIs are currently supported.",
        )

    if not source_content:
        raise HTTPException(status_code=400, detail="No content found to convert")

    # Handle binary content
    if isinstance(source_content, bytes):
        source_content = BytesIO(source_content)

    # Convert to markdown
    try:
        result = markitdown_instance.convert(source_content)
    except Exception as e:
        logger.error(f"Failed to convert content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert content: {str(e)}"
        )

    # Extract or generate title
    title = result.title or extract_title(
        result.text_content, request.source.split("/")[-1]
    )

    return MarkItDownResponse(title=title, text_content=result.text_content)
