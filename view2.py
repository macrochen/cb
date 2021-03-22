# 与收益率（低价格高收益，回售）相关的视图展示

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

    # 我的低价高收益
    result = con_file.execute("""
        SELECT cb_num_id, cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, bt_yield * 100 as 税前收益率
from changed_bond cb
WHERE
cb_name_id in ('维格转债','天创转债','国城转债','岭南转债','孚日转债','广汇转债','科达转债','汉得转债','城地转债', '交建转债')
ORDER by 税前收益率
        """)
    rows = result.fetchall()

    for row in rows:
        myCb[row[1]] = {'x': row[3], 'y': row[5]}
        plt.annotate(row[1].replace('转债', ''), (row[3], row[4]))

    # 我的回售
    result = con_file.execute("""
SELECT cb_num_id, cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, cb_premium_id*100 as 溢价率, bt_yield * 100 as 税前收益率, red_t as 回售年限
from changed_bond cb
WHERE
cb_name_id in ('众信转债','久其转债','亚太转债','特一转债','铁汉转债','林洋转债','众兴转债','吉视转债')

        """)
    rows = result.fetchall()

    for row in rows:
        myCb[row[1]] = {'x': row[3], 'y': row[5]}

    # 当前低价格高收益债
    result = con_file.execute("""
    SELECT cb_num_id, cb_name_id as 名称, rating as 信用, cb_price2_id as 转债价格, bt_yield*100 as 收益率, 100- cb_price2_id + BT_yield * 100 as 性价比
    from changed_bond cb 
    WHERE 
    cb.rating in ('AA+', 'AA-', 'AA', 'AAA', 'A', 'A+') 
    -- cb_name_id not in( '亚药转债' , '本钢转债','搜特转债','广汇转债') 
    AND bt_yield > -0 
    and cb_price2_id < 110 
    order by 转债价格 ASC, 收益率 DESC 
    limit  30;
    """)

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

    # 收益率中位数
    midYield = 0.1
    # 转债价格中位数
    midPrice = 107.7

    minPrice = 150
    maxPrice = 0

    minYield = 100
    maxYield = -100

    po_annotation1 = []

    # fig, ax = plt.subplots()

    for row in rows:
        name = row[1]
        price = row[3]
        yieldRate = row[4]

        myXy = myCb.get(name)

        if myXy != None:
            # 有交集
            unionX.append(price)
            unionY.append(yieldRate)

            point, = plt.plot(price, yieldRate, 'ro', alpha=0.6)

            plt.annotate(name.replace('转债', ''), (price, yieldRate))

            # annot = ax.annotate(name + ",价格:" + str(price) + ",溢价率:" + str(round(premium, 2)) + "%",
            #                     xy=(price, premium), xytext=(6, 8), textcoords="offset points",
            #                     bbox=dict(boxstyle="round", fc="w"))
            # annot.set_visible(False)
            # po_annotation1.append([point, annot])
            
            del myCb[name]
        else:
            x.append(price)
            y.append(yieldRate)
            point, = plt.plot(price, yieldRate, 'bo', alpha=0.6)
            plt.annotate(name.replace('转债', ''), (price, yieldRate))

        # plt.annotate(name.replace('转债', ''), (price, premium))

        # annot = ax.annotate(name + ",价格:" + str(price) + ",溢价率:" + str(round(premium, 2)) + "%", xy=(price, premium), xytext=(6, 8), textcoords="offset points",
        #                     bbox=dict(boxstyle="round", fc="w"))
        # annot.set_visible(False)
        # po_annotation1.append([point, annot])

    for key, value in myCb.items():
        myX.append(value['x'])
        myY.append(value['y'])
        plt.annotate(key.replace('转债', ''), (value['x'], value['y']))

    con_file.close()

    # plt.axis([70, 150, -5, 70])
    # plt.scatter(x, y, alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）

    l1, = plt.plot(myX, myY, 'go', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
    # l2, = ax.plot(unionX, unionY, 'ro', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）
    # l3, = ax.plot(x, y, 'bo', alpha=0.6)  # 绘制散点图，透明度为0.6（这样颜色浅一点，比较好看）

    # 单独一种策略使用
    # plt.legend(handles=[l1, l2, l3], labels=['我的', '重叠', '现有'], loc='best')

    # plt.legend(handles=[l2, l3], labels=['我的', '现有'], loc='best')

    # 水平线
    plt.axhline(y=midYield, color='grey', linestyle='--', alpha=0.6)

    # 垂直线
    plt.axvline(x=midPrice, color='grey', linestyle='--', alpha=0.6)

    # # 四象限文字输出
    # # 第1象限（高价格高溢价）
    # plt.text(132, 105, "高价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))
    #
    # # 第2象限（低价格高溢价）
    # plt.text(92, 105, "低价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))
    #
    # # 第3象限（低价格低溢价）
    # plt.text(92, -20, "低价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))
    #
    # # 第4象限（高价格低溢价）
    # plt.text(132, -20, "高价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))

    # 转债价格
    plt.xlabel("转债价格(元)", bbox=dict(facecolor='green', alpha=0.5))
    # 税前收益率
    plt.ylabel("税前收益率(%)", bbox=dict(facecolor='green', alpha=0.5))

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

    fig = plt.figure()
    # 鼠标移动事件
    on_move_id = fig.canvas.mpl_connect('motion_notify_event', on_move)

    plt.show()

except Exception as e:
    con_file.close()
    print("操作失败", e)
# print(type(x))