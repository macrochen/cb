#一些公共方法
import os
import sqlite3

from jinja2 import Environment, FileSystemLoader

from selenium import webdriver

import re

css_html = """
<style>

    td, th {
      border-right :1px solid gray;
      border-bottom :1px solid gray;
      text-align:center;
      width:100px;
      height:50px;
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
    
    .site-link{
        margin-bottom:2px;
        margin-right:3px
    }
    
    .next-site-link{
        margin-bottom:-1px;
        margin-right:4px
    }
    
    .remarked-up{
        color:red
    }
    .remarked-down{
        color:green
    }
    
</style>
"""

env = Environment(
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(
                (
                    os.path.join(os.path.dirname(__file__), "templates")
                )
            )
        )
#https://www.jisilu.cn/data/cbnew/cb_index/
#转股价格中位数
MID_X = 122.349
#转股溢价率中位数
MID_Y = 34.90
#到期收益率中位数
MID_YIELD = -3.92

# MID_Y, MID_X, MID_YIELD = get_cb_sum_data()

def get_cb_sum_data():

    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')
    cur = con_file.cursor()
    cur.execute("""select key, value from config where field_name='cb_sum_data'""")
    rows = cur.fetchall()
    for row in rows:
        key = row[0]
        value = row[1]
        if key == 'mid_premium_rate':
            mid_y = value
        elif key == 'mid_price':
            mid_x = value
        elif key == 'mid_yield_rate':
            mid_yield = value
        else:
            raise Exception('unknow key:' + key)

    return mid_y, mid_x, mid_yield


def update_cb_sum_data():

    # 打开文件数据库
    con_file = sqlite3.connect('db/cb.db3')

    driver = webdriver.Chrome()

    driver.implicitly_wait(10)

    url = "https://www.jisilu.cn/data/cbnew/cb_index/"

    # fixme 需要把chromedriver放到/usr/local/bin目录下
    driver.get(url)

    div = driver.find_element_by_id("cb_index")

    s = div.text
    ss = re.findall(r"转股溢价率 (\d+\.?\d*)%", s)
    if len(ss) != 1:
        raise Exception("没有找到转股溢价率中位数:" + s)
    # MID_Y = ss[0]
    result = con_file.execute("""insert into config(key,value,field_name)values
                                    ('mid_premium_rate', ?, 'cb_sum_data')""",
                              (ss[0])
                              )
    if result.rowcount == 0:
        print("not insert mid_premium_rate config:" + ss[0])
    else:
        print("insert mid_premium_rate is successful. count:" + str(result.rowcount))

    ss = re.findall(r"中位数价格 (\d+\.?\d*)", s)
    if len(ss) != 1:
        raise Exception("没有找到转股价格中位数:" + s)
    # MID_X = ss[0]
    result = con_file.execute("""insert into config(key,value,field_name)values
                                    ('mid_price', ?, 'cb_sum_data')""",
                              (ss[0])
                              )
    if result.rowcount == 0:
        print("not insert mid_price config:" + ss[0])
    else:
        print("insert mid_price is successful. count:" + str(result.rowcount))

    ss = re.findall(r"到期收益率 (-?\d+\.?\d*)%", s)
    if len(ss) != 1:
        raise Exception("没有找到到期收益率中位数:" + s)
    # MID_YIELD = ss[0]
    result = con_file.execute("""insert into config(key,value,field_name)values
                                    ('mid_yield_rate', ?, 'cb_sum_data')""",
                              (ss[0])
                              )
    if result.rowcount == 0:
        print("not insert mid_yield_rate config:" + ss[0])
    else:
        print("insert mid_yield_rate is successful. count:" + str(result.rowcount))

    # print("MID_Y = " + MID_Y + ' \nMID_X = ' + MID_X + '\nMID_YIELD = ' + MID_YIELD)

    driver.close()

