import json
import os
from pathlib import Path
import inquirer
import asyncio
import traceback
import sys
from dotenv import load_dotenv, set_key
from dnse import DNSEClient
from trading_websocket import TradingClient
from execution_engine import ExecutionEngine

# BASE_DIR = Path(__file__).resolve().parent

import sys, os
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
BASE_DIR = Path(BASE_PATH)

CONFIG_PATH = BASE_DIR / "config.json"
ENV_PATH = BASE_DIR / ".env"
SESSION_FILE = BASE_DIR / "session.json"

load_dotenv(ENV_PATH)

SIDE_MAP_VN_TO_EN = {"MUA": "BUY", "BÁN": "SELL"}
SIDE_MAP_EN_TO_VN = {"BUY": "MUA", "SELL": "BÁN"}

# --------------------------
# UTIL
# --------------------------
def pause():
    print()
    input("Nhấn Enter để tiếp tục...")
    print()

# --------------------------
# ERROR HANDLING
# --------------------------
def handle_errors(func):
    if asyncio.iscoroutinefunction(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                itb = sys.exc_info()[2]
                stack = traceback.extract_tb(itb)
                # Get the last entry in the stack which is usually the source of the error
                last_trace = stack[-1]
                print(f"❌ Lỗi: {e} (File: {last_trace.filename.split('/')[-1]}, Dòng: {last_trace.lineno})")
                pause()
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                itb = sys.exc_info()[2]
                stack = traceback.extract_tb(itb)
                last_trace = stack[-1]
                print(f"❌ Lỗi: {e} (File: {last_trace.filename.split('/')[-1]}, Dòng: {last_trace.lineno})")
                pause()
        return sync_wrapper

def header(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50 + "\n")

# --------------------------
# SESSION
# --------------------------
def load_session():
    if SESSION_FILE.exists():
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_session(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_account_no(rest_client):
    session = load_session()

    if "account_no" in session:
        return session["account_no"]

    status, body = rest_client.get_accounts()
    if status != 200:
        raise Exception("❌ Lỗi lấy tài khoản")

    body = json.loads(body)
    account_no = body["accounts"][0]["id"]

    session["account_no"] = account_no
    save_session(session)

    return account_no

# --------------------------
# CONFIG
# --------------------------
def load_config():
    if not CONFIG_PATH.exists():
        return []
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def clear_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "w") as f:
            json.dump([], f)
        print("\n🧹 Đã xoá toàn bộ cấu hình\n")

# --------------------------
# VIEW CONFIG
# --------------------------
@handle_errors
def view_config():
    config = load_config()
    header("DANH SÁCH CẤU HÌNH")

    if not config:
        print("⚠️ Không có cấu hình\n")
        pause()
        return

    for i, c in enumerate(config):
        side = SIDE_MAP_EN_TO_VN.get(c["order_side"])
        print(f"[{i}] Mã: {c['symbol']}")
        print(f"    Loại lệnh   : {side}")
        print(f"    Khối lượng  : {c['quantity']}")
        print(f"    Giá mục tiêu: {c['price']}")
        print(f"    Ngưỡng KL   : {c['qty_threshold']}")
        print(f"    Gói vay     : {c['loan_package_id']}")
        print(f"\n    Thời gian thực hiện: {c['time_execute']}")
        print(f"    Trạng thái cấu hình  : {c['status']}")
        print("-" * 50)

    pause()

# --------------------------
# ADD CONFIG
# --------------------------
@handle_errors
def add_config():
    config = load_config()
    header("THÊM CẤU HÌNH")

    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    rest_client = DNSEClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url="https://openapi.dnse.com.vn",
    )

    account_no = get_account_no(rest_client)
    print(f"Tài khoản: {account_no}\n")

    symbol = input("Mã cổ phiếu: ").upper()

    mode = inquirer.prompt([
        inquirer.List(
            "mode",
            message="Chế độ",
            choices=[
                "Thường (cần đủ sức mua/bán)",
                "Đợi T+ (không cần đủ sức mua/bán, bắt buộc thời gian)"
            ]
        )
    ])["mode"]

    is_tplus = "Đợi T+" in mode

    side_vn = inquirer.prompt([
        inquirer.List("side", message="Loại lệnh", choices=["MUA", "BÁN"])
    ])["side"]

    side = SIDE_MAP_VN_TO_EN[side_vn]

    price = None
    threshold = None

    if not is_tplus:
        price = float(input("Giá mục tiêu: "))

    status_api, body = rest_client.get_loan_packages(
        account_no=account_no,
        market_type="STOCK",
        symbol=symbol,
    )

    if status_api != 200:
        print("❌ Không lấy được gói vay\n")
        pause()
        return

    body = json.loads(body)

    loan_package_id = None
    for package in body.get("loanPackages", []):
        if package.get("initialRate") == 1:
            loan_package_id = package.get("id")
            break

    if not loan_package_id:
        print("❌ Không tìm thấy gói vay phù hợp\n")
        pause()
        return

    qmax_buy, qmax_sell = 0, 0

    if not is_tplus:
        status_api, body = rest_client.get_ppse(
            account_no=account_no,
            market_type="STOCK",
            symbol=symbol,
            price=int(price * 1000) if price < 1000 else int(price),
            loan_package_id=loan_package_id,
            dry_run=False,
        )

        if status_api != 200:
            print("❌ Không lấy được PPE\n")
            pause()
            return

        body = json.loads(body)

        qmax_buy = body.get("qmaxBuy", 0)
        qmax_sell = body.get("qmaxSell", 0)

        print("\n--- GIỚI HẠN GIAO DỊCH ---")
        print(f"Max MUA : {qmax_buy}")
        print(f"Max BÁN : {qmax_sell}")
        print("--------------------------\n")

    while True:
        try:
            qty = int(input("\nNhập khối lượng: "))
            if qty <= 0:
                print("\n⚠️ Khối lượng phải > 0")
                continue
        except ValueError:
            print("\n❌ Nhập số hợp lệ\n")
            continue

        status = "✅ Cấu hình hợp lệ"

        if not is_tplus:
            exceed = False

            if side == "BUY" and qty > qmax_buy:
                print(f"\n⚠️ Vượt sức mua ({qty} > {qmax_buy})")
                exceed = True

            if side == "SELL" and qty > qmax_sell:
                print(f"\n⚠️ Vượt sức bán ({qty} > {qmax_sell})")
                exceed = True

            if exceed:
                confirm = input("\nVẫn dùng? (y/n): ").lower()
                status = "⚠️ Vượt giới hạn"
                if confirm != "y":
                    continue
        else:
            status = "⏳ Chờ T+"

        break

    if not is_tplus:
        threshold = int(input("\nNgưỡng khối lượng kích hoạt: "))

    time_execute = None

    while True:
        time_input = input("\nThời gian (HH:MM:SS): ").strip()

        if time_input == "":
            if is_tplus:
                print("\n❌ T+ bắt buộc nhập thời gian\n")
                continue
            else:
                break

        try:
            h, m, s = map(int, time_input.split(":"))
            if 0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60:
                time_execute = f"{h:02d}:{m:02d}:{s:02d}"
                break
            else:
                print("\n❌ Thời gian không hợp lệ\n")
        except:
            print("\n❌ Format HH:MM:SS\n")

    new_cfg = {
        "symbol": symbol,
        "order_side": side,
        "quantity": qty,
        "price": price,
        "qty_threshold": threshold,
        "loan_package_id": loan_package_id,
        "time_execute": time_execute,
        "status": status,
        "mode": "TPLUS" if is_tplus else "NORMAL"
    }

    config.append(new_cfg)
    save_config(config)

    print("\n✅ ĐÃ THÊM CẤU HÌNH:\n")

    print(f"Mã: {new_cfg['symbol']}")
    print(f"Mode        : {new_cfg['mode']}")
    print(f"Loại lệnh   : {side_vn}")
    print(f"Khối lượng  : {new_cfg['quantity']}")

    if not is_tplus:
        print(f"Giá mục tiêu: {new_cfg['price']}")
        print(f"Ngưỡng KL   : {new_cfg['qty_threshold']}")

    print(f"Gói vay     : {new_cfg['loan_package_id']}")
    print(f"\nThời gian   : {new_cfg['time_execute']}")
    print(f"Trạng thái  : {new_cfg['status']}")
    print("-" * 50)

    pause()
        
