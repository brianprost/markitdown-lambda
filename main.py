import sys
from markitdown import MarkItDown

valid_sources = [
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
]


def main(source: str = None):
    if source and source.lower().split(".")[-1] not in valid_sources:
        raise ValueError(f"Source must be one of: {valid_sources}")

    md = MarkItDown()
    result = md.convert(source)
    print(result.text_content)
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(result.text_content)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        source_arg = sys.argv[1]
    else:
        raise ValueError(
            "Please provide a source file as a command line argument. Example: python main.py yourfile.pdf"
        )
    main(source_arg)
