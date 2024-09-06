from aws_cdk import (
    Stack,
    aws_dynamodb,
    CfnOutput  # Import CfnOutput explicitly
)
from constructs import Construct

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
        
        # Output the table name
        CfnOutput(self, 'DynamoDBTableName', value=ddb_table.table_name,
            export_name=f'{self.stack_name}-TableName')
