import akshare as ak
from akshare.stock.cons import zh_sina_a_stock_payload

zh_sina_a_stock_payload.update({"symbol": "sh510300"})
stock_zh_a_spot_df = ak.stock_zh_a_spot()
print(stock_zh_a_spot_df)