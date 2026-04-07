import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich import box
from logger import setup_logger_global


class ExecutionEngine:
    def __init__(self, rest_client, ws_client, trading_token, account_no, config_path, test=False):
        self.rest_client = rest_client
        self.ws_client = ws_client
        self.trading_token = trading_token
        self.account_no = account_no
        self.test = test

        self.config = self._load_config(config_path)

        self.symbol_map = {}
        for c in self.config:
            self.symbol_map.setdefault(c["symbol"], []).append(c)

        self.active = {}
        for i, c in enumerate(self.config):
            self.active[i] = True
            c["_id"] = i

        self.market_state = defaultdict(lambda: {
            "bid_px": None,
            "bid_qty": None,
            "ask_px": None,
            "ask_qty": None,
            "signal": Text(""),
            "pending": Text(""),
            "tplus": Text("-")
        })

        self.last_exec_time = {}
        self.logger = setup_logger_global("ExecutionEngine", "engine.log")

        self._init_state()

    def _load_config(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def _init_state(self):
        tz = timezone(timedelta(hours=7))
        now_dt = datetime.now(tz)

        for c in self.config:
            sym = c["symbol"]
            side = c["order_side"]
            qty = c["quantity"]
            mode = c.get("mode", "NORMAL")

            if mode == "TPLUS":
                time_execute_str = c.get("time_execute")

                if time_execute_str:
                    h, m, s = map(int, time_execute_str.split(":"))
                    exec_time = now_dt.replace(hour=h, minute=m, second=s, microsecond=0)

                    delta = int((exec_time - now_dt).total_seconds())

                    self.market_state[sym]["tplus"] = Text(f"{max(delta,0)}s", style="yellow")
                    self.market_state[sym]["pending"] = Text(
                        f"CHỜ {'MUA' if side=='BUY' else 'BÁN'} {qty}",
                        style="cyan"
                    )
            else:
                self.market_state[sym]["pending"] = Text(
                    f"{'MUA' if side=='BUY' else 'BÁN'} {qty}",
                    style="blue" if side == "BUY" else "red"
                )

    def build_table(self):
        table = Table(title="Execution Engine Monitor", box=box.SQUARE)

        table.add_column("Mã", style="bold cyan")
        table.add_column("Giá mua", justify="right")
        table.add_column("KL mua", justify="right")
        table.add_column("Giá bán", justify="right")
        table.add_column("KL bán", justify="right")
        table.add_column("T hàng về", justify="right")
        table.add_column("Lệnh chờ")
        table.add_column("Tín hiệu")

        for sym in self.symbol_map.keys():
            d = self.market_state[sym]

            p_bid = Text(f'{d["bid_px"]:.2f}', style="green") if d["bid_px"] else Text("-")
            q_bid = Text(f'{int(d["bid_qty"])}', style="green") if d["bid_qty"] else Text("-")

            p_ask = Text(f'{d["ask_px"]:.2f}', style="orange3") if d["ask_px"] else Text("-")
            q_ask = Text(f'{int(d["ask_qty"])}', style="orange3") if d["ask_qty"] else Text("-")

            table.add_row(
                sym,
                p_bid,
                q_bid,
                p_ask,
                q_ask,
                d["tplus"],
                d["pending"],
                d["signal"]
            )

        return table

    async def start(self):
        symbols = list(self.symbol_map.keys())

        await self.ws_client.connect()

        await self.ws_client.subscribe_quotes(
            symbols,
            on_quote=self.on_quote,
            encoding="msgpack",
            board_id="G1"
        )

        asyncio.create_task(self.tplus_scheduler())

        print("")
        with Live(self.build_table(), refresh_per_second=5) as live:
            self.live = live
            await asyncio.sleep(8 * 60 * 60)

    async def tplus_scheduler(self):
        tz = timezone(timedelta(hours=7))

        while True:
            now_dt = datetime.now(tz)

            for cfg in self.config:
                sid = cfg["_id"]

                if not self.active[sid]:
                    continue

                if cfg.get("mode") != "TPLUS":
                    continue

                symbol = cfg["symbol"]
                side = cfg["order_side"]
                qty = cfg["quantity"]
                loan_package_id = cfg["loan_package_id"]

                time_execute_str = cfg.get("time_execute")
                if not time_execute_str:
                    continue

                h, m, s = map(int, time_execute_str.split(":"))
                exec_time = now_dt.replace(hour=h, minute=m, second=s, microsecond=0)

                delta = (exec_time - now_dt).total_seconds()

                self.market_state[symbol]["tplus"] = Text(
                    f"{max(int(delta),0)}s",
                    style="yellow" if delta > 0 else "red"
                )

                if delta <= 0:
                    asyncio.create_task(
                        self.execute_tplus(symbol, side, qty, loan_package_id, sid)
                    )

            if hasattr(self, "live"):
                self.live.update(self.build_table())

            await asyncio.sleep(0.05)

    def on_quote(self, quote):
        symbol = quote.symbol

        if symbol not in self.symbol_map:
            return

        tz = timezone(timedelta(hours=7))
        now_dt = datetime.now(tz)

        best_bid = quote.bid[0] if quote.bid else None
        best_offer = quote.offer[0] if quote.offer else None

        self.market_state[symbol]["bid_px"] = best_bid.price if best_bid else None
        self.market_state[symbol]["bid_qty"] = best_bid.quantity if best_bid else None
        self.market_state[symbol]["ask_px"] = best_offer.price if best_offer else None
        self.market_state[symbol]["ask_qty"] = best_offer.quantity if best_offer else None

        for cfg in self.symbol_map[symbol]:
            sid = cfg["_id"]

            if not self.active[sid]:
                continue

            if cfg.get("mode") == "TPLUS":
                continue

            key = f"{symbol}_{sid}"
            now_ts = now_dt.timestamp()

            if key in self.last_exec_time:
                if now_ts - self.last_exec_time[key] < 5:
                    continue

            side = cfg["order_side"]
            qty = cfg["quantity"]
            target_price = float(cfg["price"])
            # Normalize target and market price to VND (Normal Scale)
            target_price_vnd = int(target_price * 1000) if target_price < 1000 else int(target_price)
            
            qty_threshold = cfg["qty_threshold"]
            loan_package_id = cfg["loan_package_id"]

            if side == "BUY":
                if not best_offer:
                    continue
                
                market_price_vnd = int(best_offer.price * 1000) if best_offer.price < 1000 else int(best_offer.price)
                trigger = market_price_vnd <= target_price_vnd and best_offer.quantity <= qty_threshold
                price = best_offer.price
            else:
                if not best_bid:
                    continue
                
                market_price_vnd = int(best_bid.price * 1000) if best_bid.price < 1000 else int(best_bid.price)
                trigger = market_price_vnd >= target_price_vnd and best_bid.quantity <= qty_threshold
                price = best_bid.price

            if trigger:
                self.execute_order(symbol, side, qty, price, loan_package_id, order_type="MTL")

                # Display price in Thousand Scale for consistency
                display_price = price if price < 1000 else price / 1000
                self.market_state[symbol]["signal"] = Text(
                    f"{'MUA' if side=='BUY' else 'BÁN'} {qty} @ {display_price:.2f}",
                    style="green" if side=="BUY" else "red"
                )

                self.market_state[symbol]["pending"] = Text("DONE", style="bold green")
                self.market_state[symbol]["tplus"] = Text("-")

                self.active[sid] = False
                self.last_exec_time[key] = now_ts

        self.live.update(self.build_table())

    async def execute_tplus(self, symbol, side, qty, loan_package_id, sid):
        await asyncio.sleep(1)

        tz = timezone(timedelta(hours=7))
        now = datetime.now(tz).time()

        ato_start = datetime.strptime("09:00:00", "%H:%M:%S").time()
        ato_end   = datetime.strptime("09:15:00", "%H:%M:%S").time()

        atc_start = datetime.strptime("14:30:00", "%H:%M:%S").time()
        atc_end   = datetime.strptime("14:45:00", "%H:%M:%S").time()

        # ---------------- SESSION LOGIC ----------------
        if ato_start <= now <= ato_end:
            order_type = "ATO"
            price = 0
            label = "ATO"
            price_txt = "ATO"

        elif atc_start <= now <= atc_end:
            order_type = "ATC"
            price = 0
            label = "ATC"
            price_txt = "ATC"

        else:
            best_bid = self.market_state[symbol]["bid_px"]
            best_offer = self.market_state[symbol]["ask_px"]

            price = best_offer if side == "BUY" else best_bid
            if not price:
                return

            order_type = "MTL"
            label = "MKT"
            # Normalize display price to thousand scale
            display_price = price if price < 1000 else price / 1000
            price_txt = f"{display_price:.2f}"

        # ---------------- EXECUTE ----------------
        self.execute_order(
            symbol,
            side,
            qty,
            price,
            loan_package_id,
            order_type=order_type
        )

        # ---------------- UI UPDATE ----------------
        self.market_state[symbol]["signal"] = Text(
            f"[T+] {label} {side} {qty} @ {price_txt}",
            style="green" if side == "BUY" else "red"
        )

        self.market_state[symbol]["pending"] = Text("DONE", style="bold green")
        self.market_state[symbol]["tplus"] = Text("DONE", style="bold green")

        self.active[sid] = False

    def execute_order(self, symbol, side, qty, price, loan_package_id, order_type="MTL"):
        payload = {
            "accountNo": self.account_no,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "quantity": qty
        }

        if order_type not in ["ATO", "ATC"]:
            payload["price"] = int(price * 1000) if price < 1000 else int(price)

        self.logger.warning(f"EXECUTE {symbol} {side} {qty} {order_type} @ {price}")

        status, body = self.rest_client.post_order(
            market_type="STOCK",
            payload=payload,
            trading_token=self.trading_token,
            order_category="NORMAL",
            dry_run=self.test,
            loan_package_id=loan_package_id
        )
        
        

        self.logger.warning(f"RESULT {symbol} -> {status}")