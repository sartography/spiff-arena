"""AddDynamoItem."""
import json

from connector_aws.auths.simpleAuth import SimpleAuth  # type: ignore


class AddDynamoItem:
    """Add a new record to a dynamo db table."""

    def __init__(
        self, access_key: str, secret_key: str, table_name: str, item_data: str
    ):
        """
        :param access_key: AWS Access Key
        :param secret_key: AWS Secret Key
        :param table_name: The name of hte Dynamo DB table to add information to.
        :param item_data: The data to add
        :return: Json Data structure containing a http status code (hopefully '200' for success..)
            and a response string.
        """
        # Get the service resource.
        self.dynamodb = SimpleAuth("dynamodb", access_key, secret_key).get_resource()

        # Instantiate a table resource object without actually
        # creating a DynamoDB table. Note that the attributes of this table
        # are lazy-loaded: a request is not made nor are the attribute
        # values populated until the attributes
        # on the table resource are accessed or its load() method is called.
        self.table = self.dynamodb.Table(table_name)
        self.item_data = json.loads(item_data)

    def execute(self, config, task_data):
        """Execute."""
        result = self.table.put_item(Item=self.item_data)
        if "ResponseMetadata" in result:
            del result["ResponseMetadata"]
        result_str = json.dumps(result)
        return dict(response=result_str, mimetype="application/json")
