# import akshare as ak
# from akshare.stock.cons import zh_sina_a_stock_payload
#
# zh_sina_a_stock_payload.update({"symbol": "sh510300"})
# stock_zh_a_spot_df = ak.stock_zh_a_spot()
# print(stock_zh_a_spot_df)

import datetime
# print(datetime.datetime.now().year)
# print(datetime.datetime.now().month)
# print(datetime.datetime.now().day)

# 当前报告期
report_date = '2021-03-31'
# 当前日月
# y = datetime.datetime.now().year
# m = datetime.datetime.now().month
# d = datetime.datetime.now().day
# current = m * 100 + d
find_date = ''

# # 计算最近的报告期
# report_dates = {331: '03-31', 630: '06-30', 930: '09-30', 1231: '12-31'}
# # 当前日月
# y = datetime.datetime.now().year
# m = datetime.datetime.now().month
# d = datetime.datetime.now().day
# current = 212 #m * 100 + d
#
# count = 0
# for key, value in report_dates.items():
#     if key < current:
#         count += 1
#         continue
#
#     find_date = list(report_dates.values())[count - 1]
#     break
#
# print(find_date)
import time

# y = datetime.datetime.now().year
# m = datetime.datetime.now().month
# d = datetime.datetime.now().day
# t = datetime.datetime(y, m, d)
# print(t.toordinal())
# print((t-datetime.datetime(1970,1,1)).total_seconds())

print(str(int(round(time.time() * 1000))))