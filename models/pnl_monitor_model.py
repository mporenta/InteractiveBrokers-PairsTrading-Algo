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

    def close_all_positions(self):
    """ Close all open positions by fetching the current position quantities """
    print('Attempting to close all positions...')
    
    # Fetch all open positions
    open_positions = self.positions  # Positions are stored in BaseModel
    
    if not open_positions:
        print("No positions to close.")
        return
    
    # Iterate over open positions and place market orders to close each
    for symbol, position in open_positions.items():
        contract_close = position.contract
        qty = position.position  # Get the current position quantity
        
        if qty == 0:
            print(f"No open position for {symbol}. Skipping...")
            continue

        # Ensure the symbol is tracked, otherwise log a warning
        if symbol not in self.symbols:
            print(f'[warn] {symbol} not tracked by model, but position exists. Skipping...')
            continue

        print(f"Placing order to close {qty} units of {symbol}")
        
        try:
            # Place the market order to close the position
            trade_close = self.place_market_order(contract_close, -qty, self.on_filled)
            print('Order placed to close position:', trade_close)

            # Track the pending orders
            self.is_orders_pending = True
            self.pending_order_ids.add(trade_close.order.orderId)
            print(f'Order ID {trade_close.order.orderId} pending execution.')
        
        except Exception as e:
            # Handle any errors during the order placement
            print(f"Error placing order to close {symbol}: {str(e)}")
            continue

    if not self.is_orders_pending:
        print("All positions closed successfully.")
    else:
        print(f"Pending orders for closing positions: {self.pending_order_ids}")
    def on_filled(self, trade):
        print('Order filled:', trade)
        self.pending_order_ids.remove(trade.order.orderId)
        print('Order IDs pending execution:', self.pending_order_ids)

        # Update flag when all pending orders are filled
        if not self.pending_order_ids:
            self.is_orders_pending = False
    
