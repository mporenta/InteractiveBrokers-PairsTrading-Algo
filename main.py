import os

from ib_async import Forex, Stock
from models.pnl_monitor_model import PnLMonitorModel

if __name__ == '__main__':
    TWS_HOST = '127.0.0.1'
    TWS_PORT = 4002

    print('Connecting on host:', TWS_HOST, 'port:', TWS_PORT)

    model = PnLMonitorModel(
        host=TWS_HOST,
        port=TWS_PORT,
        client_id=7,
        max_drawdown_pct=1.0  # 1% daily PnL loss threshold
    )

    model.run()
