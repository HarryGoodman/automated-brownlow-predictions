#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda,
    aws_iam,
    aws_events,
    aws_events_targets,
    aws_ecr,
)
from constructs import Construct

class ScheduledLambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the IAM Role for Lambda with necessary permissions
        lambda_role = aws_iam.Role(self, "LambdaExecutionRoleBrownlow",
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.ServicePrincipal("events.amazonaws.com")
            ),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Add inline policies to the role for S3, DynamoDB, and CloudWatch Logs access
        lambda_role.add_to_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            resources=[
                "arn:aws:s3:::afl-game-data/*",
                "arn:aws:s3:::afl-game-data"
            ]
        ))

        lambda_role.add_to_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=[
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem",
                "dynamodb:Scan",
                "dynamodb:BatchWriteItem",
                "dynamodb:BatchGetItem"
            ],
            resources=["*"]  
        ))

        lambda_role.add_to_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            resources=["*"]  
        ))

        ecr_repository_inference = aws_ecr.Repository.from_repository_name(self, "ECRRepoInference", "lambda-brownlow-inference-onnx")

        # Define the Lambda function for Brownlow Inference using a Docker image 
        lambda_inference_fn = aws_lambda.DockerImageFunction(self, "BrownlowInference",
            function_name="brownlow-inference",
            description="Scheduled Lambda using Docker Image for Brownlow Inference",
            code=aws_lambda.DockerImageCode.from_ecr(
                repository=ecr_repository_inference,
                tag_or_digest="20231217"
            ),
            role=lambda_role,
            timeout=cdk.Duration.minutes(15),
            memory_size=1024,
            environment={
                "ENV_VARIABLE_NAME": "value"
            }
        )

        # Create an EventBridge rule for Brownlow Inference
        inference_schedule = aws_events.Rule(self, 'BrownlowInferenceScheduledRule',
            rule_name="brownlow-inference-weekly",
            description="Scheduled rule for brownlow-inference",
            schedule=aws_events.Schedule.cron(minute="20", hour="9", day="4", month="*", year="*")
        )

        inference_schedule.add_target(aws_events_targets.LambdaFunction(
            lambda_inference_fn,
            event=aws_events.RuleTargetInput.from_object({
                "bucket_to_save": "afl-game-data",
                "data_path": "data/player-gamebygame/AFL-Tables_game-by-game-stats_",
                "model_path": "models/brownlow_player_single-game/afl_brownlow_player_single-game.onnx",
                "year_to_query": 2024,
                "region_name": "ap-southeast-2",
                "table_name": "afl-brownlow-vote-predictions",
                "projection_expression": "HashKey"
            })
        ))

        ecr_repository_scrape = aws_ecr.Repository.from_repository_name(self, "ECRRepoScrape", "afl-gamebygame-scrape")

        # Define the Lambda function for Brownlow Scrape using the correct Docker image
        lambda_scrape_fn = aws_lambda.DockerImageFunction(self, "BrownlowScrape",
            function_name="brownlow-scrape",
            description="Scheduled Lambda using Docker Image for Brownlow Scrape",
            code=aws_lambda.DockerImageCode.from_ecr(
                repository=ecr_repository_scrape,
                tag_or_digest="20231217"
            ),
            role=lambda_role,
            timeout=cdk.Duration.minutes(15),
            memory_size=1024,
            environment={
                "ENV_VARIABLE_NAME": "value"
            }
        )

        # Create an EventBridge rule for Brownlow Scrape
        scrape_schedule = aws_events.Rule(self, 'BrownlowScrapeScheduledRule',
            rule_name="brownlow-scrape-weekly",
            description="Scheduled rule for brownlow-scrape",
            schedule=aws_events.Schedule.cron(minute="0", hour="9", day="4", month="*", year="*")
        )

        scrape_schedule.add_target(aws_events_targets.LambdaFunction(
            lambda_scrape_fn,
            event=aws_events.RuleTargetInput.from_object({
                "bucket_to_save": "afl-game-data",
                "data_path": "data/player-gamebygame/AFL-Tables_game-by-game-stats_",
                "year_to_query": 2024
            })
        ))

app = cdk.App()
ScheduledLambdaStack(app, "ScheduledLambdaStack")
app.synth()
