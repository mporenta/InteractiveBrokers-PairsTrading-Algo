import asyncio
import datetime as dt
import time
from models.base_model import BaseModel
from util import dt_util
from models.base_model import BaseModel

class PnLMonitorModel(BaseModel):
    def __init__(self, host='127.0.0.1', port=4002, client_id=7, max_drawdown_pct=1.0):
        super().__init__(host, port, client_id)
        self.max_drawdown_pct = max_drawdown_pct / 100.0  # Convert percentage to decimal
        self.starting_pnl = None

    def run(self):
        """ Start monitoring PnL and positions. """
        self.connect_to_ib()
        self.request_pnl_updates()
        self.request_position_updates()
        asyncio.run(self.monitor_pnl_loop())

    async def monitor_pnl_loop(self):
        """ Async loop to monitor PnL in real-time. """
        while True:
            await asyncio.sleep(1)  # Check every second
            self.check_pnl()

    def check_pnl(self):
        """ Check if PnL exceeds the max drawdown threshold. """
        if not self.pnl or self.starting_pnl is None:
            self.starting_pnl = self.pnl.dailyPnL
            return

        pnl_change = self.pnl.dailyPnL - self.starting_pnl
        pnl_loss_pct = abs(pnl_change / self.starting_pnl) if self.starting_pnl != 0 else 0

        if pnl_loss_pct >= self.max_drawdown_pct:
            print(f"Max drawdown reached: {pnl_loss_pct * 100:.2f}%")
            self.close_all_positions()
            self.cancel_all_orders()

    def close_all_positions(self):
        """ Close all positions with market orders in the opposite direction. """
        for symbol, position in self.positions.items():
            if position.position != 0:
                print(f"Closing position for {symbol}")
                self.place_market_order(position.contract, -position.position, self.on_filled)

    def cancel_all_orders(self):
        """ Cancel all open orders. """
        print("Canceling all open orders")
        self.ib.reqGlobalCancel()

    def on_filled(self, trade):
        """ Called when an order is filled. """
        print(f"Order filled: {trade}")
