# AFL Brownlow Vote Prediction - Scheduled Lambda Functions

This AWS CDK app provisions the infrastructure for scheduling two AWS Lambda functions that handle AFL game data scraping and Brownlow vote predictions. These Lambda functions are triggered automatically by EventBridge rules and use Docker images for execution.

## Overview

The CDK app sets up the following:
- **Lambda Functions**:
  - **Data Scraping**: Scrapes AFL game statistics weekly.
  - **Vote Prediction**: Runs an ONNX model to predict Brownlow votes for each game, based on the data scraped.
- **EventBridge Rules**: Schedules the Lambda functions to run weekly.
- **ECR Repositories**: Retrieves Docker images for Lambda functions that handle scraping and inference tasks.

## CDK Stacks

- **`ScheduledLambdaStack`**: Defines the infrastructure for both scheduled Lambda functions, their permissions, and the EventBridge rules for triggering them.

### Lambda Functions

1. **Brownlow Inference**: 
   - Function name: `brownlow-inference`
   - **Docker Image**: Hosted in Amazon ECR and used to run the ONNX model for vote prediction.
   - **Triggered by**: An EventBridge rule that runs the function weekly.
   - **Permissions**: S3 access for retrieving game data, DynamoDB access for storing predictions, and CloudWatch Logs for logging.

2. **Brownlow Scrape**:
   - Function name: `brownlow-scrape`
   - **Docker Image**: Used to scrape AFL game data weekly.
   - **Triggered by**: An EventBridge rule that runs the function weekly.
   - **Permissions**: S3 access for storing scraped game data and CloudWatch Logs for logging.

### EventBridge Rules

- **`brownlow-inference-weekly`**: Runs the `brownlow-inference` Lambda function weekly to generate vote predictions based on the latest game data.
- **`brownlow-scrape-weekly`**: Runs the `brownlow-scrape` Lambda function weekly to scrape the latest AFL game data.

## Deployment

### Prerequisites

- AWS CDK installed (`npm install -g aws-cdk`)
- AWS account with necessary permissions
- Python3 installed for CDK