# --------------------------
# DELETE CONFIG
# --------------------------
@handle_errors
def delete_config():
    config = load_config()
    header("XOÁ CẤU HÌNH")

    if not config:
        print("⚠️ Không có cấu hình\n")
        pause()
        return

    choices = [
        (f"[{i}] {c['symbol']} - {SIDE_MAP_EN_TO_VN[c['order_side']]} @ {c['price']}", i)
        for i, c in enumerate(config)
    ]

    ans = inquirer.prompt([
        inquirer.Checkbox("selected", message="Chọn để xoá", choices=choices)
    ])

    selected = ans["selected"]

    for idx in sorted(selected, reverse=True):
        removed = config.pop(idx)
        print(f"🗑️  Xóa cấu hình: {removed['symbol']}")

    save_config(config)

    print("\n✅ Đã xoá\n")
    pause()

# --------------------------
# UPDATE API
# --------------------------
@handle_errors
def update_api():
    header("CẬP NHẬT API")

    api_key = input("API_KEY: ")
    api_secret = input("API_SECRET: ")

    set_key(str(ENV_PATH), "API_KEY", api_key)
    set_key(str(ENV_PATH), "API_SECRET", api_secret)
    
    # Reload environment variables for current session
    load_dotenv(ENV_PATH, override=True)

    print("\n✅ OK\n")
    pause()

