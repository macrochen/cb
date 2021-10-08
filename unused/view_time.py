# # 与时间相关的视图展示
#
# # 需导入要用到的库文件
# import numpy as np  # 数组相关的库
# import matplotlib.pyplot as plt  # 绘图库
# import sqlite3
#
# import numpy as np
# # import matplotlib.pyplot as plt
# # plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
#
# con_file = None
# try:
#     # 打开文件数据库
#     con_file = sqlite3.connect('../db/cb.db3')
#
#     myCb = {}
#
#     # 当前可转债的续存期情况
#     result = con_file.execute("""
#     SELECT cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, duration as 续存期
#     from changed_bond cb
#     WHERE
#     --cb.rating in ('AA+', 'AA-', 'AA', 'AAA', 'A', 'A+')
#     cb_price2_id < 300
#     order by duration desc
#     --limit  30;
#     """)
#
#     rows = result.fetchall()
#
#     # 我的
#     myX = []
#     myY = []
#
#     # 重叠的
#     unionX = []
#     unionY = []
#
#     # 无交集的
#     x = []
#     y = []
#
#     # 所有的
#
#     # 强赎的平均续存期
#     midDuration = 2.6
#     # 强赎价格
#     midPrice = 130
#
#     minPrice = 1500
#     maxPrice = 0
#
#     minYield = 100
#     maxYield = -100
#
#     po_annotation1 = []
#
#     # fig, ax = plt.subplots()
#
#     for row in rows:
#         name = row[0]
#         price = row[2]
#         duration = row[4]
#
#         myXy = myCb.get(name)
#
#         if myXy != None:
#             # 有交集
#             unionX.append(price)
#             unionY.append(duration)
#
#             point, = plt.plot(price, duration, 'ro', alpha=0.6)
#
#             plt.annotate(name.replace('转债', ''), (price, duration))
#
#             # annot = ax.annotate(name + ",价格:" + str(price) + ",溢价率:" + str(round(premium, 2)) + "%",
#             #                     xy=(price, premium), xytext=(6, 8), textcoords="offset points",
#             #                     bbox=dict(boxstyle="round", fc="w"))
#             # annot.set_visible(False)
#             # po_annotation1.append([point, annot])
#
#             del myCb[name]
#         else:
#             x.append(price)
#             y.append(duration)
#             point, = plt.plot(price, duration, 'bo', alpha=0.6)
#             plt.annotate(name.replace('转债', ''), (price, duration))
#
#         # plt.annotate(name.replace('转债', ''), (price, premium))
#
#         # annot = ax.annotate(name + ",价格:" + str(price) + ",溢价率:" + str(round(premium, 2)) + "%", xy=(price, premium), xytext=(6, 8), textcoords="offset points",
#         #                     bbox=dict(boxstyle="round", fc="w"))
#         # annot.set_visible(False)
#         # po_annotation1.append([point, annot])
#
#     for key, value in myCb.items():
#         myX.append(value['x'])
#         myY.append(value['y'])
#         plt.annotate(key.replace('转债', ''), (value['x'], value['y']))
#
#     con_file.close()
#
#     # plt.axis([70, 150, -5, 70])
#     # plt.scatter(x, y, alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
#
#     l1, = plt.plot(myX, myY, 'go', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
#     # l2, = ax.plot(unionX, unionY, 'ro', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
#     # l3, = ax.plot(x, y, 'bo', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
#
#     # 单独一种策略使用
#     # plt.legend(handles=[l1, l2, l3], labels=['我的', '重叠', '现有'], loc='best')
#
#     # plt.legend(handles=[l2, l3], labels=['我的', '现有'], loc='best')
#
#     # 水平线
#     plt.axhline(y=midDuration, color='grey', linestyle='--', alpha=0.6)
#
#     # 垂直线
#     plt.axvline(x=midPrice, color='grey', linestyle='--', alpha=0.6)
#
#     # # 四象限文字输出
#     # # 第1象限（高价格高溢价）
#     # plt.text(132, 105, "高价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))
#     #
#     # # 第2象限（低价格高溢价）
#     # plt.text(92, 105, "低价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))
#     #
#     # # 第3象限（低价格低溢价）
#     # plt.text(92, -20, "低价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))
#     #
#     # # 第4象限（高价格低溢价）
#     # plt.text(132, -20, "高价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))
#
#     # 转债价格
#     plt.xlabel("转债价格(元)", bbox=dict(facecolor='green', alpha=0.5))
#     # 税前收益率
#     plt.ylabel("续存期(年)", bbox=dict(facecolor='green', alpha=0.5))
#
#     # 定义鼠标响应函数
#     def on_move(event):
#         visibility_changed = False
#         for point1, annotation in po_annotation1:
#             should_be_visible = (point1.contains(event)[0] == True)
#
#             if should_be_visible != annotation.get_visible():
#                 visibility_changed = True
#                 annotation.set_visible(should_be_visible)
#
#         # for point, annotation in po_annotation2:
#         #     should_be_visible = (point.contains(event)[0] == True)
#         #
#         #     if should_be_visible != annotation.get_visible():
#         #         visibility_changed = True
#         #         annotation.set_visible(should_be_visible)
#
#         if visibility_changed:
#             plt.draw()
#
#     # fig = plt.figure()
#     # # 鼠标移动事件
#     # on_move_id = fig.canvas.mpl_connect('motion_notify_event', on_move)
#
#     plt.show()
#
# except Exception as e:
#     con_file.close()
#     print("操作失败", e)
# # print(type(x))