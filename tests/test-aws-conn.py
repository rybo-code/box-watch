import boto3


def test_aws_s3_connectivity(bucket_name):
    """
    Test connectivity to the AWS S3 bucket.

    :param bucket_name: Name of the S3 bucket
    :return: True if connectivity is successful, False otherwise
    """
    try:
        # Initialize Boto3 S3 client
        s3 = boto3.client("s3")

        # Attempt to list contents of the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)

        # If no exception is raised, connectivity is successful
        print("Connected to AWS S3 bucket successfully.")
        return True
    except Exception as e:
        # If an exception is raised, connectivity failed
        print(f"Failed to connect to AWS S3 bucket: {e}")
        return False


if __name__ == "__main__":
    # Define the bucket name
    bucket_name = "your-bucket-name"  # Replace with your bucket name

    # Run the connectivity test
    connectivity_successful = test_aws_s3_connectivity(bucket_name)

    # Exit with status code based on test result
    exit_code = 0 if connectivity_successful else 1
    exit(exit_code)
