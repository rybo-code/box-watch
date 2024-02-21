import boto3
import os


def download_sentinel_imagery(bucket_name, object_key, local_path):
    """
    Download Sentinel imagery from AWS S3.

    :bucket_name: Name of the S3 bucket containing Sentinel data
    :object_key: Key (path) of the Sentinel data object on S3
    :local_path: Path to save the downloaded data
    """
    try:
        # Initialize Boto3 S3 client
        s3 = boto3.client("s3")

        # Download the object from S3 to the local filesystem
        s3.download_file(bucket_name, object_key, local_path)

        print("File downloaded successfully.")
    except Exception as e:
        print(f"Error downloading file: {e}")


if __name__ == "__main__":
    # Define the bucket and key (path) of the Sentinel data on AWS S3
    bucket_name = "sentinel-s2-l1c"
    object_key = "tiles/31/U/ET/2019/12/2/0/preview.jpg"  # Example key, replace with the desired object key

    # Define local path to save the downloaded data
    local_path = "path/to/save/data/preview.jpg"  # Replace with your desired local path

    # Download Sentinel imagery
    download_sentinel_imagery(bucket_name, object_key, local_path)
