from dnse import DNSEClient
import asyncio
import os
from trading_websocket import TradingClient
from trading_websocket.models import Quote
from pathlib import Path
from dotenv import load_dotenv
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import os

# script path: .../python/websocket-marketdata/quote.py
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PASS_CODE = os.getenv("PASS_CODE")

client = DNSEClient(
    api_key=API_KEY,
    api_secret=API_SECRET,
    base_url="https://openapi.dnse.com.vn",
)

status, body = client.get_loan_packages(
    account_no="0003659227",
    market_type="STOCK",
    symbol="SCR",
)

print(status, body)


# status, body = client.create_trading_token(
#     otp_type="smart_otp",
#     passcode=PASS_CODE,
#     dry_run=False,
# )

# trading_token = body.get("tradingToken", "")
# if trading_token == "":
#     print("Failed to create trading token")

# trading_token = "eb3b5923-2e68-4be5-8bbe-4c60a7175fbe"

# payload = {
#     "accountNo": "0003659227",
#     "symbol": "VCB",
#     "side": "BUY",
#     "orderType": "LO",
#     "price": 55000,
#     "quantity": 100,
#     "loanPackageId": 1775,
# }

# status, body = client.post_order(
#     market_type="STOCK",
#     payload=payload,
#     trading_token=trading_token,
#     order_category="NORMAL",
#     dry_run=False,
# )

# print(status, body)


# VALID_STATUS = ["Pending", "PendingNew", "New", "PartiallyFilled"]

# status, body = client.get_orders(
#     account_no="0003659227",
#     market_type="STOCK",
#     order_category="NORMAL",
#     dry_run=False,
# )

# if status == 200:
#     body = json.loads(body)
#     print(body)
#     for order in body.get("orders", []):
#         status = order.get("orderStatus", "")
#         if status not in VALID_STATUS:
#             continue
        
#         acc_no = order.get("accountNo", "")
#         oid = order.get("id", "")
#         market_type = order.get("marketType", "")
#         order_cate = order.get("orderCategory", "")

#         status, body = client.cancel_order(
#             account_no=acc_no,
#             order_id=oid,
#             trading_token=trading_token,
#             market_type=market_type,
#             order_category=order_cate
#         )

#         print(status, body)



# status, body = client.get_accounts(dry_run=False)
# print(status, body)
