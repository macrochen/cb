import akshare as ak
stock_zh_a_daily_qfq_df = ak.stock_zh_a_daily(symbol="sz000002", start_date="20101103", end_date="20201116", adjust="qfq")
print(stock_zh_a_daily_qfq_df)
#
#
# url = "http://77.push2.eastmoney.com/api/qt/clist/get"
# params = {
#     "cb": "jQuery112406285914172501668_1590386857513",
#     "pn": "1",
#     "pz": "5000",
#     "po": "1",
#     "np": "1",
#     "ut": "bd1d9ddb04089700cf9c27f6f7426281",
#     "fltt": "2",
#     "invt": "2",
#     "fid": "f243",
#     "fs": "b:MK0354",
#     "fields": "f1,f152,f2,f3,f12,f13,f14,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f26,f243",
#     "_": "1590386857527",
# }
# r = requests.get(url, params=params)
# text_data = r.text
# json_data = demjson.decode(text_data[text_data.find("{") : -2])
# # items = json.loads(json_data)
#
# data = json_data.get('data')
# if data == None:
#     print("没有获取到转债列表数据")
#
# for item in data.get('diff'):
#     # 转债代码
#     code = item['f12']
#     # 上市时间
#     date = item['f243']
#     if date == '-':
#         print(item['f14'] + '未上市')
#     else:
#         print('name:' + item['f14'] + ',code:' + code + ',date:' + str(date))
#
#
#
#
#     con.commit()
#     con.close()


# d = datetime.datetime.strptime('2021-03-15', '%Y-%m-%d')
# print(str())