def has_api():
    return bool(os.getenv("API_KEY")) and bool(os.getenv("API_SECRET"))

def has_config():
    config = load_config()
    return len(config) > 0

def print_system_status():
    api_ok = has_api()
    cfg_ok = has_config()

    print("--- TRẠNG THÁI HỆ THỐNG ---")

    print("Note: Để dừng Engine, nhấn Ctrl+C")
    print(f"API         : {'✅ OK' if api_ok else '❌ Missing'}")
    print(f"Cấu hình    : {'✅ OK' if cfg_ok else '❌ Empty'}")

    print("---------------------------\n")

# --------------------------
# RUN ENGINE
# --------------------------

import signal

exit_flag = False

def signal_handler(sig, frame):
    global exit_flag
    if exit_flag:
        print("\n⚠️ Exiting program...")
        exit(0)
    else:
        print("\n⚠️ Interrupted! Press Ctrl+C again to exit.")
        exit_flag = True

signal.signal(signal.SIGINT, signal_handler)

@handle_errors
async def run_engine():
    header("CHẠY ENGINE")

    config = load_config()
    if not config:
        print("❌ Không có config\n")
        pause()
        return

    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    rest_client = DNSEClient(api_key=api_key, api_secret=api_secret, base_url="https://openapi.dnse.com.vn")

    account_no = get_account_no(rest_client)
    print(f"Tài khoản: {account_no}")

    otp = input("OTP: ")

    status, body = rest_client.create_trading_token(
        otp_type="smart_otp",
        passcode=otp,
        dry_run=False,
    )

    if status != 200:
        print("❌ Token lỗi\n")
        pause()
        return

    token = json.loads(body)["tradingToken"]

    ws_client = TradingClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url="wss://ws-openapi.dnse.com.vn",
        encoding="msgpack",
    )

    engine = ExecutionEngine(
        rest_client,
        ws_client,
        token,
        account_no,
        str(CONFIG_PATH)
    )

    print("\n🚀 Running...\n")
    await engine.start()

# --------------------------
# MENU
# --------------------------

import os

def render_menu():
    os.system("clear")  # or "cls" on Windows

    header("MENU CHÍNH")
    print_system_status()

    while not has_api():
        print("⚠️ API chưa cài đặt")
        print("Cập nhật API trước khi sử dụng chương trình.\n")
        update_api()

    print("\n")  # spacing

    ans = inquirer.prompt([
        inquirer.List(
            "action",
            message="Chọn chức năng",
            choices=[
                "Xem cấu hình",
                "Thêm cấu hình",
                "Xoá cấu hình",
                "Cập nhật API",
                "Chạy Engine",
                "Thoát"
            ],
        )
    ])

    return ans["action"]

def main_menu():
    global exit_flag
    try:
        while True:
            exit_flag = False  # reset at start of each menu cycle
            action = render_menu()

            if action == "Xem cấu hình":
                view_config()
            elif action == "Thêm cấu hình":
                add_config()
            elif action == "Xoá cấu hình":
                delete_config()
            elif action == "Cập nhật API":
                update_api()
            elif action == "Chạy Engine":
                try:
                    asyncio.run(run_engine())
                except KeyboardInterrupt:
                    print("\n⚠️ Engine stopped\n")
            elif action == "Thoát":
                print("\n👋 Thoát chương trình\n")
                break

    except KeyboardInterrupt:
        print("\n⚠️ Thoát menu\n")
    finally:
        clear_config()


if __name__ == "__main__":
    main_menu()