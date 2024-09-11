import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_dynamodb,
    aws_lambda,
    aws_apigateway,
    CfnOutput
)
from constructs import Construct
from aws_cdk.aws_iam import PolicyStatement

class BrownlowVotesDynamodbStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create DynamoDB table
        ddb_table = aws_dynamodb.Table(self, "AflBrownlowVotePredictionsTable",
            table_name="afl-brownlow-vote-predictions",
            partition_key=aws_dynamodb.Attribute(name="HashKey",
                type=aws_dynamodb.AttributeType.STRING),
            sort_key=aws_dynamodb.Attribute(name="Model",
                type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PROVISIONED,
            read_capacity=5,
            write_capacity=5,
        )

        # Add Global Secondary Index (GSI)
        ddb_table.add_global_secondary_index(
            index_name="playerGSI",
            partition_key=aws_dynamodb.Attribute(
                name="Player",
                type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="Model",
                type=aws_dynamodb.AttributeType.STRING
            ),
            projection_type=aws_dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=["Team", "Opponent", "Round", "Year", "Votes"],
            read_capacity=5,
            write_capacity=5
        )

        # Create Lambda function from external file
        leaderboard_lambda = aws_lambda.Function(self, "LeaderboardLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="leaderboard_lambda.handler",  # Handler function
            code=aws_lambda.Code.from_asset("lambda"), 
            timeout=cdk.Duration.minutes(15),
            memory_size=1024,# Path to lambda function folder
        )

        # Grant DynamoDB read permissions to the Lambda
        leaderboard_lambda.add_to_role_policy(
            PolicyStatement(
                actions=["dynamodb:Scan", "dynamodb:Query"],
                resources=[ddb_table.table_arn]
            )
        )

        # Create API Gateway
        api = aws_apigateway.LambdaRestApi(self, "LeaderboardAPI",
            handler=leaderboard_lambda,
            proxy=False
        )

        # Create a specific resource for the leaderboard query
        leaderboard_resource = api.root.add_resource("leaderboard")
        leaderboard_resource.add_method("GET")  # Allow GET requests

        # Output the API endpoint
        CfnOutput(self, 'LeaderboardAPIUrl', value=api.url,
            export_name=f'{self.stack_name}-LeaderboardAPIUrl')

        # Output the table name
        CfnOutput(self, 'DynamoDBTableName', value=ddb_table.table_name,
            export_name=f'{self.stack_name}-TableName')
