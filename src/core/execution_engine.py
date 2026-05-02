import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich import box
from src.utils.logger import setup_logger_global


class ExecutionEngine:
    def __init__(self, rest_client, ws_client, trading_token, account_no, config_path, test=False, disable_live_ui=False, account_id=None):
        self.rest_client = rest_client
        self.ws_client = ws_client
        self.trading_token = trading_token
        self.account_no = account_no
        self.test = test
        self.disable_live_ui = disable_live_ui
        self.account_id = account_id

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
        
        self.ui_lock = asyncio.Lock()
        self._init_state()

    def _load_config(self, path):
        with open(path, "r") as f:
            configs = json.load(f)
            if self.account_id:
                configs = [c for c in configs if c.get("account_id") == self.account_id]
            return configs

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

    async def update_ui(self):
        if not hasattr(self, "live"):
            return
        async with self.ui_lock:
            self.live.update(self.build_table())

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
        if not self.disable_live_ui:
            with Live(self.build_table(), refresh_per_second=5) as live:
                self.live = live
                
                ui_task = asyncio.create_task(self._ui_updater_loop())
                try:
                    await asyncio.sleep(8 * 60 * 60)
                finally:
                    ui_task.cancel()
        else:
            while True:
                await asyncio.sleep(1)

    async def _ui_updater_loop(self):
        while True:
            await asyncio.sleep(0.2)
            async with self.ui_lock:
                if hasattr(self, "live"):
                    self.live.update(self.build_table())

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

                if delta <= 0 and self.active[sid]:
                    # MANDATORY: Set active to False BEFORE creating the task 
                    # to prevent duplicate triggers in the next scheduler tick.
                    self.active[sid] = False
                    asyncio.create_task(
                        self.execute_tplus(cfg, sid)
                    )

            await asyncio.sleep(0.5)

    def on_quote(self, quote):
        symbol = quote.symbol

        if symbol not in self.symbol_map:
            return

        tz = timezone(timedelta(hours=7))
        now_dt = datetime.now(tz)

        best_bid = quote.bid[0] if quote.bid else None
        best_offer = quote.offer[0] if quote.offer else None

        self.market_state[symbol]["bid_px"] = best_bid.price if best_bid else None
        self.market_state[symbol]["bid_qty"] = best_bid.quantity * 10 if best_bid else None
        self.market_state[symbol]["ask_px"] = best_offer.price if best_offer else None
        self.market_state[symbol]["ask_qty"] = best_offer.quantity * 10 if best_offer else None

        for cfg in self.symbol_map[symbol]:
            sid = cfg["_id"]

            if not self.active[sid]:
                continue

            if cfg.get("mode") == "TPLUS":
                continue

            side = cfg["order_side"]
            qty = cfg["quantity"]
            target_price = float(cfg["price"])
            qty_threshold = cfg["qty_threshold"]
            loan_package_id = cfg["loan_package_id"]

            # ✅ EVALUATE TRIGGER CONDITION FIRST (before locking)
            trigger = False
            price = None

            if side == "BUY":
                # Pre-breakout BUY:
                # best_offer = cheapest ask (sellers waiting at resistance)
                # Trigger when ask is AT or ABOVE target (wall is at/above resistance)
                # AND volume there is thin → wall about to be broken upward → BUY
                if best_offer:
                    trigger = (
                        best_offer.price >= target_price and
                        best_offer.quantity * 10 <= qty_threshold
                    )
                    price = best_offer.price

            else:  # SELL
                # Pre-breakout SELL:
                # best_bid = highest bid (buyers waiting at support)
                # Trigger when bid is AT or BELOW target (wall is at/below support)
                # AND volume there is thin → wall about to be broken downward → SELL
                if best_bid:
                    trigger = (
                        best_bid.price <= target_price and
                        best_bid.quantity * 10 <= qty_threshold
                    )
                    price = best_bid.price

            if not trigger:
                # Condition not met — skip, do NOT lock
                continue

            # ✅ LOCK ONLY AFTER confirming trigger (prevent double-fire)
            key = f"{symbol}_{sid}"
            now_ts = now_dt.timestamp()

            # Extra guard: prevent re-fire within 5 seconds
            if key in self.last_exec_time:
                if now_ts - self.last_exec_time[key] < 5:
                    continue

            self.active[sid] = False
            self.last_exec_time[key] = now_ts

            self.execute_order(
                symbol, side, qty, price,
                loan_package_id, order_type=cfg.get("order_type", "MTL")
            )

    async def execute_tplus(self, cfg, sid):
        await asyncio.sleep(1)

        symbol = cfg["symbol"]
        side = cfg["order_side"]
        qty = cfg["quantity"]
        loan_package_id = cfg["loan_package_id"]
        cfg_order_type = cfg.get("order_type", "MTL")
        cfg_price = cfg.get("price")

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
            order_type = cfg_order_type
            
            if order_type == "LO" and cfg_price is not None:
                price = cfg_price
                label = "LO"
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
        pass # execute_order will update signal and pending status
        self.market_state[symbol]["tplus"] = Text("DONE", style="bold green")

        # active[sid] already set to False in tplus_scheduler before this task was created

    def execute_order(self, symbol, side, qty, price, loan_package_id, order_type="MTL"):
        # Map side to DNSE API format (NB = Buy, NS = Sell)
        side_api = "NB" if side == "BUY" else "NS"
        
        payload = {
            "accountNo": self.account_no,
            "symbol": symbol,
            "side": side_api,
            "orderType": order_type,
            "quantity": int(qty)
        }
        if loan_package_id:
            try:
                payload["loanPackageId"] = int(loan_package_id)
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid loan_package_id: {loan_package_id}")

        if order_type == "LO":
            payload["price"] = int(price * 1000) if price < 1000 else int(price)
        else:
            payload["price"] = 0

        self.logger.info(
            f"EXECUTE {symbol} {side} {qty} {order_type} @ {price} "
            f"(raw_vnd={payload.get('price', 'N/A')})"
        )

        params = dict(
            market_type="STOCK",
            payload=payload,
            trading_token=self.trading_token,
            order_category="NORMAL",
            dry_run=self.test
        )

        self.logger.debug(f"POST_ORDER {symbol} {side} {qty} {order_type} @ {price} "
                          f"(raw_vnd={payload.get('price', 'N/A')})"
                          f" params={params}")

        try:
            status, body = self.rest_client.post_order(**params)
            self.logger.info(f"RESULT {symbol} -> {status} | {body}")
            
            # Parse body if it's a string
            if isinstance(body, str):
                try:
                    body_json = json.loads(body)
                except:
                    body_json = {}
            else:
                body_json = body or {}

            if status in [200, 201]:
                # Order accepted by DNSE
                msg = f"KHỚP {side} {qty} @ {price:.2f}"
                style = "bold green" if side == "BUY" else "bold red"
                self.market_state[symbol]["signal"] = Text(msg, style=style)
                self.market_state[symbol]["pending"] = Text("SUCCESS", style="bold green")
            else:
                # Order rejected or error
                err_msg = body_json.get("message") or body_json.get("msg") or "Error"
                self.logger.error(f"ORDER REJECTED: {symbol} -> {err_msg}")
                self.market_state[symbol]["signal"] = Text(f"LỖI: {err_msg[:20]}", style="bold yellow")
                self.market_state[symbol]["pending"] = Text("REJECTED", style="bold orange3")

        except Exception as e:
            self.logger.error(f"CRITICAL ERROR during execute_order for {symbol}: {str(e)}")
            self.market_state[symbol]["signal"] = Text("LỖI MẠNG/HỆ THỐNG", style="bold white on red")
            self.market_state[symbol]["pending"] = Text("FAILED", style="bold red")