# 目前市面上各种策略(高收益, 双低, 活性债, 回售)的数据视图展示


# 需导入要用到的库文件
import numpy as np  # 数组相关的库
import matplotlib.pyplot as plt  # 绘图库
import sqlite3
import common

import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable
from prettytable import from_db_cursor

import webbrowser
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

config = {'type': [
    '双低策略',
    '高收益策略',
    '回售策略',
    '活性债策略',
    '低溢价低余额策略',
],
}

draw_plot = lambda row: plt.plot(row['转债价格'], row['溢价率'], 'ro', alpha=0.6)
get_annotate = lambda row: plt.annotate(row['名称'].replace('转债', ''), (row['转债价格'], row['溢价率']))


def draw_figure(con_file,
                sql,
                type,
                title,
                html,
                midY=29.49, # 溢价率(或各种收益率)中位数
                midX=108.13, # 转债价格中位数
                labelY='转债溢价率(%)',
                show_quadrant=True, #增加象限信息
                draw_plot=draw_plot,
                get_annotate=get_annotate):
    plt.figure(figsize=(10, 7),)

    cur = con_file.cursor()
    cur.execute(sql)

    table = from_db_cursor(cur)

    for row in table._rows:
        record = common.getRecord(table, row)
        get_annotate(record)
        draw_plot(record)

    # 水平线
    plt.axhline(y=midY, color='grey', linestyle='--', alpha=0.6)
    # 垂直线
    plt.axvline(x=midX, color='grey', linestyle='--', alpha=0.6)
    if show_quadrant:
        # 只有使用到溢价率时才使用四象限
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
    # 税前收益率
    plt.ylabel(labelY, bbox=dict(facecolor='green', alpha=0.5))
    plt.title(type)

    return html + "<br><center> =========<b><font color='red'>" + title + "</font></b>=========</center><br>" + common.get_html_string(table)


def draw_figures():
    # 打开文件数据库
    con_file = sqlite3.connect('cb.db3')

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
    try:

        # =========回售策略=========
        if "回售策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有
  FROM (
      SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
      cb_price2_id as 转债价格, round(bt_red * 100,2) || '%' as 回售收益率, red_t as '回售年限(年)', round((bt_red * 100) + (2-bond_t1),2) as 性价比,
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
        round(bt_yield*100,2) as 税前收益,
        round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
        s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
        round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as '市盈率(动)', c.stock_pb as 市净率,
        market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
        cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度,
        rating as '信用', duration as 续存期
        from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s
        where c.bond_code = s.bond_code
         and red_t not in('无权', '回售内')
         and red_t < 1
         and round(bt_red * 100,2) > 1
        --ORDER by 回售年限 ASC, 回售收益率 DESC;
        ORDER by 性价比 DESC) d left join 
        (select id as hold_id, bond_code from hold_bond where hold_owner = 'me' and hold_amount != -1 and strategy_type = '回售') e 
        on d.id = e.bond_code
            """
            draw_plot = lambda row: plt.plot(row['转债价格'], row['回售收益率'], 'ro', alpha=0.6)
            get_annotate = lambda row: plt.annotate(row['名称'].replace('转债', ''),
                                                    (row['转债价格'], row['回售收益率']))
            html = draw_figure(con_file, sql, "回售策略", "回售策略(回售年限<1年, 回收收益率>1%)", html,
                               midX=102, midY=0, labelY="回售收益率(%)",
                               show_quadrant=False, draw_plot=draw_plot, get_annotate=get_annotate)

        # =========低余额策略=========
        if "低溢价低余额策略" in config['type']:
            sql = """
SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有
  FROM (
      SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, remain_amount as '余额(亿元)', 
        cb_price2_id as 转债价格, round(cb_premium_id*100,2) || '%' as 溢价率, round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
        market_cap as '市值(亿元)', round(cb_to_share_shares * 100,2)  as '余额/股本(%)',
        c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as '市盈率(动)', c.stock_pb as 市净率,
    cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s
    where c.bond_code = s.bond_code
        and cb_premium_id * 100 < 30 
        and remain_amount < 3 
        and cb_price2_id < 115
        ORDER by 转债价格 ASC
        limit 10) d left join 
        (select id as hold_id, bond_code from hold_bond where hold_owner = 'me' and hold_amount != -1 and strategy_type = '低溢价低余额') e 
        on d.id = e.bond_code            
            """
            get_annotate = lambda row: plt.annotate(row['名称'].replace('转债', '') + '(' + str(row['余额(亿元)']) + '亿元)',
                                                    (row['转债价格'], row['溢价率']))
            html = draw_figure(con_file, sql, "低溢价低余额策略", "低余额策略(价格<115, 余额<3亿, 溢价率<30%)", html,
                               midX=120, midY=30, show_quadrant=False, get_annotate=get_annotate)

        # =========双低债=========
        if "双低策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有
  FROM (
      SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
      cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
      c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round(bt_yield*100,2) as 税前收益,
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as '市盈率(动)', c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度,
    rating as '信用', duration as 续存期
    from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s
    where c.bond_code = s.bond_code
        ORDER by 双低值
        limit 20) d left join 
        (select id as hold_id, bond_code from hold_bond where hold_owner = 'me' and hold_amount != -1 and strategy_type = '双低') e 
        on d.id = e.bond_code
        
            """
            html = draw_figure(con_file, sql, "双低策略", "双低债(双低值前20)", html, midY=29.7)

        # =========高收益策略=========
        if "高收益策略" in config['type']:
            sql = """
        SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有
  FROM (
      SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, 
      cb_price2_id as '转债价格', round(bt_yield*100,2) || '%' as 到期收益率, round(100- cb_price2_id + BT_yield * 100, 2) as 性价比,
      c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
    round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
    s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
    round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as '市盈率(动)', c.stock_pb as 市净率,
    market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
    cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度,
    round(cb_premium_id*100,2) as 溢价率, rating as '信用', duration as 续存期
        from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s
    where c.bond_code = s.bond_code
        and c.rating in ('AA+', 'AA-', 'AA', 'AAA', 'A', 'A+')
        --and c.cb_name_id not in( '亚药转债' , '本钢转债','搜特转债','广汇转债')
        AND bt_yield > 0
        and cb_price2_id < 110
        order by 性价比 DESC
        limit  20) d left join 
        (select id as hold_id, bond_code from hold_bond where hold_owner = 'me' and hold_amount != -1 and strategy_type = '低价格高收益') e 
        on d.id = e.bond_code;
            """
            draw_plot = lambda row: plt.plot(row['转债价格'], row['到期收益率'], 'ro', alpha=0.6)
            get_annotate = lambda row: plt.annotate(row['名称'].replace('转债', ''),
                                                    (row['转债价格'], row['到期收益率']))
            html = draw_figure(con_file, sql, "高收益策略", "高收益策略(价格<110, 到期收益率前20, 信用A以上)", html,
                               midX=98, midY=2, labelY="到期收益率(%)",
                               show_quadrant=False, draw_plot=draw_plot, get_annotate=get_annotate)

            # =========活性债策略=========
            if "活性债策略" in config['type']:
                sql = """
          SELECT DISTINCT d.* , case when e.hold_id is not null then  '✔️️' else  '' END as 持有
        FROM (
            SELECT c.bond_code as id, c.stock_code, c.cb_name_id as 名称, c.stock_name as 正股名称, c.industry as '行业', c.sub_industry as '子行业',
          cb_price2_id as '转债价格', round(cb_premium_id*100,2) || '%' as 溢价率,round(cb_price2_id + cb_premium_id * 100, 2) as 双低值,
          rating as '信用', duration as 续存期, round(bt_yield*100,2) as 税前收益,
          round(s.revenue,2) as '营收(亿元)',s.yoy_revenue_rate || '%' as '营收同比', round(s.net,2) as '净利润(亿元)', s.yoy_net_rate || '%' as '净利润同比', 
          s.margin || '%' as '利润率(%)', s.yoy_margin_rate || '%' as '利润率同比', s.roe || '%' as 'ROE(%)', s.yoy_roe_rate || '%' as 'ROE同比',  
          round(s.al_ratio,2) || '%' as 负债率, s.yoy_al_ratio_rate || '%' as '负债率同比', s.pe as '市盈率(动)', c.stock_pb as 市净率,
          market_cap as '市值(亿元)', remain_amount as '余额(亿元)', round(cb_to_share_shares * 100,2) || '%'  as '余额/股本(%)',
          cb_ma20_deviate as 'ma20乖离', cb_hot as 热门度
          from (select * from changed_bond where enforce_get not in ('强赎中', '满足强赎') or enforce_get is null) c, stock_report s
          where c.bond_code = s.bond_code
          and duration < 3 
          and cb_price2_id > 108 and cb_price2_id < 125 
          -- and roe > 5 
          and s.net > 0
          -- and s.margin > 10
          and cb_t_id = '转股中' 
          and (enforce_get not in ('强赎中', '满足强赎') or enforce_get is null)
          -- and 溢价率 < 20 
          and 双低值 < 120
          order by 双低值 ASC) d left join 
              (select id as hold_id, bond_code from hold_bond where hold_owner = 'me' and hold_amount != -1 and strategy_type = '活性债') e 
              on d.id = e.bond_code
                  """
                html = draw_figure(con_file, sql, "活性债策略", "活性债策略(价格在108~120, 净利润为正, 双低值<120, 存续期<3年)", html, midY=13)

        con_file.close()



        f = open('view/view_market.html', 'w')
        s = ("""
            <style>
            div{

              overflow:auto;

              width:1424px;

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
        filename = 'file:///' + os.getcwd() + '/view/' + 'view_market.html'
        webbrowser.open_new_tab(filename)

        plt.show()
    except Exception as e:
        con_file.close()
        print("操作失败. " + str(e), e)
        raise e

if __name__ == "__main__":
    draw_figures()
    print("显示完成")
