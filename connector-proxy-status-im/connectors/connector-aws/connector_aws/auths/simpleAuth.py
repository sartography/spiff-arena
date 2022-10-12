"""SimpleAuth."""
import boto3  # type: ignore
from botocore.config import Config  # type: ignore


class SimpleAuth:
    """Established a simple Boto 3 Client based on an access key and a secret key."""

    def __init__(self, resource_type: str, access_key: str, secret_key: str):
        """
        :param access_key: AWS Access Key
        :param secret_key: AWS Secret Key
        """
        my_config = Config(
            region_name="us-east-1", retries={"max_attempts": 10, "mode": "standard"}
        )

        # Get the service resource.
        self.resource = boto3.resource(
            resource_type,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=my_config,
        )

    def get_resource(self):
        """Get_resource."""
        return self.resource
