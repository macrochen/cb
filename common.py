#一些公共方法

def get_html_string(table):
    lines = []
    linebreak = "<br>"

    lines.append("<table>")

    # Headers
    lines.append("    <thead>")
    lines.append("        <tr>")
    for field in table._field_names:
        if field == 'nid' or field == 'id' or field == 'stock_code':
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
            if field == 'nid' or field == 'id' or field == 'stock_code':
                continue

            # 标题增加链接
            # 可转债: http://quote.eastmoney.com/bond/sz128051.html
            # 正股: http://quote.eastmoney.com/sz002741.html
            prefix = ''
            suffix = ''
            if field == '名称':
                bond_id = record['id']
                nid = record.get('nid')
                stock_code = record['stock_code']
                market = 'sz'
                if bond_id.startswith('11'):
                    market = 'sh'
                prefix = "<a target = '_blank' href = 'http://quote.eastmoney.com/bond/" + market + bond_id + ".html'>"

                suffix = ''
                if nid is not None:
                    suffix += "</a>&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=detail&a=detail&id=" + nid + "'>[nw]</a>"

                suffix += "</a>&nbsp;<a target='_blank' href='https://www.jisilu.cn/data/convert_bond_detail/" + bond_id + "'>[jsl]</a>"
                suffix += "</a>&nbsp;<a target='_blank' href='http://quote.eastmoney.com/" + market + stock_code + ".html'>[正股]</a>"
                suffix += "</a>&nbsp;<a target='_blank' href='http://doctor.10jqka.com.cn/" + stock_code + "/'>[诊断]</a>"


                if nid is not None:
                    #http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=157
                    suffix += "</a>&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=" + nid + "'>[走势]</a>"

            lines.append(
                ("            <td>" + prefix + "%s" + suffix + "</td>") % datum.replace("\n", linebreak)
            )
        lines.append("        </tr>")
    lines.append("    </tbody>")
    lines.append("</table>")

    return "\n".join(lines)

def getRecord(table, row):
    return dict(zip(table._field_names, row))

def rebuild_stock_code(stock_code):
    # 沪市A股票买卖的代码是以600、601或603打头, 688创业板
    # 深市A股票买卖的代码是以000打头, 中小板股票代码以002打头, 创业板股票代码以300打头
    if stock_code.startswith('600') or stock_code.startswith('601') or stock_code.startswith(
            '603') or stock_code.startswith('688'):
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