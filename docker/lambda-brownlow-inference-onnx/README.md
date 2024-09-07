# AFL Brownlow Vote Prediction - Lambda Function

This folder contains the AWS Lambda function responsible for processing AFL game data and predicting Brownlow votes. The function is packaged within a Docker image for deployment and execution.

## Overview

The Lambda function performs the following tasks:
1. **Data Fetching**: Retrieves AFL game data from an S3 bucket in Parquet format.
2. **Data Transformation**: Transforms and cleans the data, organizing it by player and game.
3. **Inference**: Uses an ONNX model to predict Brownlow votes for the top 3 players in each game based on their performance.
4. **DynamoDB Storage**: Stores the predicted votes and related game data into a DynamoDB table, using a partition key (HashKey) and a Global Secondary Index (GSI) for efficient querying.

## Workflow

1. The function receives an event that specifies the following parameters:
   - `year_to_query`: The AFL season year.
   - `bucket_to_save`: The S3 bucket where data is stored.
   - `data_path`: The path in the S3 bucket to the game data file.
   - `region_name`: The AWS region where the DynamoDB table is located.
   - `table_name`: The name of the DynamoDB table.
   - `model_path`: The S3 path to the ONNX model used for inference.

2. The function retrieves the AFL game data, processes it, and uses the ONNX model to predict votes for each game.

3. The predictions are stored in DynamoDB, where each record includes player stats, the round, the predicted votes, and a unique identifier (HashKey) for each entry.

## Docker Setup

The Lambda function is containerized using Docker. The `Dockerfile` sets up the environment with necessary dependencies, including:
- **pandas** and **pyarrow** for data processing.
- **onnxruntime** for running ONNX models.
- **boto3** for interacting with AWS services like S3 and DynamoDB.

## Docker Commands

To build and push the Docker image for Lambda, follow these steps:

1. **Build the Docker Image**:
   ```bash
   docker build -t lambda-brownlow-inference-onnx .