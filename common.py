#一些公共方法

def get_html_string(table):
    lines = []
    linebreak = "<br>"

    lines.append("<table>")

    # Headers
    lines.append("    <thead>")
    lines.append("        <tr>")
    for field in table._field_names:
        if field == 'id' or field == 'stock_code':
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
            if field == 'id' or field == 'stock_code':
                continue

            # 标题增加链接
            # 可转债: http://quote.eastmoney.com/bond/sz128051.html
            # 正股: http://quote.eastmoney.com/sz002741.html
            prefix = ''
            suffix = ''
            if field == '名称':
                bond_id = record['id']
                stock_code = record['stock_code']
                market = 'sz'
                if bond_id.startswith('11'):
                    market = 'sh'
                prefix = "<a target = '_blank' href = 'http://quote.eastmoney.com/bond/" + market + bond_id + ".html'>"
                suffix = "</a>&nbsp;<a target='_blank' href='http://quote.eastmoney.com/" + market + stock_code + ".html'>[正股]</a>"

            lines.append(
                ("            <td>" + prefix + "%s" + suffix + "</td>") % datum.replace("\n", linebreak)
            )
        lines.append("        </tr>")
    lines.append("    </tbody>")
    lines.append("</table>")

    return "\n".join(lines)

def getRecord(table, row):
    return dict(zip(table._field_names, row))