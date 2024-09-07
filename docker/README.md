# AFL Brownlow Vote Prediction - Dockerized Lambda Functions

This directory contains the Dockerized AWS Lambda functions used for AFL Brownlow vote prediction and game data scraping. Each function is designed to handle specific tasks related to either scraping AFL game data or predicting Brownlow votes based on player performance.

## Structure

- **lambda-afl-gamebygame-scrape/**: Contains the Lambda function responsible for scraping AFL game-by-game statistics from the AFL Tables website and uploading the processed data to an S3 bucket in Parquet format.
- **lambda-brownlow-inference-onnx/**: Contains the Lambda function responsible for predicting AFL Brownlow votes using the previously scraped game data, running inference with an ONNX model, and storing the results in DynamoDB.

Each folder contains a `Dockerfile` for building the Lambda function and a `lambda_function.py` script that implements the core logic.

## Functionality

1. **afl-gamebygame-scrape**:
   - **Scrapes AFL game statistics** for all teams for a given season.
   - **Processes the data** into a tidy format using Pandas.
   - **Uploads the data** to an S3 bucket in Parquet format.

2. **lambda-brownlow-inference-onnx**:
   - **Fetches the game data** from S3.
   - **Processes the data** and runs inference using an ONNX model to predict the Brownlow votes for each game.
   - **Stores the results** in a DynamoDB table with predicted votes.

## Deployment

To deploy each function, you need to:
1. **Build the Docker images** for each Lambda function.
2. **Push the images** to Amazon ECR (Elastic Container Registry).
3. **Deploy the Lambda functions** using the AWS CDK or manually through the AWS Lambda service, specifying the ECR image as the code source.

### Building and Pushing Docker Images

For each folder, follow these steps:

1. **Navigate into the function’s folder** (e.g., `cd lambda-afl-gamebygame-scrape`).

2. **Build the Docker image**:
   ```bash
   docker build -t <function-name> .
