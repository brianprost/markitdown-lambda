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

## Usage

```bash
uv run main.py <source_file>
```

The converted Markdown content will be saved to `output.md`.

## Requirements

- Python 3.13+
- I'm using `uv` for managing the package, but you can also use `pip` to install dependencies if you prefer.
- Dependencies listed in pyproject.toml
