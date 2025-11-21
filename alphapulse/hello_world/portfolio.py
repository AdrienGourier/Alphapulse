# hello_world/portfolio.py
import json
import boto3
import os
from decimal import Decimal
import urllib.request

TABLE_NAME = os.environ['TABLE_NAME']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def get_price(ticker):
    try:
        url = f"https://api.polygon.io/v2/last/trade/{ticker.upper()}?apiKey=PK8T3O5O8O8O8O8O8O8O8O8O8O8O8O8O"  # free tier works without key for limited calls
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
            return Decimal(str(data['results']['p']))
    except:
        return Decimal('0')

def lambda_handler(event, context):
    user_id = event['requestContext']['authorizer']['lambda']['userId']

    if event['httpMethod'] == 'POST':
        body = json.loads(event['body'])
        ticker = body['ticker'].upper()
        shares = Decimal(str(body['shares']))
        buy_price = Decimal(str(body['buy_price']))

        sk = f"{ticker}#{body.get('date', 'nodate')}"

        table.put_item(Item={
            'user_id': user_id,
            'sk': sk,
            'ticker': ticker,
            'shares': shares,
            'buy_price': buy_price,
            'cost': shares * buy_price
        })

        return {'statusCode': 200, 'body': json.dumps('Stock added!')}

    elif event['httpMethod'] == 'GET':
        items = table.query(KeyConditionExpression='user_id = :u', 
                           ExpressionAttributeValues={':u': user_id})['Items']

        total_cost = total_value = Decimal('0')
        stocks = []

        for item in items:
            ticker = item['ticker']
            shares = item['shares']
            buy_price = item['buy_price']
            cost = shares * buy_price
            current = get_price(ticker)
            value = shares * current
            pnl = value - cost
            pnl_pct = float(pnl / cost * 100) if cost else 0

            stocks.append({
                "ticker": ticker,
                "shares": float(shares),
                "buy_price": float(buy_price),
                "current_price": float(current),
                "pnl_pct": round(pnl_pct, 2)
            })

            total_cost += cost
            total_value += value

        total_pnl = float((total_value - total_cost) / total_cost * 100) if total_cost else 0

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'portfolio': stocks,
                'total_pnl_pct': round(total_pnl, 2)
            })
        }