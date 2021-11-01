import json
import os

from jinja2 import Environment, FileSystemLoader

from models import db, Config

default_get_label = lambda row: row['名称'].replace('转债', '')


def add_nav_html(nav_html_list, type):
    if type is not None and nav_html_list is not None:
        nav_html_list.append(get_nav_html(type))


def add_sub_nav_html(htmls, title, s):
    # 增加导航
    nav_html = htmls.get('nav', '')

    nav_html += """
        <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">""" + title + """</a>
            <ul class="dropdown-menu">
              """ + s + """
            </ul>
        </li>
    """
    htmls['nav'] = nav_html


def get_nav_html(type):
    return '<li><a href="#' + type + '">' + type + '</a></li>'


def default_edit_link_maker(id, hold_id, bond_code):
    s = "&nbsp;<a href='"
    if hold_id is not None:
        s += '/sync_trade_data.html/' + str(hold_id) + '/'
    else:
        s += '/new_sync_trade_data.html/' + bond_code + '/'
    s += "'><img src='/static/img/trade.png' alt='交易' title='交易' width='14' height='14' class='next-site-link'/></a>"
    return s

env = Environment(
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            loader=FileSystemLoader(
                (
                    os.path.join(os.path.dirname(__file__), "../templates")
                )
            )
        )


def get_strategy_options_html(selected):
    row = db.session.query(Config) \
        .filter(Config.group == 'selectable_strategy_type_list', Config.key == 'strategy_type', Config.is_delete == 0) \
        .first()
    types = json.loads(row.value)
    options = '<option value="">Choose...</option>'
    for type in types:
        options += '<option value="' + type
        if type == selected:
            options += '" selected="selected">'
        else:
            options += '">'
        options += type + '</option>'
    return options