# Automated AFL Brownlow Vote Prediction System

This project automates the prediction of AFL Brownlow votes using a combination of AWS services, Dockerized Lambda functions, and scheduled event triggers. The infrastructure is defined using AWS CDK and consists of multiple components that handle data scraping, model inference, and storage of predicted votes.

## Workflow

1. **Dockerized Lambda Functions**:
   - **Game Data Scraping**: A Lambda function, packaged in a Docker image, scrapes AFL game statistics from the AFL Tables website. It is triggered weekly by AWS EventBridge and stores the scraped data in S3.
   - **Brownlow Vote Prediction**: Another Lambda function is triggered weekly to process the scraped game data and predict Brownlow votes using an ONNX model. This function also uses a Docker image to handle complex processing tasks, such as model inference and data transformation.

2. **DynamoDB Storage**:
   - The predicted results, including player statistics and Brownlow vote predictions, are stored in a DynamoDB table. The table is designed with a partition key (`HashKey`) for game data and a Global Secondary Index (GSI) for efficient querying based on player information.

3. **EventBridge Scheduling**:
   - AWS EventBridge is used to automate the scheduling of the Lambda functions. The scraping function is scheduled to run after each completed AFL round, and the prediction function is triggered after the scraping is complete, ensuring the most up-to-date data is used for predictions.

## Project Structure

- **`docker/`**: Contains the Dockerfiles and related resources for building the Docker images used by the Lambda functions.
- **`scheduled-lambda/`**: Contains the CDK stack responsible for creating the scheduled Lambda functions and EventBridge rules.
- **`brownlow-votes-dynamodb/`**: Contains the CDK stack responsible for provisioning the DynamoDB table where Brownlow vote predictions and game data are stored.

Each folder includes its own `README.md` file. 