def get_html_string(table, remark_fields_color = []):
    ignore_fields = ['nid', 'id', 'stock_code', '持有', '持有成本', '持有数量', 'cb_mov2_id']

    lines = []
    linebreak = "<br>"

    lines.append("<table>")

    # Headers
    lines.append("    <thead>")
    lines.append("        <tr>")

    for field in table._field_names:
        if ignore_fields.count(field) > 0:
            continue

        lines.append(
            "            <th>%s</th>" % field.replace("\n", linebreak)
        )
    lines.append("        </tr>")
    lines.append("    </thead>")

    # Data
    lines.append("    <tbody>")
    options = table._get_options({})
    rows = table._get_rows(options)
    formatted_rows = table._format_rows(rows, options)
    for row in formatted_rows:
        lines.append("        <tr>")
        record = getRecord(table, row)
        for field, datum in record.items():
            if ignore_fields.count(field) > 0:
                continue

            # 标题增加链接
            # 可转债: http://quote.eastmoney.com/bond/sz128051.html
            # 正股: http://quote.eastmoney.com/sz002741.html
            prefix = ''
            prefix_append = ''
            suffix = ''
            if field == '名称':
                bond_id = record['id']
                nid = record['nid']
                stock_code = record['stock_code']
                market = 'sz'
                if bond_id.startswith('11'):
                    market = 'sh'
                prefix = "<a target = '_blank' href = 'http://quote.eastmoney.com/bond/" + market + bond_id + ".html'>"

                prefix_append += "</a>&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=detail&a=detail&id=" + nid + "'><img src='../img/nw.png' alt='宁稳网' title='宁稳网查看转债信息' width='14' height='14' class='site-link'/></a>"

                prefix_append += "&nbsp;<a target='_blank' href='https://www.jisilu.cn/data/convert_bond_detail/" + bond_id + "'><img src='../img/jsl.png' alt='集思录' title='集思录查看转债信息' width='14' height='14' class='site-link'/></a>"

                # https://xueqiu.com/S/SH600998
                suffix = "<br/>&nbsp;<a target = '_blank' href = 'https://xueqiu.com/S/" + market + bond_id + "'><img src='../img/xueqiu.png' alt='雪球' title='雪球查看转债讨论' width='14' height='14' class='next-site-link'/></a>"
                suffix += "&nbsp;<a target='_blank' href='http://quote.eastmoney.com/" + market + stock_code + ".html'><img src='../img/eastmoney.png' alt='东方财富' title='东方财富查看正股信息' width='14' height='14' class='next-site-link'/></a> "
                suffix += "<a target='_blank' href='http://doctor.10jqka.com.cn/" + stock_code + "/'><img src='../img/ths.png' alt='同花顺' title='同花顺正股诊断' width='14' height='14' class='next-site-link'/></a>"

                #http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=157
                suffix += "&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=" + nid + "'><img src='../img/trend.png' alt='走势图' title='宁稳网查看转债&正股走势(非会员20次/天)' width='14' height='14' class='next-site-link'/></a>"
            remark_color = ''
            if remark_fields_color.count(field) > 0:
                if datum.startswith('-'):
                    remark_color = 'class="remarked-down"'
                else:
                    remark_color = 'class="remarked-up"'

            lines.append(
                ("            <td " + remark_color + ">" + prefix + "%s" + prefix_append + "" + suffix + "</td>") % datum.replace("\n", linebreak)
                # fixme 重构成函数变量
                .replace('转债标的 ', '')
                .replace('标准普尔 ', '')
                .replace('富时罗素 ', '')
                .replace('上证380 ', '')
                .replace('央视50_ ', '')
                .replace('中证500 ', '')
                .replace('深成500 ', '')
                .replace('融资融券 ', '')
                .replace('上证180_ ', '')
                .replace('HS300_ ', '')
                .replace('MSCI中国 ', '')
                .replace('深股通 ', '')
                .replace('创业板综 ', '')
                .replace('沪股通 ', '')
                )
        lines.append("        </tr>")
    lines.append("    </tbody>")
    lines.append("</table>")

    return "\n".join(lines)

def add_nav_html(htmls, type):
    # 增加导航
    active = ''
    if len(htmls) == 0:
        active = 'class="active"'
    nav_html = htmls.get('nav', '')
    nav_html += '<li ' + active + '><a href="#' + type + '">' + type + '</a></li>'
    htmls['nav'] = nav_html

def getRecord(table, row):
    return dict(zip(table._field_names, row))

def getDictRow(cursor, row):
    if cursor.description:
        field_names = [col[0] for col in cursor.description]
        return dict(zip(field_names, row))

    raise Exception('not convert to dict row')

def rebuild_stock_code(stock_code):
    # 沪市A股票买卖的代码是以600、601或603打头, 688创业板
    # 深市A股票买卖的代码是以000打头, 中小板股票代码以002打头, 创业板股票代码以300打头
    if stock_code.startswith('600') or stock_code.startswith('601') or \
            stock_code.startswith('605') or stock_code.startswith('603') or stock_code.startswith('688'):
        stock_code = 'SH' + stock_code
    elif stock_code.startswith('000') or stock_code.startswith('001') or stock_code.startswith(
            '002') or stock_code.startswith('300'):
        stock_code = 'SZ' + stock_code
    else:
        raise Exception("未知股票类型。" + stock_code)
    return stock_code

def rebuild_bond_code(bond_code):
    market = 'sz'
    if bond_code.startswith('11'):
        market = 'sh'
    return market + bond_code

if __name__ == "__main__":
    update_cb_sum_data()