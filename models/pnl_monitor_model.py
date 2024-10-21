import asyncio
from ib_async.ib import IB
from ib_async.order import MarketOrder

async def get_positions_and_place_market_orders():
    ib = IB()
    await ib.connectAsync(host="127.0.0.1", port=7497, clientId=1)
    try:
        positions = await ib.reqPositionsAsync()

        for position in positions:
            contract = position.contract
            quantity = abs(position.position)
            action = "SELL" if position.position > 0 else "BUY"
            order = MarketOrder(action, quantity)
            trade = ib.placeOrder(contract, order)
            print(f"Placed order for {contract.symbol}: {trade}")
    finally:
        ib.disconnect()

async def monitor_pnl_and_trade():
    ib = IB()
    await ib.connectAsync(host="127.0.0.1", port=7497, clientId=1)

    try:
        # Subscribe to PnL updates for the account
        pnl = ib.reqPnL("")  # Request PnL for all accounts

        @pnl.updateEvent
        def on_pnl_update(entry):
            net_liquidation = entry.netLiquidation
            daily_pnl = entry.dailyPnL

            if net_liquidation != 0:
                pnl_percentage = (daily_pnl / net_liquidation) * 100

                if pnl_percentage <= -1.0:
                    print(f"PnL is at a 1% loss or more: {pnl_percentage}%")
                    asyncio.create_task(get_positions_and_place_market_orders())

        while True:
            # Wait for 5 seconds before continuing the loop
            await asyncio.sleep(5)

    finally:
        ib.disconnect()

# Run the monitor function to continuously monitor PnL and place orders when needed
asyncio.run(monitor_pnl_and_trade())
