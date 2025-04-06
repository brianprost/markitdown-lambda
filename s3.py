import boto3
import logging
import time
from nanoid import generate
from botocore.exceptions import ClientError
from typing import Optional, Union, Dict, Any, Tuple


def fetch_from_s3(
    bucket_name: str,
    object_key: str,
    region: str = "us-east-1",
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    version_id: Optional[str] = None,
    download_path: Optional[str] = None,
) -> Union[bytes, str, Dict[str, Any], Tuple[bool, Any]]:
    """
    Fetch content from an S3 bucket with best practices implemented.

    Args:
        bucket_name: Name of the S3 bucket
        object_key: Key of the object to fetch
        region: AWS region (defaults to us-east-1)
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        version_id: Specific version of the object to retrieve
        download_path: Path to download file to (if None, returns content)

    Returns:
        The object content as bytes, or a tuple with success status and error info

    Raises:
        Various boto3 exceptions after retry attempts are exhausted
    """
    request_id = str(generate(size=6))
    logger = logging.getLogger(__name__)

    # Initialize S3 client with appropriate config
    s3_client = boto3.client(
        "s3",
        region_name=region,
    )

    # Prepare get_object parameters
    get_kwargs = {"Bucket": bucket_name, "Key": object_key}
    if version_id:
        get_kwargs["VersionId"] = version_id

    # Implement retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(
                f"[{request_id}] Fetching s3://{bucket_name}/{object_key} (attempt {attempt + 1}/{max_retries})"
            )

            if download_path:
                # Download to file
                s3_client.download_file(
                    Bucket=bucket_name, Key=object_key, Filename=download_path
                )
                logger.info(
                    f"[{request_id}] Successfully downloaded to {download_path}"
                )
                return True
            else:
                # Get object content
                response = s3_client.get_object(**get_kwargs)
                content = response["Body"].read()

                # Log success with metadata
                logger.info(
                    f"[{request_id}] Successfully fetched object "
                    f"({len(content)} bytes, ETag: {response.get('ETag', 'unknown')})"
                )

                return content

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            # Handle specific error cases
            if error_code == "NoSuchKey":
                logger.error(
                    f"[{request_id}] Object not found: s3://{bucket_name}/{object_key}"
                )
                return False, {"error": "not_found", "message": str(e)}

            elif error_code == "AccessDenied":
                logger.error(
                    f"[{request_id}] Access denied to s3://{bucket_name}/{object_key}"
                )
                return False, {"error": "access_denied", "message": str(e)}

            # Retry on throttling or temporary errors
            elif error_code in ("ThrottlingException", "RequestTimeout", "500", "503"):
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2**attempt)
                    logger.warning(
                        f"[{request_id}] Temporary error ({error_code}), "
                        f"retrying in {wait_time:.2f}s: {str(e)}"
                    )
                    time.sleep(wait_time)
                    continue

            # For other errors, log and re-raise
            logger.error(f"[{request_id}] S3 error: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error: {str(e)}")
            raise

    # If we've exhausted retries
    logger.error(f"[{request_id}] Failed to fetch after {max_retries} attempts")
    return False, {
        "error": "max_retries_exceeded",
        "message": f"Failed after {max_retries} attempts",
    }
