# 与溢价率（双低）相关的视图


# 需导入要用到的库文件
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
import sqlite3

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

con_file = None
try:
    # 打开文件数据库
    con_file = sqlite3.connect('cb.db3')

    myCb = {}

    # 我的双低债
    result = con_file.execute("""
        SELECT cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, cb_price2_id + cb_premium_id * 100 as 双低值
        from changed_bond cb
        WHERE
        cb_name_id in ('鸿达转债','靖远转债','文科转债','广汇转债','利群转债','灵康转债','万顺转2','亚泰转债','永安转债','海兰转债','嘉泽转债','润建转债','美力转债','祥鑫转债','百川转债','杭电转债','北陆转债','胜达转债','永冠转债','铁汉转债')
        ORDER by 双低值
        """)
    rows = result.fetchall()

    for row in rows:
        myCb[row[1]] = {'x': row[3], 'y': row[4]}
        # plt.annotate(row[1].replace('转债', ''), (row[3], row[4]))


    # 活性债
    result = con_file.execute("""
SELECT c.cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, duration as 续存期,
round(s.revenue,2) as '营收(亿元)', round(s.net,2) as '净利润(亿元)', s.roe as 'ROE(%)', s.margin as  '利润率(%)', cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, 
cb_price2_id + cb_premium_id * 100 as 双低值 , market_cap as 股票市值, cb_to_share_shares * 100  as '余额/股本(%)', remain_amount as 转股余额
    from changed_bond c, stock_report s
	where c.bond_code = s.bond_code
	and duration < 3 
	-- and cb_price2_id > 108 and cb_price2_id < 120 
	-- and roe > 5 
	and s.net > 0
	-- and s.margin > 10
	and cb_t_id = '转股中' 
	-- and 溢价率 < 20 
	and 双低值 < 120
	order by 双低值 ASC
        """)

    # 低溢价率
    # result = con_file.execute("""
    #     SELECT cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id * 100 as 溢价率 from changed_bond order by 溢价率 ASC limit 10
    #     """)

    # 当前双低债
#     result = con_file.execute("""
#         SELECT cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, round(cb_price2_id + cb_premium_id * 100, 3)  as 双低值
# from changed_bond cb
# WHERE
# cb_name_id not in( '本钢转债' , '洪涛转债')
# order by 双低值 ASC limit  30;
#         """)

    # 当前债
    # result = con_file.execute("""
    # SELECT cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, cb_price2_id + cb_premium_id * 100 as 双低值
    # from changed_bond cb
    # where cb_price2_id < 150 and cb_premium_id < 1
    # ORDER by 双低值
    # """)



    rows = result.fetchall()

    # 我的
    myX = []
    myY = []

    # 重叠的
    unionX = []
    unionY = []

    # 无交集的
    x = []
    y = []

    # 所有的

    # 转股溢价率中位数
    midPremium = 29.5
    # 转债价格中位数
    midPrice = 107.7

    minPrice = 150
    maxPrice = 0

    minPremium = 0.5
    maxPremium = 0

    po_annotation1 = []

    fig, ax = plt.subplots()

    for row in rows:
        name = row[0]
        price = row[2]
        premium = row[3]

        myXy = myCb.get(name)

        if myXy != None:
            # 有交集
            unionX.append(price)
            unionY.append(premium)

            point, = ax.plot(price, premium, 'ro', alpha=0.6)

            plt.annotate(name.replace('转债', ''), (price, premium))

            # annot = ax.annotate(name + ",价格:" + str(price) + ",溢价率:" + str(round(premium, 2)) + "%",
            #                     xy=(price, premium), xytext=(6, 8), textcoords="offset points",
            #                     bbox=dict(boxstyle="round", fc="w"))
            # annot.set_visible(False)
            # po_annotation1.append([point, annot])
            
            del myCb[name]
        else:
            x.append(price)
            y.append(premium)
            plt.annotate(name.replace('转债', ''), (price, premium))
            point, = ax.plot(price, premium, 'bo', alpha=0.6)

        # plt.annotate(name.replace('转债', ''), (price, premium))

        # annot = ax.annotate(name + ",价格:" + str(price) + ",溢价率:" + str(round(premium, 2)) + "%", xy=(price, premium), xytext=(6, 8), textcoords="offset points",
        #                     bbox=dict(boxstyle="round", fc="w"))
        # annot.set_visible(False)
        # po_annotation1.append([point, annot])

    for xy in myCb.values():
        myX.append(xy['x'])
        myY.append(xy['y'])

    con_file.close()

    # plt.axis([70, 150, -5, 70])
    # plt.scatter(x, y, alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）

    # l1, = ax.plot(myX, myY, 'go', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
    # l2, = ax.plot(unionX, unionY, 'ro', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
    # l3, = ax.plot(x, y, 'bo', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）

    # 单独一种策略使用
    # plt.legend(handles=[l1, l2, l3], labels=['我的', '重叠', '现有'], loc='best')

    # plt.legend(handles=[l2, l3], labels=['我的', '现有'], loc='best')

    # 水平线
    plt.axhline(y=midPremium, color='grey', linestyle='--', alpha=0.6)

    # 垂直线
    plt.axvline(x=midPrice, color='grey', linestyle='--', alpha=0.6)

    # 四象限文字输出
    # 第1象限（高价格高溢价）
    plt.text(132, 105, "高价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))

    # 第2象限（低价格高溢价）
    plt.text(92, 105, "低价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))

    # 第3象限（低价格低溢价）
    plt.text(92, -20, "低价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))

    # 第4象限（高价格低溢价）
    plt.text(132, -20, "高价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))

    # 转债价格
    plt.xlabel("转债价格(元)", bbox=dict(facecolor='green', alpha=0.5))
    # 转股溢价率
    plt.ylabel("转股溢价率(%)", bbox=dict(facecolor='green', alpha=0.5))

    # fig, ax = plt.subplots()
    # # sc = plt.scatter(x, y)

    # 定义鼠标响应函数
    def on_move(event):
        visibility_changed = False
        for point1, annotation in po_annotation1:
            should_be_visible = (point1.contains(event)[0] == True)

            if should_be_visible != annotation.get_visible():
                visibility_changed = True
                annotation.set_visible(should_be_visible)

        # for point, annotation in po_annotation2:
        #     should_be_visible = (point.contains(event)[0] == True)
        #
        #     if should_be_visible != annotation.get_visible():
        #         visibility_changed = True
        #         annotation.set_visible(should_be_visible)

        if visibility_changed:
            plt.draw()


    # 鼠标移动事件
    # on_move_id = fig.canvas.mpl_connect('motion_notify_event', on_move)

    plt.show()

except Exception as e:
    con_file.close()
    print("操作失败", e)
# print(type(x))