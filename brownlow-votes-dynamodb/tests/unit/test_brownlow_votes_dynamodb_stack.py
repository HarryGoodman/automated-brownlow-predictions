import aws_cdk as core
import aws_cdk.assertions as assertions

from brownlow_votes_dynamodb.brownlow_votes_dynamodb_stack import BrownlowVotesDynamodbStack

# example tests. To run these tests, uncomment this file along with the example
# resource in brownlow_votes_dynamodb/brownlow_votes_dynamodb_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BrownlowVotesDynamodbStack(app, "brownlow-votes-dynamodb")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
