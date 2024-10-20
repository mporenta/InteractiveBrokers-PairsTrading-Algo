from ib_async import *

from util import order_util
import pandas as pd
"""
A base model containing common IB functions. 

For other models to extend and use.
"""

max_drawdown_pct=1.0
class PnLMonitorModel():
	def __init__(self, host='127.0.0.1', port=4002, client_id=1, max_drawdown_pct=1.0):
		self.host = host
		self.port = port
		self.client_id = client_id

		self.__ib = None
		self.pnl = None  # stores IB PnL object
		self.positions = {}  # stores IB Position object by symbol

		self.symbol_map = {}  # maps contract to symbol
		self.symbols, self.contracts = [], []
		self.daily_loss_threshold = max_drawdown_pct  # Set the PnL loss threshold
		self.trade_qty = 0


	def init_model(self, to_trade):
		"""
		Initialize the model given inputs before running.
		Stores the input symbols and contracts that will be used for reading positions.

		:param to_trade: list of a tuple of symbol and contract, Example:
			[('EURUSD', Forex('EURUSD'), ]
		"""
		self.symbol_map = {str(contract): ident for (ident, contract) in to_trade}
		self.contracts = [contract for (_, contract) in to_trade]
		self.symbols = list(self.symbol_map.values())

	def connect_to_ib(self):
		self.ib.connect(self.host, self.port, clientId=self.client_id)

	def request_pnl_updates(self):
		account = self.ib.managedAccounts()[0]
		self.ib.reqPnL(account)
		self.ib.pnlEvent += self.on_pnl

	def on_pnl(self, pnl):
		""" Simply store a copy of the latest PnL whenever where are changes """
		self.pnl = pnl

	def request_position_updates(self):
		self.ib.reqPositions()
		self.ib.positionEvent += self.on_position

	def on_position(self, position):
		""" Simply store a copy of the latest Position object for the provided contract """
		symbol = self.get_symbol(position.contract)
		if symbol not in self.symbols:
			print('[warn]symbol not found for position:', position)
			return

		self.positions[symbol] = position

	def request_all_contracts_data(self, fn_on_tick):
		for contract in self.contracts:
			self.ib.reqMktData(contract,)

		self.ib.pendingTickersEvent += fn_on_tick

	def place_market_order(self, contract, qty, fn_on_filled):
		order = MarketOrder(order_util.get_order_action(qty), abs(qty))
		trade = self.ib.placeOrder(contract, order)
		trade.filledEvent += fn_on_filled
		return trade

	def get_symbol(self, contract):
		"""
		Finds the symbol given the contract.

		:param contract: The Contract object
		:return: the symbol given for the specific contract
		"""
		symbol = self.symbol_map.get(str(contract), None)
		if symbol:
			return symbol

		symbol = ''
		if type(contract) is Forex:
			symbol = contract.localSymbol.replace('.', '')
		elif type(contract) is Stock:
			symbol = contract.symbol

		return symbol if symbol in self.symbols else ''

	@property
	def ib(self):
		if not self.__ib:
			self.__ib = IB()

		return self.__ib

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
		open_positions = self.positions  
		
		# Debug: Log the fetched positions
		print(f"Fetched positions: {open_positions}")
		
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
			except Exception as e:
				print(f"Error placing order to close {symbol}: {e}")

	def on_filled(self, trade):
		print('Order filled:', trade)
		self.pending_order_ids.remove(trade.order.orderId)
		print('Order IDs pending execution:', self.pending_order_ids)

		# Update flag when all pending orders are filled
		if not self.pending_order_ids:
			self.is_orders_pending = False
