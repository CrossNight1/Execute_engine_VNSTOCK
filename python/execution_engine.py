import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from rich.live import Live
from rich.table import Table
from rich.text import Text
from logger import setup_logger_global

class ExecutionEngine:
    def __init__(self, rest_client, ws_client, trading_token, account_no, config_path, test = False):
        self.rest_client = rest_client
        self.ws_client = ws_client
        self.trading_token = trading_token
        self.account_no = account_no

        self.config = self._load_config(config_path)

        # group strategies per symbol
        self.symbol_map = {}
        for c in self.config:
            self.symbol_map.setdefault(c["symbol"], []).append(c)

        # track active strategies
        self.active = {}
        for i, c in enumerate(self.config):
            self.active[i] = True
            c["_id"] = i

        # UI state
        self.market_state = defaultdict(lambda: {
            "bid_px": None,
            "bid_qty": None,
            "ask_px": None,
            "ask_qty": None,
            "signal": ""
        })

        self.logger = setup_logger_global("ExecutionEngine", "engine.log")

    def _load_config(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def build_table(self):
        table = Table(title="Execution Engine Monitor")

        table.add_column("Mã")
        table.add_column("G_Mua_(1)", justify="right")
        table.add_column("KL_Mua_(1)", justify="right")
        table.add_column("G_Bán_(1)", justify="right")
        table.add_column("KL_Bán_(1)", justify="right")
        table.add_column("Tín hiệu")

        for sym, data in self.market_state.items():
            p_mua = f'{data["bid_px"]:.2f}' if data["bid_px"] else "-"
            q_mua = f'{int(data["bid_qty"])}' if data["bid_qty"] else "-"

            p_ban = f'{data["ask_px"]:.2f}' if data["ask_px"] else "-"
            q_ban = f'{int(data["ask_qty"])}' if data["ask_qty"] else "-"

            signal = data["signal"]

            table.add_row(sym, p_mua, q_mua, p_ban, q_ban, signal)

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

        print("")
        with Live(self.build_table(), refresh_per_second=5) as live:
            self.live = live
            await asyncio.sleep(8 * 60 * 60)

    def on_quote(self, quote):
        symbol = quote.symbol

        if symbol not in self.symbol_map:
            return

        tz = timezone(timedelta(hours=7))
        now = datetime.now(tz).time()

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

            # --- TIME FILTER ---
            time_execute_str = cfg.get("time_execute", None)
            if time_execute_str is not None:
                h, m, s = map(int, time_execute_str.split(":"))
                exec_time = datetime.now(tz).replace(hour=h, minute=m, second=s, microsecond=0).time()

                if now < exec_time:
                    continue
            # -------------------

            side = cfg["order_side"]
            target_price = float(cfg["price"])
            qty = cfg["quantity"]
            qty_threshold = cfg["qty_threshold"]

            if side == "BUY":
                if not best_offer:
                    continue

                book_price = best_offer.price
                book_qty = best_offer.quantity
                trigger = (book_price <= target_price) and (book_qty <= qty_threshold)

            else:
                if not best_bid:
                    continue

                book_price = best_bid.price
                book_qty = best_bid.quantity
                trigger = (book_price >= target_price) and (book_qty <= qty_threshold)

            if trigger:
                from rich.text import Text
                signal = Text(
                    f"{'MUA' if side=='BUY' else 'BÁN'} {qty} @ {book_price:.2f}",
                    style="green" if side=="BUY" else "red"
                )

                self.market_state[symbol]["signal"] = signal

                self.active[sid] = False

        self.live.update(self.build_table())
        
    def execute_order(self, symbol, side, qty, price, loan_package_ids):
        payload = {
            "accountNo": self.account_no,
            "symbol": symbol,
            "side": side,
            "orderType": "LO",
            "price": int(price * 1000) if price < 1000 else int(price),
            "quantity": qty
        }

        self.logger.warning(f"EXECUTE {symbol} {side} {qty} @ {price}")

        status, body = self.rest_client.post_order(
            market_type="STOCK",
            payload=payload,
            trading_token=self.trading_token,
            order_category="NORMAL",
            dry_run=self.test,
            loan_package_id=loan_package_id
        )

        self.logger.warning(f"RESULT {symbol} -> {status}")