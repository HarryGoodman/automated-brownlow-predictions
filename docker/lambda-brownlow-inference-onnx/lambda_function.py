import io
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
import boto3
import onnxruntime
import hashlib
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ScrapedColumnNames():
    INDEX = 'index'
    PLAYER = 'player'
    TEAM = 'team'
    ROUND = 'round'
    OPPENENT = 'opponents'
    STAT = 'stat'
    VALUE = 'value'
    YEAR = 'year'

ExportColumns = {
    'YearRound': 'year_round',
    'Year': 'year',
    'Round': 'round',
    'Player': 'player',
    'Model': 'model',
    'Team': 'team',
    'Votes': 'votes',
    'Opponent': 'opponents',
    'GameID': 'game_id',
}

TeamKeys = {
    "adelaide": 'AD',
    "brisbaneb": 'BB',
    "brisbanel": 'BL',
    "carlton": 'CA',
    "collingwood": 'CW',
    "essendon": 'ES',
    "fitzroy": 'FI',
    "fremantle": 'FR',
    "geelong": 'GE',
    "goldcoast": 'GC',
    "gws": 'GW',
    "hawthorn": "HW",
    "melbourne": 'ME',
    "kangaroos": 'NM',
    "padelaide": 'PA',
    "richmond": 'RI',
    "stkilda": 'SK',
    "swans": 'SY',
    "westcoast": 'WC',
    "bullldogs": 'WB',
}

INFERENCE_COLUMNS = [
    "team",
    "opponents",
    "%_played",
    "behinds",
    "bounces",
    "clangers",
    "clearances",
    "contested_marks",
    "contested_possessions",
    "disposals",
    "frees",
    "frees_against",
    "goal_assists",
    "goals",
    "handballs",
    "hit_outs",
    "inside_50s",
    "kicks",
    "marks",
    "marks_inside_50",
    "one_percenters",
    "rebounds",
    "tackles",
    "uncontested_possessions",
]

def transform_gamebygame(df: pd.DataFrame, year: int):
    df = df.copy()
    df = df.loc[~df[ScrapedColumnNames.VALUE].isin(["Off", "On"])]
    df[ScrapedColumnNames.VALUE] = df[ScrapedColumnNames.VALUE].replace({"NA": 0})
    df[ScrapedColumnNames.VALUE] = df[ScrapedColumnNames.VALUE].astype(np.float32)

    df = df.pivot(
        index=[
            ScrapedColumnNames.PLAYER,
            ScrapedColumnNames.TEAM,
            ScrapedColumnNames.ROUND,
            ScrapedColumnNames.OPPENENT,
        ],
        columns=ScrapedColumnNames.STAT,
        values=ScrapedColumnNames.VALUE,
    ).reset_index()

    if 'subs' in df.columns:
        df = df.drop(columns='subs')

    df[ScrapedColumnNames.YEAR] = year
    df['opponents'] = df['opponents'].map({v: k for k, v in TeamKeys.items()}, na_action=None)
    df['game_id'] = df.apply(lambda row: '_'.join(sorted([row['team'], row['opponents']]) + [str(row['round'])]), axis=1)
    df['year_round'] = df.apply(lambda row: '_'.join([str(row[ScrapedColumnNames.YEAR]), str(row['round'])]), axis=1)

    return df

