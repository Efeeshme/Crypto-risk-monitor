import requests

PROXY_BASE = "http://localhost:3001"

def fetch_coin_list():
    return [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        {"id": "solana", "symbol": "sol", "name": "Solana"},
        {"id": "binancecoin", "symbol": "bnb", "name": "BNB"},
        {"id": "ripple", "symbol": "xrp", "name": "XRP"},
        {"id": "cardano", "symbol": "ada", "name": "Cardano"},
        {"id": "avalanche-2", "symbol": "avax", "name": "Avalanche"},
        {"id": "dogecoin", "symbol": "doge", "name": "Dogecoin"},
        {"id": "tron", "symbol": "trx", "name": "TRON"},
        {"id": "polkadot", "symbol": "dot", "name": "Polkadot"},
    ]

def fetch_market_data(symbol):
    r = requests.get(
        f"http://localhost:3001/coins/markets",
        params={
            "vs_currency": "usd",
            "ids": symbol.lower()
        },
        timeout=5
    )
    r.raise_for_status()
    return r.json()[0]