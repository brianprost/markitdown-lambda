from pathlib import Path
import re
from io import BytesIO
import warnings
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from markitdown import MarkItDown
from s3 import fetch_from_s3

s3 = boto3.client("s3")
app = FastAPI()
md = MarkItDown()

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


@app.post("/", response_model=MarkItDownResponse)
async def convert_to_markdown(request: MarkItDownRequest) -> MarkItDownResponse:
    """Convert various file types to markdown format."""
    validate_source(request.source)

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
    result = md.convert(source_content)

    # Extract or generate title
    title = result.title or extract_title(
        result.text_content, request.source.split("/")[-1]
    )

    return MarkItDownResponse(title=title, text_content=result.text_content)