def lambda_handler(event, context):
    # Extract parameters from the event
    year_to_query = event['year_to_query']
    bucket_name = event['bucket_to_save']
    data_path = event['data_path']
    data_path = f'{data_path}{str(year_to_query)}.parquet'

    # DynamoDB params
    region_name = event['region_name']
    table_name = event['table_name']
    projection_expression = event['projection_expression']  # This should be 'HashKey'
    model_path = event['model_path']

    logger.info(f"Projection expression: {projection_expression}")

    # Set up the S3 client
    s3_client = boto3.client('s3')

    # Fetch data from S3
    logger.info(f"Fetching data from bucket: {bucket_name}, path: {data_path}")
    response = s3_client.get_object(Bucket=bucket_name, Key=data_path)
    parquet_data = response['Body'].read()

    # Read Parquet data using pyarrow
    parquet_table = pq.read_table(io.BytesIO(parquet_data))

    # Convert Parquet table to Pandas DataFrame
    df = parquet_table.to_pandas()
    df = transform_gamebygame(df, year_to_query)

    # DynamoDB setup
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(table_name)
    response = table.scan(
        ProjectionExpression='YearRound, ' + projection_expression  # Ensure 'YearRound' is included
    )

    # Safely extract unique YearRound values
    unique_year_round_values = {item['YearRound'] for item in response.get('Items', []) if 'YearRound' in item}
    
    # Check if the table is empty or if there are no matching 'YearRound' values
    if not unique_year_round_values:
        logger.warning("No 'YearRound' values found in DynamoDB scan results. Table might be empty.")
        rounds_in_year = []  # Set rounds_in_year to empty to avoid further processing
    else:
        rounds_in_year = [int(x.split('_')[1]) for x in unique_year_round_values if int(x.split('_')[0]) == year_to_query]

    if not rounds_in_year:
        logger.warning("No matching rounds found for the specified year.")
        max_round_inferenced = 0
    else:
        max_round_inferenced = max(rounds_in_year, default=0)

    # Continue with your code only if you have rounds to infer on
    if max_round_inferenced + 1 in df['round'].unique():
        df = df.loc[df['round'] == max_round_inferenced + 1]

        # Fetch model from S3
        logger.info(f"Fetching model from bucket: {bucket_name}, path: {model_path}")
        logger.info(f"Round to inference on: {str(max_round_inferenced + 1)}")
        response = s3_client.get_object(Bucket=bucket_name, Key=model_path)
        onnx_model_bytes = response['Body'].read()

        # Load ONNX model using ONNX Runtime
        onnx_session = onnxruntime.InferenceSession(onnx_model_bytes)

        # Ensure only existing columns are dropped, allowing 'brownlow_votes' to be missing
        columns_to_drop = ['player', 'team', 'opponents', 'round', 'year', 'brownlow_votes', 'game_id', 'year_round']
        missing_columns = [col for col in columns_to_drop if col not in df.columns and col != 'brownlow_votes']

        if missing_columns:
            raise KeyError(f"Columns not found in DataFrame: {missing_columns}")

        X_test = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
        X_test = X_test.astype(np.float32)
        X_test = X_test.to_numpy()

        # Perform inference using ONNX Runtime
        inf = []
        for x in X_test:
            t = onnx_session.run(None, {'input': x.reshape(1, -1)})
            inf.append(float(t[0]))

        # Predict Brownlow
        df['game_weight'] = inf
        df['model'] = model_path

        games = []
        for game in df.groupby('game_id'):
            game_df = game[1].nlargest(n=3, columns='game_weight')
            game_df['votes'] = [3, 2, 1]
            games.append(game_df)
        votes_df = pd.concat(games, axis=0)

        for index, row in votes_df.iterrows():
            item = {k: str(row[v]) if pd.notnull(row[v]) else None for k, v in ExportColumns.items()}
            item = {k: v for k, v in item.items() if v is not None}

            # Create a unique identifier for the HashKey using multiple attributes
            unique_identifier = f"{row[ExportColumns['Player']]}_{row[ExportColumns['Round']]}_{row[ExportColumns['Year']]}_{row[ExportColumns['GameID']]}"
            item[projection_expression] = str(hashlib.sha256(unique_identifier.encode()).hexdigest())
            item['Model'] = model_path  # Assuming model_path or a similar value is used as the Model attribute

            # Log the item and its keys to ensure correctness
            logger.info(f"Item to insert: {item}")
            logger.info(f"Keys in item: {list(item.keys())}")

            # Put the item into DynamoDB
            table.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': 'Lambda execution completed successfully.'
    }
