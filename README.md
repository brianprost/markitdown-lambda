# markitdown-aws-lambda

A Lambda function wrapper for Microsoft's [markitdown library](https://github.com/microsoft/markitdown) to convert various file formats to Markdown Text.

## Supported File Types

- Documents: PDF, DOC, DOCX, PPT, PPTX
- Spreadsheets: XLS, XLSX, CSV
- Images: JPG, JPEG, PNG, TIFF
- Audio: MP3, WAV, OGG
- Web: HTML, HTM
- Data: JSON, XML
- Other: ZIP, EPUB, YouTube links

## API Usage

The Lambda function exposes a FastAPI service with the following endpoints:

### Health Check
```bash
GET /health
```
Returns service status and MarkItDown availability.

### Root Endpoint
```bash
GET /
```
Simple readiness check for Lambda adapter.

### Convert Files
```bash
POST /events
Content-Type: application/json

{
  "source": "s3://your-bucket/path/to/file.pdf"
}
```

Returns:
```json
{
  "title": "Document Title",
  "text_content": "# Document Title\n\nConverted markdown content...",
  "content_type": "text/markdown"
}
```

## Local Development

```bash
# Build the Docker image
docker build -t markitdown-lambda .

# Run locally
docker run -p 8080:8080 markitdown-lambda

# Test the service
python test_local.py
```

## Requirements

- Python 3.13+
- I'm using `uv` for managing the package, but you can also use `pip` to install dependencies if you prefer.
- Dependencies listed in pyproject.toml
