import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.core.dnse.client import DNSEClient
from src.core.trading_websocket import TradingClient
from src.core.execution_engine import ExecutionEngine

CONFIG_PATH = BASE_DIR / "data" / "config.json"
ACCOUNTS_PATH = BASE_DIR / "data" / "accounts.json"

app = FastAPI(title="Execute Engine VNSTOCK Web UI - Multi Account")

# Global state
active_engines = {}  # account_id -> ExecutionEngine
engine_tasks = {}    # account_id -> Task

class AccountCreate(BaseModel):
    name: str
    api_key: str
    api_secret: str

class ConfigItem(BaseModel):
    account_id: str
    symbol: str
    mode: str
    order_side: str
    quantity: int
    price: Optional[float] = None
    qty_threshold: Optional[int] = None
    time_execute: Optional[str] = None
    order_type: Optional[str] = "MTL"
    loan_package_id: Optional[int] = None
    status: Optional[str] = None

class CapacityCheckRequest(BaseModel):
    account_id: str
    symbol: str
    price: float
    order_side: str

class StartEngineRequest(BaseModel):
    account_id: str
    otp: str

class StopEngineRequest(BaseModel):
    account_id: str

def load_accounts():
    if not ACCOUNTS_PATH.exists():
        return []
    with open(ACCOUNTS_PATH, "r") as f:
        return json.load(f)

def save_accounts(data):
    with open(ACCOUNTS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    if not CONFIG_PATH.exists():
        return []
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

@app.get("/")
async def serve_ui():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))

# --- ACCOUNT MANAGEMENT ---
@app.get("/api/accounts")
async def get_accounts():
    accounts = load_accounts()
    # Mask API secrets
    for acc in accounts:
        acc["api_secret"] = "********"
    return accounts

@app.post("/api/accounts")
async def add_account(req: AccountCreate):
    rest_client = DNSEClient(api_key=req.api_key, api_secret=req.api_secret, base_url="https://openapi.dnse.com.vn")
    status, body = rest_client.get_accounts()
    if status != 200:
        raise HTTPException(status_code=400, detail="API Key/Secret không hợp lệ hoặc lỗi kết nối DNSE.")
    
    body = json.loads(body)
    if not body.get("accounts"):
        raise HTTPException(status_code=400, detail="Tài khoản không có tiểu khoản hợp lệ.")
        
    account_no = body["accounts"][0]["id"]
    
    accounts = load_accounts()
    new_acc = {
        "id": str(uuid.uuid4()),
        "name": req.name,
        "api_key": req.api_key,
        "api_secret": req.api_secret,
        "account_no": account_no
    }
    accounts.append(new_acc)
    save_accounts(accounts)
    
    return {"message": "Account added successfully", "id": new_acc["id"]}

@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str):
    accounts = load_accounts()
    accounts = [a for a in accounts if a["id"] != account_id]
    save_accounts(accounts)
    
    # Also remove configs for this account
    configs = load_config()
    configs = [c for c in configs if c.get("account_id") != account_id]
    save_config(configs)
    
    # Stop engine if running
    if account_id in active_engines:
        if engine_tasks.get(account_id):
            engine_tasks[account_id].cancel()
        del active_engines[account_id]
        del engine_tasks[account_id]
        
    return {"message": "Account deleted"}

# --- STATUS ---
@app.get("/api/status/{account_id}")
async def get_status(account_id: str):
    configs = load_config()
    account_configs = [c for c in configs if c.get("account_id") == account_id]
    
    accounts = load_accounts()
    account = next((a for a in accounts if a["id"] == account_id), None)
    
    is_running = account_id in active_engines
    
    return {
        "api_valid": account is not None,
        "has_configs": len(account_configs) > 0,
        "engine_running": is_running
    }

# --- CONFIG MANAGEMENT ---
@app.get("/api/config/{account_id}")
async def get_config_list(account_id: str):
    configs = load_config()
    return [c for c in configs if c.get("account_id") == account_id]

@app.post("/api/config")
async def add_config_item(item: ConfigItem):
    config = load_config()

    price = item.price
    if price is not None and price > 1000:
        price = price / 1000

    if item.status:
        status_label = item.status
    elif item.mode == "TPLUS":
        status_label = "⏳ Chờ T+"
    else:
        status_label = "✅ Cấu hình hợp lệ"

    new_cfg = {
        "account_id": item.account_id,
        "symbol": item.symbol.upper(),
        "order_side": item.order_side,
        "quantity": item.quantity,
        "price": price,
        "qty_threshold": item.qty_threshold,
        "order_type": item.order_type or "MTL",
        "loan_package_id": item.loan_package_id,
        "time_execute": item.time_execute,
        "status": status_label,
        "mode": item.mode
    }

    config.append(new_cfg)
    save_config(config)
    return {"message": "Config added successfully"}

