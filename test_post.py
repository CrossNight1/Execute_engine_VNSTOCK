import requests

payload = {
    "symbol": "VND",
    "mode": "NORMAL",
    "order_side": "BUY",
    "quantity": 1000,
    "price": None,
    "qty_threshold": None,
    "time_execute": None
}

try:
    response = requests.post("http://localhost:8000/api/config", json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
