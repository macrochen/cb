# 将我的各种策略(双低, 回售, 高收益，活性债）选取的可转债一同展示

# 需导入要用到的库文件
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
import sqlite3
import common

import matplotlib.pyplot as plt
from prettytable import PrettyTable
from prettytable import from_db_cursor

import webbrowser
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 单选
select = [
    "低价格高收益",
    "回售",
    "双低",
    "低溢价低余额",
    "每周精选",
    "网格",
    "活性债",
    "基本面",
    "其他",
]

con_file = None

def print_table(type, cur, html, color=None):
    table = from_db_cursor(cur)
    if color != None:
        myCb[type] = {'color': color, 'table': table}

    return html + "<br><center> =========我的" + type + "=========</center><br>" + common.get_html_string(table)

def draw_figure(myCb):

    plt.figure(figsize=(12, 7), )

    for label, data in myCb.items():
        if label not in select:
            continue

        x = []
        y = []
        table = data['table']
        rows = table._rows
        for row in rows:
            record = common.getRecord(table, row)
            plt.annotate(record['名称'].replace('转债', ''), (record['转债价格'], record['溢价率']))
            x.append(record['转债价格'])
            y.append(record['溢价率'])

        color = data['color']
        handle = plt.scatter(x, y, marker='o', c=color, alpha=0.6, label=label)

    plt.legend()

    plt.title("可转债摊大饼")

    # 所有的

    # 溢价率中位数
    midYield = 29.49
    # 转债价格中位数
    midPrice = 108.13

    # 水平线
    plt.axhline(y=midYield, color='grey', linestyle='--', alpha=0.6)

    # 垂直线
    plt.axvline(x=midPrice, color='grey', linestyle='--', alpha=0.6)

    # 单个策略, 不输出四象限
    if len(select) > 1:
        # 四象限文字输出
        # 第1象限（高价格高溢价）
        plt.text(120, 180, "高价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))

        # 第2象限（低价格高溢价）
        plt.text(92, 180, "低价格高溢价", bbox=dict(facecolor='yellow', alpha=0.5))

        # 第3象限（低价格低溢价）
        plt.text(92, -20, "低价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))

        # 第4象限（高价格低溢价）
        plt.text(120, -20, "高价格低溢价", bbox=dict(facecolor='yellow', alpha=0.5))

    # 转债价格
    plt.xlabel("转债价格(元)", bbox=dict(facecolor='green', alpha=0.5))
    # 税前收益率
    plt.ylabel("转债溢价率(%)", bbox=dict(facecolor='green', alpha=0.5))

    # # 定义鼠标响应函数
    # def on_move(event):
    #     visibility_changed = False
    #     for point1, annotation in po_annotation1:
    #         should_be_visible = (point1.contains(event)[0] == True)
    #
    #         if should_be_visible != annotation.get_visible():
    #             visibility_changed = True
    #             annotation.set_visible(should_be_visible)
    #
    #     # for point, annotation in po_annotation2:
    #     #     should_be_visible = (point.contains(event)[0] == True)
    #     #
    #     #     if should_be_visible != annotation.get_visible():
    #     #         visibility_changed = True
    #     #         annotation.set_visible(should_be_visible)
    #
    #     if visibility_changed:
    #         plt.draw()
    #
    # fig = plt.figure()
    # # 鼠标移动事件
    # on_move_id = fig.canvas.mpl_connect('motion_notify_event', on_move)

    plt.show()

try:
    # 打开文件数据库
    con_file = sqlite3.connect('cb.db3')
    cur = con_file.cursor()

    # {"高收益":{"color":"co","rows":["广汇转债":{"x":111,"y":222}]}}
    myCb = {}
    html = """
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Title</title>
</head>
<body>
<div>
    """

    # =========我的回售=========
    cur.execute("""
SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, round(bt_red * 100,2) as 回售收益率, red_t as 回售年限, rating as 信用
from changed_bond c, hold_bond h
WHERE c.bond_code = h.bond_code AND h.strategy_type = '回售' and h.hold_owner = 'me' and h.hold_amount != -1
order by 回售收益率
        """)

    html = print_table("回售", cur, html, 'r')

    # =========我的低溢价低余额策略=========
    cur.execute("""
SELECT c.bond_code as id, stock_code, c.cb_name_id as 名称, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2)  as '余额/股本(%)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, round(cb_price2_id + cb_premium_id * 100,2) as 双低值, rating as 信用
from changed_bond c, hold_bond h
WHERE c.bond_code = h.bond_code 
AND h.strategy_type = '低溢价低余额' 
and h.hold_owner = 'me' 
and h.hold_amount != -1
order by 转债价格
        """)

    html = print_table("低溢价低余额", cur, html, 'pink')

    # =========我的低价高收益策略=========
    cur.execute("""
        SELECT c.bond_code as id, stock_code, c.cb_name_id as 名称, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
        h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, round(bt_yield*100,2) as 收益率, round(100- cb_price2_id + BT_yield * 100, 2) as 性价比, rating as 信用
from changed_bond c, hold_bond h
WHERE c.bond_code = h.bond_code AND h.strategy_type = '低价格高收益' and h.hold_owner = 'me' and h.hold_amount != -1
ORDER by 性价比 desc
        """)

    html = print_table("低价格高收益", cur, html, 'b')

    # =========我的双低策略=========
    cur.execute("""
SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, 
round(cb_price2_id + cb_premium_id * 100,2) as 双低值, rating as 信用
from changed_bond c, hold_bond h
WHERE c.bond_code = h.bond_code AND h.strategy_type = '双低' and h.hold_owner = 'me' and h.hold_amount != -1
order by 双低值
        """)

    html = print_table("双低", cur, html, 'g')

    # =========我的打新策略=========
    cur.execute("""
SELECT c.bond_code as id, stock_code, c.cb_name_id as 名称, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, 
round(cb_price2_id + cb_premium_id * 100,2) as 双低值, rating as 信用, memo as 备注
from changed_bond c, hold_bond h
WHERE c.bond_code = h.bond_code AND h.strategy_type = '打新' and h.hold_owner = 'me' and h.hold_amount != -1
order by 转债价格
        """)

    html = print_table("打新", cur, html, 'm')

    # =========我的网格策略=========
    cur.execute("""
SELECT c.bond_code as id, stock_code, c.cb_name_id as 名称, round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, 
h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as 转债价格, round(cb_premium_id*100,2) as 溢价率, 
round(cb_price2_id + cb_premium_id * 100,2) as 双低值, rating as 信用
from changed_bond c, hold_bond h
WHERE c.bond_code = h.bond_code AND h.strategy_type = '网格' and h.hold_owner = 'me' and h.hold_amount != -1
order by 转债价格
        """)

    html = print_table("网格", cur, html, 'm')

    # =========我的基本面策略=========
    cur.execute("""
SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', 
    cb_price2_id as '转债价格', round(cb_premium_id*100,2) as 溢价率,
    rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as 市盈率, c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
    , cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s, 
    (select distinct bond_code, hold_owner, hold_amount, hold_price, strategy_type from hold_bond where hold_amount != -1) h
	where c.bond_code = s.bond_code and c.bond_code = h.bond_code
	 AND h.strategy_type = '基本面' and h.hold_owner = 'me' and h.hold_amount != -1
    order by 转债价格
        """)

    html = print_table("基本面", cur, html, 'darkorange')

    # =========我的每周精选策略=========
    cur.execute("""
SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) as 溢价率, 
    rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as 市盈率, c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
    , cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s, 
    (select distinct bond_code, hold_owner, hold_amount, hold_price, strategy_type from hold_bond where hold_amount != -1) h
	where c.bond_code = s.bond_code and c.bond_code = h.bond_code 
	AND h.strategy_type = '每周精选' and h.hold_owner = 'me' and h.hold_amount != -1
order by 转债价格
        """)

    html = print_table("每周精选", cur, html, 'c')

    # =========我的活性债策略=========
    cur.execute("""
SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) as 溢价率,
    rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as 市盈率, c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
    , cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s, 
    (select distinct bond_code, hold_owner, hold_amount, hold_price, strategy_type from hold_bond where hold_amount != -1) h
	where c.bond_code = s.bond_code and c.bond_code = h.bond_code
AND h.strategy_type = '活性债' and h.hold_owner = 'me' and h.hold_amount != -1 
--and h.hold_owner = '水晶杯'
order by 转债价格
        """)

    html = print_table("活性债", cur, html, 'y')

    # =========其他=========
    cur.execute("""
    SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) as 溢价率,
    rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as 市盈率, c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
    , cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.memo as 备注
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s, 
    (select distinct bond_code, hold_owner, hold_amount, hold_price, strategy_type, memo from hold_bond where hold_amount != -1) h
	where c.bond_code = s.bond_code and c.bond_code = h.bond_code 
	AND h.strategy_type is null and h.hold_owner = 'me' and h.hold_amount != -1
order by 双低值
        """)

    html = print_table("其他", cur, html, 'k')

    # =========全表=========
    cur.execute("""
    SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2) as 盈亏, h.hold_price || ' (' || h.hold_amount || ')' as '买入价(量)', cb_price2_id as '转债价格', round(cb_premium_id*100,2) as 溢价率,
    rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as 市盈率, c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    round(cb_price2_id + cb_premium_id * 100, 2) as 双低值
    , cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度, h.memo as 备注
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s, 
    (select distinct bond_code, hold_owner, hold_amount, hold_price, memo from hold_bond where hold_amount != -1) h
	where c.bond_code = s.bond_code and c.bond_code = h.bond_code
	and h.hold_owner='me' and h.hold_amount != -1
	--and duration < 3
	-- and cb_price2_id > 108
	and cb_price2_id < 130
	-- and roe > 5
	-- and s.net > 0
	-- and s.margin > 10
	-- and cb_t_id = '转股中'
	-- and 溢价率 < 20
	-- and 双低值 < 120
	order by 双低值 ASC;
        """)

    html = print_table("全表", cur, html)

    # 数据汇总
    cur.execute("""
        SELECT 
		sum(round(h.hold_price*h.hold_amount, 2)) as 总投入,
        sum(round((c.cb_price2_id - h.hold_price)*h.hold_amount, 2)) as 总盈亏
from changed_bond c, hold_bond h
    	where c.bond_code = h.bond_code and hold_amount != -1 and hold_owner='me'
            """)
    result = cur.fetchone()
    # 总金额
    invest = result[0]
    # 盈亏
    profit = result[1]
    # 收益率
    yield_rate = round(profit/invest*100, 2)

    html += """
    <center>
        </br>=========数据汇总=========</br>
        总投入: """ + str(invest) + """</br>
        总盈亏: """ + str(profit) + """</br>
        收益率: """ + str(yield_rate) + """%</br>
    </center>
    """

    f = open('view/view_my.html', 'w')
    s = ("""
    <style>
    div{

      overflow:auto;

      width:1324px;

      height:890px; /* 固定高度 */
      border:1px solid gray;
      border-bottom: 0;
      border-right: 0;
      

    }

    td, th {

      border-right :1px solid gray;
      border-bottom :1px solid gray;

      width:100px;

      height:30px;

      box-sizing: border-box;
      
      font-size:7;

    }

    th {

      background-color:lightblue;

    }


    table {
      border-collapse:separate;
      table-layout: fixed;
      width: 100%; /* 固定寬度 */

    }

    td:first-child, th:first-child {

      position:sticky;

      left:0; /* 首行在左 */

      z-index:1;

      background-color:lightpink;

    }

    thead tr th {

      position:sticky;

      top:0; /* 第一列最上 */

    }

    th:first-child{

      z-index:2;

      background-color:lightblue;

    }
  </style>

    """
    + html
    + """
    </div>
</body>
</html>
    """)
    f.write(s)
    f.close()
    filename = 'file:///' + os.getcwd() + '/view/' + 'view_my.html'
    webbrowser.open_new_tab(filename)

    con_file.close()

    draw_figure(myCb)

except Exception as e:
    con_file.close()
    print("操作失败", e)
    raise e
# print(type(x))