@app.delete("/api/config/{account_id}/{index}")
async def delete_config_item(account_id: str, index: int):
    # The index from the frontend is relative to the filtered list
    configs = load_config()
    account_configs = [c for c in configs if c.get("account_id") == account_id]
    
    if 0 <= index < len(account_configs):
        cfg_to_delete = account_configs[index]
        configs.remove(cfg_to_delete)
        save_config(configs)
        return {"message": "Config removed successfully"}
    raise HTTPException(status_code=404, detail="Config not found")

# --- ENGINE & DNSE ACTIONS ---
@app.post("/api/capacity")
async def check_capacity(req: CapacityCheckRequest):
    accounts = load_accounts()
    account = next((a for a in accounts if a["id"] == req.account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    rest_client = DNSEClient(api_key=account["api_key"], api_secret=account["api_secret"], base_url="https://openapi.dnse.com.vn")
    account_no = account["account_no"]

    symbol = req.symbol.upper()
    price = req.price if req.price <= 1000 else req.price / 1000

    status_api, body = rest_client.get_loan_packages(
        account_no=account_no,
        market_type="STOCK",
        symbol=symbol,
    )
    if status_api != 200:
        raise HTTPException(status_code=502, detail="Không lấy được gói vay từ DNSE")

    body = json.loads(body)
    loan_package_id = None
    for package in body.get("loanPackages", []):
        if package.get("initialRate") == 1:
            loan_package_id = package.get("id")
            break

    if not loan_package_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy gói vay phù hợp (initialRate=1)")

    status_api, body = rest_client.get_ppse(
        account_no=account_no,
        market_type="STOCK",
        symbol=symbol,
        price=int(price * 1000),
        loan_package_id=loan_package_id,
        dry_run=False,
    )
    if status_api != 200:
        raise HTTPException(status_code=502, detail="Không lấy được sức mua/bán từ DNSE")

    body = json.loads(body)
    return {
        "loan_package_id": loan_package_id,
        "qmax_buy": body.get("qmaxBuy", 0),
        "qmax_sell": body.get("qmaxSell", 0),
        "account_no": account_no,
    }

@app.post("/api/engine/start")
async def start_engine(req: StartEngineRequest):
    acc_id = req.account_id
    if acc_id in active_engines:
        raise HTTPException(status_code=400, detail="Engine already running for this account.")

    accounts = load_accounts()
    account = next((a for a in accounts if a["id"] == acc_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    rest_client = DNSEClient(api_key=account["api_key"], api_secret=account["api_secret"], base_url="https://openapi.dnse.com.vn")
    
    status, body = rest_client.create_trading_token(
        otp_type="smart_otp",
        passcode=req.otp,
        dry_run=False,
    )
    if status != 200:
        raise HTTPException(status_code=400, detail="Token lỗi / OTP không hợp lệ")

    token = json.loads(body)["tradingToken"]

    ws_client = TradingClient(
        api_key=account["api_key"],
        api_secret=account["api_secret"],
        base_url="wss://ws-openapi.dnse.com.vn",
        encoding="msgpack",
    )

    engine = ExecutionEngine(
        rest_client,
        ws_client,
        token,
        account["account_no"],
        str(CONFIG_PATH),
        disable_live_ui=True,
        account_id=acc_id  # <--- Pass account_id here
    )

    active_engines[acc_id] = engine

    async def run_wrapper():
        try:
            await engine.start()
        except Exception as e:
            print(f"Engine {acc_id} error: {e}")

    engine_tasks[acc_id] = asyncio.create_task(run_wrapper())
    return {"message": "Engine started"}

@app.post("/api/engine/stop")
async def stop_engine(req: StopEngineRequest):
    acc_id = req.account_id
    if acc_id not in active_engines:
        raise HTTPException(status_code=400, detail="Engine not running.")

    if engine_tasks.get(acc_id):
        engine_tasks[acc_id].cancel()

    del active_engines[acc_id]
    del engine_tasks[acc_id]
    return {"message": "Engine stopped"}

@app.get("/api/engine/state/{account_id}")
async def get_engine_state(account_id: str):
    engine = active_engines.get(account_id)
    if not engine:
        return {"running": False, "data": []}

    data = []
    for sym, state in engine.market_state.items():
        data.append({
            "symbol": sym,
            "bid_px": state.get("bid_px"),
            "bid_qty": state.get("bid_qty"),
            "ask_px": state.get("ask_px"),
            "ask_qty": state.get("ask_qty"),
            "tplus": str(state.get("tplus", "-")),
            "pending": str(state.get("pending", "")),
            "signal": str(state.get("signal", ""))
        })
    return {"running": True, "data": data}

static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
