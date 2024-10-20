import datetime as dt
import time

import pandas as pd
from models.base_model import BaseModel
"""
		

def place_spread_order(self, qty):
print('Placing spread orders...')

contract_close = self.contracts

trade_close = self.place_market_order(contract_close, qty, self.on_filled)
print('Order placed:', trade_close)



self.is_orders_pending = True

self.pending_order_ids.add(trade_close.order.orderId)

print('Order IDs pending execution:', self.pending_order_ids)
"""


class PnLMonitorModel(BaseModel):
    def __init__(self, *args, max_drawdown_pct=1.0, **kwargs):
        super().__init__(*args, **kwargs)

        self.daily_loss_threshold = max_drawdown_pct  # Set the PnL loss threshold
        self.trade_qty = 0

    def run(self, to_trade=[], trade_qty=0):
        """ Entry point for PnL monitoring """
        print(f"[{pd.to_datetime('now')}] PnL Monitor started")

        # Initialize model based on inputs
        self.init_model(to_trade)
        self.trade_qty = trade_qty

        # Establish connection to IB
        self.connect_to_ib()
        self.request_pnl_updates()  # Monitor PnL using BaseModel method
        self.request_position_updates()  # Track positions using BaseModel method

        # Main loop to monitor PnL and take action on loss threshold breach
        while self.ib.waitOnUpdate():
            self.ib.sleep(1)
            self.check_pnl_threshold()


    def check_pnl_threshold(self):
        """ Check if PnL exceeds the threshold and close positions if necessary """
        if self.pnl and self.pnl.unrealizedPnL <= -self.daily_loss_threshold:
            print(f"PnL dropped below threshold: {self.pnl.unrealizedPnL}")
            self.close_all_positions()

    def close_all_positions(self, qty):
        print('Placing spread orders...')

        contract_close = self.contracts

        trade_close = self.place_market_order(contract_close, qty, self.on_filled)
        print('Order placed:', trade_close)


        self.is_orders_pending = True

        self.pending_order_ids.add(trade_close.order.orderId)
        print('Order IDs pending execution:', self.pending_order_ids)

    def on_filled(self, trade):
        print('Order filled:', trade)
        self.pending_order_ids.remove(trade.order.orderId)
        print('Order IDs pending execution:', self.pending_order_ids)

        # Update flag when all pending orders are filled
        if not self.pending_order_ids:
            self.is_orders_pending = False
    
