import aws_cdk as core
import aws_cdk.assertions as assertions

from scheduled_lambda.scheduled_lambda_stack import ScheduledLambdaStack

# example tests. To run these tests, uncomment this file along with the example
# resource in scheduled_lambda/scheduled_lambda_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ScheduledLambdaStack(app, "scheduled-lambda")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
