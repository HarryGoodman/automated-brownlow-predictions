import json
import boto3
from collections import defaultdict

def handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('afl-brownlow-vote-predictions')

    # Scan the DynamoDB table to retrieve all votes
    response = table.scan()
    items = response['Items']

    # Dictionary to hold the total votes for each player
    player_votes = defaultdict(int)

    # Sum votes for each player
    for item in items:
        player = item['Player']
        votes = int(item['Votes'])
        player_votes[player] += votes

    # Convert dictionary to a sorted list of tuples (player, votes)
    leaderboard = sorted(player_votes.items(), key=lambda x: x[1], reverse=True)

    # Return the top player and leaderboard
    return {
        'statusCode': 200,
        'body': json.dumps({
            'Leaderboard': leaderboard
        })
    }
