"""
Demonstrates:
- Subscribing to quote (BBO) updates
"""

import asyncio
import os
from trading_websocket import TradingClient
from trading_websocket.models import Quote
from pathlib import Path
from dotenv import load_dotenv
import os

# script path: .../python/websocket-marketdata/quote.py
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("SECRET_KEY")

async def main():
    encoding = "msgpack"  # json or msgpack
    client = TradingClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        base_url="wss://ws-openapi.dnse.com.vn",
        encoding=encoding,
    )

    def handle_quote(quote: Quote):
        print(f"QUOTE: {quote}")

    print("Connecting to WebSocket gateway...")
    await client.connect()
    print(f"Connected! Session ID: {client._session_id}\n")

    print("Subscribing to quotes for SSI and 41I1G2000...")
    await client.subscribe_quotes(
        ["HPG"],
        on_quote=handle_quote,
        encoding=encoding,
        board_id="G1"
    )

    print("\nReceiving market data (will run for 8 hours)...\n")
    await asyncio.sleep(8 * 60 * 60)

    print("\n\nDisconnecting...")
    await client.disconnect()
    print("Disconnected!")


if __name__ == "__main__":
    asyncio.run(main())