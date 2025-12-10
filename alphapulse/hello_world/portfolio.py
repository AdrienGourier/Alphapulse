# hello_world/portfolio.py
import json
import boto3
import os
from decimal import Decimal
import yfinance as yf

TABLE_NAME = os.environ.get('TABLE_NAME', 'alphapulse-portfolios')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_price(ticker):
    """Get current stock price using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Try different price fields that yfinance provides
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        if price:
            return Decimal(str(price))
        return Decimal('0')
    except Exception as e:
        print(f"Error getting price for {ticker}: {e}")
        return Decimal('0')

def lambda_handler(event, context):
    """Handle portfolio CRUD operations"""
    # Get user_id from authorizer context or default to public-test
    try:
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('sub', 'public-test')
    except Exception:
        user_id = 'public-test'
    
    http_method = event.get('httpMethod', '')

    if http_method == 'POST':
        # Add stock to portfolio
        try:
            body = json.loads(event.get('body', '{}'))
            ticker = body['ticker'].upper()
            shares = Decimal(str(body['shares']))
            buy_price = Decimal(str(body['buy_price']))
            date = body.get('date', 'nodate')

            sk = f"{ticker}#{date}"

            table.put_item(Item={
                'user_id': user_id,
                'sk': sk,
                'ticker': ticker,
                'shares': shares,
                'buy_price': buy_price,
                'cost': shares * buy_price
            })

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({'message': 'Stock added successfully', 'ticker': ticker})
            }
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({'error': str(e)})
            }

    elif http_method == 'GET':
        # Get portfolio with current prices and PNL
        try:
            response = table.query(
                KeyConditionExpression='user_id = :u',
                ExpressionAttributeValues={':u': user_id}
            )
            items = response.get('Items', [])

            total_cost = Decimal('0')
            total_value = Decimal('0')
            stocks = []

            for item in items:
                ticker = item['ticker']
                shares = item['shares']
                buy_price = item['buy_price']
                cost = shares * buy_price
                
                # Get current price
                current = get_price(ticker)
                value = shares * current
                pnl = value - cost
                pnl_pct = float(pnl / cost * 100) if cost > 0 else 0

                stocks.append({
                    "ticker": ticker,
                    "shares": float(shares),
                    "buy_price": float(buy_price),
                    "current_price": float(current),
                    "cost": float(cost),
                    "value": float(value),
                    "pnl": float(pnl),
                    "pnl_pct": round(pnl_pct, 2)
                })

                total_cost += cost
                total_value += value

            total_pnl = float((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({
                    'user_id': user_id,
                    'portfolio': stocks,
                    'total_cost': float(total_cost),
                    'total_value': float(total_value),
                    'total_pnl_pct': round(total_pnl, 2)
                }, cls=DecimalEncoder)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({'error': str(e)})
            }
    
    return {
        'statusCode': 405,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({'error': 'Method not allowed'})
    }