# AFL Game Data Scraper - Lambda Function

This folder contains the AWS Lambda function that scrapes AFL game-by-game statistics and uploads the data to an S3 bucket in Parquet format. The function is packaged using Docker to handle the scraping, data processing, and uploading tasks.

## Overview

The Lambda function performs the following steps:
1. **Scrape Data**: Retrieves game-by-game statistics for AFL teams from the AFL Tables website for a given year.
2. **Data Processing**: Converts the scraped HTML data into a Pandas DataFrame and processes it into a tidy format, where each row represents a player's statistics for a particular round.
3. **Upload to S3**: Converts the DataFrame into Parquet format and uploads it to a specified S3 bucket.

## Workflow

1. The function accepts an event with the following parameters:
   - `year_to_query`: The year of AFL game data to scrape (e.g., 2021).
   - `bucket_to_save`: The name of the S3 bucket where the data will be uploaded.
   - `data_path`: The path inside the S3 bucket where the Parquet file will be saved.

2. The function scrapes the game statistics for all AFL teams for the specified year.

3. The data is transformed into a tidy DataFrame, then converted into Parquet format using **pyarrow**.

4. The Parquet file is uploaded to the S3 bucket at the specified path.

## Docker Setup

This Lambda function is packaged in a Docker image. The `Dockerfile` contains all necessary dependencies for scraping the AFL Tables website and processing the data.

### Docker Commands

To build and push the Docker image for the Lambda function, follow these steps:

1. **Build the Docker Image**:
   ```bash
   docker build -t afl-gamebygame-scrape .
