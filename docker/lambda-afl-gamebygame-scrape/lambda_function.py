import logging
from io import BytesIO
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_game_by_game_stats(year: int = 2021) -> pd.DataFrame:
    """Retrieves the detailed game-by-game AFL player statistics for a year."""
    min_year, max_year = 1965, 2025
    if not (min_year <= year <= max_year):
        raise ValueError(f"{year=} is not in range: {min_year}-{max_year}")

    teams = [
        "adelaide", "brisbaneb", "brisbanel", "carlton", "collingwood", "essendon", "fitzroy", "fremantle",
        "geelong", "goldcoast", "gws", "hawthorn", "melbourne", "kangaroos", "padelaide", "richmond",
        "stkilda", "swans", "westcoast", "bullldogs"
    ]

    URL = "https://afltables.com/afl/stats/teams/"

    def url_func(team):
        return f"{URL}{team}/{year}_gbg.html"

    gbg_content = {}
    for team in teams:
        r = requests.get(url_func(team))
        if r.status_code != 200:
            logger.error(f"Failed to retrieve data for {team}. HTTP Status Code: {r.status_code}")
            continue

        html_content = BeautifulSoup(r.content, features="html.parser")
        opponents = [
            s.string
            for s in html_content.find("tfoot").find_all("tr")[1].find_all("th")
        ]
        opponents = opponents[1:-1]

        for body, header in zip(
                html_content.find_all("tbody"), html_content.find_all("thead")):
            table_name = header.find("tr").find("th").string
            table_name = table_name.lower().replace(" ", "_")
            for table_row in body.find_all("tr"):
                table_content = [
                    s.string.replace("\xa0", "NA").replace("-", "NA")
                    for s in table_row.find_all("td")
                ]

                if table_content[0] not in gbg_content.keys():
                    gbg_content[table_content[0]] = {table_name: table_content[1:-1]}
                    gbg_content[table_content[0]]["opponents"] = opponents
                    gbg_content[table_content[0]]["team"] = [team for _ in range(len(opponents))]
                else:
                    gbg_content[table_content[0]][table_name] = table_content[1:-1]

    for key, values in gbg_content.items():
        if "df" not in locals():
            df = pd.DataFrame.from_dict(values)
            df["player"] = key
            df["round"] = df.index.values
        else:
            try:
                dat = pd.DataFrame.from_dict(values)
            except ValueError as ve:
                logger.error(f"Unable to parse values for {key}: {ve}")
                continue
            dat["player"] = key
            dat["round"] = dat.index.values
            df = pd.concat([df, dat], axis=0)

    return df.melt(
        id_vars=["player", "team", "round", "opponents"],
        value_name="value",
        var_name="stat",
    ).reset_index()

def lambda_handler(event, context):
    try:
        year_to_query = event['year_to_query']
        bucket_name = event['bucket_to_save']
        data_path = event['data_path']
        data_path = f'{data_path}{str(year_to_query)}.parquet'

        logger.info(f"Fetching game-by-game stats for year {year_to_query}")

        df = get_game_by_game_stats(year=year_to_query)

        buffer = BytesIO()
        pq.write_table(pa.Table.from_pandas(df), buffer)

        s3_client = boto3.client('s3')

        s3_client.put_object(
            Bucket=bucket_name,
            Key=data_path,
            Body=buffer.getvalue()
        )

        logger.info(f"File uploaded to S3: s3://{bucket_name}/{data_path}")

        return {
            'statusCode': 200,
            'body': f'Successfully uploaded to s3://{bucket_name}/{data_path}'
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
